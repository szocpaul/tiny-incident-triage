# Tasks: Határeset-konvenciók javítása

**Input**: Design documents from `/specs/003-borderline-conventions/`

**Prerequisites**: plan.md, spec.md (jóváhagyott); 002-es modell és baseline-ok
léteznek (`runs/baseline`, `runs/baseline-teacher`, `runs/002-boost`).

**Organization**: US1 = konfúziós térkép (P1), US2 = átütemezés (P1),
US3 = újramérés (P1).

## Phase 1: Konfúziós térkép (US1)

- [x] T027 Tesztek ELŐSZÖR: `tests/unit/test_confusion.py` — a riport sémája
  (mátrix, tévesztett sorok listája: id, text, helyes, jósolt), helyes
  számolás toy-adaton. FAIL előbb.
- [x] T028 [US1] `src/triage/confusion.py` + CLI (`python -m triage confusion
  --run runs/002-boost-s0`); riport → `runs/003-confusion/report.json`

## Phase 2: Határeset-átütemezés (US2)

- [x] T029 Tesztek ELŐSZÖR: `tests/unit/test_relabel.py` — a kulcsszabály
  jelöltjei a várt sorok; az átütemezés csak jóváhagyott sorokon dolgozik;
  a v3 fájl 0 átfedésű a teszttel (id + szöveg). FAIL előbb.
- [x] T030 [US2] `src/triage/relabel.py` — jelöltlista a konfúziós térképből
  vezetett szabállyal → `data/labels/relabel_review.csv`; az átütemező
  a jóváhagyott CSV-ből → `data/labels/train_v3.parquet` (001/002 érintetlen)
- [x] T031 **[MANUÁLIS KAPU]** A felhasználó soronként dönt a
  relabel_review.csv-n (áthelyez / marad). Agent NEM pipálhatja.

## Phase 3: Újramérés (US3)

- [x] T032 [US3] `scripts/run_relabel.py`: 3 seed, változatlan recept, fagyott
  teszt → `runs/003-relabel/metrics.json`, 4-oszlopos összevetés
  (zaj/teacher/boost/relabel), nem-átfedő intervallum-ítélet
- [x] T033 **[MANUÁLIS KAPU]** SC-validáció a felhasználó által: `pytest -q` +
  a riport átnézése (SC-001: Security és P&D ≥90% átlag; SC-002: össz ≥95%;
  SC-003: védelem; SC-004: a javítás a mért párokat célozta)

---

## Dependencies & Execution Order

- T027 → T028 → T029 → T030 → T031 (MANUÁLIS KAPU) → T032 → T033 (MANUÁLIS KAPU)
- A konfúziós térkép (T028) a jelöltszabály (T030) inputja.
- T032 csak jóváhagyott (T031) átütemezés után.

## Validation Checklist

- [ ] FR-001→T028, FR-002→T030, FR-003→T030/T031, FR-004→T032, FR-005→T032
- [ ] Minden SC gate-ként futtatható (T033)
- [ ] MANUÁLIS KAPU-k jelölve: T031, T033
- [ ] Nincs kimenő adatforgalom egyetlen taskban sem
- [ ] A korábbi baseline-fájlok és tanítóhalmazok érintetlenek
