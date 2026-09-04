"""web/forms.py — форма запуска новой симуляции (страница /).

Поля и их имена — те же, что в модели и в HospitalParams (web/schemas.py):
см. "Работа 2: API", пункт 2 — разные имена в форме/схеме были бы
источником половины ошибок на защите.
"""
from django import forms

from .models import SimulationRun


class SimulationRunForm(forms.ModelForm):
    # seed на форме намеренно нет — это технический параметр
    # воспроизводимости, сервис подбирает и сохраняет его сам
    # (см. web/services.execute_run). Поле остаётся в модели, но не
    # входит в пользовательскую форму.
    class Meta:
        model = SimulationRun
        fields = [
            "doctors",
            "arrival_rate",
            "service_mean",
            "horizon_min",
            "strategy",
            "n_runs",
        ]
        widgets = {
            "doctors": forms.NumberInput(attrs={"min": 1, "max": 20}),
            "arrival_rate": forms.NumberInput(attrs={"min": 0.01, "step": 0.01}),
            "service_mean": forms.NumberInput(attrs={"min": 0.1, "step": 0.1}),
            "horizon_min": forms.NumberInput(attrs={"min": 10}),
            "n_runs": forms.NumberInput(attrs={"min": 1, "max": 1000}),
        }
        help_texts = {
            "arrival_rate": "пациентов в минуту",
            "service_mean": "среднее время приёма, мин",
            "horizon_min": "длина смены, мин (по умолчанию 480 — 8 часов)",
            "n_runs": "сколько независимых прогонов усреднить",
        }
