# Implementation Plan: Ticket triage classifier

**Branch**: `001-ticket-triage` | **Date**: 2026-10-05 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-ticket-triage/spec.md`

## Summary

From the 1,000-row synthetic ticket sample a unified tidy table is built;
labels come from an LLM teacher (the owner's approved Kimi Code account via
lm15 saved sign-in, low-concurrency adaptive throttle). A small encoder model
is fully fine-tuned on CPU locally; evaluation is an exit-code gate command
writing overall and per-category accuracy. The first run is the baseline,
written to a file; every later change is measured against it.

## Technical Context

**Language/Version**: Python 3.12 (project venv on the machine)

**Primary Dependencies** (all pinned, Constitution III):

- `torch` (CPU wheel, exact version in `requirements.txt`)
- `transformers` (exact version)
- `polars` (the dpyr engine; exact version)
- `dpyr` (the tutorial's data verbs: `read`, `col`, `mutate`, `left_join`, …; exact version)
- `lm15` (teacher labeling, with saved Kimi Code sign-in; exact version)
- `pytest` (test and gate runner)

**Student model**: `jhu-clsp/ettin-encoder-17m` (pinned HF revision)

**Storage**: filesystem — `data/` (Parquet/JSONL), `runs/<name>-<timestamp>/`
(config.json, metrics.json, model checkpoint)

**Testing**: `pytest -q` (unit + integration), plus the eval command as a
threshold gate: `python -m triage eval --min-accuracy 0.85`

**Target Platform**: Windows 11, the owner's PC (Ryzen 5 7600X, 32 GB RAM);
CPU-only PyTorch. No CUDA, and none needed.

**Project Type**: CLI package (`python -m triage ...`)

**Performance Goals** (bound to the spec's SCs):

- training + evaluation ≤ 15 min on CPU (SC-003)
- inference ≤ 100 ms/item per single call (SC-004)
- overall accuracy ≥ 85%, per-category ≥ 75% (SC-001, SC-002)

**Constraints**: ticket text does not leave the machine (Constitution IV, with
the FR-006 exception); train/test 0 overlap (Constitution II); every version
pinned (Constitution III).

**Scale/Scope**: 1,000 tickets, 8 categories, 17M-parameter model —
deliberately small scale; larger datasets are restart-condition-bound (spec
Out of Scope).

## Key Decisions

### D1: LLM teacher labeling (flipped by the baseline measurement)

**Decision**: the 1,000 ticket texts are labeled by an LLM teacher through the
owner's own, approved Kimi Code account (lm15 saved sign-in, low-concurrency
adaptive throttle). The student trains on teacher labels; the evaluation
reference is the owner's hand-checked ~200-row frozen test set.

**Rationale**: the original D1 rejected the teacher because "the sample
already has reference labels" — the baseline measurement (12.0% ± 0.0, chance
level) proved that assumption false: the sample's labels are noise. Teacher
labeling is therefore not an extra round but the only path to trustworthy
labels.

**Rejected alternative**: training on the noisy labels — measured to yield
chance-level results.

**Rejected alternative**: fully new LLM-generated text+label pairs — we would
lose the sample's realistic texts; kept as a fallback.

**Student remains**: Ettin-17M encoder, all weights trained, on CPU (the
recipe is unchanged).

### D2: dpyr for data tables (aligning with the tutorial)

**Decision**: the tidy step is written with dpyr — the same verbs (`read`,
`col`, `mutate`, `left_join`, `select`) that the tiny-classifiers tutorial
uses.

**Rationale**: the owner wants to align with the tutorial code. Although our
v1 cleanup would be 6–8 lines in plain polars, choosing dpyr enables direct
reuse of the tutorial's later teacher-labeling round (`label_all`,
`accuracy`, comparison report) — those functions all work on dpyr tables.
The extra dependency's cost (pinning, Constitution III) is consciously
accepted.

**Rejected alternative**: plain polars — fewer dependencies, but every table
operation would need rewriting when adopting the tutorial code.

### D3: Stratified split, seed=0, recorded in config

**Decision**: per-category proportional allocation, `seed=0`, and the overlap
checker proves 0 overlap at the start of every run (test-first quota: exactly
25 test rows per category; the remainder goes to train, max 100/category —
771 train / 200 test on the v1 labeled data).

**Rationale**: with 8 balanced categories, stratification guarantees
per-category test coverage; the fixed seed gives reproducibility
(Constitution II).

**Rejected alternative**: plain random split — on a small sample it can skew
the rarer categories' test coverage.

### D4: Baseline-first run model

**Decision**: the first successful training+evaluation result is written to
`runs/baseline-*/metrics.json`; any later change to the recipe is a new run,
and the report compares against the baseline.

**Rationale**: Constitution I (measurement discipline) — improvement is only
accepted on non-overlapping intervals; that needs a physical baseline file.
(The first, noisy-label baseline — 12.0% — is kept as documented negative
evidence.)

**Rejected alternative**: "we'll look at it at the end" — per the playbook,
this is the most easily botched part; hence a gate.

## Architecture (ASCII)

```text
data/raw/tickets.csv + categories.csv
        |
        v
