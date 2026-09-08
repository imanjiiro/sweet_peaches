"""Сценарный тест (третий уровень): пользователь через форму создаёт задачу и видит результат."""
import pytest


@pytest.mark.django_db
def test_user_creates_task_via_form_and_sees_result(client):
    r = client.post("/tasks/new/", {"name": "demo", "function": "x2", "a": 0, "b": 1, "n": 100, "method": "simpson"})
    assert r.status_code == 302
    page = client.get(r.headers["Location"])
    assert page.status_code == 200
    assert "Готово" in page.content.decode()
    assert "0,333333" in page.content.decode() or "0.333333" in page.content.decode()
