"""
ЗАЕЗД 2 (занятия 11–12): очередь задач на RQ + Redis.
Включается флагом USE_QUEUE=1 в .env. Воркер: `python manage.py rqworker` — см. web/management/commands/rqworker.py.
"""
from django.conf import settings


def get_queue():
    from redis import Redis
    from rq import Queue

    return Queue("calc", connection=Redis.from_url(settings.REDIS_URL))


def enqueue_task(task_id: int) -> None:
    from web.models import Task

    Task.objects.filter(pk=task_id).update(status=Task.Status.QUEUED)
    get_queue().enqueue("web.services.execute_task", task_id, job_timeout=600)
