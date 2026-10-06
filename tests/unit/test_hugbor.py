"""T041: hugbor.py szerződés-tesztek — FR-001, FR-002, FR-003, FR-004.

FAIL-elniük kell, amíg a hugbor.py (T042) nem készül el.
"""
import json

import polars as pl
import pytest

from triage.hugbor import (
    CATEGORIES,
    agreement_rate,
    build_tidy_hugbor,
    split_holdout,
    truncate_text,
)


def _write_raw(tmp_path, n_per_cat=6):
    """Mini HugBor-szerű CSV a valódi oszlopnevekkel."""
    rows = []
    i = 0
    for cat in CATEGORIES:
        for j in range(n_per_cat):
            i += 1
            rows.append({
                "number": f"INC{i:07d}", "created_by": "tester",
                "short_description": f"{cat} issue {j}",
                "category": cat,
                "description": f"Details about {cat} problem {j}. " * 3,
                "impact": "Medium", "urgency": "High",
                "resolution": "fixed",
            })
    pl.DataFrame(rows).write_csv(tmp_path / "hugbor.csv")


def test_categories_14_after_merge():
    assert len(CATEGORIES) == 14
    assert "Printer/Peripherals" in CATEGORIES
    assert "Backup/Recovery" in CATEGORIES
    assert "Software" not in CATEGORIES  # Application-be olvadt (spec módosítás)


def test_tidy_schema_and_text(tmp_path):
    _write_raw(tmp_path)
    df = build_tidy_hugbor(tmp_path / "hugbor.csv")
    assert df.columns == ["task", "id", "text", "label"]
    row = df.filter(pl.col("id").str.contains("INC0000001")).row(0, named=True)
    assert "issue 0" in row["text"] and "Details about" in row["text"]
    assert set(df["label"].unique().to_list()) == set(CATEGORIES)


def test_truncation_uniform():
    long_text = "x" * 900
    out = truncate_text(long_text)
    assert len(out) <= 500
    short = "short text"
    assert truncate_text(short) == short


def test_split_stratified_and_no_overlap(tmp_path):
    _write_raw(tmp_path, n_per_cat=6)
    df = build_tidy_hugbor(tmp_path / "hugbor.csv")
    train, test = split_holdout(df, test_frac=0.34, seed=0)
    assert len(train) + len(test) == len(df)
    assert set(train["id"].to_list()) & set(test["id"].to_list()) == set()
    # rétegzett: minden kategória megvan a tesztben (14 az összevonás után)
    assert test["label"].n_unique() == 14
    # reprodukálható
    tr2, te2 = split_holdout(df, test_frac=0.34, seed=0)
    assert te2["id"].to_list() == test["id"].to_list()


def test_agreement_rate():
    a = ["Security", "Network", "Email"]
    b = ["Security", "VPN", "Email"]
    assert agreement_rate(a, b) == pytest.approx(2 / 3)
