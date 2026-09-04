"""
web/views.py

Форма создаёт задачу (SimulationRun) и запускает расчёт В ФОНЕ через
web/services.execute_run_async — вьюха НЕ содержит логики расчёта (см.
AGENTS.md, ограничение 2) и не ждёт её завершения: сохранила форму,
отправила задачу в фоновый поток, сразу же отдала редирект на список
(galочка 7 "Фон + измерение"). Статус на странице /runs/ меняется
queued -> running -> done по ходу расчёта — обновите страницу ещё раз,
чтобы увидеть готовый результат.
"""
from django.shortcuts import redirect, render

from .forms import SimulationRunForm
from .models import SimulationRun
from .services import execute_run_async


def form_view(request):
    """Страница '/' — форма запуска новой симуляции."""
    if request.method == "POST":
        form = SimulationRunForm(request.POST)
        if form.is_valid():
            run = form.save()  # status по умолчанию = "queued" (см. models.py)
            execute_run_async(run)  # считаем в фоне, не блокируя ответ
            return redirect("web:list")
    else:
        form = SimulationRunForm()
    return render(request, "web/form.html", {"form": form})


def list_view(request):
    """Страница '/runs/' — список всех созданных прогонов."""
    runs = SimulationRun.objects.select_related("result").all()
    return render(request, "web/list.html", {"runs": runs})
