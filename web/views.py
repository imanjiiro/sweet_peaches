from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from web import services
from web.forms import TaskForm
from web.models import Task


def task_list(request):
    if request.user.is_authenticated:
        tasks = Task.objects.filter(owner=request.user)[:50]
    else:
        # Для неавторизованных пользователей показываем только анонимные задачи
        tasks = Task.objects.filter(owner__isnull=True)[:50]
    return render(request, "web/list.html", {"tasks": tasks})


def task_create(request):
    form = TaskForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        owner = request.user if request.user.is_authenticated else None
        task = services.create_task(form.cleaned_data["name"], form.params(), owner=owner)
        return redirect("task_detail", pk=task.pk)
    return render(request, "web/form.html", {"form": form})


def task_detail(request, pk: int):
    task = get_object_or_404(Task, pk=pk)
    
    # Проверка прав доступа: если у задачи есть владелец, просматривать её может только он
    if task.owner and task.owner != request.user:
        raise PermissionDenied("У вас нет доступа к этой задаче.")
        
    return render(request, "web/detail.html", {"task": task})