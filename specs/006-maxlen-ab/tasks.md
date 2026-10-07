# Tasks: maxlen A/B

**Input**: Design documents from `/specs/006-maxlen-ab/`

**Prerequisites**: plan.md, spec.md (approved); 005 artifacts frozen
(train_v6, holdout test, probe).

- [ ] T050 `train.py`: `maxlen` parameter (None = recipe default 128); unit
  test: config records the effective maxlen; tokenizer truncation uses it.
- [ ] T051 `scripts/run_maxlen_ab.py`: arm A (128) and arm B (256), 3 seeds
  each, eval on the frozen holdout + probe; arm B starts with a memory smoke
  step (documented failure, no silent fallback).
- [ ] T052 Comparison report: `runs/006-maxlen/report.json` — both arms,
  pre-registered verdict (SC-001) computed and recorded.
- [ ] T053 **[MANUAL GATE]** The owner reviews the report and accepts the
  verdict (adopt 256 / keep 128 / inconclusive). Agent may NOT check this off.

---

## Dependencies & Execution Order

- T050 → T051 → T052 → T053 (MANUAL GATE)
- Arm A and arm B run sequentially on the same machine (CPU).

## Validation Checklist

- [ ] FR-001/002/003→T051, FR-004→T052, SC-001 rule pre-registered (T052)
- [ ] MANUAL GATE: T053
- [ ] No outbound traffic; 005 artifacts untouched
