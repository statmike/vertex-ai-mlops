# Data Onboarding Chat Agent — Optimization Plans

## Current State (2026-03-27)

The chat agent system (`agent_chat`) routes user questions to three personas:
- **Data Analyst** → `agent_context` (reranker) → `agent_convo` (Conversational Analytics API)
- **Data Engineer** → `agent_engineer` (meta_chat via Conversational Analytics API)
- **Catalog Explorer** → `agent_catalog` (semantic search + direct column lookup)

We've completed a major optimization pass and are partway through a second refinement pass. All 289 unit tests pass. The system is functional but has remaining quality issues documented below.

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

### Optimization 2: Targeted Improvements (partially complete)

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

## Known Issues (TODO)

### P0: Critical

1. **Reranker callback double-invocation**: The `before_agent_callback` runs every time `agent_context` is invoked. When agent_convo finishes and control returns to agent_chat, agent_chat sometimes re-invokes agent_context, causing the reranker to run twice. This wastes ~20s per redundant call. Seen in data-analyst-q1 (15 events vs expected 8).

   **Possible fixes:**
   - Check `callback_context.state.get("reranker_result")` at the top of the callback — if already set, skip the reranker and return None immediately
   - Update `agent_chat` prompts to never re-invoke `agent_context` after `agent_convo` has answered

2. **data-analyst-q6 excessive events (19)**: The LLM in agent_context doesn't always transfer to agent_convo on the first try. Sometimes it calls sample_data or loops. The instruction says "transfer immediately" but the LLM ignores it.

   **Possible fix:** Remove `sample_data` from agent_context tools entirely so the LLM has no tools to distract it — its only option is to transfer.

### P1: Routing

3. **catalog-explorer-q4 misrouted to agent_context**: "What columns are shared between underlying_eod and underlying_trades?" — router interprets this as a Data Analyst question (comparing tables). It's borderline. Could fix by adding "What columns are shared between X and Y?" to Catalog Explorer examples.

4. **catalog-explorer-q9 misrouted to agent_context**: "Which tables contain VIX-related data?" — router interprets as Data Analyst. Could fix by adding "Which tables contain X data?" to Catalog Explorer examples.

5. **agent_chat routing instruction conflict**: The prompt says "When in doubt, prefer the Data Analyst persona for data questions" — this biases catalog questions toward Data Analyst. Consider removing or qualifying this rule.

### P2: Answer Quality

6. **catalog-explorer-q7 still weak**: "What reference tables exist and what do they look up?" — the concept of "reference table" isn't in any chunk text. Requires either:
   - Adding category/role annotations during onboarding (e.g., "reference table", "fact table")
   - Teaching the agent to search for patterns like "ID table", "lookup", "mapping"

7. **catalog-explorer-q1 inherently unanswerable**: "What does PRVDR_NUM mean?" — PRVDR_NUM doesn't exist in the Cboe dataset (it's from healthcare data). The agent correctly reports not finding it. This is expected behavior.

8. **data-engineer-q5 answer has error**: The Conversational Analytics API couldn't find `INFORMATION_SCHEMA` dataset. The agent returned an error message instead of actual table counts. The `meta_chat` tool sends queries to the Conversational Analytics API which may not have access to INFORMATION_SCHEMA. May need a direct BQ query fallback.

9. **Glossary term format changed**: All conversational_chat calls log a warning: `Failed to parse glossary_terms field: "GlossaryTerm" has no field named "term"`. The Conversational Analytics API changed the GlossaryTerm proto — it now uses `displayName` instead of `term`. Need to update `util_conversational_api.py` to use `displayName`.

### P3: Performance

10. **Table-summary chunks not yet populated**: The `table_summary` chunk type was added to the chunking utility but existing onboarded data doesn't have these chunks. Need to either:
    - Re-run the context population step (`populate_context` tool)
    - Write a migration script to generate summary chunks from existing `table_documentation` data

11. **Data Analyst times increased**: The callback adds 1 LLM turn (~2-3s) for the transfer. Plus the LLM sometimes doesn't transfer cleanly, adding extra events. Net effect: average Data Analyst time went from 94s → 110s per question. The callback still prevents bounces (Q3 was 101s → 85s) but clean questions are slightly slower.

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
│  agent_engineer
│    → meta_chat (6 fixed meta tables)
│    → calls Conversational Analytics API via shared util
│
└─ Catalog Explorer path:
   agent_catalog
     → search_context (AI.SEARCH over context_chunks)
     → get_table_columns (direct table_documentation query)
