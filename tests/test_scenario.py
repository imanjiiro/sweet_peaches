"""Сценарный тест: пользователь через форму создаёт задачу и видит результат."""
import pytest


@pytest.mark.django_db
def test_user_creates_task_via_form_and_sees_result(client):
    # Используем минимальные параметры n_runs и horizon_min, чтобы симуляция отрабатывала за миллисекунды
    form_data = {
        "name": "demo",
        "doctors": 2,
        "strategy": "fifo",
        "arrival_rate": 2.0,
        "service_mean": 5.0,
        "horizon_min": 60.0,
        "n_runs": 1,
    }

    r = client.post("/tasks/new/", form_data)

    if r.status_code == 200 and "form" in r.context:
        assert not r.context["form"].errors, f"Ошибки валидации формы: {r.context['form'].errors}"

    assert r.status_code == 302
    redirect_url = r.headers["Location"]

    page = client.get(redirect_url)
    assert page.status_code == 200

    content = page.content.decode()

    # Проверяем отображение имени задачи
    assert "demo" in content