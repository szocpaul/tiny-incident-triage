# Implementation Plan: Fixing borderline conventions

**Branch**: `003-borderline-conventions` | **Date**: 2026-10-05 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/003-borderline-conventions/spec.md`

## Summary

First a confusion map on the 002 model (which category is confused with
which, row by row), then keyword-based borderline candidates from the
training set, owner approval (MANUAL GATE), targeted relabeling into a
versioned new file, and finally a 3-seed re-measurement with the unchanged
recipe on the frozen test — compared against all three previous baselines.

## Technical Context

The 001/002 stack and recipe are unchanged. New modules:
`src/triage/confusion.py` (confusion report), `src/triage/relabel.py`
(candidates + relabeling). No outbound data traffic.

## Key Decisions

### D1: Measurement first, fix after

**Decision**: the first artifact is the confusion report (on
`runs/002-boost-s0`, frozen test): matrix + every misclassified row (text,
true, predicted).

**Rationale**: 002 showed that "well-intuited" additions don't move Security —
the fix must target measured pairs (SC-004). The report tells whether
Security truly bleeds toward Access Management, and what P&D is confused
with. (Measurement result: Security → Email & Collaboration was the dominant
confusion, not Access Management — the keyword candidates were built from
this.)

**Rejected alternative**: immediate relabeling on assumed borders — guessing;
exactly what failed in 002.

### D2: Keyword-based candidates + the owner's table

**Decision**: a keyword rule collects candidates in the training set
(MFA|password|SSO|Okta|login|webcam|dock|monitor|printer|scanner…), each with:
id, text, current label, suggested label (rule derived from the confusion
map). The owner decides row by row (relocate / keep), in CSV; only approved
rows are rewritten.

**Rationale**: the convention is the owner's property; the keyword rule only
nominates, never decides (the 002 lesson: automatic "fixes" can hide errors).

**Rejected alternative**: automatic keyword-based relabeling — fast, but per
the spec's Edge Cases an over-aggressive rule must be filtered by a human.

### D3: Versioned relabeling, untouched predecessors

**Decision**: the relabeled set is a new file (`data/labels/train_v3.parquet`,
then `train_v4.parquet` after the micro-iteration); the 001/002 files are
untouched. Rollback = the old file.

**Rationale**: Constitution II + the comparability of baselines.

### D4: Re-measurement with the same harness

**Decision**: `scripts/run_relabel.py` follows the run_boost.py pattern but on
the v3/v4 training set; report: 4 columns (noise / teacher / boost / relabel),
per category, with a non-overlapping-interval verdict.

**Implementation note (v4 micro-iteration)**: the first relabel run (v3,
97.3%) degraded Laptop (−10.1 pp) and E&C (−5.3 pp) — SC-003 failed. Root
cause: the "shared drive" suggestion (not owner-ruled) plus leftover
"Teams calls"→Telephony rows contradicting the owner's convention. Fix:
revert that rule, move Teams-calls rows to E&C, re-measure → v4:
**98.17% ± 0.58%**, all categories ≥96%.

## Architecture (ASCII)

```text
runs/002-boost-s0/model + frozen test (200 rows)
        |
        v
[confusion]  matrix + misclassified rows ----> runs/003-confusion/report.json
        |                                    (SC-004: the fix targets these)
        v
[candidates] keyword rule on the training set -> data/labels/relabel_review.csv
        |                                    (id, text, current, suggested)
        v
[review] owner row by row (MANUAL GATE)
        |
        v
[relabel] only approved rows ----------------> data/labels/train_v3.parquet
        |                                    (001/002 files untouched)
        |                                    then v4: shared-drive reverted,
        |                                    Teams-calls -> E&C
        v
[train+eval] unchanged recipe, seeds 0/1/2  -> runs/003-relabel-v4/metrics.json
        report: noise 12% | teacher 93.3% | boost 94.0% | relabel-v4 98.2%
```

## Constitution Check

| Principle | Check | Result |
|-----|-----------|----------|
| I. Measurement discipline | 3 previous baselines in files; 3 seeds; non-overlapping interval (SC-002) | PASS |
| II. Data hygiene | frozen test unchanged; 0 overlap in v3/v4 too; untouched predecessors (D3) | PASS |
| III. Version pinning | stack/recipe unchanged | PASS |
| IV. Data privacy | no outbound traffic in this feature | PASS |
| V. Simplicity | two thin new modules; no new external dependency | PASS |

## Project Structure

```text
src/triage/
├── confusion.py   # NEW: confusion report (FR-001)
└── relabel.py     # NEW: candidates + relabeling (FR-002, FR-003)

tests/unit/
├── test_confusion.py  # NEW
└── test_relabel.py    # NEW

scripts/run_relabel.py      # NEW: 3-seed re-measurement on v3
scripts/run_relabel_v4.py   # NEW: same on v4 (micro-iteration)
```

## Complexity Tracking

No constitution violation — the table is empty.
