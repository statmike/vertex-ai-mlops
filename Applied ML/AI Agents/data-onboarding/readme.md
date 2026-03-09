# Data Onboarding

A multi-agent ADK system that automates data onboarding into BigQuery. Takes a URL or GCS path, crawls/downloads files, analyzes schemas and context documents, designs BQ tables, generates Dataform SQLX, loads data, and validates — with full lineage tracking and human-in-the-loop checkpoints.

## Status

Under active development. See `ai_context.md` for the development log.

## Architecture

7 agents, each a Python package:

| Agent | Role |
|-------|------|
| `agent_orchestrator` | Root agent, routes between phases, owns shared config |
| `agent_acquire` | URL/GCS → staging (crawl, download, extract page content) |
| `agent_discover` | GCS inventory, file classification, change detection |
| `agent_understand` | Read files, analyze schemas, cross-reference with context |
| `agent_design` | Propose BQ table structures with rich descriptions |
| `agent_implement` | Generate Dataform SQLX, apply BQ metadata, changelog |
| `agent_validate` | Quality checks, lineage verification |

Pipeline flow: `acquire → discover → understand → design → [HUMAN APPROVAL] → implement → [HUMAN APPROVAL] → validate`

## Setup

```bash
make install
```

## Usage

```bash
adk web agent_orchestrator
```

## Development

```bash
make lint      # Run linter
make test      # Run all tests
make format    # Auto-format code
make check     # Lint + tests
```
