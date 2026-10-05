"""T015: LLM-tanár címkézés lm15-tel — a tutorial label_all mintája alapján.

- a címkelista a system promptban van (tutorial-mérés: ez a legmegbízhatóbb);
- a válasz-illesztés szigorú: csak pontos címke érvényes, egyéb = None
  (kihagyva + naplózva, sosem találgatva — Constitution II);
- resumable: a teacher.jsonl-ben már szereplő id-k kimaradnak;
- adaptív throttle (start=4): rate limitnél felez, sikeres kör után +1;
- minden futás költség/idő-statisztikát ír (FR-008, SC-005).
"""
import asyncio
import json
import random
import time
from pathlib import Path

from triage.data import INSTRUCTION, LABELS_EXPECTED

DEFAULT_MODEL = "kimi-code:k3"  # a Kimi Code-végpont modelljei: k3, kimi-for-coding…
TIMEOUT_S = 60
MAX_ATTEMPTS = 6

# Az lm15 1.2.0 declared route-ja a /coding helyett a helyes /coding/v1-re mutatna —
# a regisztrált base_url hiányzik a /v1-gyel (élőben igazolva: /coding/messages = 404,
# /coding/v1/messages = 200). A router létrehozása előtt patcheljük.
def _patch_kimi_code_base_url():
    import dataclasses

    from lm15.login import declared

    fixed = dataclasses.replace(
        declared.KIMI_CODE,
        access=dataclasses.replace(declared.KIMI_CODE.access,
                                   base_url="https://api.kimi.com/coding/v1"),
    )
    declared.KIMI_CODE = fixed
    declared.DECLARED_PROVIDERS = tuple(
        fixed if p.id == "kimi-code" else p for p in declared.DECLARED_PROVIDERS
    )


def build_system_prompt(labels=None) -> str:
    labels = labels or LABELS_EXPECTED
    return (f"{INSTRUCTION} Answer with exactly one label from this list:\n"
            + "\n".join(labels))


def match_answer(text, labels) -> str | None:
    """Szigorú illesztés: csak pontosan egy címke érvényes (tutorial answer())."""
    if not text:
        return None
    cleaned = text.strip().strip("`*.\"' ")
    return {l.lower(): l for l in labels}.get(cleaned.lower())


def done_ids(path) -> set:
    path = Path(path)
    if not path.exists():
        return set()
    return {json.loads(line)["id"] for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()}


class Throttle:
    """TCP-szerű adaptáció (tutorial): túlterhelésnél felez, sikeres kör után +1."""

    def __init__(self, start=4):
        self.limit, self.inflight, self.ok = float(start), 0, 0
        self.cond = asyncio.Condition()
        self.lowest = float(start)

    async def __aenter__(self):
        async with self.cond:
            await self.cond.wait_for(lambda: self.inflight < int(self.limit))
            self.inflight += 1

    async def __aexit__(self, *exc):
        async with self.cond:
            self.inflight -= 1
            self.cond.notify_all()

    def success(self):
        self.ok += 1
        if self.ok >= self.limit:
            self.ok, self.limit = 0, self.limit + 1

    def overloaded(self):
        self.limit = max(1.0, self.limit / 2)
        self.lowest = min(self.lowest, self.limit)


async def label_all(rows, out_path, model=DEFAULT_MODEL, start=4) -> dict:
    """rows: [{"id", "text"}]; kimenet: teacher.jsonl + statisztika."""
    from lm15 import (AsyncLMRouter, Config, Message, Reasoning, Request,
                      RETRYABLE_ERRORS, RouterConfig)
    from lm15.login import Auth

    _patch_kimi_code_base_url()

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    already = done_ids(out_path)
    todo = [r for r in rows if r["id"] not in already]
    system = build_system_prompt()
    throttle = Throttle(start)
    t0 = time.monotonic()
    n_done, n_invalid, tokens_in, tokens_out = 0, 0, 0, 0

    async with AsyncLMRouter(config=RouterConfig(auth=Auth.local())) as router:
        async def one(row):
            nonlocal n_done, n_invalid, tokens_in, tokens_out
            for attempt in range(MAX_ATTEMPTS):
                try:
                    async with throttle:
                        r = await asyncio.wait_for(
                            router.complete(Request(
                                model=model, system=system,
                                messages=(Message.user(row["text"]),),
                                config=Config(max_tokens=512, temperature=0,
                                              reasoning=Reasoning(effort="off")))),
                            TIMEOUT_S)
                    throttle.success()
                    label = match_answer(r.text, LABELS_EXPECTED)
                    tokens_in += r.usage.input_tokens or 0
                    tokens_out += r.usage.output_tokens or 0
                    if label is None:
                        n_invalid += 1
                    with open(out_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps({"id": row["id"], "label": label},
                                           ensure_ascii=False) + "\n")
                    n_done += 1
                    if n_done % 50 == 0:
                        print(f"  {n_done}/{len(todo)} kész | "
                              f"{n_done / (time.monotonic() - t0):.1f}/s | "
                              f"{int(throttle.limit)} in flight", flush=True)
                    return
                except (*RETRYABLE_ERRORS, asyncio.TimeoutError):
                    throttle.overloaded()
                    await asyncio.sleep(min(30, 0.5 * 2 ** attempt)
                                        * random.uniform(0.5, 1.5))
            n_invalid += 1  # minden próba elfogyott: kihagyva, naplózva
            with open(out_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"id": row["id"], "label": None},
                                   ensure_ascii=False) + "\n")

        await asyncio.gather(*(one(r) for r in todo))

    seconds = time.monotonic() - t0
    stats = {
        "model": model, "requested": len(rows), "newly_labeled": n_done,
        "skipped_already_done": len(already), "invalid": n_invalid,
        "valid_rate": (n_done - n_invalid) / n_done if n_done else None,
        "seconds": round(seconds, 1), "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "throttle_ended_at": int(throttle.limit), "throttle_lowest": int(throttle.lowest),
    }
    (out_path.parent / "label_stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    return stats
