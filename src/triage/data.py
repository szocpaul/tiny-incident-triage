"""FR-001/FR-002/FR-009: tidy + split a tanár-címkés adatúton.

Adatút (spec, 2026-10-05-i módosítás):
  data/tidy/texts.parquet (címke nélkül) + data/labels/teacher.jsonl (tanár)
  + data/labels/handchecked_test.jsonl (fagyott, kézi) -> train/test.

A minta eredeti category-címkéi zaj (baseline-mérés, 12,0% = véletlenszint),
ezért a category-join kódút törölve.
"""
import json
from pathlib import Path

import polars as pl
from dpyr import read, col, lit

TASK = "servicenow_ticket_triage"
INSTRUCTION = "Classify the IT support ticket by the team that should handle it."

# A 8 kategória (categories.csv sorrendje)
LABELS_EXPECTED = [
    "Access Management",
    "Laptop / Endpoint",
    "Network & VPN",
    "Email & Collaboration",
    "ERP / WMS",
    "Printers & Devices",
    "Security",
    "Telephony",
]


def build_texts(raw_dir) -> pl.DataFrame:
    """Nyers CSV-k -> címke nélküli szövegtábla (task, id, text)."""
    raw_dir = Path(raw_dir)
    tickets = read(str(raw_dir / "tickets.csv"))
    df = (
        tickets.mutate(task=lit(TASK))
        .unite("id", [col.task, col.ticket_id], sep="-", remove=False)
        .unite("text", [col.summary, col.description], sep=". ")
        .select(col.task, col.id, col.text)
    )
    return df.collect()


def load_jsonl(path) -> list[dict]:
    return [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines()
            if l.strip()]


def build_labeled(texts: pl.DataFrame, teacher_jsonl) -> pl.DataFrame:
    """texts + tanár-címkék -> labeled tábla (task, id, text, label).

    Érvénytelen (None / ismeretlen) címke: kihagyva — sosem találgatva
    (Constitution II, FR-008).
    """
    labels = {r["id"]: r.get("label") for r in load_jsonl(teacher_jsonl)}
    df = texts.with_columns(
        pl.col("id").map_elements(lambda i: labels.get(i), return_dtype=pl.String).alias("label")
    )
    df = df.filter(pl.col("label").is_in(LABELS_EXPECTED))
    return df.select(["task", "id", "text", "label"])


def assert_no_overlap(train: pl.DataFrame, test: pl.DataFrame) -> None:
    """Constitution II / FR-009: a futás megáll, ha bármely id átfedésben van."""
    overlap = set(train["id"].to_list()) & set(test["id"].to_list())
    assert not overlap, f"train/test átfedés: {sorted(overlap)[:5]}"


def split_teacher(labeled: pl.DataFrame, handchecked_jsonl) -> tuple[pl.DataFrame, pl.DataFrame]:
    """test = a kézzel ellenőrzött fagyott halmaz; train = tanár-címkék mínusz
    a kézi teszt azonosítói. 0 átfedés mindkét irányban (FR-009)."""
    hand = pl.DataFrame(load_jsonl(handchecked_jsonl)).select(["id", "text", "label"])
    test_ids = set(hand["id"].to_list())
    train = labeled.filter(~pl.col("id").is_in(test_ids))
    test = hand.with_columns(pl.lit(TASK).alias("task")).select(["task", "id", "text", "label"])
    assert_no_overlap(train, test)
    return train, test


def write_recipe_format(train: pl.DataFrame, test: pl.DataFrame, out_dir) -> None:
    """A tiny-classifiers recipe-sémája: task.json + train.jsonl/test.jsonl."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "task.json").write_text(
        json.dumps({"name": TASK, "instruction": INSTRUCTION, "labels": LABELS_EXPECTED},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    for frame, name in ((train, "train.jsonl"), (test, "test.jsonl")):
        with open(out_dir / name, "w", encoding="utf-8") as f:
            for row in frame.select("id", "text", "label").iter_rows(named=True):
                f.write(json.dumps(row, ensure_ascii=False) + "\n")


def tidy_and_split(texts_parquet, teacher_jsonl, handchecked_jsonl, tidy_dir, tasks_dir,
                   seed=0):
    """A Phase 6 végpontja: texts + tanár + kézi teszt -> tidy Parquet + recipe jsonl."""
    tidy_dir, tasks_dir = Path(tidy_dir), Path(tasks_dir)
    tidy_dir.mkdir(parents=True, exist_ok=True)
    texts = pl.read_parquet(texts_parquet)
    labeled = build_labeled(texts, teacher_jsonl)
    train, test = split_teacher(labeled, handchecked_jsonl)
    train.write_parquet(tidy_dir / "train.parquet")
    test.write_parquet(tidy_dir / "test.parquet")
    write_recipe_format(train, test, tasks_dir / TASK)
    meta = {"seed": seed, "n_train": len(train), "n_test": len(test),
            "test_source": "handchecked", "labels": LABELS_EXPECTED}
    (tidy_dir / "split_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return train, test
