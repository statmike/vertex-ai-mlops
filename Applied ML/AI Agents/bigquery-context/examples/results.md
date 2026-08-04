# NL2SQL retrieval benchmark — results

Six table-discovery approaches for BigQuery NL2SQL, scored on a factorial experiment that isolates **catalog enrichment** as the independent variable. See [`readme.md`](../readme.md) for the challenge and approach spec cards, and [`GROUND_TRUTH.md`](GROUND_TRUTH.md) for the grading rubric.

## Headline — discovery vs reranking

Recall decomposed into two stages: **discovery recall** (was the must-have table in the candidate set at all?) and **final recall** (did it survive the reranker's top-5 cut?). The gap between them is **rerank loss**. Means, not medians — the corpus is easy enough that medians saturate at 100% and hide the tail.

| Approach | Discovery recall | Final recall | Rerank loss |
|---|---|---|---|
| 1: BQ Tools (control) | 1.000 | 0.993 | 0.007 |
| 2: KC Search | 0.967 | 0.949 | 0.018 |
| 3: KC Context | 1.000 | 0.940 | 0.060 |
| 4: Pre-Filter | 1.000 | 0.976 | 0.024 |
| 5: Semantic | 0.967 | 0.945 | 0.022 |
| 6: Search Direct (control) | 0.967 | 0.967 | 0.000 |

_**Scoped semantic search retrieves the right tables — the reranker's job is precision, not recall recovery.** Once the search is scoped with the correct query syntax (a bare `parent:datasets/…` predicate; see Methodology), it returns a small, already-ranked, in-scope set that contains all must-have tables for 14 of the 16 multi-table questions — including the disparate joins — **before any reranking**. `Search Direct` takes that set as its answer with no LLM at all; `KC Search` and `Semantic` add a rerank on top of the identical retrieval, and the `Search Direct`-vs-`KC Search` gap measures exactly what that rerank buys. The search-based approaches show ~zero rerank loss: the reranker keeps the must-have tables search surfaced. The full-corpus approaches (`BQ Tools`, `KC Context`, `Pre-Filter`) see the whole scoped corpus, so their discovery recall is 1.0 by construction and any loss is purely at the reranker._

The **one** residual retrieval gap is a genuine relevance miss, not a scope or budget problem:

- **Relevance gap (one disparate join).** It takes **two factors together**: the required table is keyed to a *different geography* than the question names (a county question needing a ZIP-keyed population table) **and** the join is implied only by a computed ratio, sharing no salient term with the query — so it never ranks into the returned set. Matching the geography *or* naming the partner restores discovery to 100%, so neither factor alone is sufficient. The API returns *well under* the `page_size` budget (a handful of in-scope tables, all correctly scoped), so the budget is not the constraint; semantic relevance is. Raising `page_size` does not surface it (the count is governed by search's internal relevance cutoff, not the page size). The catalog-native fix is join-aware expansion (`frequent_joins`), not a wider page — see the worked example.

_This is the only case where a must-have table is absent **before** reranking, so it is the only recall the reranker cannot recover. Every other multi-table question — related and disparate alike — retrieves its full must-have set from the scoped search directly._


### Discovery recall by question category

| Category | 1: BQ Tools | 2: KC Search | 3: KC Context | 4: Pre-Filter | 5: Semantic | 6: Search Direct |
|---|---|---|---|---|---|---|
| single-table | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| multi-table-related | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| multi-table-disparate | 1.00 | 0.93 | 1.00 | 1.00 | 0.93 | 0.93 |
| trap | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |

_Where the candidate set is complete (1.00) vs missing a must-have table. With the scoped query the search-based approaches reach ~1.00 on `single-table` and `multi-table-related` questions; the only sub-1.00 cells are in `multi-table-disparate`, driven by a single **relevance gap** — a geography-mismatched, ratio-implied join (a county question needing a ZIP-keyed table) that search never surfaces (see the worked example)._

**The one residual gap.** For the multi-table-disparate question "Which US counties have the highest number of births per capita?", scoped search misses `population_by_zip_2010` in every run — even though search retrieves `population_by_zip_2010` readily for questions that name it. The failure is **two factors together**: the table is keyed to a *different geography* than the question names (a county question needing a ZIP-keyed table), and the join is implied only by a computed ratio, so it shares no salient term with the query. Either rescue — naming the partner ("…resident population") or matching the geography (a ZIP-anchored question) — restores discovery to 100%. `3: KC Context` sidesteps it by seeing the whole scoped corpus and carrying the table into reranking; the catalog-native fix is join-aware expansion (`frequent_joins`).

## Summary metrics — all questions, all tiers

| Metric | 1: BQ Tools | 2: KC Search | 3: KC Context | 4: Pre-Filter | 5: Semantic | 6: Search Direct |
|---|---|---|---|---|---|---|
| Final recall | 100% | 100% | 100% | 100% | 100% | 100% |
| Discovery recall | 100% | 100% | 100% | 100% | 100% | 100% |
| Precision | 100% | 100% | 100% | 100% | 100% | 50% |
| nDCG@5 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.97 |
| Latency p50 (s) | 39.48 | 8.57 | 3.99 | 14.60 | 6.06 | 2.09 |
| Reranker tokens | 3470 | 8388 | 44020 | 10749 | 14909 | 0 |

_Values are **medians** across all approach-runs — they saturate at 100% on this easy corpus, which is why the headline above uses means to expose the tail. Recall counts `must_have` tables; precision credits `must_have`+`nice_to_have` and is diluted by ranked distractors. See [`GROUND_TRUTH.md`](GROUND_TRUTH.md)._

## Enrichment response — final recall by tier

| Approach | 0 · schema | 1 · +profiling | 2 · +glossary | 3 · +guidelines | Δ (t3−t0) |
|---|---|---|---|---|---|
| 1: BQ Tools (control) | 100% | 100% | 100% | 100% | +0% |
| 2: KC Search (context) | 100% | 100% | 100% | 100% | +0% |
| 3: KC Context (context) | 100% | 100% | 100% | 100% | +0% |
| 4: Pre-Filter (context) | 100% | 100% | 100% | 100% | +0% |
| 5: Semantic (context) | 100% | 100% | 100% | 100% | +0% |
| 6: Search Direct (control) | 100% | 100% | 100% | 100% | +0% |

_The tier axis: controls (`BQ Tools`, `Search Direct`) read no reranker enrichment (`BQ Tools` reads BQ schema; `Search Direct` applies no reranker at all); context approaches feed progressively richer metadata to the reranker. On this corpus final recall is flat across tiers — enrichment does not move top-5 recall here because scoped search already retrieves the must-have tables (see the headline above), so there is little recall left for richer metadata to recover. 🟢 would mark a context approach gaining >5pp from tier 0 → tier 3._


## Rank quality by category — nDCG@5 at tier 3

**nDCG@5** (normalized discounted cumulative gain over the top 5) scores *ranking order*, not just presence: it rewards putting the most relevant table highest — `must_have` earns gain 2, `nice_to_have` gain 1, a `distractor` gain 0 — and discounts each hit by its rank, then normalizes against the ideal ordering so **1.00 is a perfect ranking**. Recall asks *was the table found?*; nDCG@5 asks *was it ranked well, and did junk stay out of the top 5?*

| Category | 1: BQ Tools | 2: KC Search | 3: KC Context | 4: Pre-Filter | 5: Semantic | 6: Search Direct |
|---|---|---|---|---|---|---|
| single-table | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| multi-table-related | 0.98 | 0.98 | 0.93 | 0.98 | 0.98 | 0.91 |
| multi-table-disparate | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.70 |
| trap | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.78 |

_`trap` questions bait distractor tables; low nDCG there means an approach ranked the wrong-but-similar table. See [`GROUND_TRUTH.md`](GROUND_TRUTH.md)._


## Cost & latency (isolated per-approach)

| Approach | Latency p50 (s) | Latency p95 (s) | Reranker tokens (median) | Reranker calls |
|---|---|---|---|---|
| 1: BQ Tools | 39.48 | 64.24 | 3470 | 1.0 |
| 2: KC Search | 8.57 | 11.74 | 8388 | 1.0 |
| 3: KC Context | 3.99 | 6.90 | 44020 | 1.0 |
| 4: Pre-Filter | 14.60 | 27.66 | 10749 | 1.0 |
| 5: Semantic | 6.06 | 9.84 | 14909 | 1.0 |
| 6: Search Direct | 2.09 | 2.40 | 0 | 0.0 |

_Latency is wall-clock for one approach run in isolation (no parallel contention). Reranker tokens are exact from `usage_metadata`; they are the dominant model cost since discovery is otherwise deterministic._


## Methodology & reproducibility

- **Design:** factorial — approach × tier × question × run. 3000 approach-runs scored.
- **Enrichment tiers:** identical 15-table corpus replicated ×4, differing only in catalog enrichment (3 distractor tables).
- **Replicates:** n=5 runs per cell; metrics reported as medians with IQR bands.
- **Models:** agent `gemini-3.6-flash`, reranker `gemini-3.5-flash-lite` at temperature 0.0, top_k=5.
- **Packages:** google-adk 1.36.2, google-genai 2.14.0, google-cloud-dataplex 2.20.0, google-cloud-bigquery 3.40.1.
- **Isolation:** each approach runs in its own `InMemoryRunner`, one at a time, so latency and token counts carry no parallel-contention artifact.
- **Scope-query probe (reproducible):** `examples/probe_scope_filter.py` replays the exact `search_entries` call the search approaches make (`semantic_search=True`, scoped by `parent:datasets/…`) and documents the correct query syntax. It shows: the `parent:` predicate **is honored** with a free-text question; an earlier low-recall result was a client-side query-construction bug (**wrapping the question in parentheses silently voided the predicate** — an isolation table pins this as the sole trigger, with `AND` connectors and parent-value parentheses both harmless); with the corrected bare query, 14 of 16 multi-table questions retrieve *all* their must-have tables before any rerank; the `scope=` request field is project/org-level only (a dataset-level ref → 400), so dataset scoping must go through `parent:`; and the returned count is governed by search's internal relevance cutoff, not `page_size` (raising it 20 → 100 adds nothing; no threshold parameter or relevance score is exposed). The harness also records per-run `search_stats` (`raw_search_count`, `out_of_scope_dropped`) for every search-based cell — now expected to show zero out-of-scope drops.
