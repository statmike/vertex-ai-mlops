![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FApplied+ML%2FAI+Agents%2Fbigquery-context&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20ML/AI%20Agents/bigquery-context/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/bigquery-context/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/bigquery-context/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/bigquery-context/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/bigquery-context/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Connect With Author On: </b> 
    <a href="https://www.linkedin.com/in/statmike"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a>
    <a href="https://www.github.com/statmike"><img src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub Logo" width="20px"></a> 
    <a href="https://www.youtube.com/@statmike-channel"><img src="https://upload.wikimedia.org/wikipedia/commons/f/fd/YouTube_full-color_icon_%282024%29.svg" alt="YouTube Logo" width="20px"></a>
    <a href="https://bsky.app/profile/statmike.bsky.social"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://x.com/statmike"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/Applied%20ML/AI%20Agents/bigquery-context/readme.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/Applied%20ML/AI%20Agents/bigquery-context/readme.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# BigQuery Context — Six Approaches to Table Discovery

An [ADK](https://google.github.io/adk-docs/) multi-agent system comparing six approaches to finding the best BigQuery tables for a natural-language question — the retrieval step of NL2SQL. Five of the six converge on the **same shared reranker**, so their outputs are directly comparable; the sixth (**Search Direct**) deliberately skips the reranker and uses semantic search's own ranking, which turns the search-vs-rerank contrast into a measured result rather than an assumption. It works two ways: an interactive **story** (the notebook + `adk web`) and a rigorous **benchmark** (a factorial experiment in [`examples/`](examples/)) that a data platform team can trust as evidence.

> **Naming note:** Google renamed **Dataplex Universal Catalog** to **Knowledge Catalog** (April 2026). This is a branding change only — the API service, Python SDK, CLI, and IAM roles are all unchanged (`dataplex.googleapis.com`, `google-cloud-dataplex` / `dataplex_v1`, `roles/dataplex.*`). This project uses "Knowledge Catalog" in prose and code identifiers, while API-mechanic identifiers keep the `dataplex` namespace.

## The Challenge

Before an agent can write SQL, it must find the *right tables* — from tens to thousands of candidates, often with lookalike names (a taxi *zone-lookup* table vs the trips table; a *Citi Bike* stations table vs Austin's). Get retrieval wrong and the best SQL model still answers the wrong question. So: **which discovery strategy retrieves the right tables, and how much does richer catalog metadata (profiling, a business glossary, NL→SQL guidelines) actually help?**

That second half is easy to get wrong. If you enrich only some topics, "enrichment helps" is confounded with "those topics are easier." This project isolates the effect with a designed experiment.

## The Experiment

**Independent variable:** catalog **enrichment tier** — `0` schema only → `1` +profiling → `2` +glossary → `3` +guidelines.
**Held constant:** the corpus. `scripts/setup.py` replicates the **identical** 15-table corpus into one dataset per tier (`{prefix}_tier0`..`_tier3`); the datasets differ *only* in catalog enrichment. Every topic appears at every tier, so tier is decoupled from topic — the replication *is* the ablation.

**Design:** a full factorial over four factors — **3,000** isolated approach-runs:

- **Approach (6):** the six discovery strategies compared (see [The Six Approaches](#the-six-approaches)).
- **Tier (4):** enrichment level `0`–`3` (the independent variable above).
- **Question (25):** the graded question set (composition below).
- **Run (n=5):** replicates per cell, for medians + IQR spread.

Each cell is an **isolated** approach-run (its own `InMemoryRunner`, one at a time) for clean latency and token attribution.

**The 25 questions** are deliberately weighted toward the hard case — nearly half require joining tables that share no obvious name, which is where discovery strategies actually separate:

| Category | Count | What it tests | Example |
|---|---|---|---|
| `single-table` | 5 | Basic discovery + rejecting a same-topic distractor. | *"What were the strongest hurricanes to make landfall in the last 20 years?"* |
| `multi-table-related` | 4 | Tables an analyst would obviously pair. | *"Which bike share stations have the highest average trip duration, and where are they located?"* (trips + stations) |
| `multi-table-disparate` | 12 | Seemingly-unrelated tables joined via geography (ZIP / county FIPS) — the hard discovery case, and home to the relevance-gap probes. | *"Which US counties have the most weather stations per capita?"* (counties + weather + population) |
| `trap` | 4 | Phrased to bait a distractor (wrong city, zone-vs-trips, national-vs-local); the `must_have` is the real table. | *"Which Citi Bike-style docking stations in Austin are the busiest?"* (baits the NYC `citibike_stations` table) |

The full graded set — every question with its `must_have` tables and baited distractor:

<details>
<summary><b>All 25 questions with their needed tables</b></summary>

<!-- QUESTIONS:START (generated by build_results.py) -->

_Auto-generated by `examples/build_results.py` from `examples/questions.json` — do not edit between the markers._

All **25** graded questions (5 single-table, 4 multi-table-related, 12 multi-table-disparate, 4 trap). `Must-have` tables are the recall target; `distractor` is the baited wrong table (blank if none). Full grading rubric: [`examples/GROUND_TRUTH.md`](examples/GROUND_TRUTH.md).

| # | Category | Question | Must-have tables | Distractor baited |
|---|---|---|---|---|
| `single-q1` | single-table | What are the busiest bike share stations in Austin by month? | `austin_bikeshare_trips` | `citibike_stations` |
| `single-q2` | single-table | How do tip amounts vary by time of day for NYC taxi rides? | `nyc_taxi_trips_2022` | `taxi_zone_geom` |
| `single-q3` | single-table | What were the strongest hurricanes to make landfall in the last 20 years? | `hurricanes` | — |
| `single-q4` | single-table | Which baby names have grown fastest in popularity across US states since 1990? | `usa_names_1910_current` | — |
| `single-q5` | single-table | What is the average birth weight by US county? | `county_natality` | — |
| `multi-rel-q1` | multi-table-related | Which bike share stations have the highest average trip duration, and where are they located? | `austin_bikeshare_trips`, `austin_bikeshare_stations` | `citibike_stations` |
| `multi-rel-q2` | multi-table-related | Are there weather stations near the paths of major hurricanes? | `hurricanes`, `weather_stations` | — |
| `multi-rel-q3` | multi-table-related | Which US counties have the worst annual air quality, and what are their boundaries? | `air_quality_annual_summary`, `us_counties` | — |
| `multi-rel-q4` | multi-table-related | How do birth rates compare across US counties relative to their population? | `county_natality`, `population_by_zip_2010` | — |
| `multi-disp-q1` | multi-table-disparate | Is there a correlation between crime rates and bike share usage near specific stations in Austin? | `austin_crime`, `austin_bikeshare_trips`, `austin_bikeshare_stations` | `citibike_stations` |
| `multi-disp-q10` | multi-table-disparate | Which US counties have the most weather stations relative to their resident population? | `us_counties`, `weather_stations`, `population_by_zip_2010` | — |
| `multi-disp-q11` | multi-table-disparate | Which US counties have the highest number of births per capita? | `county_natality`, `population_by_zip_2010` | — |
| `multi-disp-q12` | multi-table-disparate | Which US counties have the most births relative to their resident population? | `county_natality`, `population_by_zip_2010` | — |
| `multi-disp-q2` | multi-table-disparate | How does population density by ZIP code relate to bike share station placement in Austin? | `population_by_zip_2010`, `austin_bikeshare_stations` | `citibike_stations` |
| `multi-disp-q3` | multi-table-disparate | Which US counties have the most weather stations per capita? | `us_counties`, `weather_stations`, `population_by_zip_2010` | — |
| `multi-disp-q4` | multi-table-disparate | Does county air quality relate to average birth weight across the US? | `air_quality_annual_summary`, `county_natality` | — |
| `multi-disp-q5` | multi-table-disparate | Do Austin ZIP codes with more reported crime also have worse air quality? | `austin_crime`, `air_quality_annual_summary` | — |
| `multi-disp-q6` | multi-table-disparate | Which Austin ZIP codes have the most reported crimes per capita? | `austin_crime`, `population_by_zip_2010` | `unemployment_cps` |
| `multi-disp-q7` | multi-table-disparate | Which Austin ZIP codes have the most reported crime relative to their resident population? | `austin_crime`, `population_by_zip_2010` | `unemployment_cps` |
| `multi-disp-q8` | multi-table-disparate | Which Austin ZIP codes have the most reported crimes per square mile? | `austin_crime`, `zip_codes` | — |
| `multi-disp-q9` | multi-table-disparate | Which Austin ZIP codes have the most reported crime relative to their land area? | `austin_crime`, `zip_codes` | — |
| `trap-q1` | trap | Which Austin bike share stations currently have the most open docks? | `austin_bikeshare_stations` | `citibike_stations` |
| `trap-q2` | trap | What is the total fare and tip revenue collected across NYC taxi zones? | `nyc_taxi_trips_2022` | — |
| `trap-q3` | trap | How does the unemployment rate differ between high-crime and low-crime Austin ZIP codes? | `austin_crime` | `unemployment_cps` |
| `trap-q4` | trap | Which Citi Bike-style docking stations in Austin are the busiest? | `austin_bikeshare_trips`, `austin_bikeshare_stations` | `citibike_stations` |

<!-- QUESTIONS:END -->

</details>

Raw grading source: [`examples/questions.json`](examples/questions.json) and [`examples/GROUND_TRUTH.md`](examples/GROUND_TRUTH.md).

- `bq_tools` and `search_direct` read no reranker enrichment → they are **enrichment-invariant controls** (`bq_tools` reads BQ schema; `search_direct` applies no reranker at all), isolating what enrichment adds over a schema-only baseline. The `search_direct` vs `kc_search` pair — identical retrieval, with and without the LLM rerank — measures exactly what the reranker buys (see **Results**).
- Ground truth is **graded** (`must_have` / `nice_to_have` / `distractor`) and the corpus includes deliberate **distractor tables** + **trap questions**, so precision and rank-quality metrics are meaningful. See [`examples/GROUND_TRUTH.md`](examples/GROUND_TRUTH.md).
- Metrics per approach × tier (median + IQR over the 5 runs): discovery vs final recall, nDCG@5, precision-with-distractors, isolated latency p50/p95, and reranker token cost — sliced by question category. See [`examples/`](examples/) to run it and [`examples/results.md`](examples/results.md) for the report.

## The Six Approaches

Each approach uses a different combination of APIs, execution patterns, and metadata richness to discover and evaluate BigQuery tables:

| # | Approach | Discovery API | Metadata API | Metadata Content | Execution Pattern | Cache Usage | Reranker Called As | Reranker Receives |
|---|---|---|---|---|---|---|---|---|
| 1 | **BQ Metadata Tools** | BQ API: `list_dataset_ids`, `list_table_ids` | BQ API: `get_table_info` | Schema (columns, types, modes), description, row count | LLM-driven tool calls | None | ADK tool (`rerank_tables`) — LLM decides when | `get_table_info` text (schema only, no `dataProfile`) |
| 2 | **Knowledge Catalog Search** | KC: [`search_entries`](https://cloud.google.com/python/docs/reference/dataplex/latest/google.cloud.dataplex_v1.services.catalog_service.CatalogServiceClient#google_cloud_dataplex_v1_services_catalog_service_CatalogServiceClient_search_entries) | KC: [`lookup_entry`](https://cloud.google.com/python/docs/reference/dataplex/latest/google.cloud.dataplex_v1.services.catalog_service.CatalogServiceClient#google_cloud_dataplex_v1_services_catalog_service_CatalogServiceClient_lookup_entry) | Schema, description, catalog aspects (no profiling) | `before_agent_callback` (deterministic) | None | Direct function in `before_agent_callback` | `lookup_entry` JSON (schema + aspects, no `dataProfile`) |
| 3 | **Knowledge Catalog Context** | None (all tables from cache) | KC: [`lookup_context`](https://cloud.google.com/dataplex/docs/retrieve-data-context) *(preview)* | Schema, description, `dataProfile`, glossary terms, `frequent_joins`, guidelines | `before_agent_callback` (deterministic) | `get_all_detailed()` — all tables, full JSON | Direct function in `before_agent_callback` | capsule JSON — all tables |
| 4 | **Context Pre-Filter** | None (LLM reviews cached briefs) | KC: [`lookup_context`](https://cloud.google.com/dataplex/docs/retrieve-data-context) *(preview)* | **Briefs**: schema + enrichments, no `dataProfile`; **Reranker**: full capsule | LLM tool call + `after_agent_callback` | `get_all_briefs()` → `get_detailed_for_tables()` | Direct function in `after_agent_callback` | capsule JSON — nominated tables only |
| 5 | **Semantic Context** | KC: [`search_entries`](https://cloud.google.com/python/docs/reference/dataplex/latest/google.cloud.dataplex_v1.services.catalog_service.CatalogServiceClient#google_cloud_dataplex_v1_services_catalog_service_CatalogServiceClient_search_entries) | KC: [`lookup_context`](https://cloud.google.com/dataplex/docs/retrieve-data-context) *(preview)* | Schema, description, `dataProfile`, glossary terms, `frequent_joins`, guidelines | `before_agent_callback` (deterministic) | `get_detailed_for_tables()` — matched tables only | Direct function in `before_agent_callback` | capsule JSON — matched tables only |
| 6 | **Search Direct** | KC: [`search_entries`](https://cloud.google.com/python/docs/reference/dataplex/latest/google.cloud.dataplex_v1.services.catalog_service.CatalogServiceClient#google_cloud_dataplex_v1_services_catalog_service_CatalogServiceClient_search_entries) | None (search order is the answer) | Name + relevance rank from search | `before_agent_callback` (deterministic) | None | **Not called** — search's own order is the final ranking | — (no reranker) |

### Key APIs Used

| API | SDK / Protocol | What It Returns | Used By |
|---|---|---|---|
| BQ `get_table_info` | ADK [BigQueryToolset](https://google.github.io/adk-docs/integrations/bigquery/) | Schema (column names, types, modes), description, row count | Approach 1 |
| KC `search_entries` | `google-cloud-dataplex` SDK | Semantically matched, already-ranked in-scope entries (name, description, entry type); count set by search's internal relevance cutoff | Approaches 2, 5, 6 |
| KC `lookup_entry` | `google-cloud-dataplex` SDK | Schema + catalog aspects as JSON (no data profiling stats) | Approach 2 |
| KC `lookup_context` | `google-cloud-dataplex` SDK (>=2.20.0, **preview**) | LLM-ready capsule: schema + descriptions + `dataProfile` + glossary terms + `frequent_joins` + guidelines (JSON format, batch limit 10) | Approaches 3, 4, 5 (via shared cache) |

### Shared Context Cache

Approaches 3, 4, and 5 share a context cache (`context_cache/`) populated once at startup from the Knowledge Catalog [`lookup_context`](https://cloud.google.com/dataplex/docs/retrieve-data-context) API (SDK >=2.20.0, preview). The cache stores per-table metadata with two views derived from the same JSON response:

| View | Function | Content | Typical Size | Used By |
|---|---|---|---|---|
| **brief** | `get_all_briefs()` | Capsule with per-column `dataProfile` stripped — keeps table name, description, schema (name/type/description), **plus enrichments**: glossary terms, `frequent_joins`, guidelines | ~1,300 chars/table | Approach 4 (LLM pre-filtering in system prompt) |
| **detailed** | `get_all_detailed()`, `get_detailed_for_tables()` | Full capsule including `dataProfile` per column (nullRatio, distinctValues, sampleValues) and all enrichments | ~5,500 chars/table | Approaches 3, 4 (reranking), 5 |

Both views come from the same `lookup_context` JSON — the brief is derived *subtractively* by stripping only the heavy per-column `dataProfile` section, so the cheap high-signal enrichments (glossary terms, join hints, guidelines) survive into briefs for LLM pre-filtering. No separate BQ API calls are needed.

**Cache population at startup:**
1. Build table list from `config.SCOPE` — for bare datasets, enumerate tables via `bq_client.list_tables()`; for `dataset.table` entries, use directly
2. Build catalog entry names for each table
3. Call `lookup_context` in batches per dataset (up to 10 entries per API call, JSON format)
4. Parse response, split into per-table entries, store both brief (stripped) and detailed (full) views in `_CACHE[project.dataset.table]`

The orchestrator is a `SequentialAgent`: a `ParallelAgent` fans the question out to all six approaches at once, then a `compare_results` agent synthesizes their outputs from shared state. The per-approach flows below detail what each one does inside that fan-out.

### Detailed Approach Flows

#### Approach 1: BQ Metadata Tools (`agent_bq_tools`)

LLM-driven discovery using ADK BigQueryToolset — no cache, no Knowledge Catalog. The agent decides which datasets to explore and which tables to inspect:

1. **`list_dataset_ids`** → `after_tool_callback` (`filter_scope`) prunes to `config.SCOPE` → LLM sees only in-scope datasets
2. **`list_table_ids`** per dataset → `filter_scope` prunes to scoped tables
3. **`get_table_info`** per table → schema (columns, types, modes), description, row count — no column descriptions, no `dataProfile`
4. **`rerank_tables`** ADK tool → LLM passes nominated table IDs → `call_reranker()` → results stored in state
5. LLM formats final response

#### Approach 2: Knowledge Catalog Search (`agent_kc_search`)

Deterministic `before_agent_callback` — LLM never invoked. Uses the Knowledge Catalog SDK for both discovery and metadata:

1. **`search_entries`** — `CatalogServiceClient`, `semantic_search=True`, scoped via a bare `parent:datasets/{ds}` predicate (no parentheses around the question — wrapping it voids the predicate; see the Results probe)
2. **Scope filter** — `is_table_in_scope()` on each match (defense-in-depth; with the correct query the predicate already scopes server-side)
3. **`lookup_entry`** per matched table — `EntryView.FULL` → schema, description, catalog aspects. **No `dataProfile`**
4. **`call_reranker()`** direct function call → results stored in state
5. **Return `types.Content`** → LLM skipped

This is the baseline that Approach 5 improves upon — same semantic search, but weaker metadata (`lookup_entry` vs cached `lookup_context`). It shares its exact retrieval with Approach 6 (Search Direct); the difference is that Approach 2 reranks the results while Approach 6 keeps search's own order, so the pair isolates the reranker's marginal value.

#### Approach 3: Knowledge Catalog Context (`agent_kc_context`)

Deterministic `before_agent_callback` — zero per-query API calls, all metadata from shared cache:

1. **`get_all_detailed()`** from cache → JSON array of ALL in-scope tables with the full capsule (`dataProfile` + enrichments)
2. **`call_reranker()`** → sends everything to the reranker (no pre-filtering)
3. **Return `types.Content`** → LLM skipped

Sends the richest metadata but evaluates all tables — relies entirely on the reranker to sort by relevance.

#### Approach 4: Context Pre-Filter (`agent_context_prefilter`)

Hybrid: LLM selects candidates from briefs, deterministic `after_agent_callback` reranks with full metadata:

1. **System prompt embeds `get_all_briefs()`** — JSON array of all tables, `dataProfile` stripped (name, description, schema columns only)
2. **LLM reviews briefs** → calls `nominate_tables(table_ids=[...])` tool
3. **`after_agent_callback`** (`rerank_nominations`):
   - **`get_detailed_for_tables(nominated_ids)`** — full JSON with `dataProfile` for nominated tables only
   - **`call_reranker()`** → results stored in state
   - LLM's reasoning response serves as agent output (no Content returned)

Two-stage approach: compact briefs for LLM filtering, full metadata for reranking.

#### Approach 5: Semantic Context (`agent_semantic_context`)

Deterministic `before_agent_callback` — Approach 2's search + Approach 3's cached metadata:

1. **`search_entries`** — same semantic search as Approach 2 (`semantic_search=True`, `parent:` scoped)
2. **Scope filter** — `is_table_in_scope()` on each match
3. **`get_detailed_for_tables(matched_ids)`** — cache lookup replaces Approach 2's N `lookup_entry` calls (zero additional API calls). Full capsule with `dataProfile` + enrichments
4. **`call_reranker()`** → results stored in state
5. **Return `types.Content`** → LLM skipped

The improved version of Approach 2: same discovery, richer metadata, fewer API calls.

#### Approach 6: Search Direct (`agent_search_direct`)

Deterministic `before_agent_callback` — same retrieval as Approach 2, but **no reranker and no LLM at all**:

1. **`search_entries`** — the *identical* bare-form semantic search Approach 2 issues (`semantic_search=True`, `parent:datasets/{ds}` scoped)
2. **Scope filter** — `is_table_in_scope()` on each match
3. **Build `RerankerResponse` from search order** — rank = search position, confidence = a descending proxy; the full returned set is the answer, with no truncation and no `call_reranker()`
4. **Return `types.Content`** → LLM skipped

This is the control that treats semantic search as *both* discovery and ranking. Because it runs the same retrieval as Approach 2 but skips the rerank, the **Approach 6 vs Approach 2** contrast measures the reranker's marginal value directly (see **Results**).

#### Shared Reranker

Five of the six approaches converge on `call_reranker()` (Gemini structured output → `RerankerResponse`); Approach 6 deliberately skips it:

- **Input**: question + `candidate_metadata` string + `discovery_method` + `top_k`
- **Output**: `ranked_tables` with confidence scores, `key_columns` with filtering/aggregation hints, `sql_hints`, and `join_suggestions`
- **State**: each approach stores `nominated_tables_{method}` and `reranker_result_{method}` — read by the compare agent. Approach 6 populates the same state keys, but its `ranked_tables` come from search order rather than the reranker.
- **Invocation**: Approach 1 calls it as an ADK tool (LLM decides when); Approaches 2–5 call it as a direct function in callbacks; Approach 6 does not call it.

## Prerequisites

### 1. Install dependencies

```bash
uv sync --extra dev
# or: make install
```

Register the Jupyter kernel so the notebook uses this project's virtual environment:

```bash
uv run python -m ipykernel install --user --name "bigquery-context" --display-name "Python (bigquery-context)"
# or: make kernel
```

### 2. Configure `.env`

Copy `.env` and set your project ID:

```env
GOOGLE_CLOUD_PROJECT=your-project-id
```

### 3. Run setup (demo data)

This step provisions the experiment's corpus. If you already have BigQuery tables you want to discover, skip it and update `SCOPE` in `config.py` to point at your own datasets/tables.

The setup script replicates a single 15-table corpus (views over `bigquery-public-data`) into **one dataset per enrichment tier**, then applies only that tier's catalog enrichment:

```bash
uv run python scripts/setup.py
# or: make setup
```

**What setup creates** — four datasets, each holding the *identical* corpus, differing only in enrichment:

| Dataset | Tier | Profiling | Glossary | Guidelines |
|---|---|---|---|---|
| `{prefix}_tier0` | 0 · schema only | — | — | — |
| `{prefix}_tier1` | 1 · + profiling | yes | — | — |
| `{prefix}_tier2` | 2 · + glossary | yes | yes | — |
| `{prefix}_tier3` | 3 · + guidelines | yes | yes | yes |

The corpus (15 tables), glossary terms, and guideline text are authored **once** in `scripts/setup.py` (`CORPUS`, `GLOSSARY_TERMS`, `GUIDELINES`) — the single source of truth, imported by `cleanup.py` and the benchmark so nothing drifts. It spans transportation, weather, demographics, geography, and health-by-geography tables, plus **3 deliberate distractor tables** (`taxi_zone_geom`, `citibike_stations`, `unemployment_cps`) that look relevant by name but are never a correct answer. See [`examples/GROUND_TRUTH.md`](examples/GROUND_TRUTH.md) for the grading rubric.

<details>
<summary><b>The 15-table corpus (tables picked, with sources)</b></summary>

<!-- CORPUS:START (generated by build_results.py) -->

_Auto-generated by `examples/build_results.py` from `scripts/setup.py`'s `CORPUS` — do not edit between the markers._

The identical corpus — **12 answer tables + 3 distractors = 15** — is replicated into every tier dataset. Distractors look relevant by name but are never a correct answer.

| Table | Role | Source (`bigquery-public-data.…`) | What it holds |
|---|---|---|---|
| `austin_bikeshare_trips` | answer | `austin_bikeshare.bikeshare_trips` | Bike share trip records from Austin, Texas. Each row is a single bike trip with start/end times, stations, duration, and subscriber type. |
| `austin_bikeshare_stations` | answer | `austin_bikeshare.bikeshare_stations` | Bike share station locations in Austin, Texas. Each row is a station with name, status, latitude/longitude, and number of docks. |
| `nyc_taxi_trips_2022` | answer | `new_york_taxi_trips.tlc_yellow_trips_2022` | NYC yellow taxi trip records for 2022. Includes pickup/dropoff times and locations, fare amounts, tip amounts, and payment types. |
| `hurricanes` | answer | `noaa_hurricanes.hurricanes` | International Best Track Archive for Climate Stewardship (IBTrACS). Historical hurricane and tropical cyclone tracks with wind speed, pressure, position, and storm classification from multiple agencies. |
| `weather_stations` | answer | `ghcn_d.ghcnd_stations` | Global Historical Climatology Network weather station inventory. Station locations with latitude, longitude, elevation, and name. |
| `population_by_zip_2010` | answer | `census_bureau_usa.population_by_zip_2010` | US Census 2010 population counts by ZIP code. Includes total population, minimum and maximum age, and gender breakdowns. |
| `usa_names_1910_current` | answer | `usa_names.usa_1910_current` | US baby name popularity from Social Security applications. Each row is a name-state-year-gender combination with occurrence count. |
| `us_counties` | answer | `geo_us_boundaries.counties` | US county boundaries with FIPS codes, names, state associations, land/water area, and geographic coordinates. |
| `austin_crime` | answer | `austin_crime.crime` | Austin, Texas crime reports. Each row is a reported crime incident with type, description, location, timestamp, and clearance status. |
| `county_natality` | answer | `sdoh_cdc_wonder_natality.county_natality` | CDC WONDER natality (birth) statistics by US county and year. Each row aggregates births with average mother age, gestational age, birth weight, and pre-pregnancy BMI, keyed by county FIPS code. |
| `air_quality_annual_summary` | answer | `epa_historical_air_quality.air_quality_annual_summary` | EPA annual air-quality summaries by monitoring site. Each row is a pollutant measured at a site (state/county code, lat/long) for a year, with the annual arithmetic mean, maxima, and exceedance counts. |
| `zip_codes` | answer | `geo_us_boundaries.zip_codes` | US ZIP code geographic boundaries and attributes: city, county, state, land/water area, and centroid latitude/longitude. A crosswalk between ZIP codes and counties/states. |
| `taxi_zone_geom` | distractor | `new_york_taxi_trips.taxi_zone_geom` | NYC taxi zone lookup: zone id, name, borough, and boundary geometry. A reference table for taxi zones — it holds no trip, fare, or tip records. |
| `citibike_stations` | distractor | `new_york.citibike_stations` | New York City Citi Bike station status: capacity, bikes/docks available, and real-time availability flags. NYC bike share — not Austin — and holds no trip history. |
| `unemployment_cps` | distractor | `bls.unemployment_cps` | US Bureau of Labor Statistics national unemployment time series from the Current Population Survey. National monthly series — not broken down by ZIP code or county. |

<!-- CORPUS:END -->

</details>

**Why replicate ×4?** For the enrichment ablation (see **The Experiment**). One operational consequence: because every tier dataset holds identically-named tables and scoring matches on short table name, **each benchmark run is scoped to exactly one tier dataset** (`config.ACTIVE_TIER`) — see the Configuration section.

**Why views?** Views are free (zero storage cost) and place everything in your project's Knowledge Catalog, so all six discovery approaches work equally. Without this, semantic search only finds tables in your own project.

#### What each enrichment tier adds

- **Profiling** — a [data profile scan](https://cloud.google.com/dataplex/docs/data-profiling-overview) (`DataProfileScan`, `catalog_publishing_enabled=True`) publishes column-level statistics (null ratios, distinct values, sample values). These surface in the `lookup_context` capsule as `dataProfile`.
  - Before profiling: ~600 chars (schema only)
  - After profiling: ~3,500+ chars (schema + `dataProfile` per column)
- **Glossary** — a [business glossary](https://cloud.google.com/dataplex/docs/create-glossary) with terms linked to specific columns via definition entry links. Terms surface in the capsule as `related_terms`.
- **Guidelines** — the `guidelines` [system aspect](https://cloud.google.com/dataplex/docs/enrich-entries-metadata) carries authored NL→SQL guidance per table. It surfaces in the capsule as `guidelines`.

> **Example queries / "golden queries":** Knowledge Catalog *auto-generates* example SQL queries for well-used tables; there is no manual authoring API for them. The user-authorable hook that reliably surfaces in `lookup_context` is the `guidelines` aspect, which is what this project uses to embed query guidance.

### 4. Notebook walkthrough

Before running the agents, the [`bigquery_context.ipynb`](bigquery_context.ipynb) notebook walks through the approaches step-by-step — showing the raw API calls, the metadata each approach provides (including the enriched `lookup_context` capsule with glossary terms, join hints, and guidelines), and a side-by-side comparison of results. This helps you understand what each agent does under the hood.

### 5. Run the agents

**Interactive web UI (recommended):**

```bash
uv run adk web .
```

This opens a browser-based chat interface. Use the agent selector dropdown (top-left) to choose which agent to run — `agent_orchestrator` runs all six in parallel, or pick any individual approach to run it standalone.

**Example questions to try:**

Single-table:
- "What are the busiest bike share stations in Austin by month?"
- "How do tip amounts vary by time of day for NYC taxi rides?"
- "What were the strongest hurricanes to make landfall in the last 20 years?"

Multi-table (same dataset):
- "Which bike share stations have the highest average trip duration, and where are they located?" *(trips + stations)*
- "Are there weather stations near the paths of major hurricanes?" *(hurricanes + weather_stations)*

Multi-table (cross-dataset):
- "Is there a correlation between crime rates and bike share usage near specific stations in Austin?" *(austin_crime + trips + stations)*
- "How does population density by ZIP code relate to bike share station placement in Austin?" *(population_by_zip_2010 + stations)*
- "Which US counties have the most weather stations per capita?" *(us_counties + weather_stations + population_by_zip_2010)*

### 6. Run the benchmark

The rigorous, statistically-grounded comparison lives in [`examples/`](examples/) — the factorial experiment described in **The Experiment** above. It runs each approach in isolation across all four tiers and n replicate runs, then scores graded recall, rank-aware metrics, precision-with-distractors, latency, and cost. See [`examples/README.md`](examples/README.md) for details and [`examples/results.md`](examples/results.md) for the report:

```bash
uv run python examples/run_questions.py --runs 2 --id single-q1   # quick smoke
uv run python examples/run_questions.py                            # full n=5 factorial
uv run python examples/run_questions.py --resume                   # skip completed cells
uv run python examples/build_results.py                            # score → report + plots
```

## Results

<!-- RESULTS:START (generated by build_results.py) -->

_Auto-generated by `examples/build_results.py` — do not edit between the markers._

**Scoped semantic search retrieves the right tables; the reranker adds precision, not recall.** With the corrected scoped query (a bare `parent:datasets/…` predicate), search returns a small, already-ranked, in-scope set holding every must-have table for nearly all multi-table questions **before any rerank**. `Search Direct` (search order, no rerank) vs `KC Search` (rerank on the identical retrieval) measures the reranker's marginal value directly. This matters at scale: past a few dozen tables the whole-corpus shortcut closes and search recall becomes the pipeline's hard ceiling — the reranker can raise precision, never recall.

| Approach | Discovery recall | Final recall | Rerank loss |
|---|---|---|---|
| 1: BQ Tools (control) | 1.000 | 0.993 | 0.007 |
| 2: KC Search | 0.967 | 0.949 | 0.018 |
| 3: KC Context | 1.000 | 0.940 | 0.060 |
| 4: Pre-Filter | 1.000 | 0.976 | 0.024 |
| 5: Semantic | 0.967 | 0.945 | 0.022 |
| 6: Search Direct (control) | 0.967 | 0.967 | 0.000 |

Means across all questions × tiers × runs (medians saturate at 100% on this corpus). Full tables, plots, per-category breakdown, cost/latency, and the one residual relevance gap: [`examples/results.md`](examples/results.md).

<!-- RESULTS:END -->

## Cleanup

Delete all BQ datasets, views, profile scans, glossary, and entry links:

```bash
uv run python scripts/cleanup.py
# or: make cleanup
```

## Configuration

### `.env` — Environment variables

| Variable | Default | Description |
|---|---|---|
| `GOOGLE_CLOUD_PROJECT` | — | Your GCP project ID (required) |
| `GOOGLE_CLOUD_LOCATION` | `us-central1` | Default GCP region |
| `AGENT_MODEL` | `gemini-3.6-flash` | LLM for agent reasoning |
| `AGENT_MODEL_LOCATION` | — | Vertex AI endpoint region for agent model (e.g., `global`) |
| `TOOL_MODEL` | `gemini-3.5-flash-lite` | LLM for reranker structured output |
| `TOOL_MODEL_LOCATION` | — | Vertex AI endpoint region for tool model (e.g., `global`) |
| `BQ_LOCATION` | `US` | BigQuery dataset location (multi-region) |
| `DATAPLEX_LOCATION` | `us-central1` | Knowledge Catalog regional location for DataScans, glossary, and entry links (used by setup/cleanup scripts) |
| `TOP_K` | `5` | Default max tables in reranker output |
| `RESOURCE_PREFIX` | `bigquery_context` | Prefix for created tier datasets |
| `ACTIVE_TIER` | `3` | Which single tier dataset (`{prefix}_tier{N}`) is in scope. The notebook / `adk web` story uses the fully-enriched tier 3; the benchmark sets this per run. |

### `config.py` — Agent configuration

Pure data module used by the ADK agents. `SCOPE` defines what agents search within — each entry is either a bare dataset name (all tables) or `dataset.table` (specific table). Agents discover metadata at runtime. No SDK imports.

`SCOPE` resolves to the **single** `{prefix}_tier{ACTIVE_TIER}` dataset. This is correctness-critical: every tier dataset holds identically-named tables and downstream scoring matches on short table name, so scope must resolve to exactly one tier or candidates collide across tiers. `set_active_tier(tier)` repoints scope (the benchmark calls it per tier; `context_cache.repopulate_for_tier` wraps it and rebuilds the cache). To point the agents at your own tables instead, override `SCOPE` directly:

```python
SCOPE = [
    "my_dataset",                # all tables in this dataset
    "other_dataset.specific_tbl", # only this table
]
```

### `schemas.py` — Reranker output schema

`RerankerResponse` is the Pydantic schema shared by all six approaches (Approach 6 builds it directly from search order instead of from the reranker). Each ranked table includes:
- `table_id`, `rank`, `confidence`, `reasoning`
- `key_columns` with data types and filtering/aggregation hints
- `sql_hints` with concrete SQL patterns
- `join_suggestions` for multi-table queries
- `discovery_method` identifying which approach found it

## Caveats and Future Directions

### Current limitations

- **`lookup_context` is preview**: The Knowledge Catalog `lookup_context` API (SDK `CatalogServiceClient.lookup_context`, `google-cloud-dataplex` >=2.20.0) is in **preview**. Two request details are not fully documented and are handled defensively in code: the context-budget option key (`context_budget` vs `budget` — omitted here for the full capsule) and the `guidelines` aspect field schema (introspected at runtime, with the `overview` aspect as a fallback).

- **Search is project-scoped**: `search_entries` with semantic search only finds entries in the caller's project's Knowledge Catalog. This is why setup creates views in your project — without them, public dataset tables would not be discoverable via approach 2.

- **`lookup_context` richness depends on enrichment**: The `lookup_context` API returns whatever metadata exists in the catalog. Without enrichment, you get schema only (~600 chars/table). With profiling you get column statistics and sample values (~5,500 chars/table in JSON); glossary terms and guidelines add business context on top. The setup script's enrichment matrix demonstrates the full range.

- **Glossary and DataScans require a regional location**: Data profile scans and business glossaries require a regional location (e.g., `us-central1`), not a multi-region like `US`. The BQ datasets are in `US`, but these catalog resources are created in `DATAPLEX_LOCATION`. This works fine.

### Why direct API calls instead of MCP Toolbox?

This project calls BigQuery and Knowledge Catalog APIs directly to keep the focus on **what each API provides** — the six approaches are a teaching tool for understanding the metadata landscape, not a production architecture.

The [MCP Toolbox for Databases](https://googleapis.github.io/genai-toolbox/) is the production-grade alternative. It wraps BigQuery and Knowledge Catalog APIs behind a single MCP server and offers several advantages over our approach:

| Capability | This project | MCP Toolbox |
|---|---|---|
| **Dataset scoping** | `after_tool_callback` prunes results client-side | [`allowedDatasets`](https://googleapis.github.io/genai-toolbox/resources/sources/bigquery/) in YAML — enforced server-side |
| **Catalog search** | Custom `FunctionTool` calling `search_entries` | Prebuilt [`dataplex-search-entries`](https://googleapis.github.io/genai-toolbox/resources/tools/dataplex/dataplex-search-entries/) tool with scope filtering |
| **Catalog lookup** | Custom `FunctionTool` calling `lookup_entry` | Prebuilt [`dataplex-lookup-entry`](https://googleapis.github.io/genai-toolbox/resources/tools/dataplex/dataplex-lookup-entry/) tool |
| **Context lookup** | Custom cache calling `lookup_context` | Prebuilt [`dataplex-lookup-context`](https://googleapis.github.io/genai-toolbox/resources/tools/dataplex/) tool (capsule with profiling + enrichments) |
| **Write protection** | `WriteMode.BLOCKED` on BigQueryToolset | `writeMode: "blocked"` with SQL dry-run validation |
| **Framework coupling** | Tightly coupled to ADK callbacks | Framework-independent — works with ADK, LangGraph, Claude, any MCP client |
| **Configuration** | Scoping logic spread across Python callbacks | Centralized in one `tools.yaml` file |

ADK connects to MCP Toolbox via [`ToolboxToolset`](https://google.github.io/adk-docs/integrations/mcp-toolbox-for-databases/) (native HTTP) or [`MCPToolset`](https://google.github.io/adk-docs/tools-custom/mcp-tools/) (stdio/SSE), and the server can run locally or on [Cloud Run](https://googleapis.github.io/genai-toolbox/how-to/deploy_toolbox/).

MCP Toolbox now exposes a `lookup_context` tool, so the capsule-based approaches (3, 4, 5) can be reproduced against a managed server rather than the custom cache used here. The value of this project is in showing the raw API surface behind that tool and how enrichment tiers change what it returns.

### Future directions

- **Richer Knowledge Context**: As more organizations run profiling and enrichment, `lookup_context` capsules increasingly include glossary terms, join patterns, guidelines, and usage statistics — the "tribal knowledge" that makes AI-generated SQL significantly more accurate. The enrichment matrix in this project demonstrates that effect directly.

## Project Structure

```
bigquery-context/
├── .env                              # Environment configuration
├── config.py                         # Central scope + settings
├── schemas.py                        # Pydantic: RerankerResponse
├── discovery_common.py               # Shared search/rerank/emit helpers (approaches 2, 5, 6)
├── bigquery_context.ipynb            # Step-by-step notebook walkthrough
├── pyproject.toml                    # uv-managed dependencies
├── Makefile                          # install, setup, cleanup, test
├── readme.md
│
├── scripts/
│   ├── setup.py                      # Create BQ datasets, views, enrichment matrix
│   └── cleanup.py                    # Delete everything
│
├── context_cache/                    # Shared context cache (approaches 3, 4, 5)
│   ├── __init__.py                   # Public API: get_all_briefs, get_detailed_for_tables, etc.
│   ├── cache.py                      # Cache population + brief/detailed views
│   └── util_lookup_context.py        # SDK client for lookup_context (preview)
│
├── reranker/                         # Shared reranker tool
│   ├── __init__.py
│   ├── function_tool_rerank.py       # ADK tool: Gemini structured output
│   └── util_rerank.py                # Reranker prompt + API call
│
├── agent_bq_tools/                   # Approach 1: BQ metadata enumeration
│   ├── __init__.py
│   ├── agent.py
│   ├── callback_filter_scope.py      # after_tool_callback: scope filtering
│   └── prompts.py
│
├── agent_kc_search/                  # Approach 2: Knowledge Catalog semantic search
│   ├── __init__.py
│   ├── agent.py
│   ├── prompts.py
│   └── tools/
│       ├── __init__.py
│       └── callback_discover_and_rerank.py
│
├── agent_kc_context/                 # Approach 3: Knowledge Catalog Context capsules
│   ├── __init__.py
│   ├── agent.py
│   ├── prompts.py
│   └── tools/
│       ├── __init__.py
│       └── callback_discover_and_rerank.py
│
├── agent_context_prefilter/          # Approach 4: LLM pre-filter + rerank
│   ├── __init__.py
│   ├── agent.py
│   ├── prompts.py
│   └── tools/
│       ├── __init__.py
│       ├── function_tool_nominate_tables.py
│       └── callback_rerank_nominations.py
│
├── agent_semantic_context/           # Approach 5: Semantic search + cached context
│   ├── __init__.py
│   ├── agent.py
│   ├── prompts.py
│   └── tools/
│       ├── __init__.py
│       └── callback_discover_and_rerank.py
│
├── agent_search_direct/              # Approach 6: Semantic search as discovery AND rank (no reranker)
│   ├── __init__.py
│   ├── agent.py
│   ├── prompts.py
│   └── tools/
│       ├── __init__.py
│       └── callback_search_direct.py
│
├── agent_orchestrator/               # Root: parallel fan-out + compare
│   ├── __init__.py
│   ├── agent.py
│   ├── prompts.py
│   └── callback_build_comparison.py  # before_agent_callback: builds cross-approach summary
│
└── examples/                         # Factorial NL2SQL retrieval benchmark
    ├── README.md                     # How to run the benchmark and read the report
    ├── questions.json                # 25 questions with graded relevance
    ├── GROUND_TRUTH.md               # Corpus + grading rubric (must/nice/distractor)
    ├── run_questions.py              # Factorial harness: approach × tier × question × run
    ├── build_results.py              # Score, compute stats, render plots + report
    ├── results.md                    # Generated report
    └── results/
        ├── results.json             # Raw approach-run cells (auto-generated)
        └── plots/                   # Generated PNG plots (auto-generated)
```
