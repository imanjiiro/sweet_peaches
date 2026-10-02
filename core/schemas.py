"""
Контракт ядра: что принимаем на вход, что отдаём на выход.
Валидация входа — ДО запуска расчёта: плохие данные не должны доходить до алгоритма симуляции.
"""

from pydantic import BaseModel, Field, field_validator

# Разрешённые стратегии обслуживания
STRATEGIES = ["fifo", "priority", "dynamic"]

# Границы входа («не больше»): один запрос не должен занимать сервер надолго.
# Проверяются ДО расчёта; форма (web/forms.py) берёт те же числа отсюда.
MAX_DOCTORS = 20
MAX_ARRIVAL_RATE = 10.0  # не больше 10 пациентов в минуту
MAX_SERVICE_MEAN = 240.0  # приём в среднем не дольше 4 часов (в минутах)
MAX_HORIZON_MIN = 1440.0  # смена не длиннее суток (в минутах)


class PatientInput(BaseModel):
    """Описание одного пациента (для детерминированных тестов)."""
    id: int = Field(gt=0, description="Уникальный ID пациента")
    arrival_time: float = Field(ge=0, description="Время прихода (в минутах от начала смены)")
    service_time: float = Field(gt=0, description="Время обслуживания врачом (в минутах)")
    priority: int = Field(default=1, ge=1, le=3, description="1 - плановый, 2 - срочный, 3 - критический")


class SimulationParams(BaseModel):
    """Параметры запуска симуляции больницы."""
    doctors: int = Field(default=1, ge=1, le=MAX_DOCTORS, description="Количество врачей/кабинетов")
    arrival_rate: float = Field(
        default=1.0, gt=0, le=MAX_ARRIVAL_RATE, description="Интенсивность поступления пациентов (чел/мин)"
    )
    service_mean: float = Field(default=5.0, gt=0, le=MAX_SERVICE_MEAN, description="Среднее время обслуживания (мин)")
    horizon_min: float = Field(
        default=480.0, gt=0, le=MAX_HORIZON_MIN, description="Длина смены в минутах (по умолчанию 8 часов = 480 мин)"
    )
    n_runs: int = Field(default=500, ge=1, le=1000, description="Количество прогонов для усреднения")
    strategy: str = Field(default="fifo", description="Стратегия обслуживания: fifo | priority | dynamic")
    seed: int | None = Field(default=None, description="Зерно генератора случайных чисел для воспроизводимости")
    
    # Для детерминированных тестов (если передаем готовый список пациентов)
    patients: list[PatientInput] | None = Field(
        default=None, description="Фиксированный список пациентов (опционально)"
    )

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