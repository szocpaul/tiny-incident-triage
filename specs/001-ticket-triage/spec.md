# Feature Specification: Ticket-triázs osztályozó

**Feature Branch**: `001-ticket-triage`

**Created**: 2026-10-05

**Status**: Draft

**Input**: User description: "A beérkező IT support-ticketek kategorizálása és a megfelelő kezelőcsapathoz irányítása ma kézi munka: lassú, drága és inkonzisztens. Szeretnénk, hogy minden új ticket azonnal, egyenletes minőségben megkapja a helyes kategóriát — anélkül, hogy a ticketszöveg elhagyná a saját környezetünket, és állandó API-költség nélkül."

## Background (diagnózis)

- A célzott felhasználási terület (ITSM ticket-triázs) nyilvános, valódi
  adathalmazokkal nem rendelkezik — a céges ticketek érzékenyek. A rendelkezésre
  álló eszköz egy 1000 soros, kategóriacímkézett szintetikus ticket-minta
  (8 kategória, kiegyensúlyozott).
- A kézi triázs költsége és inkonzisztenciája ismert probléma; a piaci
  megoldások (ITSM-eszközök beépített AI-ja, LLM API-k) vagy drágák, vagy a
  ticketszöveget külső szolgáltatóhoz küldik.
- **Mérési megállapítás (2026-10-05, baseline-run):** a minta címkéi
  függetlenek a szövegtartalomtól — a szintetikus generátor a szöveget és a
  címkét külön sorsolta. Bizonyíték: 3-seedes baseline 12,0% ± 0,0 pontosság
  (véletlenszint, 1/8) 99,9%-os tanító-pontosság mellett. A szövegek jók,
  a címkék zaj — ezért a tanítócímkéket egy nagy nyelvi modell (tanár) gyártja,
  és az értékelés referenciája a felhasználó által kézzel ellenőrzött
  teszthalmaz lesz.
- Ez a diagnózis; a megoldási irányok (modellméret, tanítási módszer,
  címkézési stratégia) a plan.md-ben landolnak.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Tanár-címkék és kézzel ellenőrzött teszthalmaz (Priority: P1)

A felhasználó a címkézetlen ticketszövegeket egy általa jóváhagyott nagy
nyelvi modellfiókkal címkézteti le, és az eredményből egy részhalmazt kézzel
átnéz — ez a kézzel ellenőrzött halmaz lesz a fagyott tesztreferencia.

**Why this priority**: A baseline-mérés bizonyította, hogy a forrásadat címkéi
zaj; megbízható címke nélkül nincs mit tanítani és nincs mihez mérni. Ez a
story minden másnak az előfeltétele.

**Independent Test**: A címkézés egy parancsként fut, érvényes címkét ad a
sorok ≥99%-ára, költség- és időnaplóval; a kézzel ellenőrzött teszthalmaz
külön, verziózott fájlban áll, amit a tanítás sosem lát.

**Acceptance Scenarios**:

1. **Given** 1000 címkézetlen ticketszöveg, **When** lefut a címkéző parancs,
   **Then** minden sor címkét kap a 8 kategória egyikéből (érvénytelen =
   kihagyva, naplózva), és a futás költség/idő-statisztikája fájlba íródik.
2. **Given** a felhasználó kézzel átnézett ~200 sort, **When** a teszthalmaz
   fagyasztásra kerül, **Then** az külön fájlban, verziózva áll, és a
   tanítófolyamat hibát dob, ha abba a halmazba tanítósor kerülne.

---

### User Story 2 - Kategóriázott ticket, helyben (Priority: P2)

A felhasználó egy ticketszöveget (cím + leírás) ad a rendszernek, és azonnal,
helyben kapja meg a legvalószínűbb kezelőkategóriát — külső szolgáltatás és
API-költség nélkül.

**Why this priority**: Ez a feature egész értéke: ha a kategorizálás nem
működik megbízhatóan és helyben, a többi részeredmény önmagában nem szállít
értéket.

