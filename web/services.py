"""
Сервисный слой (занятие 7): прикладная логика между views/API и ядром.
Views и API не вызывают core напрямую и не меняют статусы задач сами — только через сервисы.
"""
import sys
import threading
from django.conf import settings
from django.db import connections, transaction
from django.utils import timezone

from core import VERSION, run
from web.models import Task


def create_task(name: str, params: dict, owner=None, async_exec: bool | None = None) -> Task:
    task = Task.objects.create(name=name, params=params, owner=owner)

    # Определяем, нужен ли синхронный запуск в тестах по умолчанию, 
    # если флаг async_exec не передан явно
    is_testing = (
        getattr(settings, "TESTING", False)
        or "pytest" in sys.modules
        or any("test" in arg for arg in sys.argv)
    )

    if settings.USE_QUEUE:
        from web.jobs import enqueue_task
        enqueue_task(task.pk)
    else:
        if async_exec is None:
            async_exec = not is_testing

        if async_exec:
            thread = threading.Thread(target=execute_task, args=(task.pk,))
            thread.daemon = True
            thread.start()
        else:
            execute_task(task.pk)

    return task


def execute_task(task_id: int) -> None:
    """Выполняет расчёт. Вызывается синхронно или в фоновом потоке threading.Thread."""
    connections.close_all()
    task = None
    try:
        with transaction.atomic():
            task = Task.objects.get(pk=task_id)
            task.status = Task.Status.RUNNING
            task.save(update_fields=["status"])

        result = run(task.params)

        with transaction.atomic():
            task.refresh_from_db()
            task.result = result
            task.core_version = result.get("core_version", VERSION)
            task.status = Task.Status.DONE
            task.finished_at = timezone.now()
            task.save()
    except Exception as exc:  # noqa: BLE001 — граница слоя
        if task is None:
            try:
                task = Task.objects.get(pk=task_id)
            except Exception:  # noqa: BLE001
                pass
        if task:
            with transaction.atomic():
                task.error = str(exc)
                task.status = Task.Status.FAILED
                task.finished_at = timezone.now()
                task.save()
    finally:
        connections.close_all()