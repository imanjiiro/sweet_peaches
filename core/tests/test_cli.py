"""CLI ядра: python -m core --help печатает подсказку, example_input.json — вход нашей задачи."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def _cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "core", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8"
    )


def test_help_prints_usage_not_error():
    done = _cli("--help")
    assert done.returncode == 0
    assert "usage" in done.stdout.lower()
    assert "input" in done.stdout


def test_example_input_is_hospital_input():
    params = json.loads((ROOT / "example_input.json").read_text(encoding="utf-8"))
    assert {"doctors", "strategy", "arrival_rate", "service_mean", "horizon_min"} <= set(params)


def test_example_input_runs():
    done = _cli("example_input.json")
    assert done.returncode == 0
    result = json.loads(done.stdout)
    assert result["served_patients_count"] > 0
    assert len(result["wait_by_priority"]) == 3
