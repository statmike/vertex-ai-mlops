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

A multi-agent ADK system that automates data onboarding into BigQuery. Give it a URL or GCS path and it crawls/downloads files, analyzes schemas and context documents, designs BQ tables, creates them with full metadata, publishes end-to-end lineage to Dataplex, and validates — with human-in-the-loop checkpoints.

## Architecture

7 agents coordinated by a central orchestrator, each implemented as a Python package:

| Agent | Role | Tools |
|-------|------|-------|
| `agent_orchestrator` | Root agent — routes between phases, owns shared config and metadata | — |
| `agent_acquire` | Crawl URLs (BFS, configurable depth), download files, extract page content | `crawl_url`, `download_files`, `extract_page_content` |
| `agent_discover` | Inventory staged files, classify as data/context, detect changes via hash comparison | `inventory_files`, `classify_files`, `detect_changes` |
| `agent_understand` | Read multi-format files, analyze column statistics, cross-reference with context docs | `read_data_file`, `read_context_file`, `analyze_columns`, `cross_reference` |
| `agent_design` | Propose BQ table structures with types, partitioning, clustering, and descriptions | `propose_tables`, `propose_columns`, `record_decisions` |
| `agent_implement` | Create external + materialized BQ tables, publish Dataplex lineage, apply metadata | `create_external_tables`, `execute_sql`, `publish_lineage`, `apply_bq_metadata`, `update_changelog` |
| `agent_validate` | Validate row counts, column types, and end-to-end lineage completeness | `validate_counts`, `validate_types`, `validate_lineage` |

### Pipeline

```
acquire → discover → understand → design → [HUMAN APPROVAL] → implement → [HUMAN APPROVAL] → validate
```

### Data Flow

```
URL ──crawl──→ File URLs ──download──→ GCS staging ──ext table──→ BQ external table ──SQL──→ BQ materialized table
                                                                                                       │
                                                              Dataplex Data Lineage ◄──publish_lineage──┘
```

### Metadata Tracking

5 BigQuery tables in the `*_bronze_meta` dataset provide full observability:

| Table | Tracks |
|-------|--------|
| `source_manifest` | Every file — GCS path, SHA-256 hash, size, type, classification, original URL |
| `processing_log` | Every pipeline action — phase, status, timestamps |
| `table_lineage` | BQ table → external table → source file mappings with column-level lineage |
| `schema_decisions` | Design proposals with reasoning and approval status |
| `web_provenance` | URL crawl graph — parent/child URLs, page titles, status codes |

### Dataplex Lineage

After tables are created, `publish_lineage` writes three custom lineage events per file to the [Data Lineage API](https://cloud.google.com/dataplex/docs/about-data-lineage):

1. `custom:<starting_url>` → `custom:<file_url>` — web crawl provenance
2. `custom:<file_url>` → `gcs:<gs://bucket/path>` — download to staging
3. `gcs:<gs://bucket/path>` → `bigquery:<project.dataset.ext_table>` — GCS to external table

BigQuery automatically captures the fourth hop (external table → materialized table) when the Data Lineage API is enabled. The result is full end-to-end lineage visible in the Google Cloud Console.

### Supported File Formats

| Category | Formats |
|----------|---------|
| Data files | CSV, TSV, JSON, JSONL, Excel (xlsx/xls), Parquet, Avro, ORC, XML |
| Context files | PDF, TXT, Markdown, HTML |
| Archives | ZIP (auto-extracted, flattened, deduplicated) |

## Setup

The project uses `pyproject.toml` (PEP 621) so it works with any Python package manager.

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

### Configure

Create a `.env` file with your GCP settings:

```env
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_STORAGE_BUCKET=your-bucket-name

# Optional — all have sensible defaults
# AGENT_MODEL=gemini-2.5-flash
# BQ_DATASET_LOCATION=US
1# CRAWL_MAX_DEPTH=1
# CRAWL_MAX_FILES=100
# CRAWL_SAME_ORIGIN_ONLY=true
# RESOURCE_PREFIX=data_onboarding
```

### Required APIs

Enable these Google Cloud APIs:
- BigQuery API
- Cloud Storage API
- Data Lineage API (for Dataplex lineage)
- Vertex AI API (for deployment)

## Usage

```bash
uv run adk web agent_orchestrator
```

Then provide a URL (e.g. a page with downloadable CSV/JSON files) or a GCS path in the chat.

### Deploy to Vertex AI Agent Engine

```bash
python deploy/deploy.py             # Deploy (runs local test first)
python deploy/deploy.py --update    # Update existing deployment
python deploy/deploy.py --delete    # Delete deployment
python deploy/deploy.py --info      # Show deployment info
```

## Development

```bash
make lint      # Run ruff linter
make test      # Run all tests (148 tests)
make format    # Auto-format + sort imports
make check     # Lint + tests
```

## Cleanup

Remove cloud resources (BQ datasets, GCS blobs) and local output:

```bash
python scripts/cleanup.py --dry-run    # Preview
python scripts/cleanup.py              # Interactive confirmation
python scripts/cleanup.py --yes        # Skip confirmation
```

Selectively skip with `--skip-bq`, `--skip-gcs`, `--skip-local`, `--skip-agent-engine`.
