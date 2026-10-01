from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from web import services
from web.forms import TaskForm
from web.models import Task


@login_required
def task_list(request):
    # Каждая учетка видит только свои задачи
    tasks = Task.objects.filter(owner=request.user)[:50]
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
    task = get_object_or_404(Task, pk=pk)
    
    # Проверка прав: суперпользователь или владелец задачи
    if task.owner and task.owner != request.user and not request.user.is_superuser:
        raise PermissionDenied("У вас нет доступа к этой задаче.")
        
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