"""
web/models.py

Модели соответствуют docs/ER.md, поля названы так же, как в
HospitalParams (core-схема параметров, занятие 3, слайд "API:
Больница") — форма, API и модель используют одни и те же имена
осознанно (см. "Работа 2: API", пункт 2 — разные имена были бы
источником половины ошибок на защите).

Большие данные (сотни/тысячи точек для графика очереди во времени) в
эти таблицы НЕ пишутся — см. docs/ER.md, раздел «Где большие данные».
"""
import uuid

from django.db import models


class Strategy(models.TextChoices):
    FIFO = "fifo", "FIFO"
    PRIORITY = "priority", "Приоритетная"
    DYNAMIC = "dynamic", "Динамическая"


class RunStatus(models.TextChoices):
    QUEUED = "queued", "В очереди"
    RUNNING = "running", "Считается"
    DONE = "done", "Готово"
    FAILED = "failed", "Ошибка"


class SimulationRun(models.Model):
    """Один запуск симуляции с заданными параметрами больницы."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    doctors = models.PositiveIntegerField("Количество врачей")
    arrival_rate = models.FloatField("Поток пациентов, чел/мин")
    service_mean = models.FloatField("Среднее время приёма, мин")
    horizon_min = models.PositiveIntegerField("Горизонт смены, мин", default=480)
    strategy = models.CharField(
        "Стратегия", max_length=16, choices=Strategy.choices, default=Strategy.FIFO
    )
    n_runs = models.PositiveIntegerField("Число прогонов", default=10)
    seed = models.IntegerField("Зерно ГПСЧ", null=True, blank=True)

    status = models.CharField(
        "Статус", max_length=16, choices=RunStatus.choices, default=RunStatus.QUEUED
    )
    error_message = models.TextField("Ошибка расчёта", blank=True, default="")
    duration_seconds = models.FloatField(
        "Время расчёта, с", null=True, blank=True
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Прогон симуляции"
        verbose_name_plural = "Прогоны симуляции"

    def __str__(self) -> str:
        return f"Run {self.id} ({self.strategy}, {self.status})"


class SimulationResult(models.Model):
    """Метрики завершённого прогона. До завершения расчёта не существует."""

    run = models.OneToOneField(
        SimulationRun, on_delete=models.CASCADE, related_name="result"
    )

    avg_wait_time = models.FloatField("Среднее ожидание, мин", null=True, blank=True)
    max_wait_time = models.FloatField("Макс. ожидание, мин", null=True, blank=True)
    avg_queue_length = models.FloatField("Средняя очередь, чел", null=True, blank=True)
    doctor_utilization = models.FloatField("Загрузка врачей", null=True, blank=True)
    patients_served = models.PositiveIntegerField(
        "Обслужено пациентов", null=True, blank=True
    )

    class Meta:
        verbose_name = "Результат симуляции"
        verbose_name_plural = "Результаты симуляции"

    def __str__(self) -> str:
        return f"Result for run {self.run_id}"
