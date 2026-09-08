"""
Вычислительное ядро: имитационное моделирование работы приёмного отделения больницы.

Заменяет заготовку численного интегрирования. Сохраняет контракт run(params) -> dict
и поддерживает тесты на эталонных задачах (core/tests/).
"""
import random
import time
from core.schemas import SimulationParams, SimulationResult

VERSION = "1.0.0"  # версия ядра для воспроизводимости расчётов


def _run_single_simulation(doctors: int, patients_list: list, strategy: str) -> dict:
    """
    Прогон одной симуляции для заданного списка пациентов.
    Пациенты — список словарей: [{'id': 1, 'arrival_time': 0, 'service_time': 5, 'priority': 1}, ...]
    """
    # Сортируем приходы пациентов по времени
    events = sorted(patients_list, key=lambda x: x["arrival_time"])
    
    # Время освобождения каждого врача (изначально все свободны в t = 0)
    doctor_free_times = [0.0] * doctors
    
    wait_times = []
    queue = []  # Очередь ожидающих пациентов: (patient_dict, queue_enter_time)
    
    current_time = 0.0
    patient_idx = 0
    total_patients = len(events)
    served_count = 0
    
    # Для расчёта загрузки врачей
    total_busy_time = 0.0

    while patient_idx < total_patients or queue:
        # Если очередь пуста, перематываем время к приходу следующего пациента
        if not queue and patient_idx < total_patients:
            current_time = max(current_time, events[patient_idx]["arrival_time"])

        # Все пациенты, пришедшие к текущему моменту времени, попадают в очередь
        while patient_idx < total_patients and events[patient_idx]["arrival_time"] <= current_time:
            queue.append((events[patient_idx], events[patient_idx]["arrival_time"]))
            patient_idx += 1

        # Ищем первого освободившегося врача
        earliest_doctor_idx = min(range(doctors), key=lambda i: doctor_free_times[i])
        doctor_available_time = doctor_free_times[earliest_doctor_idx]

        if doctor_available_time > current_time and queue:
            current_time = doctor_available_time
            # Дозаполняем очередь теми, кто успел прийти за время ожидания врача
            while patient_idx < total_patients and events[patient_idx]["arrival_time"] <= current_time:
                queue.append((events[patient_idx], events[patient_idx]["arrival_time"]))
                patient_idx += 1

        if not queue:
            continue

        # ВЫБОР ПАЦИЕНТА ИЗ ОЧЕРЕДИ ПО СТРАТЕГИИ
        if strategy == "fifo":
            chosen_idx = 0
        elif strategy == "priority":
            # Выбираем максимальный приоритет (3 - критический, 2 - срочный, 1 - плановый)
            chosen_idx = max(range(len(queue)), key=lambda i: queue[i][0].get("priority", 1))
        elif strategy == "dynamic":
            # Dynamic: учитывает срочность + старение (ageing: +1 к приоритету за каждые 15 минут ожидания)
            def score(i):
                p_dict, arr_t = queue[i]
                base_p = p_dict.get("priority", 1)
                wait_t = current_time - arr_t
                return base_p + (wait_t / 15.0)

            chosen_idx = max(range(len(queue)), key=lambda i: score(i))
        else:
            chosen_idx = 0

        patient, arr_time = queue.pop(chosen_idx)
        wait_t = max(0.0, current_time - arr_time)
        wait_times.append(wait_t)

        serv_t = patient["service_time"]
        total_busy_time += serv_t

        # Обновляем время врача
        start_service = max(current_time, arr_time)
        doctor_free_times[earliest_doctor_idx] = start_service + serv_t
        served_count += 1

    avg_wait = sum(wait_times) / len(wait_times) if wait_times else 0.0
    max_wait = max(wait_times) if wait_times else 0.0
    
    # Максимальное время работы всей симуляции
    max_time = max(doctor_free_times) if doctor_free_times else 1.0
    doc_utilization = total_busy_time / (doctors * max_time) if max_time > 0 else 0.0

    return {
        "average_wait_time": round(avg_wait, 2),
        "max_wait_time": round(max_wait, 2),
        "average_queue_length": round(len(wait_times) / max(1, len(events)), 2),
        "doctor_utilization": round(min(1.0, doc_utilization), 2),
        "served_patients_count": served_count,
        "wait_times": [round(w, 2) for w in wait_times],
    }


