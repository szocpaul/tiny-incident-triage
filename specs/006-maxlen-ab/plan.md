# Implementation Plan: maxlen A/B (128 vs 256)

**Branch**: `006-maxlen-ab` | **Date**: 2026-10-07 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/006-maxlen-ab/spec.md`

## Summary

One changed variable: `max_length`. Arm A (128, status quo) and arm B (256)
train on train_v6 with the unchanged recipe, 3 seeds each, evaluated on the
frozen HugBor holdout and the wild probe. A pre-registered decision rule
produces the verdict mechanically.

## Technical Context

Everything inherited from 005 (stack, data, taxonomy, test set, probe). The
only code change: `train.py` gets a `maxlen` parameter (currently hardcoded
via `RECIPE["maxlen"]`). New script: `scripts/run_maxlen_ab.py`.

## Key Decisions

### D1: maxlen as an explicit override, recipe dict untouched

**Decision**: `train_run(..., maxlen=None)` — None means the recipe default
(128); arm B passes 256. The RECIPE constant itself is not edited, so arm A
is bit-identical to previous runs' code path.

**Rationale**: FR-002 (single variable) must be provable from the code too.

### D2: Memory probe before arm B

**Decision**: arm B starts with a one-batch smoke step (batch=32, maxlen=256)
to verify CPU memory; on failure the arm is documented as failed (spec Edge
Cases), no silent batch reduction.

### D3: One report, verdict from the pre-registered rule

**Decision**: `runs/006-maxlen/report.json` contains both arms (per-seed and
mean ± stdev accuracies, probe hits, train seconds) plus the computed
verdict per SC-001. The MANUAL GATE reviews the verdict's application, not
the numbers' reinterpretation.

## Architecture (ASCII)

```text
train_v6 + frozen holdout + probe (005 artifacts, untouched)
        |
        +-- arm A: maxlen=128, seeds 0/1/2 -> runs/006-maxlen-a-s*/
        +-- arm B: maxlen=256, seeds 0/1/2 -> runs/006-maxlen-b-s*/
                        |
                        v
              [report] runs/006-maxlen/report.json
              per arm: accuracy (mean±stdev), probe, train_seconds
              verdict: pre-registered rule (SC-001)
                        |
                        v
              [MANUAL GATE] owner accepts the verdict
```

## Constitution Check

| Principle | Check | Result |
|-----|-----------|----------|
| I. Measurement discipline | pre-registered decision rule; 3 seeds; non-overlapping interval required for adoption | PASS |
| II. Data hygiene | data/test/probe frozen from 005; no overlap changes | PASS |
| III. Version pinning | stack unchanged; the recipe constant untouched (D1) | PASS |
| IV. Data privacy | no outbound traffic at all | PASS |
| V. Simplicity | one parameter, one script, one report | PASS |

## Complexity Tracking

No constitution violation — the table is empty.
