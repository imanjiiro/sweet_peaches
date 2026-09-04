"""
web/services.py

Связующий код между веб-слоем и ядром: "вызвать core, полученные
метрики положить в модели" — вынесено сюда из вьюхи и из API, чтобы
обе точки входа (форма /, POST /api/tasks) звали одну и ту же функцию
(см. docs/fat_review.md, пункт 4).

Тяжёлая функция (core.simulation.simulate) считается В ФОНЕ отдельным
потоком (galочка 7 "Фон + измерение"): вьюха/API создают SimulationRun
со статусом "queued" и сразу отвечают, не дожидаясь расчёта. Статус
меняется queued -> running -> done/failed по ходу работы потока —
если несколько раз обновить страницу /runs/ или дёрнуть
GET /api/tasks/{id}, будет видно, как он меняется "на глазах".

Это стандартный threading.Thread, а не очередь задач (Celery/RQ) — для
учебного одно-процессного проекта этого достаточно (см. ADR-001,
раздел "Последствия": полноценная очередь — следующий шаг, не
меняющий core). Из-за этого есть особенность SQLite + Django ORM:
каждый поток открывает СВОЁ соединение с БД, и его обязательно нужно
закрывать по завершении (connections.close_all()), иначе соединения
утекают.
"""
from __future__ import annotations

import random
import threading
import time

from django.db import connections

from core.simulation import simulate

from .models import RunStatus, SimulationResult, SimulationRun


def execute_run(
    run: SimulationRun,
    patients: list[tuple[float, str]] | None = None,
) -> SimulationRun:
    """Синхронно прогнать core.simulation для уже созданного
    SimulationRun и сохранить результат (или ошибку) в БД. Меряет
    время расчёта (duration_seconds) — см. galочку 7.

    patients — необязательный готовый список пациентов (см.
    HospitalParams.patients, слайд "Тонкость"): используется только
    для детерминированных тестовых запусков через API и НЕ сохраняется
    в модели — это не параметр обычной задачи, а способ проверить ядро
    на заранее известном сценарии."""
    run.status = RunStatus.RUNNING
    if run.seed is None and patients is None:
        # seed не обязателен на форме/в API — но core.simulation.simulate()
        # всегда должен быть воспроизводим, поэтому если пользователь его
        # не задал, выбираем и сохраняем сами, а не гоняем каждый раз новый.
        run.seed = random.randint(0, 2**31 - 1)
        run.save(update_fields=["status", "seed"])
    else:
        run.save(update_fields=["status"])

    started = time.perf_counter()
    try:
        metrics = simulate(
            doctors=run.doctors,
            arrival_rate=run.arrival_rate,
            service_mean=run.service_mean,
            horizon_min=run.horizon_min,
            strategy=run.strategy,
            n_runs=run.n_runs,
            seed=run.seed,
            patients=patients,
        )
    except Exception as exc:  # noqa: BLE001 — граница веб-слоя, см. fat_review п.6
        run.status = RunStatus.FAILED
        run.error_message = str(exc)
        run.duration_seconds = time.perf_counter() - started
        run.save(update_fields=["status", "error_message", "duration_seconds"])
        return run

    SimulationResult.objects.update_or_create(
        run=run,
        defaults={
            "avg_wait_time": metrics.avg_wait_time,
            "max_wait_time": metrics.max_wait_time,
            "avg_queue_length": metrics.avg_queue_length,
            "doctor_utilization": metrics.doctor_utilization,
            "patients_served": metrics.patients_served,
        },
    )
    run.status = RunStatus.DONE
    run.error_message = ""
    run.duration_seconds = time.perf_counter() - started
    run.save(update_fields=["status", "error_message", "duration_seconds"])
    return run


def _execute_run_in_background(
    run_id, patients: list[tuple[float, str]] | None
) -> None:
    """Тело фонового потока: своё соединение с БД, обязательно
    закрывается в finally — иначе после многих запусков накопится куча
    висящих соединений к SQLite."""
    try:
        run = SimulationRun.objects.get(id=run_id)
        execute_run(run, patients=patients)
    finally:
        connections.close_all()


def execute_run_async(
    run: SimulationRun,
    patients: list[tuple[float, str]] | None = None,
) -> threading.Thread:
    """Запустить расчёт run в фоновом потоке и сразу вернуть управление
    (run остаётся в статусе "queued" на момент возврата — статус
    сменится на running/done по ходу работы потока)."""
    thread = threading.Thread(
        target=_execute_run_in_background,
        args=(run.id, patients),
        daemon=True,
    )
    thread.start()
    return thread


def create_and_run_async(
    patients: list[tuple[float, str]] | None = None, **params
) -> SimulationRun:
    """Создать SimulationRun из параметров и сразу запустить расчёт в
    фоне, не дожидаясь его завершения (см. execute_run_async)."""
    run = SimulationRun.objects.create(**params)
    execute_run_async(run, patients=patients)
    return run
