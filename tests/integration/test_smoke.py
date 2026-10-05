"""End-to-end smoke: texts + tanár-címkék + kézi teszt -> train(1 epoch) -> eval.

A tanítási recept epoch-formulája itt 1 epochra van felülírva a sebességért.
"""
import json

import polars as pl
import pytest

from triage.data import LABELS_EXPECTED, tidy_and_split
from triage.evaluate import evaluate_run
from triage.train import train_run


@pytest.mark.integration
def test_smoke_end_to_end(tmp_path):
    # 4 sor/kategória szöveg + tanár-címke + kézi teszt (1 sor/kategória)
    texts = pl.DataFrame({
        "task": ["servicenow_ticket_triage"] * 32,
        "id": [f"servicenow_ticket_triage-{i}" for i in range(32)],
        "text": [f"sample ticket about {LABELS_EXPECTED[i % 8]} number {i}" for i in range(32)],
    })
    texts_path = tmp_path / "texts.parquet"
    texts.write_parquet(texts_path)
    teacher = tmp_path / "teacher.jsonl"
    with open(teacher, "w", encoding="utf-8") as f:
        for i in range(32):
            f.write(json.dumps({"id": f"servicenow_ticket_triage-{i}",
                                "label": LABELS_EXPECTED[i % 8]}) + "\n")
    hand = tmp_path / "handchecked_test.jsonl"
    with open(hand, "w", encoding="utf-8") as f:
        for i in range(8):  # minden kategóriából 1 sor (i%8 == i az első 8 sorban)
            f.write(json.dumps({"id": f"servicenow_ticket_triage-{i}",
                                "text": texts["text"][i],
                                "label": LABELS_EXPECTED[i % 8]}) + "\n")

    train_df, test_df = tidy_and_split(texts_path, teacher, hand,
                                       tmp_path / "tidy", tmp_path / "tasks")
    assert len(train_df) == 24 and len(test_df) == 8

    run_dir = tmp_path / "runs" / "smoke"
    train_run(train_df, test_df, run_dir, seed=0, epochs_override=1, batch=8)
    assert (run_dir / "config.json").exists()
    assert (run_dir / "model").exists()

    m = evaluate_run(run_dir, test_df, min_accuracy=0.0)
    assert 0.0 <= m["accuracy"] <= 1.0
    assert len(m["per_category"]) == 8
