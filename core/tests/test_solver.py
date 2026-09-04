# core/tests/test_solver.py — Больница
# Эталон: 1 врач, 3 пациента приходят в t = 0,
# приём каждого ровно 5 минут → ждут 0, 5 и 10 минут
#
# Ответ известен ДО кода: посчитан на листке за минуту, без единого
# запуска функции (см. занятие 3, слайд "Эталон: Больница"). Тест
# фиксирует этот ответ; реализация в core/simulation.py должна его
# воспроизводить.

from core.simulation import run

BASE = {
    "doctors": 1,
    "service_time": 5,
    "seed": 1,
    "patients": [
        (0, "плановый"),
        (0, "плановый"),
        (0, "плановый"),
    ],
}


def test_fifo_waits_are_0_5_10():
    r = run(**{**BASE, "strategy": "fifo"})
    assert r["waits"] == [0, 5, 10]  # третий ждёт двоих
    assert r["avg_wait"] == 5


def test_priority_serves_critical_first():
    p = [(0, "плановый"), (0, "срочный"), (0, "критический")]
    r = run(**{**BASE, "patients": p, "strategy": "priority"})
    assert r["served"] == ["критический", "срочный", "плановый"]


def test_priority_waits_are_0_5_10_by_urgency():
    # Эталон: критический -> 0, срочный -> 5, плановый -> 10;
    # среднее ожидание = (0 + 5 + 10) / 3 = 5.
    p = [(0, "плановый"), (0, "срочный"), (0, "критический")]
    r = run(**{**BASE, "patients": p, "strategy": "priority"})
    # waits — в исходном порядке списка patients: плановый, срочный, критический
    assert r["waits"] == [10, 5, 0]
    assert r["avg_wait"] == 5


def test_priority_does_not_preempt_already_started_service():
    # Плановый пришёл в t=0 и сразу начал обслуживаться (врач был
    # свободен, критический ещё не пришёл). Критический приходит
    # только в t=1 — он НЕ может вытеснить уже идущее обслуживание
    # или "телепортироваться" перед плановым задним числом.
    p = [(0, "плановый"), (1, "критический")]
    r = run(doctors=1, service_time=5, patients=p, strategy="priority")
    assert r["served"] == ["плановый", "критический"]
    assert r["waits"] == [0, 4]  # плановый: 0; критический: (0+5) - 1 = 4


def test_fifo_respects_arrival_order():
    p = [(0, "плановый"), (1, "плановый"), (2, "плановый")]
    r = run(doctors=1, service_time=5, patients=p, strategy="fifo")
    assert r["served"] == ["плановый", "плановый", "плановый"]
    assert r["waits"] == [0, 4, 8]
