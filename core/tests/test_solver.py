"""
Тесты ядра на ЭТАЛОНАХ: задачи с известным точным ответом. Без Django, без БД, без HTTP.
"""
import random

import pytest

from core.schemas import MAX_ARRIVAL_RATE, MAX_HORIZON_MIN, MAX_PATIENTS, MAX_SERVICE_MEAN, SimulationParams
from core.solver import run


def test_reference_hospital_queue_fifo():
    """
    Эталонный тест из методички (Стратегия FIFO):
    - 1 врач
    - 3 пациента приходят одновременно в t = 0 (время приема = 5 мин)
    - Ожидаемые задержки: [0.0, 5.0, 10.0]
    - Среднее время ожидания: 5.0
    """
    params = {
        "doctors": 1,
        "strategy": "fifo",
        "patients": [
            {"id": 1, "arrival_time": 0.0, "service_time": 5.0, "priority": 1},
            {"id": 2, "arrival_time": 0.0, "service_time": 5.0, "priority": 1},
            {"id": 3, "arrival_time": 0.0, "service_time": 5.0, "priority": 1},
        ],
    }

    result = run(params)

    assert result["wait_times"] == [0.0, 5.0, 10.0]
    assert result["average_wait_time"] == 5.0
    assert result["served_patients_count"] == 3


def test_priority_differs_from_fifo():
    """
    Эталонный тест с разным временем приёма (Слайды 15 и 76):
    - Пациент 1: плановый (priority=1), долгий приём (service_time=10.0)
    - Пациент 2: критический (priority=3), короткий приём (service_time=2.0)

    В FIFO: Пациент 1 (ждет 0), Пациент 2 (ждет 10.0) -> avg = (0 + 10) / 2 = 5.0
    В Priority: Пациент 2 идет первым (ждет 0), Пациент 1 (ждет 2.0) -> avg = (0 + 2) / 2 = 1.0
    """
    patients = [
        {"id": 1, "arrival_time": 0.0, "service_time": 10.0, "priority": 1},
        {"id": 2, "arrival_time": 0.0, "service_time": 2.0, "priority": 3},
    ]

    base_params = {"doctors": 1, "patients": patients}

    # Прогон по FIFO
    fifo_result = run({**base_params, "strategy": "fifo"})
    assert fifo_result["average_wait_time"] == 5.0

    # Прогон по Priority
    prio_result = run({**base_params, "strategy": "priority"})
    assert prio_result["average_wait_time"] == 1.0


def test_invalid_strategy_rejected():
    """Проверка валидации: неизвестная стратегия отвергается до расчёта."""
    with pytest.raises(ValueError):
        run({"doctors": 1, "strategy": "unknown_strategy_name"})


def test_average_queue_length_matches_queueing_theory():
    """
    Эталон: теория очередей M/M/1. Приход 0.1 пациента в минуту, приём в среднем 5 минут, один врач:
    загрузка rho = 0.1 * 5 = 0.5, средняя длина очереди Lq = rho^2 / (1 - rho) = 0.25 / 0.5 = 0.5 человека.
    Результат случайный, поэтому проверяем диапазон; смена самая длинная из допустимых (1440 мин, граница входа),
    а прогонов много, чтобы стартовая пустая очередь не искажала среднее.
    """
    result = run({
        "doctors": 1,
        "strategy": "fifo",
        "arrival_rate": 0.1,
        "service_mean": 5.0,
        "horizon_min": 1440,
        "n_runs": 200,
        "seed": 1,
    })

    assert 0.4 < result["average_queue_length"] < 0.6


def test_same_seed_same_result():
    """У каждого прогона свой генератор: тот же seed -> тот же ответ."""
    params = {"doctors": 2, "strategy": "priority", "arrival_rate": 0.5, "n_runs": 5, "seed": 7}

    assert run(params)["average_wait_time"] == run(params)["average_wait_time"]


def test_global_random_is_not_touched():
    """Ядро не трогает общий random: соседняя задача в другом потоке не сбивает свои числа."""
    random.seed(123)
    expected = random.random()

    random.seed(123)
    run({"doctors": 1, "arrival_rate": 0.2, "n_runs": 3, "seed": 99})

    assert random.random() == expected


def test_priority_heap_order():
    """Куча отдаёт пациентов по приоритету, при равном — по времени прихода."""
    patients = [
        {"id": 1, "arrival_time": 0.0, "service_time": 10.0, "priority": 1},
        {"id": 2, "arrival_time": 1.0, "service_time": 5.0, "priority": 1},
        {"id": 3, "arrival_time": 2.0, "service_time": 5.0, "priority": 3},
        {"id": 4, "arrival_time": 3.0, "service_time": 5.0, "priority": 2},
    ]
    result = run({"doctors": 1, "strategy": "priority", "patients": patients})

    # порядок приёма: 1, 3, 4, 2 -> ожидание 0, 10-2, 15-3, 20-1
    assert result["wait_times"] == [0.0, 8.0, 12.0, 19.0]


