# Feature Specification: Strengthening the weak categories

**Feature Branch**: `002-security-recall`

**Created**: 2026-10-05

**Status**: Approved (implemented; measured result in runs/002-boost)

**Input**: User description: "The system's weak categories are the weakest link: about a quarter of Security tickets (76.9%), about a seventh of Printers & Devices (86.2%) and about an eighth of Laptop/Endpoint (87–91%) tickets land with the wrong team; overall accuracy is 92%. Goal: the weak categories strengthen to ≥90%, overall accuracy ≥95% — without the already-good (96–100%) categories degrading."

## Background (diagnosis)

From feature 001's teacher-labeled baseline (`runs/baseline-teacher/metrics.json`,
3 seeds, hand-checked 200-row test):

- **Security: 79.5% mean / 76.9% min** (n=26) — the weakest category.
- **Printers & Devices: 86.2% mean** (n=29) — the second weak link.
- **Laptop / Endpoint: 91.3% mean / 87.0% min** (n=23) — the third.
- The other five categories stand at 96–100%; overall accuracy 93.3%
  (3-seed mean; 92.0% on a single run).
- Train-set distribution: Security only **47 rows** (5.9%), Printers &
  Devices 121 rows, Laptop / Endpoint 98 rows; the most frequent category has
  185 rows.
- Counterpoint: Telephony reaches 100% with just 10 train rows — so few
  examples alone are not fatal. Security presumably struggles at the
  **borderline cases** (MFA, password, SSO → toward Access Management);
  Printers & Devices and Laptop/Endpoint at the Endpoint–peripheral border.
  Underrepresentation and the semantic boundary act together.
- The measurement framework is given: frozen hand-checked test set, 3-seed
  runs, non-overlapping-interval rule (Constitution I).

This is the diagnosis; the solution direction (producing and labeling new
examples) lands in plan.md. Threshold-calibration (ReAnchor-style) solutions
were explicitly excluded by the owner: the goal is improving the model, not
adjusting the decision threshold.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Weak categories catch up (Priority: P1)

The owner wants the system to classify reliably in every category: the weak
trio (Security, Printers & Devices, Laptop/Endpoint) rises above ≥90%,
overall accuracy reaches ≥95% — on the frozen test set, with numeric proof.

**Why this priority**: This is the only value the feature exists for;
everything else (process, tooling) is instrumental to it.

**Independent Test**: The strengthened model's accuracy in every category is
measurable on the frozen, hand-checked test set with a single gate command,
and comparable to the baseline metrics.json.

**Acceptance Scenarios**:

1. **Given** the strengthened model, **When** the eval gate runs on the
   frozen test set, **Then** every category's accuracy reaches the specified
   threshold (SC-001).
2. **Given** the same measurement, **When** the other categories are examined,
   **Then** none degrades significantly versus baseline (SC-003).

---

### User Story 2 - Verified generation of new weak-category examples (Priority: P2)

The owner wants additional Security-, Printers & Devices- and
Laptop/Endpoint-themed ticket examples in the training set, with trustworthy
labels — and to hand-review a sample of the generated examples before they
become training data.

**Why this priority**: The diagnosis points to underrepresentation as the
prime suspect; but without hand review, generated data would carry the same
trust problem we saw with the noisy sample in 001.

**Independent Test**: the new examples live in a separate file, a sample is
hand-reviewed, and they enter the training set only after approval.

**Acceptance Scenarios**:

1. **Given** the new generated examples, **When** the owner reviews the
   sample, **Then** rows judged wrong do not enter the training set.
2. **Given** the extended training set, **When** the split checker runs,
   **Then** there is still 0 overlap with the hand-checked test set (FR-009
   inherited).

---

### Edge Cases

- Generated examples too templated (copying the teacher's clichés): the hand
  review filters them; measurement happens on the frozen (not generated) test
  set, so templatedness cannot falsify the result.
- Generated examples accidentally overlap a test row: the overlap checker
  also tests text identity (not just id); on error the run stops.
- The extension degrades other categories (e.g. confusion grows toward Access
  Management): the SC-003 gate catches exactly that.
- New examples would introduce a topic outside the existing 8 categories:
  not admitted; the category system is frozen in this feature.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: New training examples are produced in the same schema as the
  existing training set (id, text, label), and live in a separate, versioned
  file.
- **FR-002**: New examples' labels are consistent by construction (the example
  is written for the label's topic), and the owner reviews a sample before
  training (MANUAL GATE).
- **FR-003**: 0 overlap between the extended training set and the frozen test
  set — checked by id AND normalized text.
- **FR-004**: Training runs with the unchanged recipe recorded in 001 (same
  model, hyperparameters, epoch formula); only the data changes.
- **FR-005**: Measurement runs on the frozen, hand-checked 200-row test set
  with 3 seeds (0, 1, 2), and the report compares against `baseline-teacher`
  (mean, stdev, per-category breakdown).
- **FR-006**: Improvement is accepted only with non-overlapping intervals
  (Constitution I) — "somewhat better" is not a result.

### Key Entities

- **Generated example**: an LLM-written, weak-category ticket text; with a
  by-construction label; in a versioned file.
- **Extended training set**: the 001 training set + the approved generated
  examples.
- **Frozen test set**: unchanged (the 200 rows from 001); the basis of
  comparison.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001 (category level)**: the three weak categories (Security, Printers &
  Devices, Laptop / Endpoint) 3-seed mean ≥ 90% on the frozen test set
  (baseline: 79.5% / 86.2% / 91.3%), AND in each of them every seed ≥ 85% —
  proven with non-overlapping intervals. The report also marks the 95%
  stretch goal (not a gate).
- **SC-002 (big picture)**: overall accuracy 3-seed mean ≥ 95% (baseline:
  93.3%), with non-overlapping intervals.
- **SC-003 (protection)**: categories currently ≥96% keep a 3-seed mean ≥
  their baseline mean minus 2 percentage points.
- **SC-004**: training+evaluation ≤ 15 min/seed on the local machine
  (inherited constraint), and the recipe is unchanged (FR-004 verified).
- **SC-005**: of the generated examples, the owner finds ≥90% of the reviewed
  sample correct; the rejected rate is logged.

## Assumptions

- The 001 frozen test set remains unchanged — sacrificing comparability would
  be a greater loss than the benefit of extending the test set.
- The teacher account (Kimi Code) remains usable for one-off, approved data
  generation (the 001 FR-006 exception extends to generation).
- The weak categories' borderline cases are the focus of the extension:
  Security (MFA/password/SSO ↔ Access Management), Printers & Devices and
  Laptop/Endpoint (peripheral ↔ Endpoint border).

## Out of Scope

- Decision-threshold calibration, DSPy/ReAnchor adapter (excluded by the
  owner). *Restart condition: separate spec, if model improvement is
  exhausted.*
- Further polishing of categories currently ≥96%. *Restart condition: SC-001
  and SC-002 pass, and the owner sets a higher bar.*
- Introducing a new category. *Restart condition: separate spec, as it would
  affect the frozen test set too.*
