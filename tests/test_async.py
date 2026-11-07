import time

import pytest

from web.models import Task
from web.services import create_task


@pytest.mark.django_db(transaction=True)
def test_async_thread_execution():
    """Тест фонового выполнения через threading.Thread."""
    params = {
        "doctors": 1,
        "arrival_rate": 0.1,
        "service_mean": 5.0,
        "horizon_min": 60.0,
        "strategy": "fifo",
    }
    
    # Создаем задачу и запрашиваем фоновый запуск
    task = create_task(name="Async Test", params=params, async_exec=True)
    
    # Сразу после создания статус CREATED, QUEUED или RUNNING
    assert task.status in [Task.Status.CREATED, Task.Status.QUEUED, Task.Status.RUNNING]
    
    # Ожидаем завершения фонового процесса (до 3 секунд)
    for _ in range(30):
        task.refresh_from_db()
        if task.status in [Task.Status.DONE, Task.Status.FAILED]:
            break
        time.sleep(0.1)
        
    assert task.status == Task.Status.DONE
    assert task.result is not None

@pytest.mark.django_db(transaction=True)
def test_three_background_tasks_in_a_row_all_done():
    """Три задачи подряд в фоне: раньше они падали с «database is locked», теперь все done."""
    params = {
        "doctors": 2,
        "arrival_rate": 0.3,
        "service_mean": 5.0,
        "horizon_min": 120.0,
        "n_runs": 20,
        "strategy": "priority",
    }
    tasks = [create_task(name=f"Фон {i}", params=params, async_exec=True) for i in range(3)]

    deadline = time.time() + 30
    while time.time() < deadline:
        for t in tasks:
            t.refresh_from_db()
        if all(t.status in [Task.Status.DONE, Task.Status.FAILED] for t in tasks):
            break
        time.sleep(0.2)

    assert [t.status for t in tasks] == [Task.Status.DONE] * 3, [t.error for t in tasks]


def test_sqlite_waits_for_lock_instead_of_failing():
    """Настройка SQLite из config/settings.py: IMMEDIATE и ожидание до 20 с."""
    from django.conf import settings

    db = settings.DATABASES["default"]
    if "sqlite" not in db["ENGINE"]:
        pytest.skip("настройка нужна только для SQLite")
    assert db["OPTIONS"]["transaction_mode"] == "IMMEDIATE"
    assert db["OPTIONS"]["timeout"] == 20
