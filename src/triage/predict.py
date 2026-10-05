"""T008: egyedi osztályozás + időmérés (SC-004).

Üres/túl rövid szöveg: jelzés, nem magabiztos rossz válasz (spec Edge Cases).
"""
import time
from pathlib import Path

MIN_CHARS = 10  # ez alatt a bemenet "nem osztályozható megbízhatóan"


def predict_one(model_dir, text: str) -> dict:
    """Egy ticket osztályozása; ms-méréssel."""
    from triage.evaluate import predict_texts

    text = (text or "").strip()
    if len(text) < MIN_CHARS:
        return {"label": None, "ok": False,
                "reason": f"a szöveg túl rövid ({len(text)} < {MIN_CHARS} karakter)"}
    t0 = time.monotonic()
    label = predict_texts(Path(model_dir), [text], batch=1)[0]
    ms = (time.monotonic() - t0) * 1000
    return {"label": label, "ok": True, "ms": round(ms, 1)}
