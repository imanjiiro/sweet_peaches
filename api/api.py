"""
REST API на Django Ninja (занятие 8). Документация: /api/docs (Swagger UI), схема: /api/openapi.json.
Ресурс — задача: POST /api/tasks -> 202 Accepted (расчёт «принят», см. занятие 2 про 200 vs 202).
Описание адресов и кодов ответа: docs/api.md.
"""
from typing import Any

from ninja import NinjaAPI, Schema
from ninja.responses import Status
from ninja.security import django_auth
from pydantic import Field

from web import services
from web.models import Task

# auth=django_auth: API только после входа (cookie входа едет из того же браузера, в /api/docs тоже).
# Без входа ответ 401. django_auth проверяет и CSRF-токен для запросов, меняющих данные.
api = NinjaAPI(
    title="Hospital Flow Simulation API",
    version="1.0",
    description="Симуляция очереди приёмного отделения: создать расчёт, узнать статус, получить результат",
    auth=django_auth,
)


class TaskIn(Schema):
    name: str = Field(min_length=1, max_length=200)  # как Task.name; слишком длинное имя -> 422
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
    from core.schemas import SimulationParams  # валидируем ДО создания задачи

    try:
        SimulationParams.model_validate(payload.params)
    except Exception as exc:  # noqa: BLE001
        return Status(422, {"detail": str(exc)})
    task = services.create_task(payload.name, payload.params, owner=request.user)
    return Status(202, task)


@api.get("/tasks", response=list[TaskOut], summary="Список своих задач")
def list_tasks(request, status: str | None = None):
    qs = services.list_tasks(request.user)
    if status:
        qs = qs.filter(status=status)
    return qs[:100]


@api.get("/tasks/{task_id}", response=TaskOut, summary="Статус задачи")
def get_task(request, task_id: int):
    # Чужая задача -> 404 (то же правило, что на странице: web/services.py, get_task; ADR-004)
    return services.get_task(request.user, task_id)


@api.get("/tasks/{task_id}/result", response={200: ResultOut, 409: ErrorOut}, summary="Результат задачи")
def get_result(request, task_id: int):
    task = services.get_task(request.user, task_id)
    if task.status != Task.Status.DONE:
        return Status(409, {"detail": f"Задача ещё не завершена: статус {task.status}"})
    return Status(200, task)
