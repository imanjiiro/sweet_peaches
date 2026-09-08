"""
REST API на Django Ninja (занятие 8). Документация: /api/docs (Swagger UI), схема: /api/openapi.json.
Ресурс — задача: POST /api/tasks -> 202 Accepted (расчёт «принят», см. занятие 2 про 200 vs 202).
"""
from typing import Any

from django.shortcuts import get_object_or_404
from ninja import NinjaAPI, Schema
from ninja.responses import Status

from web import services
from web.models import Task

api = NinjaAPI(title="Calc Service API", version="1.0", description="Учебный вычислительный сервис")


class TaskIn(Schema):
    name: str
    params: dict[str, Any]


class TaskOut(Schema):
    id: int
    name: str
    status: str
    core_version: str
    error: str


class ResultOut(Schema):
    id: int
    status: str
    result: dict[str, Any] | None


class ErrorOut(Schema):
    detail: str


@api.post("/tasks", response={202: TaskOut, 422: ErrorOut}, summary="Создать задачу (поставить расчёт)")
def create_task(request, payload: TaskIn):
    from core.schemas import IntegrateParams  # валидируем ДО создания задачи

    try:
        IntegrateParams.model_validate(payload.params)
    except Exception as exc:  # noqa: BLE001
        return Status(422, {"detail": str(exc)})
    owner = request.user if request.user.is_authenticated else None
    task = services.create_task(payload.name, payload.params, owner=owner)
    return Status(202, task)


@api.get("/tasks", response=list[TaskOut], summary="Список задач")
def list_tasks(request, status: str | None = None):
    qs = Task.objects.all()
    if status:
        qs = qs.filter(status=status)
    return qs[:100]


@api.get("/tasks/{task_id}", response=TaskOut, summary="Статус задачи")
def get_task(request, task_id: int):
    return get_object_or_404(Task, pk=task_id)


@api.get("/tasks/{task_id}/result", response={200: ResultOut, 409: ErrorOut}, summary="Результат задачи")
def get_result(request, task_id: int):
    task = get_object_or_404(Task, pk=task_id)
    if task.status != Task.Status.DONE:
        return Status(409, {"detail": f"Задача ещё не завершена: статус {task.status}"})
    return Status(200, task)
