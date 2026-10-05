"""T015: label.py szerződés-tesztek — FR-008, SC-005.

FAIL-elnie kell, amíg a label.py nem készül el.
A tesztek nem igényelnek bejelentkezést (a hálózati rész nincs mockolva,
hanem nincs is meghívva).
"""
import json

from triage.data import INSTRUCTION, LABELS_EXPECTED
from triage.label import build_system_prompt, done_ids, match_answer


def test_system_prompt_contains_instruction_and_labels():
    p = build_system_prompt()
    assert INSTRUCTION in p
    for label in LABELS_EXPECTED:
        assert label in p


def test_match_answer_strict():
    assert match_answer("Network & VPN", LABELS_EXPECTED) == "Network & VPN"
    assert match_answer("  network & vpn. ", LABELS_EXPECTED) == "Network & VPN"
    assert match_answer("`Security`", LABELS_EXPECTED) == "Security"
    # nem találgat: ismeretlen, üres vagy többszörös válasz = None
    assert match_answer("probably network stuff", LABELS_EXPECTED) is None
    assert match_answer("", LABELS_EXPECTED) is None
    assert match_answer("Network & VPN and Security", LABELS_EXPECTED) is None


def test_done_ids_resumable(tmp_path):
    path = tmp_path / "teacher.jsonl"
    rows = [{"id": "a", "label": "Security"}, {"id": "b", "label": None}]
    path.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    assert done_ids(path) == {"a", "b"}
    assert done_ids(tmp_path / "nonexistent.jsonl") == set()
