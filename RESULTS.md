# Results

All measurements: 3 seeds (0, 1, 2), frozen hand-checked test set,
CPU-only (Ryzen 5 7600X), the unchanged tiny-classifiers recipe throughout.

## Headline table (overall accuracy)

| run | mean | stdev | per-seed (0/1/2) | notes |
|---|---|---|---|---|
| `baseline` (the sample's stock labels) | **12.00%** | ±0.00 | 12.0 / 12.0 / 12.0 | chance level (1/8) — the stock labels are noise |
| `baseline-teacher` (Kimi K3 labels) | **93.33%** | ±1.26 | 92.0 / 94.5 / 93.5 | teacher labeling on Kimi Code subscription, $0 |
| `002-boost` (+460 generated tickets) | **94.00%** | ±0.50 | 94.0 / 93.5 / 94.5 | Laptop/Endpoint improved; Security did not |
| `003-relabel` (105 relabeled borderlines) | **97.33%** | ±0.29 | 97.0 / 97.5 / 97.5 | Security fixed; Laptop dipped (fixed in v4) |
| `003-relabel-v4` (final) | **98.17%** | ±0.58 | 97.5 / 98.5 / 98.5 | every category 96–100% |
| `004-testset-v2` (same model, cleaned test) | **99.48%** | — | single eval (n=193) | frozen test cleaned of contradictory duplicates |

Raw data: `runs/*/metrics.json` (versioned in this repo).

## Final model, per category (003-relabel-v4, 3-seed mean / min)

| category | mean | worst seed | test rows |
|---|---|---|---|
| Access Management | 100.0% | 100.0% | 24 |
| ERP / WMS | 100.0% | 100.0% | 25 |
| Printers & Devices | 100.0% | 100.0% | 29 |
| Telephony | 100.0% | 100.0% | 23 |
| Laptop / Endpoint | 97.1% | 91.3% | 23 |
| Security | 96.2% | 96.2% | 26 |
| Email & Collaboration | 96.0% | 96.0% | 25 |
| Network & VPN | 96.0% | 96.0% | 25 |

On the cleaned v2 test set: all categories 100%, except Security 95.7% (the
one remaining error is a genuine borderline: "Excel add-in blocked by security
policy").

## Comparison with the original repository

| | tiny-classifiers (AG News tutorial) | this project |
|---|---|---|
| task | AG News, 4 topics, real news | ServiceNow tickets, 8 categories, synthetic |
| train set | 2,000 rows | 997 rows |
| training (CPU) | ~11 min (laptop) | ~4.4 min/seed (Ryzen 7600X) |
| inference (CPU) | ~6 ms/message | **3.7 ms/ticket** |
| accuracy (human labels) | 89.2% | — |
| accuracy (Kimi K3 teacher labels) | 85.1% | **98.2% (v1) / 99.5% (v2)** |
| labeling cost | ~$1 (Kimi K3 on Fireworks) | **$0** (Kimi Code subscription) |

**Honest caveats:**

1. Task difficulty is not comparable: our synthetic tickets are templated and
   keyword-rich — an easier task than AG News. The 98–99% does not mean we
   "beat" the repo; it means the method works excellently in this domain.
2. The recipe was used **unmodified** ("nothing is tuned per task" held true).
3. The student beat its own teacher here (teacher ~96.5% on the review sample)
   because the owner's hand corrections aligned both the training data and the
   test conventions to the house rules — "human labels break that ceiling",
   literally.
4. What this repo adds over the original: an auditable SDD process —
   exit-code gates, 3-seed noise measurement, confusion-driven fixes, and a
   versioned hand-checked test set.

## Measurement hygiene

- Every number above comes from `runs/*/metrics.json`, committed to this repo.
- Baselines are measured before changes; improvements accepted only with
  non-overlapping intervals (3 seeds).
- Train/test overlap is 0, verified on every run (by id and normalized text).
- The frozen test set was versioned (v1 archived, v2 current) with a full
  changelog; the v1 numbers remain valid in their own context.

## Feature 005: full HugBor adoption (new 14-category taxonomy)

After 004, the project switched data sources and taxonomy (owner decision):
the HugBor/servicenow_incidents_slm6 dataset (1,640 realistic incidents)
replaced the mindweave-derived data; Software was merged into Application
after the label-trust spot-check showed the pair is inherently ambiguous
(local Qwen blind agreement: 85.3% → 88.6% after the merge; the remaining
borderline pairs are documented and accepted).

| run | overall | probe (8 wild incidents) | notes |
|---|---|---|---|
| `005-hugbor` (v5: HugBor + 325 generated top-up rows) | 95.25% ± 0.46 | 6/8, 5/8, 5/8 | SC-004 failed (strict gate) — monitoring-style data didn't cover the end-user voice |
| `005-uservoice` (v6: + 210 user-voice rows) | **94.55% ± 1.32** | **7/8, 7/8, 7/8** | all gates pass; tiny frozen-test dip (within noise), large robustness gain |

Per-category (v6): 10/14 categories ≥ 92%; the weak pair (Cloud Services
71.4%, Performance 81.9%) matches the documented taxonomy borderlines.
Everything was produced locally: the teacher was a local Qwen3.8-27B
(llama.cpp) — zero cloud LLM traffic, $0.
