# tiny-incident-triage Constitution

## Core Principles

### I. Measurement discipline (NON-NEGOTIABLE)

Every quality claim starts and ends with a measurement. A baseline is ALWAYS
taken before any change, written to a file, broken down per axis. Improvement
is only accepted on non-overlapping intervals (noise measured on small samples
with 2–3 repetitions). Gates are exit-code commands (e.g. `pytest -q`,
`python -m triage eval --min-accuracy 0.85`), not subjective steps. Cache
hygiene is mandatory when measuring (cache=False or equivalent).

### II. Data hygiene (NON-NEGOTIABLE)

Train and test sets never mix; the split seed is fixed and documented in the
spec. Nothing touches the test set during training — evaluation always runs on
the same frozen test set. Invalid or missing labels: dropped from training,
never guessed.

### III. Version pinning

Model, tokenizer, library and data versions are always pinned exactly (no
floating aliases, no `latest`). A version change = baseline re-measured.

### IV. Data privacy

Ticket text does not leave the machine by default. Teacher labeling may only
happen through an account/provider explicitly approved by the owner, and the
spec records which dataset was allowed out and which was not.

### V. Simplicity (YAGNI)

The smallest solution that passes the gates. No speculative abstraction; what
the spec does not require does not get built.

## Development environment

Implementation happens locally, on the owner's Windows 11 PC (Ryzen 5 7600X,
32 GB RAM, Radeon RX 7900 XT — no NVIDIA/CUDA). Training runs on CPU; every
hardware assumption in plan.md files follows from this. There is NO
server-side Prime Agent handoff in this project — if that ever becomes
necessary, it happens via a constitution amendment.

## Review process

- spec.md, plan.md and tasks.md each pass through a human approval gate;
  none of them counts as approved without the owner's explicit decision.
- Tasks marked MANUAL GATE must not be checked off by an agent — the owner
  performs and confirms them.
- The constitution supersedes all other practices; amending it is a
  documented, owner-approved step.

## Governance

The Constitution Check gate is mandatory when writing every spec and plan: a
violation must be fixed, or explicitly justified in the plan.md Complexity
Tracking section.

**Version**: 1.0.0 | **Ratified**: 2026-10-05 | **Last Amended**: 2026-10-05
