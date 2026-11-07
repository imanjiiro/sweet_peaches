"""
Доступ к страницам: вход обязателен, чужая задача -> 404 (то же правило, что в API, ADR-004).
Граница входа в форме: слишком большая смена отвергается сразу, расчёт не запускается.
"""
import pytest
from django.contrib.auth import get_user_model

from web.models import Task


@pytest.fixture
def owner(db):
    return get_user_model().objects.create_user("page_owner", password="pass-owner-12345")


@pytest.fixture
def stranger(db):
    return get_user_model().objects.create_user("page_stranger", password="pass-stranger-12345")


@pytest.fixture
def owners_task(owner):
    return Task.objects.create(
        name="задача владельца",
        owner=owner,
        params={},
        status=Task.Status.DONE,
        result={"average_wait_time": 1.0},
    )


@pytest.mark.django_db
def test_foreign_task_page_gets_404(client, stranger, owners_task):
    """Чужая задача на странице -> 404 (раньше было 403: два правила для одного и того же)."""
    client.force_login(stranger)
    assert client.get(f"/tasks/{owners_task.pk}/").status_code == 404


@pytest.mark.django_db
def test_page_and_api_use_one_rule_for_foreign_task(client, stranger, owners_task):
    """Страница и API отвечают на чужую задачу одинаково."""
    client.force_login(stranger)
    assert client.get(f"/tasks/{owners_task.pk}/").status_code == 404
    assert client.get(f"/api/tasks/{owners_task.pk}").status_code == 404


@pytest.mark.django_db
def test_owner_sees_own_task_page(client, owner, owners_task):
    client.force_login(owner)
    r = client.get(f"/tasks/{owners_task.pk}/")
    assert r.status_code == 200
    assert "задача владельца" in r.content.decode()


@pytest.mark.django_db
def test_superuser_does_not_bypass_owner_rule(client, owners_task):
    """Исключения для суперпользователя нет: ему — админка (/admin/), страница и API — по общему правилу."""
    admin = get_user_model().objects.create_superuser("page_admin", password="pass-admin-12345")
    client.force_login(admin)
    assert client.get(f"/tasks/{owners_task.pk}/").status_code == 404


@pytest.mark.django_db
def test_anonymous_is_redirected_to_login(client, owners_task):
    """Без входа страницы ведут на форму входа, задачу не видно."""
    for url in ("/", "/tasks/create/", f"/tasks/{owners_task.pk}/"):
        r = client.get(url)
        assert r.status_code == 302
        assert r.headers["Location"].startswith("/login/")


@pytest.mark.django_db
def test_task_list_page_shows_only_own_tasks(client, owner, stranger, owners_task):
    client.force_login(stranger)
    assert "задача владельца" not in client.get("/").content.decode()
    client.force_login(owner)
    assert "задача владельца" in client.get("/").content.decode()


@pytest.mark.django_db
def test_form_rejects_too_long_shift_before_calculation(client, owner):
    """Смена 48 000 минут: форма отвечает ошибкой сразу, задача не создаётся, расчёт не запускается."""
    client.force_login(owner)
    r = client.post(
        "/tasks/create/",
        {
            "name": "слишком длинная смена",
            "doctors": 3,
            "strategy": "fifo",
            "arrival_rate": 1.0,
            "service_mean": 5.0,
            "horizon_min": 48000,
        },
    )
    assert r.status_code == 200
    assert "horizon_min" in r.context["form"].errors
    assert Task.objects.count() == 0
