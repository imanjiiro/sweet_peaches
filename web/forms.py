from django import forms

from core.schemas import MAX_ARRIVAL_RATE, MAX_DOCTORS, MAX_HORIZON_MIN, MAX_SERVICE_MEAN


class TaskForm(forms.Form):
    name = forms.CharField(
        label="Название запуска",
        max_length=200,
        initial="Симуляция очереди больницы",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    doctors = forms.IntegerField(
        label="Количество врачей",
        min_value=1,
        max_value=MAX_DOCTORS,
        initial=3,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    strategy = forms.ChoiceField(
        label="Стратегия очереди",
        choices=[
            ("fifo", "FIFO (Обычная очередь)"),
            ("priority", "Priority (По приоритету)"),
            ("dynamic", "Dynamic Ageing (Динамический приоритет)"),
        ],
        initial="fifo",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    arrival_rate = forms.FloatField(
        label="Интенсивность прихода (пациентов/мин)",
        min_value=0.01,
        max_value=MAX_ARRIVAL_RATE,  # граница потока: те же числа, что в core/schemas.py
        initial=0.15,  # 0.15 пац/мин = ~9 пац/час на 3 врачей (утилизация ~75%)
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
    )
    service_mean = forms.FloatField(
        label="Среднее время приема (мин)",
        min_value=0.1,
        max_value=MAX_SERVICE_MEAN,
        initial=15.0,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.1"}),
    )
    horizon_min = forms.FloatField(
        label="Длительность смены (мин)",
        min_value=1.0,
        max_value=MAX_HORIZON_MIN,  # граница смены: не больше суток
        initial=480.0,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    def params(self) -> dict:
        """Возвращает очищенные параметры симуляции без поля name."""
        data = self.cleaned_data.copy()
        data.pop("name", None)
        return data