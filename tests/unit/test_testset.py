"""T034: testset.py szerződés-tesztek — FR-001, FR-002, FR-003.

FAIL-elniük kell, amíg a testset.py (T035) nem készül el.
"""
import json

import pytest

from triage.testset import (
    apply_decisions,
    find_conflicts,
    freeze_v2,
    write_decisions_template,
)

ROWS = [
    {"id": "t-1", "text": "Spam burst hit inbox. Reported by A.", "label": "Security"},
    {"id": "t-2", "text": "spam burst hit inbox! Reported by B", "label": "Email & Collaboration"},
    {"id": "t-3", "text": "VPN down in office.", "label": "Network & VPN"},
    {"id": "t-4", "text": "VPN down in office. Reported by D.", "label": "Network & VPN"},
]


def test_find_conflicts_normalized(tmp_path):
    f = tmp_path / "t.jsonl"
    f.write_text("\n".join(json.dumps(r) for r in ROWS), encoding="utf-8")
    groups = find_conflicts(f)
    # csak a spam-csoport konfliktusos; a VPN-duplikátum konzisztens
    assert len(groups) == 1
    g = groups[0]
    assert g["count"] == 2
    assert set(g["labels"]) == {"Security", "Email & Collaboration"}
    assert set(g["ids"]) == {"t-1", "t-2"}


def test_write_decisions_template(tmp_path):
    f = tmp_path / "t.jsonl"
    f.write_text("\n".join(json.dumps(r) for r in ROWS), encoding="utf-8")
    out = tmp_path / "decisions.csv"
    write_decisions_template(find_conflicts(f), out)
    import csv
    rows = list(csv.DictReader(open(out, encoding="utf-8-sig")))
    assert len(rows) == 1
    assert set(rows[0]) >= {"group", "text", "labels", "ids", "decision", "reason"}
    assert rows[0]["decision"] == ""  # a felhasználó tölti


def test_apply_decisions_requires_full_coverage(tmp_path):
    f = tmp_path / "t.jsonl"
    f.write_text("\n".join(json.dumps(r) for r in ROWS), encoding="utf-8")
    groups = find_conflicts(f)
    with pytest.raises(ValueError):
        apply_decisions(ROWS, groups, [{"group": 0, "decision": ""}])  # kitöltetlen


def test_apply_decisions_canonical_label(tmp_path):
    f = tmp_path / "t.jsonl"
    f.write_text("\n".join(json.dumps(r) for r in ROWS), encoding="utf-8")
    groups = find_conflicts(f)
    new_rows, log = apply_decisions(
        ROWS, groups, [{"group": 0, "decision": "Security", "reason": "spam = security"}])
    kept = [r for r in new_rows if r["id"] in ("t-1", "t-2")]
    assert len(kept) == 1 and kept[0]["label"] == "Security"
    assert log[0]["reason"] == "spam = security"


def test_apply_decisions_drop(tmp_path):
    f = tmp_path / "t.jsonl"
    f.write_text("\n".join(json.dumps(r) for r in ROWS), encoding="utf-8")
    groups = find_conflicts(f)
    new_rows, log = apply_decisions(ROWS, groups, [{"group": 0, "decision": "drop", "reason": "megitellehetetlen"}])
    assert not [r for r in new_rows if r["id"] in ("t-1", "t-2")]
    assert log[0]["dropped"] == ["t-1", "t-2"]


def test_freeze_v2_archives_and_checks(tmp_path):
    v1 = tmp_path / "handchecked_test.jsonl"
    v1.write_text("\n".join(json.dumps(r) for r in ROWS), encoding="utf-8")
    new_rows = ROWS[:1] + ROWS[2:]  # a konfliktus feloldva
    train = tmp_path / "train.parquet"
    import polars as pl
    pl.DataFrame({"task": ["t"], "id": ["x"], "text": ["other"], "label": ["Security"]}).write_parquet(train)
    out = freeze_v2(v1, new_rows, train, tmp_path / "labels", tmp_path / "test.parquet",
                    changelog=[{"group": 0, "decision": "Security"}])
    assert (tmp_path / "labels" / "handchecked_test_v1.jsonl").exists()
    v2 = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines()]
    assert len(v2) == 3
    assert (tmp_path / "labels" / "testset_v2_changelog.json").exists()
    assert (tmp_path / "test.parquet").exists()
