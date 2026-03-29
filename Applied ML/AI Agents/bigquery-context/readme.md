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

An [ADK](https://google.github.io/adk-docs/) multi-agent system that demonstrates five different approaches to finding the best BigQuery tables for answering a user's question. All five approaches run in parallel and produce the same ranked output via a shared reranker, making results directly comparable.

## The Five Approaches

Each approach uses a different combination of APIs, execution patterns, and metadata richness to discover and evaluate BigQuery tables:

| # | Approach | Discovery API | Metadata API | Metadata Content | Execution Pattern | Cache Usage | Reranker Called As | Reranker Receives |
|---|---|---|---|---|---|---|---|---|
| 1 | **BQ Metadata Tools** | BQ API: `list_dataset_ids`, `list_table_ids` | BQ API: `get_table_info` | Schema (columns, types, modes), description, row count | LLM-driven tool calls | None | ADK tool (`rerank_tables`) — LLM decides when | `get_table_info` text (schema only, no `dataProfile`) |
| 2 | **Dataplex Search** | Dataplex: [`search_entries`](https://cloud.google.com/python/docs/reference/dataplex/latest/google.cloud.dataplex_v1.services.catalog_service.CatalogServiceClient#google_cloud_dataplex_v1_services_catalog_service_CatalogServiceClient_search_entries) | Dataplex: [`lookup_entry`](https://cloud.google.com/python/docs/reference/dataplex/latest/google.cloud.dataplex_v1.services.catalog_service.CatalogServiceClient#google_cloud_dataplex_v1_services_catalog_service_CatalogServiceClient_lookup_entry) | Schema, description, catalog aspects (no profiling) | `before_agent_callback` (deterministic) | None | Direct function in `before_agent_callback` | `lookup_entry` JSON (schema + aspects, no `dataProfile`) |
| 3 | **Dataplex Context** | None (all tables from cache) | Dataplex: [`lookupContext`](https://cloud.google.com/dataplex/docs/reference/rest/v1/projects.locations/lookupContext) | Schema, description, `dataProfile` (nullRatio, distinctValues, sampleValues) | `before_agent_callback` (deterministic) | `get_all_detailed()` — all tables, full JSON | Direct function in `before_agent_callback` | `lookupContext` JSON — all tables, full `dataProfile` |
| 4 | **Context Pre-Filter** | None (LLM reviews cached briefs) | Dataplex: [`lookupContext`](https://cloud.google.com/dataplex/docs/reference/rest/v1/projects.locations/lookupContext) | **Briefs**: schema without `dataProfile`; **Reranker**: full JSON with `dataProfile` | LLM tool call + `after_agent_callback` | `get_all_briefs()` → `get_detailed_for_tables()` | Direct function in `after_agent_callback` | `lookupContext` JSON — nominated tables only, full `dataProfile` |
| 5 | **Semantic Context** | Dataplex: [`search_entries`](https://cloud.google.com/python/docs/reference/dataplex/latest/google.cloud.dataplex_v1.services.catalog_service.CatalogServiceClient#google_cloud_dataplex_v1_services_catalog_service_CatalogServiceClient_search_entries) | Dataplex: [`lookupContext`](https://cloud.google.com/dataplex/docs/reference/rest/v1/projects.locations/lookupContext) | Schema, description, `dataProfile` (nullRatio, distinctValues, sampleValues) | `before_agent_callback` (deterministic) | `get_detailed_for_tables()` — matched tables only | Direct function in `before_agent_callback` | `lookupContext` JSON — matched tables only, full `dataProfile` |

### Key APIs Used

| API | SDK / Protocol | What It Returns | Used By |
|---|---|---|---|
| BQ `get_table_info` | ADK [BigQueryToolset](https://google.github.io/adk-docs/integrations/bigquery/) | Schema (column names, types, modes), description, row count | Approach 1 |
| Dataplex `search_entries` | `google-cloud-dataplex` SDK | Up to 20 semantically matched entries (name, description, entry type) | Approaches 2, 5 |
| Dataplex `lookup_entry` | `google-cloud-dataplex` SDK | Schema + catalog aspects as JSON (no data profiling stats) | Approach 2 |
| Dataplex `lookupContext` | REST API (not yet in SDK) | Schema + descriptions + `dataProfile` per column (JSON format, batch limit 10) | Approaches 3, 4, 5 (via shared cache) |

### Shared Context Cache

Approaches 3, 4, and 5 share a context cache (`context_cache/`) populated once at startup from the Dataplex [`lookupContext`](https://cloud.google.com/dataplex/docs/reference/rest/v1/projects.locations/lookupContext) REST API. The cache stores per-table metadata with two views derived from the same JSON response:

| View | Function | Content | Typical Size | Used By |
|---|---|---|---|---|
| **brief** | `get_all_briefs()` | JSON with `dataProfile` stripped — table name, description, schema columns (name, type, description only) | ~1,300 chars/table | Approach 4 (LLM pre-filtering in system prompt) |
| **detailed** | `get_all_detailed()`, `get_detailed_for_tables()` | Full JSON including `dataProfile` per column (nullRatio, distinctValues, sampleValues) | ~5,500 chars/table | Approaches 3, 4 (reranking), 5 |

Both views come from the same `lookupContext` JSON — the brief is derived by stripping the `dataProfile` section from each schema column. No separate BQ API calls are needed.

**Cache population at startup:**
1. Build table list from `config.SCOPE` — for bare datasets, enumerate tables via `bq_client.list_tables()`; for `dataset.table` entries, use directly
2. Build Dataplex entry names for each table
3. Call `lookupContext` REST API in batches per dataset (up to 10 entries per API call, JSON format)
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
    │       ├── Approach 2: Dataplex Search (deterministic callback)     │
    │       │     before_agent_callback:                                  │
    │       │       search_entries (semantic) → lookup_entry per table    │
    │       │       → call_reranker → return Content (LLM skipped)       │
    │       │                                                            │
    │       ├── Approach 3: Dataplex Context (deterministic callback)    │
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

LLM-driven discovery using ADK BigQueryToolset — no cache, no Dataplex. The agent decides which datasets to explore and which tables to inspect:

1. **`list_dataset_ids`** → `after_tool_callback` (`filter_scope`) prunes to `config.SCOPE` → LLM sees only in-scope datasets
2. **`list_table_ids`** per dataset → `filter_scope` prunes to scoped tables
3. **`get_table_info`** per table → schema (columns, types, modes), description, row count — no column descriptions, no `dataProfile`
4. **`rerank_tables`** ADK tool → LLM passes nominated table IDs → `call_reranker()` → results stored in state
5. LLM formats final response

#### Approach 2: Dataplex Search (`agent_dataplex_search`)

Deterministic `before_agent_callback` — LLM never invoked. Uses Dataplex SDK for both discovery and metadata:

1. **`search_entries`** — `CatalogServiceClient`, `semantic_search=True`, scoped via `parent:` filter, `page_size=20`
2. **Scope filter** — `is_table_in_scope()` on each match
3. **`lookup_entry`** per matched table — `EntryView.FULL` → schema, description, catalog aspects. **No `dataProfile`**
4. **`call_reranker()`** direct function call → results stored in state
5. **Return `types.Content`** → LLM skipped

This is the baseline that Approach 5 improves upon — same semantic search, but weaker metadata (`lookup_entry` vs cached `lookupContext`).

#### Approach 3: Dataplex Context (`agent_dataplex_context`)

Deterministic `before_agent_callback` — zero per-query API calls, all metadata from shared cache:

1. **`get_all_detailed()`** from cache → JSON array of ALL in-scope tables with full `dataProfile`
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
3. **`get_detailed_for_tables(matched_ids)`** — cache lookup replaces Approach 2's N `lookup_entry` calls (zero additional API calls). Full JSON with `dataProfile`
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
| **Agent** | `agent_bq_tools` | `agent_dataplex_search` | `agent_dataplex_context` | `agent_context_prefilter` | `agent_semantic_context` |
| **Execution** | LLM tool calls | `before_agent_callback` | `before_agent_callback` | LLM + `after_agent_callback` | `before_agent_callback` |
| **Discovery** | BQ: `list_dataset_ids` / `list_table_ids` | Dataplex: `search_entries` | Cache (all tables) | Cache (LLM reviews briefs) | Dataplex: `search_entries` |
| **Metadata API** | BQ: `get_table_info` | Dataplex: `lookup_entry` | Cache: `lookupContext` | Cache: brief → detailed | Cache: `lookupContext` |
| **`dataProfile`** | No | No | Yes | Briefs: no / Reranker: yes | Yes |
| **Per-query calls** | 4–10+ BQ API | 1 search + N lookups | 0 | 0 | 1 search + 0 |
| **Tables evaluated** | Scoped datasets | Up to 20 matches | All cached | LLM-selected subset | Up to 20 matches |
| **Reranker called as** | ADK tool (LLM calls) | Direct function | Direct function | Direct function | Direct function |
| **Reranker receives** | `get_table_info` text | `lookup_entry` JSON | `lookupContext` JSON (all) | `lookupContext` JSON (nominated) | `lookupContext` JSON (matched) |
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

These questions are also used as an automated benchmark in [`examples/`](examples/). The benchmark runs all 8 questions through the orchestrator using ADK's `InMemoryRunner`, scores each approach on recall/precision against expected tables, and tracks timing. See [`examples/results.md`](examples/results.md) for the latest results, or run it yourself:

```bash
uv run python examples/run_questions.py              # run all questions
uv run python examples/run_questions.py --resume      # skip already-completed
uv run python examples/build_results.py --write       # generate results.md
```

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

- **`lookupContext` richness depends on profiling**: The `lookupContext` API returns whatever metadata exists in the Dataplex catalog. Without data profiling, you get schema only (~600 chars/table). With profiling, you get column statistics and sample values (~5,500 chars/table in JSON format). The setup script runs profiling to demonstrate the full capability.

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
│       └── callback_discover_and_rerank.py
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
├── agent_orchestrator/               # Root: parallel fan-out + compare
│   ├── __init__.py
│   ├── agent.py
│   ├── prompts.py
│   └── callback_build_comparison.py  # before_agent_callback: builds cross-approach summary
│
└── examples/                         # Automated testing + results
    ├── questions.json                # Test questions with expected tables
    ├── run_questions.py              # InMemoryRunner: run all questions, collect results
    ├── build_results.py              # Generate results.md from results JSON
    └── results/
        └── results.json              # Raw per-question results (auto-generated)
```
