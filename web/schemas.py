"""
web/schemas.py

Схемы запросов и ответов для web/api.py. Валидация входных данных
происходит здесь, до того как параметры попадают в модель.

HospitalParams — те же имена и границы, что на слайде "API: Больница"
(занятие 3): doctors (1..20), arrival_rate (чел/мин), service_mean,
horizon_min (смена, по умолчанию 480 мин), strategy (только
fifo/priority/dynamic — иначе 422), n_runs (1..1000), seed, и
необязательный patients — готовый список пациентов для детерминированных
тестов (см. слайд "Тонкость": если он передан, ядро считает по нему, а
не генерирует поток по arrival_rate/seed).
"""
from datetime import datetime
from uuid import UUID

from ninja import Field, Schema

from .models import RunStatus, Strategy


class HospitalParams(Schema):
    doctors: int = Field(ge=1, le=20)
    arrival_rate: float = Field(gt=0)  # пациентов в минуту
    service_mean: float = Field(gt=0)  # среднее время приёма, мин
    horizon_min: int = Field(default=480, ge=10)  # смена 8 часов
    strategy: str = Field(default="fifo", pattern=r"^(fifo|priority|dynamic)$")
    n_runs: int = Field(default=10, ge=1, le=1000)  # прогонов
    seed: int | None = None
    patients: list[tuple[float, str]] | None = None  # готовый список — для теста


class TaskIn(Schema):
    params: HospitalParams


class SimulationResultOut(Schema):
    avg_wait_time: float | None = None
    max_wait_time: float | None = None
    avg_queue_length: float | None = None
    doctor_utilization: float | None = None
    patients_served: int | None = None


class SimulationRunOut(Schema):
    task_id: UUID
    created_at: datetime
    doctors: int
    arrival_rate: float
    service_mean: float
    horizon_min: int
    strategy: Strategy
    n_runs: int
    seed: int | None
    status: RunStatus
    error_message: str
    duration_seconds: float | None = None
    result: SimulationResultOut | None = None

    @staticmethod
    def resolve_task_id(obj):
        return obj.id
