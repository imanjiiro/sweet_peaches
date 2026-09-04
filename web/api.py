"""
web/api.py

JSON API поверх тех же моделей и того же сервисного слоя, что использует
веб-форма (web/views.py + web/services.py) — см. "Работа 2: API".

POST /api/tasks   — создать задачу и ЗАПУСТИТЬ расчёт в фоне (galочка 7),
                    202 + task_id сразу, не дожидаясь результата: в
                    момент ответа статус обычно ещё "queued" или
                    "running" (фоновый поток мог и успеть — для очень
                    маленьких n_runs это не страшно, семантика 202
                    "принято в обработку" всё равно верна).
GET  /api/tasks/{id}         — прогон целиком (параметры + статус + результат).
GET  /api/tasks/{id}/result  — только результат (пустой, пока прогон не done).
GET  /api/tasks               — список прогонов.
"""
from django.shortcuts import get_object_or_404
from ninja import NinjaAPI

from .models import SimulationRun
from .schemas import SimulationResultOut, SimulationRunOut, TaskIn
from .services import create_and_run_async

api = NinjaAPI(title="Hospital Flow Simulation API")


@api.post("/tasks", response={202: SimulationRunOut})
def create_task(request, payload: TaskIn):
    params = payload.params.dict()
    patients = params.pop("patients")
    run = create_and_run_async(patients=patients, **params)
    return 202, run


@api.get("/tasks/{run_id}", response=SimulationRunOut)
def get_task(request, run_id: str):
    run = get_object_or_404(SimulationRun, id=run_id)
    return run


@api.get("/tasks/{run_id}/result", response=SimulationResultOut)
def get_task_result(request, run_id: str):
    run = get_object_or_404(SimulationRun.objects.select_related("result"), id=run_id)
    return getattr(run, "result", None) or SimulationResultOut()


@api.get("/tasks", response=list[SimulationRunOut])
def list_tasks(request):
    return SimulationRun.objects.select_related("result").all()
