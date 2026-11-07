"""Сценарный тест: пользователь через форму создаёт задачу и видит результат."""

import re

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


@pytest.mark.django_db
def test_user_creates_task_via_form_and_sees_result(client):
    # Создаем и авторизуем пользователя
    user = User.objects.create_user(username="testuser", password="password123")
    client.force_login(user)

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

    url = reverse("task_create")
    r = client.post(url, form_data)

    if r.status_code == 200 and "form" in r.context:
        assert not r.context["form"].errors, f"Ошибки валидации формы: {r.context['form'].errors}"

    assert r.status_code == 302
    redirect_url = r.headers["Location"]

    page = client.get(redirect_url)
    assert page.status_code == 200

    content = page.content.decode()

    # Имя задачи
    assert "demo" in content

    # Результат появился на странице: таблицы с числами, а не только имя
    assert "Результат симуляции" in content
    assert "Ожидание по срочности" in content
    assert "Плановые" in content and "Критические" in content
    assert "Среднее время ожидания" in content

    # Интерфейс по-русски, без словаря Python и без «сырых» длинных чисел
    assert "<title>Задача №" in content
    assert "Hospital Flow Simulation" not in content
    assert "{'doctors'" not in content
    assert "Стратегия очереди" in content and "По порядку прихода" in content
    assert not re.search(r"\d+[.,]\d{4,}", content)