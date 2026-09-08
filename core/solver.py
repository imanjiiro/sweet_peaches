"""
Пример вычислительного ядра: численное интегрирование на [a, b].

Это ЗАГОТОВКА. Команда заменяет её на свой метод (ОДУ, оптимизация, Монте-Карло, СЛАУ, ...),
сохраняя контракт run(params) -> dict и тесты на эталонных задачах (core/tests/).

Метод намеренно написан на чистом Python без numpy: при большом n он считается секунды —
это нужно, чтобы на заезде 2 очередь задач имела смысл. Ускорение через numpy — «расширение».
"""
import math
import time

from core.schemas import IntegrateParams, IntegrateResult

VERSION = "0.1.0"  # версия ядра хранится рядом с результатом (занятие 11: воспроизводимость)

_FUNCS = {
    "sin": math.sin,
    "cos": math.cos,
    "exp": math.exp,
    "x2": lambda x: x * x,
    "sqrt": lambda x: math.sqrt(x) if x >= 0 else float("nan"),
    "gauss": lambda x: math.exp(-x * x),
}


def _trapezoid(f, a, b, n):
    h = (b - a) / n
    s = 0.5 * (f(a) + f(b))
    for i in range(1, n):
        s += f(a + i * h)
    return s * h


def _simpson(f, a, b, n):
    h = (b - a) / n
    s = f(a) + f(b)
    for i in range(1, n):
        s += (4 if i % 2 else 2) * f(a + i * h)
    return s * h / 3


def run(params: dict) -> dict:
    """Единственная точка входа ядра. Вход и выход — обычные dict (JSON-совместимые)."""
    p = IntegrateParams.model_validate(params)  # ошибка валидации = понятное сообщение, а не Traceback
    f = _FUNCS[p.function]
    method = _simpson if p.method == "simpson" else _trapezoid

    started = time.perf_counter()
    value = method(f, p.a, p.b, p.n)
    # Оценка погрешности по правилу Рунге: сравниваем с вдвое более грубой сеткой.
    coarse = method(f, p.a, p.b, max(2, p.n // 2))
    order = 4 if p.method == "simpson" else 2
    error_estimate = abs(value - coarse) / (2**order - 1)
    elapsed = time.perf_counter() - started

    k = max(1, p.n // 200)
    points = [[p.a + i * (p.b - p.a) / p.n, f(p.a + i * (p.b - p.a) / p.n)] for i in range(0, p.n + 1, k)]

    result = IntegrateResult(value=value, error_estimate=error_estimate, method=p.method, n=p.n,
                             core_version=VERSION, points=points)
    out = result.model_dump()
    out["elapsed_sec"] = round(elapsed, 4)
    return out
