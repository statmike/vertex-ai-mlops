# BigQuery Context — Three Approaches to Table Discovery

An [ADK](https://google.github.io/adk-docs/) multi-agent system that demonstrates three different approaches to finding the best BigQuery tables for answering a user's question. All three approaches run in parallel and produce the same ranked output via a shared reranker, making results directly comparable.

## The Three Approaches

| # | Agent | Strategy | Per-Query Cost | Input Source |
|---|---|---|---|---|
| 1 | `agent_bq_tools` | **BQ Metadata Tools** — enumerate datasets/tables, inspect schemas | Multiple BQ API calls | ADK `BigQueryToolset` |
| 2 | `agent_catalog_search` | **Dataplex Catalog Search** — semantic natural language search | `search_entries` + `lookup_entry` | Dataplex Catalog API |
| 3 | `agent_knowledge_context` | **Knowledge Context API** — pre-loaded LLM-ready capsules | Zero (cached at init) | Dataplex `lookupContext` REST API |

### How It Works

```
User question
    │
    ▼
SequentialAgent (orchestrator)
    │
    ├──▶ ParallelAgent ─────────────────────────────────────┐
    │       ├── agent_bq_tools          (enumerate + rerank) │
    │       ├── agent_catalog_search    (search + rerank)    │
    │       └── agent_knowledge_context (cache + rerank)     │
    │    ◀──────────────────────────────────────────────────┘
    │
    └──▶ compare_results (synthesize and compare all three)
```

Each discovery agent calls the shared `rerank_tables` tool as its final step, producing a `RerankerResponse` with ranked tables, confidence scores, column hints, and SQL suggestions.

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

```bash
uv run adk run agent_orchestrator
```

Or run individual approaches:

```bash
uv run adk run agent_bq_tools
uv run adk run agent_catalog_search
uv run adk run agent_knowledge_context
```

**Example questions to try:**

- "What are the busiest bike share stations in Austin by month?"
- "How do tip amounts vary by time of day for NYC taxi rides?"
- "Which Austin neighborhoods have the highest crime rates on weekends?"
- "What were the strongest hurricanes to make landfall in the last 20 years?"
- "How does population density by ZIP code relate to bike share station placement in Austin?"

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
| `TOOL_MODEL` | `gemini-2.5-flash` | LLM for reranker structured output |
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

### Coming soon

- **MCP Toolbox for Databases**: A fourth approach using the [MCP Toolbox](https://github.com/googleapis/genai-toolbox) for direct BigQuery metadata access via MCP protocol.

- **ADK native MCP tools**: ADK is expected to wrap MCP Toolbox tools natively, providing another path to BQ metadata discovery.

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
│   └── prompts.py
│
├── agent_catalog_search/             # Approach 2: Dataplex semantic search
│   ├── __init__.py
│   ├── agent.py
│   ├── prompts.py
│   └── tools/
│       ├── __init__.py
│       ├── function_tool_search_catalog.py
│       └── function_tool_lookup_entry.py
│
├── agent_knowledge_context/          # Approach 3: Knowledge Context capsules
│   ├── __init__.py
│   ├── agent.py
│   ├── prompts.py
│   └── tools/
│       ├── __init__.py
│       ├── function_tool_initialize_context.py
│       └── util_lookup_context.py    # REST client (SDK pending)
│
└── agent_orchestrator/               # Root: parallel fan-out + compare
    ├── __init__.py
    ├── agent.py
    └── prompts.py
```
