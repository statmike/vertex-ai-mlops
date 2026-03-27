# BigQuery Context — Current State & Next Steps

Last updated: 2026-03-27
Latest commit: `d00c0a37` (scope Dataplex semantic search to configured datasets)

---

## Current Architecture Summary

Five approaches to BigQuery table discovery, all sharing a common reranker. Each approach:
1. **Nominates** tables (discovers candidates via its strategy)
2. **Sends nominations to the reranker** (Gemini structured output → `RerankerResponse`)
3. **Stores both** `nominated_tables_{method}` and `reranker_result_{method}` in ADK session state

The orchestrator runs all five in parallel (`ParallelAgent`), then a compare agent reads all state keys and synthesizes results.

---

## The Three Metadata Retrieval Mechanisms

This is where the inconsistencies and improvement opportunities live. There are three fundamentally different ways we retrieve table metadata, and different approaches use different ones:

### 1. BQ `get_table_info` / `get_table()` (schema-only)

**Used by:** Approach 1 (via ADK BigQueryToolset), context_cache briefs
**API:** `bigquery.Client.get_table(full_id)` or ADK's `get_table_info` tool
**Returns:** Schema (column names, types, modes), description, row count, byte sizes, timestamps
**Does NOT include:** Data profiling stats, sample values, column descriptions from catalog
**Size:** ~600-2,000 chars per table

### 2. Dataplex `lookup_entry` (schema + catalog aspects)

**Used by:** Approach 2 (per-table after semantic search)
**API:** `dataplex_v1.CatalogServiceClient().lookup_entry()` with `EntryView.FULL`
**Returns:** Schema, display name, description, catalog aspects (schema aspect, storage aspect)
**Does NOT include:** Data profiling statistics, LLM-ready formatting
**Format:** Raw JSON dict extracted from protobuf → custom JSON summary
**Size:** ~1,000-3,000 chars per table

### 3. Dataplex `lookupContext` REST API (full YAML capsules)

**Used by:** Approaches 3, 4, 5 (via shared context_cache)
**API:** REST POST to `dataplex.googleapis.com/v1/projects/{project}/locations/{location}:lookupContext`
**Returns:** LLM-ready YAML including schema, descriptions, AND data profile statistics (null ratios, distinct values, sample values, min/max) when profiling has been run
**Format:** Pre-formatted YAML designed for LLM consumption
**Size:** ~600 chars without profiling, ~3,500+ chars with profiling
**Batch limit:** 10 entries per API call

---

## Current State by Approach

### Approach 1: BQ Metadata Tools (`agent_bq_tools`)

- **Discovery:** LLM-driven. Uses ADK `BigQueryToolset` (list_dataset_ids, list_table_ids, get_table_info)
- **Scope:** `after_tool_callback` (`filter_scope`) prunes list results to `config.SCOPE`
- **Metadata for reranker:** Schema-only from `get_table_info` (mechanism 1)
- **Reranker:** Called as an ADK tool by the LLM (`rerank_tables`)
- **Nominations:** `table_ids` parameter passed by LLM to `rerank_tables` tool → stored in `state["nominated_tables_bq_tools"]`
- **Status:** Working. No lookupContext used.

### Approach 2: Dataplex Search (`agent_dataplex_search`)

- **Discovery:** `search_entries` with `semantic_search=True`, scoped via `parent:` filter to SCOPE datasets
- **Scope:** `parent:` filter in query + `is_table_in_scope()` post-filter for table-level scope
- **Metadata for reranker:** `lookup_entry` per matched table → custom JSON summary (mechanism 2)
- **Reranker:** Called as direct function in `before_agent_callback`
- **Nominations:** Table IDs extracted during lookup step → stored in `state["nominated_tables_dataplex_search"]`
- **Status:** Working. Does NOT use lookupContext — uses the weaker `lookup_entry` instead.

### Approach 3: Dataplex Context (`agent_dataplex_context`)

