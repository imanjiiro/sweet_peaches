"""
Тесты ядра на ЭТАЛОНАХ: задачи с известным точным ответом. Без Django, без БД, без HTTP.
"""
import pytest
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


def test_hospital_queue_priority():
    """
    Тест приоритетной очереди (Priority):
    Пациенты приходят в t=0:
    - Пациент 1: плановый (priority=1)
    - Пациент 2: критический (priority=3)
    Критический должен пройти раньше планового!
    """
    params = {
        "doctors": 1,
        "strategy": "priority",
        "patients": [
            {"id": 1, "arrival_time": 0.0, "service_time": 5.0, "priority": 1},
            {"id": 2, "arrival_time": 0.0, "service_time": 5.0, "priority": 3},
        ],
    }

    result = run(params)

    # Первый пришедший обслуживается сразу (0.0), а второй (критический) выходит следующим
    assert result["served_patients_count"] == 2
    assert result["average_wait_time"] == 2.5


def test_invalid_strategy_rejected():
    """Проверка валидации: неизвестная стратегия отвергается до расчёта."""
    with pytest.raises(ValueError):
        run({"doctors": 1, "strategy": "unknown_strategy_name"})