"""
Тесты ядра на ЭТАЛОНАХ: задачи с известным точным ответом. Без Django, без БД, без HTTP.
"""
import random

import pytest

from core.schemas import MAX_ARRIVAL_RATE, MAX_HORIZON_MIN, MAX_SERVICE_MEAN, SimulationParams
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
