# Tasks: Ticket triage classifier

**Input**: Design documents from `/specs/001-ticket-triage/`

**Prerequisites**: plan.md (approved), spec.md (approved), constitution.md
(approved)

**Tests**: spec FR-002 and FR-004 require exit-code gates, so test tasks are
MANDATORY, in test-first order (playbook).

**Organization**: US1 = teacher labels + hand-checked test set (P1),
US2 = local classification (P2), US3 = minute-scale retrainability (P3).

**Status note**: T001–T010 were completed in the first iteration; the T010
baseline (12.0% ± 0.0) proved the sample's labels are noise — a documented
negative result in the spec Background. From T014 the teacher-labeling path
follows. (Story tags [US1]/[US2] in the old phases reflect the original
numbering: local classification / retrainability.)

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup (Shared Infrastructure)

- [x] T001 Project structure per plan.md (`src/triage/`, `tests/`,
  `data/tidy/`, `runs/`), project venv, pinned `requirements.txt`
  (torch CPU wheel, transformers, polars, dpyr, pytest — exact versions,
  Constitution III)
- [x] T002 [P] `.gitignore` (runs model dirs, data, venv) and
  `src/triage/__init__.py` skeleton

---

## Phase 2: Foundational (Blocking Prerequisites)

- [x] T003 Tests FIRST: `tests/unit/test_data.py` — tidy schema columns
  (task, split, id, text, label), stratified split ratio, 0 overlap between
  train/test, invalid label dropped. Tests had to FAIL before implementation
  (FR-001, FR-002)
- [x] T004 `src/triage/data.py` — tidy (dpyr: join with the category table,
  text = summary + description) + stratified split (seed=0, recorded) +
  overlap checker that stops the run on error. T003 turned green.

**Checkpoint**: Foundation ready — tidy Parquet and split exist, verified.

---

## Phase 3: Local classification (original US1, Priority: P1) 🎯 MVP

### Tests (written first, FAILED before implementation) ⚠️

- [x] T005 [P] `tests/unit/test_evaluate.py` — metrics.json format (overall +
  per-category accuracy), non-zero exit code below threshold;
  `tests/integration/test_smoke.py` — end-to-end tidy→train(1 epoch)→eval on
  a 40-row slice

### Implementation

- [x] T006 `src/triage/train.py` — Ettin-17M full fine-tune on CPU, **exactly
  the repo's recipe** (reference: `recipe/train.py`): AdamW lr=1e-4, wd=0.01,
  batch=32, 5% warmup + cosine decay, gradient clipping 1.0, cross-entropy,
  maxlen=128, and **fixed step count via the epoch formula**:
  `epochs = max(6, round(6 * 9493 / train_rows))`. Every parameter into the
  run's `config.json` (FR-003, FR-007)
- [x] T007 `src/triage/evaluate.py` — overall + per-category accuracy →
  `runs/<run>/metrics.json`, `--min-accuracy` exit-code gate (FR-004)
- [x] T008 [P] `src/triage/predict.py` — single classification + timing
  (SC-004), empty/short text signal (spec Edge Cases)
- [x] T009 `src/triage/__main__.py` — CLI: `tidy | train | eval | predict`
  subcommands from one entry
- [x] T010 **Baseline run**: tidy→train→eval **with 3 seeds (0, 1, 2)**;
  metrics.json contains mean and stdev (the repo's "means of 3 runs" method;
  Constitution I noise measurement). Result: `runs/baseline-*/metrics.json`
  (FR-005, D4). **Result: 12.0% ± 0.0 — chance level; the sample's labels
  are noise.** Kept as documented negative evidence.

**Checkpoint**: the pipeline works end to end; the baseline file exists and
drove the spec amendment (teacher labeling).

---

## Phase 4: Minute-scale retrainability (original US2, Priority: P2)

- [x] T011 Reproducibility endpoint: `python -m triage run --name <name>`
  executes the tidy→split→train→eval chain, writes config and measured times
  into the run folder; baseline and new run metrics.json side by side in the
  report (FR-007, SC-003)

