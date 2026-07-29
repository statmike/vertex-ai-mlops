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

## Editing rules

- Use **short table names** exactly as they appear in `scripts/setup.py`'s
  `CORPUS` (the harness scores on `full_id.rsplit(".", 1)[-1]`).
- Every `distractor` must be a table that is genuinely present in the corpus and
  genuinely wrong for that question — never invent one, never let it be correct
  for the same question elsewhere.
- Keep `must_have` minimal: only tables without which the question cannot be
  answered. Push "would help" tables to `nice_to_have`.
