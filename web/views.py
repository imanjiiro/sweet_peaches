from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render

from web import services
from web.forms import STRATEGY_LABELS, TaskForm


@login_required
def task_list(request):
    # Каждая учётка видит только свои задачи (одно правило со страницей и API: web/services.py)
    tasks = services.list_tasks(request.user)[:50]
    return render(request, "web/list.html", {"tasks": tasks})


@login_required
def task_create(request):
    form = TaskForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        task = services.create_task(
            form.cleaned_data["name"], 
            form.params(), 
            owner=request.user
        )
        return redirect("task_detail", pk=task.pk)
    return render(request, "web/form.html", {"form": form})


PRIORITY_LABELS = {1: "Плановые", 2: "Срочные", 3: "Критические"}


def _params_rows(params: dict) -> list[tuple[str, str]]:
    """Параметры запуска для таблицы: русские подписи вместо ключей словаря Python."""
    rows = []
    if "doctors" in params:
        rows.append(("Количество врачей", str(params["doctors"])))
    if "strategy" in params:
        rows.append(("Стратегия очереди", STRATEGY_LABELS.get(params["strategy"], params["strategy"])))
    if "arrival_rate" in params:
        rows.append(("Интенсивность прихода, пациентов/мин", _num(params["arrival_rate"])))
    if "service_mean" in params:
        rows.append(("Среднее время приёма, мин", _num(params["service_mean"])))
    if "horizon_min" in params:
        rows.append(("Длительность смены, мин", _num(params["horizon_min"])))
    if params.get("n_runs"):
        rows.append(("Число прогонов", str(params["n_runs"])))
    if params.get("seed") is not None:
        rows.append(("Зерно генератора (seed)", str(params["seed"])))
    if params.get("patients"):
        rows.append(("Заданный список пациентов", f"{len(params['patients'])} чел."))
    return rows


def _num(value) -> str:
    """Число без хвоста вида 0,7083333333: до 2 знаков, лишние нули убираем."""
    return f"{value:.2f}".rstrip("0").rstrip(".").replace(".", ",")


def _priority_rows(result: dict) -> list[dict]:
    """Ожидание по срочности для таблицы (у старых результатов этого поля нет — тогда таблицы не будет)."""
    return [
        {**row, "label": PRIORITY_LABELS.get(row["priority"], str(row["priority"]))}
        for row in result.get("wait_by_priority") or []
    ]


@login_required
def task_detail(request, pk: int):
    # Ищем по номеру И владельцу: чужая задача -> 404, то же правило, что в API (api/api.py, ADR-004)
    task = services.get_task(request.user, pk)
    context = {
        "task": task,
        "params_rows": _params_rows(task.params),
        "priority_rows": _priority_rows(task.result or {}),
        "utilization_percent": round((task.result or {}).get("doctor_utilization", 0) * 100),
    }
    return render(request, "web/detail.html", context)


def signup(request):
    """Регистрация нового пользователя."""
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("task_list")
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})