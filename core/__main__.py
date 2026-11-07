"""CLI ядра: python -m core input.json [output.json]  (без output.json — печать в stdout)."""
import argparse
import json
import sys

from core.solver import run

DESCRIPTION = "Симуляция очереди приёмного отделения больницы. Читает параметры из JSON, печатает результат."
EXAMPLE = "Пример: python -m core example_input.json   (файл example_input.json лежит в корне проекта)"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m core", description=DESCRIPTION, epilog=EXAMPLE)
    parser.add_argument("input", help="JSON-файл с параметрами (doctors, strategy, arrival_rate, ...)")
    parser.add_argument("output", nargs="?", help="куда записать результат (если не указан — печать на экран)")
    return parser


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)  # --help печатает подсказку и завершается кодом 0
    try:
        with open(args.input, encoding="utf-8") as fh:
            params = json.load(fh)
        result = run(params)
    except Exception as exc:  # noqa: BLE001 — на границе CLI ловим всё и печатаем понятно
        print(f"Ошибка расчёта: {exc}", file=sys.stderr)
        return 1
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(text)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
