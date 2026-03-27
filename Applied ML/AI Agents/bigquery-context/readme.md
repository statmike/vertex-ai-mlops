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
</table><br/><br/>

---
# BigQuery Context — Five Approaches to Table Discovery

An [ADK](https://google.github.io/adk-docs/) multi-agent system that demonstrates five different approaches to finding the best BigQuery tables for answering a user's question. All five approaches run in parallel and produce the same ranked output via a shared reranker, making results directly comparable.

## The Five Approaches

| # | Agent | Strategy | Per-Query Cost | Input Source |
|---|---|---|---|---|
| 1 | `agent_bq_tools` | **BQ Metadata Tools** — enumerate datasets/tables, inspect schemas | Multiple BQ API calls | ADK [BigQueryToolset](https://google.github.io/adk-docs/tools/built-in-tools.html#bigquery-tools) |
| 2 | `agent_dataplex_search` | **Dataplex Search** — semantic natural language search | `search_entries` + `lookup_entry` | Dataplex [Catalog Search](https://cloud.google.com/dataplex/docs/search-for-resources) API |
| 3 | `agent_dataplex_context` | **Dataplex Context** — pre-loaded LLM-ready capsules | Zero (cached at init) | Dataplex [lookupContext](https://cloud.google.com/dataplex/docs/reference/rest/v1/projects.locations/lookupContext) REST API |
| 4 | `agent_context_prefilter` | **Context Pre-Filter** — LLM reviews brief summaries, nominates candidates | Zero discovery (cached briefs) | Shared context cache (brief view) |
| 5 | `agent_semantic_context` | **Semantic Context** — semantic search + cached context lookup | 1 `search_entries` + 0 lookups | Dataplex search + shared context cache (detailed view) |

### How It Works

```
User question
    │
    ▼
SequentialAgent (orchestrator)
    │
    ├──▶ ParallelAgent ──────────────────────────────────────────────────┐
    │       │                                                            │
    │       ├── agent_bq_tools (LLM-driven, scope-filtered)               │
    │       │     LLM reasoning loop:                                    │
    │       │       list_dataset_ids → list_table_ids → get_table_info   │
    │       │       → rerank_tables tool (calls call_reranker)           │
    │       │     after_tool_callback: prunes list results to SCOPE      │
    │       │                                                            │
    │       ├── agent_dataplex_search (callback-driven, deterministic)    │
    │       │     before_agent_callback:                                  │
    │       │       search_entries (semantic) → lookup_entry per table    │
    │       │       → call_reranker → return Content (LLM skipped)       │
    │       │                                                            │
    │       ├── agent_dataplex_context (callback-driven, deterministic)  │
    │       │     before_agent_callback:                                  │
    │       │       read shared cache (pre-fetched at startup)            │
    │       │       → call_reranker → return Content (LLM skipped)       │
    │       │                                                            │
    │       ├── agent_context_prefilter (LLM + callback hybrid)          │
    │       │     LLM reviews brief summaries → calls nominate_tables    │
    │       │     after_agent_callback:                                   │
    │       │       get detailed cache for nominees → call_reranker       │
    │       │                                                            │
    │       └── agent_semantic_context (callback-driven, deterministic)  │
    │             before_agent_callback:                                  │
    │               search_entries (semantic) → cache lookup per match    │
    │               → call_reranker → return Content (LLM skipped)       │
    │                                                                    │
    │    ◀──────────────────────────────────────────────────────────────┘
    │
    └──▶ compare_results (LLM synthesizes all five from state)
```

All five approaches use the same `call_reranker` function (Gemini structured output) to produce a `RerankerResponse` with ranked tables, confidence scores, column hints, and SQL suggestions. Approaches 2, 3, and 5 run entirely in `before_agent_callback` — no LLM agent calls needed. Approach 4 uses LLM reasoning to review brief summaries and nominate candidates, with deterministic reranking in `after_agent_callback`. Approach 1 uses LLM reasoning to iterate through BigQuery metadata tools. All five enforce `config.SCOPE` programmatically: approaches 2–5 filter during discovery, while approach 1 uses an `after_tool_callback` to prune `list_dataset_ids` and `list_table_ids` results so the LLM never sees out-of-scope resources.

Approaches 3, 4, and 5 share a **context cache** (`context_cache/`) that pre-fetches metadata for all in-scope tables at startup. The cache provides two views: **brief** summaries (description + column names/types + row count) for LLM pre-filtering, and **detailed** YAML capsules (from `lookupContext`) for reranking.

### Detailed Approach Flows

#### Approach 1: BQ Metadata Tools — step-by-step

The agent LLM drives the discovery loop, deciding which datasets to explore and which tables to inspect:

1. **LLM calls `list_dataset_ids`** → BQ API returns all project datasets → `after_tool_callback` (`filter_scope`) prunes to `config.SCOPE` datasets → LLM sees only in-scope datasets
2. **LLM calls `list_table_ids`** per dataset → BQ API returns all tables → `filter_scope` prunes to scoped tables (via `get_scoped_tables`) → LLM sees filtered list
3. **LLM calls `get_table_info`** per relevant table → returns full schema (columns, types, modes), description, row count, byte sizes, timestamps — schema only, no column descriptions or profile data
4. **LLM calls `rerank_tables` tool** → passes question + all gathered metadata as a formatted string → tool calls `call_reranker()` via thread pool → Gemini structured output → `RerankerResponse` stored in `state["reranker_result_bq_tools"]`
5. **LLM formats final response** using reranker results

Key characteristics:
- **LLM-driven**: the agent decides which datasets to explore, which tables to inspect, when to call the reranker
- **Variable API calls**: 4–10+ BQ API calls depending on exploration depth
- **Scope enforcement**: deterministic `after_tool_callback` — LLM never sees out-of-scope resources
- **Metadata richness**: schema only (no profiling, no sample values)
- **Reranker invocation**: called as an ADK tool by the LLM

#### Approach 2: Dataplex Search — step-by-step

The entire flow runs in `before_agent_callback` — the agent LLM is never invoked:

1. **Extract question** from `callback_context.user_content`
2. **`search_entries`** — semantic search via `dataplex_v1.CatalogServiceClient` with `query="({question}) AND system=BIGQUERY"`, `page_size=20`, `semantic_search=True`, location `global` → returns up to 20 semantically matched entries with entry name, fully qualified name, display name, and description
3. **Scope filter** — parse `fully_qualified_name`, call `is_table_in_scope(dataset, table)`, skip non-matching entries
4. **`lookup_entry`** per matching table — `EntryView.FULL` → returns schema (columns, types), display name, description, and catalog aspects (richer than BQ `get_table_info` because Dataplex includes catalog metadata)
5. **`call_reranker()`** — direct function call via `asyncio.to_thread` (not a tool call) → Gemini structured output → `RerankerResponse` stored in `state["reranker_result_dataplex_search"]`
6. **Return `types.Content`** with formatted markdown → agent LLM skipped entirely

Key characteristics:
- **Deterministic**: entire flow runs in callback, zero LLM reasoning
- **Per-query cost**: 1 `search_entries` + N `lookup_entry` calls (N = in-scope matches from up to 20 results)
- **Semantic matching**: Dataplex ranks results by semantic relevance to the question
- **Scope filtering happens post-search**: Dataplex `semantic_search` doesn't support `linked_resource` filters, so filtering is applied after results are returned
- **Reranker invocation**: called as a direct function, not as an ADK tool

#### Approach 3: Dataplex Context — step-by-step

Two phases: startup pre-fetch (shared cache) + per-query callback.

**Startup (shared context cache — `context_cache/`):**
1. **Build table list** from `config.SCOPE` — for bare datasets, enumerate tables via BQ API; for specific `dataset.table` entries, use directly
2. **Build Dataplex entry names** for each dataset and table
3. **`bq_client.get_table()`** per table → build **brief** summary (description + column names/types + row count)
4. **`lookupContext` REST API** for dataset-level entries (batched) and each table entry — URL: `dataplex.googleapis.com/v1/projects/{project}/locations/{location}:lookupContext` — request payload includes entry names and `format: "YAML"` — batch limit of 10 entries per API call → stored as **detailed** YAML
5. **Cache** in module-level `_CACHE` dict keyed by `project.dataset.table` — each entry has `brief` and `detailed` views — returns YAML-formatted metadata including schema, descriptions, and data profile statistics (sample values, null ratios, cardinality) when profiling has been run

The shared cache is used by approaches 3, 4, and 5 — populated once at startup.

**Per-query (`before_agent_callback`):**
1. **Extract question** from callback context
2. **Read `get_all_detailed()`** from the shared cache — instant, zero API calls
3. **`call_reranker()`** — direct function call via `asyncio.to_thread` → passes full cached context as `candidate_metadata` → Gemini structured output → `RerankerResponse` stored in `state["reranker_result_dataplex_context"]`
4. **Return `types.Content`** → agent LLM skipped

Key characteristics:
- **Zero per-query API calls** — all context pre-fetched at startup via shared cache
- **Richest metadata**: YAML capsules include data profile statistics when profiling has run (~3,500+ chars per table vs ~600 without profiling)
- **`lookupContext` is a REST call** — not yet in the `google-cloud-dataplex` Python SDK (v2.16.0)
- **Batch limit**: 10 entries per API call

#### Approach 4: Context Pre-Filter — step-by-step

LLM-driven candidate selection with deterministic reranking.

1. **System prompt includes brief summaries** for all in-scope tables (from `context_cache.get_all_briefs()`) — each brief shows table description, column names/types, and row count
2. **LLM reviews briefs** and calls `nominate_tables(table_ids=[...])` tool — selects tables it believes are relevant based on column names, descriptions, and the user's question
3. **`nominate_tables` tool** stores `table_ids` list in `tool_context.state["nominated_tables"]`
4. **`after_agent_callback`** (`rerank_nominations`):
   - Reads `state["nominated_tables"]`
   - Calls `context_cache.get_detailed_for_tables(table_ids)` to get full YAML for nominated tables only
   - Calls `call_reranker()` via `asyncio.to_thread` → `RerankerResponse` stored in `state["reranker_result_context_prefilter"]`
   - Does not return Content — the LLM's response explaining its reasoning serves as the agent output

Key characteristics:
- **Hybrid**: LLM reasoning for candidate selection + deterministic reranking
- **Zero discovery API calls**: briefs come from the shared cache (pre-fetched at startup)
- **Selective metadata**: only fetches detailed context for nominated tables (not all)
- **Reranker in `after_agent_callback`**: runs exactly once after LLM finishes — guaranteed, deterministic

#### Approach 5: Semantic Context — step-by-step

Fully deterministic, runs in `before_agent_callback`:

1. **Extract question** from callback context
2. **`search_entries`** — semantic search via `dataplex_v1.CatalogServiceClient` with `query="({question}) AND system=BIGQUERY"`, `page_size=20`, `semantic_search=True` (same as Approach 2)
3. **Scope filter** — parse `fully_qualified_name`, call `is_table_in_scope(dataset, table)`, skip non-matching entries
4. **Cache lookup** — `context_cache.get_detailed_for_tables(matched_ids)` — replaces Approach 2's N `lookup_entry` API calls with a single cache lookup (zero additional API calls)
5. **`call_reranker()`** — direct function call via `asyncio.to_thread` → `RerankerResponse` stored in `state["reranker_result_semantic_context"]`
6. **Return `types.Content`** → agent LLM skipped

Key characteristics:
- **Deterministic**: entire flow runs in callback, zero LLM reasoning
- **Per-query cost**: 1 `search_entries` + 0 additional API calls (cache replaces `lookup_entry`)
- **Richer metadata than Approach 2**: cache contains full YAML with profiling stats (vs Approach 2's schema-only JSON from `lookup_entry`)
- **Semantic matching**: same Dataplex semantic search as Approach 2 for candidate narrowing

#### Shared Reranker — the bridge to downstream

All five approaches converge on the same reranker, which bridges discovery and downstream use (SQL generation or Conversational Analytics API):

- **Model**: `TOOL_MODEL` (default `gemini-2.5-flash`) at temperature 0.1
- **Input**: question + `candidate_metadata` string + `discovery_method` + `top_k` (default 5)
- **Output**: `RerankerResponse` via Gemini structured output — not just "which tables" but actionable context:
  - `ranked_tables` — each with `confidence` (0.0–1.0), `reasoning`, and `table_description`
  - `key_columns` — each with `data_type`, `is_key`, `useful_for_filtering`, `useful_for_aggregation`
  - `sql_hints` — concrete SQL patterns (GROUP BY, WHERE, JOINs, etc.)
  - `join_suggestions` — each with `target_table`, `join_keys`, and `relationship` type
- **State storage**: `state[f"reranker_result_{discovery_method}"]` — read by the compare agent
- **Downstream handoff**: the reranker output is designed to be passed directly to a SQL generation agent or the Conversational Analytics API — it provides the table context needed to write accurate queries

#### Comparison Table

| Dimension | Approach 1: BQ Tools | Approach 2: Dataplex Search | Approach 3: Dataplex Context | Approach 4: Context Pre-Filter | Approach 5: Semantic Context |
|---|---|---|---|---|---|
| **Execution model** | LLM-driven (`Agent` with tools) | Deterministic (`before_agent_callback`) | Deterministic (`before_agent_callback`) | Hybrid (LLM + `after_agent_callback`) | Deterministic (`before_agent_callback`) |
| **Per-query API calls** | 4–10+ BQ API calls | 1 `search_entries` + N `lookup_entry` | 0 (shared cache) | 0 (shared cache) | 1 `search_entries` + 0 (shared cache) |
| **Discovery mechanism** | Enumerate datasets → tables → schemas | Semantic search over Dataplex catalog | Read all from shared cache | LLM reviews briefs, nominates candidates | Semantic search → cache lookup |
| **Results retrieved** | All tables in scoped datasets | Up to 20 semantic matches | All in-scope tables (cached) | LLM-selected subset of all cached tables | Up to 20 semantic matches (cached metadata) |
| **Scope enforcement** | `after_tool_callback` prunes API results | `is_table_in_scope()` post-search filter | Built into cache (only fetches scoped entries) | Built into cache | `is_table_in_scope()` + cache |
| **Metadata richness** | Schema only (columns, types, modes) | Schema + catalog aspects | Schema + catalog + data profile statistics | Brief for selection, detailed for reranking | Schema + catalog + data profile statistics |
| **Reranker invocation** | ADK tool call (LLM decides when) | Direct function call in callback | Direct function call in callback | Direct function call in `after_agent_callback` | Direct function call in callback |
| **Determinism** | Non-deterministic (LLM chooses exploration path) | Deterministic | Deterministic | Hybrid (LLM selects, reranker deterministic) | Deterministic |
| **Latency profile** | Highest (LLM reasoning + sequential API calls) | Medium (semantic search + lookups) | Lowest per-query (cached); startup cost | Medium (LLM reasoning + cache lookup) | Low (semantic search + cache lookup) |

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

This step creates example datasets and tables for the demo. If you already have BigQuery tables you want to discover, skip this step and update `SCOPE` in `config.py` to point at your own datasets/tables.

The setup script creates BigQuery datasets with views pointing to `bigquery-public-data` tables, then runs Dataplex data profile scans to enrich the catalog metadata:

```bash
uv run python scripts/setup.py
# or: make setup
```

**What setup creates:**

| Dataset | Views | Source |
|---|---|---|
| `bigquery_context_transportation` | `austin_bikeshare_trips`, `austin_bikeshare_stations`, `nyc_taxi_trips_2022` | Austin bikeshare, NYC taxi |
| `bigquery_context_weather` | `hurricanes`, `weather_stations` | NOAA hurricanes, GHCN stations |
| `bigquery_context_demographics` | `population_by_zip_2010`, `usa_names_1910_current` | US Census, SSA baby names |
| `bigquery_context_geography` | `us_counties`, `austin_crime` | US boundaries, Austin crime |

**Why views?** Views are free (zero storage cost) and place everything in your project's Dataplex catalog, so all five discovery approaches work equally. Without this, Dataplex semantic search only finds tables in your own project.

**Why profile scans?** Data profiling publishes column-level statistics (null ratios, distinct values, sample values) to the Dataplex catalog. The `lookupContext` API includes these in its response, giving the Knowledge Context approach dramatically richer metadata:
- Before profiling: ~600 chars (schema only)
- After profiling: ~3,500+ chars (schema + `dataProfile` per column)

### 4. Notebook walkthrough

Before running the agents, the [`bigquery_context.ipynb`](bigquery_context.ipynb) notebook walks through the first three approaches step-by-step — showing the raw API calls, the metadata each approach provides, and a side-by-side comparison of results. This helps you understand what each agent does under the hood.

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

## Cleanup

Delete all BQ datasets, views, and Dataplex profile scans:

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
| `DATAPLEX_LOCATION` | `us-central1` | Dataplex DataScan location (used by setup/cleanup scripts) |
| `TOP_K` | `5` | Default max tables in reranker output |
| `RESOURCE_PREFIX` | `bigquery_context` | Prefix for created datasets |

### `config.py` — Agent configuration

Pure data module used by the ADK agents. `SCOPE` defines what agents search within — each entry is either a bare dataset name (all tables) or `dataset.table` (specific table). Agents discover metadata at runtime. No SDK imports.

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

- **`lookupContext` via REST**: The Dataplex `lookupContext` API is not yet in the `google-cloud-dataplex` Python SDK (v2.16.0). We call it via REST with `google.auth` credentials. This will be updated when the SDK adds native support.

- **Dataplex search is project-scoped**: `search_entries` with semantic search only finds entries in the caller's project's Dataplex catalog. This is why setup creates views in your project — without them, public dataset tables would not be discoverable via approach 2.

- **Knowledge Context richness depends on profiling**: The `lookupContext` API returns whatever metadata exists in the Dataplex catalog. Without data profiling, you get schema only. With profiling, you get column statistics and sample values. The setup script runs profiling to demonstrate the full capability.

- **DataScan requires regional location**: Dataplex DataScan requires a regional location (e.g., `us-central1`), not a multi-region like `US`. The BQ datasets are in `US`, but the scans are created in `us-central1`. This works fine.

### Why direct API calls instead of MCP Toolbox?

This project calls BigQuery and Dataplex APIs directly to keep the focus on **what each API provides** — the three approaches are a teaching tool for understanding the metadata landscape, not a production architecture.

The [MCP Toolbox for Databases](https://googleapis.github.io/genai-toolbox/) is the production-grade alternative. It wraps BigQuery and Dataplex APIs behind a single MCP server and offers several advantages over our approach:

| Capability | This project | MCP Toolbox |
|---|---|---|
| **Dataset scoping** | `after_tool_callback` prunes results client-side | [`allowedDatasets`](https://googleapis.github.io/genai-toolbox/resources/sources/bigquery/) in YAML — enforced server-side |
| **Dataplex search** | Custom `FunctionTool` calling `search_entries` | Prebuilt [`dataplex-search-entries`](https://googleapis.github.io/genai-toolbox/resources/tools/dataplex/dataplex-search-entries/) tool with scope filtering |
| **Dataplex lookup** | Custom `FunctionTool` calling `lookup_entry` | Prebuilt [`dataplex-lookup-entry`](https://googleapis.github.io/genai-toolbox/resources/tools/dataplex/dataplex-lookup-entry/) tool |
| **Write protection** | `WriteMode.BLOCKED` on BigQueryToolset | `writeMode: "blocked"` with SQL dry-run validation |
| **Framework coupling** | Tightly coupled to ADK callbacks | Framework-independent — works with ADK, LangGraph, Claude, any MCP client |
| **Configuration** | Scoping logic spread across Python callbacks | Centralized in one `tools.yaml` file |

ADK connects to MCP Toolbox via [`ToolboxToolset`](https://google.github.io/adk-docs/integrations/mcp-toolbox-for-databases/) (native HTTP) or [`MCPToolset`](https://google.github.io/adk-docs/tools-custom/mcp-tools/) (stdio/SSE), and the server can run locally or on [Cloud Run](https://googleapis.github.io/genai-toolbox/how-to/deploy_toolbox/).

**Gap:** MCP Toolbox does not yet (03/2026) have a prebuilt tool for the Dataplex [`lookupContext`](https://cloud.google.com/dataplex/docs/reference/rest/v1/projects.locations/lookupContext) API (our Approach 3), which returns LLM-ready metadata capsules with data profiling statistics. This would still require a custom implementation.

### Future directions

- **Richer Knowledge Context**: As more organizations run Dataplex profiling and enrichment, `lookupContext` capsules will include sample queries, join patterns, and usage statistics — the "tribal knowledge" that makes AI-generated SQL significantly more accurate.

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
│   ├── setup.py                      # Create BQ datasets, views, profile scans
│   └── cleanup.py                    # Delete everything
│
├── context_cache/                    # Shared context cache (approaches 3, 4, 5)
│   ├── __init__.py                   # Public API: get_all_briefs, get_detailed_for_tables, etc.
│   ├── cache.py                      # Cache population + brief/detailed views
│   └── util_lookup_context.py        # REST client for lookupContext (SDK pending)
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
├── agent_dataplex_search/            # Approach 2: Dataplex semantic search
│   ├── __init__.py
│   ├── agent.py
│   ├── prompts.py
│   └── tools/
│       ├── __init__.py
│       ├── callback_discover_and_rerank.py
│       ├── function_tool_search_catalog.py
│       └── function_tool_lookup_entry.py
│
├── agent_dataplex_context/           # Approach 3: Dataplex Context capsules
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
└── agent_orchestrator/               # Root: parallel fan-out + compare
    ├── __init__.py
    ├── agent.py
    └── prompts.py
```
