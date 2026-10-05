"""T032: 003-as újramérés — átütemezett v3 tanítóhalmaz, változatlan recept, 3 seed.

Kimenet: runs/003-relabel/metrics.json, 4-oszlopos összevetéssel
(zaj / teacher / boost / relabel), nem-átfedő intervallum-ítélettel.
Futtatás: .venv/Scripts/python.exe scripts/run_relabel.py
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

train_df = pl.read_parquet("data/labels/train_v3.parquet")
test_df = pl.read_parquet("data/tidy/test.parquet")  # fagyott kézi teszt (változatlan)

results = []
t0 = time.monotonic()
for s in SEEDS:
    run_dir = Path("runs") / f"003-relabel-s{s}"
    print(f"\n=== seed {s} ===", flush=True)
    train_run(train_df, test_df, run_dir, seed=s)
    m = evaluate_run(run_dir, test_df)
    results.append({"seed": s, "accuracy": m["accuracy"],
                    "train_seconds": m.get("train_seconds"),
                    "per_category": m["per_category"]})
    print(f"seed {s}: accuracy={m['accuracy']:.1%}", flush=True)

refs = {
    "zaj": json.loads(Path("runs/baseline/metrics.json").read_text(encoding="utf-8")),
    "teacher": json.loads(Path("runs/baseline-teacher/metrics.json").read_text(encoding="utf-8")),
    "boost": json.loads(Path("runs/002-boost/metrics.json").read_text(encoding="utf-8")),
}
accs = [r["accuracy"] for r in results]
labels = sorted(test_df["label"].unique().to_list())
per_cat = {}
for label in labels:
    vals = [r["per_category"][label]["accuracy"] for r in results]
    per_cat[label] = {
        "n": results[0]["per_category"][label]["n"],
        "teacher": refs["teacher"]["per_category_mean"][label]["mean"],
        "boost": refs["boost"]["per_category"][label]["boost_mean"],
        "relabel_mean": statistics.mean(vals), "relabel_min": min(vals),
    }

out = Path("runs/003-relabel")
out.mkdir(parents=True, exist_ok=True)
agg = {
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "seeds": SEEDS, "n_train": len(train_df), "relabeled_rows": 105,
    "accuracies": accs,
    "mean_accuracy": statistics.mean(accs),
    "stdev_accuracy": statistics.stdev(accs),
    "reference_means": {k: v["mean_accuracy"] for k, v in refs.items()},
    "non_overlapping_vs_boost": min(accs) > refs["boost"]["mean_accuracy"] + refs["boost"]["stdev_accuracy"],
    "n_test": len(test_df), "total_seconds": round(time.monotonic() - t0, 1),
    "per_category": per_cat, "runs": results,
}
(out / "metrics.json").write_text(json.dumps(agg, ensure_ascii=False, indent=2),
                                  encoding="utf-8")
print(f"\nRELABEL: mean={agg['mean_accuracy']:.2%} ± {agg['stdev_accuracy']:.2%}", flush=True)
print(f"{'kategória':22s} {'teacher':>8s} {'boost':>8s} {'relabel':>8s}")
for k, v in sorted(per_cat.items()):
    print(f"  {k:22s} {v['teacher']:8.1%} {v['boost']:8.1%} {v['relabel_mean']:8.1%}",
          flush=True)
