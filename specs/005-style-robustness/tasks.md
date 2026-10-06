# Tasks: Full HugBor adoption

**Input**: Design documents from `/specs/005-style-robustness/`

**Prerequisites**: plan.md, spec.md (approved); local endpoint
(127.0.0.1:8080, Qwen3.8-27B) available; HugBor dataset accessible.

## Phase 1: Tidy, split, label trust (US1)

- [x] T040 Remap the wild probe to the new taxonomy →
  `probes/wild_probe_v2.jsonl` (8 incidents, expected labels in the
  15-category system).
- [x] T041 Tests FIRST: `tests/unit/test_hugbor.py` — tidy schema; text =
  short_desc + desc with uniform truncation (≤ ~500 chars) and a
  truncated-row count; stratified split keeps per-category test share; 0
  overlap (id + normalized text); spot-check agreement-rate computation.
  FAIL first.
- [x] T042 [US1] `src/triage/hugbor.py` + run: download HugBor (record
  commit hash + license check), tidy, stratified split 80/20 seed=0 →
  `data/tidy/train.parquet` (new), `data/labels/hugbor_test.jsonl` (new
  frozen test), stats file.
- [x] T043 [US1] Label-trust spot-check: local Qwen blind-labels 75
  stratified rows → `runs/005-hugbor/spotcheck.json`; **SC-001 gate:
  agreement ≥90%, else STOP before training.**

## Phase 2: Top-up thin categories (US2)

- [x] T044 Tests FIRST: `tests/unit/test_stylegen.py` — local-endpoint-only
  guard; few-shot prompts sampled from HugBor rows of the same category;
  stats schema. FAIL first.
- [x] T045 [US2] `src/triage/stylegen.py` + run: local Qwen generates for
  Telephony, Software, Cloud Services, Data Center (target ≥100 train rows
  per category after merge) → `data/labels/generated_v3.jsonl` + stats.
- [x] T046 **[MANUAL GATE]** The owner reviews a stratified sample of the
  generated rows (`data/labels/review_stylegen.csv`; SC-003: ≥90% ok).
  Agent may NOT check this off.

## Phase 3: New baseline (US3)

- [x] T047 [US3] Merge: HugBor train + approved top-up →
  `data/labels/train_v5.parquet`; overlap checker against the new frozen
  test (id + normalized text).
- [x] T048 [US3] `scripts/run_hugbor.py`: 3 seeds, unchanged recipe →
  `runs/005-hugbor/metrics.json` (overall + per-category, mean ± stdev,
  SC-002: ≥90%); plus remapped probe eval (SC-004: ≥6/8 on ≥2 seeds).
- [x] T049 **[MANUAL GATE]** SC validation by the owner: `pytest -q` +
  metrics + spotcheck review (SC-001…SC-005). Agent may NOT check this off.

---

## Dependencies & Execution Order

- T040 → T041 → T042 → T043 (SC-001 gate) → T044 → T045 →
  T046 (MANUAL GATE) → T047 → T048 → T049 (MANUAL GATE)
- Test tasks (T041, T044) fail first.
- T047 works only with approved (T046) rows; T048 only if T043 passed.

## Validation Checklist

- [ ] FR-001/002→T042, FR-003→T043, FR-004→T041/T042, FR-005→T045/T046,
  FR-006→T048, FR-007→T040/T048, FR-008→T043/T045
- [ ] Every SC gate-runnable (T043, T048, T049)
- [ ] MANUAL GATEs: T046, T049
- [ ] Zero cloud LLM traffic; old data archived and unused; HugBor commit
  hash and license recorded
