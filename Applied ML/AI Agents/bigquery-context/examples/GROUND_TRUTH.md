# Ground truth & grading rubric

This file documents how `questions.json` encodes the "correct answer" for each
NL2SQL discovery question, and how the harness turns a ranked list of tables
into scores. It is the contract the benchmark scores against — read it before
editing questions or interpreting results.

## Why graded relevance (not a flat table list)

A flat `expected_tables` list forces every retrieval error into one bucket and
makes precision uninformative on a tiny corpus. Real NL2SQL retrieval has
degrees: some tables are *required* to answer, some *help* but aren't essential,
and some are *plausible-looking traps* that a good retriever must reject. We
encode all three so rank-aware metrics (nDCG) and precision (with distractors)
mean something.

Each question carries a `relevance` object with three lists of **short table
names** (the corpus is identical across tiers, so names are unambiguous):

| Key | Meaning | Scoring role |
|-----|---------|--------------|
| `must_have` | Required to answer the question correctly. | Recall numerator; nDCG gain = **2**. |
| `nice_to_have` | Genuinely helps (e.g. a geometry/boundary table for a map, a ZIP↔county crosswalk for a join) but the question is answerable without it. | nDCG gain = **1**; not counted against recall. |
| `distractor` | Looks relevant by name/topic but is the **wrong** table for *this* question. | Precision penalty; nDCG gain = **0** (never correct). |

**Recall** = |ranked ∩ must_have| / |must_have|.
**Precision** = |ranked ∩ (must_have ∪ nice_to_have)| / |ranked|; ranking a
`distractor` directly lowers it.
**Discovery recall** vs **final recall** use the same numerator against the
*nominated* set vs the *reranked* set, isolating discovery from reranking.

## The corpus (15 tables, identical at every tier)

Answer tables:
- `austin_bikeshare_trips`, `austin_bikeshare_stations` — Austin bike share.
- `nyc_taxi_trips_2022` — NYC taxi trips (fares, tips, times).
- `hurricanes`, `weather_stations` — NOAA storms & station locations.
- `population_by_zip_2010`, `usa_names_1910_current`, `us_counties` — demographics/geo.
- `austin_crime` — Austin incident reports.
- `county_natality` — CDC births by county (birth weight, birth rate).
- `air_quality_annual_summary` — EPA annual air quality by county.
- `zip_codes` — ZIP boundaries + ZIP↔county crosswalk (join glue).

Distractors (present in every tier, **never** a correct answer):
- `taxi_zone_geom` — NYC taxi *zone polygons* only. Baits taxi questions that
  actually need trip records (`nyc_taxi_trips_2022`).
- `citibike_stations` — **NYC** Citi Bike stations. Baits Austin bike share
  questions (wrong city).
- `unemployment_cps` — **national** monthly unemployment (CPS). Baits
  local/ZIP-level socioeconomic questions; has no local granularity.

## Question categories

| Category | Intent |
|----------|--------|
| `single-table` | Direct question answerable from one table. Tests basic discovery + rejecting a same-topic distractor. |
| `multi-table-related` | Needs 2+ tables an analyst would obviously pair (trips+stations, hurricanes+weather). |
| `multi-table-disparate` | Needs seemingly-unrelated tables joined via geography (county FIPS / ZIP), e.g. air quality ↔ natality. The hard discovery case. |
| `trap` | Phrased to bait a distractor (wrong city, zone-vs-trips, national-vs-local). The `must_have` is the real table; the `distractor` must stay out of the top ranks. |

## Trap design (how each distractor is baited)

- **Wrong city:** `citibike_stations` is baited by any Austin bike share
  question, most aggressively by `trap-q4` ("Citi Bike-style docking stations
  **in Austin**") — the name matches, the geography does not.
- **Zone-vs-trips:** `taxi_zone_geom` is baited by taxi questions about fares /
  tips / revenue, which live in `nyc_taxi_trips_2022`, not the zone lookup.
- **National-vs-local:** `unemployment_cps` is baited by `trap-q3`, which asks
  for unemployment by **Austin ZIP code** — a granularity CPS does not have, so
  the real answer stays `austin_crime` (+ ZIP geography) and CPS is wrong.

A retriever that pattern-matches on keywords ranks the distractor; one that
reasons about geography/granularity rejects it. That gap is what precision and
nDCG on the `trap` category measure.

## Relevance-gap probes (geography-mismatch + implicit ratio)

The disparate set includes a deliberate probe grid isolating **one** discovery
failure of semantic search. An initial "implicit ratios are the problem"
hypothesis is **refuted by the data**: implicit per-capita questions whose
geography *matches* the denominator table (Austin-ZIP question ↔ ZIP-keyed table)
retrieve the partner at 100%. The failure needs **two factors together**:

1. **Geography mismatch** — the required table is keyed to a *different*
   geography than the question names (a **county** question needing the
   **ZIP-keyed** `population_by_zip_2010`), and
2. **Implicit reference** — the join is implied only by a computed ratio ("per
   capita"), sharing no salient term with the query text.

The probes form a 2×2 over those factors, so the confirmed pattern — fail only
when *both* hold — is a property of the reference, not a quirk of one table:

| Probe | Geography | Reference | Partner (`population_by_zip_2010` / area) | Discovery |
|---|---|---|---|---|
| `multi-disp-q6` — "crimes **per capita**" | ZIP ↔ ZIP (match) | implicit | `population_by_zip_2010` | ✅ 100% |
| `multi-disp-q8` — "crimes **per square mile**" | ZIP ↔ ZIP (match) | implicit | `zip_codes` (area) | ✅ 100% |
| `multi-disp-q3` — "weather stations **per capita**" | **county ↔ ZIP (mismatch)** | implicit | `population_by_zip_2010` | ❌ 0% |
| `multi-disp-q11` — "births **per capita**" | **county ↔ ZIP (mismatch)** | implicit | `population_by_zip_2010` | ❌ 0% |
| `multi-disp-q10` — "…relative to their **resident population**" | county ↔ ZIP (mismatch) | **named** | `population_by_zip_2010` | ✅ 100% |
| `multi-disp-q12` — "…relative to their **resident population**" | county ↔ ZIP (mismatch) | **named** | `population_by_zip_2010` | ✅ 100% |

Two independent rescue paths close the gap, confirming both factors are load-bearing:
**match the geography** (q6/q8, ZIP-anchored implicit → 100%) *or* **name the
partner** (q10/q12, mismatched but explicit → 100%). The gap holds across two
unrelated subject tables (`weather_stations`, `county_natality`) and is
**tier-invariant** (0% at every enrichment tier — richer metadata cannot recover a
table search never retrieves), so it is a *retrieval* limit, not a metadata one.
`multi-disp-q7`/`q9` ("relative to their resident population" / "land area") are
named twins of the ZIP-anchored probes; `multi-disp-q2` and `multi-rel-q4` are
additional named-population controls. All join keys are real: `austin_crime.zipcode`
↔ `population_by_zip_2010.zipcode` / `zip_codes.zip_code`, `zip_codes.area_land_meters`
supplies land area, and `county_natality.County_of_Residence_FIPS` joins counties to
ZIP population via the `zip_codes` crosswalk.

## Editing rules

- Use **short table names** exactly as they appear in `scripts/setup.py`'s
  `CORPUS` (the harness scores on `full_id.rsplit(".", 1)[-1]`).
- Every `distractor` must be a table that is genuinely present in the corpus and
  genuinely wrong for that question — never invent one, never let it be correct
  for the same question elsewhere.
- Keep `must_have` minimal: only tables without which the question cannot be
  answered. Push "would help" tables to `nice_to_have`.
