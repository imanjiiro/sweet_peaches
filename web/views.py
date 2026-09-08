from django.shortcuts import get_object_or_404, redirect, render

from web import services
from web.forms import TaskForm
from web.models import Task


def task_list(request):
    tasks = Task.objects.all()[:50]
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
    return render(request, "web/detail.html", {"task": task})
