# Data Onboarding Chat Agent — Optimization Plans

## Current State (2026-03-27)

The chat agent system (`agent_chat`) routes user questions to three personas:
- **Data Analyst** → `agent_context` (reranker) → `agent_convo` (Conversational Analytics API)
- **Data Engineer** → `agent_engineer` (meta_chat via Conversational Analytics API)
- **Catalog Explorer** → `agent_catalog` (semantic search + direct column lookup)

We've completed three optimization passes plus targeted fixes. All 326 unit tests pass. V4 evaluation shows -17% total time and correct answers across all three personas.

---

## What Was Done

### Optimization 1: Two-Pass Reranker + Structured Catalog

**Problem:** The Data Analyst path timed out (499) because the reranker sent full metadata for all 58 tables in one Gemini call. Startup also made redundant lookupContext REST calls.

**Solution implemented:**

1. **Structured catalog** (`agent_context/catalog.py`): Module-level `_catalog_data` dict (full metadata per table) and `_catalog_summary` string (compact text). Loaded once at startup from `data_catalog` and `table_documentation`. No lookupContext calls.

2. **Two-pass reranker** (`agent_context/tools/util_rerank.py`):
   - Pass 1 (shortlist): Compact summaries for ALL tables → top 10 candidates
   - Pass 2 (detail): Full metadata for top 10 → final ranking with key columns, SQL hints, joins
   - Uses `ShortlistResponse` and `RerankerResponse` pydantic schemas

3. **Auto-pick tables** (`agent_convo/tools/function_tool_conversational_chat.py`): `bigquery_tables` parameter is now optional. When not provided, auto-extracts from `reranker_result` in session state via `_tables_from_reranker()`.

4. **Shared Conversational Analytics API util** (`agent_convo/tools/util_conversational_api.py`): Common logic for session management, response processing, chart handling. Used by both `conversational_chat` and `meta_chat`.

5. **Removed tools:** `discover_datasets`, `find_tables`, `get_table_context` from agent_context (replaced by pre-loaded catalog + reranker).

### Optimization 2: Targeted Improvements

**Changes implemented:**

1. **Router prompt fixes** (`agent_chat/prompts.py`):
   - Added Data Analyst examples: "What are the names/values of trade conditions?"
   - Added Data Engineer examples: "How many tables created?", "What relationships detected?", "Which tables partitioned?"
   - Added Disambiguation Guide section with explicit routing rules

2. **Deterministic reranker callback** (`agent_context/tools/callback_rerank.py`):
   - `before_agent_callback` on `agent_context` runs the two-pass reranker automatically
   - Returns `None` so the LLM gets a turn to transfer to `agent_convo`
   - Stores `reranker_result` and `reranker_markdown` in session state
   - Removed `rerank_tables` from the tools list (only `sample_data` remains)

3. **Table-summary chunks** (`agent_orchestrator/util_context_chunks.py`):
   - New `table_summary` chunk type: single chunk per table listing ALL column names + types + descriptions
   - Helps "describe all columns in table X" searches find a comprehensive chunk
   - **NOTE:** These chunks only exist for FUTURE onboardings. The current Cboe data needs to be re-onboarded or have chunks manually inserted to benefit.

4. **`get_table_columns` tool** (`agent_catalog/tools/function_tool_get_table_columns.py`):
   - Direct query to `table_documentation` to list all columns for a specific table
   - No semantic search needed — returns complete, structured output
   - Updated `agent_catalog/prompts.py` with guidance on when to use each tool

---

## Test Results: V1 vs V3 Comparison

We ran 30 questions across 3 personas. Results saved in `examples/cboe/results/`:
- `cboe_results_v1.json` — baseline (before optimizations 2)
- `cboe_results_v2.json` — callback returned Content (broken — agent_convo never invoked)
- `cboe_results.json` — current (V3, callback returns None)

### Key Wins

