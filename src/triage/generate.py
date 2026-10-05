"""T021: célzott szintetikus ticketgyártás a gyenge kategóriákhoz (plan D1/D2).

A címke konstrukció szerinti: a tanár egy (kategória, altéma) pároshoz ír
szöveget — a címke input, nem output. Utána: dedup + teszt-átfedés-ellenőrző
(FR-003), és a kézi review (T023) dönt a bekerülésről.
"""
import asyncio
import json
import random
import re
import time
from pathlib import Path

from triage.label import DEFAULT_MODEL, Throttle, _patch_kimi_code_base_url

# plan.md D1: altémák a diagnosztizált határvonalak mentén — ANGOLUL
# (a v1-es magyar altémák magyar ticketeket generáltak: 319/460 sor; v1
# dokumentált hibaként megmarad, v2 angol instrukciókkal készül)
SUBTOPICS = {
    "Security": [
        "impossible travel / suspicious sign-in alert",
        "phishing email report",
        "BitLocker recovery key prompt",
        "antivirus/EDR detection alert",
        "unauthorized USB device detected",
        "suspected MFA fatigue attack (borderline: not a plain MFA outage)",
        "suspected credential theft / credential stuffing signs",
    ],
    "Printers & Devices": [
        "printer offline / stuck print queue",
        "paper jam / printer hardware fault",
        "label printer / barcode printer failure",
        "scanner failure / firmware issue",
        "docking station peripheral fault that is NOT the laptop's fault (borderline)",
        "headset / external device connectivity issue",
    ],
    "Laptop / Endpoint": [
        "built-in webcam / microphone failure on the device",
        "laptop slowdown / storage / memory issues",
        "screen / display fault on the laptop",
        "battery / charging / overheating",
        "VPN client on the endpoint itself (borderline: not network infra)",
        "docking issue affecting the endpoint (borderline)",
    ],
}

DEPARTMENTS = ["Finance", "HR", "Sales", "Operations", "Warehouse", "Legal",
               "Marketing", "Support", "Engineering", "Logistics"]

_GENERATE_SYSTEM = (
    "You write realistic IT support tickets for a 500-person company, "
    "in ENGLISH ONLY. Each ticket is one or two sentences: what broke, where, "
    "and the impact. Vary the phrasing; do not reuse stock sentences. "
    'Answer with a JSON array of objects, each {"text": "..."}, no commentary.'
)

_HUN_MARKS = re.compile(r"[áéíóöőúüű]", re.I)


def is_english(text: str) -> bool:
    """Nyelvszűrő: magyar ékezetes sor nem mehet a tanítóhalmazba (v1-tanulság)."""
    return not _HUN_MARKS.search(text)


def normalize_text(text: str) -> str:
    """Kisbetű, írásjel- és whitespace-normalizálás; a „Reported by X"
    végződés levágva (ugyanaz a hiba más bejelentőtől = ugyanaz a szöveg)."""
    t = re.sub(r"(?i)\s*reported by .*$", "", text)
    t = t.lower()
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def dedupe_rows(rows: list[dict]) -> list[dict]:
    """Pontos és normalizált szöveg-duplikáció szűrése; az első példány marad."""
    seen, kept = set(), []
    for r in rows:
        key = normalize_text(r["text"])
        if key not in seen:
            seen.add(key)
            kept.append(r)
    return kept


def assert_no_test_overlap(rows: list[dict], handchecked_jsonl) -> None:
    """FR-003: a futás megáll, ha egy gyártott szöveg a fagyott tesztben van."""
    from triage.data import load_jsonl

    test_texts = {normalize_text(r["text"]) for r in load_jsonl(handchecked_jsonl)}
    hits = [r["id"] for r in rows if normalize_text(r["text"]) in test_texts]
    assert not hits, f"gyártott/teszt szöveg-átfedés: {hits[:5]}"


def parse_generated(raw: str, category: str, batch_id: int) -> list[dict]:
    """JSON-tömb kinyerése a válaszból; a címke a konstruált kategória (FR-002).

    A hibás sorok (nincs text mező) kimaradnak — sosem találgatunk.
    """
    m = re.search(r"\[.*\]", raw or "", re.DOTALL)
    if not m:
        return []
    try:
        items = json.loads(m.group(0))
    except json.JSONDecodeError:
        return []
    rows = []
    for i, item in enumerate(items):
        if isinstance(item, dict) and isinstance(item.get("text"), str) and item["text"].strip():
            rows.append({"id": f"gen-v1-{category[:4]}-{batch_id}-{i}",
                         "text": item["text"].strip(), "label": category})
    return rows


async def generate_all(out_path, handchecked_jsonl, per_subtopic=5, n_per_call=5,
                       model=DEFAULT_MODEL, start=4, seed=0) -> dict:
    """Altéma × osztály mátrixon generál; dedup + átfedés-ellenőrző a végén."""
    from lm15 import (AsyncLMRouter, Config, Message, Reasoning, Request,
                      RETRYABLE_ERRORS, RouterConfig)
    from lm15.login import Auth

    _patch_kimi_code_base_url()
    rng = random.Random(seed)
    jobs = []
    bid = 0
    for category, topics in SUBTOPICS.items():
        for topic in topics:
            for _ in range(per_subtopic):
                jobs.append((category, topic, rng.choice(DEPARTMENTS), bid))
                bid += 1

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    throttle = Throttle(start)
    t0 = time.monotonic()
    rows: list[dict] = []
    failures = 0

    async with AsyncLMRouter(config=RouterConfig(auth=Auth.local())) as router:
        async def one(category, topic, dept, batch_id):
            nonlocal failures
            user = (f"Write {n_per_call} different IT support tickets from the {dept} "
                    f"department about: {topic}. They must clearly belong to the "
                    f'"{category}" support team.')
            for attempt in range(6):
                try:
                    async with throttle:
                        r = await asyncio.wait_for(
                            router.complete(Request(
                                model=model, system=_GENERATE_SYSTEM,
                                messages=(Message.user(user),),
                                config=Config(max_tokens=4000, temperature=0.9,
                                              reasoning=Reasoning(effort="off")))),
                            120)
                    throttle.success()
                    got = parse_generated(r.text, category, batch_id)
                    rows.extend(got)
                    done = len(jobs) - failures
                    if (len(rows) // 50) != ((len(rows) - len(got)) // 50):
                        print(f"  {len(rows)} sor | {time.monotonic() - t0:.0f}s",
                              flush=True)
                    return
                except (*RETRYABLE_ERRORS, asyncio.TimeoutError):
                    throttle.overloaded()
                    await asyncio.sleep(min(30, 0.5 * 2 ** attempt)
                                        * random.uniform(0.5, 1.5))
            failures += 1

        await asyncio.gather(*(one(*j) for j in jobs))

    english_only = [r for r in rows if is_english(r["text"])]
    deduped = dedupe_rows(english_only)
    assert_no_test_overlap(deduped, handchecked_jsonl)
    with open(out_path, "w", encoding="utf-8") as f:
        for r in deduped:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    stats = {
        "model": model, "jobs": len(jobs), "failed_jobs": failures,
        "generated_raw": len(rows),
        "non_english_dropped": len(rows) - len(english_only),
        "after_dedup": len(deduped),
        "dedup_dropped": len(english_only) - len(deduped),
        "seconds": round(time.monotonic() - t0, 1),
        "per_category": {c: sum(1 for r in deduped if r["label"] == c)
                         for c in SUBTOPICS},
    }
    (out_path.parent / "generate_stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    return stats
