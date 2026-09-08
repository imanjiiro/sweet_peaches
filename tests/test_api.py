"""Тесты API-контракта. Используют тестовую БД Django."""

import pytest
from web.models import Task


@pytest.mark.django_db
def test_create_task_returns_202_and_computes(client):
    valid_params = {
        "doctors": 3,
        "strategy": "fifo",
        "arrival_rate": 10.0,
        "service_mean": 15.0,
        "horizon_min": 480.0,
        "n_runs": 5
    }
    r = client.post(
        "/api/tasks",
        {"name": "t", "params": valid_params},
        content_type="application/json",
    )
    assert r.status_code == 202
    task_id = r.json()["id"]

    r2 = client.get(f"/api/tasks/{task_id}/result")
    assert r2.status_code == 200

    res = r2.json()["result"]
    assert "average_wait_time" in res or "wait_time" in res or "metrics" in res


@pytest.mark.django_db
def test_bad_params_are_rejected_with_422(client):
    invalid_params = {
        "doctors": -1,
        "strategy": "invalid",
        "arrival_rate": -5.0
    }
    r = client.post(
        "/api/tasks", 
        {"name": "bad", "params": invalid_params}, 
        content_type="application/json"
    )
    assert r.status_code == 422
    assert Task.objects.count() == 0


@pytest.mark.django_db
def test_list_and_status(client):
    valid_params = {
        "doctors": 3,
        "strategy": "fifo",
        "arrival_rate": 10.0,
        "service_mean": 15.0,
        "horizon_min": 480.0,
        "n_runs": 5
    }
    client.post(
        "/api/tasks", 
        {"name": "x", "params": valid_params}, 
        content_type="application/json"
    )
    assert len(client.get("/api/tasks").json()) == 1

    tasks = client.get("/api/tasks").json()
    assert tasks[0]["status"] in ["done", "running", "created"]

    assert client.get("/api/tasks/999").status_code == 404