| Question | V1 | V3 | Notes |
|----------|----|----|-------|
| data-engineer-q5 "How many tables created?" | 216s / 29 events | **28.8s / 5 events** | Was bouncing across 5 agents. Now correctly routed. |
| data-engineer-q9 "Relationships detected?" | Error (misrouted to catalog) | **75.6s / 5 events** | FIXED — correct routing + substantive answer |
| data-analyst-q6 "Names of trade conditions?" | Error (misrouted to catalog) | **128s / 19 events** | FIXED — now queries actual data, lists 9 conditions |
| data-analyst-q3 "Compare short sale volume" | 101s / 17 events (bounced) | **85s / 8 events** | Callback ensures reranker always runs |
| data-engineer-q3 "ZIP archives vs direct?" | Stub answer (10.8s) | **96.8s / 5 events** | FIXED — complete answer (61 direct, 27 ZIP) |
| catalog-explorer-q2 "Describe underlying_eod" | Only 1 column found | **All 12 columns listed** | `get_table_columns` tool working |
| catalog-explorer-q3 "Vol surface relationships" | "couldn't find" | Detailed comparison of all 4 tables | Multiple search calls + better synthesis |

### Per-Persona Summary

| Persona | V1 Time | V3 Time | V1 Events | V3 Events |
|---------|---------|---------|-----------|-----------|
| Data Analyst | 937s | 1106s (+18%) | 94 | 98 |
| Data Engineer | 554s | 503s (-9%) | 76 | 50 (-34%) |
| Catalog Explorer | 104s | 246s (+137%) | 50 | 60 |

Total time increased because previously-erroring questions now actually do work (Q6 went from 8s error → 128s real answer).

---

## Known Issues — All Resolved

All issues from the original TODO have been addressed:

| # | Issue | Status | Fix |
|---|-------|--------|-----|
| 1 | Reranker callback double-invocation | **FIXED** (Opt 3) | Guard in `callback_rerank.py` checks state |
| 2 | data-analyst-q6 excessive events (19→14) | **FIXED** (Opt 3) | Removed `sample_data` from agent_context tools |
| 3 | catalog-explorer-q4 misrouted | **FIXED** (Opt 3) | Added routing examples + disambiguation rules |
| 4 | catalog-explorer-q9 misrouted | **FIXED** (Opt 3) | Added routing examples |
| 5 | Routing bias toward Data Analyst | **FIXED** (Opt 3) | Replaced with structured guidance |
| 6 | catalog-explorer-q7 weak answer | **FIXED** (Opt 3) | `list_all_tables` tool enables table-role reasoning |
| 7 | catalog-explorer-q1 unanswerable | **Expected** | PRVDR_NUM not in Cboe data, correctly reports not found |
| 8 | data-engineer-q5 INFORMATION_SCHEMA error | **FIXED** (Opt 3) | Enhanced `meta_chat` system instruction + `data_catalog` guidance |
| 9 | Glossary term format (`term` → `displayName`) | **FIXED** (Opt 3) | Updated `util_build_context.py` |
| 10 | Table-summary chunks not populated | **Superseded** (Opt 3) | Context cache with Dataplex lookupContext replaces chunk approach |
| 11 | Data Analyst times increased | **FIXED** (Opt 3) | Reranker guard eliminated double-invocations, -22% total time |
| 12 | agent_engineer bounce-back routing | **FIXED** (post-Opt 3) | `disallow_transfer_to_parent=True` + single-call prompt guidance |

### Minor Remaining Observations (not blocking)

- **catalog-explorer-q9**: Agent used `search_context` instead of `list_all_tables`, missing `underlying_eod` as a VIX table. The tool exists but the LLM chose the wrong one. Could improve with prompt tweaks.
- **data-engineer-q5**: Correct answer but 140.8s — the Conversational Analytics API takes ~131s to process the multi-table row-count query. This is API latency, not a routing or code issue.

---

## Architecture Reference

### Agent Flow

```
agent_chat (root router, LLM: classify + route)
│
├─ Data Analyst path:
│  agent_context (before_agent_callback: rerank_and_transfer)
│    → callback runs two-pass reranker, stores in state
│    → LLM transfers to agent_convo
│  agent_convo
│    → conversational_chat (auto-picks tables from state)
│    → calls Conversational Analytics API
│
├─ Data Engineer path:
│  agent_engineer (disallow_transfer_to_parent=True)
│    → meta_chat (6 fixed meta tables, enhanced system instruction)
│    → calls Conversational Analytics API via shared util
│
└─ Catalog Explorer path:
   agent_catalog
     → search_context (AI.SEARCH over context_chunks)
     → get_table_columns (cache-first, BQ fallback)
     → list_all_tables (full inventory from context cache)
```

### Key Files

