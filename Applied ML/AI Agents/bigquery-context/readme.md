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
# BigQuery Context — Three Approaches to Table Discovery

An [ADK](https://google.github.io/adk-docs/) multi-agent system that demonstrates three different approaches to finding the best BigQuery tables for answering a user's question. All three approaches run in parallel and produce the same ranked output via a shared reranker, making results directly comparable.

## The Three Approaches

| # | Agent | Strategy | Per-Query Cost | Input Source |
|---|---|---|---|---|
| 1 | `agent_bq_tools` | **BQ Metadata Tools** — enumerate datasets/tables, inspect schemas | Multiple BQ API calls | ADK [BigQueryToolset](https://google.github.io/adk-docs/tools/built-in-tools.html#bigquery-tools) |
| 2 | `agent_dataplex_search` | **Dataplex Search** — semantic natural language search | `search_entries` + `lookup_entry` | Dataplex [Catalog Search](https://cloud.google.com/dataplex/docs/search-for-resources) API |
| 3 | `agent_dataplex_context` | **Dataplex Context** — pre-loaded LLM-ready capsules | Zero (cached at init) | Dataplex [lookupContext](https://cloud.google.com/dataplex/docs/reference/rest/v1/projects.locations/lookupContext) REST API |

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
    │       └── agent_dataplex_context (callback-driven, deterministic)  │
    │             before_agent_callback:                                  │
    │               read module-level cache (pre-fetched at startup)      │
    │               → call_reranker → return Content (LLM skipped)       │
    │                                                                    │
    │    ◀──────────────────────────────────────────────────────────────┘
    │
    └──▶ compare_results (LLM synthesizes all three from state)
```

All three approaches use the same `call_reranker` function (Gemini structured output) to produce a `RerankerResponse` with ranked tables, confidence scores, column hints, and SQL suggestions. Approaches 2 and 3 run entirely in `before_agent_callback` — no LLM agent calls needed — while approach 1 uses LLM reasoning to iterate through BigQuery metadata tools. All three enforce `config.SCOPE` programmatically: approaches 2 and 3 filter during discovery, while approach 1 uses an `after_tool_callback` to prune `list_dataset_ids` and `list_table_ids` results so the LLM never sees out-of-scope resources.

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

**Why views?** Views are free (zero storage cost) and place everything in your project's Dataplex catalog, so all three discovery approaches work equally. Without this, Dataplex semantic search only finds tables in your own project.

**Why profile scans?** Data profiling publishes column-level statistics (null ratios, distinct values, sample values) to the Dataplex catalog. The `lookupContext` API includes these in its response, giving the Knowledge Context approach dramatically richer metadata:
- Before profiling: ~600 chars (schema only)
- After profiling: ~3,500+ chars (schema + `dataProfile` per column)

### 4. Notebook walkthrough

Before running the agents, the [`bigquery_context.ipynb`](bigquery_context.ipynb) notebook walks through all three approaches step-by-step — showing the raw API calls, the metadata each approach provides, and a side-by-side comparison of results. This helps you understand what each agent does under the hood.

### 5. Run the agents

**Interactive web UI (recommended):**

```bash
uv run adk web agent_orchestrator
```

This opens a browser-based chat interface where you can interact with the agents, see tool calls in real time, and inspect state.

**CLI (headless):**

```bash
uv run adk run agent_orchestrator
```

Or run individual approaches:

```bash
uv run adk web agent_bq_tools              # Interactive
uv run adk run agent_bq_tools              # CLI
uv run adk web agent_dataplex_search
uv run adk run agent_dataplex_search
uv run adk web agent_dataplex_context
uv run adk run agent_dataplex_context
```

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

`RerankerResponse` is the Pydantic schema shared by all three approaches. Each ranked table includes:
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
│       ├── function_tool_initialize_context.py
│       └── util_lookup_context.py    # REST client (SDK pending)
│
└── agent_orchestrator/               # Root: parallel fan-out + compare
    ├── __init__.py
    ├── agent.py
    └── prompts.py
```