**Checkpoint**: both original stories work independently.

---

## Phase 5: Polish & Cross-Cutting Concerns

- [x] T012 **[MANUAL GATE]** Full SC validation by the owner: `pytest -q` +
  eval gate + predict timing, baseline metrics.json reviewed. An agent may
  NOT check this off. (Approved by the owner, 2026-10-05.)
- [x] T013 [P] `README.md` — quickstart in the repo

---

## Phase 6: Teacher labeling and new baseline (US1, after the measurement)

**Goal**: trustworthy labels for the 1,000 rows from an LLM teacher;
hand-checked frozen test set; new baseline on content-true labels

**Independent Test**: `python -m triage label` runs, SC-005 (≥99% valid); the
hand-checked test set is a versioned file; the new baseline mean accuracy is
significantly above the 12% noise baseline (non-overlapping interval)

- [x] T014 **[MANUAL GATE]** Owner signs in to Kimi Code via lm15 saved
  sign-in (`scripts/login_kimi.py`). Done 2026-10-05 (device flow,
  `--kimi-ai` host).
- [x] T015 Tests FIRST: `tests/unit/test_label.py` — the prompt contains the
  instruction and the 8 labels; answer matching accepts only an exact label
  (else None); the jsonl is resumable. FAILED first. Then
  `src/triage/label.py`: lm15 async labeling, low start throttle (start=4),
  60 s timeout, exponential-backoff retries, `data/labels/teacher.jsonl` +
  `label_stats.json` (FR-008). Note: required a base_url fix
  (`/coding` → `/coding/v1`) and max_tokens=512 (the endpoint's thinking
  otherwise consumed the whole budget).
- [x] T016 Labeling run on all 1,000 rows with the saved sign-in; SC-005
  verified: **99.7% valid (997/1000), 421 s, $0** (FR-006 exception confirmed)
- [x] T017 **[MANUAL GATE]** The owner hand-reviewed ~200 teacher-labeled rows
  (stratified sample: 25/category), corrected 7 borderline rulings; result:
  `data/labels/handchecked_test.jsonl` (frozen, versioned). Approved.
- [x] T018 `data.py` rework: tidy now uses teacher labels; test set = the
  hand-checked file; train = teacher labels minus hand-checked ids; 0 overlap
  both ways (FR-002, FR-009). T003 tests updated to the new contract (the
  noisy category-join path deleted). Real split: 797 train / 200 test.
- [x] T019 **New baseline**: 3 seeds (0, 1, 2) on teacher labels, eval on the
  hand-checked test; `runs/baseline-teacher/metrics.json` (mean ± stdev).
  **Result: 93.33% ± 1.26** — non-overlapping with the 12% noise baseline.

**Checkpoint**: a content-true, measured baseline exists; the SC-001 gate
from now on runs on the hand-checked test set.

---

## Dependencies & Execution Order

- **Phase 1 → 2 → 3 → 4 → 5** strictly in order; test tasks (T003, T005)
  BEFORE their implementation (T004, T006–T009), failing first.
- **Phase 6** (the new P1 story): T014 (MANUAL GATE) → T015 (test first) →
  T016 → T017 (MANUAL GATE) → T018 → T019 → back to T012.
- T001 → T002 [P] → T003 → T004 → T005 [P] → T006 → T007 → T008 [P] → T009 →
  T010 → T011 → [Phase 6] → T012 (MANUAL GATE) → T013 [P].

## Validation Checklist

- [x] Every FR (FR-001…FR-009) has at least one task
- [x] Every SC (SC-001…SC-005) runnable as a gate
- [x] MANUAL GATE tasks explicitly marked (T012, T014, T017)
- [x] The noise baseline (T010, 12%) and the teacher baseline (T019) both
  preserved in files
- [x] Outbound data traffic only in T016, with the owner's approval (FR-006
  exception)
