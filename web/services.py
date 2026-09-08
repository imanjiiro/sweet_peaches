"""
Сервисный слой (занятие 7): прикладная логика между views/API и ядром.
Views и API не вызывают core напрямую и не меняют статусы задач сами — только через сервисы.
"""
from django.conf import settings
from django.utils import timezone

from core import VERSION, run
from web.models import Task
import threading


def create_task(name: str, params: dict, owner=None) -> Task:
    task = Task.objects.create(name=name, params=params, owner=owner)
    
    if settings.USE_QUEUE:
        from web.jobs import enqueue_task
        enqueue_task(task.pk)
    else:
        # Запускаем execute_task в отдельном фоновом потоке!
        # Теперь HTTP-запрос завершится МГНОВЕННО, а расчет продолжится на фоне.
        thread = threading.Thread(target=execute_task, args=(task.pk,))
        thread.daemon = True
        thread.start()

    return task


def execute_task(task_id: int) -> None:
    """Выполняет расчёт. Вызывается синхронно (заезд 1) или воркером очереди (заезд 2)."""
    task = Task.objects.get(pk=task_id)
    task.status = Task.Status.RUNNING
    task.save(update_fields=["status"])
    try:
        result = run(task.params)
        task.result = result
        task.core_version = result.get("core_version", VERSION)
        task.status = Task.Status.DONE
    except Exception as exc:  # noqa: BLE001 — граница слоя: ошибка ядра превращается в статус, а не в 500
        task.error = str(exc)
        task.status = Task.Status.FAILED
    task.finished_at = timezone.now()
    task.save()
