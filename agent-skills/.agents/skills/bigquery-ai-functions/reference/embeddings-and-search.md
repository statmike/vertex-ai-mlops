# Embeddings & Semantic Search in BigQuery

Contents: [Options](#options) · [Choosing among them](#choosing-among-them) · [Gotchas verified in this repo](#gotchas-verified-in-this-repo) · [Hybrid search (semantic + lexical)](#hybrid-search-semantic--lexical) · [Canonical snippet](#canonical-snippet) · [Go deeper](#go-deeper)

## Options

| Function | What it does | Use this when | Key differentiator vs siblings |
|---|---|---|---|
| **AI.EMBED** | Scalar function; sends a single text/image/multimodal input to a Vertex AI embedding endpoint and returns `STRUCT(result ARRAY<FLOAT64>, status STRING)`. No model object needed. | You need embeddings row-by-row without pre-creating a model object, or you're prototyping/one-off scoring. | Only embedding function that needs no `CREATE MODEL` — endpoint specified inline. Scalar, so it runs per-row like any UDF. |
| **AI.GENERATE_EMBEDDING** | Table-valued function (TVF); generates embeddings in bulk over a table/query. Requires a pre-created remote model. This is Google's **recommended** TVF for new work. | You're embedding a whole table (or PCA/autoencoder/matrix-factorization output) and want the current, supported column-naming convention. | TVF (not scalar) and also supports non-generative model types (PCA, autoencoder, matrix factorization) that AI.EMBED cannot. |
| **ML.GENERATE_EMBEDDING** (legacy) | Predecessor TVF to AI.GENERATE_EMBEDDING. Identical capability, `ml_generate_embedding_*` prefixed output columns, plus a `flatten_json_output` option. | You have existing pipelines already built on it, or you need `flatten_json_output => FALSE` to get the raw JSON response. | Same engine as AI.GENERATE_EMBEDDING under different column names; **Google recommends migrating to AI.GENERATE_EMBEDDING** for new queries. |
| **AI.SIMILARITY** | Scalar function; embeds two inputs at runtime and returns their cosine similarity as FLOAT64. | You need to compare exactly two things (text-text, image-image, or cross-modal) and don't want to manage stored embeddings. | Only function that returns a similarity score directly — no manual dot-product/cosine math, no vectors returned. Generates 2 embeddings per call (costs 2x). |
| **VECTOR_SEARCH** | TVF; top-K nearest-neighbor search over a base table of pre-computed embeddings. Supports vector indexes for approximate nearest neighbor (ANN) search, batch or single-query search. | You have (or will materialize) a table of embeddings and need fast, scalable top-K retrieval — the core primitive for RAG/semantic search at scale. | Operates on **pre-computed** embeddings from any source; the only one of the group designed to use a vector index for ANN performance. |
| **AI.SEARCH** | TVF; simplified semantic search — embeds a query string at runtime and searches a table configured with **autonomous embedding generation**. | You want turnkey semantic search over a table without hand-rolling the embed-then-VECTOR_SEARCH pipeline, and you're fine enabling autonomous embedding generation on that table. | Requires autonomous embedding generation (VECTOR_SEARCH does not); simpler call surface (string in, ranked rows out) but text-only and single-query-literal only — no batch queries, no custom embedding source. |
| **Hybrid search** *(a capability, not a function)* | Re-ranks a candidate pool of `10 * top_k` rows by fusing the semantic and lexical *rankings* (reciprocal rank fusion). Shipped as parameters on the two search TVFs above — **there is no `HYBRID_SEARCH` function in the SQL surface.** | Exact tokens matter — SKUs, error codes, model numbers, proper nouns — and you have sized `top_k` for the reach you need. It promotes rows the semantic leg ranked within reach, and that reach is capped at `10 * top_k` rows however large the lexical signal. | Two routes: `VECTOR_SEARCH` with `lexical_search_columns` (+ optional `lexical_search_query_value`), or `AI.SEARCH` with `mode => 'HYBRID'`. Both are single-query only; neither supports batch. A lexical hit buys exactly `1/62` of score; below `top_k` = 51 that budget is what limits reach (10 rows deep at `top_k => 5`), and from 51 up the `10 * top_k` pool binds instead (640 rows at `top_k => 64`). See the hybrid section below. |

## Choosing among them

- **"I need to turn text/images into embedding vectors."**
  - One-off / row-by-row / prototyping → **AI.EMBED** (scalar, no model object, endpoint specified directly).
  - Bulk over a table, or you need PCA/autoencoder/matrix-factorization embeddings → **AI.GENERATE_EMBEDDING** (TVF, requires `CREATE MODEL` first). Prefer this over the legacy TVF for anything new.
  - Only reach for **ML.GENERATE_EMBEDDING** if you're maintaining an existing pipeline already built on it, or you specifically need `flatten_json_output => FALSE` to inspect the raw JSON response.

- **"I need to compare two things for similarity."**
  - Use **AI.SIMILARITY** rather than computing it yourself — it embeds both inputs at runtime and returns cosine similarity directly as FLOAT64. Good for prototyping and small comparisons; not meant for scale (2 embedding calls per invocation, no indexing). It also supports **cross-modal** comparison (text vs. image) with `multimodalembedding@001` or `gemini-embedding-2-preview`, since text and image embeddings share a vector space.
  - If you're comparing one item against many (not just two specific things), don't loop AI.SIMILARITY — that's a search problem; use VECTOR_SEARCH or AI.SEARCH instead.

- **"I need to search a large corpus of embeddings for nearest neighbors."**
  - Use **VECTOR_SEARCH**. Requires the embeddings to already be materialized as an `ARRAY<FLOAT64>` column (or a STRING column with autonomous embedding generation enabled) in a real table — logical views are not supported, and you shouldn't filter the embedding column in the base table query.
  - For performance on large base tables, create a **vector index** on the embedding column; BigQuery will use it automatically when present, or you can force exact results with `use_brute_force`. Use the single-search syntax (Preview) when you only have one query embedding — it's optimized for that case. Batch syntax handles multiple query rows at once via a `query_table`.
  - Default `distance_type` is `EUCLIDEAN`; `COSINE` and `DOT_PRODUCT` are also available and must be specified explicitly if you need them (e.g., to match AI.EMBED/AI.SIMILARITY's cosine-based comparisons).

- **"Pure semantic search is missing exact tokens"** (SKUs, error codes, part numbers, proper nouns).
  - Use **hybrid search**, with a caveat you should state up front. It is not a separate function — it's `lexical_search_columns` on **VECTOR_SEARCH** or `mode => 'HYBRID'` on **AI.SEARCH**. Reach for VECTOR_SEARCH's route when you need to name several lexical columns; reach for AI.SEARCH's when you already have autonomous embedding generation and want the one-parameter version.
  - **The caveat:** rank fusion promotes rows the semantic leg already ranked within reach, and `top_k` sets how deep that reach goes — twice over. BigQuery hands the lexical leg only the top `10 * top_k` rows by semantic rank, and inside that pool the fused score still has to beat the row holding the last slot. At `top_k` of 30 or less a lexical hit only lifts rows already near the top; at `top_k => 64` it reaches semantic rank 640 and no deeper. **To retrieve a row at semantic rank `R` by exact token, size `top_k` to at least `R/10` — that is a floor, not a recipe.** Below a few hundred ranks deep the score gate binds and asks for considerably more: a target at semantic rank 100 needs `top_k` near 29, not 10. Take the real number from the reach table below. If the token is the entire query and you want certainty, a `WHERE` predicate is still the correct answer. Read the dedicated section below — especially the reach table — before you recommend either route.

- **"I want a more turnkey search experience."**
  - Use **AI.SEARCH** instead of hand-building an embed-then-VECTOR_SEARCH pipeline — it embeds a plain string query at runtime and searches a table directly. The catch: the base table **must** have autonomous embedding generation enabled first, `column_to_search` refers to the source string column (not the embedding column), and it only accepts a single string literal per call — no batch queries, no custom/external embeddings. If you need batch search, non-text embeddings, or a table without autonomous embedding generation, drop down to VECTOR_SEARCH.

## Gotchas verified in this repo

- `multimodalembedding@001` accepts images only (JPEG, PNG, BMP, GIF) — **not PDFs**, in AI.EMBED, AI.GENERATE_EMBEDDING, and AI.SIMILARITY alike. Render PDFs to images (e.g. `pdftoppm`) first, or switch to `gemini-embedding-2-preview`, which does support PDFs (plus audio/video) but is US/us-central1 only.
- `multimodalembedding@001` does **not** return the `statistics` output column — queries that `SELECT statistics` against it will error. Only text embedding models and `gemini-embedding-2-preview` return `statistics` (token_count/truncated, or per-modality token counts for the latter).
- Output dimensionality is model-specific and must be respected: `text-embedding-005` and `text-multilingual-embedding-002` max out at 768; `gemini-embedding-001`/`gemini-embedding-2-preview` go up to 3072; `multimodalembedding@001` only accepts the discrete values 128, 256, 512, or 1408 (default 1408) via `output_dimensionality`/`dimension` — arbitrary values are not allowed for the multimodal model.
- The built-in `model => 'embeddinggemma-300m'` option (AI.EMBED and AI.SIMILARITY, Preview) runs entirely inside BigQuery using slots — no Vertex AI charges, no `connection_id`. It's fixed at 768 dimensions / 2048 tokens and is mutually exclusive with `endpoint`, `title`, `model_params`, and `connection_id`.
- VECTOR_SEARCH requires embeddings to be **materialized in a real table** first (an `ARRAY<FLOAT64>` column, or STRING with autonomous embedding generation) — you cannot point it at a view, and you should not filter the embedding column itself in the base table query, since that can defeat index usage.
- Object tables used with remote models for multimodal embedding generation require a **BigQuery reservation**; the inline `OBJ.MAKE_REF` → `OBJ.FETCH_METADATA` → `OBJ.GET_ACCESS_URL` pattern avoids that requirement entirely and is the preferred approach for one-off multimodal calls.
- Distance metric default differs by function family: VECTOR_SEARCH and AI.SEARCH both default to `EUCLIDEAN`, not `COSINE` — if you're benchmarking against AI.SIMILARITY's cosine output, you must explicitly pass `distance_type => 'COSINE'`.
- AI.SIMILARITY generates **two** embeddings per invocation (one per input) — factor that into cost/quota estimates versus a single AI.EMBED call.
- Multimodal calls (AI.EMBED, AI.GENERATE_EMBEDDING, AI.SIMILARITY) require `connection_id` and a connection service account with `roles/aiplatform.user` and `roles/storage.objectViewer`; text-only calls can skip `connection_id` for calls under 48 hours.
- Video embeddings via AI.GENERATE_EMBEDDING only process the **first 2 minutes** (`end_second` max/default 120), and `output_dimensionality` cannot be combined with video embeddings.
- AI.SEARCH fails the entire query if embedding generation for the single `query_value` fails; rows in the base table missing embeddings are silently skipped rather than erroring.
- Google explicitly recommends **AI.GENERATE_EMBEDDING over ML.GENERATE_EMBEDDING** for new work — the legacy function is kept for compatibility and its `ml_generate_embedding_*` naming, not for new development.
- **There is no `HYBRID_SEARCH` function.** It was widely expected as a standalone TVF and never shipped as one; Google delivered hybrid retrieval as parameters on `VECTOR_SEARCH` and `AI.SEARCH` instead. If a user asks for `HYBRID_SEARCH`, redirect them to those parameters rather than reporting the feature as unavailable.

## Hybrid search (semantic + lexical)

Two routes, both **single-query only** — hybrid and batch search are mutually exclusive:

| Route | How to invoke | Lexical columns |
|---|---|---|
| `VECTOR_SEARCH` | Single-search syntax + `lexical_search_columns` (+ optional `lexical_search_query_value`) | Any set of base table columns you name |
| `AI.SEARCH` | `mode => 'HYBRID'` (also `'VECTOR'`, `'AUTO'`) | Only `column_to_search` |

Verified gotchas:

- **Neither route requires a vector index.** Both work against an unindexed base table; the index only accelerates the lexical leg.
- Passing `lexical_search_columns` with the batch (`query_table`) syntax fails with `lexical_search_columns is not supported when query_value is not specified.`
- **Hybrid re-ranks *and* widens, and `top_k` decides how much — twice over.** It fuses two *rankings* rather than unioning two result sets, so the gain is bounded by arithmetic, not by whether the token matched. Two gates apply: the lexical leg only ever sees the top `10 * top_k` rows by semantic rank, and within that pool the fused score must still beat the last slot on the page. At small `top_k` a lexical hit only nudges rows already near the top; at `top_k => 64` it surfaces a matching row from semantic rank 640 at the very deepest. Size `top_k` deliberately before you promise a user that hybrid "recovers the exact tokens semantic search misses."
- **The returned `distance` is not a distance.** In hybrid mode it is a reciprocal-rank-fusion score reproduced by the following, with ranks 1-based:

  ```
  distance = 1 - ( 1/(60 + rank_vector) + 1/(61 + rank_lexical) )
  ```

  Only `rank_vector` is ever read directly — `VECTOR_SEARCH` returns no rank column, so it comes from a separate semantic-only run and the lexical term is the remainder. That pins denominators, not constants: the semantic leg's top row contributes `1/61`, the lexical leg's top row `1/62`. Two readings fit identically, since `1/(61 + r)` = `1/(60 + (r + 1))` — (A) two constants, k = 60 semantic and k = 61 lexical, both ranks `1..n`; or (B) k = 60 on both with lexical ranks `2..n+1`. **B is the likelier**: k = 60 over 1-based ranks is canonical RRF (Cormack et al. 2009) and the default wherever exposed — Elasticsearch and OpenSearch call it `rank_constant` and default it to 60, Spanner and AlloyDB write 60 into their documented SQL — while no published implementation uses 61 as the constant. Do not repeat the argument that "decoding with 60 on both legs implies lexical ranks `2..n+1`, which no n-row list hands out" as proof of two constants; that is exactly what B predicts. The 60/61 form is shorthand for arithmetic that holds, not two design decisions. *Why* the lexical leg would start at 2 is a separate, open question — a deliberate tie-break (at equal ranks `1/(60 + r)` beats `1/(61 + r)`, so the semantic leg wins every tie by a hair), a reserved slot at lexical position 1, and a plain off-by-one all fit equally well. Only the last is a defect, and nothing observable distinguishes them: never tell a user this is a BigQuery bug. The best attainable score is `1 - (1/61 + 1/62)` = `0.9674775251189847`, at rank 1 in *both* legs — not 0 — and the frequently quoted `1 - 2/61` = `0.96721` is unattainable. Values cluster in a narrow band just under 1 and are **not comparable** to `VECTOR`-mode distances — never reuse a cosine-tuned threshold. Because the score depends only on ranks, `distance_type` has no effect in hybrid mode. *(Measured against BigQuery, not documented by Google — it explains the ordering you see; it is not a contract.)*
- **The lexical leg ranks the entire candidate pool, so no pooled row forfeits a term.** BM25 matches take lexical ranks `1..m`; **every remaining pooled row falls back to its semantic order behind them**. Verified two ways: with a `lexical_search_query_value` matching zero rows, every returned row still received a lexical term with `rank_lexical = rank_vector`; and promoting one row to lexical rank 1 moved the former rank-1 row to rank 2 and left every row below the promoted row byte-identical. There is no single-list state and no `1 - 1/61` ceiling — a pooled row with no lexical match still carries a lexical rank — its semantic rank, pushed down one place for each match below it — and where nothing matched at all that is exactly `1 - ( 1/(60 + r) + 1/(61 + r) )` for semantic rank `r`. What a lexical match buys is promotion to lexical rank 1, worth `1/62` ≈ `0.0161`.
- **Gate 1 — the lexical candidate pool is `10 * top_k` rows.** BigQuery hands the BM25 leg only the top `10 * top_k` rows by semantic rank. A row deeper than that receives **no lexical rank at all**, however perfectly the token matches — it is never a candidate, so no score can rescue it. The diagnostic signature of a target outside the pool is a result set carrying `rank_lexical = rank_vector` throughout: every distance equals `1 - ( 1/(60 + r) + 1/(61 + r) )`, so the best row comes back `0.967478` (nothing matched) instead of `0.967734` (a match fired).
- **Gate 2 — the fused score has to beat the last slot.** A matched row at semantic rank `R` scores `1/(60 + R) + 1/62`; it displaces the row holding the last slot, which sits at semantic rank `top_k` and — pushed down one by the match — lexical rank `top_k + 1`, scoring `1/(60 + top_k) + 1/(61 + top_k + 1)`. Solving that gives the deepest semantic rank the score gate alone admits.
- **Effective reach is the `min` of both gates: `min( score gate, 10 * top_k )`.** Gate 2 binds below `top_k = 51`; Gate 1 binds from 51 up, where reach simply grows linearly at ten rows per unit of `top_k`:

  | `top_k` | 2 | 3 | 5 | 10 | 20 | 30 | 40 | 50 | 51 | 64 | 100 | 208 | 300 |
  |---|---|---|---|---|---|---|---|---|---|---|---|---|---|
  | deepest semantic rank retrievable | 3 | 6 | 10 | 23 | 56 | 110 | 212 | 468 | 510 | 640 | 1,000 | 2,080 | 3,000 |

  Below 51 the curve is steep and unintuitive — `top_k => 5` reaches 10 rows deep, `top_k => 50` reaches 468. Above it the rule is simply `10 * top_k`, so **retrieving a row at semantic rank `R` by exact token needs `top_k >= R/10` — a minimum, not a recipe.** Below `R` of about 500 the score gate is the binding one and asks for more than `R/10` (rank 100 needs `top_k` 29; rank 200 needs 40), so read the requirement off the table rather than the ratio. Hybrid does widen recall, but proportionally to `top_k` — never further. If a user reports "hybrid changed nothing," check their `top_k` first.
- **The evidence for the reach table.** Measured across four corpora, including three sharp out-of-sample predictions. A 500-row corpus pins the score gate: 499 rows about office/desk items, semantically close to the query "desk accessories for a computer setup", plus one target row `ZQX-9999` described as "bulk compost bin for garden waste and autumn leaf mulching" — semantic rank **500 of 500**. Searching with `lexical_search_query_value => 'ZQX-9999'`:

  | `top_k` | 10 | 49 | 50 | 51 | 63 | 64 |
  |---|---|---|---|---|---|---|
  | target returned | no | no | no | **yes** | yes | yes |

  The arithmetic predicts the flip between 50 and 51 to the exact position (the pool was not binding here — 500 rows sit inside `10 * 51`). The target's returned distance, `0.9820852534562212`, is exactly `1 - (1/560 + 1/62)` — semantic rank 500, lexical rank 1. The pool gate shows up on deeper corpora, where it is predicted before it is observed: a 1,500-row table with the target at rank 1,500 flips at `top_k = 150` (149 no match, 150 match), and a 3,000-row table with the target at rank 3,000 flips at `top_k = 300` (299 no match, 300 match). All three synthetic probe tables — 3,000, 1,500 and 500 rows — are **unindexed**, each sitting below BigQuery's 5,000-row `CREATE VECTOR INDEX` minimum and therefore brute-force scanned, so no index exists to restrict anything. The fourth corpus, the real 7,275-row product catalog, **was indexed**: it carried a `TREE_AH` hybrid vector index with `lexical_search_columns`, `ACTIVE` at 100% coverage, when its target at semantic rank 2,072 came back absent at `top_k => 64` — the pool is only 640 rows deep there, and the row needs `top_k >= 208`. The gate behaves identically with and without an index, which makes it the stronger result: the pool is neither an index artifact nor something an index can avoid. Every hybrid demo in this sub-project used `top_k` between 2 and 64, i.e. reach between 3 and 640, which is why none of them showed a recall gain.
- **Promotion is a swap.** The page is fixed-length, so a row hybrid adds displaces one semantic-only would have returned. When comparing, compute both the added and the dropped set.
- **If an opaque identifier is the entire query and you want certainty, use `WHERE sku = @sku`** — a predicate cannot be outranked by a fusion score, and it has no candidate pool, so it is not sensitive to `top_k` at all. Hybrid can find the row too, but only at a `top_k` of at least a tenth of its semantic rank and often well above that floor — check the reach table for the rank you care about — and it spends a full search to do what a filter does exactly. Hybrid earns its keep on queries carrying descriptive words *and* an identifier.
- To build a vector index that accelerates the lexical leg, every column in `lexical_search_columns` **must also appear in `STORING(...)`** (else `Lexical search column x must be in the list of stored columns`), and a lexical column **may not also be the index key** (else `Column x found multiple times`).
- **An AI.SEARCH base table can never have a hybrid vector index.** Autonomous embedding generation produces a `STRUCT<result, status>` column, and a vector index key must be `ARRAY<FLOAT64>`. Consequence: `mode => 'AUTO'` silently resolves to semantic-only on such a table, so name `'HYBRID'` explicitly. Demonstrating both autonomous embeddings and a vector index requires two tables.
- **Two separate vector-index size gates.** `CREATE VECTOR INDEX` is rejected outright below **5,000 rows** (`Total rows 30 is smaller than min allowed 5000 for CREATE VECTOR INDEX query with the IVF index type` — verified for both `IVF` and `TREE_AH`, and *not* stated in Google's vector-index docs). Separately, **population** is asynchronous and does not start until the base table exceeds roughly **10 MB**; below that the index reports `coverage_percentage` 0 / `BASE_TABLE_TOO_SMALL` and queries silently fall back to brute force. A demo table must clear both bars.

## Canonical snippet

```sql
-- 1. Generate and materialize embeddings for a corpus of text
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.doc_embeddings` AS
SELECT
  doc_id,
  content,
  AI.EMBED(
    content => content,
    endpoint => 'text-embedding-005',
    task_type => 'RETRIEVAL_DOCUMENT'
  ).result AS embedding
FROM `PROJECT_ID.DATASET.documents`;

-- 2. Search the materialized embeddings for nearest neighbors to a query
SELECT
  query.query_text,
  base.doc_id,
  base.content,
  distance
FROM VECTOR_SEARCH(
  TABLE `PROJECT_ID.DATASET.doc_embeddings`,
  'embedding',
  (
    SELECT
      'find pricing details' AS query_text,
      AI.EMBED(
        content => 'find pricing details',
        endpoint => 'text-embedding-005',
        task_type => 'RETRIEVAL_QUERY'
      ).result AS embedding
  ),
  query_column_to_search => 'embedding',
  top_k => 5,
  distance_type => 'COSINE'
) AS query, base;
```

## Go deeper

Full extracted notebook walkthroughs live in this skill's `narrative/` folder:

- [`narrative/ai_embed.md`](../narrative/ai_embed.md) (source: `functions/ai_embed/`)
- [`narrative/ai_generate_embedding.md`](../narrative/ai_generate_embedding.md) (source: `functions/ai_generate_embedding/`)
- [`narrative/ml_generate_embedding.md`](../narrative/ml_generate_embedding.md) (source: `functions/ml_generate_embedding/`) — legacy
- [`narrative/ai_similarity.md`](../narrative/ai_similarity.md) (source: `functions/ai_similarity/`)
- [`narrative/vector_search.md`](../narrative/vector_search.md) (source: `functions/vector_search/`)
- [`narrative/ai_search.md`](../narrative/ai_search.md) (source: `functions/ai_search/`)

Hybrid search has no folder of its own because it is not a function — it is covered inside `narrative/vector_search.md` and `narrative/ai_search.md`, and worked end-to-end in `narrative/catalog_search.md` (source: `workflows/catalog_search/`). The sibling `bigquery-ml` skill's `narrative/pca.md`/`narrative/autoencoder.md` show that PCA and AUTOENCODER models can also produce embeddings via `ML.GENERATE_EMBEDDING` — a non-generative-AI alternative worth knowing about for tabular/structured data rather than text/image content.

Full syntax/options tables: see RESOURCES.md in the source repo (`bq-ai-functions/RESOURCES.md`).
