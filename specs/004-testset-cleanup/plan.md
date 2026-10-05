# Implementation Plan: Cleaning the frozen test set

**Branch**: `004-testset-cleanup` | **Date**: 2026-10-05 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/004-testset-cleanup/spec.md`

## Summary

Conflict report on the frozen test set's duplicates → the owner's row-level
decisions (MANUAL GATE) → archived v1 + new frozen v2 → re-evaluation of the
final model on both, without retraining, with a side-by-side report.

## Technical Context

The stack is unchanged. New module: `src/triage/testset.py` (conflict
detection, decision application, versioning). Normalization reuses
`generate.normalize_text`. CLI: `python -m triage testconflicts [--exit-code]`.

## Key Decisions

### D1: Normalized text identity as the conflict definition

**Decision**: duplicate groups are formed per `normalize_text` (lowercase,
punctuation- and whitespace-independent, and the "Reported by X" tail
stripped); a conflict = more than one distinct label within a group.

**Rationale**: this is exactly how the 003 confusion reports surfaced them
(same text, different labels); the same normalization is already tested.
(Implementation note: the reporter tail had to be stripped — identical
tickets from different reporters otherwise looked like different texts.)

**Rejected alternative**: exact text equality — whitespace/punctuation
differences would slip through.

### D2: Replacement with archiving, never overwriting

**Decision**: `handchecked_test.jsonl` → renamed to `handchecked_test_v1.jsonl`
(content untouched), the new one is `handchecked_test_v2.jsonl`;
`data/tidy/test.parquet` regenerated from v2; the changelog is
`data/labels/testset_v2_changelog.json`.

**Rationale**: SC-003 — v1 is physically restorable, the audit trail complete.

### D3: Re-evaluation without retraining

**Decision**: the final model (`runs/003-relabel-v4-s1`, the best seed) is
unchanged; eval runs twice: on v1 and on v2; the report puts them side by
side with the n difference.

**Rationale**: the test set is independent of training; retraining would add
nothing but noise (Constitution V). Rule of thumb: test changes → re-measure;
training data changes → retrain + re-measure.

## Architecture (ASCII)

```text
data/labels/handchecked_test.jsonl (v1)
        |
        v
[testconflicts] groups per normalize_text, >1 label
        |                                  runs/004-conflicts/report.json
        |                                  (2 groups: spam burst 5x,
        v                                    shared drive 4x)
[decision] owner row by row (MANUAL GATE)
        |                                  data/labels/testset_decisions.csv
        |                                  (spam → Security; shared drive →
        v                                    Laptop / Endpoint)
[freeze] v1 archived + v2 frozen + changelog + 0-overlap check
        |                                  (200 → 193 rows)
        v
[eval] 003-relabel-v4-s1 model, on v1 AND v2 (no retraining)
        |                                  runs/004-testset-v2/
        v
        report: v1 98.50% (n=200) vs v2 99.48% (n=193), with the n difference
```

## Constitution Check

| Principle | Check | Result |
|-----|-----------|----------|
| I. Measurement discipline | v1 archived + v1/v2 side-by-side report; gate is exit-code (SC-001) | PASS |
| II. Data hygiene | 0 overlap with train in v2 too; test replacement only logged and archived | PASS |
| III. Version pinning | stack unchanged; test set versioned (v1/v2) | PASS |
| IV. Data privacy | no outbound traffic | PASS |
| V. Simplicity | one thin module, no new dependency, no retraining | PASS |

## Project Structure

```text
src/triage/testset.py          # NEW: conflicts, decision application, versioning
tests/unit/test_testset.py     # NEW
scripts/freeze_testset_v2.py   # (logic in testset.py; freeze run from CLI/script)
runs/004-testset-v2/           # NEW: v1/v2 eval report
```

## Complexity Tracking

No constitution violation — the table is empty.