[tidy]  dpyr: text = summary + description ---> data/tidy/texts.parquet
        |                                      (task, id, text — NO label:
        v                                       the sample's labels are noise)
[label] LLM teacher (Kimi Code, lm15 login)
        low throttle, resumable, cost/time log
        |                                      data/labels/teacher.jsonl
        v
[review] owner hand-reviews ~200 rows        data/labels/handchecked_test.jsonl
        |                                    (MANUAL GATE, frozen, versioned)
        v
[split] stratified, seed=0, 0 overlap with the hand-checked set too (FR-009)
        |
        v
[train] ettin-encoder-17m, full FT, CPU
        AdamW lr=1e-4, batch=32, cosine, maxlen=128
        |
        v
runs/<run>/  config.json + model/ + metrics.json
        |
        +--> [eval]  python -m triage eval --min-accuracy 0.85
        |            exit 0/1; overall + per-category accuracy -> metrics.json
        |            (reference: the hand-checked test set)
        |
        +--> [predict] python -m triage predict "ticket text"
                       <= 100 ms/item, CPU
```

## Constitution Check

| Principle | Check | Result |
|-----|-----------|----------|
| I. Measurement discipline | baseline file exists (the noisy-label run is its documented negative result); new baseline on teacher labels; gate is exit-code (SC-001) | PASS |
| II. Data hygiene | split seed=0 recorded (D3); 0-overlap checker at run start, on the hand-checked set too (FR-009); invalid label dropped + logged | PASS |
| III. Version pinning | torch/transformers/dpyr/polars/lm15 exact versions, model pinned revision | PASS |
| IV. Data privacy | outbound traffic only the owner-approved one-off labeling (FR-006 exception, 1,000 rows, own Kimi Code account) | PASS |
| V. Simplicity | no GPU path; dpyr justified by tutorial alignment (D2); the teacher round is required by the measurement finding (D1) | PASS |

No Complexity Tracking needed (no principle violated).

## Project Structure

### Documentation (this feature)

```text
specs/001-ticket-triage/
├── plan.md              # this file
├── spec.md              # approved spec
└── tasks.md             # task breakdown
```

### Source Code (repository root)

```text
src/triage/
├── __init__.py
├── __main__.py          # CLI entry: tidy / label / train / eval / predict / run
├── data.py              # tidy + stratified split + overlap checker
├── label.py             # teacher labeling (lm15, adaptive throttle)
├── train.py             # fine-tuning (from config)
├── evaluate.py          # overall + per-category accuracy, exit-code gate
└── predict.py           # single classification + timing

tests/
├── unit/                # data.py, evaluate.py, label.py unit tests
└── integration/         # end-to-end smoke on a small slice

data/
├── raw/                 # downloaded CSVs
├── tidy/                # generated Parquet
└── labels/              # teacher.jsonl, handchecked_test.jsonl

runs/                    # run logs + checkpoints + metrics.json (versioned)
requirements.txt         # pinned dependencies
```

**Structure Decision**: single-package CLI, because the feature is a linear
data pipeline; no web layer, service or database (YAGNI).

## Complexity Tracking

No constitution violation — the table is empty.
