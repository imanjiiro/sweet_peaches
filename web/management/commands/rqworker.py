"""python manage.py rqworker — запуск воркера очереди (заезд 2). Требует Redis (docker compose up redis)."""
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Воркер очереди задач RQ"

    def handle(self, *args, **options):
        from redis import Redis
        from rq import Worker

        conn = Redis.from_url(settings.REDIS_URL)
        self.stdout.write(f"Воркер слушает очередь 'calc' на {settings.REDIS_URL}")
        Worker(["calc"], connection=conn).work()
