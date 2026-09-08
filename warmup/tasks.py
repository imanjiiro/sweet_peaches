"""Заглушки восьми задач. Замените `...` на код. Тесты: pytest warmup -q"""


def mean(values: list[float]) -> float:
    """Среднее арифметическое. Для пустого списка вернуть 0.0."""
    ...


def word_count(text: str) -> dict[str, int]:
    """Сколько раз встречается каждое слово (без учёта регистра). 'a b A' -> {'a': 2, 'b': 1}"""
    ...


def parse_params(line: str) -> dict[str, float]:
    """'a=1;b=2.5' -> {'a': 1.0, 'b': 2.5}. Пробелы вокруг игнорировать."""
    ...


class Stats:
    """Накапливает числа. summary() -> {'count', 'min', 'max', 'mean'};
    для пустого — count 0, остальные None."""

    def __init__(self): ...

    def add(self, value: float) -> None: ...

    def summary(self) -> dict: ...


def read_numbers(path: str) -> list[float]:
    """Прочитать файл построчно, вернуть числа; строки, которые не парсятся в float, пропустить."""
    ...


def safe_div(a: float, b: float) -> float | None:
    """a / b, а при делении на ноль — None (без исключения наружу)."""
    ...


def trapezoid(f, a: float, b: float, n: int) -> float:
    """Интеграл f на [a, b] методом трапеций с n разбиениями."""
    ...


def to_json_line(d: dict) -> str:
    """JSON-строка с ключами в алфавитном порядке, без пробелов после разделителей: {"a":1,"b":2}"""
    ...
