"""T044: stylegen.py szerződés-tesztek — FR-005, FR-008.

FAIL-elniük kell, amíg a stylegen.py (T045) nem készül el.
"""
import json

import polars as pl
import pytest

from triage.stylegen import (
    assert_local_only,
    build_topup_prompt,
    parse_topup,
    thin_categories,
)

HUGBOR_SAMPLE = pl.DataFrame({
    "task": ["t"] * 4,
    "id": [f"i-{i}" for i in range(4)],
    "text": [
        "VPN drops every 15 minutes. Users report the tunnel reconnects.",
        "Webex jitter on VLAN 30. Call quality degraded all morning.",
        "UPS battery low on Rack B. Power event last night.",
        "Shared mailbox not syncing. Outlook shows stale items.",
    ],
    "label": ["VPN", "Telephony", "Data Center", "Email"],
})


def test_local_only_guard():
    assert_local_only("http://127.0.0.1:8080")
    assert_local_only("http://localhost:8080")
    with pytest.raises(AssertionError):
        assert_local_only("https://api.fireworks.ai/v1")  # felhő tilos!


def test_thin_categories():
    counts = {"VPN": 81, "Network": 167, "Telephony": 42, "Email": 80}
    thin = thin_categories(counts, min_rows=100)
    assert set(thin) == {"VPN", "Telephony", "Email"}
    assert thin["VPN"] == 100 - 81
    assert thin["Telephony"] == 100 - 42


def test_topup_prompt_fewshot_same_category():
    prompt = build_topup_prompt("Telephony", HUGBOR_SAMPLE, n=3, seed=0)
    # few-shot: a kategória saját sorai a promptban
    assert "Webex jitter" in prompt
    assert "VPN drops" not in prompt  # más kategória nem kerülhet bele
    assert "Telephony" in prompt
    assert "ENGLISH" in prompt.upper()


def test_parse_topup_schema_and_filter():
    raw = json.dumps([
        {"short_description": "PBX trunk down", "description": "Calls fail."},
        {"short_description": "", "description": "no title"},
        "garbage",
    ])
    rows = parse_topup(raw, category="Telephony", batch_id=0)
    assert len(rows) == 1
    assert rows[0]["label"] == "Telephony"
    assert "PBX trunk down" in rows[0]["text"]
    assert "Calls fail." in rows[0]["text"]
