# Feature Specification: Ticket triage classifier

**Feature Branch**: `001-ticket-triage`

**Created**: 2026-10-05

**Status**: Approved (implemented)

**Input**: User description: "Categorizing incoming IT support tickets and routing them to the right team is manual work today: slow, expensive and inconsistent. We want every new ticket to get the right category immediately, with consistent quality — without ticket text leaving our own environment, and without recurring API costs."

## Background (diagnosis)

- The target domain (ITSM ticket triage) has no public real-world datasets —
  company tickets are sensitive. The available asset is a 1,000-row synthetic
  ticket sample with category labels (8 categories, balanced).
- The cost and inconsistency of manual triage is a known problem; market
  solutions (built-in AI of ITSM tools, LLM APIs) are either expensive or send
  ticket text to third parties.
- **Measurement finding (2026-10-05, baseline run):** the sample's labels are
  independent of text content — the synthetic generator drew text and label
  separately. Evidence: 3-seed baseline 12.0% ± 0.0 accuracy (chance level,
  1/8) with 99.9% train accuracy. The texts are good, the labels are noise —
  so training labels are produced by a large language model (teacher), and the
  evaluation reference is a hand-checked frozen test set reviewed by the owner.
- This is the diagnosis; solution directions (model size, training method,
  labeling strategy) land in plan.md.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Teacher labels and a hand-checked test set (Priority: P1)

The owner labels the unlabeled ticket texts through their own approved LLM
account, and hand-reviews a subset — this hand-checked set becomes the frozen
test reference.

**Why this priority**: The baseline measurement proved the source labels are
noise; without trustworthy labels there is nothing to train on and nothing to
measure against. This story is the prerequisite of everything else.

**Independent Test**: Labeling runs as one command, yields a valid label for
≥99% of rows, with a cost/time log; the hand-checked test set lives in a
separate versioned file that training never sees.

**Acceptance Scenarios**:

1. **Given** 1,000 unlabeled ticket texts, **When** the labeling command runs,
   **Then** every row gets one of the 8 categories (invalid = dropped and
   logged), and the run's cost/time statistics are written to a file.
2. **Given** ~200 rows hand-reviewed by the owner, **When** the test set is
   frozen, **Then** it lives in a separate, versioned file, and the training
   process errors out if a train row would land in it.

---

### User Story 2 - Categorized ticket, locally (Priority: P2)

The owner gives the system a ticket text (title + description) and immediately
gets the most likely handling category back, locally — no external service,
no API cost.

**Why this priority**: The entire value of the feature: if categorization
does not work reliably and locally, the rest delivers no value on its own.

**Independent Test**: The system's accuracy on the frozen test set is
checkable with one command whose exit code signals whether the threshold is
met.

**Acceptance Scenarios**:

1. **Given** a trained classifier and the frozen test set, **When** the eval
   command runs, **Then** overall accuracy reaches the specified threshold and
   the command exits 0.
2. **Given** a new, unseen ticket text, **When** the system classifies it,
   **Then** the answer is one of the 8 categories, arriving in well under a
   second on the local machine.

---

### User Story 3 - Minute-scale retrainability (Priority: P3)

If the category system or the ticket mix changes, the owner retrains the
system with new data in minutes and immediately sees the new measurement —
no week-long project, no external dependency.

**Why this priority**: Business categories change; fast retraining is what
keeps the system alive long-term. But the first value comes from US1–US2.

**Independent Test**: The full pipeline (data → trained model → measurement)
is reproducible by re-running one command, and end-to-end time is measurable.

**Acceptance Scenarios**:

1. **Given** a modified training set, **When** the owner re-runs the pipeline,
   **Then** training and evaluation finish within the specified time limit on
   the local machine, and the new measurement lands next to the previous one
   in the measurement log.

---

### Edge Cases

- Invalid or missing label in training data: the row is dropped from training
  and the drop is logged (never guessed).
- Empty or extremely short ticket text: the system signals that the input
  cannot be classified reliably, instead of confidently guessing wrong.
