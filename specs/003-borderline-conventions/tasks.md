# Tasks: Fixing borderline conventions

**Input**: Design documents from `/specs/003-borderline-conventions/`

**Prerequisites**: plan.md, spec.md (approved); the 002 model and baselines
exist (`runs/baseline`, `runs/baseline-teacher`, `runs/002-boost`).

**Organization**: US1 = confusion map (P1), US2 = relabeling (P1),
US3 = re-measurement (P1).

## Phase 1: Confusion map (US1)

- [x] T027 Tests FIRST: `tests/unit/test_confusion.py` — report schema
  (matrix, misclassified row list: id, text, true, predicted), correct
  counting on toy data. FAILED first.
- [x] T028 [US1] `src/triage/confusion.py` + CLI (`python -m triage confusion
  --run runs/002-boost-s0`); report → `runs/003-confusion/report.json`.
  **Result: 12 misclassifications, 6 patterns — dominant: Security → Email &
  Collaboration (spam burst), P&D → E&C / Laptop (camera/webcam/docking).**

## Phase 2: Borderline relabeling (US2)

- [x] T029 Tests FIRST: `tests/unit/test_relabel.py` — the keyword rule hits
  the expected rows; relabeling works only on approved rows; the v3 file has
  0 overlap with the test (id + text); unknown target label rejected.
  FAILED first.
- [x] T030 [US2] `src/triage/relabel.py` — candidate list with the rule
  derived from the confusion map → `data/labels/relabel_review.csv`;
  the relabeler from the approved CSV → `data/labels/train_v3.parquet`
  (001/002 untouched). 105 candidates in 7 convention pairs.
- [x] T031 **[MANUAL GATE]** The owner decided on relabel_review.csv row by
  row. Approved 2026-10-05 (all 7 suggestion lines accepted).

## Phase 3: Re-measurement (US3)

- [x] T032 [US3] `scripts/run_relabel.py`: 3 seeds, unchanged recipe, frozen
  test → `runs/003-relabel/metrics.json`, 4-column comparison
  (noise/teacher/boost/relabel), non-overlapping-interval verdict.
  **v3 result: 97.33% ± 0.29 — SC-001/002 passed, SC-003 FAILED (Laptop
  −10.1 pp, E&C −5.3 pp).** Micro-iteration (v4): shared-drive rule reverted,
  Teams-calls Telephony→E&C relabeled; **v4 result: 98.17% ± 0.58%, every
  category ≥96%.**
- [x] T033 **[MANUAL GATE]** SC validation by the owner: `pytest -q` + report
  review. **Approved 2026-10-05** (the E&C −2.7 pp accepted as frozen-test
  contradiction, not a real regression — documented; this opened feature 004).

---

## Dependencies & Execution Order

- T027 → T028 → T029 → T030 → T031 (MANUAL GATE) → T032 → T033 (MANUAL GATE)
- The confusion map (T028) is the input of the candidate rule (T030).
- T032 runs only after the approved (T031) relabeling.

## Validation Checklist

- [x] FR-001→T028, FR-002→T030, FR-003→T030/T031, FR-004→T032, FR-005→T032
- [x] Every SC runnable as a gate (T033)
- [x] MANUAL GATEs marked: T031, T033
- [x] No outbound data traffic in any task
- [x] Previous baseline files and training sets untouched
