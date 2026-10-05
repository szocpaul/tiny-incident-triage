"""T025: 002-es újramérés — bővített tanítóhalmaz, változatlan recept, 3 seed.

Kimenet: runs/002-boost/metrics.json, a baseline-teacher-rel összevetve
(SC-001/002/003, nem-átfedő intervallum-ítélet).
Futtatás: .venv/Scripts/python.exe scripts/run_boost.py
"""
import json
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import polars as pl

from triage.data import merge_generated
from triage.evaluate import evaluate_run
from triage.train import train_run

SEEDS = [0, 1, 2]
CAPS = {"Security": 100, "Printers & Devices": 60, "Laptop / Endpoint": 40}  # plan D1

train_df = pl.read_parquet("data/tidy/train.parquet")
test_df = pl.read_parquet("data/tidy/test.parquet")
extended = merge_generated(train_df, "data/labels/generated_v2.jsonl", CAPS, test_df)
print(f"bővített tanítóhalmaz: {len(train_df)} -> {len(extended)} sor", flush=True)

results = []
t0 = time.monotonic()
for s in SEEDS:
    run_dir = Path("runs") / f"002-boost-s{s}"
    print(f"\n=== seed {s} ===", flush=True)
    train_run(extended, test_df, run_dir, seed=s)
    m = evaluate_run(run_dir, test_df)
    results.append({"seed": s, "accuracy": m["accuracy"],
                    "train_seconds": m.get("train_seconds"),
                    "per_category": m["per_category"]})
    print(f"seed {s}: accuracy={m['accuracy']:.1%}", flush=True)

baseline = json.loads(Path("runs/baseline-teacher/metrics.json").read_text(encoding="utf-8"))
accs = [r["accuracy"] for r in results]
labels = sorted(test_df["label"].unique().to_list())
per_cat = {}
for label in labels:
    vals = [r["per_category"][label]["accuracy"] for r in results]
    base = baseline["per_category_mean"][label]
    per_cat[label] = {
        "n": base["n"], "baseline_mean": base["mean"],
        "boost_mean": statistics.mean(vals), "boost_min": min(vals),
        "improved": statistics.mean(vals) > base["mean"],
    }

out = Path("runs/002-boost")
out.mkdir(parents=True, exist_ok=True)
agg = {
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "seeds": SEEDS, "caps": CAPS, "n_train": len(extended),
    "accuracies": accs,
    "mean_accuracy": statistics.mean(accs),
    "stdev_accuracy": statistics.stdev(accs),
    "baseline_mean_accuracy": baseline["mean_accuracy"],
    "baseline_stdev": baseline["stdev_accuracy"],
    "non_overlapping_vs_baseline": min(accs) > baseline["mean_accuracy"] + baseline["stdev_accuracy"],
    "n_test": len(test_df), "total_seconds": round(time.monotonic() - t0, 1),
    "per_category": per_cat, "runs": results,
}
(out / "metrics.json").write_text(json.dumps(agg, ensure_ascii=False, indent=2),
                                  encoding="utf-8")
print(f"\nBOOST: mean={agg['mean_accuracy']:.2%} ± {agg['stdev_accuracy']:.2%} "
      f"(baseline: {baseline['mean_accuracy']:.2%} ± {baseline['stdev_accuracy']:.2%})",
      flush=True)
for k, v in sorted(per_cat.items()):
    print(f"  {k:22s} {v['baseline_mean']:.1%} -> {v['boost_mean']:.1%}", flush=True)
