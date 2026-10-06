"""T045: vékony kategóriák feltöltése a helyi Qwennel (FR-005, FR-008).

Few-shot a HugBor saját sorai közül (plan D4: a dataset regiszterét követi),
kizárólag helyi végpont (FR-001/FR-008: felhő-fallback tilos).
"""
import json
import random
import time
import urllib.request
from pathlib import Path

import polars as pl

from triage.generate import dedupe_rows, is_english
from triage.hugbor import CATEGORIES, TRUNCATE_AT

DEFAULT_URL = "http://127.0.0.1:8080"
DEFAULT_MODEL = "models\\Qwen3.8-27B-UD-Q4_K_M.gguf"


def assert_local_only(url: str) -> None:
    """FR-008: a generálás kizárólag helyi végponton mehet (nincs felhő)."""
    assert url.startswith(("http://127.0.0.1", "http://localhost")), \
        f"felhős végpont tilos: {url}"


def thin_categories(counts: dict, min_rows: int = 100) -> dict:
    """{kategória: hiányzó sorok száma} a min_rows alatti kategóriákra."""
    return {c: min_rows - n for c, n in counts.items() if n < min_rows}


def build_topup_prompt(category: str, hugbor_df: pl.DataFrame, n: int, seed: int) -> str:
    """Few-shot prompt: a kategória 2 saját HugBor-sora mintaként (plan D4)."""
    own = hugbor_df.filter(pl.col("label") == category)
    rng = random.Random(seed)
    idx = rng.sample(range(len(own)), k=min(2, len(own)))
    shots = [own["text"][i][:300] for i in idx]
    return (
        "You write realistic ServiceNow incidents for a 500-person company, in "
        "ENGLISH ONLY, matching the style of these examples from the same category:\n\n"
        f"EXAMPLE 1 ({category}):\n{shots[0]}\n\n"
        + (f"EXAMPLE 2 ({category}):\n{shots[1]}\n\n" if len(shots) > 1 else "")
        + f"Now write {n} NEW, different incidents that clearly belong to the "
        f'"{category}" category. Vary systems, causes and phrasing; do not copy '
        "the examples. Answer with a JSON array of objects, each "
        '{"short_description": "...", "description": "..."}, no commentary.'
    )


def parse_topup(raw: str, category: str, batch_id: int) -> list[dict]:
    """JSON-tömb -> {id, text, label}; hibás sorok kimaradnak (sosem találgatunk)."""
    import re

    m = re.search(r"\[.*\]", raw or "", re.DOTALL)
    if not m:
        return []
    try:
        items = json.loads(m.group(0))
    except json.JSONDecodeError:
        return []
    rows = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        sd, desc = item.get("short_description"), item.get("description")
        if isinstance(sd, str) and sd.strip() and isinstance(desc, str) and desc.strip():
            rows.append({
                "id": f"gen-v3-{category[:4]}-{batch_id}-{i}",
                "text": f"{sd.strip()}. {desc.strip()}"[:TRUNCATE_AT],
                "label": category,
            })
    return rows


def _chat(url: str, model: str, prompt: str, temperature: float = 0.9,
          max_tokens: int = 4000, timeout: int = 180) -> str:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    req = urllib.request.Request(
        f"{url}/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    return r["choices"][0]["message"].get("content") or ""


def generate_topup(hugbor_train: pl.DataFrame, out_path, url=DEFAULT_URL,
                   model=DEFAULT_MODEL, min_rows=100, n_per_call=5, seed=0) -> dict:
    """Vékony kategóriák feltöltése; kimenet + stats (FR-005)."""
    assert_local_only(url)
    counts = {r["label"]: r["len"] for r in
              hugbor_train.group_by("label").len().iter_rows(named=True)}
    thin = thin_categories(counts, min_rows)
    rng = random.Random(seed)
    t0 = time.monotonic()
    rows: list[dict] = []
    bid = 0
    for category in sorted(thin):
        need = thin[category] + 4  # kis buffer a szűrésekre
        got = 0
        while got < need:
            prompt = build_topup_prompt(category, hugbor_train, n_per_call,
                                        seed + bid)
            try:
                raw = _chat(url, model, prompt)
            except Exception as e:  # végpont-hiba: megállunk és jelentjük
                print(f"HIBA a végpontnál ({category}): {e}", flush=True)
                break
            batch = parse_topup(raw, category, bid)
            batch = [r for r in batch if is_english(r["text"])]
            rows.extend(batch)
            got += len(batch)
            bid += 1
            if bid % 5 == 0:
                print(f"  {category}: {got}/{need} | {time.monotonic()-t0:.0f}s",
                      flush=True)
    deduped = dedupe_rows(rows)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for r in deduped:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    stats = {
        "model": model, "url": url, "thin": thin,
        "generated_raw": len(rows), "after_dedup": len(deduped),
        "seconds": round(time.monotonic() - t0, 1),
        "per_category": {c: sum(1 for r in deduped if r["label"] == c)
                         for c in sorted(thin)},
    }
    (out_path.parent / "stylegen_stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    return stats
