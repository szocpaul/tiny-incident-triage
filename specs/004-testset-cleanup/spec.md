# Feature Specification: Cleaning the frozen test set

**Feature Branch**: `004-testset-cleanup`

**Created**: 2026-10-05

**Status**: Approved (implemented; measured result in runs/004-testset-v2)

**Input**: User description: "The frozen test set — the reference of every measurement — contains duplicated texts with contradictory labels (the same ticket once Security, once Email & Collaboration), so measured accuracy has an artificial ceiling: on those rows the model cannot in principle be flawless. We want the test set cleaned in a way that keeps it comparable and auditable — and the current 98.2% result re-measurable against the clean reference."

## Background (diagnosis)

The 003 confusion reports (`runs/003-confusion*`) revealed:

- The text "Spam burst hit shared support inbox this morning" appears in
  **5 rows** of the frozen test with contradictory labels (3× Security, later
  canonicalized from a mix of Security / Email & Collaboration) — the teacher
  labeled the duplicates inconsistently.
- "User cannot map shared drive from new laptop" likewise in multiple copies,
  with Laptop/Endpoint AND Network & VPN labels.
- On these rows no deterministic model can be fully correct: the measured
  ceiling was ~98.5–99%, not 100%.
- The hand-checked test set was created in 001 (T017, owner review); the
  duplicate conflicts did not surface then because the review worked at the
  200-row sample level, not at text-duplication level.
- The test set was "frozen" per the 002/003 specs — this feature is the
  rule-bound exception: it precisely delineates what may change and what may
  not.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Conflict map of the test set (Priority: P1)

The owner first wants to see exactly which texts appear multiple times and
with what contradictory labels — before anything changes.

**Why this priority**: The test set is the measurement base; change is only
permissible with full transparency.

**Independent Test**: one command lists the duplicated texts and their
labels; with zero conflicts it produces an empty report.

**Acceptance Scenarios**:

1. **Given** the frozen test set, **When** the conflict report runs, **Then**
   every duplicated text is listed with its copy count and label
   distribution.

---

### User Story 2 - The owner's decision on canonical labels (Priority: P1)

For every conflicted text the owner designates the SINGLE correct label (or
drops the rows if the text is unjudgeable); the decision is logged.

**Why this priority**: The convention is the owner's; the machine cannot
decide in their place in the reference set.

**Independent Test**: the decision table covers every conflict; an unfilled
row prevents freezing.

**Acceptance Scenarios**:

1. **Given** the conflict table, **When** the owner has decided on every row,
   **Then** the new test set has no two identical texts with different
   labels.

---

### User Story 3 - Versioned replacement and re-measurement (Priority: P1)

The old test set remains archived (`handchecked_test_v1`); the new
`handchecked_test_v2` becomes the frozen reference; the final model is
re-measured on both, and the report shows them side by side.

**Why this priority**: Comparability is only preserved this way: the v1
historical numbers remain valid, v2 is the new base.

**Acceptance Scenarios**:

1. **Given** the v1 and v2 test sets, **When** the final model is measured on
   both, **Then** the report contains both results and the explanation of the
   difference (the removed conflicted rows).
2. **Given** the v2 test set, **When** the split checker runs, **Then** 0
   overlap with the training set (id + normalized text), as before.

### Edge Cases

- The owner finds a conflicted text unjudgeable: the rows are dropped, and
  the drop appears in the log with a reason.
- Some duplicates may also be contradictory in the training set: cleaning the
  training side is a separate decision; this feature focuses on the test.
- v2 will be smaller than v1 (duplicate surplus falls out): the report
  documents the n change; percentages remain comparable.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Conflict report on the frozen test set: duplicated (normalized)
  texts, copy counts, label distribution.
- **FR-002**: Conflicts are resolved only by the owner's explicit, row-level
  decision (MANUAL GATE); an unfilled decision = freezing stops.
- **FR-003**: The old test set is archived unchanged
  (`handchecked_test_v1.jsonl`), the new one is `handchecked_test_v2.jsonl`;
  the difference (dropped/relabeled rows) is written to a log file, with
  reasons.
- **FR-004**: The final model (003-relabel-v4 best seed) is NOT retrained,
  merely re-evaluated on both test sets; the report shows the two results and
  the n difference.
- **FR-005**: The training set is unchanged in this feature.

### Key Entities

- **Conflict group**: test rows with identical normalized text and differing
  labels.
- **Canonical decision**: the owner's row-level ruling (one label or drop).
- **Test set version**: v1 (archived, historical) and v2 (frozen, current).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 0 conflict groups in the v2 test set (gate command:
  `python -m triage testconflicts --exit-code`, 0 = clean).
- **SC-002**: The v2-measured overall accuracy ≥ v1's 98.2% minus the removed
  rows' share — i.e. the cleanup must not magically "improve" the model; the
  report shows both numbers and the n difference.
- **SC-003**: Every removed row appears in the log with a reason (the owner's
  decision), and v1 is restorable unchanged.

## Assumptions

- The number of conflicts is small (per the 003 reports ~3–5 text groups).
- The historical results measured on v1 (93.3% / 94.0% / 97.3% / 98.2%)
  remain valid in their own context; v2 is the new reference.
- The feature needs no outbound data traffic and no retraining.

## Out of Scope

- Cleaning the training set's duplicate conflicts. *Restart condition:
  separate spec, if training-side noise remains a measurable problem after
  the v2 measurement.*
- Adding new test rows to the test set. *Restart condition: separate spec,
  with more hand review.*
- Retraining the model for v2 (not needed: the test is independent of
  training).
