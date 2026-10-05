# tiny-incident-triage

Classifying ServiceNow-style IT tickets with a 17M-parameter classifier that
runs locally (CPU). The training recipe comes from
[tiny-classifiers](https://github.com/MaximeRivest/tiny-classifiers); the data
is the free sample of
[mindweave/help-desk-tickets](https://huggingface.co/datasets/mindweave/help-desk-tickets)
(1,000 tickets, 8 categories) — relabeled by an LLM teacher because the
sample's original labels turned out to be noise (measured: 12% = chance level).

Development method: Spec-Driven Development — see `specs/constitution.md` and
`specs/001..004` (spec.md, plan.md, tasks.md per feature).

**Headline result: 99.5% accuracy** on the cleaned, hand-checked test set
(98.2% on the original frozen set), 3.7 ms/ticket on CPU, $0 labeling cost
(the teacher ran on the owner's Kimi Code subscription). Full numbers:
[RESULTS.md](RESULTS.md).

## Quickstart

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt # pinned versions, CPU torch
pip install -e .                # installs the triage package (python -m triage)

# data: download the mindweave sample into data/raw/ (tickets.csv, categories.csv)
# NOTE: the sample's stock labels are noise (measured: 12% = chance), so
# labels are produced by an LLM teacher:

python scripts/login_kimi.py                 # Kimi Code sign-in (one-off)
python -m triage label                       # label 1,000 rows (resumable)
# -> review data/labels/review_template.csv by hand, freeze handchecked_test.jsonl

python -m triage tidy                        # tidy Parquet + recipe jsonl
python -m triage train --run runs/experiment-s0 --seed 0
python -m triage eval  --run runs/experiment-s0 --min-accuracy 0.85   # gate: exit 0/1
python -m triage predict --run runs/experiment-s0 "VPN client update failed with rollback error."
```

Everything in one step (tidy → train → eval, with timestamped run log):

```bash
python -m triage run --name experiment --seed 0
```

Baselines (3 seeds, mean ± stdev):

```bash
python scripts/run_baseline.py    # runs/baseline-teacher/metrics.json
```

## Tests and gates

```bash
pytest -q                                              # unit + smoke
python -m triage eval --run runs/experiment-s0 --min-accuracy 0.85   # SC-001 gate
python -m triage testconflicts --exit-code            # test-set conflict gate
```

## Principles (short version)

- Measurement discipline: baseline first, written to a file; improvement only
  counts with non-overlapping intervals (3 seeds).
- Data hygiene: 0 train/test overlap, fixed split seed, invalid labels dropped
  (never guessed).
- Everything pinned (`requirements.txt`); the trained model is Ettin-17M
  (`jhu-clsp/ettin-encoder-17m`).
- Ticket text never leaves the machine, except the one-off, owner-approved
  teacher labeling (see Constitution IV).

The full principle list: `specs/constitution.md`.
