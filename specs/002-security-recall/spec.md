# Feature Specification: Gyenge kategóriák erősítése (minden kategória ≥90%)

**Feature Branch**: `002-security-recall`

**Created**: 2026-10-05

**Status**: Draft

**Input**: User description: "A rendszer gyenge kategóriáinak felismerése a leggyengébb láncszem: a Security-ticketek kb. negyede (76,9%), a Printers & Devices kb. hetede (86,2%), a Laptop/Endpoint kb. nyolcada (87–91%) rossz csapathoz kerül; az összpontosság 92%. A cél: a gyenge kategóriák ≥90%-ra erősödjenek, az összpontosság ≥95% legyen — anélkül, hogy a már jó (96–100%) kategóriák romlanának."

## Background (diagnózis)

A 001-es feature tanár-címkés baseline-ja (`runs/baseline-teacher/metrics.json`,
3 seed, kézzel ellenőrzött 200 soros teszten):

- **Security: 79,5% átlag / 76,9% min** (n=26) — a leggyengébb kategória.
- **Printers & Devices: 86,2% átlag** (n=29) — a második gyenge láncszem.
- **Laptop / Endpoint: 91,3% átlag / 87,0% min** (n=23) — a harmadik gyenge.
- A többi öt kategória 96–100% között áll; az összpontosság 93,3% (3 seedes
  átlag; egyedi futáson 92,0%).
- A tanítóhalmaz-eloszlás: Security mindössze **47 sor** (5,9%), Printers &
  Devices 121 sor, Laptop / Endpoint 98 sor; a leggyakoribb kategória 185 sor.
- Ellenvetés: a Telephony 100%-ot ér el 10 tanítósorral is — tehát a kevés
  példa önmagában nem végzetes. A Security valószínűleg **a határesetekben**
  ütközik (MFA, jelszó, SSO → Access Management felé); a Printers & Devices és
  a Laptop/Endpoint az Endpoint–periféria határon. Az alulreprezentáltság és
  a szemantikai határ együtt játszik.
- A mérési keret adott: fagyott kézi teszthalmaz, 3-seedes futamok,
  nem-átfedő intervallum-szabály (Constitution I).

Ez diagnózis; a megoldási irány (új példák gyártása és címkézése) a plan.md-ben
landol. A küszöb-kalibrációs (ReAnchor-szerű) megoldást a felhasználó
explicit kizárta: a cél a modell javítása, nem a döntési küszöb igazítása.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A gyenge kategóriák felzárkózása (Priority: P1)

A felhasználó azt akarja, hogy a rendszer minden kategóriában megbízhatóan
osztályozzon: a gyenge hármas (Security, Printers & Devices, Laptop/Endpoint)
≥90% fölé kerüljön, az összpontosság ≥95% legyen — a fagyott teszthalmazon,
számszerűen igazolva.

**Why this priority**: Ez az egyetlen érték, amiért a feature létezik; minden
más (folyamat, eszköz) ennek az eszköze.

**Independent Test**: A megerősített modell minden kategóriájának pontossága a
fagyott, kézzel ellenőrzött teszthalmazon mérhető egyetlen gate-paranccsal, és
a baseline metrics.json-nal összevethető.

**Acceptance Scenarios**:

1. **Given** a megerősített modell, **When** lefut az eval-gate a fagyott
   teszthalmazon, **Then** minden kategória pontossága eléri a
   specifikált küszöböt (SC-001).
2. **Given** ugyanaz a mérés, **When** a többi kategóriát vizsgáljuk, **Then**
   egyik sem romlik szignifikánsan a baseline-hoz képest (SC-002).

---

### User Story 2 - Új gyenge-kategóriás példák ellenőrzött gyártása (Priority: P2)

A felhasználó további, Security-, Printers & Devices- és Laptop/Endpoint-témájú
ticket-példákat akar a tanítóhalmazba, megbízható címkékkel — és a gyártott
példákat egy rétegen át kézzel áttekinteni, mielőtt azok tanítóadattá válnak.

**Why this priority**: A diagnózis szerint az alulreprezentáltság a fő gyanúsított;
de a kézi review nélkül a gyártott adat ugyanolyan bizalom-problémát hozna,
mint amit a 001-ben a zajos mintánál láttunk.

**Independent Test**: az új példák külön fájlban állnak, a mintájuk
kézzel átnézve, és a tanítóhalmazba csak a jóváhagyás után kerülnek.

**Acceptance Scenarios**:

1. **Given** az új gyártott példák, **When** a felhasználó átnézi a mintájukat,
   **Then** a rossznak ítélt sorok nem kerülnek a tanítóhalmazba.
2. **Given** a bővített tanítóhalmaz, **When** a split-ellenőrző fut, **Then**
   továbbra is 0 átfedés áll a kézi teszthalmazzal (FR-009 öröklődik).

