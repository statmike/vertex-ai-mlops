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
</table><br/><br/>

---
# Data Onboarding

Two multi-agent systems built with [Google ADK](https://google.github.io/adk-docs/) that automate the full lifecycle of data: **onboard** it from a URL into BigQuery, then **chat** with it using natural language.

**Onboarding** (`agent_orchestrator`) — Give it a URL and it crawls the site, downloads every data file it finds (CSV, Excel, Parquet, JSON, XML, and more), reads any documentation alongside them (PDFs, READMEs, data dictionaries), uses that context to design BigQuery tables with meaningful column names, descriptions, and types, creates them, publishes end-to-end lineage to Dataplex, and validates — all end-to-end, autonomously.

**Chat** (`agent_chat`) — Ask questions about the onboarded data in plain English. The chat agent finds the right tables from the metadata the onboarding agent created, then answers using the [Conversational Analytics API](https://cloud.google.com/gemini/docs/conversational-analytics-api/overview) which generates SQL, runs queries, produces data tables, charts, and insights.

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

Run the onboarding agent:

```bash
uv run adk web agent_orchestrator
```

Then provide a URL (e.g., a data portal page with downloadable files) in the chat. The agent crawls it, downloads everything, and walks through the full pipeline with checkpoints for your approval.

### Motion 2: Chat With Your Data

```
User question ──→ agent_chat ──→ agent_context (find tables) ──→ agent_convo (query & answer)
                                       │                               │
                            reads data_catalog &              calls Conversational
                            table_documentation               Analytics API
```

Run the chat agent:

```bash
uv run adk web agent_chat
```

Ask questions like "What is the highest VIX close value?" or "Compare short sale volume across exchanges" — the agent finds the right tables, queries them, and returns answers with data tables, charts, and insights.

---

## Onboarding Agent (`agent_orchestrator`)

7 sub-agents coordinated by a central orchestrator. Each agent is a Python package with its own tools, prompts, and tests.

### Pipeline

```
acquire → discover → understand → design → implement → validate
```

### Agents

#### `agent_acquire` — Crawl & Download

Crawls a URL using breadth-first search and downloads every data file it finds to GCS staging.

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

**Idempotency** — Before downloading, the agent checks if a file already exists in GCS with the same path. Duplicate downloads are skipped.

#### `agent_discover` — Inventory & Classify

Inventories all staged files in GCS and classifies each as **data** (for table creation) or **context** (for understanding schemas). Files in a `context/` subdirectory are always classified as context.

**Change detection** — On reruns, the agent queries `source_manifest` for previously seen files and compares SHA-256 hashes. Files are categorized as new, modified, unchanged, or removed. Only new and modified files are reprocessed.

#### `agent_understand` — Read & Cross-Reference

Reads every file and builds a schema summary. This is where the agent starts acting like a data engineer — it doesn't just look at data files, it reads the documentation alongside them and uses that context to understand what the data means.

**Headerless CSV detection** — If more than half of a CSV's column names look like data values (numbers, dates, or very long strings), the agent flags it as headerless, re-reads with generic names (`col_0`, `col_1`, ...), and stores the original first row as data. The cross-reference step later uses context documents to assign real column names by matching positions.

**Multi-sheet Excel** — Workbooks with multiple non-empty sheets are split into separate data sources, one per sheet. Each gets a virtual path like `file.xlsx#SheetName` and its own schema summary.

**XML xpath fallback** — XML files don't always follow the same structure. The agent tries multiple xpath patterns (`None`, `.//row`, `.//record`, `.//item`, `./*`) and picks the one that produces the DataFrame with the lowest null rate.

**Cross-reference with context** — This is the key step. The agent sends each file's schema alongside all context documents (PDFs, READMEs, data dictionaries) to an LLM and gets back per-column insights:
- `suggested_bq_name` — a meaningful column name derived from documentation
- `suggested_bq_type` — an appropriate BigQuery type
- `description` — what the column represents
- `attributed_to` — which context document(s) informed each column's description

For headerless CSVs, the LLM matches generic column positions to documented field lists, giving every column a real name.

#### `agent_design` — Propose Tables

Takes the enriched schemas and proposes BigQuery table structures.

**File grouping** — Files with date suffixes (`_2025-01-01`, `_20250101`) are grouped into a single table. For example, `trades_2025-01-01.csv` and `trades_2025-01-02.csv` become one `trades` table.

**Schema compatibility** — All files in a group must have the same columns (case-insensitive). If they don't match, they become separate tables.

**Partitioning & clustering** — The agent suggests partitioning on datetime/date columns and clustering on high-cardinality string/integer columns. Partitioning is only suggested for tables with more than 10,000 rows (configurable via `PARTITION_MIN_ROWS`). Granularity (DAY, MONTH, YEAR) is chosen to stay within BigQuery's 4,000-partition limit.

**Column enrichment** — The `suggested_bq_name` from cross-reference is applied here. If two columns end up with the same enriched name (common when the LLM maps multiple generic columns to the same concept), they get numeric suffixes (`price`, `price_1`). Partition and cluster column references are updated to match the renamed columns.

**Relationship detection** — The agent identifies relationships between tables:
- Snapshot relationships (e.g., `foo_lro` is a snapshot of `foo`)
- Containment (e.g., `foo_full` contains `foo_bar` if columns are a superset)
- Shared join keys (columns with matching name and type across tables)

#### `agent_implement` — Create Tables & Documentation

Creates the actual BigQuery tables in a two-step process:

**Step 1: External tables** in a staging dataset (`*_staging`)
- **BQ autodetect path** — For CSV, TSV, JSON, Parquet, Avro, ORC: creates a BigQuery external table that reads directly from GCS with schema autodetection.
- **Pandas load path** — For formats BQ can't autodetect (Excel, XML) or data that needs transformation (headerless CSVs, columns with special characters): reads into a pandas DataFrame and loads via `load_table_from_dataframe`.

**Step 2: Materialized tables** in the bronze dataset (`*_bronze`)
- Runs `CREATE OR REPLACE TABLE ... AS SELECT ...` with type casting.
- All casts go through STRING first: `SAFE_CAST(CAST(col AS STRING) AS target_type)`. This avoids hard BigQuery errors on incompatible type pairs (like TIME → TIMESTAMP) — the STRING intermediate lets SAFE_CAST return NULL instead of failing.

**Resilient column recovery** — If a pandas DataFrame fails to load (e.g., mixed-type columns that pyarrow can't serialize), the agent tests each column individually:
1. Try converting to pyarrow — if it works, keep it
2. If not, coerce the column to STRING — if that works, keep it as STRING
3. If even STRING fails, drop the column entirely

Coerced and dropped columns are logged to `processing_log` in the meta dataset and surfaced in the table documentation as "Data Quality Notes."

**DataFrame deduplication** — If an Excel file has duplicate column names (e.g., two columns both called "ID"), they're deduplicated with numeric suffixes before loading to avoid BigQuery schema errors.

**Documentation generation** — Writes two tables (no LLM call — purely programmatic from enriched metadata):
- `table_documentation` in each bronze dataset — per-table markdown with a column dictionary, source attribution, related tables, schema provenance, and data quality notes
- `data_catalog` in the meta dataset — dataset-level overview with all tables, context documents, and relationships

**Lineage publishing** — Writes custom lineage events to the [Dataplex Data Lineage API](https://cloud.google.com/dataplex/docs/about-data-lineage):

| Hop | From | To |
|-----|------|----|
| 1 | `custom:<starting_url>` | `custom:<file_url>` |
| 2 | `custom:<file_url>` | `gcs:<gs://bucket/path>` |
| 3 | `gcs:<gs://bucket/path>` | `bigquery:<project.dataset.ext_table>` |
| 4 | `bigquery:<ext_table>` | `bigquery:<bronze_table>` |

Hop 4 is captured automatically by BigQuery when the Data Lineage API is enabled. The result is full end-to-end lineage from the original URL to the final bronze table, visible in the Google Cloud Console.

#### `agent_validate` — Verify Results

Runs two validation checks on every created table:

**Row count validation** — Compares expected rows (from the proposal) against actual BigQuery table rows. Allows ±1 tolerance for header differences. If the source data was sampled (capped at 500 rows), any actual count above the expected count passes.

**Type validation** — Compares each column's expected BQ type against the actual schema. Reports null rates per column. Type aliases are normalized (e.g., `INT64` = `INTEGER`, `FLOAT64` = `FLOAT`).

Results are reported as PASS, WARN, FAIL, or SKIP per table.

---

## Chat Agent (`agent_chat`)

An orchestrator with two sub-agents that lets you query the onboarded data conversationally.

### `agent_context` — Find the Right Tables

This agent knows about every table the onboarding agent created. At startup, it pre-loads the full data catalog from BigQuery — every dataset, table name, column list, column descriptions, and relationships. This pre-loaded catalog is embedded directly in the agent's instructions so it can instantly identify which tables match a user's question without any tool calls.

It still calls `find_tables` to load detailed table documentation into the conversation history (so the next agent can see it), and can optionally call `sample_data` to run short read-only queries that verify table contents.

**Where the context comes from:**
- `data_catalog` in the meta dataset — written by the onboarding agent's `generate_documentation` tool
- `table_documentation` in each bronze dataset — per-table markdown with column details, descriptions, attribution, and relationships
- The onboarding agent's cross-reference enrichment — column descriptions, suggested names, and BQ types all flow through into the documentation

This means any bronze dataset created by the onboarding agent is immediately available for chat. No additional configuration needed.

### `agent_convo` — Answer Questions

Calls the [Conversational Analytics API](https://cloud.google.com/gemini/docs/conversational-analytics-api/overview) with the table references from `agent_context` and the user's question. The API:
- Resolves schemas for the referenced tables
- Generates and runs SQL queries
- Returns text answers, data tables, and charts
- Maintains session history for follow-up questions

The tool processes the API's response stream and returns only the useful parts: text summaries, data result tables, and insights. Intermediate steps (schema resolution, query planning, raw SQL) are filtered out for a clean chat experience. Charts are saved as image artifacts.

### Flow

1. **New question** → `agent_chat` transfers to `agent_context`
2. **`agent_context`** consults its pre-loaded catalog, calls `find_tables`, transfers to `agent_convo`
3. **`agent_convo`** calls `conversational_chat` with the right table references, returns the answer
4. **Follow-up questions** on the same topic go directly to `agent_convo` (session history preserved)
5. **Topic changes** go back to `agent_context` to find new tables

---

## What Gets Created in BigQuery

The onboarding agent creates three categories of BigQuery datasets, and the ADK framework adds a fourth for analytics.

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

- **One table per data file** (or file group) — the materialized data with enriched column names, types, descriptions, partitioning, and clustering.
- **`table_documentation`** — A metadata table with one row per data table. Each row has:
  - `documentation_md` — Markdown documentation with overview, column dictionary, related tables, schema provenance, and data quality notes
  - `column_details` — JSON array with each column's name, source name, BQ type, description, and attribution
  - `related_tables` — JSON with relationships to other tables (shared keys, snapshots, containment)
  - `source_documents` — JSON list of context documents that informed the table's schema

This `table_documentation` table is what `agent_context` reads when answering chat questions. It's the bridge between the onboarding pipeline and the chat agent.

### Staging Datasets (`data_onboarding_{domain}_staging`)

Temporary external tables used during the onboarding pipeline. Each external table (`ext_{table_name}`) points to the raw files in GCS. The materialized bronze tables are created from these via `CREATE OR REPLACE TABLE ... AS SELECT`.

### ADK Analytics Dataset (`data_onboarding_adk`)

Created by the ADK BigQuery analytics plugin. Contains:

- **`agent_events`** — Every agent event logged by the framework: user messages, LLM requests/responses, tool calls with arguments and results, agent transfers, state changes. Each row includes `session_id`, `timestamp`, `event_type`, `agent` name, and a JSON `content` column with full details.

This table is useful for debugging agent behavior, reviewing conversation traces, and understanding how the agents make decisions.

---

## Configuration

### Environment Variables

Create a `.env` file. Only `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_STORAGE_BUCKET` are required — everything else has sensible defaults.

```env
# Required
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_STORAGE_BUCKET=your-bucket-name

# Models — which Gemini models the agents use
# AGENT_MODEL=gemini-2.5-flash          # Model for agent reasoning
# TOOL_MODEL=gemini-2.5-pro             # Model for tool LLM calls (cross-reference, etc.)
# AGENT_MODEL_LOCATION=global           # API endpoint location for agent model
# TOOL_MODEL_LOCATION=global            # API endpoint location for tool model

# Web crawling
# CRAWL_MAX_DEPTH=1                     # Link depth from starting URL
# CRAWL_MAX_FILES=100                   # Maximum files to discover
# CRAWL_SAME_ORIGIN_ONLY=true           # Only follow same-domain links

# BigQuery
# BQ_DATASET_LOCATION=US                # Where to create datasets
# PARTITION_MIN_ROWS=10000              # Minimum rows before suggesting partitioning
# RESOURCE_PREFIX=data_onboarding       # Prefix for all dataset names

# File types
# ACQUIRE_FILE_EXTENSIONS=csv,tsv,json,jsonl,xlsx,xls,parquet,avro,orc,xml,pdf,txt,md,html,zip
# DATA_FILE_EXTENSIONS=csv,tsv,json,jsonl,xlsx,xls,parquet,avro,orc,xml
# CONTEXT_FILE_EXTENSIONS=pdf,txt,md,html
```

### Required Google Cloud APIs

- BigQuery API
- Cloud Storage API
- Vertex AI API
- Data Lineage API (for Dataplex lineage)
- Conversational Analytics API (for `agent_chat`)

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

### Run

**Onboard data from a URL:**
```bash
uv run adk web agent_orchestrator
```

**Chat with onboarded data:**
```bash
uv run adk web agent_chat
```

### Deploy to Vertex AI Agent Engine

```bash
python deploy/deploy.py             # Deploy (runs local test first)
python deploy/deploy.py --update    # Update existing deployment
python deploy/deploy.py --delete    # Delete deployment
python deploy/deploy.py --info      # Show deployment info
```

---

## Development

```bash
make test      # Run all tests (231 tests)
make lint      # Run ruff linter
make format    # Auto-format + sort imports
make check     # Lint + tests
```

## Cleanup

Remove all cloud resources (BQ datasets, GCS blobs) and local output:

```bash
python scripts/cleanup.py --dry-run    # Preview what would be deleted
python scripts/cleanup.py              # Interactive confirmation
python scripts/cleanup.py --yes        # Skip confirmation
```

Selectively skip with `--skip-bq`, `--skip-gcs`, `--skip-local`, `--skip-agent-engine`.
