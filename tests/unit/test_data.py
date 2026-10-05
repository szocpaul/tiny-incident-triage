"""T018: data.py szerződés-tesztek az ÚJ adatúthoz — FR-001, FR-002, FR-009.

A tanítóhalmaz = tanár-címkék mínusz a kézi teszt id-i; a teszt = a kézzel
ellenőrzött fagyott halmaz; 0 átfedés mindkét irányban.
"""
import json

import polars as pl
import pytest

from triage.data import (
    LABELS_EXPECTED,
    TASK,
    assert_no_overlap,
    build_labeled,
    build_texts,
    split_teacher,
    tidy_and_split,
    write_recipe_format,
)


def _write_raw(tmp_path, n=40):
    rows = [{"ticket_id": i, "summary": f"issue {i}", "description": f"detail {i}"}
            for i in range(1, n + 1)]
    pl.DataFrame(rows).write_csv(tmp_path / "tickets.csv")


def _teacher(tmp_path, texts):
    """Tanár-címkék: kategóriát rendelünk sorindex szerint; 2 szándékosan None."""
    path = tmp_path / "teacher.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for i, row in enumerate(texts.iter_rows(named=True)):
            label = None if i < 2 else LABELS_EXPECTED[i % 8]
            f.write(json.dumps({"id": row["id"], "label": label}) + "\n")
    return path


def _handchecked(tmp_path, texts, k=8):
    ids = texts["id"].to_list()[:k]
    path = tmp_path / "handchecked_test.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for i, id_ in enumerate(ids):
            text = texts.filter(pl.col("id") == id_)["text"][0]
            f.write(json.dumps({"id": id_, "text": text,
                                "label": LABELS_EXPECTED[i % 8]}) + "\n")
    return path


def test_build_texts_schema(tmp_path):
    _write_raw(tmp_path)
    df = build_texts(tmp_path)
    assert df.columns == ["task", "id", "text"]
    assert len(df) == 40
    assert set(df["task"].unique().to_list()) == {TASK}
    assert "issue 1" in df.filter(pl.col("id") == f"{TASK}-1")["text"][0]


def test_build_labeled_drops_invalid(tmp_path):
    _write_raw(tmp_path)
    texts = build_texts(tmp_path)
    teacher = _teacher(tmp_path, texts)
    labeled = build_labeled(texts, teacher)
    assert len(labeled) == 38  # a 2 None-címke kihagyva
    assert set(labeled["label"].unique().to_list()) <= set(LABELS_EXPECTED)


def test_split_teacher_no_overlap_and_test_is_handchecked(tmp_path):
    _write_raw(tmp_path)
    texts = build_texts(tmp_path)
    labeled = build_labeled(texts, _teacher(tmp_path, texts))
    hand = _handchecked(tmp_path, texts, k=8)
    train, test = split_teacher(labeled, hand)
    assert len(test) == 8
    # a kézi teszt id-i kikerülnek a tanítóból; a 2 None-címkés sor (id 1-2)
    # amúgy sincs a labeled-ben, ezért 38 - 6
    assert len(train) == 32
    assert_no_overlap(train, test)
    with pytest.raises(AssertionError):
        assert_no_overlap(train, train)


def test_tidy_and_split_writes_all_outputs(tmp_path):
    _write_raw(tmp_path)
    texts = build_texts(tmp_path)
    texts_path = tmp_path / "texts.parquet"
    texts.write_parquet(texts_path)
    teacher = _teacher(tmp_path, texts)
    hand = _handchecked(tmp_path, texts, k=8)
    train, test = tidy_and_split(texts_path, teacher, hand,
                                 tmp_path / "tidy", tmp_path / "tasks")
    assert (tmp_path / "tidy" / "train.parquet").exists()
    assert (tmp_path / "tidy" / "test.parquet").exists()
    task = json.loads((tmp_path / "tasks" / TASK / "task.json").read_text(encoding="utf-8"))
    assert task["name"] == TASK and len(task["labels"]) == 8
    n_train_jsonl = len((tmp_path / "tasks" / TASK / "train.jsonl")
                        .read_text(encoding="utf-8").splitlines())
    assert n_train_jsonl == len(train)
    meta = json.loads((tmp_path / "tidy" / "split_meta.json").read_text(encoding="utf-8"))
    assert meta["test_source"] == "handchecked"
