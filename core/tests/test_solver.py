"""
Тесты ядра на ЭТАЛОНАХ: задачи с известным точным ответом. Без Django, без БД, без HTTP.
Замените на эталоны своей задачи (аналитическое решение, справочные значения, sympy).
"""
import math

import pytest

from core import run
from core.schemas import FUNCTIONS


def test_sin_on_0_pi_equals_2():
    r = run({"function": "sin", "a": 0, "b": math.pi, "n": 1000})
    assert abs(r["value"] - 2.0) < 1e-6


def test_x2_on_0_1_equals_one_third():
    r = run({"function": "x2", "a": 0, "b": 1, "n": 100, "method": "trapezoid"})
    assert abs(r["value"] - 1 / 3) < 1e-4


def test_error_estimate_is_small_and_positive():
    r = run({"function": "exp", "a": 0, "b": 1, "n": 200})
    assert 0 <= r["error_estimate"] < 1e-6


def test_unknown_function_is_rejected_before_compute():
    with pytest.raises(ValueError):
        run({"function": "__import__('os')", "a": 0, "b": 1})


def test_points_are_limited_for_plot():
    r = run({"function": "cos", "a": 0, "b": 1, "n": 100_000})
    assert len(r["points"]) <= 202


def test_all_functions_run():
    for fn in FUNCTIONS:
        run({"function": fn, "a": 0.1, "b": 1, "n": 10})