- Extremely long ticket text: the truncation rule is documented and the
  measurement is made with that rule.
- A train row accidentally lands in the test set: the split checker proves 0
  overlap; on error the run stops.
- Non-English ticket text: current data is English; other languages' behavior
  is unspecified (see Out of Scope).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system must produce a unified data table with a documented
  schema from the source data (id, text, label, split).
- **FR-002**: The train/test split must be reproducible with a fixed seed,
  and must prove 0 overlap between the two sets at the start of every run.
- **FR-003**: The system must train the classifier locally on the developer
  machine from the training set.
- **FR-004**: Evaluation must be runnable as one command that writes overall
  and per-category accuracy to a file and returns a threshold-based exit code.
- **FR-005**: Every measurement starts with a baseline: the first evaluation
  result is written to a file before any further change.
- **FR-006**: Ticket text must not leave the machine by default.
  **Exception (approved by the owner on 2026-10-05):** the 1,000 ticket texts
  may go out once for labeling through the owner's own approved LLM account.
  Any other outbound traffic remains forbidden.
- **FR-007**: Every run's configuration (seeds, versions, parameters) is saved
  with the run so the result is reproducible.
- **FR-008**: Teacher labeling runs as one command, resumable after
  interruption; invalid answer = dropped + logged (never guessed); the run
  writes time and cost statistics.
- **FR-009**: The hand-checked test set lives in a separate versioned file;
  the training process errors out if a train row would land in it (0 overlap
  between train and the hand-checked test too).

### Key Entities

- **Ticket**: the unit to classify; id, title, description.
- **Category**: the label of the handling team; 8 categories in v1.
- **Teacher label**: the label produced by the LLM account; the training
  source.
- **Hand-checked test set**: ~200 rows reviewed by the owner; the evaluation
  reference; frozen, versioned.
- **Split**: the train/test allocation; fixed seed, documented ratio.
- **Measurement run**: one training + evaluation unit; kept together with its
  configuration and result file.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `python -m triage eval --min-accuracy 0.85` exits 0 on the
  hand-checked frozen test set (the student typically lands a few points under
  its teacher — per the tiny-classifiers tutorial measurements).
- **SC-002**: Per-category accuracy ≥ 75% in every category on the frozen test
  set (the eval report prints this row by row).
- **SC-003**: Full training + evaluation ≤ 15 minutes on the local machine,
  on CPU (measured: run log timestamps).
- **SC-004**: Classifying a new ticket ≤ 100 ms/item on the local machine,
  measured per individual call.
- **SC-005**: Teacher labeling yields a valid label for ≥99% of rows; the
  run's cost and time statistics are written to a file.

## Assumptions

- ~~The synthetic sample's category labels count as acceptable reference for
  the v1 measurement~~ — **REFUTED by the baseline measurement (2026-10-05):
  12.0% ± 0.0, chance level.** Instead: teacher labels count as the training
  reference; the evaluation reference is the hand-checked test set.
- The owner's Kimi Code account is usable for labeling through lm15's saved
  sign-in; the owner approved this one-off, 1,000-row outbound traffic
  (FR-006 exception).
- The owner's machine is the only execution environment; internet access is
  needed for the initial downloads and the approved labeling only.
- The data and the trained model licenses allow local, experimental use.

## Out of Scope

- Evaluation on real (PDI-sourced) incidents: the available 67 rows are too
  few for reliable measurement, so v1 deliberately excludes it.
  *Restart condition: at least a few hundred real labeled incidents available.*
- Priority estimation (P1–P4): rare classes are too few in the sample.
  *Restart condition: the full 10,000-row dataset is available, or at least
  150/live class from real tickets.*
- Non-English (e.g. Hungarian) ticket support. *Restart condition: Hungarian
  tickets appear in the target environment with at least a few hundred labeled
  examples.*
- Production ServiceNow integration (flow, REST call from the instance).
  *Restart condition: SC-001 passes and the owner requests productionization.*
- Generative answer or solution-suggestion writing (the system only
  categorizes). *Restart condition: separate spec, different architecture.*
