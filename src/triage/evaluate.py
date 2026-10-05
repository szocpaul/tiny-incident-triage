"""T007: értékelés — teljes + kategóriánkénti pontosság, exit-code gate (FR-004)."""
import json
import time
from datetime import datetime, timezone
from pathlib import Path


def write_metrics(run_dir, y_true, y_pred, labels, extra=None) -> Path:
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    n = len(y_true)
    acc = sum(p == g for p, g in zip(y_pred, y_true)) / n if n else 0.0
    per_category = {}
    for label in labels:
        idx = [i for i, g in enumerate(y_true) if g == label]
        hits = sum(y_pred[i] == y_true[i] for i in idx)
        per_category[label] = {
            "n": len(idx),
            "accuracy": hits / len(idx) if idx else None,
        }
    metrics = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "n_test": n,
        "accuracy": acc,
        "per_category": per_category,
        **(extra or {}),
    }
    path = run_dir / "metrics.json"
    path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def check_threshold(metrics: dict, min_accuracy: float) -> int:
    """SC-001 gate: 0, ha teljesül, 1, ha nem (exit-code-os parancs, Constitution I)."""
    return 0 if metrics["accuracy"] >= min_accuracy else 1


def evaluate_run(run_dir, test_df, min_accuracy=0.90) -> dict:
    """Betölti a run modelljét, osztályozza a fagyott teszthalmazt, metrics.json-t ír."""
    run_dir = Path(run_dir)
    texts = test_df["text"].to_list()
    y_true = test_df["label"].to_list()
    labels = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))["labels"]
    y_pred = predict_texts(run_dir / "model", texts)
    extra = {}
    config = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
    if "train_seconds" in config:
        extra["train_seconds"] = config["train_seconds"]
    path = write_metrics(run_dir, y_true, y_pred, labels, extra=extra)
    metrics = json.loads(path.read_text(encoding="utf-8"))
    metrics["gate_exit_code"] = check_threshold(metrics, min_accuracy)
    path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    return metrics


def predict_texts(model_dir, texts, batch=256):
    """CPU-n, batch-elve; az időmérés a predict.py-ban (SC-004)."""
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForSequenceClassification.from_pretrained(model_dir).eval()
    labels = [model.config.id2label[i] for i in range(model.config.num_labels)]
    out = []
    with torch.no_grad():
        for i in range(0, len(texts), batch):
            enc = tok(texts[i:i + batch], truncation=True, max_length=128,
                      padding=True, return_tensors="pt")
            out += [labels[k] for k in model(**enc).logits.argmax(1).tolist()]
    return out


def measure_latency(model_dir, texts):
    """SC-004: ms/db, egyedi hívásonként."""
    total, t0 = 0.0, None
    preds = []
    start = time.monotonic()
    for t in texts:
        preds.append(predict_texts(model_dir, [t], batch=1)[0])
    total = time.monotonic() - start
    return preds, total / len(texts) * 1000 if texts else 0.0
