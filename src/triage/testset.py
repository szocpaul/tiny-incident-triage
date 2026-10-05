"""T035: teszthalmaz-tisztítás — konfliktus-keresés, döntés-alkalmazás, verziózás.

A duplikátum-definíció a generate.normalize_text (plan D1); a v1 archív
sosem íródik felül (plan D2); a fagyasztás csak teljes döntési táblával
(FR-002).
"""
import csv
import json
import shutil
from pathlib import Path

import polars as pl

from triage.data import LABELS_EXPECTED, TASK, assert_no_overlap, load_jsonl
from triage.generate import normalize_text


def find_conflicts(test_jsonl) -> list[dict]:
    """Duplikált (normalizált) szövegek >1 distinct címkével (FR-001)."""
    rows = load_jsonl(test_jsonl)
    groups: dict[str, list[dict]] = {}
    for r in rows:
        groups.setdefault(normalize_text(r["text"]), []).append(r)
    out = []
    for key, members in groups.items():
        labels = sorted({m["label"] for m in members})
        if len(labels) > 1:
            out.append({"key": key, "count": len(members), "labels": labels,
                        "ids": [m["id"] for m in members],
                        "texts": [m["text"] for m in members]})
    return out


def write_decisions_template(groups: list[dict], out_path) -> None:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["group", "text", "labels", "ids",
                                          "decision", "reason"])
        w.writeheader()
        for i, g in enumerate(groups):
            w.writerow({"group": i, "text": g["texts"][0],
                        "labels": " | ".join(g["labels"]),
                        "ids": " | ".join(g["ids"]), "decision": "", "reason": ""})


def _read_decisions(decisions_csv) -> list[dict]:
    with open(decisions_csv, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def apply_decisions(rows: list[dict], groups: list[dict], decisions: list[dict]):
    """A felhasználó döntései: kanonikus címke (1 példány marad) vagy 'drop'.

    Kitöltetlen döntés = ValueError (FR-002: a fagyasztás megáll).
    """
    if len(decisions) != len(groups):
        raise ValueError(f"{len(decisions)} döntés érkezett, {len(groups)} kell")
    for d in decisions:
        dec = (d.get("decision") or "").strip()
        if not dec:
            raise ValueError(f"kitöltetlen döntés: group {d.get('group')}")
        if dec != "drop" and dec not in LABELS_EXPECTED:
            raise ValueError(f"ismeretlen címke: {dec}")

    drop_ids, canon = set(), {}
    log = []
    for d, g in zip(decisions, groups):
        dec = d["decision"].strip()
        if dec == "drop":
            drop_ids.update(g["ids"])
            log.append({"group": d["group"], "decision": "drop",
                        "dropped": g["ids"], "reason": d.get("reason", "")})
        else:
            keep, rest = g["ids"][0], g["ids"][1:]
            drop_ids.update(rest)
            canon[keep] = dec
            log.append({"group": d["group"], "decision": dec, "kept": keep,
                        "dropped": rest, "reason": d.get("reason", "")})
    new_rows = []
    for r in rows:
        if r["id"] in drop_ids:
            continue
        if r["id"] in canon:
            r = {**r, "label": canon[r["id"]]}
        new_rows.append(r)
    return new_rows, log


def freeze_v2(v1_path, new_rows: list[dict], train_parquet, labels_dir,
              test_parquet_out, changelog) -> Path:
    """v1 archiválása érintetlenül, v2 fagyasztása, changelog, 0-átfedés (FR-003)."""
    labels_dir = Path(labels_dir)
    labels_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(v1_path, labels_dir / "handchecked_test_v1.jsonl")
    v2_path = labels_dir / "handchecked_test_v2.jsonl"
    with open(v2_path, "w", encoding="utf-8") as f:
        for r in new_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    (labels_dir / "testset_v2_changelog.json").write_text(
        json.dumps(changelog, ensure_ascii=False, indent=2), encoding="utf-8")
    test_df = pl.DataFrame(new_rows).with_columns(pl.lit(TASK).alias("task")) \
        .select(["task", "id", "text", "label"])
    train_df = pl.read_parquet(train_parquet)
    assert_no_overlap(train_df, test_df)
    test_df.write_parquet(test_parquet_out)
    return v2_path


def decisions_from_csv(decisions_csv):
    return _read_decisions(decisions_csv)
