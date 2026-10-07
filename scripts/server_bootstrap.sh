#!/usr/bin/env bash
# Server bootstrap: regenerates the gitignored data + the 005 final model
# on a fresh clone. Deterministic (fixed seeds) — produces bit-identical
# artifacts to the originals. Run: bash scripts/server_bootstrap.sh
set -euo pipefail

cd "$(dirname "$0")/.."
PY=".venv/bin/python"

echo "== 1/4: HugBor letöltése (pinnelt commit) =="
mkdir -p data/raw
HUGBOR_SHA="2344a8b8aec1bbeebbaffdd541a3bfd901af36c6"
if [ ! -f data/raw/hugbor.csv ]; then
  curl -sL "https://huggingface.co/datasets/HugBor/servicenow_incidents_slm6/resolve/${HUGBOR_SHA}/servicenow_incidents_2k.csv" \
    -o data/raw/hugbor.csv
fi
wc -l data/raw/hugbor.csv

echo "== 2/4: tidy + stratifikált split (seed=0, determinisztikus) =="
$PY - <<'EOF'
import sys
sys.path.insert(0, "src")
import json
import polars as pl
from triage.hugbor import build_tidy_hugbor, split_holdout

df = build_tidy_hugbor("data/raw/hugbor.csv")
train, test = split_holdout(df, test_frac=0.2, seed=0)
assert len(train) == 1310 and len(test) == 330, "a split nem egyezik az eredetivel!"
train.write_parquet("data/tidy/train_hugbor.parquet")
test.write_parquet("data/tidy/test_hugbor.parquet")
with open("data/labels/hugbor_test.jsonl", "w", encoding="utf-8") as f:
    for r in test.iter_rows(named=True):
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print(f"tidy OK: {len(train)} train / {len(test)} test")
EOF

echo "== 3/4: címkék és train_v6 ellenőrzése (commitolva kell legyenek) =="
for f in data/labels/train_v6.parquet data/labels/handchecked_test_v2.jsonl probes/wild_probe_v2.jsonl; do
  [ -f "$f" ] || { echo "HIÁNYZIK: $f — a repóból kellene jönnie!"; exit 1; }
done
echo "címkék OK"

echo "== 4/4: az 005-ös végleges modell újratanítása (runs/005-uservoice-s1) =="
echo "   (4 vCPU: ~50 perc — a runner ezt háttérben futtathatja)"
$PY - <<'EOF'
import sys
sys.path.insert(0, "src")
import polars as pl
from triage.train import train_run
from triage.evaluate import evaluate_run

train_df = pl.read_parquet("data/labels/train_v6.parquet")
test_df = pl.read_parquet("data/tidy/test_hugbor.parquet")
config = train_run(train_df, test_df, "runs/005-uservoice-s1", seed=1)
m = evaluate_run("runs/005-uservoice-s1", test_df)
print(f"005 modell kész: accuracy={m['accuracy']:.1%} (várható ~94-95%)")
EOF

echo "== KÉSZ: a szerver a 006-os runner-feladatokra kész =="
