"""T028: konfúziós riport — melyik kategória melyikkel keveredik (FR-001).

A 003-as feature első artifactja: a javítás csak a mért párokat célozhatja
(SC-004).
"""
import json
from pathlib import Path


def confusion_report(ids, texts, y_true, y_pred, labels, out_dir=None) -> dict:
    """Mátrix + tévesztett sorok listája; opcionálisan report.json-be ír."""
    matrix = {t: {p: 0 for p in labels} for t in labels}
    misclassified = []
    for id_, text, t, p in zip(ids, texts, y_true, y_pred):
        matrix[t][p] += 1
        if t != p:
            misclassified.append({"id": id_, "text": text, "true": t, "pred": p})
    n = len(y_true)
    report = {
        "n_test": n,
        "accuracy": sum(t == p for t, p in zip(y_true, y_pred)) / n if n else 0.0,
        "matrix": matrix,
        "misclassified": misclassified,
    }
    if out_dir:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def top_confusions(report: dict, top_n=10) -> list[dict]:
    """A leggyakoribb (helyes -> jósolt) tévesztési párok, sorlistával."""
    pairs: dict[tuple[str, str], list[dict]] = {}
    for row in report["misclassified"]:
        pairs.setdefault((row["true"], row["pred"]), []).append(row)
    ranked = sorted(pairs.items(), key=lambda kv: -len(kv[1]))
    return [{"true": t, "pred": p, "n": len(rows), "rows": rows}
            for (t, p), rows in ranked[:top_n]]
