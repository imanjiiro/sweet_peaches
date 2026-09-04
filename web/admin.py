"""
web/admin.py

Регистрация моделей в стандартной админке Django — именно это открывает
препод на /admin/, проверяя галочку 2 («/admin показывает сущность»).
"""
from django.contrib import admin

from .models import SimulationResult, SimulationRun


@admin.register(SimulationRun)
class SimulationRunAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "created_at",
        "doctors",
        "arrival_rate",
        "service_mean",
        "horizon_min",
        "strategy",
        "n_runs",
        "status",
        "duration_seconds",
    )
    list_filter = ("strategy", "status")
    readonly_fields = ("id", "created_at")


@admin.register(SimulationResult)
class SimulationResultAdmin(admin.ModelAdmin):
    list_display = (
        "run",
        "avg_wait_time",
        "max_wait_time",
        "doctor_utilization",
        "patients_served",
    )
