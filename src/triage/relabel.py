"""T030: határeset-jelöltek és átütemezés — FR-002, FR-003.

A jelöltek kulcsszabálya a 003-as konfúziós térképből vezetett (D2):
a szabály csak jelöl, a döntés a felhasználóé (T031, MANUÁLIS KAPU).
Csak jóváhagyott sorok íródnak át; az eredmény új, verziózott fájl.
"""
import re
from pathlib import Path

import polars as pl

from triage.data import LABELS_EXPECTED, TASK, assert_no_overlap

# A konfúziós térkép (runs/003-confusion) alapján — minden szabály dokumentált
RULES = [
    # (szabály neve, regex, javasolt címke) — a felhasználó T017-es döntéseiből
    ("mfa-security", r"(?i)MFA (push|fatigue|prompt)|MFA not|MFA-code", "Security"),
    ("teams-camera-pd", r"(?i)meeting room camera|camera flickers", "Printers & Devices"),
    ("webcam-pd", r"(?i)webcam (missing|not detected|not working)", "Printers & Devices"),
    ("docking-pd", r"(?i)docking station", "Printers & Devices"),
    ("spam-security", r"(?i)spam (burst|wave|campaign)|phishing", "Security"),
    ("wms-access-erp", r"(?i)temporary access to WMS|WMS access", "ERP / WMS"),
    ("shared-drive-network", r"(?i)map shared drive|shared drive", "Network & VPN"),
    ("voicemail-telephony", r"(?i)voicemail", "Telephony"),
]


def find_candidates(df: pl.DataFrame) -> list[dict]:
    """Kulcsszavas jelöltek a tanítóhalmazból (FR-002)."""
    out = []
    for row in df.iter_rows(named=True):
        for name, pattern, suggested in RULES:
            if re.search(pattern, row["text"]) and row["label"] != suggested:
                out.append({"id": row["id"], "text": row["text"],
                            "current_label": row["label"],
                            "suggested_label": suggested, "rule": name})
                break  # egy sorhoz egy szabály
    return out


def write_review_csv(candidates: list[dict], out_path) -> None:
    pl.DataFrame([{**c, "relabel_to": ""} for c in candidates]).write_csv(out_path)


def apply_relabels(df: pl.DataFrame, decisions: list[dict]):
    """Csak a jóváhagyott (kitöltött relabel_to) ÉS jelölt sorok változnak.

    Visszatér: (új DataFrame, napló). A cél-címke a 8 kategória egyike kell legyen.
    """
    valid = set(LABELS_EXPECTED)
    cand_ids = {c["id"] for c in find_candidates(df)}
    changes = {}
    for d in decisions:
        target = (d.get("relabel_to") or "").strip()
        if not target or d["id"] not in cand_ids:
            continue
        if target not in valid:
            raise ValueError(f"ismeretlen cél-kategória: {target}")
        changes[d["id"]] = target
    mapping = pl.DataFrame({"id": list(changes), "new_label": list(changes.values())})
    out = df.join(mapping, on="id", how="left").with_columns(
        pl.when(pl.col("new_label").is_not_null())
          .then(pl.col("new_label")).otherwise(pl.col("label")).alias("label")
    ).drop("new_label")
    log = [{"id": k, "relabel_to": v} for k, v in changes.items()]
    return out, log


def build_v3(train_v2: pl.DataFrame, decisions_csv, test_df: pl.DataFrame,
             out_path) -> tuple[pl.DataFrame, list]:
    """A jóváhagyott döntésekből az új tanítóhalmaz (FR-003, D3)."""
    decisions = pl.read_csv(decisions_csv).to_dicts()
    v3, log = apply_relabels(train_v2, decisions)
    assert_no_overlap(v3, test_df)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    v3.write_parquet(out_path)
    return v3, log