| File | Purpose |
|------|---------|
| `agent_chat/prompts.py` | Router classification + disambiguation guide |
| `agent_context/catalog.py` | Module-level `_catalog_data` dict + `_catalog_summary` string (populated from context cache) |
| `agent_context/context_cache/cache.py` | Pre-fetched metadata with brief/detailed views (Dataplex lookupContext + BQ fallback) |
| `agent_context/context_cache/util_lookup_context.py` | Dataplex lookupContext REST client (batched, 10/call) |
| `agent_context/tools/callback_rerank.py` | `before_agent_callback` — runs reranker, stores in state, returns None |
| `agent_context/tools/util_rerank.py` | `call_reranker_two_pass()`, `_shortlist_pass()`, `_detail_pass()` |
| `agent_context/schemas.py` | `ShortlistEntry/Response`, `RankedTable`, `RerankerResponse` |
| `agent_convo/tools/function_tool_conversational_chat.py` | Auto-picks tables from `reranker_result` in state |
| `agent_convo/tools/util_conversational_api.py` | Shared Conversational Analytics API calling logic |
| `agent_engineer/tools/function_tool_meta_chat.py` | Uses shared util, 6 fixed meta tables |
| `agent_catalog/tools/function_tool_search_context.py` | AI.SEARCH over `context_chunks` table |
| `agent_catalog/tools/function_tool_get_table_columns.py` | Cache-first column listing, BQ fallback |
| `agent_catalog/tools/function_tool_list_all_tables.py` | Full table inventory from context cache |
| `agent_convo/tools/util_build_context.py` | Enriched Context builder (glossary uses `displayName`) |
| `agent_orchestrator/util_context_chunks.py` | Chunking logic (includes `table_summary` type) |
| `agent_orchestrator/config.py` | All config: models, datasets, `CHAT_SCOPE`, `TOP_K`, retry options |

### Test & Evaluation Files

| File | Purpose |
|------|---------|
| `examples/cboe/cboe_questions.json` | 30 questions (10 per persona) |
| `examples/cboe/run_cboe_questions.py` | Programmatic runner using ADK `InMemoryRunner` |
| `examples/cboe/build_cboe_results.py` | Builds markdown Results section for `cboe.md` |
| `examples/cboe/cboe.md` | Full documentation + results |
| `examples/cboe/results/cboe_results.json` | Current (V4) results |
| `examples/cboe/results/cboe_results_v1.json` | Baseline results |
| `examples/cboe/results/cboe_results_v2.json` | Broken V2 (callback returned Content) |
| `examples/cboe/results/cboe_results_v3.json` | V3 results (before Optimization 3) |

### Running the Evaluation

```bash
# From data-onboarding project root:
uv run python examples/cboe/run_cboe_questions.py              # run all 30
uv run python examples/cboe/run_cboe_questions.py --resume      # skip completed
uv run python examples/cboe/run_cboe_questions.py --persona "Data Analyst"  # one persona
uv run python examples/cboe/run_cboe_questions.py --id data-analyst-q3      # one question

# Build the results markdown:
uv run python examples/cboe/build_cboe_results.py --write       # update cboe.md

# Run tests:
uv run python -m pytest -q                                      # 326 tests
```

---

## Optimization 3: Context Cache + Scoping + Bug Fixes (2026-03-30)

All 8 items implemented, plus 2 additional fixes. 326 tests pass.

### Changes Implemented

1. **Reranker double-invocation guard** (`callback_rerank.py`):
   - Checks `callback_context.state.get("reranker_result")` at the top — if already set, returns None immediately
   - Prevents the ~20s wasted reranker call when agent_chat re-invokes agent_context

2. **Removed sample_data from agent_context tools** (`agent_context/tools/__init__.py`):
   - `TOOLS = []` — the LLM has no tools to distract it, must transfer to agent_convo immediately

3. **Context cache module** (`agent_context/context_cache/`):
   - `cache.py`: Pre-fetches metadata at startup with brief/detailed views per table
   - `util_lookup_context.py`: REST client for Dataplex lookupContext API (batched, 10 entries/call)
   - Strategy: tries Dataplex lookupContext first (rich metadata with dataProfile stats — sample values, null ratios, cardinality), falls back to BQ `table_documentation`
   - `catalog.py` updated to populate from the context cache instead of querying BQ directly

4. **Table ID normalizer** (`util_rerank.py`):
   - `_normalize_table_id()` regex strips Dataplex path format (e.g., `projects.proj.datasets.ds.tables.tbl` → `proj.ds.tbl`)
   - Applied after every reranker call to prevent broken table references downstream

