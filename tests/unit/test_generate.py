"""T020: generate.py szerződés-tesztek — FR-001, FR-002, FR-003.

FAIL-elniük kell, amíg a generate.py (T021) nem készül el.
"""
import json

import pytest

from triage.generate import (
    SUBTOPICS,
    assert_no_test_overlap,
    dedupe_rows,
    normalize_text,
    parse_generated,
)

WEAK = ["Security", "Printers & Devices", "Laptop / Endpoint"]


def test_subtopics_cover_weak_categories():
    assert set(SUBTOPICS) == set(WEAK)
    for cat in WEAK:
        assert len(SUBTOPICS[cat]) >= 4  # minden gyenge kategóriának >=4 altémája


def test_normalize_text():
    assert normalize_text("  VPN   Disconnects, EVERY 15 min! ") == \
        normalize_text("vpn disconnects every 15 min")
    assert normalize_text("A\nB") == normalize_text("a b")


def test_dedupe_exact_and_normalized():
    rows = [
        {"id": "g-1", "text": "Printer jam on floor 2.", "label": "Printers & Devices"},
        {"id": "g-2", "text": "printer  jam on floor 2", "label": "Printers & Devices"},
        {"id": "g-3", "text": "Scanner offline.", "label": "Printers & Devices"},
    ]
    kept = dedupe_rows(rows)
    assert [r["id"] for r in kept] == ["g-1", "g-3"]


def test_test_overlap_raises(tmp_path):
    hand = tmp_path / "handchecked_test.jsonl"
    hand.write_text(json.dumps({"id": "h-1", "text": "Suspicious login alert triggered.",
                                "label": "Security"}) + "\n", encoding="utf-8")
    good = [{"id": "g-1", "text": "Totally different text.", "label": "Security"}]
    assert_no_test_overlap(good, hand)  # nem dob
    bad = [{"id": "g-2", "text": "suspicious login alert triggered", "label": "Security"}]
    with pytest.raises(AssertionError):
        assert_no_test_overlap(bad, hand)  # normalizált egyezés = megáll


def test_parse_generated_schema():
    raw = json.dumps([
        {"text": "BitLocker recovery key prompt after BIOS update.",},
        {"text": "Phishing email reported by Finance."},
    ])
    rows = parse_generated(raw, category="Security", batch_id=0)
    assert len(rows) == 2
    for r in rows:
        assert set(r) == {"id", "text", "label"}
        assert r["label"] == "Security"  # konstrukció szerinti címke
    assert rows[0]["id"] != rows[1]["id"]


def test_parse_generated_tolerates_junk():
    raw = '```json\n[{"text": "ok"}, {"no_text": true}, "garbage"]\n```'
    rows = parse_generated(raw, category="Security", batch_id=0)
    assert len(rows) == 1  # csak az érvényes sor marad


def test_language_filter():
    from triage.generate import is_english
    assert is_english("Printer jam on floor 2.")
    assert not is_english("A nyomtató elakadt a második emeleten.")
    assert not is_english("Több kolléga jelezte, hogy hamis e-mailt kapott.")
