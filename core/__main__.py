"""CLI ядра: python -m core input.json output.json  (или без output — печать в stdout)."""
import json
import sys

from core.solver import run


def main(argv: list[str]) -> int:
    if len(argv) < 1:
        print("Использование: python -m core input.json [output.json]", file=sys.stderr)
        return 2
    with open(argv[0], encoding="utf-8") as fh:
        params = json.load(fh)
    try:
        result = run(params)
    except Exception as exc:  # noqa: BLE001 — на границе CLI ловим всё и печатаем понятно
        print(f"Ошибка расчёта: {exc}", file=sys.stderr)
        return 1
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if len(argv) > 1:
        with open(argv[1], "w", encoding="utf-8") as fh:
            fh.write(text)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
