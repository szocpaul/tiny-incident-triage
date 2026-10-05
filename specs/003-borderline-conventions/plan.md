# Implementation Plan: Határeset-konvenciók javítása

**Branch**: `003-borderline-conventions` | **Date**: 2026-10-05 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/003-borderline-conventions/spec.md`

## Summary

Először konfúziós térkép a 002-es modellen (melyik kategória melyikkel
keveredik, soronként), aztán kulcsszavas határeset-jelöltek a tanítóhalmazból,
felhasználói jóváhagyás (MANUÁLIS KAPU), célzott átcímkézés verziózott új
fájlba, végül változatlan recepttel 3-seedes újramérés a fagyott teszten —
mindhárom korábbi baseline-hoz viszonyítva.

## Technical Context

A 001/002-es stack és recept változatlan. Új modulok: `src/triage/confusion.py`
(konfúziós riport), `src/triage/relabel.py` (jelöltek + átütemezés). Nincs
kimenő adatforgalom.

## Key Decisions

### D1: Mérés előbb, javítás utána

**Döntés**: az első artifact a konfúziós riport (`runs/002-boost-s0`-on,
fagyott teszten): mátrix + minden tévesztett sor (szöveg, helyes, jósolt).

**Indoklás**: a 002 azt mutatta, hogy a „jó megérzésű" pótlás (100 Security
sor) nem mozdította a Securityt — a javításnak a mért párokat kell célznia
(SC-004). A riport megmondja, a Security tényleg Access Management felé szór-e,
és a P&D mivel keveredik.

**Elvetett alternatíva**: azonnali átcímkézés a feltételezett határvonalakon —
találgatás; pont ez bukott meg a 002-ben.

### D2: Kulcsszavas jelöltek + felhasználói tábla

**Döntés**: a tanítóhalmazban kulcsszabály gyűjti a jelölteket
(MFA|password|SSO|Okta|login|webcam|dock|monitor|printer|scanner…), minden
jelölthöz: id, szöveg, jelenlegi címke, javasolt címke (a konfúziós térképből
származó szabállyal). A felhasználó soronként dönt (áthelyez / marad),
CSV-ben; csak a jóváhagyott sorok íródnak át.

**Indoklás**: a konvenció a felhasználó tulajdona; a kulcsszabály csak
jelölt, nem döntés (a 002 tanulság: az automatikus „javítás" rejthet hibát).

**Elvetett alternatíva**: automatikus átcímkézés kulcsszó alapján — gyors,
de a spec Edge Cases szerint a túl agresszív szabályt az ember szűri.

### D3: Verziózott átütemezés, érintetlen előzmények

**Döntés**: az átcímkézett halmaz új fájl (`data/labels/train_v3.parquet`);
a 001/002-es fájlok érintetlenek. A visszafordítás = régi fájl.

**Indoklás**: Constitution II + a baseline-ok összehasonlíthatósága.

### D4: Újramérés ugyanazzal a harness-szel

**Döntés**: `scripts/run_relabel.py` = a run_boost.py mintája, de a v3
tanítóhalmazon; riport: 4 oszlop (zaj / teacher / boost / relabel),
kategóriánként, nem-átfedő intervallum-ítélettel.

## Architektúra (ASCII)

```text
runs/002-boost-s0/model + fagyott teszt (200 sor)
        |
        v
[confusion]  mátrix + tévesztett sorok ----> runs/003-confusion/report.json
        |                                    (SC-004: a javítás ezeket célozza)
        v
[candidates] kulcsszabály a tanítóhalmazon -> data/labels/relabel_review.csv
        |                                    (id, text, mostani, javasolt)
        v
[review] felhasználó soronként (MANUÁLIS KAPU)
        |
        v
[relabel] csak a jóváhagyott sorok --------> data/labels/train_v3.parquet
        |                                    (001/002 fájlok érintetlenek)
        v
[train+eval] változatlan recept, seed 0/1/2 -> runs/003-relabel/metrics.json
        riport: zaj 12% | teacher 93,3% | boost 94,0% | relabel ?
```

## Constitution Check

| Elv | Ellenőrzés | Eredmény |
|-----|-----------|----------|
| I. Mérés-fegyelem | 3 korábbi baseline fájlban; 3 seed; nem-átfedő intervallum (SC-002) | PASS |
| II. Adathigiénia | fagyott teszt változatlan; 0 átfedés a v3-ban is; érintetlen előzmények (D3) | PASS |
| III. Verzió-pinnelés | stack/recept változatlan | PASS |
| IV. Adatvédelem | nincs kimenő forgalom ebben a feature-ben | PASS |
| V. Egyszerűség | két új vékony modul; nincs új külső függőség | PASS |

## Project Structure

```text
src/triage/
├── confusion.py   # ÚJ: konfúziós riport (FR-001)
└── relabel.py     # ÚJ: jelöltek + átütemezés (FR-002, FR-003)

tests/unit/
├── test_confusion.py  # ÚJ
└── test_relabel.py    # ÚJ

scripts/run_relabel.py  # ÚJ: 3-seedes újramérés v3-on
```

## Complexity Tracking

Nincs constitution-sértés — a táblázat üres.