5. **Catalog explorer routing improvements** (`agent_chat/prompts.py`):
   - Added examples: "What columns are shared between X and Y?", "Which tables contain X data?", "What reference tables exist?"
   - Added disambiguation rules for shared-column and contains-data questions
   - Replaced biased "prefer Data Analyst" rule with structured guidance: meaning/structure → Catalog Explorer, query/compute → Data Analyst

6. **Cache-powered column lookups** (`function_tool_get_table_columns.py`):
   - Checks context cache first (instant, no BQ call) before falling back to BQ table_documentation
   - Uses `get_table_columns_from_cache()` which matches by short name or full ref

7. **Glossary displayName fix** (`util_build_context.py`):
   - Changed `{"term": term}` to `{"displayName": term}` to match current Conversational Analytics API proto

8. **Dataset/table scoping config** (`agent_orchestrator/config.py`):
   - `CHAT_SCOPE` env var (comma-separated): `"cboe_bronze"` (all tables) or `"ds.table_a,ds.table_b"` (specific)
   - Helpers: `get_scope_datasets()`, `get_scoped_tables()`, `is_table_in_scope()`, `get_dataplex_entry_name()`
   - When empty (default), discovers datasets dynamically from `data_catalog`
   - `TOP_K` config added (default 10, overridable via env var)

### New/Updated Files

| File | Change |
|------|--------|
| `agent_context/context_cache/__init__.py` | New — cache module public API |
| `agent_context/context_cache/cache.py` | New — cache with brief/detailed views, public accessors |
| `agent_context/context_cache/util_lookup_context.py` | New — Dataplex lookupContext REST client |
| `agent_context/catalog.py` | Rewritten — now populates from context cache |
| `agent_context/tools/__init__.py` | `TOOLS = []` |
| `agent_context/tools/callback_rerank.py` | Added double-invocation guard |
| `agent_context/tools/util_rerank.py` | Added `_normalize_table_id()`, applied after reranker calls |
| `agent_chat/prompts.py` | Added catalog explorer examples + disambiguation rules |
| `agent_catalog/tools/function_tool_get_table_columns.py` | Cache-first column lookup |
| `agent_convo/tools/util_build_context.py` | `displayName` instead of `term` |
| `agent_orchestrator/config.py` | Added `CHAT_SCOPE`, `TOP_K`, scoping helpers, `get_dataplex_entry_name()` |

### New Test Files

| File | Tests |
|------|-------|
| `agent_context/tests/unit/test_context_cache.py` | Cache API, brief/detailed views, column lookup |
| `agent_catalog/tests/unit/test_get_table_columns.py` | Cache-hit path, cache-miss fallback |
| Updated `test_rerank.py` | `_normalize_table_id()` tests, double-invocation guard test |
| Updated `test_build_context.py` | `displayName` field assertion |
| Updated `test_config.py` | `CHAT_SCOPE` parsing and helper tests |

---

### Additional Fixes (same session)

9. **`list_all_tables` tool for agent_catalog** (`agent_catalog/tools/function_tool_list_all_tables.py`):
   - Returns every onboarded table with description, column count, and column names from the context cache
   - Enables the catalog agent to reason about table roles (reference, fact, etc.) without semantic search
   - Prompt updated to guide the agent to use this for broad "what tables exist?" questions
   - Falls back to BQ `data_catalog` query if cache is empty

10. **Enhanced `meta_chat` system instruction** (`agent_engineer/tools/function_tool_meta_chat.py`):
    - Added per-table guidance describing what each meta table contains
    - Explicitly directs the API to use `data_catalog.tables_created` for table-count questions
    - Tells the API "Do NOT use INFORMATION_SCHEMA" to prevent the error

11. **Prevent agent_engineer bounce-back** (`agent_engineer/agent.py`):
    - Set `disallow_transfer_to_parent=True` — agent must answer or explain, never bounce back to router
    - Eliminates re-routing loops that caused 16-event traces and incorrect persona switches

12. **Single meta_chat call guidance** (`agent_engineer/prompts.py`):
    - Added "Call `meta_chat` once per question" — present partial results rather than retrying
    - Eliminated double `meta_chat` calls that added 100-200s of wasted API time

---

## V4 Evaluation Results (2026-03-30)

