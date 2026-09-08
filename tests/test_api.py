"""Тесты API-контракта (занятие 16: второй уровень пирамиды). Используют тестовую БД Django."""

import pytest

from web.models import Task


@pytest.mark.django_db
def test_create_task_returns_202_and_computes(client):
    r = client.post(
        "/api/tasks",
        {"name": "t", "params": {"function": "sin", "a": 0, "b": 3.141592653589793, "n": 100}},
        content_type="application/json",
    )
    assert r.status_code == 202
    task_id = r.json()["id"]
    r2 = client.get(f"/api/tasks/{task_id}/result")
    assert r2.status_code == 200
    assert abs(r2.json()["result"]["value"] - 2.0) < 1e-4


@pytest.mark.django_db
def test_bad_params_are_rejected_with_422(client):
    r = client.post(
        "/api/tasks", {"name": "bad", "params": {"function": "eval", "a": 0, "b": 1}}, content_type="application/json"
    )
    assert r.status_code == 422
    assert Task.objects.count() == 0  # задача не создаётся, если вход невалиден


@pytest.mark.django_db
def test_list_and_status(client):
    client.post(
        "/api/tasks", {"name": "x", "params": {"function": "x2", "a": 0, "b": 1}}, content_type="application/json"
    )
    assert len(client.get("/api/tasks").json()) == 1
    assert client.get("/api/tasks?status=done").json()[0]["status"] == "done"
    assert client.get("/api/tasks/999").status_code == 404
