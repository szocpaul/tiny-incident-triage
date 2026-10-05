# Implementation Plan: Gyenge kategóriák erősítése

**Branch**: `002-security-recall` | **Date**: 2026-10-05 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-security-recall/spec.md`

## Summary

A gyenge kategóriákhoz (Security, Printers & Devices, Laptop / Endpoint) a
tanárral célzott, altémázott szintetikus ticketeket gyártunk (~200 új sor),
a felhasználó mintát kézzel átnézi (MANUÁLIS KAPU), a bővített tanítóhalmazon
a **változatlan recepttel** újratanítunk (3 seed), és a fagyott kézi
teszthalmazon mérünk — a 001-es baseline-hoz viszonyítva, nem-átfedő
intervallum-szabállyal.

## Technical Context

A 001-es stack változatlan (Python 3.12, torch CPU, transformers, dpyr/polars,
lm15, mind pinnelve). Új elem: egy generáló lépés ugyanazzal a mentett
Kimi Code-bejelentkezéssel (a spec FR-006-kivétele kiterjed a gyártásra).

**Új modul**: `src/triage/generate.py` — altémázott, seeded szintetikus
ticketgyártás + dedup + teszt-átfedés-ellenőrző.

## Key Decisions

### D1: Gyártás altémára bontva, „konstrukció szerinti címke"

**Döntés**: nem szabad szöveget kérünk, hanem **(kategória, altéma) párokon**
iterálunk: minden generált sor eleve a célzott kategóriához készül, tehát a
címke konstrukció szerint helyes; a tanártól csak a szöveg jön.

Altémák (a baseline-diagnózis határvonalai mentén):

- **Security** (~100 sor): gyanús belépés/impossible travel, phishing-gyanú,
  BitLocker/recovery key, vírusirtó-riasztás, jogosulatlan eszköz,
  **határeset**: MFA/jelszó/SSO-incidensek biztonsági szögből
  (pl. „MFA fatigue attack gyanúja").
- **Printers & Devices** (~60 sor): nyomtató offline/jam, scanner,
  címkenyomtató, **határeset**: docking/periféria, amely nem a laptop hibája.
- **Laptop / Endpoint** (~40 sor): webcam, lassulás, tárhely, képernyő,
  **határeset**: dokkoló és beépített periféria az eszköz hibájaként.

**Indoklás**: a 001 tanulsága, hogy a címke-zaj a legnagyobb kockázat; ha a
címke a generálás inputja (nem outputja), a zajforrás kikapcsolódik. A kézi
review (SC-005) a maradék minőségi kockázatot fogja.

**Elvetett alternatíva**: szabadon generált ticketek utólagos tanár-címkézése
— felesleges kör, és visszahozná a címkehibát.

### D2: Változatosság szisztematikusan

**Döntés**: altéma × osztály (Finance, HR, Sales, Operations, Warehouse…) ×
hangnem rövidített seed-lista; minden kérés N különböző ticketet ad vissza
JSON-tömbben; utólagos dedup (pontos + normalizált szöveg) és
**teszt-átfedés-ellenőrző** (FR-003).

**Indoklás**: 200 sablonmásolat értéktelen; a kézi teszttel való szöveges
átfedés pedig a mérést hazudítaná meg.

**Elvetett alternatíva**: egyszerű „írj 100 security ticketet" prompt —
kliséhalmazt adna.

### D3: A recept szent (FR-004)

**Döntés**: modell, hiperparaméterek, epoch-formula, seed-ek (0/1/2) mind
változatlanok; kizárólag a tanítóhalmaz bővül. Az új futamok
`runs/002-boost-s{0,1,2}` alá kerülnek, a riport a `baseline-teacher`-hez
viszonyít.

**Indoklás**: így a javulás egyetlen okra (az adatra) vezethető vissza.

**Elvetett alternatíva**: epoch/hiperparaméter-finomítás ugyanabban a körben
— keverednék az okok; ha az adatbővítés nem elég, az külön, mérhető lépés.

### D4: A fagyott teszthalmaz változatlan

**Döntés**: a 200 soros kézi teszt marad; az új példák csak a tanítóhalmazba
mennek. A teszt-átfedés-ellenőrző szövegazonosságot is vizsgál.

**Indoklás**: összehasonlíthatóság (spec Assumptions); a mérés érvényessége
fontosabb, mint a teszthalmaz bővítése.

## Architektúra (ASCII)

```text
altéma-lista (D1) × osztály/hangnem seedek
        |
        v
[generate] Kimi Code (lm15), JSON-tömb válaszok   data/labels/generated_v1.jsonl
        |                                          + generate_stats.json
        v
[dedup]  pontos + normalizált szöveg-dedup,
         teszt-átfedés-ellenőrző (hiba = megáll)  (FR-003)
        |
        v
[review] felhasználó átnéz ~50 sort (MANUÁLIS KAPU, SC-005)
        |
        v
[train]  001-es tanítóhalmaz + jóváhagyott példák
         változatlan recept, seed 0/1/2            runs/002-boost-s*/
        |
        v
[eval]   fagyott kézi teszt (200 sor)             runs/002-boost/metrics.json
         riport: baseline-teacher vs 002-boost
         (átlag ± szórás, nem-átfedő intervallum, SC-001…SC-005 gate-ek)
```

## Constitution Check

| Elv | Ellenőrzés | Eredmény |
|-----|-----------|----------|
| I. Mérés-fegyelem | baseline-teacher létezik; 3 seed; nem-átfedő intervallum (SC-001/002); gate exit-code-os | PASS |
| II. Adathigiénia | fagyott teszt változatlan (D4); 0 átfedés id+szöveg szerint (FR-003); konstrukció szerinti címke (D1) | PASS |
| III. Verzió-pinnelés | stack és modell változatlan | PASS |
| IV. Adatvédelem | kimenő forgalom = a jóváhagyott Kimi Code-fiók, most generálásra (spec FR-006 kivétel kiterjesztve) | PASS |
| V. Egyszerűség | recept szent (D3); nincs kalibráció/DSPy (spec Out of Scope) | PASS |

## Project Structure

Új/módosuló fájlok a 001-es struktúrán belül:

```text
src/triage/
├── generate.py          # ÚJ: altémázott gyártás + dedup + átfedés-ellenőrző
└── data.py              # bővített tanítóhalmaz összeállítása (generated merge)

tests/
└── unit/test_generate.py   # ÚJ: dedup, átfedés-ellenőrző, séma-tesztek

data/labels/
├── generated_v1.jsonl      # ÚJ: gyártott példák (verziózott)
└── review_generated.csv    # ÚJ: kézi review-sablon a gyártott mintára
```

## Complexity Tracking

Nincs constitution-sértés — a táblázat üres.