---

### Edge Cases

- A gyártott példák túl sablonosak (a tanár kliséit másolják): a kézi review
  szűri; a mérés a fagyott (nem gyártott) teszthalmazon történik, így a
  sablonosság nem hazudtolhatja meg az eredményt.
- A gyártott példák véletlenül átfednek egy tesztsorral: az átfedés-ellenőrző
  szövegazonosságot is vizsgál (nem csak id-t), hiba esetén a futás megáll.
- A bővítés más kategóriákat ront (pl. Access Management felé nő a zavár):
  az SC-002 gate pont ezt fogja meg.
- Az új példák a meglévő 8 kategórián kívüli témát hoznának: nem kerülnek be;
  a kategóriarendszer ebben a feature-ben fagyott.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Az új tanítópéldák azonos sémában készüljenek, mint a meglévő
  tanítóhalmaz (azonosító, szöveg, címke), és külön fájlban, verziózva álljanak.
- **FR-002**: Az új példák címkéje konstrukció szerint legyen konzisztens
  (a példa a címkéhez tartozó témából készül), és a tanítás előtt a
  felhasználó mintát átnéz (MANUÁLIS KAPU).
- **FR-003**: A bővített tanítóhalmaz és a fagyott teszthalmaz között 0
  átfedés — azonosítóra ÉS normalizált szövegre is ellenőrizve.
- **FR-004**: A tanítás a 001-ben rögzített, változatlan recepttel fusson
  (ugyanaz a modell, hiperparaméterek, epoch-formula); csak az adat változik.
- **FR-005**: A mérés a fagyott, kézzel ellenőrzött 200 soros teszthalmazon,
  3 seeddel (0, 1, 2) fusson, és a riport a `baseline-teacher` eredményéhez
  viszonyítson (átlag, szórás, kategóriánkénti bontás).
- **FR-006**: A javulás csak nem-átfedő intervallumokkal fogadható el
  (Constitution I) — a „valamivel jobb" nem eredmény.

### Key Entities

- **Gyártott példa**: LLM által írt, gyenge-kategóriás ticketszöveg; konstrukció
  szerinti címkével; verziózott fájlban.
- **Bővített tanítóhalmaz**: a 001-es tanítóhalmaz + a jóváhagyott gyártott
  példák.
- **Fagyott teszthalmaz**: változatlan (a 001-beli 200 sor); az összehasonlítás
  alapja.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001 (kategória-szint)**: a három gyenge kategória (Security, Printers &
  Devices, Laptop / Endpoint) 3-seedes átlaga ≥ 90% a fagyott teszthalmazon
  (baseline: 79,5% / 86,2% / 91,3%), ÉS mindegyikben minden seed ≥ 85% —
  nem-átfedő intervallummal igazolva. A riport a 95%-os stretch-célt is
  jelzi (nem gate).
- **SC-002 (összkép)**: az összpontosság 3-seedes átlaga ≥ 95% (baseline:
  93,3%), nem-átfedő intervallummal.
- **SC-003 (védelem)**: a jelenleg ≥96%-os kategóriák 3-seedes átlaga ≥ a
  baseline átlaga mínusz 2 százalékpont.
- **SC-004**: A tanítás+értékelés ≤ 15 perc/seed a helyi gépen (örökölt
  korlát), és a recept változatlan (FR-004 ellenőrzött).
- **SC-005**: A gyártott példákból a felhasználó által átnézett minta
  ≥ 90%-a találja a felhasználó helyesnek; a kiszórt arány naplózódik.

## Assumptions

- A 001-es fagyott teszthalmaz változatlan marad — az összehasonlíthatóság
  feláldozása nagyobb kár lenne, mint a teszthalmaz bővítésének haszna.
- A tanár-fiók (Kimi Code) továbbra is használható egyszeri, jóváhagyott
  adatgyártásra (a 001-beli FR-006 kivétel kiterjed a gyártásra is).
- A gyenge kategóriák határesetei a bővítés fókuszában állnak: Security
  (MFA/jelszó/SSO ↔ Access Management), Printers & Devices és Laptop/Endpoint
  (periféria ↔ Endpoint határ).

## Out of Scope

- Döntési küszöb kalibrálása, DSPy/ReAnchor-adapter (a felhasználó kizárta).
  *Újraindítási feltétel: külön spec, ha a modell-javítás kimerült.*
- A jelenleg ≥96%-os kategóriák további csiszolása. *Újraindítási feltétel:
  ha az SC-001 és SC-002 teljesül, és a felhasználó magasabb sávot tűz ki.*
- Új kategória bevezetése. *Újraindítási feltétel: külön spec, mert az a
  fagyott teszthalmazt is érintené.*
