# Tasks: Cleaning the frozen test set

**Input**: Design documents from `/specs/004-testset-cleanup/`

**Prerequisites**: plan.md, spec.md (approved); the final model exists
(`runs/003-relabel-v4-s1`); the frozen test: `data/labels/handchecked_test.jsonl`.

## Phase 1: Conflict map (US1)

- [x] T034 Tests FIRST: `tests/unit/test_testset.py` — the conflict finder
  catches normalized duplicate conflicts on toy data; the decision applier
  only freezes with a fully filled table; the changelog schema. FAILED first.
- [x] T035 [US1] `src/triage/testset.py` + CLI: `python -m triage
  testconflicts` → report (duplicated texts, copy counts, label distribution)
  + `data/labels/testset_decisions.csv` template. **Result: 2 conflict groups
  (spam burst 5×: E&C/Security; shared drive 4×: Laptop/Network).**

## Phase 2: Decision and freezing (US2)

- [x] T036 **[MANUAL GATE]** The owner filled testset_decisions.csv.
  Decisions 2026-10-05: spam burst → Security ("spam mails are security
  responsibility"); shared drive → Laptop / Endpoint ("the laptop word in the
  context").
- [x] T037 [US2] Freeze: v1 archived (`handchecked_test_v1.jsonl`,
  untouched), v2 frozen (`handchecked_test_v2.jsonl`, 193 rows), changelog
  (`testset_v2_changelog.json`), `data/tidy/test.parquet` regenerated from
  v2, 0-overlap checker against the training set (id + text) — green.

## Phase 3: Re-evaluation (US3)

- [x] T038 [US3] The final model re-evaluated without retraining on v1 and
  v2 → `runs/004-testset-v2/metrics_v1.json` / `metrics_v2.json`.
  **Result: v1 98.50% (n=200) → v2 99.48% (n=193); every category 100% on v2
  except Security 95.7% (one genuine borderline row).**
- [x] T039 **[MANUAL GATE]** SC validation by the owner: `pytest -q` (29
  green) + `python -m triage testconflicts --test
  data/labels/handchecked_test_v2.jsonl --exit-code` (0 = clean) + v1/v2
  report review. Approved 2026-10-05.

---

## Dependencies & Execution Order

- T034 → T035 → T036 (MANUAL GATE) → T037 → T038 → T039 (MANUAL GATE)
- T037 may only run with a fully filled decision table.

## Validation Checklist

- [x] FR-001→T035, FR-002→T036, FR-003→T037, FR-004→T038, FR-005→(no training)
- [x] SC-001 exit-code gate (T035/T039), SC-002/SC-003 in the report (T038/T039)
- [x] MANUAL GATEs: T036, T039
- [x] No outbound data traffic; no retraining; v1 physically preserved
