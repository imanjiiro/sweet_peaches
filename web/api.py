import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from web import services
from web.models import Task


def validate_params(params: dict) -> bool:
    if not isinstance(params, dict):
        return False

    doctors = params.get("doctors")
    if doctors is None or not isinstance(doctors, int) or doctors <= 0:
        return False

    strategy = params.get("strategy")
    if strategy not in ["fifo", "lifo", "priority"]:
        return False

    arrival_rate = params.get("arrival_rate")
    if arrival_rate is not None and (not isinstance(arrival_rate, (int, float)) or arrival_rate <= 0):
        return False

    horizon_min = params.get("horizon_min")
    if horizon_min is not None:
        if not isinstance(horizon_min, (int, float)) or horizon_min <= 0 or horizon_min > 1440.0:
            return False

    return True


def task_list_create_api(request):
    if not request.user.is_authenticated:
        if request.method == "GET":
            return JsonResponse([], safe=False)
        return JsonResponse({"error": "Unauthorized"}, status=401)

    if request.method == "GET":
        tasks = list(Task.objects.filter(owner=request.user).values("id", "name", "status"))
        return JsonResponse(tasks, safe=False)

    elif request.method == "POST":
        try:
            data = json.loads(request.body)
            name = data.get("name")
            params = data.get("params", {})

            if not name or not validate_params(params):
                return JsonResponse({"error": "Invalid parameters"}, status=422)

            task = services.create_task(
                name=name,
                params=params,
                owner=request.user,
            )

            return JsonResponse({
                "id": task.id,
                "name": task.name,
                "status": getattr(task, "status", "done")
            }, status=202)

        except (json.JSONDecodeError, AttributeError):
            return JsonResponse({"error": "Invalid JSON"}, status=422)

    return JsonResponse({"error": "Method not allowed"}, status=405)


def task_detail_api(request, pk: int):
    # Возвращаем 404, если не авторизован или задача не принадлежит пользователю
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Not found"}, status=404)

    task = get_object_or_404(Task, pk=pk, owner=request.user)
    return JsonResponse({
        "id": task.id,
        "name": task.name,
        "status": getattr(task, "status", None)
    })


def task_result_api(request, pk: int):
    # Возвращаем 404, если не авторизован или задача не принадлежит пользователю
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Not found"}, status=404)

    task = get_object_or_404(Task, pk=pk, owner=request.user)
    
    result_data = getattr(task, "result", {}) or {}
    return JsonResponse({"result": result_data}, status=200)