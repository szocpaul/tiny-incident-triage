# Tasks: Strengthening the weak categories

**Input**: Design documents from `/specs/002-security-recall/`

**Prerequisites**: plan.md (approved), spec.md (approved); feature 001 is
complete (baseline-teacher metrics exist: overall 93.3% ± 1.3%; weak:
Security 79.5%, P&D 86.2%, Laptop 91.3%)

**Tests**: test-first order (playbook); measurement gates are exit-code based.

**Organization**: US1 = weak categories catch up (P1), US2 = verified
generation (P2).

## Phase 1: Generation (US2)

- [x] T020 Tests FIRST: `tests/unit/test_generate.py` — the subtopic list
  covers the 3 weak categories; dedup filters exact and normalized text; the
  test-overlap checker raises when a generated text appears in the frozen
  test; generated row schema {id, text, label} with the constructed category;
  language filter. FAILED first.
- [x] T021 [US2] `src/triage/generate.py` — subtopic × department seeds, Kimi
  Code (lm15, saved login), JSON-array answers; output
  `data/labels/generated_v2.jsonl` + `generate_stats.json`. (v1 lesson:
  Hungarian subtopics produced Hungarian tickets — v2: English subtopics +
  explicit language constraint + language filter.)
- [x] T022 [US2] Generation run; dedup + overlap checker green; review
  template: `data/labels/review_generated.csv` (stratified sample, 50 rows).
  Result: 475 rows, 0 non-English, 0 duplicates (Security 175 / P&D 150 /
  Laptop 150).
- [x] T023 **[MANUAL GATE]** The owner reviewed review_generated.csv
  (SC-005). Approved 2026-10-05 (sample accepted, 0 rows dropped).

## Phase 2: Extended training and measurement (US1)

- [x] T024 [US1] `data.py`: training set = 001 training set + approved
  generated examples (caps per plan: Security 100 / P&D 60 / Laptop 40 →
  797 → 997 rows); test unchanged (frozen); overlap checker after merge
  (id + normalized text); the T018 tests stayed green.
- [x] T025 [US1] 3-seed re-measurement: `scripts/run_boost.py` →
  `runs/002-boost/metrics.json`; report: baseline-teacher vs 002-boost,
  per category, mean ± stdev, non-overlapping-interval verdict.
  **Result: 94.00% ± 0.50; Laptop/Endpoint 91.3% → 97.1%; P&D flat (86.2%);
  Security 79.5% → 78.2% (did NOT improve) — SC-001/002 failed.**
- [x] T026 **[MANUAL GATE]** SC validation by the owner. Verdict: the feature
  failed its gates; the diagnosis (convention conflict, not data quantity)
  led to feature 003.

---

## Dependencies & Execution Order

- T020 → T021 → T022 → T023 (MANUAL GATE) → T024 → T025 → T026 (MANUAL GATE)
- T020's tests fail first, T021 turns them green.
- T024 works only with approved (T023) examples.

## Validation Checklist

- [x] Every FR covered: FR-001/002→T021/T022, FR-003→T020/T024,
  FR-004→T025, FR-005→T025, FR-006→T025/T026
- [x] Every SC runnable as a gate (T026)
- [x] MANUAL GATEs marked: T023, T026
- [x] Outbound data traffic only in T021, with the approved account
- [x] The baseline-teacher metrics preserved unchanged (comparison)

## Outcome note (documented)

The 002 measurement proved that data quantity was not Security's problem —
the convention conflict was. This finding opened feature
`003-borderline-conventions`.
