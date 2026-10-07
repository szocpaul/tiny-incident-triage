# Runner Handoff — 006-borderline-pairs

**For the prime-agent runner executing this feature.**
Read `specs/constitution.md` and `specs/006-borderline-pairs/spec.md` FIRST.
You work from FILES in this repository, not from conversation context.

## Environment

- Repo: `/home/ubuntu/tiny-incident-triage` (Linux server, 4 vCPU EPYC Genoa,
  no GPU; training is CPU-only BY DESIGN — do not try to change that).
- **Bootstrap first**: if `data/tidy/test_hugbor.parquet` or
  `runs/005-uservoice-s1/model` is missing, run
  `bash scripts/server_bootstrap.sh` (~1 h incl. retraining; deterministic,
  bit-identical artifacts). Do not hand-assemble data files.
- Interpreter: `/home/ubuntu/tiny-incident-triage/.venv/bin/python`
  (Python 3.12, deps installed, `pip install -e .` done, 39/39 tests green).
- LLM endpoint for any generation: the local Qwen at the URL configured in
  `src/triage/stylegen.py` (`http://127.0.0.1:8080/v1` on the ORIGINAL
  workstation — if unreachable from this server, STOP and report; DO NOT
  reroute to any other provider).
- Frozen artifacts (DO NOT MODIFY): `data/tidy/test_hugbor.parquet`,
  `probes/wild_probe_v2.jsonl`, `data/labels/train_v6.parquet`.

## Status gate (READ FIRST)

The spec at `specs/006-borderline-pairs/spec.md` was in **Draft** status at
handoff. Implementation tasks (anything beyond T054/T055's confusion report)
MUST NOT start until the spec's Status is Approved by the owner. If still
Draft: produce the confusion report draft inputs only, then STOP and report.

## Tasks (from spec; full detail in the spec file)

1. **Confusion report** on the frozen holdout with the 005 final model
   (`runs/005-uservoice-s1/model`), focused on Cloud Services and
   Performance: reuse `src/triage/confusion.py`
   (`python -m triage confusion --run runs/005-uservoice-s1 --out runs/006-confusion`).
   If the errors are NOT concentrated in the documented pairs (Application ↔
   Cloud Services, Application ↔ Performance): per SC-004, the feature ends
   with a documented negative result — DO NOT invent a fix.
2. **Fix proposal**: every proposed change must cite a measured confusion
   pair. Write it as a file; the owner reviews it (MANUAL GATE — see TILALMAK).
3. After owner approval: apply the fix (versioned, predecessors untouched),
   retrain 3 seeds (0/1/2) with the UNCHANGED recipe, measure on the frozen
   holdout + probe, write `runs/006-borderline/metrics.json`.

## Gates (exit-code commands — pass/fail by exit code, never by judgment)

- `pytest -q` (must stay green: 39+ tests)
- Overlap check on any new training file (id + normalized text vs frozen
  holdout) — fails = STOP.
- SC gates per spec §Success Criteria (SC-001…SC-004), computed into
  `runs/006-borderline/metrics.json`.

## Limits

- Training: unchanged recipe only (Ettin-17M, batch 32, lr 1e-4, wd 0.01,
  5% warmup + cosine, clip 1.0, maxlen 128, epoch formula unchanged).
- Expected runtime on this server: ~40–55 min per seed (4 vCPU). 3 seeds
  sequentially. DO NOT parallelize training runs (CPU contention).
- Any generation: ≤ 400 rows total, local Qwen only.

## TILALMAK (PROHIBITIONS — nagybetűvel szándékosan / intentionally in caps)

- **NE PIPÁLD KI A MANUAL GATE-TASKOKAT** — those belong to the owner
  (fix-proposal review, final SC validation). You may only prepare inputs.
- **NINCS FELHŐS LLM-FORGALOM** — no calls to any external LLM API
  (Fireworks, OpenAI, Anthropic, Parasail, Moonshot, etc.). Only the
  configured local endpoint; if down: STOP and report.
- **A TANÍTÁSI RECEPT NE VÁLTOZZON** — including maxlen, batch, LR, epoch
  formula, seeds.
- **A FROZEN TESZTHALMAZT NE MÓDOSÍTSD** — and do not retrain on it.
- **A SPEC-BEN NEM SZEREPLŐ FÁJLT NE HOZZ LÉTRE** — work only within the
  paths named in this handoff and the spec.
- **NE KÖTESS ELL HAMIS METRIKÁT** — report what you measured; a failed gate
  is a reportable result, not something to work around.

## Stop-and-report conditions

Stop and report (do not improvise) if: the spec is still Draft; the local
endpoint is unreachable; a gate fails twice in a row; the confusion map is
diffuse (SC-004); memory/disk is insufficient; anything ambiguous about
conventions appears.
