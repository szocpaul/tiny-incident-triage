"""T029: relabel.py szerződés-tesztek — FR-002, FR-003.

FAIL-elniük kell, amíg a relabel.py (T030) nem készül el.
"""
import polars as pl
import pytest

from triage.relabel import RULES, apply_relabels, find_candidates


def _df():
    return pl.DataFrame({
        "task": ["t"] * 4,
        "id": ["a", "b", "c", "d"],
        "text": [
            "MFA push not arriving on replacement phone. Reported by A.",
            "Printer jam on floor 2. Reported by B.",
            "Teams meeting room camera flickers after restart. Reported by C.",
            "Password reset loop continues. Reported by D.",
        ],
        "label": ["Access Management", "Printers & Devices",
                  "Email & Collaboration", "Access Management"],
    })


def test_find_candidates_hits_rules():
    cands = find_candidates(_df())
    ids = {c["id"] for c in cands}
    assert "a" in ids  # MFA-jelölt
    assert "c" in ids  # Teams camera-jelölt
    assert "b" not in ids  # sima printer-sor nem jelölt
    for c in cands:
        assert set(c) >= {"id", "text", "current_label", "suggested_label", "rule"}


def test_apply_relabels_only_approved():
    df = _df()
    decisions = [
        {"id": "a", "relabel_to": "Security"},   # jóváhagyva
        {"id": "c", "relabel_to": ""},           # marad
        {"id": "b", "relabel_to": "Security"},   # nem jelölt → figyelmen kívül
    ]
    out, log = apply_relabels(df, decisions)
    assert out.filter(pl.col("id") == "a")["label"][0] == "Security"
    assert out.filter(pl.col("id") == "c")["label"][0] == "Email & Collaboration"
    assert out.filter(pl.col("id") == "b")["label"][0] == "Printers & Devices"
    assert len(log) == 1  # csak a jóváhagyott, jelölt sor változott


def test_apply_relabels_validates_target():
    df = _df()
    with pytest.raises(ValueError):
        apply_relabels(df, [{"id": "a", "relabel_to": "NincsIlyenKategoria"}])
