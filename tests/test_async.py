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