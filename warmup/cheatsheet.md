# Python за одну страницу (то, что нужно в этом курсе)

```python
# функции и значения по умолчанию
def area(a, b=1.0):            # -> float
    return a * b

# списки, словари, включения
xs = [1, 2, 3]; xs.append(4); xs[0]; xs[-1]; xs[1:3]
d = {"a": 1}; d["b"] = 2; d.get("c", 0); for k, v in d.items(): ...
squares = [x * x for x in xs if x % 2 == 0]

# строки
s = "a=1;b=2"; s.split(";")  # ['a=1', 'b=2']; "a=1".split("=", 1); s.strip(); f"{x:.3f}"

# классы
class Stats:
    def __init__(self):
        self.values = []
    def add(self, v):
        self.values.append(v)

# файлы
with open("data.txt", encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()

# исключения
try:
    x = float("abc")
except ValueError as exc:
    print("плохое число:", exc)

# функция как аргумент
def apply(f, x): return f(x)
apply(lambda t: t * 2, 3)      # 6

# json
import json; json.dumps({"b": 1, "a": 2}, sort_keys=True); json.loads('{"a": 1}')

# модули и пакеты: папка с __init__.py — пакет; python -m core запускает core/__main__.py
# venv: python -m venv .venv ; .venv\Scripts\activate (Windows) / source .venv/bin/activate ; pip install -r requirements.txt
# git: git clone URL ; git add -A ; git commit -m "msg" ; git push ; git pull
```
