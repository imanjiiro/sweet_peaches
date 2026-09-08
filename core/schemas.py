"""
Контракт ядра: что принимаем на вход, что отдаём на выход.
Валидация входа — ДО запуска расчёта: плохие данные не должны доходить до алгоритма симуляции.
"""
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator

# Разрешённые стратегии обслуживания
STRATEGIES = ["fifo", "priority", "dynamic"]


class PatientInput(BaseModel):
    """Описание одного пациента (для детерминированных тестов)."""
    id: int = Field(gt=0, description="Уникальный ID пациента")
    arrival_time: float = Field(ge=0, description="Время прихода (в минутах от начала смены)")
    service_time: float = Field(gt=0, description="Время обслуживания врачом (в минутах)")
    priority: int = Field(default=1, ge=1, le=3, description="1 - плановый, 2 - срочный, 3 - критический")


class SimulationParams(BaseModel):
    """Параметры запуска симуляции больницы."""
    doctors: int = Field(default=1, ge=1, le=20, description="Количество врачей/кабинетов")
    arrival_rate: float = Field(default=1.0, gt=0, description="Интенсивность поступления пациентов (чел/мин)")
    service_mean: float = Field(default=5.0, gt=0, description="Среднее время обслуживания (мин)")
    horizon_min: float = Field(default=480.0, gt=0, description="Длина смены в минутах (по умолчанию 8 часов = 480 мин)")
    n_runs: int = Field(default=1, ge=1, le=1000, description="Количество прогонов для усреднения")
    strategy: str = Field(default="fifo", description="Стратегия обслуживания: fifo | priority | dynamic")
    seed: Optional[int] = Field(default=None, description="Зерно генератора случайных чисел для воспроизводимости")
    
    # Для детерминированных тестов (если передаем готовый список пациентов)
    patients: Optional[list[PatientInput]] = Field(default=None, description="Фиксированный список пациентов (опционально)")

    @field_validator("strategy")
    @classmethod
    def _check_strategy(cls, v: str) -> str:
        v_clean = v.lower().strip()
        if v_clean not in STRATEGIES:
            raise ValueError(f"Неизвестная стратегия '{v}'. Допустимо: {', '.join(STRATEGIES)}")
        return v_clean


class SimulationResult(BaseModel):
    """Результаты выполнения симуляции."""
    average_wait_time: float = Field(description="Среднее время ожидания пациентов (в минутах)")
    max_wait_time: float = Field(description="Максимальное время ожидания (в минутах)")
    average_queue_length: float = Field(description="Средняя длина очереди")
    doctor_utilization: float = Field(description="Процент/коэффициент загрузки врачей (0.0 - 1.0)")
    served_patients_count: int = Field(description="Количество обслуженных пациентов")
    wait_times: list[float] = Field(default=[], description="Список задержек для каждого пациента")
    core_version: str = Field(default="1.0.0", description="Версия алгоритма ядра")