**Independent Test**: A rendszer egy fagyott, a tanítástól független
teszthalmazon mért pontossága egy parancs futtatásával ellenőrizhető, és a
parancs exit code-ja jelzi, hogy a küszöb teljesül-e.

**Acceptance Scenarios**:

1. **Given** egy tanított osztályozó és a fagyott teszthalmaz, **When** fut az
   értékelő parancs, **Then** a teljes pontosság eléri a specifikált küszöböt,
   és a parancs 0 exit code-dal tér vissza.
2. **Given** egy új, korábban nem látott ticketszöveg, **When** a rendszer
   osztályozza, **Then** a válasz a 8 kategória valamelyike, és az eredmény
   másodperc alatt megérkezik a helyi gépen.

---

### User Story 3 - Perces újrataníthatóság (Priority: P3)

Ha a kategóriarendszer vagy a ticketmix változik, a felhasználó új adattal
percek alatt újratanítja a rendszert, és azonnal látja az új mérést — nincs
heti projekt, nincs külső függőség.

**Why this priority**: Az üzleti kategóriák változnak; a gyors újratanítás az,
ami a rendszert hosszú távon élővé teszi. De az első értéket a P1–P2 hozza.

**Independent Test**: A teljes folyamat (adat → tanított modell → mérés) egy
parancs újrafuttatásával reprodukálható, és a végpontok közötti idő mérhető.

**Acceptance Scenarios**:

1. **Given** egy módosított tanítóhalmaz, **When** a felhasználó újrafuttatja
   a folyamatot, **Then** a tanítás és értékelés a specifikált időkorláton
   belül lefut a helyi gépen, és az új mérés a korábbi mellé kerül a mérési
   naplóba.

---

### Edge Cases

- Érvénytelen vagy hiányzó címke a tanítóadatban: a sor kimarad a tanításból,
  és a kimaradás naplózódik (sosem találgatás).
- Üres vagy szélsőségesen rövid ticketszöveg: a rendszer jelzi, hogy a bemenet
  nem osztályozható megbízhatóan, ahelyett hogy magabiztosan rosszat mondana.
- Szélsőségesen hosszú ticketszöveg: a csonkolási szabály dokumentált és a
  mérés ezzel a szabállyal készül.
- A teszthalmazba véletlenül tanítósor kerül: a split ellenőrző lépés ezt 0
  átfedéssel igazolja, hiba esetén a futás megáll.
- Nem-angol ticketszöveg: a jelenlegi adat angol; az egyéb nyelvek viselkedése
  nem specifikált (lásd Out of Scope).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A rendszernek egységes, dokumentált séma szerinti adattáblát
  kell készítenie a forrásadatokból (azonosító, szöveg, címke, split).
- **FR-002**: A tanító/teszt felosztásnak rögzített seed-del, reprodukálhatónak
  kell lennie, és a futás elején 0 átfedést kell igazolnia a két halmaz között.
- **FR-003**: A rendszernek a tanítóhalmazról helyben, a fejlesztői gépen
  kell betanítania az osztályozót.
- **FR-004**: Az értékelés egy parancsként futtatható legyen, amely a teljes
  és kategóriánkénti pontosságot fájlba írja, és küszöbalapú exit code-dal
  tér vissza.
- **FR-005**: Minden mérés baseline-nal indul: az első értékelés eredménye
  fájlba íródik a bármely további változtatás előtt.
- **FR-006**: A ticketszöveg alapértelmezetten nem hagyhatja el a gépet.
  **Kivétel (a felhasználó 2026-10-05-ön jóváhagyta):** az 1000 ticketszöveg
  egyszeri címkézésre kimehet a felhasználó saját, jóváhagyott
  LLM-fiókján keresztül. Minden más kimenő forgalom továbbra is tiltott.
- **FR-007**: Minden futtatás konfigurációja (seed-ek, verziók, paraméterek)
  a futással együtt mentődik, hogy az eredmény reprodukálható legyen.
- **FR-008**: A tanár-címkézés egy parancsként, megszakítás után folytathatóan
  fusson; érvénytelen válasz = kihagyás + naplózás (sosem találgatás); a
  futás idő- és költségstatisztikát ír.
