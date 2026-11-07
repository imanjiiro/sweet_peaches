from django import forms

from core.schemas import MAX_ARRIVAL_RATE, MAX_DOCTORS, MAX_HORIZON_MIN, MAX_SERVICE_MEAN

# Названия стратегий по-русски: форма и страница задачи берут их отсюда
STRATEGY_LABELS = {
    "fifo": "По порядку прихода (FIFO)",
    "priority": "По срочности (Priority)",
    "dynamic": "Срочность с учётом ожидания (Dynamic)",
}


class TaskForm(forms.Form):
    name = forms.CharField(
        label="Название запуска",
        max_length=200,
        initial="Симуляция очереди больницы",
    )
    doctors = forms.IntegerField(
        label="Количество врачей",
        min_value=1,
        max_value=MAX_DOCTORS,
        initial=3,
    )
    strategy = forms.ChoiceField(
        label="Стратегия очереди",
        choices=list(STRATEGY_LABELS.items()),
        initial="fifo",
    )
    arrival_rate = forms.FloatField(
        label="Интенсивность прихода (пациентов/мин)",
        min_value=0.01,
        max_value=MAX_ARRIVAL_RATE,  # граница потока: те же числа, что в core/schemas.py
        initial=0.15,  # 0.15 пац/мин = ~9 пац/час на 3 врачей (утилизация ~75%)
    )
    service_mean = forms.FloatField(
        label="Среднее время приема (мин)",
        min_value=0.1,
        max_value=MAX_SERVICE_MEAN,
        initial=15.0,
    )
    horizon_min = forms.FloatField(
        label="Длительность смены (мин)",
        min_value=1.0,
        max_value=MAX_HORIZON_MIN,  # граница смены: не больше суток
        initial=480.0,
    )

    def params(self) -> dict:
        """Возвращает очищенные параметры симуляции без поля name."""
        data = self.cleaned_data.copy()
        data.pop("name", None)
        return data