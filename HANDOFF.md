# Handoff — tiny-incident-triage

**For the agent continuing this project (e.g. a Copilot Studio agent).**
Everything you need is in this repo; the conversation history is not needed.
Read in this order: `specs/constitution.md` → this file → the latest spec.

## Current state (2026-10-07)

- Working 17M-parameter ticket classifier, 14 categories, CPU-only
  (3.7 ms/ticket), final metrics: **94.55% ± 1.32%** holdout accuracy,
  **7/8 on all 3 seeds** on the wild probe set. Numbers and method:
  [RESULTS.md](../RESULTS.md); raw data: `runs/*/metrics.json`.
- Data source: HugBor/servicenow_incidents_slm6 (commit
  `2344a8b8aec1bbeebbaffdd541a3bfd901af36c6`) + locally generated top-ups
  (local Qwen3.8-27B, llama.cpp). Zero cloud LLM traffic since feature 005.
- Features 001–005 are complete and measured. Feature 006
  (`specs/006-maxlen-ab/`) is **PARKED** — do not implement it; see
  `specs/BACKLOG.md#b0`.

## The next gate (start here)

The owner approved the problem statement for **`006-borderline-pairs`** and
its spec draft exists at `specs/006-borderline-pairs/spec.md`, awaiting the
owner's review. If the owner approves, write `plan.md` and `tasks.md` per
`specs/constitution.md` and the spec-kit templates, then stop at the review
gate.

## Non-negotiable rules (from constitution.md)

1. **Measurement discipline**: baseline before any change, written to a
   file; improvements only with non-overlapping intervals (3 seeds);
   gates are exit-code commands.
2. **Data hygiene**: 0 train/test overlap (id + normalized text); frozen
   test set is the current HugBor holdout; invalid labels are dropped, never
   guessed.
3. **Pinned versions**: no floating aliases; version change = re-baseline.
4. **Data privacy**: no cloud LLM traffic; the local teacher is the pinned
   Qwen gguf at 127.0.0.1:8080 (if offline: stop and report).
5. **MANUAL GATE tasks are the owner's** — an agent never checks them off.
6. **The recipe is sacred** (see 002 spec FR-004); changing it requires its
   own spec (the parked 006 is the example).

## Environment

Windows 11, Ryzen 5 7600X, 32 GB RAM, Radeon RX 7900 XT (no CUDA — training
is CPU-only by design). Setup: `pip install -r requirements.txt && pip
install -e .`, then `pytest -q` (39 tests green at handoff).

## How SDD works here

Problem statement (owner approves) → spec.md (owner reviews) → plan.md
(owner reviews) → tasks.md (test-first, MANUAL GATEs marked) →
implementation → measurement → owner SC-validation gate. Deferrals are
decisions too: they go to `specs/BACKLOG.md` with a restart condition.
