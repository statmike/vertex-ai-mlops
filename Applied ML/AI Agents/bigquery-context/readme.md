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
# BigQuery Context — Five Approaches to Table Discovery

An [ADK](https://google.github.io/adk-docs/) multi-agent system comparing five approaches to finding the best BigQuery tables for a natural-language question — the retrieval step of NL2SQL. All five converge on the **same shared reranker**, so their outputs are directly comparable. It works two ways: an interactive **story** (the notebook + `adk web`) and a rigorous **benchmark** (a factorial experiment in [`examples/`](examples/)) that a data platform team can trust as evidence.

> **Naming note:** Google renamed **Dataplex Universal Catalog** to **Knowledge Catalog** (April 2026). This is a branding change only — the API service, Python SDK, CLI, and IAM roles are all unchanged (`dataplex.googleapis.com`, `google-cloud-dataplex` / `dataplex_v1`, `roles/dataplex.*`). This project uses "Knowledge Catalog" in prose and code identifiers, while API-mechanic identifiers keep the `dataplex` namespace.

## The Challenge

Before an agent can write SQL, it must find the *right tables* — from tens to thousands of candidates, often with lookalike names (a taxi *zone-lookup* table vs the trips table; a *Citi Bike* stations table vs Austin's). Get retrieval wrong and the best SQL model still answers the wrong question. So: **which discovery strategy retrieves the right tables, and how much does richer catalog metadata (profiling, a business glossary, NL→SQL guidelines) actually help?**

That second half is easy to get wrong. If you enrich only some topics, "enrichment helps" is confounded with "those topics are easier." This project isolates the effect with a designed experiment.

## The Experiment

**Independent variable:** catalog **enrichment tier** — `0` schema only → `1` +profiling → `2` +glossary → `3` +guidelines.
**Held constant:** the corpus. `scripts/setup.py` replicates the **identical** 15-table corpus into one dataset per tier (`{prefix}_tier0`..`_tier3`); the datasets differ *only* in catalog enrichment. Every topic appears at every tier, so tier is decoupled from topic — the replication *is* the ablation.

**Design:** approach (5) × tier (4) × question (~18) × run (n=5), each an **isolated** approach-run (its own `InMemoryRunner`, one at a time) for clean latency and token attribution.

- `bq_tools` and `kc_search` read little/no tier enrichment → they are **enrichment-invariant controls**, isolating what enrichment adds over a schema-only baseline. On this corpus the headline turns out to be a different contrast: recall leaks at **discovery** (whether a must-have table reaches the candidate set), not at **reranking** — see **Results** below.
- Ground truth is **graded** (`must_have` / `nice_to_have` / `distractor`) and the corpus includes deliberate **distractor tables** + **trap questions**, so precision and rank-quality metrics are meaningful. See [`examples/GROUND_TRUTH.md`](examples/GROUND_TRUTH.md).
- Metrics per approach × tier (median + IQR over the 5 runs): final vs discovery recall, Recall@5, MRR, nDCG@5, precision-with-distractors, isolated latency p50/p95, and reranker token cost — sliced by question category. See [`examples/`](examples/) to run it and [`examples/results.md`](examples/results.md) for the report.

## The Five Approaches

Each approach uses a different combination of APIs, execution patterns, and metadata richness to discover and evaluate BigQuery tables:

| # | Approach | Discovery API | Metadata API | Metadata Content | Execution Pattern | Cache Usage | Reranker Called As | Reranker Receives |
|---|---|---|---|---|---|---|---|---|
| 1 | **BQ Metadata Tools** | BQ API: `list_dataset_ids`, `list_table_ids` | BQ API: `get_table_info` | Schema (columns, types, modes), description, row count | LLM-driven tool calls | None | ADK tool (`rerank_tables`) — LLM decides when | `get_table_info` text (schema only, no `dataProfile`) |
| 2 | **Knowledge Catalog Search** | KC: [`search_entries`](https://cloud.google.com/python/docs/reference/dataplex/latest/google.cloud.dataplex_v1.services.catalog_service.CatalogServiceClient#google_cloud_dataplex_v1_services_catalog_service_CatalogServiceClient_search_entries) | KC: [`lookup_entry`](https://cloud.google.com/python/docs/reference/dataplex/latest/google.cloud.dataplex_v1.services.catalog_service.CatalogServiceClient#google_cloud_dataplex_v1_services_catalog_service_CatalogServiceClient_lookup_entry) | Schema, description, catalog aspects (no profiling) | `before_agent_callback` (deterministic) | None | Direct function in `before_agent_callback` | `lookup_entry` JSON (schema + aspects, no `dataProfile`) |
| 3 | **Knowledge Catalog Context** | None (all tables from cache) | KC: [`lookup_context`](https://cloud.google.com/dataplex/docs/retrieve-data-context) *(preview)* | Schema, description, `dataProfile`, glossary terms, `frequent_joins`, guidelines | `before_agent_callback` (deterministic) | `get_all_detailed()` — all tables, full JSON | Direct function in `before_agent_callback` | capsule JSON — all tables |
| 4 | **Context Pre-Filter** | None (LLM reviews cached briefs) | KC: [`lookup_context`](https://cloud.google.com/dataplex/docs/retrieve-data-context) *(preview)* | **Briefs**: schema + enrichments, no `dataProfile`; **Reranker**: full capsule | LLM tool call + `after_agent_callback` | `get_all_briefs()` → `get_detailed_for_tables()` | Direct function in `after_agent_callback` | capsule JSON — nominated tables only |
| 5 | **Semantic Context** | KC: [`search_entries`](https://cloud.google.com/python/docs/reference/dataplex/latest/google.cloud.dataplex_v1.services.catalog_service.CatalogServiceClient#google_cloud_dataplex_v1_services_catalog_service_CatalogServiceClient_search_entries) | KC: [`lookup_context`](https://cloud.google.com/dataplex/docs/retrieve-data-context) *(preview)* | Schema, description, `dataProfile`, glossary terms, `frequent_joins`, guidelines | `before_agent_callback` (deterministic) | `get_detailed_for_tables()` — matched tables only | Direct function in `before_agent_callback` | capsule JSON — matched tables only |

### Key APIs Used

| API | SDK / Protocol | What It Returns | Used By |
|---|---|---|---|
| BQ `get_table_info` | ADK [BigQueryToolset](https://google.github.io/adk-docs/integrations/bigquery/) | Schema (column names, types, modes), description, row count | Approach 1 |
| KC `search_entries` | `google-cloud-dataplex` SDK | Up to 20 semantically matched entries (name, description, entry type) | Approaches 2, 5 |
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

### How It Works

```
User question
    │
    ▼
SequentialAgent (orchestrator)
    │
    ├──▶ ParallelAgent ──────────────────────────────────────────────────┐
    │       │                                                            │
    │       ├── Approach 1: BQ Metadata Tools (LLM-driven)              │
    │       │     LLM reasoning loop:                                    │
    │       │       list_dataset_ids → list_table_ids → get_table_info   │
    │       │       → rerank_tables (ADK tool → call_reranker)           │
    │       │     after_tool_callback: prunes list results to SCOPE      │
    │       │                                                            │
    │       ├── Approach 2: Knowledge Catalog Search (determ. callback)  │
    │       │     before_agent_callback:                                  │
    │       │       search_entries (semantic) → lookup_entry per table    │
    │       │       → call_reranker → return Content (LLM skipped)       │
    │       │                                                            │
    │       ├── Approach 3: Knowledge Catalog Context (determ. callback) │
    │       │     before_agent_callback:                                  │
    │       │       get_all_detailed() from cache → call_reranker        │
    │       │       → return Content (LLM skipped)                       │
    │       │                                                            │
    │       ├── Approach 4: Context Pre-Filter (LLM + callback hybrid)  │
    │       │     System prompt embeds get_all_briefs() from cache        │
    │       │     LLM reviews briefs → calls nominate_tables tool        │
    │       │     after_agent_callback:                                   │
    │       │       get_detailed_for_tables() → call_reranker            │
    │       │                                                            │
    │       └── Approach 5: Semantic Context (deterministic callback)    │
    │             before_agent_callback:                                  │
    │               search_entries (semantic) → get_detailed_for_tables() │
    │               → call_reranker → return Content (LLM skipped)       │
    │                                                                    │
    │    ◀──────────────────────────────────────────────────────────────┘
    │
    └──▶ compare_results (LLM synthesizes all five from state)
```

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

1. **`search_entries`** — `CatalogServiceClient`, `semantic_search=True`, scoped via `parent:` filter, `page_size=20`
2. **Scope filter** — `is_table_in_scope()` on each match
3. **`lookup_entry`** per matched table — `EntryView.FULL` → schema, description, catalog aspects. **No `dataProfile`**
4. **`call_reranker()`** direct function call → results stored in state
5. **Return `types.Content`** → LLM skipped

This is the baseline that Approach 5 improves upon — same semantic search, but weaker metadata (`lookup_entry` vs cached `lookup_context`).

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

#### Shared Reranker

All five approaches converge on `call_reranker()` (Gemini structured output → `RerankerResponse`):

- **Input**: question + `candidate_metadata` string + `discovery_method` + `top_k`
- **Output**: `ranked_tables` with confidence scores, `key_columns` with filtering/aggregation hints, `sql_hints`, and `join_suggestions`
- **State**: each approach stores `nominated_tables_{method}` and `reranker_result_{method}` — read by the compare agent
- **Invocation**: Approach 1 calls it as an ADK tool (LLM decides when); Approaches 2–5 call it as a direct function in callbacks

#### Full Comparison

| Dimension | Approach 1 | Approach 2 | Approach 3 | Approach 4 | Approach 5 |
|---|---|---|---|---|---|
| **Agent** | `agent_bq_tools` | `agent_kc_search` | `agent_kc_context` | `agent_context_prefilter` | `agent_semantic_context` |
| **Execution** | LLM tool calls | `before_agent_callback` | `before_agent_callback` | LLM + `after_agent_callback` | `before_agent_callback` |
| **Discovery** | BQ: `list_dataset_ids` / `list_table_ids` | KC: `search_entries` | Cache (all tables) | Cache (LLM reviews briefs) | KC: `search_entries` |
| **Metadata API** | BQ: `get_table_info` | KC: `lookup_entry` | Cache: `lookup_context` | Cache: brief → detailed | Cache: `lookup_context` |
| **`dataProfile`** | No | No | Yes | Briefs: no / Reranker: yes | Yes |
| **Per-query calls** | 4–10+ BQ API | 1 search + N lookups | 0 | 0 | 1 search + 0 |
| **Tables evaluated** | Scoped datasets | Up to 20 matches | All cached | LLM-selected subset | Up to 20 matches |
| **Reranker called as** | ADK tool (LLM calls) | Direct function | Direct function | Direct function | Direct function |
| **Reranker receives** | `get_table_info` text | `lookup_entry` JSON | capsule JSON (all) | capsule JSON (nominated) | capsule JSON (matched) |
| **Deterministic** | No | Yes | Yes | Hybrid | Yes |
| **Latency** | Highest | Medium | Lowest | Medium | Low |

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

The corpus (15 tables), glossary terms, and guideline text are authored **once** in `scripts/setup.py` (`CORPUS`, `GLOSSARY_TERMS`, `GUIDELINES`) — the single source of truth, imported by `cleanup.py` and the benchmark so nothing drifts. It spans transportation, weather, demographics, geography, and health-by-geography tables, plus **3 deliberate distractor tables** (`taxi_zone_geom`, `citibike_stations`, `unemployment_cps`) that look relevant by name but are never a correct answer. See [`examples/GROUND_TRUTH.md`](examples/GROUND_TRUTH.md) for the full corpus and grading rubric.

**Why replicate ×4?** Enrichment tier is the independent variable. Holding the corpus identical across tiers decouples "enrichment helps" from "some topics are easier." Because every tier dataset holds identically-named tables and scoring matches on short table name, **each benchmark run is scoped to exactly one tier dataset** (`config.ACTIVE_TIER`) — see the Configuration section.

**Why views?** Views are free (zero storage cost) and place everything in your project's Knowledge Catalog, so all five discovery approaches work equally. Without this, semantic search only finds tables in your own project.

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

This opens a browser-based chat interface. Use the agent selector dropdown (top-left) to choose which agent to run — `agent_orchestrator` runs all five in parallel, or pick any individual approach to run it standalone.

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

**Recall leaks at discovery, not reranking.** The reranker almost never drops a must-have table that discovery surfaced; the search-based approaches are capped because semantic search leaves join-partner tables out of the candidate set entirely — for **two distinct reasons**: a *relevance gap* on disparate joins (the partner shares no term with the question) and a *scope leak* on related joins (the `parent:` filter, enforceable on its own, is relaxed when combined with a free-text question under semantic search, so unrelated-dataset tables fill the page budget and crowd the in-scope partner out).

| Approach | Discovery recall | Final recall | Rerank loss |
|---|---|---|---|
| 1: BQ Tools (control) | 1.000 | 0.997 | 0.003 |
| 2: KC Search (control) | 0.884 | 0.884 | 0.000 |
| 3: KC Context | 1.000 | 0.962 | 0.038 |
| 4: Pre-Filter | 1.000 | 0.990 | 0.010 |
| 5: Semantic | 0.884 | 0.874 | 0.010 |

**Why it matters at scale:** on a small corpus you route around search by feeding the whole corpus to the reranker — which is why enrichment tier does not move recall here. At thousands of tables that escape hatch closes: search *must* subset before reranking, so search recall becomes the pipeline's hard ceiling (the reranker can raise precision, never recall). The two mechanisms need different fixes, and one gates the other: **make the `parent:` scope predicate bind under semantic search** (a precondition — it is enforceable alone but relaxed once combined with a free-text question, and while that holds a wider page just admits more pollution) and add a **query-decomposition front-end that fans out into multiple targeted searches** for the relevance gap — plus a catalog-native option: join-aware search expansion via `frequent_joins`.

Means across all questions × tiers × runs (medians saturate at 100% on this corpus). Worked example, scale discussion, full tables, plots, enrichment-response curves, per-category breakdown, cost/latency, and paired CIs: [`examples/results.md`](examples/results.md).

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
| `AGENT_MODEL` | `gemini-2.5-flash` | LLM for agent reasoning |
| `AGENT_MODEL_LOCATION` | — | Vertex AI endpoint region for agent model (e.g., `global`) |
| `TOOL_MODEL` | `gemini-2.5-flash` | LLM for reranker structured output |
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

`RerankerResponse` is the Pydantic schema shared by all five approaches. Each ranked table includes:
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

This project calls BigQuery and Knowledge Catalog APIs directly to keep the focus on **what each API provides** — the five approaches are a teaching tool for understanding the metadata landscape, not a production architecture.

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
│       ├── callback_discover_and_rerank.py
│       └── function_tool_initialize_context.py
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
├── agent_orchestrator/               # Root: parallel fan-out + compare
│   ├── __init__.py
│   ├── agent.py
│   ├── prompts.py
│   └── callback_build_comparison.py  # before_agent_callback: builds cross-approach summary
│
└── examples/                         # Factorial NL2SQL retrieval benchmark
    ├── README.md                     # How to run the benchmark and read the report
    ├── questions.json                # ~18 questions with graded relevance
    ├── GROUND_TRUTH.md               # Corpus + grading rubric (must/nice/distractor)
    ├── run_questions.py              # Factorial harness: approach × tier × question × run
    ├── build_results.py              # Score, compute stats, render plots + report
    ├── results.md                    # Generated report
    └── results/
        ├── results.json             # Raw approach-run cells (auto-generated)
        └── plots/                   # Generated PNG plots (auto-generated)
```
