# Implementation Plan: Ticket-triázs osztályozó

**Branch**: `001-ticket-triage` | **Date**: 2026-10-05 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-ticket-triage/spec.md`

## Summary

A 1000 soros, kategóriacímkézett szintetikus ticket-mintából egységes tidy
adattábla készül, rögzített seed-del 800/200 tanító/teszt felosztással. Egy
kis encoder-modell teljes (nem adapteres) finomhangolása történik CPU-n a
helyi gépen; az értékelés exit-code-os gate-parancs, amely teljes és
kategóriánkénti pontosságot ír. Az első futás a baseline, fájlba írva,
minden további változtatás ehhez mérik.

## Technical Context

**Language/Version**: Python 3.12 (projekt-venv, a gépen létrehozva)

**Primary Dependencies** (mind pinnelve, Constitution III):

- `torch` (CPU-wheel, pontos verzió a `requirements.txt`-ben)
- `transformers` (pontos verzió)
- `polars` (a dpyr motorja; pontos verzió)
- `dpyr` (a tutorial adat-verbjei: `read`, `col`, `mutate`, `left_join` stb.; pontos verzió)
- `lm15` (a tanár-címkézéshez, mentett Kimi Code-bejelentkezéssel; pontos verzió)
- `pytest` (teszt- és gate-futtatás)

**Student-modell**: `jhu-clsp/ettin-encoder-17m` (pinnelt HF-revízió)

**Storage**: fájlrendszer — `data/` (Parquet), `runs/<név>-<időbélyeg>/`
(config.json, metrics.json, modell-checkpoint)

**Testing**: `pytest -q` (unit + integrációs), plusz az értékelő parancs mint
küszöb-gate: `python -m triage eval --min-accuracy 0.90`

**Target Platform**: Windows 11, a felhasználó PC-je (Ryzen 5 7600X, 32 GB
RAM); CPU-only PyTorch. CUDA nincs, és nincs is rá szükség.

**Project Type**: CLI-csomag (`python -m triage ...`)

**Performance Goals** (a spec SC-ihez kötve):

- tanítás + értékelés ≤ 15 perc CPU-n (SC-003)
- inferencia ≤ 100 ms/db egyedi hívásonként (SC-004)
- teljes pontosság ≥ 90%, kategóriánként ≥ 80% (SC-001, SC-002)

**Constraints**: ticketszöveg nem hagyja el a gépet (Constitution IV);
train/test 0 átfedés (Constitution II); minden verzió pinnelt (Constitution III).

**Scale/Scope**: 1000 ticket, 8 kategória, 17M paraméteres modell — szándékosan
kis skála; a nagyobb adathalmaz újraindítási feltételhez kötött (spec Out of
Scope).

## Key Decisions

### D1: LLM-tanár címkézés (a baseline-mérés nyomán megfordítva)

**Döntés**: az 1000 ticketszöveget egy LLM-tanár címkézi, a felhasználó saját,
jóváhagyott Kimi Code-fiókján keresztül (lm15 mentett bejelentkezés,
alacsony párhuzamosságú adaptív throttle). A diák a tanár címkéire tanul; az
értékelés referenciája a felhasználó által kézzel ellenőrzött ~200 soros
fagyott teszthalmaz.

**Indoklás**: az eredeti D1 azért vetette el a tanárt, mert „a minta már
tartalmaz referencia-címkéket" — a baseline-mérés (12,0% ± 0,0,
véletlenszint) bizonyította, hogy ez a feltevés hamis: a minta címkéi zaj.
A tanár-címkézés tehát nem extra kör, hanem az egyetlen út megbízható
címkéhez.

**Elvetett alternatíva**: a zajos címkékre tanítás — a mérés szerint
véletlenszintű eredményt ad.

**Elvetett alternatíva**: teljesen új, LLM által generált szöveg+címke pár —
elvesztenénk a minta valószerű szövegeit; tartalék terv marad.

**Diák továbbra is**: Ettin-17M encoder, minden súly tanítva, CPU-n
(a recept változatlan).

### D2: dpyr az adattáblához (igazodás a tutorialhoz)

**Döntés**: a tidy-lépés dpyr-rel készül — ugyanazokkal a verbekkel
(`read`, `col`, `mutate`, `left_join`, `select`), amiket a tiny-classifiers
tutorial használ.

**Indoklás**: a felhasználó a tutorial kódjához akar igazodni. Bár a v1
tisztítása polarsban is 6–8 sor lenne, a dpyr-választás a későbbi
tanár-LLM címkéző kör (`label_all`, `accuracy`, összehasonlító riport) közvetlen
átvételét teszi lehetővé a tutorialból — ezek a függvények mind
dpyr-táblákon dolgoznak. Az extra függőség ára (pinnelés, Constitution III)
tudatosan vállalt.

**Elvetett alternatíva**: tiszta polars — kevesebb függőség, de a tutorial
kódjának átvételekor minden tábla-műveletet át kellene írni.

### D3: Stratifikált 800/200 split, seed=0, rögzítve a configban

**Döntés**: kategóriánként arányos felosztás, `seed=0`, a split-ellenőrző
0 átfedést igazol minden futás elején.

**Indoklás**: 8 kiegyensúlyozott kategória esetén a stratifikáció garantálja
a ~100 tanító és ~25 teszt soronkénti lefedettséget; a rögzített seed a
reprodukálhatóság (Constitution II).

**Elvetett alternatíva**: egyszerű véletlen split — kis mintán torzíthatja a
ritkább kategóriák teszt-lefedettségét.

### D4: Baseline-first futási modell

**Döntés**: az első sikeres tanítás+értékelés eredménye
`runs/baseline-*/metrics.json`-be íródik; a recept (tanítási paraméterek)
bármely későbbi változtatása új run, és a riport a baseline-hoz viszonyít.

**Indoklás**: Constitution I (mérés-fegyelem) — a javulás csak nem-átfedő
intervallumnál fogadható el; ehhez a baseline fizikai fájl kell.

**Elvetett alternatíva**: "majd megnézzük a végén" — a playbook szerint ez a
legkönnyebben elhibázható rész; ezért gate.

## Architektúra (ASCII)

```text
data/raw/tickets.csv + categories.csv
        |
        v
