# tiny-incident-triage Constitution

## Core Principles

### I. Mérés-fegyelem (NON-NEGOTIABLE)

Minden minőségi állítás méréssel indul és méréssel zárul. Baseline MINDIG a
változtatás előtt készül, fájlba írva, per-axis bontásban. Javulást csak
nem-átfedő intervallumoknál fogadunk el (kis mintán 2–3 ismétléssel mérjük a
zajt). A gate-ek exit-code-os parancsok (pl. `pytest -q`, `python eval.py --min-accuracy 0.80`),
nem szubjektív lépések. Mérésnél cache-higiénia kötelező (cache=False vagy
ekvivalens).

### II. Adathigiénia (NON-NEGOTIABLE)

A tanító- és teszthalmaz sosem keveredik; a split seedje rögzített és a
specben dokumentált. A teszthalmazhoz a tanítás alatt semmi nem nyúl — a
kiértékelés mindig ugyanazon a fagyott teszthalmazon fut. Érvénytelen vagy
hiányzó címke: kihagyjuk a tanításból, sosem találgatjuk.

### III. Verzió-pinnelés

Modell, tokenizer, könyvtár és adat-verziók mindig pontosan pinnelve (nem
lebegő alias, nem `latest`). Verzióváltás = baseline újramérés.

### IV. Adatvédelem

A ticketszöveg alapértelmezetten nem hagyja el a gépet. Tanár-címkézés csak a
felhasználó által jóváhagyott fiókon/szolgáltatón keresztül történhet, és a
spec rögzíti, melyik adathalmaz mehetett ki, melyik nem.

### V. Egyszerűség (YAGNI)

A legkisebb megoldás, ami átmegy a gate-eken. Nincs spekulatív absztrakció;
amit a spec nem ír elő, azt nem építjük meg.

## Fejlesztési környezet

Az implementáció helyben történik, a felhasználó Windows 11-es PC-jén (Ryzen 5
7600X, 32 GB RAM, Radeon RX 7900 XT — NVIDIA/CUDA nincs). A tanítás CPU-n fut;
a plan.md-ben minden hardver-feltételezés ehhez igazodik. Szerveroldali Prime
Agent-átadás ebben a projektben NINCS — ha a későbbiekben mégis szükség lenne
rá, az a constitution módosításával történik.

## Review-folyamat

- A spec.md, plan.md és tasks.md mindegyike emberi jóváhagyási kapun megy át;
  egyik sem tekinthető jóváhagyottnak a felhasználó explicit döntése nélkül.
- A MANUÁLIS KAPU-ként jelölt taskokat agent nem pipálhatja ki — azokat a
  felhasználó hajtja végre és igazolja vissza.
- A constitution minden más gyakorlat felett áll; módosítása dokumentált,
  a felhasználó által jóváhagyott lépés.

## Governance

Minden spec és plan írásakor a Constitution Check kapu kötelező: a terv
sértése esetén javítás vagy explicit, indokolt kivétel a plan.md Complexity
Tracking szekciójában.

**Version**: 1.0.0 | **Ratified**: 2026-10-05 | **Last Amended**: 2026-10-05
