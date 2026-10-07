# Feature Specification: maxlen A/B (128 vs 256)

**Feature Branch**: `006-maxlen-ab`

**Created**: 2026-10-07

**Status**: PARKED (2026-10-07 — deferred before implementation by owner decision; the 005 evidence suggests truncation is not the main error source. Restart condition in specs/BACKLOG.md#b0)

**Input**: User description: "The recipe's 128-token window truncates 76% of HugBor incidents, cutting content (typically the continuation after the symptom). We don't know numerically what the cut content is worth to the model — nor whether the larger window's cost (slower CPU training) stays below the benefit. We want the question decided by measurement, with the rest of the recipe untouched."

## Background (diagnosis)

- The recipe truncates every input at 128 tokens (`truncation=True,
  max_length=128`). At ~3.5 chars/token that is ≈500 characters.
- HugBor rows: median 532 chars → 76% of the 1,640 rows exceed the window
  (measured at tidy time, `data/tidy/hugbor_stats.json`).
- The truncated tail is mostly the *resolution* section — which a triage
  model does not need — but the borderline categories (Cloud Services,
  Performance) have long, technically dense descriptions where the decisive
  detail may sit later. Unknown until measured.
- The student (Ettin-17M) technically supports up to 512 positions; 256 is
  the practical middle (512 costs ~16× the attention compute of 128 on CPU).
- Project rule: the recipe is sacred — an A/B with a single changed variable
  (maxlen) is the only rule-compliant way to touch it, and the decision rule
  must be written before the measurement.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A single-variable A/B measurement (Priority: P1)

Two runs, identical in everything except `max_length` (128 vs 256): same
training set (train_v6), same frozen holdout test, same seeds (0/1/2), same
recipe otherwise. The owner wants the numbers, not an opinion.

**Why this priority**: the maxlen question has been open since the HugBor
adoption; every future feature (incl. backlog B1) inherits the answer.

**Independent Test**: one command produces both arms' metrics + training
times in a single comparison report.

**Acceptance Scenarios**:

1. **Given** the two arms, **When** training and evaluation finish, **Then**
   the report contains per-arm overall and per-category accuracy (mean ±
   stdev, 3 seeds), probe accuracy, and train seconds per arm.
2. **Given** the report, **When** the decision rule is applied, **Then** the
   verdict (keep 128 / adopt 256 / inconclusive) follows mechanically from
   the pre-registered rule — no post-hoc reinterpretation.

---

### Edge Cases

- 256 is better in accuracy but >2× slower per seed: the decision rule
  (SC-001) accounts for the cost explicitly; the verdict may still be 128.
- The two arms' intervals overlap: verdict = inconclusive, documented; the
  default stays 128 (status quo).
- A seed crashes on memory at 256 (CPU, 32 GB): the run is logged as failed
  and the report says so (no silent retry with changed settings).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Both arms use train_v6 and the frozen HugBor holdout test,
  unchanged; the probe set (wild_probe_v2) is measured with the same model.
- **FR-002**: The ONLY difference between arms is `max_length` (128 vs 256);
  tokenizer, model, optimizer, epoch formula, batch size, seeds identical.
- **FR-003**: Each arm runs 3 seeds (0, 1, 2); metrics per arm: overall +
  per-category accuracy (mean ± stdev), probe hits per seed, train seconds
  per seed.
- **FR-004**: A single comparison report (`runs/006-maxlen/report.json`)
  containing both arms and the verdict per the pre-registered decision rule.

### Key Entities

- **Arm**: one recipe variant (A: maxlen=128, B: maxlen=256) with its runs.
- **Decision rule**: the pre-registered verdict logic (see SC-001).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001 (decision rule, pre-registered)**:
  - **Adopt 256** if arm B's holdout accuracy (3-seed mean) exceeds arm A's
    by ≥ 1.0 percentage point with non-overlapping intervals AND arm B's
    mean train time per seed is ≤ 3× arm A's.
  - **Keep 128** if arm B's advantage is < 1.0 pp or intervals overlap, OR
    the time cost exceeds 3×.
  - **Inconclusive** is an explicit, documented outcome (default: keep 128).
- **SC-002**: both arms complete all 3 seeds; per-category breakdown
  included (the borderline pairs get special attention in the report).
- **SC-003**: probe accuracy reported per arm per seed (informational, not
  part of the verdict).

## Assumptions

- 256 fits CPU memory with batch=32 (verified at arm start; if not, the arm
  is documented as failed per Edge Cases).
- Everything else (data, taxonomy, test set, probe) is frozen from 005.

## Out of Scope

- maxlen=512 (backlog B4; only if 256 wins).
- Any other recipe change (batch size, LR, epochs).
- The B1 confusion-driven fix (runs after this decision, on the winning
  recipe).
