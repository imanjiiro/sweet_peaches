"""
ЗАГОТОВКА ДЛЯ ЗАНЯТИЯ 7: «толстая» view. НЕ подключена к urls. Задание — отрефакторить:
вынести расчёт в core/, логику статусов — в services.py, оставить во view только HTTP.
Найдите здесь минимум 5 архитектурных проблем.
"""
import math

from django.http import JsonResponse

from web.models import Task


def fat_integrate(request):
    fn = request.GET.get("f", "sin")
    a = float(request.GET.get("a", 0))
    b = float(request.GET.get("b", 3.14))
    n = int(request.GET.get("n", 1000))
    f = eval(fn, {"sin": math.sin, "cos": math.cos})  # noqa: S307 — да, это уязвимость. Специально.
    h = (b - a) / n
    s = 0.5 * (f(a) + f(b))
    for i in range(1, n):
        s += f(a + i * h)
    value = s * h
    t = Task(name="fat", params={"f": fn}, status="done", result={"value": value})
    t.save()
    return JsonResponse({"value": value, "id": t.id})
