from django import forms

from core.schemas import FUNCTIONS


class TaskForm(forms.Form):
    name = forms.CharField(label="Название", max_length=200)
    function = forms.ChoiceField(label="Функция", choices=[(f, f) for f in FUNCTIONS])
    a = forms.FloatField(label="a", initial=0)
    b = forms.FloatField(label="b", initial=3.14159)
    n = forms.IntegerField(label="n (разбиений)", initial=100_000, min_value=2)
    method = forms.ChoiceField(label="Метод", choices=[("simpson", "Симпсон"), ("trapezoid", "Трапеции")])

    def params(self) -> dict:
        d = self.cleaned_data
        return {"function": d["function"], "a": d["a"], "b": d["b"], "n": d["n"], "method": d["method"]}
