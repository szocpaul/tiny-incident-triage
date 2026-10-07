# Feature Specification: Borderline-pair fix (Cloud Services, Performance)

**Feature Branch**: `006-borderline-pairs`

**Created**: 2026-10-07

**Status**: Draft

**Input**: User description: "The final model's two categories (Cloud Services 71.4%, Performance 81.9%) lag the rest — not from too few training examples (104+ in each), but from blurred taxonomy borders (Application ↔ Cloud Services, Application ↔ Performance). We don't know numerically which side of the pairs the errors concentrate on, and whether a targeted data fix (top-up or relabeling) can improve the situation without degrading the other categories."

## Background (diagnosis)

- Final model (005-uservoice): 94.55% ± 1.32% on the frozen holdout; 10/14
  categories ≥ 92%, but **Cloud Services 71.4%** (n=14) and
  **Performance 81.9%** (n=24) lag.
- The label-trust spot-check (005) already documented these two pairs as
  inherently ambiguous (Application ↔ Cloud Services, Application ↔
  Performance) — taxonomy overlap, not noise; accepted with a carve-out.
- Training coverage is sufficient (≥104 rows/category after the top-up), so
  a pure quantity fix is not the lever; the 003 lesson applies: measure the
  confusion first, fix only what is measured.
- Available machinery from 003: `confusion.py` (confusion report),
  `relabel.py` (candidates + relabeling), `stylegen.py` (local top-up) —
  this feature reuses them.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Confusion map for the borderline pairs (Priority: P1)

The owner first wants to see exactly where Cloud Services and Performance
errors land: which category they are confused with, row by row, on the
frozen holdout.

**Why this priority**: the fix must target the measured direction of
confusion; guessing failed before (002).

**Independent Test**: one command prints the confusion pairs for the two
categories with the misclassified rows listed (text, true, predicted).

**Acceptance Scenarios**:

1. **Given** the 005 final model and the frozen holdout, **When** the report
   runs, **Then** every misclassified Cloud Services and Performance row is
   listed with true and predicted labels.

---

### User Story 2 - Targeted fix per the confusion evidence (Priority: P1)

Based on the measured confusion pairs, a targeted fix is applied to the
training data — top-up examples for the missing distinction, relabeling of
documented borderline rows, or both. The owner reviews the fix before it
enters training.

**Why this priority**: this is the feature's actual improvement; its shape
(top-up vs relabel vs both) is decided by US1's evidence, not in advance.

**Independent Test**: the fix is logged (what changed, how many rows,
evidence link), reversible (train_v6 untouched), and the owner approved it
(MANUAL GATE).

**Acceptance Scenarios**:

1. **Given** the confusion map, **When** the fix proposal is built, **Then**
   every proposed change links to a measured confusion pair.
2. **Given** the approved fix, **When** the overlap checker runs, **Then** 0
   overlap with the frozen holdout (id + normalized text), as before.

---

### User Story 3 - Re-measurement and verdict (Priority: P1)

The fixed training set, unchanged recipe, 3 seeds, frozen holdout, and the
wild probe — compared against the 005 numbers with the
non-overlapping-interval rule.

**Acceptance Scenarios**:

1. **Given** the re-measurement, **When** the report runs, **Then** Cloud
   Services and Performance are shown against their 005 values, and every
   other category against its own 005 value.

### Edge Cases

- The confusion map shows errors spread evenly (no concentrated pair): the
  feature stops and reports — no fix is better than a scattergun fix
  (documented outcome).
- The fix tilts the model (e.g. Application degrades): the SC-003 protection
  gate catches it.
- The two categories have too few test rows (14 and 24) for sharp claims:
  the report shows raw counts; improvement claims use the
  non-overlapping-interval rule on the 3-seed means, acknowledging n is
  small.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Confusion report on the 005 final model, frozen holdout,
  focused on the Cloud Services and Performance rows (with all confusion
  pairs listed).
- **FR-002**: The fix proposal is derived from the measured pairs (each
  proposed change cites its evidence); built with the local Qwen for any
  top-up (zero cloud traffic), using 003's relabel machinery where relevant.
- **FR-003**: The owner reviews the fix (MANUAL GATE) before training; the
  change is versioned (train_v7.parquet), predecessors untouched.
- **FR-004**: Unchanged recipe; 3 seeds (0, 1, 2); frozen holdout; probe
  measured.
- **FR-005**: The report compares against 005 (per category + overall),
  with a non-overlapping-interval verdict.

### Key Entities

- **Borderline pair**: (Application, Cloud Services) and (Application,
  Performance) — the documented taxonomy overlap.
- **Fix proposal**: the evidence-linked list of top-up and/or relabel
  actions awaiting owner approval.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Cloud Services 3-seed mean ≥ 85% (from 71.4%) AND Performance
  ≥ 88% (from 81.9%) on the frozen holdout — with non-overlapping intervals
  versus 005.
- **SC-002**: Overall accuracy ≥ 94.55% − 0.5 pp (3-seed mean) — the fix
  must not trade away the whole.
- **SC-003 (protection)**: no other category drops more than 2 pp versus
  its 005 value; probe stays ≥ 6/8 on at least 2 seeds.
- **SC-004**: if the confusion map shows no concentrated pair, the feature
  ends with a documented negative result instead of a forced fix.

## Assumptions

- The frozen holdout (005) and probe set are unchanged.
- The borderline pairs' taxonomy itself stays (merging categories was
  decided against in 005); the fix is data-side, not taxonomy-side.
- Local Qwen available for any top-up (zero cloud traffic).

## Out of Scope

- Taxonomy changes (merging or renaming the borderline categories).
  *Restart condition: separate spec, if data-side fixes provably fail.*
- maxlen experiments (parked, BACKLOG B0).
- New data sources beyond HugBor + local generation.
