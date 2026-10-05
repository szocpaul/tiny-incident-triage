# Feature Specification: Határeset-konvenciók javítása a tanítóhalmazban

**Feature Branch**: `003-borderline-conventions`

**Created**: 2026-10-05

**Status**: Draft

**Input**: User description: "A tanítóadat és a felhasználói szabályok között konvenció-konfliktus van a határeseteken: a tanár az MFA/jelszó/SSO-ügyeket tömegével az Access Managementhez sorolta, a felhasználó konvenciója szerint azonban ezek (egy része) a Securityhoz tartoznak; hasonlóan elmosódott a periféria↔endpoint határ. A modell így nem a háziszabályt tanulja. Szeretnénk, hogy a tanítóhalmaz határesetei a felhasználó konvencióját kövessék, és a javulás a fagyott teszthalmazon mérhető legyen."

## Background (diagnózis)

A 002-es mérés (`runs/002-boost/metrics.json`, 3 seed, fagyott teszt):

- Laptop / Endpoint: 91,3% → **97,1%** (a bővítés működött),
- Printers & Devices: 86,2% → 86,2% (mozdulatlan),
- **Security: 79,5% → 78,2%** (nem javult), összpontosság 94,0% (SC bukott).
- Diagnózis: a Security nem darabszám-, hanem **konvenció-probléma**. A
  felhasználó a T017-es review-ban az „MFA push nem érkezik" típusú sorokat
  Securitynak ítélte, míg a tanár a tanítóhalmazban ezeket Access
  Managementnek címkézte (158 soros erős konvenció). A 100 gyártott
  Security-sor nem tudta felülírni.
- Nyitott kérdés: a Printers & Devices mozdulatlanságának oka ismeretlen —
  az első lépés a **konfúziós mérés** (melyik kategóriával keveri), mert a
  javítás csak célzottan, a mért határvonalakon értelmes.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Konfúziós térkép (Priority: P1)

A felhasználó először pontosan látni akarja, hogy a modell hol téved: melyik
kategória melyikkel keveredik a fagyott teszten, soronként listázva.

**Why this priority**: A 002 tanulsága, hogy találgatással pótolt adat nem
javít (Security). A javítás csak a mért konfúziós párokra célozva értelmes.

**Independent Test**: egy parancs kiírja a konfúziós mátrixot és a tévesztett
sorok listáját (szöveg, helyes címke, jósolt címke).

**Acceptance Scenarios**:

1. **Given** a 002-es modell és a fagyott teszt, **When** fut a riport,
   **Then** minden tévesztett sor látszik a helyes és a jósolt címkével.

---

### User Story 2 - Határeset-átütemezés a felhasználó táblája szerint (Priority: P1)

A felhasználó egy explicit táblát kap a tanítóhalmaz határeset-jelöltjeiről
(kulcsszavas jelöltek, jelenlegi címke, javasolt címke), átnézi/javítja, és a
jóváhagyott tábla szerint íródnak át a címkék.

**Why this priority**: Ez a feature tényleges javítása; a konvenció a
felhasználóé, nem a tanáré.

**Independent Test**: az átcímkézés naplózott, visszafordítható (a 001/002-es
tanítóhalmaz érintetlen marad), és az átírt sorok száma pontosan a jóváhagyott
táblának felel meg.

**Acceptance Scenarios**:

1. **Given** a jelöltlista, **When** a felhasználó jóváhagyja (esetleg
   módosítva), **Then** csak a jóváhagyott sorok címkéje változik.
2. **Given** az átcímkézett tanítóhalmaz, **When** a split-ellenőrző fut,
   **Then** 0 átfedés a fagyott teszttel (id + szöveg), mint eddig.

---

### User Story 3 - Újramérés és ítélet (Priority: P1)

A javított tanítóhalmazon, változatlan recepttel, 3 seeddel újramért modell
eredménye a baseline-okhoz (zaj: 12%; teacher: 93,3%; boost: 94,0%)
viszonyítva, nem-átfedő intervallum-szabállyal.

**Acceptance Scenarios**:

1. **Given** az újramérés, **When** az SC-gate fut, **Then** a riport
   kategóriánként mutatja a három baseline-t és az új értéket.

### Edge Cases

- A határeset-átütemezés „oldalra billenti" a modellt (pl. most az Access
  Management romlik): az SC-003 védelem fogja.
- A jelöltlista túl agresszív (tényleges Access-ticketek is átcsúsznának):
  a felhasználó review-ja (MANUÁLIS KAPU) szűri.
- A konvenció belsőleg ellentmondásos (ugyanolyan szöveg két halmazban mást
  kapna): a review ezt is jelzi; a fagyott teszt konvenciója az irányadó.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Készüljön konfúziós riport: mátrix + tévesztett sorok listája
  (szöveg, helyes, jósolt), a 002-es modellen, a fagyott teszten.
- **FR-002**: A határeset-jelöltek kigyűjtése dokumentált, kulcsszavas
  szabállyal történjen (a szabály a riport része).
- **FR-003**: Az átcímkézés csak a felhasználó által jóváhagyott sorokon
  történhet (MANUÁLIS KAPU), új, verziózott tanítófájlba; az előző
  tanítóhalmazok érintetlenek maradnak (visszafordíthatóság).
- **FR-004**: A recept változatlan (mint a 002-ben); 3 seed (0, 1, 2); fagyott
  teszt változatlan.
- **FR-005**: A riport a 3 korábbi referenciához viszonyít (zaj / teacher /
  boost), nem-átfedő intervallum-ítélettel.

### Key Entities

- **Konfúziós pár**: (helyes címke, jósolt címke) gyakorisággal és sorlistával.
- **Határeset-jelölt**: tanítósor, amely kulcsszabály alapján másik
  kategóriába tartozhat; felhasználói döntés vár rá.
- **Átütemezett tanítóhalmaz**: a 002-es halmaz + a jóváhagyott címkeváltások;
  külön verziózott fájl.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Security ≥ 90% átlag (3 seed), minden seed ≥ 85%; Printers &
  Devices ≥ 90% átlag — a fagyott teszten.
- **SC-002**: Összpontosság ≥ 95% (3-seedes átlag), nem-átfedő intervallummal
  a 002-es 94,0% ± 0,5%-hoz képest.
- **SC-003 (védelem)**: a ≥96%-os kategóriák nem romlanak 2 pontnál többel;
  Laptop/Endpoint nem romlik a 002-es 97,1%-ról 2 pontnál többel.
- **SC-004**: a tévesztési riport létezik, és a javítás a mért konfúziós
  párokat célozta (a riportban nyomon követhető).

## Assumptions

- A fagyott teszthalmaz konvenciója (a felhasználó T017-es döntései) az
  irányadó; a tanár konvenciója felülírható.
- A konvenció-konfliktus lokalizált: az MFA/jelszó/SSO és a
  periféria/endpoint határvonalakra korlátozódik.
- Kimenő adatforgalom ebben a feature-ben nem kell (csak átcímkézés és
  tanítás) — ha mégis kellene, az külön jóváhagyás.

## Out of Scope

- Új szintetikus példák gyártása (a 002 eszköze; itt csak átcímkézés).
  *Újraindítási feltétel: ha az átütemezés után is darabszám-probléma mérhető.*
- Küszöbkalibráció / DSPy (kizárva, mint a 002-ben).
- A fagyott teszthalmaz módosítása. *Újraindítási feltétel: külön spec, ha a
  konvenció maga változik.*
