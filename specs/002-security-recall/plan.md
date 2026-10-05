# Implementation Plan: Strengthening the weak categories

**Branch**: `002-security-recall` | **Date**: 2026-10-05 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-security-recall/spec.md`

## Summary

For the weak categories (Security, Printers & Devices, Laptop / Endpoint) we
generate targeted, subtopic-seeded synthetic tickets with the teacher (~200
new rows), the owner hand-reviews a sample (MANUAL GATE), we retrain on the
extended training set with the **unchanged recipe** (3 seeds), and measure on
the frozen hand-checked test set — against the 001 baseline, with the
non-overlapping-interval rule.

## Technical Context

The 001 stack is unchanged (Python 3.12, CPU torch, transformers,
dpyr/polars, lm15, all pinned). New element: a generation step with the same
saved Kimi Code sign-in (the spec's FR-006 exception extends to generation).

**New module**: `src/triage/generate.py` — subtopic-seeded, seeded synthetic
ticket generation + dedup + test-overlap checker.

## Key Decisions

### D1: Generation broken down by subtopic, "by-construction label"

**Decision**: we don't ask for free text; we iterate over **(category,
subtopic) pairs**: every generated row is written for the target category in
the first place, so the label is correct by construction; only the text comes
from the teacher.

Subtopics (along the baseline diagnosis' borderlines):

- **Security** (~100 rows): impossible travel / suspicious sign-in, phishing
  report, BitLocker recovery key, antivirus/EDR alert, unauthorized USB,
  **borderline**: MFA-failure incidents from a security angle (e.g. suspected
  MFA fatigue attack).
- **Printers & Devices** (~60 rows): printer offline/jam, scanner, label
  printer, **borderline**: docking/peripheral faults that are not the laptop's.
- **Laptop / Endpoint** (~40 rows): webcam, slowdown, storage, screen,
  **borderline**: docking and built-in peripherals as the device's fault.

**Rationale**: the 001 lesson is that label noise is the biggest risk; when
the label is the input of generation (not its output), the noise source is
switched off. The hand review (SC-005) catches the remaining quality risk.

**Rejected alternative**: freely generated tickets with post-hoc teacher
labeling — a redundant round that would reintroduce label error.

### D2: Diversity systematically

**Decision**: subtopic × department × tone seed lists; each request returns N
distinct tickets as a JSON array; afterwards dedup (exact + normalized text)
and a **test-overlap checker** (FR-003).

Note from implementation: v1 used Hungarian subtopic descriptions and the
model answered in Hungarian for 319/460 rows — a documented data error. v2
uses English subtopics, an explicit "ENGLISH ONLY" constraint, and a language
filter (unit-tested).

**Rationale**: 200 template copies are worthless; text-level overlap with the
hand-checked test would falsify the measurement.

**Rejected alternative**: a single "write 100 security tickets" prompt —
yields a cliché pile.

### D3: The recipe is sacred (FR-004)

**Decision**: model, hyperparameters, epoch formula, seeds (0/1/2) all
unchanged; only the training set grows. The new runs go to
`runs/002-boost-s{0,1,2}`, and the report compares against `baseline-teacher`.

**Rationale**: only then is the improvement attributable to a single cause
(the data).

**Rejected alternative**: epoch/hyperparameter tuning in the same round —
causes would confound; if data extension isn't enough, that's a separate,
measurable step.

### D4: The frozen test set is unchanged

**Decision**: the 200-row hand-checked test stays; new examples go only to
the training set. The test-overlap checker also checks text identity.

**Rationale**: comparability (spec Assumptions); the measurement's validity
matters more than extending the test set.

## Architecture (ASCII)

```text
subtopic list (D1) × department/tone seeds
        |
        v
[generate] Kimi Code (lm15), JSON-array answers   data/labels/generated_v2.jsonl
        |                                          + generate_stats.json
        |                                          (v1: Hungarian-language bug,
        v                                           documented and discarded)
[dedup]  exact + normalized text dedup,
         language filter, test-overlap check (FR-003)
        |
        v
[review] owner reviews ~50 rows (MANUAL GATE, SC-005)
        |
        v
[train]  001 training set + approved examples
         unchanged recipe, seeds 0/1/2             runs/002-boost-s*/
        |
        v
[eval]   frozen hand-checked test (200 rows)       runs/002-boost/metrics.json
         report: baseline-teacher vs 002-boost
         (mean ± stdev, non-overlapping interval, SC-001…SC-005 gates)
```

## Constitution Check

| Principle | Check | Result |
|-----|-----------|----------|
| I. Measurement discipline | baseline-teacher exists; 3 seeds; non-overlapping interval (SC-001/002); gate is exit-code | PASS |
| II. Data hygiene | frozen test unchanged (D4); 0 overlap by id+text (FR-003); by-construction label (D1) | PASS |
| III. Version pinning | stack and model unchanged | PASS |
| IV. Data privacy | outbound traffic = the owner's approved Kimi Code account, this time for generation (spec FR-006 exception extended) | PASS |
| V. Simplicity | recipe sacred (D3); no calibration/DSPy (spec Out of Scope) | PASS |

## Project Structure

New/changed files within the 001 structure:

```text
src/triage/
├── generate.py          # NEW: subtopic-seeded generation + dedup + overlap check
└── data.py              # extended training set assembly (generated merge)

tests/
└── unit/test_generate.py   # NEW: dedup, overlap checker, schema, language filter

data/labels/
├── generated_v1.jsonl      # documented failure (Hungarian output), kept
├── generated_v2.jsonl      # generated examples (versioned, English)
└── review_generated.csv    # hand-review template for the generated sample
```

## Complexity Tracking

No constitution violation — the table is empty.
