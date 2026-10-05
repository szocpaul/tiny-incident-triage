"""T027: confusion.py szerződés-tesztek — FR-001.

FAIL-elniük kell, amíg a confusion.py (T028) nem készül el.
"""
import json

from triage.confusion import confusion_report

LABELS = ["a", "b"]


def test_confusion_matrix_counts():
    ids = [f"i-{i}" for i in range(6)]
    texts = [f"text {i}" for i in range(6)]
    y_true = ["a", "a", "a", "b", "b", "b"]
    y_pred = ["a", "b", "a", "b", "a", "a"]
    rep = confusion_report(ids, texts, y_true, y_pred, LABELS)
    assert rep["matrix"]["a"]["b"] == 1
    assert rep["matrix"]["b"]["a"] == 2
    assert rep["n_test"] == 6
    assert abs(rep["accuracy"] - 3 / 6) < 1e-9


def test_confusion_lists_misclassified_rows():
    ids = ["x1", "x2"]
    texts = ["first text", "second text"]
    y_true = ["a", "b"]
    y_pred = ["b", "b"]
    rep = confusion_report(ids, texts, y_true, y_pred, LABELS)
    assert len(rep["misclassified"]) == 1
    row = rep["misclassified"][0]
    assert row == {"id": "x1", "text": "first text", "true": "a", "pred": "b"}


def test_confusion_writes_json(tmp_path):
    path = confusion_report(["x"], ["t"], ["a"], ["a"], LABELS, out_dir=tmp_path)
    data = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert data["accuracy"] == 1.0
    assert data["misclassified"] == []
