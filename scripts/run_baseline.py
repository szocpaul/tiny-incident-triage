"""T010: baseline futtatás 3 seeddel (0, 1, 2) — a repó "means of 3 runs" módszertana.

Kimenet: runs/baseline/metrics.json (átlag + szórás + seed-enkénti részletek).
Futtatás: .venv/Scripts/python.exe scripts/run_baseline.py
"""
import json
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import polars as pl

from triage.evaluate import evaluate_run
from triage.train import train_run

SEEDS = [0, 1, 2]
RUN_PREFIX = "baseline-teacher"
OUT_DIR = Path("runs/baseline-teacher")

train_df = pl.read_parquet("data/tidy/train.parquet")
test_df = pl.read_parquet("data/tidy/test.parquet")

results = []
t0 = time.monotonic()
for s in SEEDS:
    run_dir = Path("runs") / f"{RUN_PREFIX}-s{s}"
    print(f"\n=== seed {s} ===", flush=True)
    train_run(train_df, test_df, run_dir, seed=s)
    m = evaluate_run(run_dir, test_df)
    results.append({"seed": s, "accuracy": m["accuracy"],
                    "train_seconds": m.get("train_seconds"),
                    "per_category": m["per_category"]})
    print(f"seed {s}: accuracy={m['accuracy']:.1%}", flush=True)

accs = [r["accuracy"] for r in results]
labels = sorted(test_df["label"].unique().to_list())
per_cat = {}
for label in labels:
    vals = [r["per_category"][label]["accuracy"] for r in results]
    per_cat[label] = {"n": results[0]["per_category"][label]["n"],
                      "mean": statistics.mean(vals), "min": min(vals)}

out = OUT_DIR
out.mkdir(parents=True, exist_ok=True)
agg = {
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "seeds": SEEDS,
    "accuracies": accs,
    "mean_accuracy": statistics.mean(accs),
    "stdev_accuracy": statistics.stdev(accs),
    "n_test": len(test_df),
    "total_seconds": round(time.monotonic() - t0, 1),
    "per_category_mean": per_cat,
    "runs": results,
}
(out / "metrics.json").write_text(json.dumps(agg, ensure_ascii=False, indent=2),
                                  encoding="utf-8")
print(f"\nBASELINE: mean={agg['mean_accuracy']:.2%} ± {agg['stdev_accuracy']:.2%} "
      f"(n={len(test_df)}, {agg['total_seconds']} s)", flush=True)
