"""T008: egyedi osztályozás + időmérés (SC-004).

A modellt az első hívás tölti be, utána memóriában marad (lru_cache) —
a hidegstart nem része a per-ticket latenciának.
Üres/túl rövid szöveg: jelzés, nem magabiztos rossz válasz (spec Edge Cases).
"""
import time
from functools import lru_cache
from pathlib import Path

MIN_CHARS = 10  # ez alatt a bemenet "nem osztályozható megbízhatóan"


@lru_cache(maxsize=4)
def _load_model(model_dir: str):
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForSequenceClassification.from_pretrained(model_dir).eval()
    labels = [model.config.id2label[i] for i in range(model.config.num_labels)]
    return tok, model, labels


def predict_one(model_dir, text: str) -> dict:
    """Egy ticket osztályozása; ms-méréssel (modell memóriában)."""
    import torch

    text = (text or "").strip()
    if len(text) < MIN_CHARS:
        return {"label": None, "ok": False,
                "reason": f"a szöveg túl rövid ({len(text)} < {MIN_CHARS} karakter)"}
    tok, model, labels = _load_model(str(Path(model_dir)))
    t0 = time.monotonic()
    with torch.no_grad():
        enc = tok(text, truncation=True, max_length=128, return_tensors="pt")
        label = labels[model(**enc).logits.argmax(1).item()]
    ms = (time.monotonic() - t0) * 1000
    return {"label": label, "ok": True, "ms": round(ms, 1)}
