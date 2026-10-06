# Implementation Plan: Full HugBor adoption

**Branch**: `005-style-robustness` | **Date**: 2026-10-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/005-style-robustness/spec.md`

## Summary

HugBor becomes the sole data source and its 15-category taxonomy the new
label system. Tidy + stratified holdout split; label trust verified by a
local-model blind spot-check (≥90% agreement, else stop); thin categories
topped up by the local Qwen (owner review); new 3-seed baseline with the
unchanged recipe; wild probe remapped. Zero cloud LLM traffic.

## Technical Context

The stack and recipe are unchanged. Old data (mindweave 997 rows, v1/v2 test
sets) is archived, unused. New module: `src/triage/hugbor.py` (tidy, mapping,
truncation, split, spot-check); `src/triage/stylegen.py` (top-up generation).

## Key Decisions

### D1: text = short_description + description, truncated at ~500 chars

**Decision**: the tidy text is `short_description + ". " + description`, cut
to the first ~500 characters (≈128 tokens) at data prep; the truncated-row
count is reported (FR-004).

**Rationale**: symptom + impact sit in the first sentences; the resolution
tail is not triage input. The recipe's maxlen stays 128 (sacred rule).

### D2: Label trust = local blind spot-check, not hand review

**Decision**: stratified sample (5 rows/category = 75 rows), the local Qwen
labels it blind (the 15-category list in the prompt), and the agreement rate
with the dataset labels is written to `runs/005-hugbor/spotcheck.json`.
Threshold ≥90%; below → the pipeline stops before training (SC-001, spec
Edge Case).

**Rationale**: the owner trusts the dataset but the mindweave lesson demands
measured evidence; the check is cheap, local, and numeric — without asking
for hand corrections the owner declined.

### D3: Stratified holdout = the new frozen test

**Decision**: per-category stratified split, seed=0, ~20% test
(~328 rows expected); the held-out rows with dataset labels (spot-check
verified) become the new frozen test (`data/labels/hugbor_test.jsonl` +
`data/tidy/test.parquet` regenerated). Old test sets archived (v1/v2 stay in
the repo untouched).

**Rationale**: a test must exist before training (Constitution II), and the
reference must come from the same trusted source as the training data.

### D4: Top-up only where thin (<100 rows), in HugBor's register

**Decision**: Telephony, Software, Cloud Services, Data Center get local
generation prompted with few-shot examples from HugBor itself (to match the
register), target ≥100 train rows/category after merge; owner reviews a
sample (MANUAL GATE, SC-003).

**Rationale**: few-shot from the dataset itself keeps style consistent —
better than our earlier free-form templates.

### D5: Probe remapped, old numbers archived not gated

**Decision**: the 8 probe incidents map to the new taxonomy (all clean:
Access Management, Hardware, Network, Email, Application,
Printer/Peripherals, Security, Telephony); SC-002's ≥90% baseline gate
applies to the new taxonomy only; old-taxonomy numbers live in RESULTS.md as
historical context, not as comparison gates.

## Architecture (ASCII)

```text
HugBor (1,640 rows, commit hash pinned)
        |
        v
[hugbor tidy]  text = short_desc + desc, truncate ~500c   data/tidy/hugbor.parquet
        |      stratified split 80/20, seed=0, 0 overlap
        |      -> train ~1312 / test ~328 (new frozen test)
        v
[spotcheck] local Qwen, blind, 75 rows   runs/005-hugbor/spotcheck.json
        |      agreement >= 90% else STOP (SC-001)
        v
[stylegen] top-up thin categories (<100)  data/labels/generated_v3.jsonl
        |      few-shot from HugBor, local only
        v
[review] owner sample (MANUAL GATE, SC-003)
        |
        v
[train] unchanged recipe, seeds 0/1/2    runs/005-hugbor-s*/
        |
        +--> [eval] new frozen test -> runs/005-hugbor/metrics.json (SC-002)
        +--> [probe] remapped wild probe (SC-004)
```

## Constitution Check

| Principle | Check | Result |
|-----|-----------|----------|
| I. Measurement discipline | new baseline 3-seed; label trust measured numerically (D2); old numbers archived, not gates (D5) | PASS |
| II. Data hygiene | stratified holdout before training; 0 overlap id+text; generated rows reviewed | PASS |
| III. Version pinning | stack/recipe unchanged; HugBor commit hash; teacher pinned gguf | PASS |
| IV. Data privacy | zero cloud LLM traffic; HF download is a dataset fetch | PASS |
| V. Simplicity | one source, one new thin module; no hand-review machinery beyond one gate | PASS |

## Project Structure

```text
src/triage/hugbor.py          # NEW: tidy, truncation, split, spotcheck
src/triage/stylegen.py        # NEW: top-up generation (few-shot from HugBor)
src/triage/data.py            # merge reuse
tests/unit/test_hugbor.py     # NEW
tests/unit/test_stylegen.py   # NEW
probes/wild_probe_v2.jsonl    # remapped probe (new taxonomy)
scripts/run_hugbor.py         # NEW: 3-seed baseline + dual eval
data/labels/hugbor_test.jsonl, generated_v3.jsonl, train_v5.parquet
```

## Complexity Tracking

No constitution violation — the table is empty.
