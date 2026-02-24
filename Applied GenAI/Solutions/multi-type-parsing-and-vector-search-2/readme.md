![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FApplied+GenAI%2FSolutions%2Fmulti-type-parsing-and-vector-search-2&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20GenAI/Solutions/multi-type-parsing-and-vector-search-2/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520GenAI/Solutions/multi-type-parsing-and-vector-search-2/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520GenAI/Solutions/multi-type-parsing-and-vector-search-2/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520GenAI/Solutions/multi-type-parsing-and-vector-search-2/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520GenAI/Solutions/multi-type-parsing-and-vector-search-2/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
# Multi-Type File Parsing And Vertex Vector Search 2
> You are here: `vertex-ai-mlops/Applied GenAI/Solutions/multi-type-parsing-and-vector-search-2/readme.md`

Google Cloud offers fit-for-purpose managed services that automate much of the RAG pipeline — [connectors in Gemini Enterprise](https://cloud.google.com/gemini/docs/overview), [Vertex AI Search](https://cloud.google.com/enterprise-search), and [Vertex AI RAG Engine](https://cloud.google.com/vertex-ai/generative-ai/docs/rag-overview) all handle parsing, chunking, and retrieval out of the box. This project takes a more direct approach: full control over source file parsing, chunking strategy, and metadata tagging to build a fully tunable RAG system, while leveraging the automations provided by [Vector Search 2.0](https://cloud.google.com/vertex-ai/docs/vector-search-2/overview) — auto-embeddings, schema-enforced collections, and built-in hybrid search with RRF.

## Setup

This project requires the packages listed in [pyproject.toml](pyproject.toml) and prefers the Python version specified there.

**Google Cloud APIs:**

Enable the required APIs:
```bash
gcloud services enable \
  aiplatform.googleapis.com \
  vectorsearch.googleapis.com \
  documentai.googleapis.com \
  storage.googleapis.com \
  bigquery.googleapis.com
```

**Google Cloud ADC:**

This project uses [Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials) for Google Cloud APIs. Set up and verify with:
```bash
gcloud auth application-default login
```
Verify ADC is active and check which identity it's using:
```bash
curl -s -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  https://www.googleapis.com/oauth2/v3/userinfo
```

**Project Configuration:**

All shared parameters (project ID, BigQuery dataset/tables, GCS bucket/paths, processor IDs, etc.) are centralized in [config.py](config.py). Update the values there for your environment — all scripts import from it.

**UV (recommended):**

Run the included [uv_setup.sh](uv_setup.sh) for a one-step setup (environment, packages, Jupyter kernel, and requirements.txt):
```bash
bash uv_setup.sh
```

Or manually:
```bash
uv sync
uv run python -m ipykernel install --user --name=$(basename "$PWD")
```

**Poetry:**
```bash
poetry install
poetry run python -m ipykernel install --user --name=$(basename "$PWD")
```

**pip:**
```bash
pip install -r requirements.txt
python -m ipykernel install --user --name=$(basename "$PWD")
```

### Running Scripts

**UV:** `uv run python <script.py>`

**Poetry:** `poetry run python <script.py>`

**pip:** `python <script.py>` (with your virtual environment activated)

## Generate Data

Three scripts generate synthetic forecasting-themed data in different formats. Each uses Gemini (`gemini-2.5-pro`) via Vertex AI with structured output (Pydantic schemas).

| Script | Output Folder | Format | Description |
|--------|--------------|--------|-------------|
| [generate_reddit.py](generate_reddit.py) | [generated_reddit/](generated_reddit/) | JSON | Synthetic Reddit threads with nested comments (via `comment_id`/`parent_id`). Varying depth and branching levels. |
| [generate_zoom.py](generate_zoom.py) | [generated_zoom/](generated_zoom/) | WebVTT | Synthetic Zoom meeting transcripts with multiple speakers. Varying duration and complexity. |
| [generate_pdf.py](generate_pdf.py) | [generated_pdf/](generated_pdf/) | PDF | Web pages converted to PDF using WeasyPrint. |

**Customization tips:**
- **Reddit/Zoom**: Edit the prompt in the `contents` string to change the topic, tone, or participant mix. Adjust the `configs` list to control the number/complexity of generated files.
- **PDF**: Replace the `urls` list at the top of the script with your own URLs.

## Solution Workflow

```
Generate ─► Upload ─► Object Table ─► Parse ─► Enrich ─► Collections ─► Import ─► BM25 ──► Search ─► Refresh ─► ANN Index
 (0)         (1)         (2)         (3a-3c)   (4a-4c)    (5a-5d)      (6a-6d)   (7a/7b)    (8)       (9)        (10)
```

| Step | Input | Output | What Happens |
|------|-------|--------|--------------|
| **1. Files in GCS** | Generated JSON, VTT, PDF files | GCS objects with custom metadata | Upload files + set `source-type`, `subreddit`, `cue-count`, etc. |
| **2. Object Table** | GCS bucket path | `{prefix}_source` BQ table | Live queryable view over GCS — URIs, metadata, sizes |
| **3a. Parse Reddit** | JSON files via GCS | `{prefix}_reddit_chunks` (34 rows) | Flatten comment trees → `THREAD: … \| COMMENT: …` chunks, VLM image descriptions, SNR filtering |
| **3b. Parse Zoom** | VTT files via GCS | `{prefix}_zoom_chunks` (12 rows) | Sliding window over cues, rolling Gemini summary prefix per window |
| **3c. Parse PDF** | PDF files via Document AI | `{prefix}_pdf_chunks` (71 rows) | Layout Parser v1.5 → structure-aware chunks with ancestor headings |
| **4a. Enrich Reddit** | `reddit_chunks.text_content` | + `topics`, `methods_mentioned` columns | LangExtract extracts forecasting methods + data science topics per chunk |
| **4b. Enrich Zoom** | `zoom_chunks.text_content` | + `topics`, `action_items` columns | LangExtract extracts discussion topics + action items per chunk |
| **4c. Enrich PDF** | `pdf_chunks.text_content` | + `topics`, `functions_referenced` columns | LangExtract extracts BQML functions + technical concepts per chunk |
| **5a-5d. Collections** | Schema definitions | 4 Vector Search 2.0 collections | Define data + vector schemas with auto-embeddings + sparse vector field |
| **6a-6d. Import** | BQ chunk tables | DataObjects in collections | Create DataObjects; embeddings auto-generated from `text_content` |
| **7a. Build BM25** | All chunks from BQ | Model + vocabulary in BQ | Train BM25 model, save vocabulary and metadata (version history preserved) |
| **7b. Apply BM25** | BM25 model from BQ | Sparse embeddings in BQ + VS2 | Compute sparse embeddings, update chunk tables and DataObjects |
| **8. Search** | Natural language queries | Ranked results with metadata | Query, semantic, text, sparse, hybrid/RRF, crowding (VertexRanker defined but not yet supported) |
| **9. Refresh** | Current corpus vs stored vocabulary | Conditional retrain | Drift detection → retrain if needed; run apply_bm25.py after |
| **10. ANN Index** | DataObject count in collection | ANN index on combined collection | Check size, create index if ≥ threshold; queries auto-use ANN |

<details>
<summary><b>Example data at each transformation stage</b> (click to expand)</summary>

**Step 3a — Reddit parsing** flattens nested comment trees into self-contained chunks:

```
Input (JSON):
  { "comment_id": "c3", "parent_id": "c1", "body": "Prophet handles holidays automatically.",
    "author": "forecaster99", "karma": 52 }

Output (BQ row → text_content):
  "THREAD: ARIMA vs. Prophet | PARENT: I've been comparing models for retail... | COMMENT: Prophet handles holidays automatically."
```

**Step 3b — Zoom parsing** creates overlapping windows with rolling summaries:

```
Input (VTT cues):
  00:01:05.000 --> 00:01:12.000     Sarah (Lead): Let's benchmark ARIMA against Prophet.
  00:01:12.500 --> 00:01:18.000     David (Statistician): I can set that up by Friday.
  ...15 cues per window, 5-cue overlap...

Output (BQ row → text_content):
  "[Summary: The team debates Prophet versus a gradient-boosted approach...] Sarah (Lead): Let's benchmark ARIMA against Prophet.
   David (Statistician): I can set that up by Friday. ..."
```

**Step 3c — PDF parsing** produces structure-aware chunks with heading context:

```
Input (PDF page):
  Page 4: "The CREATE MODEL statement for ARIMA PLUS models" > "model_name" section

Output (BQ row → text_content):
  "# The CREATE MODEL statement for ARIMA PLUS models\n\n## model_name\n\nThe name of the model you're creating..."
```

**Step 4 — Enrichment** tags each chunk with semantic metadata:

```
Input (text_content):
  "THREAD: ARIMA vs. Prophet | COMMENT: Prophet handles holidays automatically. I've had great results
   with it for seasonal retail demand."

Output (new BQ columns):
  topics:            ["demand forecasting", "holiday effects"]
  methods_mentioned: ["Prophet"]
```

**Step 7 — BM25 sparse embeddings** produce sparse vectors from text + enrichment tags:

```
Input (text_content + enrichment tags):
  "THREAD: ARIMA vs. Prophet | COMMENT: Prophet handles holidays automatically..."
  + topics: ["demand forecasting", "holiday effects"]
  + methods_mentioned: ["Prophet"]
  → BM25 text: "THREAD: ARIMA vs. Prophet | COMMENT: Prophet handles holidays automatically... demand forecasting holiday effects Prophet"

Preprocessing (chunk_prep):
  → lowercase, remove punctuation, lemmatize, remove stopwords, generate bigrams
  → ["thread", "arima", "prophet", "comment", "prophet", "handle", "holiday", "automatically",
     "demand", "forecasting", "thread arima", "arima prophet", "prophet comment", ...]

Output (BQ columns + VS2 DataObject):
  bm25_indices: [42, 187, 2041, 5893, ...]     # vocabulary term positions
  bm25_values:  [1.82, 0.95, 2.14, 1.33, ...]  # BM25 scores (IDF × term frequency saturation)
  bm25_model_version: 1
```

</details>

---

### 1. Files in GCS

The workflow starts with documents in Google Cloud Storage. [upload_to_gcs.py](upload_to_gcs.py) uploads all generated files to the GCS bucket/path defined in [config.py](config.py) and sets custom metadata on each object:

| Source Type | Metadata Keys |
|-------------|--------------|
| Reddit (JSON) | `source-type`, `file-format`, `content-domain`, `subreddit`, `thread-title`, `comment-count` |
| Zoom (VTT) | `source-type`, `file-format`, `content-domain`, `cue-count` |
| PDF | `source-type`, `file-format`, `content-domain` |

Metadata is set during upload (single operation per file). The `source-type` metadata is used downstream to route files to the correct parser.

---

### 2. BigQuery Object Table

The pipeline involves multiple stages — parsing, chunking, augmenting metadata, and preparing Vector Search input — each adding data that relates back to source files. Rather than managing this across loose files, we use BigQuery as the central data layer:

- **Object tables** give a queryable base over GCS files with their URIs, metadata, sizes — no ETL needed
- **Relational joins** let each downstream table (chunks, embeddings, augmented metadata) key back to source files
- **Inspectability** at every stage via SQL (e.g. "which files haven't been parsed?")
- **Export** to JSONL for Vector Search input is a single `EXPORT DATA` statement

[create_object_table.py](create_object_table.py) creates the BigQuery dataset and object table over the GCS path. The table name follows the convention `{BQ_TABLE_PREFIX}_source` from [config.py](config.py).

**BigQuery Connection:** Object tables need a [Cloud Resource connection](https://cloud.google.com/bigquery/docs/create-cloud-resource-connection) — this is just a one-time setup for the project. The connection provides a service account that BigQuery uses to read from GCS on your behalf. The script handles this automatically: it checks for an existing connection (named per `BQ_CONNECTION` in [config.py](config.py)), creates one if needed, and grants its service account `objectViewer` on your GCS bucket. Nothing to configure manually.

> **Note:** The object table is a live, auto-refreshing view over GCS with [configurable staleness](https://docs.cloud.google.com/bigquery/docs/object-table-introduction#metadata_caching_for_performance).

---

### 3a. Parse Reddit Threads

[parse_reddit.py](parse_reddit.py) reads Reddit JSON files from GCS (discovered via the object table) and produces chunked rows in BigQuery (`{BQ_TABLE_PREFIX}_reddit_chunks`).

**Tree flattening:** Reddit comments are stored flat with `comment_id`/`parent_id` references rather than nested objects. The parser reconstructs the conversational lineage for each comment by walking up the parent chain (bounded by `MAX_DEPTH`, default: 100) to build a path-based text representation:
```
THREAD: Post Title | PARENT: Parent comment (truncated to 200 chars) | COMMENT: Full comment body
```
This means each chunk is self-contained — it carries the thread title, the immediate parent's context, and the comment itself. A top-level comment (no parent) produces `THREAD: ... | COMMENT: ...` without the `PARENT` segment.

**SNR filtering:** Non-top-level comments shorter than `SHORT_RESPONSE_THRESHOLD` (default: 15 tokens) are filtered. Top-level comments are always kept regardless of length. The `SHORT_RESPONSE_MODE` parameter controls how short replies are handled:
- `"drop"` — discard them entirely (removes noise like "this" or "+1")
- `"rollup"` (default) — append their text to the nearest ancestor's chunk as `| REPLY: ...`, preserving the signal without creating low-value standalone chunks

**VLM image enrichment:** When a comment has an `image_url`, Gemini generates a dense 2-3 sentence description anchored to the comment's text context. The description is appended as `| IMAGE: ...`. If the VLM call fails, the chunk is kept without an image description and `is_image_description` remains `true`.

**Output schema:** `chunk_id`, `source_uri`, `text_content`, `subreddit`, `timestamp_unix`, `karma`, `is_image_description`, `processed_at`

**Incremental:** Tracks staleness by comparing each chunk's `processed_at` timestamp against the GCS object's `updated` timestamp. On re-run, new Reddit files are parsed and appended, updated files have their old chunks replaced, and unchanged files are skipped.

### 3b. Parse Zoom Transcripts

[parse_zoom.py](parse_zoom.py) reads WebVTT files from GCS and produces chunked rows in BigQuery (`{BQ_TABLE_PREFIX}_zoom_chunks`).

**VTT parsing:** A "cue" is the basic unit of a WebVTT transcript — a timestamp range paired with a speaker label and their spoken text. Each cue represents one uninterrupted segment of dialogue (e.g., `00:01:05.000 --> 00:01:12.000` followed by `Sarah: Let's review the data.`). The parser extracts each cue's timestamp range, speaker name, and spoken text. Speaker names are split from the text content (format: `Speaker Name: dialogue text`).

**Sliding window:** Cues are grouped into overlapping windows of `WINDOW_SIZE` (default: 15) cues with `OVERLAP` (default: 5) cues shared between consecutive windows. This ensures no context is lost at chunk boundaries — each chunk overlaps with its neighbors.

**Rolling summary:** For every window after the first, Gemini generates a 15-word summary of the previous window's content. This summary is prepended as `[Summary: ...] ` to provide continuity context for downstream retrieval. The first window has no summary prefix.

**Output schema:** `chunk_id`, `source_uri`, `text_content`, `speaker_list` (repeated), `timestamp_start`, `timestamp_end`, `processed_at`

**Incremental:** Tracks staleness by comparing each chunk's `processed_at` timestamp against the GCS object's `updated` timestamp. On re-run, new VTT files are parsed and appended, updated files have their old chunks replaced, and unchanged files are skipped.

### 3c. Parse PDFs

PDF parsing uses the [Document AI Layout Parser](https://cloud.google.com/document-ai/docs/layout-parse-chunk) (`pretrained-layout-parser-v1.5-pro-2025-08-25`) to extract structured chunks from PDF files. This is split into two parts: an inspection notebook for understanding the response structure, and a batch processing script for the full pipeline.

**Processor setup:** Both the notebook and script create a Layout Parser processor if one doesn't already exist in your project. The processor version and display name are configured in [config.py](config.py).

#### Inspect Response — [inspect_docai_response.ipynb](inspect_docai_response.ipynb)

Before building the batch pipeline, this notebook processes a single PDF (online mode) and inspects the full response structure. The source PDF is [bigquery_docs_reference_standard_sql_bigqueryml_syntax_create_time_series.pdf](generated_pdf/bigquery_docs_reference_standard_sql_bigqueryml_syntax_create_time_series.pdf) (826KB, 37 pages, contains diagrams and tables). The notebook writes the complete parsed response to [docai_response_sample.json](docai_response_sample.json) so you can compare the source PDF against the full JSON output. Key findings:

- **`chunked_document`**: Chunks have 6 fields — `chunk_id`, `content`, `page_span`, `page_headers`, `page_footers`, `source_block_ids`. No new fields in v1.5 beyond these.
- **`document_layout`**: Hierarchical blocks with `text_block` (subtypes: `heading-1`, `heading-2`, `heading-3`, `paragraph`, `footer`), `table_block` (with `header_rows`, `body_rows`, `caption`), and `list_block`.
- **Tables** are rendered as markdown in the chunk `content` (e.g., `|-|-|\n| col1 | col2 |`).
- **Images/diagrams** are OCR'd and extracted as inline text within chunks — the parser does not produce a separate image block type or flag image-derived content. Diagram labels and flowchart text appear as regular paragraphs.
- **`include_ancestor_headings`** prepends the heading hierarchy to each chunk (e.g., `# Title\n\n## Section\n\nchunk text`), making chunks self-contained.
- **Online processing limit** for v1.5 is 30 pages (up from 15 in v1.0). Use `from_start` to stay within the limit.

#### Batch Processing — [parse_pdf.py](parse_pdf.py)

Processes all PDFs in the GCS folder and produces chunked rows in BigQuery (`{BQ_TABLE_PREFIX}_pdf_chunks`).

**Batch processing:** Uses Document AI's [batch processing](https://cloud.google.com/document-ai/docs/send-request) mode with `gcs_prefix` to process all PDFs in a single job. Batch mode supports files up to 40MB and 500 pages and processes multiple files concurrently. Results are written to a GCS output path and then read back to extract chunks.

**Layout-aware chunking:** The Layout Parser detects document structure — headings, paragraphs, tables, lists, headers, footers — and produces chunks that respect these boundaries rather than splitting mid-sentence or mid-section. Configuration:
- `CHUNK_SIZE` (default: 500) — target tokens per chunk
- `INCLUDE_ANCESTOR_HEADINGS` (default: `True`) — prepend the heading hierarchy to each chunk, making chunks self-contained

**Output schema:** `chunk_id`, `source_uri`, `text_content`, `page_start`, `page_end`, `processed_at`

---

### 4. Semantic Enrichment with LangExtract

Chunks from step 3 have structural metadata (page ranges, karma, timestamps) but no semantic metadata describing *what the content is about*. [LangExtract](https://github.com/google/langextract) uses LLMs to extract structured entities from text with source grounding — each extraction points back to the exact text span it was derived from.

This step uses `gemini-2.5-flash` (`FAST_GEMINI_MODEL` in [config.py](config.py)) for cost-efficient per-chunk extraction, while the more capable `gemini-2.5-pro` is reserved for the complex tasks in step 3 (VLM image description, rolling summary).

**Inspection notebook:** [inspect_langextract.ipynb](inspect_langextract.ipynb) demonstrates LangExtract on one chunk from each type — shows extraction schema design with few-shot examples, source-grounded results, and the aggregation logic that collapses extractions into flat tag lists for BigQuery storage.

#### 4a. Enrich Reddit Chunks

[enrich_reddit.py](enrich_reddit.py) adds `topics` and `methods_mentioned` columns to the Reddit chunks table, then runs LangExtract on each chunk to extract forecasting methods and data science topics. Extractions are aggregated into deduplicated tag lists and written back to BigQuery via parameterized UPDATE queries.

#### 4b. Enrich Zoom Chunks

[enrich_zoom.py](enrich_zoom.py) adds `topics` and `action_items` columns to the Zoom chunks table, then extracts discussion topics and action items (with owners) from each transcript chunk.

#### 4c. Enrich PDF Chunks

[enrich_pdf.py](enrich_pdf.py) adds `topics` and `functions_referenced` columns to the PDF chunks table, then extracts BigQuery ML functions and technical concepts from each documentation chunk.

---

### 5. Create Collections

Each collection in [Vector Search 2.0](https://cloud.google.com/vertex-ai/docs/vector-search-2/overview) defines a `data_schema` (the fields stored with each data object) and a `vector_schema` (the embedding fields). With [auto-embeddings](https://cloud.google.com/vertex-ai/docs/vector-search-2/data-objects/data-objects#auto-populate-embeddings), the vector schema specifies which embedding model to use and how to generate embeddings from data fields — no manual embedding calls needed.

The vector schema includes two fields:
- **`text_content_embedding`** (dense) — Auto-populated using `gemini-embedding-001` at `EMBEDDING_DIMENSIONS` (768) with `RETRIEVAL_DOCUMENT` task type. Note: `gemini-embedding-001` natively produces 3072-dim vectors; the `dimensions` field in the vector schema controls truncation for auto-embedding.
- **`bm25_embedding`** (sparse) — Not auto-populated. Computed by `apply_bm25.py` (step 7b) and written via `batch_update_data_objects`.

**Embedding task types:** A critical configuration choice in the vector schema is the [embedding task type](https://cloud.google.com/vertex-ai/generative-ai/docs/embeddings/task-types). Task types tell the embedding model the intended use of the text, which changes how the embedding is generated. There are two formatting patterns:

- **Asymmetric format** — documents and queries use *different* task types. This is the pattern for retrieval use cases, where the document being indexed has a different intent than the query searching for it:

| Use Case | Query Task Type | Document Task Type |
|----------|----------------|--------------------|
| Search Query | `RETRIEVAL_QUERY` | `RETRIEVAL_DOCUMENT` |
| Question Answering | `QUESTION_ANSWERING` | `RETRIEVAL_DOCUMENT` |
| Fact Checking | `FACT_VERIFICATION` | `RETRIEVAL_DOCUMENT` |
| Code Retrieval | `CODE_RETRIEVAL_QUERY` | `RETRIEVAL_DOCUMENT` |

- **Symmetric format** — both sides use the *same* task type (`SEMANTIC_SIMILARITY`, `CLASSIFICATION`, or `CLUSTERING`).

> **Key point:** If your use case doesn't align with a documented use case, use `RETRIEVAL_QUERY` as the default query task type.

In this project, we index documents with `RETRIEVAL_DOCUMENT` (set in the collection's vector schema) and search with `QUESTION_ANSWERING` (set at query time in step 8). This asymmetric pairing tells the embedding model that the indexed text is reference material and the search text is a question — producing embeddings optimized for matching questions to relevant documents.

#### 5a. Create Reddit Collection

[create_collection_reddit.py](create_collection_reddit.py) creates a collection for Reddit thread chunks. The collection defines:

- **Data schema:** Mirrors the BigQuery `reddit_chunks` table — `chunk_id`, `text_content`, `source_uri`, `subreddit`, `timestamp_unix`, `karma`, `is_image_description`, plus enrichment fields `topics` and `methods_mentioned`.
- **Vector schema:** Dense auto-embedding (`text_content_embedding`) using `gemini-embedding-001` (`EMBEDDING_DIMENSIONS`=768, `RETRIEVAL_DOCUMENT` task type), plus a sparse vector field (`bm25_embedding`) populated by step 7b.

The script is idempotent — if the collection already exists, it skips creation and verifies the existing collection.

#### 5b. Create Zoom Collection

[create_collection_zoom.py](create_collection_zoom.py) creates a collection for Zoom transcript chunks. Same pattern as 5a with a Zoom-specific data schema:

- **Data schema:** `chunk_id`, `text_content`, `source_uri`, `speaker_list` (array of strings), `timestamp_start`, `timestamp_end`, plus enrichment fields `topics` and `action_items`.
- **Vector schema:** Same as the Reddit collection — dense auto-embedding + sparse `bm25_embedding`.

Separate collections per data type enforce strict schema validation and prevent cross-type field conflicts.

#### 5c. Create PDF Collection

[create_collection_pdf.py](create_collection_pdf.py) creates a collection for PDF document chunks. Same pattern as 5a with a PDF-specific data schema:

- **Data schema:** `chunk_id`, `text_content`, `source_uri`, `page_start`, `page_end`, plus enrichment fields `topics` and `functions_referenced`.
- **Vector schema:** Same as other collections — dense auto-embedding + sparse `bm25_embedding`.

#### 5d. Create Combined Collection

[create_collection_combined.py](create_collection_combined.py) creates a single collection for cross-type search across all data types. The schema is the union of all fields from all per-type collections plus a `source_type` discriminator:

- **Data schema:** Common fields (`chunk_id`, `text_content`, `source_uri`, `source_type`) plus all type-specific fields — Reddit (`subreddit`, `timestamp_unix`, `karma`, `is_image_description`), Zoom (`speaker_list`, `timestamp_start`, `timestamp_end`), and PDF (`page_start`, `page_end`). Enrichment fields from all types: `topics`, `methods_mentioned`, `action_items`, `functions_referenced`. Fields not relevant to a given source type are left empty at import time.
- **Vector schema:** Same as the per-type collections — dense auto-embedding + sparse `bm25_embedding`.

This enables cross-type search with full metadata — e.g., finding related content across a Reddit thread and a PDF document about the same forecasting topic, then filtering or inspecting type-specific fields in the results.

---

### 6a. Import Reddit Data Objects

[import_reddit_objects.py](import_reddit_objects.py) reads all Reddit chunks from BigQuery and creates [Data Objects](https://cloud.google.com/vertex-ai/docs/vector-search-2/data-objects/data-objects) in the Reddit collection using individual creates (not batch). Each chunk becomes a DataObject with:

- **`data_object_id`:** The `chunk_id` from BigQuery.
- **`data`:** All schema fields from the chunk row, including enrichment tags (`topics`, `methods_mentioned`).
- **`vectors`:** Empty — auto-embeddings generate the `text_content_embedding` automatically.

Uses direct (single-create) mode to simulate a continuously running system where new chunks are imported as they arrive. Existing DataObjects are skipped on re-run.

### 6b. Import Zoom Data Objects

[import_zoom_objects.py](import_zoom_objects.py) follows the same pattern as 6a for Zoom transcript chunks. Reads from the BigQuery `zoom_chunks` table and creates DataObjects in the Zoom collection with auto-generated embeddings. Includes enrichment fields `topics` and `action_items`.

### 6c. Import PDF Data Objects

[import_pdf_objects.py](import_pdf_objects.py) follows the same pattern as 6a for PDF document chunks. Reads from the BigQuery `pdf_chunks` table and creates DataObjects in the PDF collection with auto-generated embeddings. Includes enrichment fields `topics` and `functions_referenced`.

### 6d. Batch Import All Data Objects to Combined Collection

[import_combined_objects.py](import_combined_objects.py) reads chunks from all three BigQuery tables (Reddit, Zoom, PDF), adds a `source_type` field to each, deduplicates by `chunk_id`, and batch-imports them into the combined collection from step 5d. Each source's enrichment fields are included — `methods_mentioned` for Reddit, `action_items` for Zoom, `functions_referenced` for PDF, and `topics` for all types.

Unlike steps 6a-6c which use individual `create_data_object` calls (simulating a continuously running system where chunks arrive one at a time), this step uses `batch_create_data_objects` to send up to 1,000 DataObjects per API call. This is more efficient for bulk loading scenarios where all data is available upfront. The batch API handles embedding generation for all objects in the batch.

This enables unified cross-type retrieval — a single query can find relevant content across Reddit threads, Zoom transcripts, and PDF documents.

#### Alternative: GCS Import for Large Datasets

For large-scale imports, Vector Search 2.0 supports [importing DataObjects directly from JSONL files in GCS](https://cloud.google.com/vertex-ai/docs/vector-search-2/data-objects/data-objects#importing_data_objects) via the `import_data_objects` long-running operation. This is more efficient than API-based batch creation when loading thousands or millions of objects.

**Step 1 — Export from BigQuery to JSONL in GCS.** Each line must be a JSON object with `data_object_id` (the chunk ID) and `data` (the schema fields). For the combined collection:

```sql
EXPORT DATA OPTIONS (
  uri = 'gs://YOUR_BUCKET/path/to/export/*.jsonl',
  format = 'JSON',
  overwrite = true
) AS
SELECT
  chunk_id AS data_object_id,
  TO_JSON(STRUCT(
    chunk_id, text_content, source_uri, source_type,
    subreddit, timestamp_unix, karma, is_image_description,
    speaker_list, timestamp_start, timestamp_end,
    page_start, page_end,
    topics, methods_mentioned, action_items, functions_referenced
  )) AS data
FROM (
  SELECT *, 'reddit' AS source_type FROM `dataset.prefix_reddit_chunks`
  UNION ALL
  SELECT *, 'zoom' AS source_type FROM `dataset.prefix_zoom_chunks`
  UNION ALL
  SELECT *, 'pdf' AS source_type FROM `dataset.prefix_pdf_chunks`
);
```

**Step 2 — Import into the collection.** The `contents_uri` points to the JSONL export path, and `error_uri` is a GCS path where any per-row errors are written:

```python
from google.cloud import vectorsearch_v1beta

client = vectorsearch_v1beta.VectorSearchServiceClient()

operation = client.import_data_objects(
    vectorsearch_v1beta.ImportDataObjectsRequest(
        name="projects/PROJECT_ID/locations/LOCATION/collections/COLLECTION_ID",
        gcs_import={
            "contents_uri": "gs://YOUR_BUCKET/path/to/export/",
            "error_uri": "gs://YOUR_BUCKET/path/to/import-errors/",
        },
    )
)

response = operation.result()  # blocks until import completes
```

Auto-embeddings are generated during import, just like with the API-based approaches. This pattern keeps data preparation in BigQuery (SQL) and avoids loading data into Python memory, making it well-suited for pipelines where chunk counts grow beyond what fits in a single batch API call.

---

### 7. Build & Apply BM25 Sparse Embeddings

BM25 (Best Matching 25) is a statistical ranking function that scores documents based on term frequency and inverse document frequency. Unlike dense embeddings that capture semantic meaning in a fixed-size vector, BM25 produces sparse vectors — most dimensions are zero, with non-zero values only for terms that appear in the document.

**Model parameters:**
- **k1** (1.2) — Term frequency saturation. Controls how quickly repeated terms stop increasing the score. Lower values (toward 0) saturate faster; higher values (toward 2) let frequency continue to matter.
- **b** (0.6) — Document length normalization. Controls how much longer documents are penalized. 0 = no penalty, 1 = full penalty proportional to length.
- **epsilon** (0.25) — IDF smoothing floor. Prevents terms not in the corpus from having negative IDF scores.

**Approach B — text + enrichment tags:** BM25 input for each chunk is `text_content` concatenated with enrichment tag values (topics, methods, functions, action items). This normalizes extracted concepts into the BM25 vocabulary — a topic like "demand forecasting" tagged on both a Reddit chunk and a PDF chunk produces shared BM25 terms that wouldn't appear in the raw text of both. The alternative (text only) would miss this cross-type normalization.

**Inspection notebook:** [inspect_bm25.ipynb](inspect_bm25.ipynb) demonstrates the BM25 pipeline on a small sample of chunks before running the full build — shows preprocessing, input construction, model training, sparse embedding computation, and query embedding.

#### 7a. Train BM25 Model

[build_bm25.py](build_bm25.py) trains the BM25 model and stores the vocabulary + metadata in BigQuery:

1. Read all chunks from BigQuery (3 tables)
2. Build BM25 input text for each chunk (Approach B)
3. Preprocess → tokenized corpus (lowercase, lemmatize, stopwords, n-grams)
4. Train `BM25Okapi` model
5. Save vocabulary to BigQuery (`{prefix}_bm25_vocabulary` table: term, index, IDF, version)
6. Save model metadata to BigQuery (`{prefix}_bm25_model` table: corpus size, vocab size, avgdl, parameters)

**Version history:** Each training run writes a new version to BigQuery using `WRITE_APPEND`. All versions are preserved in both the vocabulary and model tables, enabling comparison across training runs and rollback to a previous version. Re-running with the same `BM25_MODEL_VERSION` in [config.py](config.py) is idempotent — it deletes the existing rows for that version before appending.

#### 7b. Apply BM25 Sparse Embeddings

[apply_bm25.py](apply_bm25.py) loads a trained BM25 model from BigQuery, computes sparse embeddings for chunks that need updating, and writes the results to BQ chunk tables and VS2 DataObjects. Schema updates are handled automatically — no need to recreate collections or alter tables manually:

1. Load BM25 model from BigQuery (vocabulary, IDF values, parameters)
2. Add BM25 columns to BQ chunk tables if they don't exist (idempotent `ALTER TABLE`)
3. Find chunks needing update (`bm25_model_version IS NULL` or `< target version`)
4. Compute sparse embedding for each chunk (indices + values)
5. Update BigQuery chunk tables with BM25 columns (`bm25_indices`, `bm25_values`, `bm25_text`, `bm25_model_version`)
6. Check each VS2 collection's vector schema for `bm25_embedding` — add the sparse vector field via `update_collection` if missing
7. Update VS2 DataObjects with sparse vectors via `batch_update_data_objects` (all 4 collections)

The apply script reconstructs the BM25 scoring function entirely from stored parameters — it does not need the `rank_bm25` library or a retrained model object. This means any version of the model stored in BigQuery can be applied at any time.

**Usage:**
```bash
uv run python apply_bm25.py              # apply latest model version
uv run python apply_bm25.py --version 1  # apply (or rollback to) version 1
uv run python apply_bm25.py --all        # re-embed all chunks (ignore version check)
```

**Incremental updates:** Only chunks with `bm25_model_version IS NULL` (never embedded) or `< target version` (stale) are processed. After importing new chunks (step 6), re-running `apply_bm25.py` adds sparse embeddings to just the new chunks without reprocessing existing ones.

**Rollback:** Use `--version N` to apply a previous model version's vocabulary to all chunks. This re-embeds everything using the older vocabulary and IDF values, effectively rolling back the sparse search behavior.

The VS2 update uses `update_mask=FieldMask(paths=["vectors"])` to update only the sparse vector field without touching the data fields or dense auto-embeddings.

---

### 8. Search & Query

[search_and_query.ipynb](search_and_query.ipynb) is an interactive notebook organized by **search taxonomy** — each section demonstrates a search method, making it a reference for "how do I do X?" All demonstrations use the Combined collection (117 DataObjects: 34 Reddit + 12 Zoom + 71 PDF).

The notebook reveals how different search methods surface different content: SemanticSearch for "demand forecasting" returns all Reddit discussion chunks, TextSearch for "ARIMA" returns all PDF documentation chunks, and BM25 sparse search returns a different PDF ranking than TextSearch for the same keywords. Hybrid search and crowding address these source-type biases by combining multiple signals or enforcing diversity constraints.

**Search Taxonomy:**

| Method | API | What Drives Results |
|--------|-----|---------------------|
| **Query** | `query_data_objects` | Field filters (`$eq`, `$gt`, `$in`) |
| **SemanticSearch** | `search_data_objects` | Auto-embedded dense similarity |
| **TextSearch** | `search_data_objects` | Native keyword matching |
| **VectorSearch (dense)** | `search_data_objects` | Dense vector you supply |
| **VectorSearch (sparse)** | `search_data_objects` | Sparse BM25 vector you supply |
| **VectorSearch (dense+sparse)** | `batch_search_data_objects` | Two VectorSearch channels via RRF |
| **Hybrid: Semantic+Text (RRF)** | `batch_search_data_objects` | 2-channel RRF fusion |
| **Hybrid: Semantic+Sparse (RRF)** | `batch_search_data_objects` | 2-channel RRF with BM25 |
| **Hybrid: 3-way (RRF)** | `batch_search_data_objects` | 3-channel RRF (semantic + text + sparse) |
| **Reranked: VertexRanker** | `batch_search_data_objects` | Cross-encoder reranking (not yet supported) |
| **Crowding** | Async parallel filtered search | Per-group diversity |

**Key distinctions:**
- **Query vs Search** — Query = metadata filtering only, no relevance ranking (like SQL `WHERE`). Search = ranked results by relevance.
- **Semantic vs Vector** — SemanticSearch = you provide text, VS2 auto-embeds it. VectorSearch = you provide raw vector(s) — required for sparse search and external embedding models.
- **Dense + Sparse** — `VectorSearch` uses a `oneof` for `vector` (dense) and `sparse_vector` — you can supply one per search channel, not both. To combine dense + sparse vectors, use `batch_search_data_objects` with two VectorSearch channels fused via RRF.
- **Manual embedding dimensions** — When supplying dense vectors manually via VectorSearch, set `output_dimensionality` to match the collection schema (`EMBEDDING_DIMENSIONS` in [config.py](config.py), currently 768). `gemini-embedding-001` natively produces 3072 dims; VS2 auto-embed handles truncation internally for SemanticSearch.
- **SearchHint (ANN vs kNN)** — `VectorSearch` and `SemanticSearch` accept a `search_hint` parameter to control index usage. By default, VS2 auto-selects an ANN index if one exists, falling back to brute-force kNN. Use `SearchHint(use_knn=True)` to force exact kNN search (useful for recall evaluation). `TextSearch` does not support `search_hint`. See step 10 for ANN index management and recall benchmarking.
- **RRF vs VertexRanker** — RRF is purely statistical rank fusion (fast, weight-tunable). VertexRanker is a model-based cross-encoder that scores each (query, document) pair (more accurate, slower). VertexRanker is defined in the `vectorsearch_v1beta` API but not yet implemented by the backend — use RRF for now.

---

### 9. BM25 Maintenance

As the corpus evolves — new documents are added, existing documents are updated or removed — the BM25 vocabulary may drift from the current data. Step 9 provides tools for monitoring this drift and rebuilding when needed.

**Inspection notebook:** [inspect_bm25_maintenance.ipynb](inspect_bm25_maintenance.ipynb) analyzes the BM25 vocabulary in BigQuery and evaluates whether a rebuild is needed. Computes three drift metrics:

- **OOV rate** — % of terms in the current corpus not in the stored vocabulary (threshold: 10%)
- **Stale rate** — % of vocabulary terms no longer in the current corpus (threshold: 15%)
- **Corpus size delta** — % change in total chunks since last training (threshold: 20%)

**Scheduled script:** [refresh_bm25.py](refresh_bm25.py) automates drift detection with conditional rebuild. Designed to be run on a schedule (e.g., Cloud Scheduler → Cloud Run function):

1. Load current model metadata from BigQuery
2. Read all current chunks and compute current terms
3. Compare against stored vocabulary to compute drift metrics
4. If any metric exceeds its threshold → retrain the BM25 model with an incremented version number and save the new vocabulary + metadata to BigQuery (the previous version is preserved for comparison and rollback)
5. If no drift → exit early with "No rebuild needed"

After a rebuild, run `apply_bm25.py` to compute new sparse embeddings and update BQ chunk tables + VS2 DataObjects. The separation between retrain (refresh) and apply means you can inspect the new model before committing to a full re-embedding.

Thresholds are configurable in [config.py](config.py) (`BM25_OOV_THRESHOLD`, `BM25_STALE_THRESHOLD`, `BM25_CORPUS_DELTA`).

---

### 10. ANN Index Management

All searches in steps 1–9 use brute-force kNN (exact nearest neighbor), which scans every DataObject in the collection. This works well at small scale (117 DataObjects) but won't scale to thousands+. [ANN indexes](https://cloud.google.com/vertex-ai/docs/vector-search-2/indexes/indexes) trade a small amount of recall for significantly lower query latency by building an approximate nearest neighbor index over the dense embeddings.

**When to build:** Collection size ≥ `ANN_INDEX_THRESHOLD` (default 1000, configurable in [config.py](config.py)). Below this threshold, brute-force kNN is efficient and provides exact results.

**Script:** [manage_ann_index.py](manage_ann_index.py) checks collection size, creates an ANN index when the threshold is reached, or deletes an existing index:

```bash
uv run python manage_ann_index.py            # check size, create if >= threshold
uv run python manage_ann_index.py --delete    # delete the ANN index
```

**Index configuration:**

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `index_field` | `text_content_embedding` | Dense vector field from vector schema |
| `distance_metric` | `DOT_PRODUCT` | Default distance metric (also supports `COSINE_DISTANCE`) |
| `filter_fields` | `["source_type"]` | Fast ANN inline filtering (avoids post-filter recall loss) |
| `store_fields` | `["chunk_id", "text_content", "source_type", "source_uri"]` | Inline data retrieval (avoids separate data fetch) |

**`filter_fields` vs `store_fields`:**
- **`filter_fields`**: Fields pushed into the index for fast ANN inline filtering. When you filter by `source_type` during a search, the index applies the filter during the ANN search rather than post-filtering results — this avoids recall loss where post-filtering could remove good matches. Add frequently filtered fields here.
- **`store_fields`**: Fields pushed into the index for inline data retrieval. Search results include these fields without a separate data fetch. This reduces latency for common result fields. Full metadata is still available via `output_fields` at slightly higher latency.
- **Trade-off**: More fields = larger index = more memory, but faster queries. Keep both lists small — add fields only when the performance benefit is measurable.

**Once built**, the ANN index auto-updates as DataObjects are added or removed — no manual rebuild needed. Queries automatically use the ANN index unless overridden.

**SearchHint — controlling ANN vs kNN at query time:**

`VectorSearch` and `SemanticSearch` accept a `search_hint` parameter. `TextSearch` does not support `search_hint`.

| Behavior | How to set |
|----------|-----------|
| **Auto (default)** | Omit `search_hint` — uses ANN index if available, falls back to kNN |
| **Force kNN** | `search_hint=SearchHint(use_knn=True)` — brute-force exact results |
| **Force specific index** | `search_hint=SearchHint(use_index=IndexHint(name=...))` — target a named index |

`SearchResponseMetadata` in the response reports which engine was used (`used_index` or `used_knn`).

**Recall comparison:** At small scale (117 DataObjects), ANN and kNN produce identical results (recall = 1.0). As the collection grows, ANN may trade a small amount of recall for significant latency improvement. The inspection notebook [inspect_ann_index.ipynb](inspect_ann_index.ipynb) benchmarks recall@k across test queries and compares kNN vs ANN latency.

---

## Planned Enhancements

The current system covers the full retrieval pipeline: multi-format parsing, semantic enrichment, dense + sparse embeddings, hybrid search with RRF, and ANN index management. The enhancements below are organized in four phases that progress from completing the RAG loop through agentic intelligence and production deployment.

### Phase 1: Complete the RAG Loop

The retrieval layer is mature but the system doesn't yet produce answers, measure quality, or analyze its own cost profile. These steps close those gaps and establish the baselines needed before adding agentic intelligence.

- **Grounded Generation with Gemini**: Connect retrieval results to Gemini for generating responses grounded in the retrieved chunks — turning the search pipeline into a full RAG (Retrieval-Augmented Generation) system. Include citation attribution back to source chunks, configurable system instructions for response style, and context window management for large result sets.

- **Evaluation**: Set up systematic evaluation of both retrieval quality and generated response quality. Retrieval metrics: recall@k, MRR (Mean Reciprocal Rank), and NDCG across a labeled query set. Generation metrics: LLM-as-judge for answer faithfulness (does the answer stay grounded in the retrieved chunks?), relevance (does it address the question?), and completeness (does it cover all relevant retrieved information?). Establish baselines before tuning retrieval or generation parameters. Evaluation should run before and after any pipeline change to catch regressions.

- **Chunking Strategy Evaluation**: Use the evaluation framework to measure how chunking decisions affect retrieval quality. The current strategies — Reddit tree flattening, Zoom sliding window (5-cue, 3-cue overlap), PDF Layout Parser — are reasonable defaults but were not tuned against retrieval metrics. Evaluate chunk size, overlap, and boundary decisions as dimensions alongside search method choice. Chunk boundaries often matter more than search method for retrieval quality.

- **Latency and Cost Analysis**: Profile the per-query cost of each search path — single-channel, 2-way RRF, 3-way RRF, crowding — in terms of API calls, latency, and token consumption. As the system adds layers (reranking, multi-hop, self-evaluation in Phase 2), the cumulative cost per user question could grow significantly. Establish a cost framework that tracks API calls per query path so that Phase 2 agent decisions can be evaluated on cost/quality trade-offs, not just quality alone.

### Phase 2: Scale and Agentic Intelligence with ADK

Before adding agentic capabilities, generate additional synthetic records to push the collection past the ANN threshold and provide a realistic scale for agent testing. Then, rather than building standalone components for query routing, reranking, and multi-hop retrieval, these capabilities emerge from an [Agent Development Kit (ADK)](https://google.github.io/adk-docs/) agent with well-designed tools. Each step adds a new capability that the agent both detects the need for and solves agentically.

- **Scale Demonstration**: Generate additional synthetic input records of each type (Reddit threads, Zoom meetings, PDF documents) using the existing step 0 generation scripts, then run the full pipeline end-to-end. This exercises capabilities that are dormant at the current 117-DataObject size: ANN index creation triggers when the collection crosses the 1000-DataObject threshold (`manage_ann_index.py`), `inspect_ann_index.ipynb` shows real ANN vs kNN recall/latency trade-offs instead of identical results, and `refresh_bm25.py` detects vocabulary drift from the new documents and triggers a conditional rebuild. Running at scale before the ADK steps ensures agent routing, reranking, and multi-hop decisions are tested against a realistically sized corpus, not just 117 DataObjects where every strategy returns similar results.

- **ADK Agent — Basic Retrieval + Generation**: Wrap retrieval and generation as ADK tools. The agent takes a question, picks a search method, retrieves chunks, and generates a grounded answer. This alone replaces the manual workflow of choosing a search type, running it, and reading results. Tools: `semantic_search`, `text_search`, `sparse_search`, `hybrid_search`, `crowded_search`, `generate_answer`.

- **ADK Agent — Search Strategy Selection**: The agent has all search methods as separate tools and reasons about which to use based on the query. A keyword lookup ("ARIMA") routes to `text_search`. A conceptual question ("What methods handle seasonality?") routes to `semantic_search`. A mixed query ("ARIMA seasonal decomposition") routes to `hybrid_search`. If initial results are poor (few results, low relevance), the agent tries a different strategy. This replaces a standalone query routing classifier — the agent *is* the router, with the advantage that it can adapt mid-conversation and explain its reasoning.

- **ADK Agent — Reranking as a Tool**: Add reranking tools that the agent calls when it detects mixed-quality results. Two tools compared: (1) [Vertex AI Ranking API](https://cloud.google.com/generative-ai-app-builder/docs/ranking) via the `discoveryengine.RankService` SDK — a standalone cross-encoder service that accepts a query and candidate documents. (2) Gemini as a reranker — prompt Gemini to score each (query, chunk) pair for relevance. The agent decides *whether* to rerank based on the query complexity and initial result quality — simple queries with clear top results skip reranking, while ambiguous queries with mixed sources benefit from it. Measure NDCG lift over the RRF baseline using the evaluation framework from Phase 1.

- **ADK Agent — Multi-Hop Retrieval**: The agent searches, reads results, identifies gaps in coverage, and issues follow-up searches with refined queries. For example: "Compare ARIMA and Prophet for retail forecasting" → first search retrieves Reddit opinions → agent notices no technical documentation → second search filtered to PDF source type → agent synthesizes both perspectives. The agent detects the need for multi-hop by reasoning about whether the retrieved context sufficiently addresses all aspects of the question.

- **ADK Agent — Self-Evaluation**: The agent generates an answer, then critiques it against the retrieved chunks before returning it. It checks for unsupported claims (hallucination), missing coverage (the chunks mention a relevant method the answer omitted), and confidence level. If the critique reveals issues, the agent retries with better retrieval or flags uncertainty to the user. This provides runtime quality control that complements the offline evaluation framework.

- **ADK Agent — Observability and Evaluation**: Enable the ADK BigQuery plugin to log all agent request/response pairs to a BigQuery table — capturing the full decision trace: which tools the agent called, in what order, what it retrieved, how it routed, whether it reranked, and the final generated answer. This provides the observability needed to debug agent behavior and understand *why* the agent chose a particular strategy. Use the logged traces to run offline evaluation against the Phase 1 framework: measure retrieval quality (recall@k, NDCG) and generation quality (faithfulness, relevance) across real agent sessions, not just synthetic test queries. Compare agent-routed search quality against the fixed baselines (e.g., did the agent's strategy selection actually outperform always-hybrid?). This closes the loop between runtime agent decisions and systematic quality measurement.

### Phase 3: Infrastructure & Deployment

These steps move the system from development scripts and notebooks to a production-grade service.

- **Real-Time Pipeline Automation**: Replace the current batch-run scripts with an event-driven pipeline that reacts to GCS changes in real time. Use [Eventarc](https://cloud.google.com/eventarc/docs/overview) or [GCS notifications](https://cloud.google.com/storage/docs/pubsub-notifications) to trigger processing when files are added, updated, or deleted — routing each event through the full chain (parse → enrich → import). Handle document updates by detecting changed `updated` timestamps via the object table, re-parsing affected files, re-enriching their chunks, and updating the corresponding DataObjects in Vector Search. Handle deletions by removing orphaned chunks from BigQuery and their DataObjects from collections. Track metadata changes (e.g., updated karma scores, new speaker labels) independently of content changes so metadata-only updates skip re-parsing and re-embedding. Orchestrate with [Cloud Workflows](https://cloud.google.com/workflows/docs/overview) or [Cloud Run functions](https://cloud.google.com/functions/docs/concepts/overview) for lightweight per-event processing, or [Cloud Composer](https://cloud.google.com/composer/docs/concepts/overview) for complex DAG-based orchestration with retry and dependency management.

- **ADK on Vertex AI Agent Engine**: Deploy the ADK agent to [Vertex AI Agent Engine](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview) for managed hosting with built-in scaling, authentication, and monitoring. This transitions the agent from a local development tool to a production service with API endpoints, session management, and observability.

- **ADK Agent in Gemini Enterprise**: Register the ADK agent as an extension in [Gemini for Google Cloud](https://cloud.google.com/gemini/docs/overview), making the retrieval pipeline accessible directly within the Gemini Enterprise experience. End users interact with the corpus through natural language in the Gemini interface without needing to understand the underlying search taxonomy or pipeline architecture.

### Phase 4: Maintenance

- **Resource Cleanup**: Create scripts to tear down all resources created by the pipeline. Delete VS2 collections and their DataObjects, ANN indexes, BigQuery tables (chunk tables, BM25 vocabulary and model tables), GCS objects under the project prefix, and Document AI processors. Include both a full cleanup script (remove everything) and a selective mode (e.g., delete only DataObjects and collections while preserving BigQuery tables for analysis). This supports repeatable demos, cost management, and clean re-runs of the pipeline from scratch.

---

## Acknowledged Limitations

This solution is a reference implementation designed to demonstrate VS2 capabilities and RAG pipeline architecture. The following limitations are inherent to its design scope and should be considered when adapting it for production use.

- **Synthetic corpus**: All input data (Reddit threads, Zoom transcripts, PDF documents) is generated by Gemini in step 0. This produces clean, well-structured content that doesn't reflect real-world data quality challenges — OCR errors, spam, broken formatting, transcription artifacts, off-topic content. The semantic enrichment step (LangExtract) extracts structured entities from text produced by the same model family, which is artificially clean. Parsing and enrichment strategies have not been stress-tested against messy real-world data.

- **Single domain**: The entire corpus is about time series forecasting and BigQuery ML. Parsing strategies, enrichment schemas (`topics`, `methods_mentioned`, `functions_referenced`), BM25 vocabulary, and search queries are all domain-specific. Adapting to a different domain would require new enrichment schemas and potentially different chunking strategies. The enrichment-fed BM25 approach (Approach B) is a design pattern that should generalize, but this has not been validated across domains.

- **Per-type collections**: Four VS2 collections exist (Reddit, Zoom, PDF, Combined) with identical schemas. The search notebook and all downstream steps use only the combined collection. The per-type collections serve the import step and demonstrate that VS2 supports multiple collections, but they add maintenance overhead (potential 4x BM25 updates, 4x ANN indexes) without a demonstrated retrieval benefit in this solution. In a production system, per-type collections would justify their cost through access control, independent scaling, or type-specific search — none of which are implemented here.

- **No real user feedback**: The evaluation framework (Phase 1) uses LLM-as-judge and synthetic queries. There is no mechanism for real user queries, click-through signals, or relevance feedback. Production RAG systems improve from user signals over time. The agent's self-evaluation (Phase 2) provides runtime quality control but is model-judging-model, not ground truth.

- **Single model dependency**: The system uses Gemini for data generation (step 0), enrichment (step 4), embeddings (`gemini-embedding-001`), and planned generation, reranking, and evaluation. This is appropriate for a Google Cloud reference implementation but represents a single-vendor dependency for all AI capabilities.
