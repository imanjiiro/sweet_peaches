"""Тесты API-контракта и безопасности доступа. Используют тестовую БД Django."""

import pytest
from django.contrib.auth import get_user_model
from web.models import Task


@pytest.fixture
def user_a(db):
    User = get_user_model()
    return User.objects.create_user("user_a", password="pass-a-12345")


@pytest.fixture
def user_b(db):
    User = get_user_model()
    return User.objects.create_user("user_b", password="pass-b-12345")


@pytest.fixture
def task_of_user_a(user_a):
    """Готовая задача пользователя A (для проверки изолированности доступа)."""
    return Task.objects.create(
        name="задача A",
        owner=user_a,
        params={},
        status=Task.Status.DONE,
        result={"x": 1},
    )


@pytest.mark.django_db
def test_create_task_returns_202_and_computes(client, user_a):
    client.login(username="user_a", password="pass-a-12345")
    valid_params = {
        "doctors": 3,
        "strategy": "fifo",
        "arrival_rate": 10.0,
        "service_mean": 15.0,
        "horizon_min": 480.0,
        "n_runs": 5,
    }
    r = client.post(
        "/api/tasks/",
        {"name": "t", "params": valid_params},
        content_type="application/json",
    )
    assert r.status_code == 202
    task_id = r.json()["id"]

    r2 = client.get(f"/api/tasks/{task_id}/result/")
    assert r2.status_code == 200

    res = r2.json()["result"]
    assert "average_wait_time" in res or "wait_time" in res or "metrics" in res


@pytest.mark.django_db
def test_bad_params_are_rejected_with_422(client, user_a):
    client.login(username="user_a", password="pass-a-12345")
    invalid_params = {
        "doctors": -1,
        "strategy": "invalid",
        "arrival_rate": -5.0,
    }
    r = client.post(
        "/api/tasks/",
        {"name": "bad", "params": invalid_params},
        content_type="application/json",
    )
    assert r.status_code == 422
    assert Task.objects.count() == 0


@pytest.mark.django_db
def test_horizon_min_validation_rejected(client, user_a):
    """Слишком большой horizon_min отвергается со статусом 422."""
    client.login(username="user_a", password="pass-a-12345")
    invalid_params = {
        "doctors": 1,
        "strategy": "fifo",
        "horizon_min": 48000.0,
    }
    r = client.post(
        "/api/tasks/",
        {"name": "horizon_too_large", "params": invalid_params},
        content_type="application/json",
    )
    assert r.status_code == 422
    assert Task.objects.filter(name="horizon_too_large").count() == 0


@pytest.mark.django_db
def test_list_and_status(client, user_a):
    client.login(username="user_a", password="pass-a-12345")
    valid_params = {
        "doctors": 3,
        "strategy": "fifo",
        "arrival_rate": 10.0,
        "service_mean": 15.0,
        "horizon_min": 480.0,
        "n_runs": 5,
    }
    client.post(
        "/api/tasks/",
        {"name": "x", "params": valid_params},
        content_type="application/json",
    )
    assert len(client.get("/api/tasks/").json()) == 1

    tasks = client.get("/api/tasks/").json()
    assert tasks[0]["status"] in ["done", "running", "created"]

    assert client.get("/api/tasks/999/").status_code == 404


@pytest.mark.django_db
def test_other_user_gets_404_for_foreign_task(client, user_b, task_of_user_a):
    """Пользователь B запрашивает задачу пользователя A -> 404 (статус и результат)."""
    client.login(username="user_b", password="pass-b-12345")

    assert client.get(f"/api/tasks/{task_of_user_a.pk}/").status_code == 404
    assert client.get(f"/api/tasks/{task_of_user_a.pk}/result/").status_code == 404


@pytest.mark.django_db
def test_anonymous_gets_404_for_foreign_task(client, task_of_user_a):
    """Без входа задача пользователя A недоступна через API: 404."""
    assert client.get(f"/api/tasks/{task_of_user_a.pk}/").status_code == 404
    assert client.get(f"/api/tasks/{task_of_user_a.pk}/result/").status_code == 404


@pytest.mark.django_db
def test_owner_sees_own_task(client, task_of_user_a):
    client.login(username="user_a", password="pass-a-12345")

    assert client.get(f"/api/tasks/{task_of_user_a.pk}/").status_code == 200
    assert client.get(f"/api/tasks/{task_of_user_a.pk}/result/").status_code == 200


@pytest.mark.django_db
def test_list_contains_only_own_tasks(client, user_a, user_b, task_of_user_a):
    """В списке только свои: у B пусто, у A одна задача, без входа тоже пусто."""
    client.login(username="user_b", password="pass-b-12345")
    assert client.get("/api/tasks/").json() == []

    client.login(username="user_a", password="pass-a-12345")
    assert [t["name"] for t in client.get("/api/tasks/").json()] == ["задача A"]

    client.logout()
    assert client.get("/api/tasks/").json() == []