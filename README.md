# tiny-incident-triage

ServiceNow-stílusú IT-ticketek kategorizálása egy 17M paraméteres, helyben
(CPU-n) futó osztályozóval. A tanítási recept a
[tiny-classifiers](https://github.com/MaximeRivest/tiny-classifiers) repóból
származik; az adat a
[mindweave/help-desk-tickets](https://huggingface.co/datasets/mindweave/help-desk-tickets)
ingyenes mintája (1000 ticket, 8 kategória).

Fejlesztési módszer: Spec-Driven Development — lásd `specs/constitution.md` és
`specs/001-ticket-triage/` (spec.md, plan.md, tasks.md).

## Quickstart

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt # pinnelt verziók, CPU torch

# adat: a mindweave minta letöltése data/raw/ alá (tickets.csv, categories.csv)
# FIGYELEM: a minta gyári címkéi zaj (baseline-mérés: 12% = véletlenszint),
# ezért a címkéket LLM-tanár gyártja:

python scripts/login_kimi.py                 # Kimi Code bejelentkezés (egyszeri)
python -m triage label                       # 1000 sor címkézése (resumable)
# -> data/labels/review_template.csv kézi átnézése, majd handchecked_test.jsonl

python -m triage tidy                        # tidy Parquet + recipe jsonl
python -m triage train --run runs/kiserlet-s0 --seed 0
python -m triage eval  --run runs/kiserlet-s0 --min-accuracy 0.85   # gate: exit 0/1
python -m triage predict --run runs/kiserlet-s0 "VPN client update failed with rollback error."
```

Egy lépésben (tidy → train → eval, időbélyeg-naplóval):

```bash
python -m triage run --name kiserlet --seed 0
```

Baseline (3 seed, átlag ± szórás):

```bash
python scripts/run_baseline.py   # runs/baseline/metrics.json
```

## Tesztek és gate-ek

```bash
pytest -q                                              # unit + smoke
python -m triage eval --run runs/kiserlet-s0 --min-accuracy 0.90   # SC-001 gate
```

## Elvek (rövidítve)

- Mérés-fegyelem: baseline előbb, fájlba; javulás csak nem-átfedő intervallumnál.
- Adathigiénia: train/test 0 átfedés, split seed=0 rögzítve, érvénytelen címke
  kihagyva (sosem találgatva).
- Minden verzió pinnelt (`requirements.txt`); a tanított modell: Ettin-17M
  (`jhu-clsp/ettin-encoder-17m`).
- A ticketszöveg nem hagyja el a gépet (Constitution IV).

A teljes elvsor: `specs/constitution.md`.