- **FR-009**: A kézzel ellenőrzött teszthalmaz külön, verziózott fájlban áll;
  a tanítófolyamat hibát dob, ha tanítósor kerülne bele (0 átfedés a
  tanító- és a kézi teszthalmaz között is).

### Key Entities

- **Ticket**: az osztályozandó egység; azonosító, cím, leírás.
- **Kategória**: a kezelőcsapathoz tartozó címke; a v1-ben a 8 kategória.
- **Tanár-címke**: az LLM-fiók által gyártott címke; a tanítás forrása.
- **Kézzel ellenőrzött teszthalmaz**: a felhasználó által átnézett ~200 sor;
  az értékelés referenciája; fagyott, verziózott.
- **Split**: a tanító/teszt felosztás; rögzített seed, dokumentált arány.
- **Mérési futam (run)**: egy tanítás + értékelés egység; konfigurációval és
  eredményfájllal együtt őrződik.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `python -m triage eval --min-accuracy 0.85` a kézzel ellenőrzött
  fagyott teszthalmazon 0 exit code-dal lefut (a diák tipikusan pár ponttal a
  tanára alatt teljesít — a tiny-classifiers tutorial mérései szerint).
- **SC-002**: Kategóriánkénti pontosság ≥ 75% minden kategóriában a fagyott
  teszthalmazon (az értékelő riport ezt sornyi bontásban írja ki).
- **SC-003**: A teljes tanítás + értékelés ≤ 15 perc a helyi gépen, CPU-n
  (mérve: a run napló időbélyegei).
- **SC-004**: Új ticket osztályozása ≤ 100 ms/db a helyi gépen, egyedi
  hívásonként mérve.
- **SC-005**: A tanár-címkézés a sorok ≥99%-ára érvényes címkét ad; a futás
  költség- és időstatisztikája fájlba íródik.

## Assumptions

- ~~A szintetikus minta kategóriacímkéi elfogadható minőségű referenciának
  számítanak~~ — **MEGDŐLT a baseline-mérésen (2026-10-05): 12,0% ± 0,0,
  véletlenszint.** Helyette: a tanár-címkék tekinthetők tanítási
  referenciának, a kiértékelés referenciája a kézzel ellenőrzött teszthalmaz.
- A felhasználó Kimi Code-fiókja az lm15 mentett bejelentkezésén keresztül
  használható címkézésre; a felhasználó ezt az egyszeri, 1000 soros
  kimenő forgalmat jóváhagyta (FR-006 kivétel).
- A felhasználó gépe az egyetlen végrehajtási környezet; internetkapcsolat
  a kezdeti letöltésekhez és a jóváhagyott címkézéshez kell.
- Az adatok és a tanított modell licence engedi a helyi, kísérleti felhasználást.

## Out of Scope

- Valódi (PDI-ből származó) incidenteken való értékelés: a rendelkezésre álló
  67 darab túl kevés a megbízható méréshez, ezért ezt a v1 szándékosan nem
  tartalmazza. *Újraindítási feltétel: ha legalább pár száz valódi, címkézett
  incident áll rendelkezésre.*
- Prioritás-becslés (P1–P4): a mintában a ritka osztályok túl kevesen vannak.
  *Újraindítási feltétel: ha a teljes 10 000 soros adathalmaz elérhető, vagy
  a valódi ticketekből legalább 150/élő osztály összegyűlik.*
- Nem-angol (pl. magyar) ticketek támogatása. *Újraindítási feltétel: ha a
  célkörnyezetben magyar ticketek jelennek meg, és legalább pár száz címkézett
  példa van belőlük.*
- Éles ServiceNow-integráció (flow, REST-hívás a példányból). *Újraindítási
  feltétel: ha SC-001 teljesül, és a felhasználó élesítést kér.*
- Generatív válasz- vagy megoldásjavaslat-készítés (a rendszer kizárólag
  kategorizál). *Újraindítási feltétel: külön spec, más architektúra.*
