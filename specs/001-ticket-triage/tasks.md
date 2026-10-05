# Tasks: Ticket-triázs osztályozó

**Input**: Design documents from `/specs/001-ticket-triage/`

**Prerequisites**: plan.md (jóváhagyott), spec.md (jóváhagyott), constitution.md (jóváhagyott)

**Tests**: a spec FR-002 és FR-004 követelményei exit-code-os gate-eket írnak elő,
ezért a teszt-taskok KÖTELEZŐK, és a playbook teszt-előbb sorrendje érvényes.

**Organization**: US1 = tanár-címkék + kézi teszthalmaz (P1), US2 = helyi
kategorizálás (P2), US3 = perces újrataníthatóság (P3).

**Állapot-jelölés**: T001–T010 elkészültek az első iterációban; a T010
baseline-ja (12,0% ± 0,0) a minta zajos címkéit bizonyította — ez a spec
Background-ban dokumentált negatív eredmény. A T014-től a tanár-címkés út
következik.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup (Shared Infrastructure)

- [x] T001 Projektstruktúra létrehozása a plan.md szerint (`src/triage/`, `tests/`,
  `data/tidy/`, `runs/`), projekt-venv a gépen, pinnelt `requirements.txt`
  (torch CPU-wheel, transformers, polars, dpyr, pytest — pontos verziók, Constitution III)
- [x] T002 [P] `.gitignore` (runs/, data/, venv) és `src/triage/__init__.py` váz

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Tesztek ELŐSZÖR: `tests/unit/test_data.py` — a tidy-séma oszlopai
  (task, split, id, text, label), a stratifikált split aránya (800/200), a 0
  átfedés train/test között, az érvénytelen címke kihagyása. A teszteknek
  FAIL-ELNIük kell implementáció előtt (FR-001, FR-002)
- [x] T004 `src/triage/data.py` — tidy (dpyr: join a kategóriatáblával, text =
  summary + description) + stratifikált split (seed=0, rögzítve) +
  átfedés-ellenőrző, amely hiba esetén megállítja a futást. Kimenet:
  `data/tidy/*.parquet` (tutorial-séma) **és** a repó recipe-sémája:
  `data/tasks/tickets/` alá `task.json` (name/instruction/labels) +
  `train.jsonl` / `test.jsonl` (`{"id","text","label"}` soronként), hogy a
  repó `recipe/train.py`-ja változtatás nélkül fusson rajta. A `task.json`
  a mi feladatunkat írja le: `name: "servicenow_ticket_triage"`,
  `instruction: "Classify the IT support ticket by the team that should
  handle it."`, `labels`: a minta 8 kategóriája. T003 zöldre vált.

**Checkpoint**: Foundation ready — a tidy Parquet és a split létezik, ellenőrzött.

---

## Phase 3: User Story 1 - Kategóriázott ticket, helyben (Priority: P1) 🎯 MVP

**Goal**: ticketszöveg → kategória, helyben, mérhető pontossággal, exit-code-os gate-tel

**Independent Test**: `python -m triage eval --min-accuracy 0.90` exit code 0 a
fagyott teszthalmazon (SC-001, SC-002)

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T005 [P] [US1] `tests/unit/test_evaluate.py` — a metrika-írás formátuma
  (metrics.json: teljes + per-category pontosság), a küszöb alatti eredmény
  nem-nulla exit code-ja; `tests/integration/test_smoke.py` — 40 soros
  szeleten tidy→train(1 epoch)→eval end-to-end lefut

### Implementation for User Story 1

- [x] T006 [US1] `src/triage/train.py` — Ettin-17M full fine-tune CPU-n,
  **pontosan a repó receptje** (referencia: `recipe/train.py`): AdamW lr=1e-4,
  wd=0.01, batch=32, 5% warmup + cosine decay, gradient clipping 1.0,
  cross-entropy, maxlen=128, és **fix lépésszám az epoch-formulával**:
  `epochs = max(6, round(6 * 9493 / tanítósorok))` (800 sorra 71 epoch ≈
  1775 lépés, megegyezően a repó 2000-soros 28-epochos futásával). Minden
  paraméter a run `config.json`-jába (FR-003, FR-008)
- [x] T007 [US1] `src/triage/evaluate.py` — teljes + kategóriánkénti pontosság
  → `runs/<run>/metrics.json`, `--min-accuracy` exit-code gate (FR-004)
- [x] T008 [P] [US1] `src/triage/predict.py` — egyedi osztályozás + időmérés
  (SC-004: ≤ 100 ms/db), üres/rövid szöveg jelzése (spec Edge Cases)
- [x] T009 [US1] `src/triage/__main__.py` — CLI: `tidy | split | train | eval
  | predict` alparancsok egy belépésből
- [x] T010 [US1] **Baseline run**: tidy→train→eval **3 seeddel (0, 1, 2)** a
  800/200 spliten; a metrics.json az átlagot és a szórást is tartalmazza
  (a repó módszertana: "tables report means of 3 runs"; Constitution I
  zajmérés). Az eredmény `runs/baseline-*/metrics.json`-be íródik (FR-005,
  D4) — a további változtatások csak ezután, és ehhez viszonyítva; javulást
  csak nem-átfedő intervallumnál fogadunk el.

**Checkpoint**: US1 önállóan működik; a baseline fájl létezik.

---

## Phase 4: User Story 2 - Perces újrataníthatóság (Priority: P2)

**Goal**: a teljes folyamat egy paranccsal reprodukálható, időméréssel

**Independent Test**: újrafuttatás eltérő run-névvel; a run-napló
időbélyegeiből a teljes idő ≤ 15 perc (SC-003)

