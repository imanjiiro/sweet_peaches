"""
Сервисный слой (занятие 7): прикладная логика между views/API и ядром.
Views и API не вызывают core напрямую и не меняют статусы задач сами — только через сервисы.
"""
import sys
import threading
from django.conf import settings
from django.utils import timezone

from core import VERSION, run
from web.models import Task


def create_task(name: str, params: dict, owner=None) -> Task:
    task = Task.objects.create(name=name, params=params, owner=owner)

    # В тестах ВСЕГДА выполняем синхронно, чтобы не забивать транзакции SQLite
    is_testing = (
        getattr(settings, "TESTING", False)
        or "pytest" in sys.modules
        or any("test" in arg for arg in sys.argv)
    )

    if settings.USE_QUEUE:
        from web.jobs import enqueue_task
        enqueue_task(task.pk)
    elif is_testing:
        execute_task(task.pk)
    else:
        thread = threading.Thread(target=execute_task, args=(task.pk,))
        thread.daemon = True
        thread.start()

    return task


def execute_task(task_id: int) -> None:
    """Выполняет расчёт. Вызывается синхронно (в тестах) или асинхронно."""
    task = Task.objects.get(pk=task_id)
    task.status = Task.Status.RUNNING
    task.save(update_fields=["status"])
    try:
        result = run(task.params)
        task.result = result
        task.core_version = result.get("core_version", VERSION)
        task.status = Task.Status.DONE
    except Exception as exc:  # noqa: BLE001 — граница слоя
        task.error = str(exc)
        task.status = Task.Status.FAILED
    task.finished_at = timezone.now()
    task.save()