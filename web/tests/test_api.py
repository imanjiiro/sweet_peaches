"""
web/tests/test_api.py — "Работа 2: API", пункт 4 (тест и коммит).

Проверяем ровно то, что просили на слайде "Работа 2":
  1. тело из примера на слайде своей команды -> 202 и task_id;
  2. испорченное тело (чужая строка в своём поле) -> 422 с этим полем в тексте;
  3. GET .../result -> 200.

Плюс отдельно — пример с самого слайда "API: Больница": strategy="random"
не входит в pattern (fifo|priority|dynamic) -> 422 ("нет такой стратегии
в списке").

Расчёт теперь фоновый (galочка 7) — сразу после POST статус обычно ещё
"queued"/"running", поэтому тесты, которым нужен готовый результат,
ждут завершения фонового потока (_wait_until_done). Используем
transaction=True: фоновый поток открывает своё соединение к БД и должен
видеть уже закоммиченную строку, а обычный @pytest.mark.django_db
оборачивает тест в незакоммиченную транзакцию, которую другому
соединению не видно.
"""
import time

import pytest
from django.test import Client

from web.models import RunStatus, SimulationRun

VALID_BODY = {
    "params": {
        "doctors": 2,
        "arrival_rate": 0.5,
        "service_mean": 8,
        "strategy": "priority",
        "n_runs": 3,
        "seed": 1,
    },
}


def _wait_until_finished(task_id: str, timeout: float = 5.0) -> SimulationRun:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        run = SimulationRun.objects.get(id=task_id)
        if run.status in (RunStatus.DONE, RunStatus.FAILED):
            return run
        time.sleep(0.02)
    raise AssertionError(f"фоновый расчёт не завершился за {timeout}с")


@pytest.mark.django_db(transaction=True)
def test_valid_body_returns_202_with_task_id_and_finishes_in_background():
    client = Client()
    response = client.post(
        "/api/tasks", data=VALID_BODY, content_type="application/json"
    )
    assert response.status_code == 202
    body = response.json()
    assert "task_id" in body
    # сразу после ответа расчёт мог ещё не завершиться — это и есть "фон"
    assert body["status"] in ("queued", "running", "done")

    run = _wait_until_finished(body["task_id"])
    assert run.status == RunStatus.DONE
    assert run.duration_seconds is not None and run.duration_seconds >= 0


@pytest.mark.django_db
def test_bad_strategy_returns_422():
    client = Client()
    bad_body = {**VALID_BODY, "params": {**VALID_BODY["params"], "strategy": "random"}}
    response = client.post(
        "/api/tasks", data=bad_body, content_type="application/json"
    )
    assert response.status_code == 422
    assert "strategy" in response.text


@pytest.mark.django_db(transaction=True)
def test_get_result_returns_200_after_background_run_finishes():
    client = Client()
    created = client.post(
        "/api/tasks", data=VALID_BODY, content_type="application/json"
    ).json()
    _wait_until_finished(created["task_id"])

    response = client.get(f"/api/tasks/{created['task_id']}/result")
    assert response.status_code == 200
    result = response.json()
    assert result["patients_served"] is not None
    assert result["avg_wait_time"] is not None
