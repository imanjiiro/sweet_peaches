"""
core/simulation.py

Вычислительное ядро сервиса. core/ не импортирует Django, не ходит в
БД и в HTTP — только чистый Python (см. AGENTS.md).

Интерфейс низкоуровневой функции run() продиктован эталонным тестом
(core/tests/test_solver.py, занятие 3, слайд "Эталон: Больница"):
чтобы тест был возможен без единого вызова random, run() должен уметь
принимать ГОТОВЫЙ список пациентов, а не только интенсивность потока.
Поэтому:

- если передан patients (список (arrival_time, urgency)) — run()
  считает детерминированно, по этому списку;
- если patients не передан — run() сам генерирует поток по интенсивности
  и seed (пуассоновские приходы + экспоненциальное время обслуживания).
  Случайный прогон проверяется отдельно, по формуле теории очередей, а
  не поэлементно.

Поверх run() есть simulate() — то, что реально вызывает web/services.py:
делает n_runs повторов (усредняет метрики) и переводит "сырые" waits в
метрики, которые хранятся в SimulationResult (см. web/models.py).
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

URGENCY_WEIGHT = {
    "критический": 3,
    "срочный": 2,
    "плановый": 1,
}

# Доли срочностей в сгенерированном потоке. Это допущение — на слайде
# инструктора распределение срочностей не задано явно, поэтому берём
# правдоподобное распределение потока приёмного отделения. Меняется
# в одном месте, если появится реальная статистика.
URGENCY_MIX = (
    ("плановый", 0.7),
    ("срочный", 0.2),
    ("критический", 0.1),
)

# Насколько быстро "стареет" пациент в динамической стратегии: за
# каждые AGING_MINUTES ожидания приоритет пациента растёт на единицу
# срочности — это не даёт "плановым" пациентам ждать бесконечно на
# фоне непрерывного потока "срочных" (простая защита от голодания).
AGING_MINUTES = 15.0

STRATEGIES = ("fifo", "priority", "dynamic")


def _pick_urgency(rng: random.Random) -> str:
    roll = rng.random()
    acc = 0.0
    for urgency, share in URGENCY_MIX:
        acc += share
        if roll <= acc:
            return urgency
    return URGENCY_MIX[-1][0]


def generate_patients(
    arrival_rate: float,
    horizon_min: float,
    seed: int,
) -> list[tuple[float, str]]:
    """
    Сгенерировать поток пациентов пуассоновским процессом.

    arrival_rate — пациентов в минуту (см. HospitalParams, занятие 3).
    horizon_min  — длина смены в минутах, поток обрезается по ней.
    seed         — делает поток воспроизводимым.
    """
    rng = random.Random(seed)
    patients: list[tuple[float, str]] = []
    t = 0.0
    while True:
        t += rng.expovariate(arrival_rate)
        if t > horizon_min:
            break
        patients.append((t, _pick_urgency(rng)))
    return patients


def _generate_service_times(
    n: int, service_time: float, seed: int
) -> list[float]:
    """Экспоненциальные времена обслуживания — свой генератор, чтобы
    не смешивать поток приходов и поток длительностей приёма одним
    и тем же rng (иначе прогоны с разным n_patients расходятся)."""
    rng = random.Random(seed)
    return [rng.expovariate(1 / service_time) for _ in range(n)]


def run(
    doctors: int,
    service_time: float,
    seed: int | None = None,
    patients: list[tuple[float, str]] | None = None,
    strategy: str = "fifo",
    horizon_min: float | None = None,
    randomize_service_times: bool = False,
) -> dict:
    """
    Разобрать пациентов по врачам одной стратегией и вернуть метрики.

    doctors      — сколько врачей (серверов) принимают пациентов.
    service_time — среднее время приёма одного пациента, минуты.
                   При явном patients — используется как ФИКСИРОВАННОЕ
                   время приёма (как в эталонном тесте). При случайной
                   генерации потока (patients не передан) — как среднее
                   экспоненциального распределения длительности приёма.
    seed         — используется только вместе с randomize_service_times
                   (см. ниже); при явном patients без этого флага
                   игнорируется, как и раньше (эталонный тест держит
                   service_time фиксированным для всех пациентов, хотя
                   и передаёт seed).
    patients     — готовый список пациентов вида (время_прихода, срочность),
                   срочность — одна из "критический" / "срочный" / "плановый".
                   Если не передан — сгенерируйте его через
                   generate_patients() и передайте (это делает simulate()).
    strategy     — "fifo" / "priority" / "dynamic".
    horizon_min  — используется только для метрики загрузки врачей
                   выше по стеку (см. simulate()); run() сама очередь
                   не обрезает.
    randomize_service_times — True только когда поток сгенерирован
                   случайно (см. simulate()): тогда service_time — это
                   СРЕДНЕЕ экспоненциального распределения длительности
                   приёма, а не фиксированное время для всех. По
                   умолчанию False — service_time одинаково для всех
                   пациентов, как того требует эталонный тест.

    Возвращает dict:
        {"waits": [...], "avg_wait": float, "served": [...],
         "total_service_time": float}
    "waits" — время ожидания каждого пациента, в исходном порядке списка
    patients. "served" — срочности пациентов в порядке, в котором их
    приняли врачи (то есть в порядке обслуживания, а не поступления).
    "total_service_time" — суммарное время работы врачей (для загрузки).
    """
    if doctors <= 0:
        raise ValueError("doctors должен быть больше нуля")
    if service_time <= 0:
        raise ValueError("service_time должен быть больше нуля")
    if strategy not in STRATEGIES:
        raise ValueError(f"unknown strategy: {strategy}")

    if patients is None:
        raise NotImplementedError(
            "run() принимает только готовый список patients — сгенерируйте "
            "поток через generate_patients() и передайте его сюда "
            "(см. simulate(), которая делает это автоматически)"
        )

    if not patients:
        return {"waits": [], "avg_wait": 0.0, "served": [], "total_service_time": 0.0}

    # Фиксированное время обслуживания — поведение эталонного теста.
    # Случайные времена обслуживания — только когда об этом явно просит
    # вызывающий код (simulate(), который сам сгенерировал поток).
    if not randomize_service_times:
        service_times = [service_time] * len(patients)
    else:
        if seed is None:
            raise ValueError("seed обязателен при randomize_service_times=True")
        service_times = _generate_service_times(len(patients), service_time, seed)

    if strategy == "fifo":
        waits, served, total_service = _run_fifo(doctors, patients, service_times)
    elif strategy == "priority":
        waits, served, total_service = _run_priority(doctors, patients, service_times)
    else:  # dynamic
        waits, served, total_service = _run_dynamic(doctors, patients, service_times)

    avg_wait = sum(waits) / len(waits)

    return {
        "waits": waits,
        "avg_wait": avg_wait,
        "served": served,
        "total_service_time": total_service,
    }


def _run_fifo(
    doctors: int,
    patients: list[tuple[float, str]],
    service_times: list[float],
) -> tuple[list[float], list[str], float]:
    """FIFO: порядок обслуживания = порядок прихода, без учёта срочности.

    Здесь безопасно один раз отсортировать всех пациентов по времени
    прихода и раздать их врачам жадно (каждому следующему по приходу —
    тот врач, что освобождается раньше): порядок обслуживания не
    зависит от того, кто из пациентов "уже пришёл" в момент
    освобождения врача, поэтому такой оффлайн-проход эквивалентен
    честной посимвольной симуляции FIFO с несколькими врачами.
    Индекс — только чтобы порядок был детерминирован при одинаковом
    времени прихода (см. тест FIFO — все приходят в момент 0).
    """
    indexed = list(enumerate(patients))
    order = sorted(indexed, key=lambda item: (item[1][0], item[0]))

    doctors_free_at = [0.0] * doctors
    waits = [0.0] * len(patients)
    served: list[str] = []
    total_service = 0.0

    for original_index, (arrival, urgency) in order:
        doctor = min(range(doctors), key=lambda d: doctors_free_at[d])
        start = max(arrival, doctors_free_at[doctor])
        waits[original_index] = start - arrival
        duration = service_times[original_index]
        doctors_free_at[doctor] = start + duration
        served.append(urgency)
        total_service += duration

    return waits, served, total_service


def _run_priority(
    doctors: int,
    patients: list[tuple[float, str]],
    service_times: list[float],
) -> tuple[list[float], list[str], float]:
    """Priority: событийная симуляция, а НЕ глобальная сортировка всех
    пациентов по срочности заранее.

    Заранее отсортировать всех пациентов по срочности нельзя: это
    позволило бы критическому пациенту, который придёт только в
    будущем, "вытеснить" уже пришедшего (или уже обслуживаемого)
    планового пациента задним числом — врач не может знать о
    пациенте, который ещё не пришёл.

    Поэтому в момент, когда врач освобождается: берём только уже
    пришедших-но-не-принятых пациентов, среди них выбираем самого
    срочного (при равной срочности — раньше пришедшего, FIFO); если
    ещё никто не пришёл — переводим время вперёд, к ближайшему
    приходу (врач не тратит время впустую, но и не может принять
    пациента раньше его прихода).
    """
    n = len(patients)
    order_by_arrival = sorted(range(n), key=lambda i: (patients[i][0], i))
    waiting: list[int] = []  # индексы пришедших, но не принятых пациентов
    next_arrival_pos = 0
    doctors_free_at = [0.0] * doctors
    waits = [0.0] * n
    served: list[str] = []
    total_service = 0.0
    served_count = 0

    while served_count < n:
        doctor = min(range(doctors), key=lambda d: doctors_free_at[d])
        now = doctors_free_at[doctor]

        # Впустить в очередь ожидания всех, кто успел прийти к этому моменту.
        while (
            next_arrival_pos < n
            and patients[order_by_arrival[next_arrival_pos]][0] <= now
        ):
            waiting.append(order_by_arrival[next_arrival_pos])
            next_arrival_pos += 1

        if not waiting:
            # Врач свободен, но ещё никто не пришёл — ждём следующего
            # пациента (нельзя принять пациента раньше его прихода).
            next_idx = order_by_arrival[next_arrival_pos]
            now = patients[next_idx][0]
            waiting.append(next_idx)
            next_arrival_pos += 1

        best = min(
            waiting,
            key=lambda i: (-URGENCY_WEIGHT[patients[i][1]], patients[i][0], i),
        )
        waiting.remove(best)

        arrival, urgency = patients[best]
        start = max(arrival, now)
        waits[best] = start - arrival
        duration = service_times[best]
        doctors_free_at[doctor] = start + duration
        served.append(urgency)
        total_service += duration
        served_count += 1

    return waits, served, total_service


def _run_dynamic(
    doctors: int,
    patients: list[tuple[float, str]],
    service_times: list[float],
) -> tuple[list[float], list[str], float]:
    """
    Динамическая стратегия: приоритет пациента растёт со временем
    ожидания (см. AGING_MINUTES) — это не даёт "плановым" пациентам
    ждать бесконечно, если непрерывно приходят более срочные.

    Событийная модель: на каждом шаге берём момент, когда освобождается
    ближайший врач, и среди уже пришедших-но-не-принятых пациентов
    выбираем того, у кого в этот момент максимальный приоритет
    (urgency + время_ожидания / AGING_MINUTES). Если на этот момент
    никто ещё не пришёл — сразу перескакиваем к приходу следующего
    пациента.
    """
    n = len(patients)
    indexed = sorted(range(n), key=lambda i: patients[i][0])  # по приходу
    waiting: list[int] = []  # индексы пришедших, но не принятых пациентов
    next_arrival_pos = 0
    doctors_free_at = [0.0] * doctors
    waits = [0.0] * n
    served: list[str] = []
    total_service = 0.0
    served_count = 0

    while served_count < n:
        doctor = min(range(doctors), key=lambda d: doctors_free_at[d])
        now = doctors_free_at[doctor]

        # Впустить в очередь всех, кто успел прийти к этому моменту.
        while (
            next_arrival_pos < n
            and patients[indexed[next_arrival_pos]][0] <= now
        ):
            waiting.append(indexed[next_arrival_pos])
            next_arrival_pos += 1

        if not waiting:
            # Врач свободен, но никто ещё не пришёл — ждём следующего
            # пациента, время врача не тратится впустую.
            next_idx = indexed[next_arrival_pos]
            now = patients[next_idx][0]
            waiting.append(next_idx)
            next_arrival_pos += 1

        best = max(
            waiting,
            key=lambda i: (
                URGENCY_WEIGHT[patients[i][1]] + (now - patients[i][0]) / AGING_MINUTES,
                -patients[i][0],
            ),
        )
        waiting.remove(best)

        arrival, urgency = patients[best]
        start = max(arrival, now)
        waits[best] = start - arrival
        duration = service_times[best]
        doctors_free_at[doctor] = start + duration
        served.append(urgency)
        total_service += duration
        served_count += 1

    return waits, served, total_service


@dataclass
class SimulationMetrics:
    avg_wait_time: float
    max_wait_time: float
    avg_queue_length: float
    doctor_utilization: float
    patients_served: int


def simulate(
    doctors: int,
    arrival_rate: float,
    service_mean: float,
    horizon_min: float,
    strategy: str,
    n_runs: int = 1,
    seed: int | None = None,
    patients: list[tuple[float, str]] | None = None,
) -> SimulationMetrics:
    """
    Высокоуровневая точка входа — то, что зовёт web/services.py.

    Если patients передан явно — считаем один детерминированный прогон
    по нему (n_runs игнорируется, как и для run(); это тестовый/
    демонстрационный режим, см. слайд "Тонкость").

    Иначе — n_runs независимых прогонов со своим seed (seed + i), поток
    каждый раз генерируется заново по arrival_rate/horizon_min, метрики
    усредняются по прогонам.
    """
    if patients is not None:
        result = run(
            doctors=doctors,
            service_time=service_mean,
            seed=seed,
            patients=patients,
            strategy=strategy,
        )
        return _metrics_from_run(result, doctors, horizon_min)

    if seed is None:
        raise ValueError("seed обязателен для случайной генерации потока")

    per_run: list[SimulationMetrics] = []
    for i in range(n_runs):
        run_seed = seed + i
        run_patients = generate_patients(arrival_rate, horizon_min, run_seed)
        result = run(
            doctors=doctors,
            service_time=service_mean,
            seed=run_seed,
            patients=run_patients,
            strategy=strategy,
            randomize_service_times=True,
        )
        per_run.append(_metrics_from_run(result, doctors, horizon_min))

    return SimulationMetrics(
        avg_wait_time=sum(m.avg_wait_time for m in per_run) / n_runs,
        max_wait_time=max(m.max_wait_time for m in per_run),
        avg_queue_length=sum(m.avg_queue_length for m in per_run) / n_runs,
        doctor_utilization=sum(m.doctor_utilization for m in per_run) / n_runs,
        patients_served=round(sum(m.patients_served for m in per_run) / n_runs),
    )


def _metrics_from_run(
    result: dict, doctors: int, horizon_min: float
) -> SimulationMetrics:
    waits = result["waits"]
    if not waits:
        return SimulationMetrics(0.0, 0.0, 0.0, 0.0, 0)

    avg_wait = result["avg_wait"]
    max_wait = max(waits)
    # Средняя длина очереди — приближение по формуле Литтла (L = λ·W):
    # честная событийная длина очереди во времени не считается, это
    # оценка через среднее ожидание и интенсивность потока.
    avg_queue_length = (len(waits) / horizon_min) * avg_wait
    doctor_utilization = min(1.0, result["total_service_time"] / (doctors * horizon_min))

    return SimulationMetrics(
        avg_wait_time=avg_wait,
        max_wait_time=max_wait,
        avg_queue_length=avg_queue_length,
        doctor_utilization=doctor_utilization,
        patients_served=len(waits),
    )
