# Feature Specification: Fixing borderline conventions in the training set

**Feature Branch**: `003-borderline-conventions`

**Created**: 2026-10-05

**Status**: Approved (implemented; measured result in runs/003-relabel-v4)

**Input**: User description: "There is a convention conflict between the training data and the owner's rules at the borderline cases: the teacher labeled MFA/password/SSO issues as Access Management en masse, while per the owner's convention some of these belong to Security; the peripheral↔endpoint border is similarly blurred. The model therefore does not learn the house rules. We want the training set's borderline cases to follow the owner's convention, with the improvement measurable on the frozen test set."

## Background (diagnosis)

From the 002 measurement (`runs/002-boost/metrics.json`, 3 seeds, frozen test):

- Laptop / Endpoint: 91.3% → **97.1%** (the extension worked),
- Printers & Devices: 86.2% → 86.2% (flat),
- **Security: 79.5% → 78.2%** (did not improve), overall 94.0% (SC failed).
- Diagnosis: Security was not a quantity problem but a **convention
  problem**. In the 001 T017 review the owner ruled "MFA push not arriving"
  type rows as Security, while the teacher labeled these Access Management in
  the training set (a strong 158-row convention). The 100 generated Security
  rows could not override that.
- Open question: the cause of Printers & Devices' flatness was unknown — so
  the first step is a **confusion measurement** (which category it is confused
  with), because a fix only makes sense when targeted at measured borders.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Confusion map (Priority: P1)

The owner first wants to see exactly where the model errs: which category is
confused with which on the frozen test, row by row.

**Why this priority**: The 002 lesson is that data added on gut feeling does
not fix (Security). A fix only makes sense targeted at measured confusion
pairs.

**Independent Test**: one command prints the confusion matrix and the list of
misclassified rows (text, true label, predicted label).

**Acceptance Scenarios**:

1. **Given** the 002 model and the frozen test, **When** the report runs,
   **Then** every misclassified row is listed with its true and predicted
   label.

---

### User Story 2 - Borderline relabeling per the owner's table (Priority: P1)

The owner receives an explicit table of borderline candidates from the
training set (keyword-based candidates, current label, suggested label),
reviews/corrects it, and labels are rewritten according to the approved
table.

**Why this priority**: This is the feature's actual fix; the convention is
the owner's, not the teacher's.

**Independent Test**: the relabeling is logged, reversible (the 001/002
training sets remain untouched), and the number of rewritten rows matches the
approved table exactly.

**Acceptance Scenarios**:

1. **Given** the candidate list, **When** the owner approves it (possibly
   modified), **Then** only the approved rows' labels change.
2. **Given** the relabeled training set, **When** the split checker runs,
   **Then** 0 overlap with the frozen test (id + text), as before.

---

### User Story 3 - Re-measurement and verdict (Priority: P1)

The model re-measured on the fixed training set with the unchanged recipe and
3 seeds, compared to the baselines (noise: 12%; teacher: 93.3%; boost: 94.0%),
with the non-overlapping-interval rule.

**Acceptance Scenarios**:

1. **Given** the re-measurement, **When** the SC gate runs, **Then** the
   report shows all three baselines and the new value per category.

### Edge Cases

- The borderline relabeling "tilts" the model sideways (e.g. Access
  Management now degrades): the SC-003 protection catches it.
- The candidate list is too aggressive (genuine Access tickets would be
  moved): the owner's review (MANUAL GATE) filters it.
- The convention is internally contradictory (identical text would get
  different labels in two sets): the review flags this too; the frozen test's
  convention is authoritative.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A confusion report: matrix + list of misclassified rows (text,
  true, predicted), on the 002 model, on the frozen test.
- **FR-002**: Borderline candidates are collected with a documented,
  keyword-based rule (the rule is part of the report).
- **FR-003**: Relabeling may only happen on rows approved by the owner
  (MANUAL GATE), into a new versioned training file; the previous training
  sets remain untouched (reversibility).
- **FR-004**: The recipe is unchanged (as in 002); 3 seeds (0, 1, 2); frozen
  test unchanged.
- **FR-005**: The report compares against the 3 previous references
  (noise / teacher / boost), with a non-overlapping-interval verdict.

### Key Entities

- **Confusion pair**: (true label, predicted label) with frequency and row
  list.
- **Borderline candidate**: a train row that may belong to another category
  per a keyword rule; awaits the owner's decision.
- **Relabeled training set**: the 002 set + the approved label changes; a
  separate versioned file.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Security ≥ 90% mean (3 seeds), every seed ≥ 85%; Printers &
  Devices ≥ 90% mean — on the frozen test.
- **SC-002**: Overall accuracy ≥ 95% (3-seed mean), with a non-overlapping
  interval versus 002's 94.0% ± 0.5%.
- **SC-003 (protection)**: the ≥96% categories do not degrade by more than 2
  points; Laptop/Endpoint does not drop more than 2 points from its 002 value
  of 97.1%.
- **SC-004**: the misclassification report exists, and the fix targeted the
  measured confusion pairs (traceable in the report).

## Assumptions

- The frozen test set's convention (the owner's T017 decisions) is
  authoritative; the teacher's convention can be overridden.
- The convention conflict is localized: limited to the MFA/password/SSO and
  peripheral/endpoint borders.
- No outbound data traffic is needed in this feature (relabeling and training
  only) — if it were needed, separate approval is required.

## Out of Scope

- Generating new synthetic examples (002's tool; only relabeling here).
  *Restart condition: if a data-quantity problem is still measurable after
  the relabeling.*
- Threshold calibration / DSPy (excluded, as in 002).
- Modifying the frozen test set. *Restart condition: separate spec, if the
  convention itself changes.* (This later became feature 004.)
