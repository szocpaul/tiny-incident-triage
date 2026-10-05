# Tasks: Gyenge kategóriák erősítése

**Input**: Design documents from `/specs/002-security-recall/`

**Prerequisites**: plan.md (jóváhagyott), spec.md (jóváhagyott), a 001-es
feature kész (baseline-teacher metrics létezik: össz 93,3% ± 1,3%; gyengék:
Security 79,5%, P&D 86,2%, Laptop 91,3%)

**Tests**: teszt-előbb sorrend (playbook); a mérés-gate-ek exit-code-osak.

**Organization**: US1 = gyenge kategóriák felzárkózása (P1), US2 = ellenőrzött
gyártás (P2).

## Phase 1: Generálás (US2)

- [x] T020 Tesztek ELŐSZÖR: `tests/unit/test_generate.py` — az altéma-lista
  lefedi a 3 gyenge kategóriát; a dedup pontos és normalizált szövegre is
  szűr; a teszt-átfedés-ellenőrző dob, ha egy gyártott szöveg a fagyott
  tesztben szerepel; a gyártott sor sémája {id, text, label} és a label a
  konstruált kategória. FAIL előbb.
- [x] T021 [US2] `src/triage/generate.py` — altéma × osztály seedek, Kimi Code
  (lm15, mentett login, D1 patch örökölve), JSON-tömb válaszok, ~100 Security
  / ~60 P&D / ~40 Laptop sor; kimenet `data/labels/generated_v1.jsonl` +
  `generate_stats.json` (idő, tokenek, dedup-hulladék)
- [x] T022 [US2] Gyártás futtatása; dedup + teszt-átfedés-ellenőrző zöld;
  review-sablon: `data/labels/review_generated.csv` (rétegzett minta,
  ~50 sor, corrected_label oszlop)
- [x] T023 **[MANUÁLIS KAPU]** A felhasználó átnézi a review_generated.csv-t,
  javítja/kiszórja a rosszakat (SC-005: ≥90% helyes). Agent NEM pipálhatja.

## Phase 2: Bővített tanítás és mérés (US1)

- [x] T024 [US1] `data.py`: a tanítóhalmaz = 001-es tanítóhalmaz + jóváhagyott
  gyártott példák; a teszt változatlan (fagyott); a merge után
  átfedés-ellenőrző (id + normalizált szöveg); a T018 tesztek zöldek maradnak
- [x] T025 [US1] 3-seedes újramérés: `scripts/run_boost.py` (a
  run_baseline.py mintájára) → `runs/002-boost/metrics.json`; riport:
  baseline-teacher vs 002-boost, kategóriánként, átlag ± szórás,
  nem-átfedő intervallum-ítélettel
- [x] T026 **[MANUÁLIS KAPU]** Teljes SC-validáció: a felhasználó lefuttatja
  `pytest -q` + a 002-es eval-gate-et, és a riportot átnézi: SC-001
  (gyengék ≥90% átlag, seedenként ≥85%), SC-002 (össz ≥95%), SC-003
  (jó kategóriák nem romlottak 2 pontnál többel), SC-004 (recept változatlan,
  ≤15 perc/seed), SC-005 (review-arány). Agent NEM pipálhatja.

---

## Dependencies & Execution Order

- T020 → T021 → T022 → T023 (MANUÁLIS KAPU) → T024 → T025 → T026 (MANUÁLIS KAPU)
- T020 tesztjei FAIL előbb, T021 zöldíti.
- A T024 csak jóváhagyott (T023) példákkal dolgozik.

## Validation Checklist

- [ ] Minden FR (FR-001…FR-006) lefedve: FR-001/002→T021/T022, FR-003→T020/T024,
  FR-004→T025, FR-005→T025, FR-006→T025/T026
- [ ] Minden SC gate-ként futtatható (T026)
- [ ] MANUÁLIS KAPU-k jelölve: T023, T026
- [ ] Kimenő adatforgalom csak T021-ben, a jóváhagyott fiókkal (spec FR-006
  kivétel)
- [ ] A baseline-teacher metrics változatlanul megmarad (összehasonlítás)
