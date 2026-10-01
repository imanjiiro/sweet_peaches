from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from web.models import Task


def task_list_create_api(request):
    if request.method == "GET":
        tasks = list(Task.objects.filter(owner=request.user).values("id", "name", "status"))
        return JsonResponse(tasks, safe=False)
    
    return JsonResponse({"error": "Method not allowed"}, status=405)


def task_detail_api(request, pk: int):
    task = get_object_or_404(Task, pk=pk, owner=request.user)
    return JsonResponse({
        "id": task.id,
        "name": task.name,
        "status": getattr(task, "status", None)
    })