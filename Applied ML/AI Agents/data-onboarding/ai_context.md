# Data Onboarding — Development Log

## Milestone 1: Project Foundation

- Created full directory structure with 7 agent packages
- All agents are LlmAgent (no SequentialAgent/ParallelAgent for now)
- Config is centralized in `agent_orchestrator/config.py` (leaf module, no circular deps)
- BQ metadata tracking via `agent_orchestrator/util_metadata.py` (5 tables)
- BQ analytics plugin follows `image-to-graph` pattern
- Pipeline: acquire → discover → understand → design → [human] → implement → [human] → validate
- State keys documented in plan; agents communicate via `tool_context.state`

## Milestone 2: Dataform → Direct SQL + Dataplex Lineage

- Replaced Dataform-based implementation with direct SQL approach
  - Deleted: `function_tool_generate_dataform.py`, `function_tool_compile_dataform.py`, `util_dataform.py`
  - Added: `function_tool_create_external_tables.py`, `function_tool_execute_sql.py`, `util_sql.py`
  - Pipeline now: GCS file → external table (autodetect schema) → `CREATE TABLE AS SELECT` with CAST
- Added Dataplex Data Lineage API integration (`google-cloud-datacatalog-lineage`)
  - New utility: `agent_orchestrator/util_lineage.py` — Process/Run/Event creation, FQN builders
  - New tool: `agent_implement/tools/function_tool_publish_lineage.py`
  - Publishes 3 custom lineage events per file: URL→file URL, file URL→GCS, GCS→ext_table
  - BQ auto-captures the 4th hop: ext_table→materialized table
  - Multi-depth crawls collapse to meaningful nodes (starting URL → file URL)
- Added `external_table` column to `table_lineage` metadata table (with schema migration)
- Comprehensive test suite: 148 tests, all passing
  - New test files: `test_util_sql.py`, `test_create_external_tables.py`, `test_execute_sql.py`,
    `test_download_files.py`, `test_util_lineage.py`, `test_publish_lineage.py`
