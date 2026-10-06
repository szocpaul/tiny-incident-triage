"""T042/T043: HugBor tidy + stratified holdout + label-trust spot-check.

FR-001/002/004: text = short_description + description, uniform truncation
(~500 chars), stratified 80/20 split (seed=0), 0 overlap.
FR-003: the local teacher blind-labels a stratified sample; agreement rate
with the dataset labels is the trust evidence (SC-001: >= 90% else stop).
"""
import json
from pathlib import Path

import polars as pl
from dpyr import read, col, lit

from triage.data import assert_no_overlap, load_jsonl

TASK = "hugbor_servicenow"

# A Software→Application összevonás a felhasználó 2026-10-06-os döntésével
# (a spot-check elemzés: a Software↔Application határ emberileg is vitatható).
# Forrás-HugBor-kategóriák a cél-kategóriákra:
CATEGORY_MAP = {
    "Access Management": "Access Management",
    "Application": "Application",
    "Software": "Application",  # merged (spec amendment 2026-10-06)
    "Backup/Recovery": "Backup/Recovery",
    "Cloud Services": "Cloud Services",
    "Data Center": "Data Center",
    "Database": "Database",
    "Email": "Email",
    "Hardware": "Hardware",
    "Network": "Network",
    "Performance": "Performance",
    "Printer/Peripherals": "Printer/Peripherals",
    "Security": "Security",
    "Telephony": "Telephony",
    "VPN": "VPN",
}

CATEGORIES = sorted(set(CATEGORY_MAP.values()))  # 14 kategória az összevonás után

TRUNCATE_AT = 500  # ~128 token recipe window (plan D1, FR-004)


def truncate_text(text: str, limit: int = TRUNCATE_AT) -> str:
    """Uniform truncation to the recipe window (FR-004)."""
    return text[:limit] if len(text) > limit else text


def build_tidy_hugbor(csv_path) -> pl.DataFrame:
    """HugBor CSV -> tidy tábla (task, id, text, label), dpyr verbekkel."""
    df = (
        read(str(csv_path))
        .mutate(task=lit(TASK), label=col.category)
        .unite("id", [col.task, col.number], sep="-", remove=False)
        .unite("text", [col.short_description, col.description], sep=". ")
        .select(col.task, col.id, col.text, col.label)
    )
    out = df.collect()
    out = out.with_columns(
        pl.col("label").map_elements(lambda c: CATEGORY_MAP[c], return_dtype=pl.String).alias("label"),
        pl.col("text").map_elements(truncate_text, return_dtype=pl.String).alias("text"),
    )
    return out


def split_holdout(df: pl.DataFrame, test_frac: float = 0.2, seed: int = 0):
    """Rétegzett holdout kategóriánként (D3); 0 átfedés igazolva."""
    train_parts, test_parts = [], []
    for label in sorted(df["label"].unique().to_list()):
        part = df.filter(pl.col("label") == label).sample(
            fraction=1.0, shuffle=True, seed=seed)
        n_te = max(1, round(len(part) * test_frac))
        test_parts.append(part.head(n_te))
        train_parts.append(part.slice(n_te))
    train = pl.concat(train_parts)
    test = pl.concat(test_parts)
    assert_no_overlap(train, test)
    return train, test


def agreement_rate(a: list, b: list) -> float:
    """A spot-check egyetértési aránya (SC-001)."""
    return sum(x == y for x, y in zip(a, b)) / len(a) if a else 0.0


def spotcheck_labels(sample_texts: list[str], model_url: str, model_id: str) -> list[str]:
    """A helyi tanár vakon címkéz (blind): a 15 kategória a promptban (D2)."""
    import urllib.request

    system = ("Classify the IT incident by its support category. Answer with "
              "exactly one label from this list:\n" + "\n".join(CATEGORIES))
    preds = []
    for text in sample_texts:
        payload = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": text},
            ],
            "max_tokens": 600,
            "temperature": 0,
        }
        req = urllib.request.Request(
            f"{model_url}/v1/chat/completions",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        r = json.load(urllib.request.urlopen(req, timeout=180))
        answer = (r["choices"][0]["message"].get("content") or "").strip().strip("`*.\"' ")
        preds.append({c.lower(): c for c in CATEGORIES}.get(answer.lower()))
    return preds
