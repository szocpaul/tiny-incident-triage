# Backlog

Deferred ideas, with restart conditions. Each entry becomes its own spec when
activated (SDD: problem statement first).

## B1 - Confusion-driven fix for Cloud Services and Performance

The two weak categories of the 005 final model (Cloud Services 71.4%,
Performance 81.9% on the holdout) suffer from the documented taxonomy
borderline pairs (Application ↔ Cloud Services, Application ↔ Performance).
Plan: run the 003 playbook again — confusion report on the 005 model, then
targeted top-up / relabeling in the training data (local Qwen, zero cost).
Expected: +1–2 pp overall.
**Restart condition**: after the 006 maxlen A/B is decided (the maxlen choice
affects the training recipe used for the fix).

## B2 - Train-set duplicate-conflict cleanup

The frozen test set was cleaned in 004; the training set may contain
similar contradictory duplicates.
**Restart condition**: if the v2/new-baseline measurements suggest
train-side noise.

## B3 - Production ServiceNow integration

REST endpoint or Flow Designer step calling the local classifier from a
ServiceNow instance.
**Restart condition**: the owner requests productionization; gates of the
latest feature still green.

## B0 - maxlen A/B (128 vs 256) — PARKED

A full spec exists at `specs/006-maxlen-ab/` (approved spec+plan+tasks,
2026-10-07). Parked before implementation: the 005 evidence (94.55% achieved
with truncation; remaining errors are taxonomy-borderline, not
content-length issues) suggests truncation is not the main error source, and
B1 has a better cost/benefit.
**Restart condition**: after B1, if the borderline-pair errors prove to be
content-length related, or if the owner wants the numeric answer anyway.

If the 006 A/B (128 vs 256) shows a clear win for 256, evaluate 512 with the
same protocol (note the ~16x attention cost vs 128 on CPU).
**Restart condition**: 006 passes with non-overlapping improvement.
