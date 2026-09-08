from django import forms


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
        label="Интенсивность прихода (пациентов/час)",
        min_value=0.1,
        initial=10.0,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.1"}),
    )
    service_mean = forms.FloatField(
        label="Среднее время приема (мин)",
        min_value=0.1,
        initial=15.0,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.1"}),
    )
    horizon_min = forms.FloatField(
        label="Длительность смены (мин)",
        min_value=1.0,
        initial=480.0,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    def params(self) -> dict:
        """Возвращает очищенные параметры симуляции без поля name."""
        data = self.cleaned_data.copy()
        data.pop("name", None)
        return data