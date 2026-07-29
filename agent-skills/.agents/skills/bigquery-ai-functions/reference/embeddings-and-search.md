# Embeddings & Semantic Search in BigQuery

Contents: [Options](#options) · [Choosing among them](#choosing-among-them) · [Gotchas verified in this repo](#gotchas-verified-in-this-repo) · [Canonical snippet](#canonical-snippet) · [Go deeper](#go-deeper)

## Options

| Function | What it does | Use this when | Key differentiator vs siblings |
|---|---|---|---|
| **AI.EMBED** | Scalar function; sends a single text/image/multimodal input to a Vertex AI embedding endpoint and returns `STRUCT(result ARRAY<FLOAT64>, status STRING)`. No model object needed. | You need embeddings row-by-row without pre-creating a model object, or you're prototyping/one-off scoring. | Only embedding function that needs no `CREATE MODEL` — endpoint specified inline. Scalar, so it runs per-row like any UDF. |
| **AI.GENERATE_EMBEDDING** | Table-valued function (TVF); generates embeddings in bulk over a table/query. Requires a pre-created remote model. This is Google's **recommended** TVF for new work. | You're embedding a whole table (or PCA/autoencoder/matrix-factorization output) and want the current, supported column-naming convention. | TVF (not scalar) and also supports non-generative model types (PCA, autoencoder, matrix factorization) that AI.EMBED cannot. |
| **ML.GENERATE_EMBEDDING** (legacy) | Predecessor TVF to AI.GENERATE_EMBEDDING. Identical capability, `ml_generate_embedding_*` prefixed output columns, plus a `flatten_json_output` option. | You have existing pipelines already built on it, or you need `flatten_json_output => FALSE` to get the raw JSON response. | Same engine as AI.GENERATE_EMBEDDING under different column names; **Google recommends migrating to AI.GENERATE_EMBEDDING** for new queries. |
| **AI.SIMILARITY** | Scalar function; embeds two inputs at runtime and returns their cosine similarity as FLOAT64. | You need to compare exactly two things (text-text, image-image, or cross-modal) and don't want to manage stored embeddings. | Only function that returns a similarity score directly — no manual dot-product/cosine math, no vectors returned. Generates 2 embeddings per call (costs 2x). |
| **VECTOR_SEARCH** | TVF; top-K nearest-neighbor search over a base table of pre-computed embeddings. Supports vector indexes for approximate nearest neighbor (ANN) search, batch or single-query search. | You have (or will materialize) a table of embeddings and need fast, scalable top-K retrieval — the core primitive for RAG/semantic search at scale. | Operates on **pre-computed** embeddings from any source; the only one of the group designed to use a vector index for ANN performance. |
| **AI.SEARCH** | TVF; simplified semantic search — embeds a query string at runtime and searches a table configured with **autonomous embedding generation**. | You want turnkey semantic search over a table without hand-rolling the embed-then-VECTOR_SEARCH pipeline, and you're fine enabling autonomous embedding generation on that table. | Requires autonomous embedding generation (VECTOR_SEARCH does not); simpler call surface (string in, ranked rows out) but text-only and single-query-literal only — no batch queries, no custom embedding source. |
| **HYBRID_SEARCH** *(docs pending — not yet built in this repo)* | Announced (Google Cloud Next 2026) TVF unifying semantic (vector) search with BigQuery's full-text SEARCH function into one ranked result set. | N/A yet — reference docs are not published. | Would combine VECTOR_SEARCH-style semantic matching with keyword/full-text search; **no reference docs, no repo folder, not verified or usable yet.** Flag as unavailable if a user asks for it. |

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
- HYBRID_SEARCH has no published reference docs, no repo folder, and no verified behavior as of this writing — treat it as unavailable rather than a real option until Google publishes docs.

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

`HYBRID_SEARCH` has no folder yet — docs pending, not built in this repo. The sibling `bigquery-ml` skill's `narrative/pca.md`/`narrative/autoencoder.md` show that PCA and AUTOENCODER models can also produce embeddings via `ML.GENERATE_EMBEDDING` — a non-generative-AI alternative worth knowing about for tabular/structured data rather than text/image content.

Full syntax/options tables: see RESOURCES.md in the source repo (`bq-ai-functions/RESOURCES.md`).
