"""T048: 005-os baseline — train_v5 (HugBor + top-up), valtozatlan recept, 3 seed.

Kimenet: runs/005-hugbor/metrics.json (osszes + kategoriankent, atlag ± szoras;
SC-002: >=90%) + a remapelt probe (SC-004: >=6/8 legalabb 2 seeden).
Futtatas: .venv/Scripts/python.exe scripts/run_hugbor.py
"""
import json
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import polars as pl

from triage.data import load_jsonl
from triage.evaluate import evaluate_run, predict_texts
from triage.train import train_run

SEEDS = [0, 1, 2]

train_df = pl.read_parquet("data/labels/train_v5.parquet")
test_df = pl.read_parquet("data/tidy/test_hugbor.parquet")
probe = load_jsonl("probes/wild_probe_v2.jsonl")

results = []
t0 = time.monotonic()
for s in SEEDS:
    run_dir = Path("runs") / f"005-hugbor-s{s}"
    metrics_path = run_dir / "metrics.json"
    if metrics_path.exists():  # resume: a kész seedet nem tanítjuk újra
        print(f"\n=== seed {s} (resume: tanítás kész, csak probe) ===", flush=True)
        m = json.loads(metrics_path.read_text(encoding="utf-8"))
    else:
        print(f"\n=== seed {s} ===", flush=True)
        train_run(train_df, test_df, run_dir, seed=s)
        m = evaluate_run(run_dir, test_df)
    probe_pred = predict_texts(run_dir / "model", [p["text"] for p in probe])
    probe_hits = sum(p == g for p, g in zip(probe_pred, [q["label"] for q in probe]))
    results.append({"seed": s, "accuracy": m["accuracy"],
                    "train_seconds": m.get("train_seconds"),
                    "per_category": m["per_category"],
                    "probe": f"{probe_hits}/{len(probe)}"})
    print(f"seed {s}: test={m['accuracy']:.1%} | probe={probe_hits}/8", flush=True)

accs = [r["accuracy"] for r in results]
labels = sorted(test_df["label"].unique().to_list())
per_cat = {}
for label in labels:
    vals = [r["per_category"][label]["accuracy"] for r in results]
    per_cat[label] = {"n": results[0]["per_category"][label]["n"],
                      "mean": statistics.mean(vals), "min": min(vals)}

out = Path("runs/005-hugbor")
out.mkdir(parents=True, exist_ok=True)
agg = {
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "seeds": SEEDS, "n_train": len(train_df), "n_test": len(test_df),
    "accuracies": accs,
    "mean_accuracy": statistics.mean(accs),
    "stdev_accuracy": statistics.stdev(accs),
    "probe_per_seed": [r["probe"] for r in results],
    "sc002_gate": statistics.mean(accs) >= 0.90,
    "sc004_probe": sum(1 for r in results if int(r["probe"].split("/")[0]) >= 6) >= 2,
    "total_seconds": round(time.monotonic() - t0, 1),
    "per_category": per_cat, "runs": results,
}
(out / "metrics.json").write_text(json.dumps(agg, ensure_ascii=False, indent=2),
                                  encoding="utf-8")
print(f"\n005 BASELINE: mean={agg['mean_accuracy']:.2%} ± {agg['stdev_accuracy']:.2%} "
      f"| SC-002 (>=90%): {'PASS' if agg['sc002_gate'] else 'FAIL'} "
      f"| probe: {agg['probe_per_seed']} | SC-004: {'PASS' if agg['sc004_probe'] else 'FAIL'}",
      flush=True)
for k, v in sorted(per_cat.items()):
    print(f"  {k:22s} {v['mean']:.1%} / min {v['min']:.1%} (n={v['n']})", flush=True)
