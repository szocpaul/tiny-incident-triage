"""T043: label-trust spot-check (SC-001) — a helyi Qwen vakon címkéz 75 sort.

Kimenet: runs/005-hugbor/spotcheck.json (egyetértési arány; <90% = STOP).
Futtatás: .venv/Scripts/python.exe scripts/run_spotcheck.py
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import polars as pl

from triage.hugbor import CATEGORIES, agreement_rate, spotcheck_labels

MODEL_URL = "http://127.0.0.1:8080"
MODEL_ID = "models\\Qwen3.8-27B-UD-Q4_K_M.gguf"
PER_CAT = 5

test = pl.read_parquet("data/tidy/test_hugbor.parquet")
parts = []
for label in CATEGORIES:
    part = test.filter(pl.col("label") == label)
    parts.append(part.head(PER_CAT))
sample = pl.concat(parts)
print(f"minta: {len(sample)} sor ({PER_CAT}/kategória)", flush=True)

t0 = time.monotonic()
preds = spotcheck_labels(sample["text"].to_list(), MODEL_URL, MODEL_ID)
gold = sample["label"].to_list()
rate = agreement_rate(preds, gold)
none_count = sum(1 for p in preds if p is None)

rows = [{"id": i, "gold": g, "qwen": p, "match": g == p}
        for i, g, p in zip(sample["id"].to_list(), gold, preds)]
per_cat = {}
for label in CATEGORIES:
    idx = [i for i, g in enumerate(gold) if g == label]
    per_cat[label] = agreement_rate([preds[i] for i in idx], [gold[i] for i in idx])

out = Path("runs/005-hugbor")
out.mkdir(parents=True, exist_ok=True)
result = {
    "n": len(sample), "agreement": rate, "invalid_qwen_answers": none_count,
    "seconds": round(time.monotonic() - t0, 1),
    "per_category": per_cat, "threshold": 0.90,
    "gate": "PASS" if rate >= 0.90 else "STOP",
    "rows": rows,
}
(out / "spotcheck.json").write_text(json.dumps(result, ensure_ascii=False, indent=2),
                                    encoding="utf-8")
print(f"SC-001: agreement={rate:.1%} (küszöb 90%) -> {result['gate']}", flush=True)
