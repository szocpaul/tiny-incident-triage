"""T005: evaluate.py szerződés-tesztek — FR-004, SC-001, SC-002.

FAIL-elnie kell, amíg a T007 implementáció nem készül el.
"""
import json

from triage.evaluate import check_threshold, write_metrics

LABELS = ["a", "b", "c"]


def test_write_metrics_schema(tmp_path):
    y_true = ["a", "a", "b", "b", "c", "c"]
    y_pred = ["a", "b", "b", "b", "c", "a"]
    path = write_metrics(tmp_path, y_true, y_pred, LABELS)
    m = json.loads(path.read_text(encoding="utf-8"))
    assert abs(m["accuracy"] - 4 / 6) < 1e-9  # találat: index 0, 2, 3, 4
    assert m["per_category"]["a"]["accuracy"] == 0.5
    assert m["per_category"]["b"]["accuracy"] == 1.0
    assert m["per_category"]["c"]["accuracy"] == 0.5
    assert m["n_test"] == 6
    assert "timestamp" in m


def test_check_threshold_exit_codes(tmp_path):
    y_true = ["a", "a", "b", "b"]
    y_pred = ["a", "a", "b", "b"]  # 100%
    path = write_metrics(tmp_path, y_true, y_pred, ["a", "b"])
    m = json.loads(path.read_text(encoding="utf-8"))
    assert check_threshold(m, min_accuracy=0.90) == 0   # SC-001 gate zöld
    assert check_threshold(m, min_accuracy=1.01) == 1   # lehetetlen küszöb -> 1


def test_check_threshold_fails_below(tmp_path):
    y_true = ["a", "a", "b", "b"]
    y_pred = ["a", "b", "b", "b"]  # 75%
    path = write_metrics(tmp_path, y_true, y_pred, ["a", "b"])
    m = json.loads(path.read_text(encoding="utf-8"))
    assert check_threshold(m, min_accuracy=0.90) == 1
