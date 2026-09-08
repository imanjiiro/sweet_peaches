from django.conf import settings
from django.db import models


class Task(models.Model):
    """
    Расчётная задача. Модель данных проекта — см. занятие 7.
    Параметры и результат хранятся как JSON: для учебной заготовки достаточно.
    Большие массивы (тысячи точек, файлы) в JSON-поле класть НЕЛЬЗЯ — для них есть result_file (MEDIA_ROOT).
    """

    class Status(models.TextChoices):
        CREATED = "created", "Создана"
        QUEUED = "queued", "В очереди"
        RUNNING = "running", "Считается"
        DONE = "done", "Готово"
        FAILED = "failed", "Ошибка"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tasks",
                              null=True, blank=True)  # заезд 2: станет обязательным (занятие 13)
    name = models.CharField("Название", max_length=200)
    params = models.JSONField("Параметры", default=dict)
    status = models.CharField("Статус", max_length=16, choices=Status.choices, default=Status.CREATED)
    result = models.JSONField("Результат", null=True, blank=True)
    result_file = models.FileField("Файл результата", upload_to="results/", null=True, blank=True)
    error = models.TextField("Ошибка", blank=True)
    core_version = models.CharField("Версия ядра", max_length=32, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "задача"
        verbose_name_plural = "задачи"

    def __str__(self) -> str:
        return f"#{self.pk} {self.name} [{self.status}]"
