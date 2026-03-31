![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FApplied+ML%2FAI+Agents%2Fdata-onboarding&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20ML/AI%20Agents/data-onboarding/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/data-onboarding/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/data-onboarding/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/data-onboarding/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/data-onboarding/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/Applied%20ML/AI%20Agents/data-onboarding/readme.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/Applied%20ML/AI%20Agents/data-onboarding/readme.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# Data Onboarding

Two multi-agent systems built with [Google ADK](https://google.github.io/adk-docs/) that automate the full lifecycle of data: **onboard** it from a URL into BigQuery, then **chat** with it using natural language.

**Onboarding** (`agent_orchestrator`) — Give it a URL and it crawls the site, downloads every data file it finds (CSV, Excel, Parquet, JSON, XML, and more), reads any documentation alongside them (PDFs, READMEs, data dictionaries), uses that context to design BigQuery tables with meaningful column names, descriptions, and types, creates them, publishes end-to-end lineage to Dataplex, and validates — all end-to-end, autonomously.

**Chat** (`agent_chat`) — Ask questions about the onboarded data in plain English. The chat agent finds the right tables from the metadata the onboarding agent created, then answers using the [Conversational Analytics API](https://cloud.google.com/gemini/docs/conversational-analytics-api/overview) which generates SQL, runs queries, produces data tables, charts, and insights.

## Contents

- [Two Motions](#two-motions) — High-level overview of both workflows
- [Onboarding Agent](#onboarding-agent-agent_orchestrator) — Pipeline stages and 7 sub-agents
- [Chat Agent](#chat-agent-agent_chat) — Three-persona router and 4 sub-agents
- [What Gets Created in BigQuery](#what-gets-created-in-bigquery) — Datasets and tables produced
- [Configuration](#configuration) — Environment variables and required APIs
- [Setup & Usage](#setup--usage) — Install, run locally, deploy to Agent Engine
- [Development](#development) — Tests, linting, cleanup

---

## Two Motions

### Motion 1: URL → Bronze Tables

```
URL ──crawl──→ File URLs ──download──→ GCS staging ──analyze──→ BQ external table ──SQL──→ BQ bronze table
 │                                         │                                                     │
 │              context docs (PDFs,        │                                                     │
 │              READMEs, data dicts)        │                                                     │
 │                     │                   │                   Dataplex Data Lineage ◄────────────┘
 └─ web_provenance     └─ cross-reference  └─ source_manifest
```

Run `uv run adk web` and select **`agent_orchestrator`** from the dropdown. Then provide a URL (e.g., a data portal page with downloadable files) in the chat. The agent crawls it, downloads everything, and walks through the full pipeline with checkpoints for your approval.

### Motion 2: Chat With Your Data

```
                             ┌─── Data Analyst ───→ agent_context ──→ agent_convo
                             │                           │                 │
User question ──→ agent_chat ├─── Data Engineer ──→ agent_engineer         │
     (router)                │                           │          Conversational
                             └─── Catalog Explorer → agent_catalog  Analytics API
                                                         │
                                                    AI.SEARCH
                                                  (semantic search)
```

The chat agent is a **three-persona router** that classifies each question and delegates to the right sub-agent:

| Persona | Route | For questions about |
|---------|-------|-------------------|
| **Data Analyst** | `agent_context` → `agent_convo` | Querying, analyzing, visualizing the actual data |
| **Data Engineer** | `agent_engineer` | Processing logs, lineage, schema decisions, source tracking |
| **Catalog Explorer** | `agent_catalog` | Column definitions, table documentation, relationships |

Run `uv run adk web` and select **`agent_chat`** from the dropdown.

Example questions:
- **Data Analyst**: "Compare the total short sale volume across the four Cboe equity exchanges."
- **Data Engineer**: "Show me the processing log for this source."
- **Catalog Explorer**: "What does PRVDR_NUM mean?"

See the examples for full question sets with automated results and timing breakdowns:
- [examples/cboe/cboe.md](examples/cboe/cboe.md) — **Cboe DataShop**: financial markets data (options, volatility, FX) — questions run locally
- [examples/medicare-provider/readme.md](examples/medicare-provider/readme.md) — **CMS Medicare Provider Data**: healthcare payment data (parquet) — demonstrates **`CHAT_SCOPE`** for multi-source disambiguation

---

## Onboarding Agent (`agent_orchestrator`)

7 sub-agents coordinated by a central orchestrator. Each agent is a Python package with its own tools, prompts, and tests.

### Pipeline

```
acquire → discover → understand → design → implement → validate
```

### Agents

#### `agent_acquire` — Crawl & Download

**Crawls a URL using breadth-first search and downloads every data file it finds to GCS staging.** Supports CSV, TSV, JSON, JSONL, Excel, Parquet, Avro, ORC, XML, ZIP archives, and context files (PDF, TXT, Markdown, HTML). Idempotent — skips files already in GCS.

<details>
<summary>Crawl settings, file formats, and ZIP handling</summary>

**Crawl settings** (all configurable via `.env`):

| Setting | Default | What it does |
|---------|---------|-------------|
| `CRAWL_MAX_DEPTH` | `1` | How many link hops from the starting URL |
| `CRAWL_MAX_FILES` | `100` | Hard cap on total files discovered |
| `CRAWL_SAME_ORIGIN_ONLY` | `true` | Only follow links on the same domain |
| `ACQUIRE_FILE_EXTENSIONS` | `csv,tsv,json,...,zip` | Which file types to download |

**File format support:**

| Category | Formats |
|----------|---------|
| Data files | CSV, TSV, JSON, JSONL, Excel (xlsx/xls), Parquet, Avro, ORC, XML |
| Context files | PDF, TXT, Markdown, HTML |
| Archives | ZIP (auto-extracted, flattened, deduplicated) |

**ZIP handling** — True ZIP archives are extracted and each member file is staged individually. But Office documents (xlsx, docx, pptx) are ZIP-based containers internally — the agent detects these by extension and treats them as single files, not archives. If a true ZIP happens to contain leaked OOXML internals (`xl/`, `docProps/`, `[Content_Types].xml`), those are filtered out.

</details>

#### `agent_discover` — Inventory & Classify

**Inventories all staged files in GCS and classifies each as data or context.** Files in a `context/` subdirectory are always classified as context. On reruns, compares SHA-256 hashes against `source_manifest` and only reprocesses new or modified files.

#### `agent_understand` — Read & Cross-Reference

**Reads every file, builds schema summaries, then cross-references data columns with context documents (PDFs, READMEs, data dictionaries) to produce meaningful column names, types, and descriptions.** This is the key intelligence step — the agent doesn't just look at data, it reads the documentation alongside it.

<details>
<summary>Format handling: headerless CSVs, multi-sheet Excel, XML</summary>

**Headerless CSV detection** — If more than half of a CSV's column names look like data values (numbers, dates, or very long strings), the agent flags it as headerless, re-reads with generic names (`col_0`, `col_1`, ...), and stores the original first row as data. The cross-reference step later uses context documents to assign real column names by matching positions.

**Multi-sheet Excel** — Workbooks with multiple non-empty sheets are split into separate data sources, one per sheet. Each gets a virtual path like `file.xlsx#SheetName` and its own schema summary.

**XML xpath fallback** — XML files don't always follow the same structure. The agent tries multiple xpath patterns (`None`, `.//row`, `.//record`, `.//item`, `./*`) and picks the one that produces the DataFrame with the lowest null rate.

</details>

<details>
<summary>Cross-reference with context</summary>

The agent sends each file's schema alongside all context documents to an LLM and gets back per-column insights:
- `suggested_bq_name` — a meaningful column name derived from documentation
- `suggested_bq_type` — an appropriate BigQuery type
- `description` — what the column represents
- `attributed_to` — which context document(s) informed each column's description

For headerless CSVs, the LLM matches generic column positions to documented field lists, giving every column a real name.

</details>

#### `agent_design` — Propose Tables

**Takes the enriched schemas and proposes BigQuery table structures.** Groups related files into single tables, applies enriched column names, suggests partitioning and clustering, and detects relationships between tables.

<details>
<summary>Grouping, partitioning, column enrichment, and relationship detection</summary>

**File grouping** — Files with date suffixes (`_2025-01-01`, `_20250101`) are grouped into a single table. For example, `trades_2025-01-01.csv` and `trades_2025-01-02.csv` become one `trades` table.

**Schema compatibility** — All files in a group must have the same columns (case-insensitive). If they don't match, they become separate tables.

**Partitioning & clustering** — The agent suggests partitioning on datetime/date columns and clustering on high-cardinality string/integer columns. Partitioning is only suggested for tables with more than 10,000 rows (configurable via `PARTITION_MIN_ROWS`). Granularity (DAY, MONTH, YEAR) is chosen to stay within BigQuery's 4,000-partition limit.

**Column enrichment** — The `suggested_bq_name` from cross-reference is applied here. If two columns end up with the same enriched name (common when the LLM maps multiple generic columns to the same concept), they get numeric suffixes (`price`, `price_1`). Partition and cluster column references are updated to match the renamed columns.

**Relationship detection** — The agent identifies relationships between tables:
- Snapshot relationships (e.g., `foo_lro` is a snapshot of `foo`)
- Containment (e.g., `foo_full` contains `foo_bar` if columns are a superset)
- Shared join keys (columns with matching name and type across tables)

</details>

#### `agent_implement` — Create Tables, Documentation & Profiling

**Creates BigQuery tables (external → materialized), generates documentation, triggers Dataplex data profile scans, and publishes end-to-end lineage.** Handles format-specific loading paths, resilient type casting, and column recovery automatically.

<details>
<summary>Table creation: external tables and materialized bronze tables</summary>

**Step 1: External tables** in a staging dataset (`*_staging`)
- **BQ autodetect path** — For CSV, TSV, JSON, Parquet, Avro, ORC: creates a BigQuery external table that reads directly from GCS with schema autodetection.
- **Pandas load path** — For formats BQ can't autodetect (Excel, XML) or data that needs transformation (headerless CSVs, columns with special characters): reads into a pandas DataFrame and loads via `load_table_from_dataframe`.

**Step 2: Materialized tables** in the bronze dataset (`*_bronze`)
- Runs `CREATE OR REPLACE TABLE ... AS SELECT ...` with type casting.
- All casts go through STRING first: `SAFE_CAST(CAST(col AS STRING) AS target_type)`. This avoids hard BigQuery errors on incompatible type pairs (like TIME → TIMESTAMP) — the STRING intermediate lets SAFE_CAST return NULL instead of failing.

</details>

<details>
<summary>Resilient column recovery and deduplication</summary>

If a pandas DataFrame fails to load (e.g., mixed-type columns that pyarrow can't serialize), the agent tests each column individually:
1. Try converting to pyarrow — if it works, keep it
2. If not, coerce the column to STRING — if that works, keep it as STRING
3. If even STRING fails, drop the column entirely

Coerced and dropped columns are logged to `processing_log` in the meta dataset and surfaced in the table documentation as "Data Quality Notes."

If an Excel file has duplicate column names (e.g., two columns both called "ID"), they're deduplicated with numeric suffixes before loading to avoid BigQuery schema errors.

</details>

<details>
<summary>Documentation, data profiling, and lineage</summary>

**Documentation generation** — Writes two tables (no LLM call — purely programmatic from enriched metadata):
- `table_documentation` in each bronze dataset — per-table markdown with a column dictionary, source attribution, related tables, schema provenance, and data quality notes
- `data_catalog` in the meta dataset — dataset-level overview with all tables, context documents, and relationships

**Data profiling** — After tables are created, the agent triggers [Dataplex data profile scans](https://cloud.google.com/dataplex/docs/data-profiling-overview) on each bronze table and on the shared meta tables (`source_manifest`, `processing_log`, `table_lineage`, `schema_decisions`, `web_provenance`). Scans run asynchronously with 10% sampling and publish results to the Dataplex catalog. This makes profile statistics (min/max values, null rates, value distributions) available via the [lookupContext API](https://cloud.google.com/dataplex/docs/reference/rest/v1/projects.locations/lookupContext) for downstream context discovery.

**Lineage publishing** — Writes custom lineage events to the [Dataplex Data Lineage API](https://cloud.google.com/dataplex/docs/about-data-lineage):

| Hop | From | To |
|-----|------|----|
| 1 | `custom:<starting_url>` | `custom:<file_url>` |
| 2 | `custom:<file_url>` | `gcs:<gs://bucket/path>` |
| 3 | `gcs:<gs://bucket/path>` | `bigquery:<project.dataset.ext_table>` |
| 4 | `bigquery:<ext_table>` | `bigquery:<bronze_table>` |

Hop 4 is captured automatically by BigQuery when the Data Lineage API is enabled. The result is full end-to-end lineage from the original URL to the final bronze table, visible in the Google Cloud Console.

</details>

#### `agent_validate` — Verify Results

**Runs row count and type validation on every created table.** Compares expected vs. actual rows (±1 tolerance) and expected vs. actual column types (with alias normalization). Results are reported as PASS, WARN, FAIL, or SKIP per table.

---

## Chat Agent (`agent_chat`)

A three-persona router with four sub-agents that lets you query onboarded data, explore pipeline metadata, and look up data definitions conversationally.

### Persona 1: Data Analyst (`agent_context` → `agent_convo`)

For questions about the actual data — querying, analyzing, summarizing, visualizing.

#### `agent_context` — Find the Right Tables

**Pre-loads the full data catalog at startup and uses a two-pass reranker to match each question to the right tables.** Any bronze dataset created by the onboarding agent is immediately available for chat — no additional configuration needed.

<details>
<summary>Two-pass reranker and context sources</summary>

**Two-pass reranker:**
1. **Shortlist pass** (fast) — sends the compact catalog summary (~100 tokens per table) for all tables to Gemini, which returns the top 10 candidates with confidence scores
2. **Detail pass** (focused) — sends full metadata (column names, types, descriptions, relationships) for only the shortlisted tables to Gemini, which returns final rankings with key columns, SQL hints, and join suggestions
3. Transfers to `agent_convo` with the reranker result stored in session state

This two-pass approach avoids sending full metadata for all tables in a single call (which caused timeouts at scale) while maintaining good recall — the fast first pass screens broadly, and the focused second pass ranks precisely.

**Where the context comes from:**
- `data_catalog` in the meta dataset — written by the onboarding agent's `generate_documentation` tool
- `table_documentation` in each bronze dataset — per-table markdown with column details, descriptions, attribution, and relationships
- The onboarding agent's cross-reference enrichment — column descriptions, suggested names, and BQ types all flow through into the documentation

</details>

#### `agent_convo` — Answer Questions

**Calls the [Conversational Analytics API](https://cloud.google.com/gemini/docs/conversational-analytics-api/overview) with enriched context from the reranker.** Auto-selects tables from session state, generates and runs SQL, returns text answers, data tables, and charts. Maintains session history for follow-up questions.

<details>
<summary>Enriched context and API details</summary>

Tables are auto-selected from the `reranker_result` in session state. When reranker results are available, the API receives:
- **Schema overrides** — per-table column names, types, and descriptions from the reranker's key columns
- **Schema relationships** — join paths between tables from the reranker's join suggestions
- **Glossary terms** — domain-specific terms extracted from column descriptions
- **SQL guidance** — per-table hints (filters, aggregations, join conditions) appended to the system instruction

When no reranker result is available, falls back to bare table references (backward compatible).

The tool processes the API's response stream and returns only the useful parts: text summaries, data result tables, and insights. Intermediate steps (schema resolution, query planning, raw SQL) are filtered out for a clean chat experience. Charts are saved as image artifacts.

The core API calling logic (session management, response processing, chart handling) is shared between `agent_convo` and `agent_engineer` via a common utility to avoid code duplication.

</details>

### Persona 2: Data Engineer (`agent_engineer`)

For questions about the onboarding pipeline — processing history, schema decisions, data lineage, source tracking.

Uses the Conversational Analytics API against the **meta dataset** tables (`source_manifest`, `processing_log`, `table_lineage`, `schema_decisions`, `web_provenance`, `data_catalog`). All meta tables are included automatically — no table discovery needed. Session history is maintained separately under `meta_api_sessions`.

### Persona 3: Catalog Explorer (`agent_catalog`)

For questions about data meaning — column definitions, table documentation, relationships, data provenance.

Uses BigQuery `AI.SEARCH` for semantic retrieval over the `context_chunks` table in the `data_onboarding_context` dataset. During onboarding, table documentation is chunked into searchable pieces (one chunk per column definition, one per table doc, one per relationship set). Each chunk has an autonomous embedding via `AI.EMBED` with `text-embedding-005`. The agent searches these chunks, then synthesizes an answer citing specific `dataset.table.column` references.

The BQ Cloud Resource connection and IAM grants are created automatically during the first onboarding run.

### Flow

1. **New question** → `agent_chat` classifies and routes:
   - **Data Analyst** → `agent_context` → `agent_convo` (Conversational Analytics API against bronze tables)
   - **Data Engineer** → `agent_engineer` (Conversational Analytics API against meta tables)
   - **Catalog Explorer** → `agent_catalog` (AI.SEARCH over context chunks)
2. **Follow-up questions** go directly to the last active agent (session history preserved)
3. **Persona changes** restart routing — the question is reclassified and sent to the right agent

---

## What Gets Created in BigQuery

The onboarding agent creates four categories of BigQuery datasets, and the ADK framework adds a fifth for analytics.

### Meta Dataset (`data_onboarding_meta`)

Shared metadata across all onboarded sources. Contains 6 tables:

| Table | What it tracks |
|-------|---------------|
| `source_manifest` | Every file the agent has seen — GCS path, SHA-256 hash, file size, type (data/context), classification, original URL, timestamps. Partitioned by `discovered_at`, clustered by `source_id` and `classification`. |
| `processing_log` | Every pipeline action — which phase (acquire, discover, etc.), what action, status (started/completed/failed), JSON details, timestamps. Partitioned by `started_at`, clustered by `source_id` and `phase`. |
| `table_lineage` | Mappings from bronze table → external table → source file, with column-level lineage stored as JSON. Partitioned by `created_at`, clustered by `source_id` and `bq_table`. |
| `schema_decisions` | Every design proposal — the full proposal JSON, reasoning, approval status. Partitioned by `created_at`, clustered by `source_id` and `status`. |
| `web_provenance` | The crawl graph — every URL visited, its parent URL, page title, content type, HTTP status code, links found, files downloaded. Partitioned by `crawled_at`, clustered by `source_id`. |
| `data_catalog` | One row per onboarded source — dataset name, source URL, domain, list of tables created, context documents used, table relationships, markdown description. Clustered by `dataset_name`. |

### Bronze Datasets (`data_onboarding_{domain}_bronze`)

One dataset per source domain. For example, onboarding from `datashop.cboe.com` creates `data_onboarding_datashop_cboe_com_bronze`. Contains:

- **One table per data file** (or file group) — the materialized data with enriched column names, types, descriptions, partitioning, and clustering. Each table also has a [Dataplex data profile scan](https://cloud.google.com/dataplex/docs/data-profiling-overview) that publishes statistics (value distributions, null rates, min/max) to the Dataplex catalog.
- **`table_documentation`** — A metadata table with one row per data table. Each row has:
  - `documentation_md` — Markdown documentation with overview, column dictionary, related tables, schema provenance, and data quality notes
  - `column_details` — JSON array with each column's name, source name, BQ type, description, and attribution
  - `related_tables` — JSON with relationships to other tables (shared keys, snapshots, containment)
  - `source_documents` — JSON list of context documents that informed the table's schema

This `table_documentation` table is what `agent_context` reads when answering chat questions. It's the bridge between the onboarding pipeline and the chat agent.

### Context Dataset (`data_onboarding_context`)

Semantic search index for the Catalog Explorer agent. Contains:

- **`context_chunks`** — Chunked table documentation with autonomous embeddings. Each row is a searchable piece of documentation:
  - `chunk_type` — `table_documentation`, `column_description`, `relationship`, or `profile_stat`
  - `chunk_text` — The searchable text content
  - `ml_embed_content` — Vector embedding generated automatically by `AI.EMBED` with `text-embedding-005`
  - Clustered by `source_dataset` and `chunk_type`

Chunks are created during onboarding by the `populate_context_chunks` tool and searched during chat by `agent_catalog` using `AI.SEARCH`. The dataset uses a Cloud Resource connection (`data_onboarding_embed`) for the `AI.EMBED` generated column.

### Staging Datasets (`data_onboarding_{domain}_staging`)

Temporary external tables used during the onboarding pipeline. Each external table (`ext_{table_name}`) points to the raw files in GCS. The materialized bronze tables are created from these via `CREATE OR REPLACE TABLE ... AS SELECT`.

### ADK Analytics Dataset (`data_onboarding_adk`)

Created by the ADK BigQuery analytics plugin. Contains:

- **`agent_events`** — Every agent event logged by the framework: user messages, LLM requests/responses, tool calls with arguments and results, agent transfers, state changes. Each row includes `session_id`, `timestamp`, `event_type`, `agent` name, and a JSON `content` column with full details.

This table is useful for debugging agent behavior, reviewing conversation traces, and understanding how the agents make decisions.

---

## Configuration

### Environment Variables

Create a `.env` file. Only two variables are required — everything else has sensible defaults.

**Required:**

| Variable | Description |
|----------|-------------|
| `GOOGLE_CLOUD_PROJECT` | Your GCP project ID |
| `GOOGLE_CLOUD_STORAGE_BUCKET` | GCS bucket for staging files |

<details>
<summary>Optional variables (models, crawling, BigQuery, file types)</summary>

**Models** — which Gemini models the agents use:

| Variable | Default | Description |
|----------|---------|-------------|
| `AGENT_MODEL` | `gemini-2.5-flash` | Model for agent reasoning |
| `TOOL_MODEL` | `gemini-2.5-pro` | Model for tool LLM calls (cross-reference, etc.) |
| `AGENT_MODEL_LOCATION` | `global` | API endpoint location for agent model |
| `TOOL_MODEL_LOCATION` | `global` | API endpoint location for tool model |

**Web crawling:**

| Variable | Default | Description |
|----------|---------|-------------|
| `CRAWL_MAX_DEPTH` | `1` | Link depth from starting URL |
| `CRAWL_MAX_FILES` | `100` | Maximum files to discover |
| `CRAWL_SAME_ORIGIN_ONLY` | `true` | Only follow same-domain links |

**Chat scope:**

| Variable | Default | Description |
|----------|---------|-------------|
| `CHAT_SCOPE` | *(empty)* | Restrict the chat agent to specific dataset(s). When empty, the agent sees all onboarded datasets — which can cause cross-source confusion when multiple sources are onboarded. Set to the bronze dataset name(s) for the source you want to query (e.g., `data_onboarding_datashop_cboe_com_bronze`). To switch sources, update this value and run `deploy.py chat --update`. |

**BigQuery:**

| Variable | Default | Description |
|----------|---------|-------------|
| `BQ_DATASET_LOCATION` | `US` | Where to create datasets |
| `PARTITION_MIN_ROWS` | `10000` | Minimum rows before suggesting partitioning |
| `RESOURCE_PREFIX` | `data_onboarding` | Prefix for all dataset names |

**Dataplex:**

| Variable | Default | Description |
|----------|---------|-------------|
| `DATAPLEX_LOCATION` | `us-central1` | Location for Dataplex data profile scans |

**File types:**

| Variable | Default | Description |
|----------|---------|-------------|
| `ACQUIRE_FILE_EXTENSIONS` | `csv,tsv,json,...,zip` | All file types to download |
| `DATA_FILE_EXTENSIONS` | `csv,tsv,json,...,xml` | Files treated as data |
| `CONTEXT_FILE_EXTENSIONS` | `pdf,txt,md,html` | Files treated as context |

</details>

### Required Google Cloud APIs

- BigQuery API
- Cloud Storage API
- Vertex AI API
- Data Lineage API (for Dataplex lineage)
- Dataplex API (for data profile scans)
- Conversational Analytics API (for `agent_chat`)
- BigQuery Connection API (for `AI.EMBED` autonomous embeddings)
- Cloud Telemetry API (for Agent Engine tracing — `telemetry.googleapis.com`)

---

## Setup & Usage

### Install

**uv** (recommended):
```bash
uv sync --extra dev
```

**pip**:
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

**Jupyter kernel** (optional — needed for notebooks like [deploy/interact.ipynb](deploy/interact.ipynb)):
```bash
uv pip install ipykernel
uv run python -m ipykernel install --user --name data-onboarding --display-name "Data Onboarding"
```

### Run

```bash
uv run adk web
```

Then select the agent from the dropdown:
- **`agent_orchestrator`** — Onboard data from a URL
- **`agent_chat`** — Chat with onboarded data

### Deploy the Chat Agent to Vertex AI Agent Engine

The chat agent (`agent_chat`) is deployed to [Vertex AI Agent Engine](https://docs.cloud.google.com/agent-builder/agent-engine/overview) — Google Cloud's managed runtime with persistent sessions, Cloud Trace, and Cloud Monitoring — no infrastructure to manage.

```bash
uv run python deploy/deploy.py chat                  # Deploy chat agent
uv run python deploy/deploy.py chat --test            # Test deployed agent
uv run python deploy/deploy.py chat --update          # Update existing
uv run python deploy/deploy.py chat --delete          # Delete deployment
```

> **Why only the chat agent?** The orchestrator runs a long batch pipeline (crawling, downloading, schema inference, table creation) that can take 20–60 minutes per source. Agent Engine is optimized for conversational agents with fast request-response cycles — long-running tool calls exceed its streaming timeout and lose in-memory state between reconnections. The chat agent, on the other hand, is conversational and fast — a perfect fit. Run `agent_orchestrator` locally via `uv run adk web`, then query the onboarded data through the deployed chat agent.

See [deploy/readme.md](deploy/readme.md) for full deployment details: packaging, entrypoints, environment variables, and how to query deployed agents.

---

## Development

```bash
make test             # Run all tests
make lint             # Run ruff linter
make format           # Auto-format + sort imports
make check            # Lint + tests
make run             # Launch adk web
```

## Cleanup

Remove all cloud resources (BQ datasets, GCS blobs) and local output:

```bash
python scripts/cleanup.py --dry-run    # Preview what would be deleted
python scripts/cleanup.py              # Interactive confirmation
python scripts/cleanup.py --yes        # Skip confirmation
```

Selectively skip with `--skip-bq`, `--skip-gcs`, `--skip-local`, `--skip-lineage`, `--skip-profiling`, `--skip-agent-engine`.