def generate_stochastic_patients(arrival_rate: float, service_mean: float, horizon_min: float, seed: int = None) -> list:
    """Генерация случайного потока пациентов (Пуассоновский процесс приходов + экспоненциальное время обслуживания)."""
    if seed is not None:
        random.seed(seed)

    patients = []
    current_t = 0.0
    p_id = 1

    while current_t < horizon_min:
        # Интервал между приходами (экспоненциальное распределение)
        inter_arrival = random.expovariate(arrival_rate)
        current_t += inter_arrival
        if current_t >= horizon_min:
            break

        # Время обслуживания (экспоненциальное распределение)
        serv_time = random.expovariate(1.0 / service_mean)
        
        # Распределение приоритетов: 70% плановые (1), 20% срочные (2), 10% критические (3)
        r = random.random()
        if r < 0.7:
            priority = 1
        elif r < 0.9:
            priority = 2
        else:
            priority = 3

        patients.append({
            "id": p_id,
            "arrival_time": current_t,
            "service_time": serv_time,
            "priority": priority
        })
        p_id += 1

    return patients


def run(params: dict) -> dict:
    """Единственная точка входа ядра. Вход и выход — обычные dict (JSON-совместимые)."""
    p = SimulationParams.model_validate(params)
    started = time.perf_counter()

    if p.patients is not None and len(p.patients) > 0:
        # Детерминированный режим (для эталонных тестов)
        patients_list = [pat.model_dump() for pat in p.patients]
        res_dict = _run_single_simulation(p.doctors, patients_list, p.strategy)
    else:
        # Стохастический режим (случайная генерация)
        runs_results = []
        base_seed = p.seed if p.seed is not None else 42

        for i in range(p.n_runs):
            patients_list = generate_stochastic_patients(
                arrival_rate=p.arrival_rate,
                service_mean=p.service_mean,
                horizon_min=p.horizon_min,
                seed=base_seed + i
            )
            if not patients_list:
                continue
            run_res = _run_single_simulation(p.doctors, patients_list, p.strategy)
            runs_results.append(run_res)

        if not runs_results:
            res_dict = {
                "average_wait_time": 0.0,
                "max_wait_time": 0.0,
                "average_queue_length": 0.0,
                "doctor_utilization": 0.0,
                "served_patients_count": 0,
                "wait_times": []
            }
        else:
            # Усредняем показатели по n_runs прогонам
            res_dict = {
                "average_wait_time": round(sum(r["average_wait_time"] for r in runs_results) / len(runs_results), 2),
                "max_wait_time": round(max(r["max_wait_time"] for r in runs_results), 2),
                "average_queue_length": round(sum(r["average_queue_length"] for r in runs_results) / len(runs_results), 2),
                "doctor_utilization": round(sum(r["doctor_utilization"] for r in runs_results) / len(runs_results), 2),
                "served_patients_count": int(sum(r["served_patients_count"] for r in runs_results) / len(runs_results)),
                "wait_times": runs_results[0]["wait_times"],  # Задержки первого прогона для наглядности
            }

    elapsed = time.perf_counter() - started

    result = SimulationResult(
        average_wait_time=res_dict["average_wait_time"],
        max_wait_time=res_dict["max_wait_time"],
        average_queue_length=res_dict["average_queue_length"],
        doctor_utilization=res_dict["doctor_utilization"],
        served_patients_count=res_dict["served_patients_count"],
        wait_times=res_dict["wait_times"],
        core_version=VERSION
    )

    out = result.model_dump()
    out["elapsed_sec"] = round(elapsed, 4)
    return out