"""User-voice top-up (SC-004 javítása): felhasználói hangú incidentek generálása.

A HugBor-adatok monitoring/ops-stílusúak; a probe-hibák felhasználói hangú
szövegeken voltak. Few-shot NEM a probe-sorok (az adatszivárgás lenne),
hanem külön írt user-voice exemplarok. Helyi Qwen, nulla felhő.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import polars as pl

from triage.generate import dedupe_rows, is_english, normalize_text
from triage.hugbor import CATEGORIES, TRUNCATE_AT
from triage.stylegen import _chat, assert_local_only, parse_topup

URL = "http://127.0.0.1:8080"
MODEL = "models\\Qwen3.8-27B-UD-Q4_K_M.gguf"
PER_CATEGORY = 10

USER_VOICE_EXAMPLE = (
    "Hi, our office printer on the 3rd floor has been flashing a red error "
    "light since Monday and nobody can print. We tried turning it off and on "
    "but the error comes back after a few pages. About fifteen of us rely on "
    "it for shipping documents. Could someone take a look today please?"
)


def build_user_voice_prompt(category: str, n: int, seed: int) -> str:
    return (
        "You write realistic IT support tickets for a 500-person company, in "
        "ENGLISH ONLY.\n\n"
        "Style: written BY THE END USER, first person, everyday language — "
        "frustrated, polite, or worried; NOT a monitoring alert, NOT a "
        "postmortem, NO tool names like CloudWatch or PagerDuty unless the "
        "user would plausibly see them. 4-7 sentences: what happened, what "
        "they tried, who is affected, what they need.\n\n"
        f"STYLE EXAMPLE (different category):\n{USER_VOICE_EXAMPLE}\n\n"
        f"Now write {n} DIFFERENT tickets in this end-user voice that clearly "
        f'belong to the "{category}" support category. Vary the issues, tone '
        "and length slightly. Answer with a JSON array of objects, each "
        '{"short_description": "...", "description": "..."}, no commentary.'
    )


def main():
    assert_local_only(URL)
    t0 = time.monotonic()
    rows, bid = [], 0
    for category in CATEGORIES:
        got = 0
        while got < PER_CATEGORY + 2:
            raw = _chat(URL, MODEL, build_user_voice_prompt(category, 5, bid),
                        max_tokens=4000)
            batch = parse_topup(raw, category, bid)
            batch = [r for r in batch if is_english(r["text"])]
            rows.extend(batch)
            got += len(batch)
            bid += 1
        print(f"{category}: {got} | {time.monotonic()-t0:.0f}s", flush=True)

    deduped = dedupe_rows(rows)
    # mondatvég-igazítás (mint a v3-nál)
    import re
    for r in deduped:
        t = r["text"]
        if len(t) == TRUNCATE_AT and t[-1] not in ".!?":
            m = list(re.finditer(r"[.!?] ", t))
            if m and m[-1].end() > 300:
                r["text"] = t[: m[-1].end() - 1]

    out = Path("data/labels/generated_uservoice.jsonl")
    with open(out, "w", encoding="utf-8") as f:
        for r in deduped:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # teszt-átfedés-ellenőrző
    test = pl.read_parquet("data/tidy/test_hugbor.parquet")
    test_texts = {normalize_text(t) for t in test["text"].to_list()}
    hits = [r for r in deduped if normalize_text(r["text"]) in test_texts]
    assert not hits, f"átfedés a teszttel: {len(hits)}"

    stats = {"generated": len(deduped), "seconds": round(time.monotonic() - t0, 1),
             "per_category": {c: sum(1 for r in deduped if r["label"] == c)
                              for c in CATEGORIES}}
    print(json.dumps(stats, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
