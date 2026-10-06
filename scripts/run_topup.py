import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import polars as pl
from triage.stylegen import generate_topup

train = pl.read_parquet("data/tidy/train_hugbor.parquet")
stats = generate_topup(train, "data/labels/generated_v3.jsonl")
import json
print(json.dumps(stats, ensure_ascii=False, indent=2))