```

### Key Files

| File | Purpose |
|------|---------|
| `agent_chat/prompts.py` | Router classification + disambiguation guide |
| `agent_context/catalog.py` | Module-level `_catalog_data` dict + `_catalog_summary` string |
| `agent_context/tools/callback_rerank.py` | `before_agent_callback` — runs reranker, stores in state, returns None |
| `agent_context/tools/util_rerank.py` | `call_reranker_two_pass()`, `_shortlist_pass()`, `_detail_pass()` |
| `agent_context/schemas.py` | `ShortlistEntry/Response`, `RankedTable`, `RerankerResponse` |
| `agent_convo/tools/function_tool_conversational_chat.py` | Auto-picks tables from `reranker_result` in state |
| `agent_convo/tools/util_conversational_api.py` | Shared Conversational Analytics API calling logic |
| `agent_engineer/tools/function_tool_meta_chat.py` | Uses shared util, 6 fixed meta tables |
| `agent_catalog/tools/function_tool_search_context.py` | AI.SEARCH over `context_chunks` table |
| `agent_catalog/tools/function_tool_get_table_columns.py` | Direct column listing from `table_documentation` |
| `agent_orchestrator/util_context_chunks.py` | Chunking logic (now includes `table_summary` type) |
| `agent_orchestrator/config.py` | All config: models, datasets, retry options |

### Test & Evaluation Files

| File | Purpose |
|------|---------|
| `examples/cboe/cboe_questions.json` | 30 questions (10 per persona) |
| `examples/cboe/run_cboe_questions.py` | Programmatic runner using ADK `InMemoryRunner` |
| `examples/cboe/build_cboe_results.py` | Builds markdown Results section for `cboe.md` |
| `examples/cboe/cboe.md` | Full documentation + results |
| `examples/cboe/results/cboe_results.json` | Current (V3) results |
| `examples/cboe/results/cboe_results_v1.json` | Baseline results |
| `examples/cboe/results/cboe_results_v2.json` | Broken V2 (callback returned Content) |

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
uv run python -m pytest -q                                      # 289 tests
```

---

## Recommended Next Steps (Priority Order)

### 1. Fix callback double-invocation (P0, ~15 min)

In `callback_rerank.py`, add a guard at the top:

```python
if callback_context.state.get("reranker_result"):
    return None  # Already ran — skip
```

This prevents the reranker from running twice when agent_chat re-invokes agent_context.

### 2. Fix glossary term format (P2, ~10 min)

In `util_conversational_api.py`, find where `GlossaryTerm` is constructed and change `term=` to `displayName=`. The Conversational Analytics API proto changed field names.

### 3. Remove sample_data from agent_context tools (P0, ~5 min)

In `agent_context/tools/__init__.py`, change `TOOLS = [sample_data]` to `TOOLS = []`. This removes the distraction — the LLM's only option after the callback is to transfer.

### 4. Fine-tune catalog explorer routing (P1, ~10 min)

Add to Catalog Explorer examples in `agent_chat/prompts.py`:
- "What columns are shared between X and Y?"
- "Which tables contain X data?"

And update the disambiguation guide:
- "What columns are shared?" → Catalog Explorer (documentation)
- "Which tables contain X?" → Catalog Explorer (documentation)

### 5. Populate table-summary chunks for Cboe data (P3, ~20 min)

Write a one-off script or re-run `populate_context` to insert `table_summary` chunks for existing tables. This will improve semantic search for "describe all columns" questions.

### 6. Re-run evaluation after fixes

```bash
mv examples/cboe/results/cboe_results.json examples/cboe/results/cboe_results_v3.json
uv run python examples/cboe/run_cboe_questions.py --delay 8
```

Compare V3 → V4 to confirm fixes.

---

## Lesson Learned: ADK Callback + Transfer

When `before_agent_callback` returns `types.Content`, the framework sets `end_invocation = True` and the agent's LLM never runs. This means `transfer_to_agent` set on `_event_actions` during the callback creates an event with the transfer action, but the framework behavior was unreliable — agent_convo was never actually invoked (V2 results showed raw reranker output as final answers).

**Working pattern:** The callback returns `None` after storing results in state. This lets the LLM run with a minimal instruction ("just transfer to agent_convo"), which reliably triggers the transfer. The tradeoff is one extra LLM call (~2-3s) but the transfer actually works.

The bigquery-context project's callback pattern (return Content to skip LLM entirely) works for **leaf agents** that don't need to transfer. For agents that need to transfer to a peer, return `None` and let the LLM handle the transfer.
