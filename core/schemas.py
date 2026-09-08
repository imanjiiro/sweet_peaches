"""
Контракт ядра: что принимаем на вход, что отдаём на выход.
Валидация входа — ДО запуска расчёта (занятие 11): плохие данные не должны доходить до численного метода.
"""
from pydantic import BaseModel, Field, field_validator

# Разрешённые функции — фиксированный список, а не eval() строки от пользователя (занятие 14: безопасность).
FUNCTIONS = ["sin", "cos", "exp", "x2", "sqrt", "gauss"]


class IntegrateParams(BaseModel):
    function: str = Field(description="Одна из: " + ", ".join(FUNCTIONS))
    a: float = Field(description="Левая граница")
    b: float = Field(description="Правая граница")
    n: int = Field(default=1000, ge=2, le=50_000_000, description="Число разбиений (чётное)")
    method: str = Field(default="simpson", description="trapezoid | simpson")

    @field_validator("function")
    @classmethod
    def _check_function(cls, v: str) -> str:
        if v not in FUNCTIONS:
            raise ValueError(f"Неизвестная функция '{v}'. Допустимо: {', '.join(FUNCTIONS)}")
        return v

    @field_validator("method")
    @classmethod
    def _check_method(cls, v: str) -> str:
        if v not in ("trapezoid", "simpson"):
            raise ValueError("method должен быть 'trapezoid' или 'simpson'")
        return v

    @field_validator("n")
    @classmethod
    def _even(cls, v: int) -> int:
        return v if v % 2 == 0 else v + 1


class IntegrateResult(BaseModel):
    value: float
    error_estimate: float
    method: str
    n: int
    core_version: str
    points: list[list[float]] = Field(description="Выборка [x, f(x)] для графика (не более 200 точек)")
