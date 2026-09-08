import math

from warmup import tasks as t


def test_1_mean():
    assert t.mean([1, 2, 3]) == 2
    assert t.mean([]) == 0.0


def test_2_word_count():
    assert t.word_count("a b A") == {"a": 2, "b": 1}


def test_3_parse_params():
    assert t.parse_params("a=1; b = 2.5") == {"a": 1.0, "b": 2.5}


def test_4_stats():
    s = t.Stats()
    assert s.summary()["count"] == 0 and s.summary()["mean"] is None
    for v in (1, 5, 3):
        s.add(v)
    assert s.summary() == {"count": 3, "min": 1, "max": 5, "mean": 3}


def test_5_read_numbers(tmp_path):
    p = tmp_path / "d.txt"
    p.write_text("1\nabc\n2.5\n\n", encoding="utf-8")
    assert t.read_numbers(str(p)) == [1.0, 2.5]


def test_6_safe_div():
    assert t.safe_div(1, 2) == 0.5
    assert t.safe_div(1, 0) is None


def test_7_trapezoid():
    assert abs(t.trapezoid(math.sin, 0, math.pi, 1000) - 2) < 1e-4


def test_8_to_json_line():
    assert t.to_json_line({"b": 2, "a": 1}) == '{"a":1,"b":2}'