@pytest.mark.parametrize(
    "field, too_big",
    [
        ("arrival_rate", MAX_ARRIVAL_RATE + 1),
        ("service_mean", MAX_SERVICE_MEAN + 1),
        ("horizon_min", MAX_HORIZON_MIN + 1),
        ("horizon_min", 48000),  # смена 48 000 минут (случай из задания пары 12)
    ],
)
def test_input_above_limit_rejected_before_calculation(field, too_big):
    """Граница «не больше» проверяется ДО расчёта: слишком большое значение -> ошибка, расчёт не начинается."""
    with pytest.raises(ValueError):
        run({"doctors": 1, "strategy": "fifo", field: too_big})


def test_input_at_limit_is_accepted():
    """Само граничное значение допустимо («не больше», а не «меньше»)."""
    p = SimulationParams.model_validate(
        {
            "arrival_rate": MAX_ARRIVAL_RATE,
            "service_mean": MAX_SERVICE_MEAN,
            "horizon_min": MAX_HORIZON_MIN,
        }
    )
    assert p.horizon_min == 1440.0



# Три пациента, на которых dynamic и priority дают РАЗНЫЙ порядок (считано руками).
# Врач один. Пациент 1 приходит в 0 и занимает врача до t = 40. Пока он принимает, ждут двое:
#   пациент 2: приход 1,  срочность 1, приём 5
#   пациент 3: приход 20, срочность 2, приём 5
# В момент t = 40 врач выбирает из двоих:
#   priority: срочность 2 больше 1, берёт пациента 3 (потом пациента 2)
#     ожидание: пациент 1 = 0, пациент 3 = 40 - 20 = 20, пациент 2 = 45 - 1 = 44  -> [0, 20, 44]
#   dynamic: счёт = срочность - приход / 15 (чем больше, тем раньше)
#     пациент 2: 1 - 1 / 15 = 0.93;  пациент 3: 2 - 20 / 15 = 0.67 -> берёт пациента 2 (он дольше в очереди)
#     ожидание: пациент 1 = 0, пациент 2 = 40 - 1 = 39, пациент 3 = 45 - 20 = 25  -> [0, 39, 25]
THREE_PATIENTS = [
    {"id": 1, "arrival_time": 0.0, "service_time": 40.0, "priority": 1},
    {"id": 2, "arrival_time": 1.0, "service_time": 5.0, "priority": 1},
    {"id": 3, "arrival_time": 20.0, "service_time": 5.0, "priority": 2},
]


def test_dynamic_and_priority_give_different_order():
    """dynamic проверен эталоном: если подставить в неё формулу priority, тест упадёт."""
    by_priority = run({"doctors": 1, "strategy": "priority", "patients": THREE_PATIENTS})
    by_dynamic = run({"doctors": 1, "strategy": "dynamic", "patients": THREE_PATIENTS})

    assert by_priority["wait_times"] == [0.0, 20.0, 44.0]
    assert by_dynamic["wait_times"] == [0.0, 39.0, 25.0]


def test_wait_by_priority_is_counted_separately():
    """Ожидание по срочности: на тех же трёх пациентах, стратегия priority (ожидания 0, 44 и 20 считаны руками)."""
    result = run({"doctors": 1, "strategy": "priority", "patients": THREE_PATIENTS})
    rows = {row["priority"]: row for row in result["wait_by_priority"]}

    assert rows[1]["count"] == 2  # пациенты 1 и 2
    assert rows[1]["average_wait_time"] == 22.0  # (0 + 44) / 2
    assert rows[1]["max_wait_time"] == 44.0
    assert rows[2]["count"] == 1  # пациент 3
    assert rows[2]["average_wait_time"] == 20.0
    assert rows[3]["count"] == 0
    assert rows[3]["average_wait_time"] == 0.0


def test_strategies_differ_by_priority_not_overall():
    """Смысл проекта: стратегия сдвигает ожидание между срочностями. У priority критические ждут меньше, чем у fifo."""
    base = {"doctors": 2, "arrival_rate": 0.3, "service_mean": 10.0, "horizon_min": 480.0, "n_runs": 30, "seed": 5}
    fifo = run({**base, "strategy": "fifo"})
    prio = run({**base, "strategy": "priority"})

    critical_fifo = fifo["wait_by_priority"][2]["average_wait_time"]
    critical_prio = prio["wait_by_priority"][2]["average_wait_time"]
    assert critical_prio < critical_fifo


def test_too_long_patient_list_rejected():
    """30 000 пациентов в готовом списке не принимаются (раньше пропускало и отвечало 202)."""
    patients = [{"id": i, "arrival_time": float(i), "service_time": 1.0} for i in range(1, 30001)]
    with pytest.raises(ValueError):
        run({"doctors": 1, "strategy": "fifo", "patients": patients})


def test_patient_list_at_limit_is_accepted():
    patients = [{"id": i, "arrival_time": float(i), "service_time": 1.0} for i in range(1, MAX_PATIENTS + 1)]
    assert SimulationParams.model_validate({"patients": patients}).patients is not None