[tidy]  dpyr: text = summary + description ---> data/tidy/texts.parquet
        |                                      (task, id, text — címke NÉLKÜL:
        v                                       a minta címkéi zaj, ld. spec)
[label] LLM-tanár (Kimi Code, lm15 login)
        alacsony throttle, resumable, költség/idő-napló
        |                                      data/labels/teacher.jsonl
        v
[review] felhasználó kézzel átnéz ~200 sort  data/labels/handchecked_test.jsonl
        |                                      (MANUÁLIS KAPU, fagyott, verziózott)
        v
[split] stratifikált, seed=0, 0 átfedés a kézi teszthez is (FR-009)
        |
        v
[train] ettin-encoder-17m, full FT, CPU
        AdamW lr=1e-4, batch=32, cosine, maxlen=128
        |
        v
runs/<run>/  config.json + model/ + metrics.json
        |
        +--> [eval]  python -m triage eval --min-accuracy 0.85
        |            exit 0/1; teljes + per-category pontosság -> metrics.json
        |            (referencia: a kézzel ellenőrzött teszthalmaz)
        |
        +--> [predict] python -m triage predict "ticket szöveg"
                       <= 100 ms/db, CPU
```

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Elv | Ellenőrzés | Eredmény |
|-----|-----------|----------|
| I. Mérés-fegyelem | baseline fájl létezik (a zajos-címkés futás dokumentált negatív eredménye); új baseline a tanár-címkéken; gate exit-code-os (SC-001) | PASS |
| II. Adathigiénia | split seed=0 rögzítve (D3); 0-átfedés-ellenőrző a futás elején, a kézi teszthalmazra is (FR-009); érvénytelen címke kihagyva + naplózva | PASS |
| III. Verzió-pinnelés | torch/transformers/dpyr/polars/lm15 pontos verzió, modell pinnelt revízió | PASS |
| IV. Adatvédelem | kimenő forgalom csak a felhasználó által jóváhagyott egyszeri címkézés (FR-006 kivétel, 1000 sor, saját Kimi Code-fiók) | PASS |
| V. Egyszerűség | nincs GPU-út; a dpyr a tutorial-igazodás miatt indokolt (D2); a tanár-kör a mérési megállapítás miatt szükséges (D1) | PASS |

Nincs szükség Complexity Tracking-re (nincs sértett elv).

## Project Structure

### Documentation (this feature)

```text
specs/001-ticket-triage/
├── plan.md              # This file
├── spec.md              # jóváhagyott spec
└── tasks.md             # Phase 2 output (tasks-írás jön)
```

### Source Code (repository root)

```text
src/triage/
├── __init__.py
├── __main__.py          # CLI belépés: tidy / split / train / eval / predict
├── data.py              # tidy + stratifikált split + átfedés-ellenőrző
├── train.py             # finomhangolás (configből)
├── evaluate.py          # teljes + per-category pontosság, exit-code gate
└── predict.py           # egyedi osztályozás + időmérés

tests/
├── unit/                # data.py, evaluate.py egységtesztek
└── integration/         # end-to-end smoke: kis szeleten tidy→train→eval

data/
├── raw/                 # letöltött CSV-k (megvan)
└── tidy/                # generált Parquet

runs/                    # futási naplók + checkpointok + metrics.json
requirements.txt         # pinnelt függőségek
```

**Structure Decision**: egycsomagos CLI (Option 1-variáns), mert a feature egy
lineáris adatfolyam; web-réteg, szolgáltatás és adatbázis nincs (YAGNI).

## Complexity Tracking

Nincs constitution-sértés — a táblázat üres.