- **Discovery:** All in-scope tables from shared context cache (pre-populated at startup)
- **Scope:** Built into cache population (only fetches scoped entries)
- **Metadata for reranker:** Full YAML capsules from `lookupContext` via shared cache (mechanism 3) — `get_all_detailed()` returns dataset context + all table YAML
- **Reranker:** Called as direct function in `before_agent_callback`
- **Nominations:** All cached table IDs → stored in `state["nominated_tables_dataplex_context"]`
- **Status:** Working. Uses the richest metadata. Sends ALL tables to reranker (no pre-filtering).

### Approach 4: Context Pre-Filter (`agent_context_prefilter`)

- **Discovery:** LLM reviews `get_all_briefs()` (brief summaries from BQ `get_table()`) embedded in system prompt, calls `nominate_tables` tool
- **Scope:** Built into cache (briefs only contain scoped tables)
- **Metadata for reranker:** `get_detailed_for_tables(nominated_ids)` — full YAML capsules for nominated tables only (mechanism 3, subset)
- **Reranker:** Called as direct function in `after_agent_callback`
- **Nominations:** LLM-selected table IDs from `nominate_tables` tool → stored in `state["nominated_tables_context_prefilter"]`
- **Status:** Working. Two-stage: briefs for LLM filtering, detailed YAML for reranking.

### Approach 5: Semantic Context (`agent_semantic_context`)

- **Discovery:** `search_entries` with `semantic_search=True`, scoped via `parent:` filter, then cache lookup for matched tables
- **Scope:** `parent:` filter + `is_table_in_scope()` + cache membership
- **Metadata for reranker:** `get_detailed_for_tables(matched_ids)` — full YAML capsules for search-matched tables (mechanism 3, subset)
- **Reranker:** Called as direct function in `before_agent_callback`
- **Nominations:** Matched table IDs from search → stored in `state["nominated_tables_semantic_context"]`
- **Status:** Working. Combines Approach 2's search with Approach 3's cached YAML.

---

## Key Issues to Address

### Issue 1: Approach 2 uses `lookup_entry` instead of `lookupContext`

**Current:** Approach 2 calls `dataplex_v1.CatalogServiceClient().lookup_entry()` per matched table. This returns schema + catalog aspects as raw JSON.

**Problem:** This is weaker metadata than what approaches 3, 4, 5 get from the shared cache (which uses `lookupContext` YAML with data profiling stats). The comparison between approaches is not apples-to-apples:
- Approaches 3/4/5: Full YAML with profiling stats (~3,500 chars/table)
- Approach 2: Schema + aspects JSON (~1,000-3,000 chars/table, no profiling)

**Options to consider:**
1. **Replace `lookup_entry` with `lookupContext`** in approach 2's callback — make per-table REST calls to `lookupContext` instead of SDK `lookup_entry` calls. This would give approach 2 the same metadata quality as approaches 3/4/5, but at the cost of REST calls instead of SDK calls.
2. **Use the shared cache for approach 2 also** — after search, look up matches in the cache (like approach 5 does). But this would make approach 2 nearly identical to approach 5 — the only difference would be that approach 2 does `lookup_entry` for tables NOT in cache.
3. **Keep as-is for comparison** — the difference in metadata richness IS part of what we're demonstrating. Approach 2 shows what you get from the SDK's `lookup_entry`, while approaches 3/4/5 show the richer `lookupContext`.

**Decision needed:** Is the comparison more valuable if all approaches use the same metadata quality, or if they show the actual differences between APIs?

### Issue 2: `function_tool_search_catalog.py` not updated with `parent:` scoping

**Current:** The standalone tool `agent_dataplex_search/tools/function_tool_search_catalog.py` still uses the old query format:
```python
query = f"({prompt}) AND system=BIGQUERY"
```

