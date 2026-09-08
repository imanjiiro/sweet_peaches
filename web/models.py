from django.conf import settings
from django.db import models


class Task(models.Model):
    class Status(models.TextChoices):
        CREATED = "created", "Создана"
        QUEUED = "queued", "В очереди"
        RUNNING = "running", "Считается"
        DONE = "done", "Готово"
        FAILED = "failed", "Ошибка"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tasks",
        null=True,
        blank=True,
    )
    name = models.CharField("Название", max_length=200, default="Симуляция больницы")
    params = models.JSONField("Параметры", default=dict)
    status = models.CharField(
        "Статус", max_length=16, choices=Status.choices, default=Status.CREATED
    )
    result = models.JSONField("Результат", null=True, blank=True)
    result_file = models.FileField(
        "Файл результата", upload_to="results/", null=True, blank=True
    )
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


class PatientLog(models.Model):
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name="patients", null=True, blank=True
    )
    patient_number = models.IntegerField("Номер пациента")
    priority = models.IntegerField("Приоритет", default=1)
    arrival_time = models.FloatField("Время прихода")
    start_service_time = models.FloatField("Начало приема", null=True, blank=True)
    wait_time = models.FloatField("Время ожидания", null=True, blank=True)