30/30 questions completed. Results in `examples/cboe/results/cboe_results.json`, V3 archived as `cboe_results_v3.json`.

Data Engineer questions re-run after fixing bounce-back routing (`disallow_transfer_to_parent=True`) and adding single-call guidance to `agent_engineer` prompt.

### Per-Persona Timing (V3 → V4)

| Persona | V3 Total | V4 Total | Delta | V3 Events | V4 Events |
|---------|----------|----------|-------|-----------|-----------|
| Data Analyst | 1106.3s | 866.9s | **-239.4s (-22%)** | 98 | 86 |
| Catalog Explorer | 246.5s | 111.9s | **-134.6s (-55%)** | 60 | 58 |
| Data Engineer | 502.9s | 557.0s | +54.1s (+11%) | 50 | 50 |
| **Total** | **1855.7s** | **1535.8s** | **-319.9s (-17%)** | **208** | **194** |

### Wins

| Question | V3 → V4 | Improvement | Reason |
|----------|---------|-------------|--------|
| catalog-explorer-q9 (VIX tables) | 87.2s → 13.7s | **-73.5s** | `list_all_tables` replaces multi-search |
| data-analyst-q6 (trade conditions) | 128.1s → 65.5s | **-62.6s** | Reranker guard + fewer events (19→14) |
| data-engineer-q3 (ZIP vs direct) | 96.8s → 38.5s | **-58.3s** | Better system instruction, single call |
| data-analyst-q5 (CAD/JPY) | 154.8s → 97.5s | **-57.3s** | Reranker guard |
| data-analyst-q1 (exchanges) | 117.0s → 62.2s | **-54.8s** | Reranker guard + fewer events (15→8) |
| catalog-explorer-q4 (shared cols) | 57.4s → 6.4s | **-51.0s** | Cache-powered `get_table_columns` |
| data-analyst-q10 (VIX intraday) | 152.6s → 118.1s | **-34.5s** | Reranker guard |
| data-engineer-q9 (relationships) | 75.6s → 63.7s | **-11.9s** | No more double meta_chat |
| data-engineer-q10 (partitioning) | 29.5s → 18.0s | **-11.5s** | Single call |
| catalog-explorer-q3 (vol surfaces) | 28.5s → 19.0s | **-9.5s** | Cache-powered search |
| catalog-explorer-q7 (ref tables) | 15.2s → 9.0s | **-6.2s** | `list_all_tables` + correct answer |

### Quality Improvements

- **catalog-explorer-q7** "What reference tables exist?": V3 returned generic search results. V4 correctly identifies `ftref_*` tables as reference/lookup tables.
- **catalog-explorer-q9** "Which tables contain VIX-related data?": V3 took 87s with 3 search rounds. V4 uses `list_all_tables` in 13.7s.
- **catalog-explorer-q4** "Shared columns": V3 took 57s with 8 events. V4 uses cached column lookup in 6.4s with 5 events.
- **data-engineer-q5** "How many tables created?": V3 returned INFORMATION_SCHEMA error (no answer). V4 correctly reports 6 metadata + 58 data tables with row counts (140.8s — the API query itself is slow but the answer is correct).
- **data-analyst-q1** "What exchanges?": V3 took 15 events. V4 takes 8 events — reranker guard eliminated the double-invocation.

### Remaining Variance

- **data-engineer-q5** (140.8s): Correctly routed, single meta_chat call, correct answer. The 131s is pure Conversational Analytics API processing time — the query requires scanning multiple tables to count rows.
- **data-engineer-q2, q7, q8** (+8-16s): API latency variance, not routing issues. All use single calls now.

---

## Lesson Learned: ADK Callback + Transfer

When `before_agent_callback` returns `types.Content`, the framework sets `end_invocation = True` and the agent's LLM never runs. This means `transfer_to_agent` set on `_event_actions` during the callback creates an event with the transfer action, but the framework behavior was unreliable — agent_convo was never actually invoked (V2 results showed raw reranker output as final answers).

**Working pattern:** The callback returns `None` after storing results in state. This lets the LLM run with a minimal instruction ("just transfer to agent_convo"), which reliably triggers the transfer. The tradeoff is one extra LLM call (~2-3s) but the transfer actually works.

The bigquery-context project's callback pattern (return Content to skip LLM entirely) works for **leaf agents** that don't need to transfer. For agents that need to transfer to a peer, return `None` and let the LLM handle the transfer.