**Context:** This tool is NOT used when the agent runs as part of the orchestrator (the callback handles everything). It's only used if someone runs `agent_dataplex_search` standalone and the callback doesn't fire (which shouldn't happen in normal operation since the callback is wired up). Still, it should be consistent.

**Fix:** Update to use `parent:` dataset scoping like the callback does.

### Issue 3: How lookupContext is retrieved and stored in the cache

**Current flow in `context_cache/cache.py`:**
1. For each table: call `lookup_context([single_entry_name])` — makes one REST call per table
2. For each dataset: call `lookup_context_batched(dataset_entry_names)` — batches up to 10 per call
3. Table YAML stored as `_CACHE[full_id].detailed` = `f"## {full_id}\n{yaml_text}"`
4. Dataset YAML stored as `_DATASET_CONTEXT` (module-level string)
5. `get_all_detailed()` returns `f"# Dataset Context\n{_DATASET_CONTEXT}\n\n# Table Context\n{table_context}"`
6. `get_detailed_for_tables(ids)` returns only the table-level YAML (NO dataset context)

**Issues:**
- **Per-table lookupContext calls are not batched.** Each table makes a separate REST call (line 109: `lookup_context([entry_name])`). This could be batched using `lookup_context_batched` for efficiency.
- **Dataset context is only included in `get_all_detailed()`** (used by approach 3) but NOT in `get_detailed_for_tables()` (used by approaches 4 and 5). This means approaches 4 and 5 get table YAML only, missing dataset-level descriptions.
- **The `## {full_id}` header** is prepended to each table's YAML in the cache. This is fine but means the raw YAML from lookupContext is wrapped.

### Issue 4: Inconsistent metadata across approaches sent to the reranker

What each approach sends to `call_reranker()` as `candidate_metadata`:

| Approach | Format | Dataset context? | Data profiling? | Source |
|----------|--------|:---:|:---:|--------|
| 1 - BQ Tools | Custom text (schema + desc + rows) | No | No | `bq_client.get_table()` |
| 2 - Dataplex Search | JSON (schema + aspects) | No | No | `lookup_entry` SDK |
| 3 - Dataplex Context | YAML (full capsules) | **Yes** | **Yes** | `lookupContext` REST via cache |
| 4 - Context Pre-Filter | YAML (full capsules) | **No** | **Yes** | `lookupContext` REST via cache (subset) |
| 5 - Semantic Context | YAML (full capsules) | **No** | **Yes** | `lookupContext` REST via cache (subset) |

Note: Approaches 4 and 5 call `get_detailed_for_tables()` which does not include dataset context, while approach 3 calls `get_all_detailed()` which does.

### Issue 5: Dead code — standalone function tools for approach 2

`function_tool_search_catalog.py` and `function_tool_lookup_entry.py` exist in `agent_dataplex_search/tools/` but are NOT used when the callback handles everything. The `tools/__init__.py` imports them and defines `TOOLS = [search_catalog, lookup_entry]`, but `agent.py` sets `tools=[]` since the callback does the work. These tools exist as reference implementations but are effectively dead code.

---

## Potential Improvements (Not Yet Prioritized)

1. **Batch table-level lookupContext calls** in `cache.py` — currently makes one REST call per table. Could batch by dataset (up to 10 per call) for faster startup.

2. **Include dataset context in `get_detailed_for_tables()`** — so approaches 4 and 5 get the same dataset-level descriptions as approach 3.

3. **Option for approach 2 to use lookupContext** — either per-table REST calls or cache lookup, to get profiling stats in its metadata.

4. **Update standalone search tool** with `parent:` dataset scoping.

5. **Consider whether approach 2's `lookup_entry` should be replaced with cache lookup** — this would make it very similar to approach 5, but would standardize the metadata format.

---

## File Map (key files only)

```
bigquery-context/
├── config.py                         # SCOPE, get_datasets(), is_table_in_scope()
├── schemas.py                        # RerankerResponse Pydantic schema
│
├── context_cache/
│   ├── __init__.py                   # Exports: get_all_briefs, get_all_detailed, get_detailed_for_tables, get_table_ids
│   ├── cache.py                      # populate_cache() at import → _CACHE dict + _DATASET_CONTEXT str
│   └── util_lookup_context.py        # lookup_context() and lookup_context_batched() — REST calls
│
├── reranker/
│   ├── __init__.py                   # Exports TOOLS = [rerank_tables]
│   ├── function_tool_rerank.py       # rerank_tables() ADK tool — stores nominations + reranker result in state
│   └── util_rerank.py                # call_reranker() — Gemini structured output, RERANKER_SYSTEM_PROMPT
│
├── agent_bq_tools/                   # Approach 1
│   ├── agent.py                      # tools=[bq_toolset] + RERANKER_TOOLS, after_tool_callback=filter_scope
│   ├── callback_filter_scope.py      # Prunes list_dataset_ids/list_table_ids to SCOPE
│   └── prompts.py                    # Tells LLM to call rerank_tables with table_ids
│
├── agent_dataplex_search/            # Approach 2
│   ├── agent.py                      # tools=[], before_agent_callback=discover_and_rerank
│   └── tools/
│       ├── callback_discover_and_rerank.py   # search_entries(parent: scoped) → lookup_entry per table → rerank
│       ├── function_tool_search_catalog.py   # Standalone tool (NOT used by callback) — STILL HAS OLD QUERY
│       └── function_tool_lookup_entry.py     # Standalone tool (NOT used by callback)
│
├── agent_dataplex_context/           # Approach 3
│   ├── agent.py                      # tools=[], before_agent_callback=discover_and_rerank
│   └── tools/
│       ├── callback_discover_and_rerank.py   # get_all_detailed() from cache → rerank
│       └── function_tool_initialize_context.py  # Returns get_all_detailed() (not used by callback)
│
├── agent_context_prefilter/          # Approach 4
│   ├── agent.py                      # tools=PREFILTER_TOOLS, after_agent_callback=rerank_nominations
│   ├── prompts.py                    # Embeds get_all_briefs() in system prompt at module load
│   └── tools/
│       ├── function_tool_nominate_tables.py      # Stores table_ids in state["nominated_tables"]
│       └── callback_rerank_nominations.py        # get_detailed_for_tables() → rerank
│
├── agent_semantic_context/           # Approach 5
│   ├── agent.py                      # tools=[], before_agent_callback=discover_and_rerank
│   └── tools/
│       └── callback_discover_and_rerank.py  # search_entries(parent: scoped) → cache lookup → rerank
│
├── agent_orchestrator/               # Orchestrator
│   ├── agent.py                      # SequentialAgent: ParallelAgent(5 agents) → compare_results agent
│   └── prompts.py                    # Compare agent reads nominated_tables_* + reranker_result_* from state
│
└── bigquery_context.ipynb            # Notebook: step-by-step demo of all 5 approaches + compare section
```

---

## State Keys Used

Each approach stores two keys in ADK session state:

| State Key | Type | Description |
|-----------|------|-------------|
| `nominated_tables_bq_tools` | `list[str]` | Table IDs the LLM passed to `rerank_tables` |
| `nominated_tables_dataplex_search` | `list[str]` | Table IDs from semantic search matches |
| `nominated_tables_dataplex_context` | `list[str]` | All cached table IDs (= all in scope) |
| `nominated_tables_context_prefilter` | `list[str]` | Table IDs the LLM nominated from briefs |
| `nominated_tables_semantic_context` | `list[str]` | Table IDs from semantic search + cache |
| `reranker_result_bq_tools` | `str` (JSON) | `RerankerResponse.model_dump_json()` |
| `reranker_result_dataplex_search` | `str` (JSON) | `RerankerResponse.model_dump_json()` |
| `reranker_result_dataplex_context` | `str` (JSON) | `RerankerResponse.model_dump_json()` |
| `reranker_result_context_prefilter` | `str` (JSON) | `RerankerResponse.model_dump_json()` |
| `reranker_result_semantic_context` | `str` (JSON) | `RerankerResponse.model_dump_json()` |

Internal (approach 4 only):
| `nominated_tables` | `list[str]` | Set by `nominate_tables` tool, read by `rerank_nominations` callback |

---

## Recent Commit History

```
d00c0a37 feat(bigquery-context): scope Dataplex semantic search to configured datasets
6a78595e feat(bigquery-context): track nominations across all five approaches
7a80e2a6 docs(bigquery-context): notebook rerun with outputs for all five approaches
2ec290e4 feat(bigquery-context): add approaches 4 and 5 demonstrations to notebook
c256369c feat(bigquery-context): shared context cache, approaches 4 (pre-filter) and 5 (semantic context)
060fa3ed refactor(bigquery-context): rename agents to match APIs, extract callbacks, add scope filtering
0f26d916 feat(bigquery-context): deterministic callbacks, async reranker, model location config
1b24212d feat(bigquery-context): ADK multi-agent system comparing three BigQuery table discovery approaches
```