- [x] T011 [US2] Reprodukálhatósági végpontok: `python -m triage run --name
  <név>` végrehajtja a tidy→split→train→eval láncot, a konfigot és a
  mért időket a run-mappába írja; a baseline és az új run metrics.json-jei
  egymás mellé kerülnek a riportban (FR-008, SC-003)

**Checkpoint**: US1 és US2 is önállóan működik.

---

## Phase 6: Tanár-címkézés és új baseline (US1, a baseline-mérés nyomán)

**Goal**: megbízható címkék az 1000 sorra LLM-tanártól; kézzel ellenőrzött
fagyott teszthalmaz; új baseline a valós tartalom szerinti címkéken

**Independent Test**: `python -m triage label` lefut, SC-005 (≥99% érvényes);
a kézi teszthalmaz verziózott fájl; az új baseline mean_accuracy szignifikánsan
a 12%-os zaj-baseline fölött van (nem-átfedő intervallum)

- [x] T014 **[MANUÁLIS KAPU]** A felhasználó bejelentkezik a Kimi
  Code-fiókjával az lm15 mentett bejelentkezésébe (`lm15.login`). Agent nem
  pipálhatja — a hitelesítés a felhasználó interakciója.
- [x] T015 [US1] Tesztek ELŐSZÖR: `tests/unit/test_label.py` — a prompt
  tartalmazza az instrukciót és a 8 címkét; a válasz-illesztés csak pontos
  címkét fogad el (egyéb = None); a jsonl resumable (újrafuttatásnál nem
  címkéz újra). FAIL előbb. Majd `src/triage/label.py`: lm15 async címkézés,
  alacsony kezdő-throttle (start=4), 60 s timeout, retry exponential
  backoff-fal, `data/labels/teacher.jsonl` + `label_stats.json` (idő, tokenek,
  érvénytelen száma) (FR-008)
- [x] T016 [US1] Címkézés futtatása mind az 1000 soron a mentett
  bejelentkezéssel; SC-005 ellenőrzés (≥99% érvényes); a futás előtt a
  felhasználó jóváhagyása a kimenő forgalomra (FR-006 kivétel igazolva)
- [x] T017 **[MANUÁLIS KAPU]** A felhasználó kézzel átnéz ~200 tanár-címkézett
  sort (rétegzett minta: 25/kategória), javítja, ami rossz; az eredmény
  `data/labels/handchecked_test.jsonl` (fagyott, verziózott). Agent nem
  pipálhatja.
- [x] T018 [US1] `data.py` átdolgozás: a tidy most a tanár-címkéket használja;
  a teszthalmaz = a kézzel ellenőrzött fájl; a tanítóhalmaz = tanár-címkék
  mínusz a kézi teszt azonosítói; 0 átfedés mindkét irányban (FR-002, FR-009).
  A T003 tesztek frissítése az új szerződéshez (a zajos category-join kódút
  törlődik)
- [x] T019 [US1] **Új baseline**: 3 seed (0, 1, 2) a tanár-címkéken, eval a
  kézi teszthalmazon; `runs/baseline-teacher/metrics.json` (átlag ± szórás).
  Összevetés a 12%-os zaj-baseline-nal; javulás csak nem-átfedő
  intervallumnál fogadható el (Constitution I)

**Checkpoint**: valós tartalom szerinti, mért baseline létezik; az SC-001
gate innentől a kézi teszthalmazon fut.

---

## Phase 5: Polish & Cross-Cutting Concerns

- [x] T012 **[MANUÁLIS KAPU]** Teljes SC-validáció: a felhasználó lefuttatja
  `pytest -q` + `python -m triage eval --min-accuracy 0.85` (a kézi
  teszthalmazon) + a predict időmérést, és átnézi a tanár-címkés baseline
  metrics.json-t (SC-001…SC-005). Ezt agent NEM pipálhatja ki.
- [x] T013 [P] `README.md` — quickstart (venv, requirements, a CLI-parancsok
  beleértve a `label` lépést, gate-parancs), a repóban

---

## Dependencies & Execution Order

- **Phase 1 → 2 → 3 → 4 → 5** szigorúan sorban; a teszt-taskok (T003, T005)
  az implementációjuk (T004, T006–T009) ELŐTT, FAIL-elve. (Elkészült; a
  story-címkék [US1]/[US2] az eredeti számozást tükrözik: helyi
  kategorizálás / újrataníthatóság.)
- **Phase 6** (az új P1 story): T014 (MANUÁLIS KAPU) → T015 (teszt előbb) →
  T016 → T017 (MANUÁLIS KAPU) → T018 → T019 → vissza a T012-re.
- T001 → T002 [P] → T003 → T004 → T005 [P] → T006 → T007 → T008 [P] → T009 →
  T010 → T011 → [Phase 6] → T012 (MANUÁLIS KAPU) → T013 [P].
- [P] jelölés: külön fájl, nincs függőség — T002, T005, T008, T013
  párhuzamosítható a szomszédaikkal.
- T012 MANUÁLIS KAPU: az implementáció akkor sem "kész", amíg a felhasználó
  vissza nem igazolta.

## Validation Checklist

- [ ] Minden FR-hez (FR-001…FR-009) tartozik legalább egy task
- [ ] Minden SC (SC-001…SC-005) gate-parancsként futtatható
- [ ] A MANUÁLIS KAPU taskok explicit jelölve (T012, T014, T017)
- [ ] A zaj-baseline (T010, 12%) és a tanár-baseline (T019) is fájlban őrződik
- [ ] Kimenő adatforgalom csak a T016-ban, a felhasználó jóváhagyásával (FR-006 kivétel)
