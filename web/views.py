from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render

from web import services
from web.forms import TaskForm


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


@login_required
def task_detail(request, pk: int):
    # Ищем по номеру И владельцу: чужая задача -> 404, то же правило, что в API (api/api.py, ADR-004)
    task = services.get_task(request.user, pk)
    return render(request, "web/detail.html", {"task": task})


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