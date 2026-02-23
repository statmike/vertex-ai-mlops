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
Generate ─► Upload ─► Object Table ─► Parse & Chunk ─► Enrich ─► Collections ─► Import ─► Search
 (0)         (1)         (2)           (3a-3c)         (4a-4c)     (5a-5d)      (6a-6d)    (7)
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
| **5a-5d. Collections** | Schema definitions | 4 Vector Search 2.0 collections | Define data + vector schemas with auto-embeddings (`gemini-embedding-001`) |
| **6a-6d. Import** | BQ chunk tables | DataObjects in collections | Create DataObjects; embeddings auto-generated from `text_content` |
| **7. Search** | Natural language queries | Ranked results with metadata | Semantic, text, hybrid/RRF, filtered, crowded, enrichment-filtered search |

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

In this project, we index documents with `RETRIEVAL_DOCUMENT` (set in the collection's vector schema) and search with `QUESTION_ANSWERING` (set at query time in step 7). This asymmetric pairing tells the embedding model that the indexed text is reference material and the search text is a question — producing embeddings optimized for matching questions to relevant documents.

#### 5a. Create Reddit Collection

[create_collection_reddit.py](create_collection_reddit.py) creates a collection for Reddit thread chunks. The collection defines:

- **Data schema:** Mirrors the BigQuery `reddit_chunks` table — `chunk_id`, `text_content`, `source_uri`, `subreddit`, `timestamp_unix`, `karma`, `is_image_description`, plus enrichment fields `topics` and `methods_mentioned`.
- **Vector schema:** A single dense embedding field (`text_content_embedding`) with auto-embeddings configured to embed the `text_content` field using `gemini-embedding-001` (768 dimensions, `RETRIEVAL_DOCUMENT` task type).

The script is idempotent — if the collection already exists, it skips creation and verifies the existing collection.

#### 5b. Create Zoom Collection

[create_collection_zoom.py](create_collection_zoom.py) creates a collection for Zoom transcript chunks. Same pattern as 5a with a Zoom-specific data schema:

- **Data schema:** `chunk_id`, `text_content`, `source_uri`, `speaker_list` (array of strings), `timestamp_start`, `timestamp_end`, plus enrichment fields `topics` and `action_items`.
- **Vector schema:** Same auto-embedding configuration as the Reddit collection — `text_content_embedding` using `gemini-embedding-001`.

Separate collections per data type enforce strict schema validation and prevent cross-type field conflicts.

#### 5c. Create PDF Collection

[create_collection_pdf.py](create_collection_pdf.py) creates a collection for PDF document chunks. Same pattern as 5a with a PDF-specific data schema:

- **Data schema:** `chunk_id`, `text_content`, `source_uri`, `page_start`, `page_end`, plus enrichment fields `topics` and `functions_referenced`.
- **Vector schema:** Same auto-embedding configuration — `text_content_embedding` using `gemini-embedding-001`.

#### 5d. Create Combined Collection

[create_collection_combined.py](create_collection_combined.py) creates a single collection for cross-type search across all data types. The schema is the union of all fields from all per-type collections plus a `source_type` discriminator:

- **Data schema:** Common fields (`chunk_id`, `text_content`, `source_uri`, `source_type`) plus all type-specific fields — Reddit (`subreddit`, `timestamp_unix`, `karma`, `is_image_description`), Zoom (`speaker_list`, `timestamp_start`, `timestamp_end`), and PDF (`page_start`, `page_end`). Enrichment fields from all types: `topics`, `methods_mentioned`, `action_items`, `functions_referenced`. Fields not relevant to a given source type are left empty at import time.
- **Vector schema:** Same auto-embedding configuration as the per-type collections.

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

### 6d. Import All Data Objects to Combined Collection

[import_combined_objects.py](import_combined_objects.py) reads chunks from all three BigQuery tables (Reddit, Zoom, PDF), adds a `source_type` field to each, and imports them into the combined collection from step 5d. Each source's enrichment fields are included — `methods_mentioned` for Reddit, `action_items` for Zoom, `functions_referenced` for PDF, and `topics` for all types. This enables unified cross-type retrieval — a single query can find relevant content across Reddit threads, Zoom transcripts, and PDF documents.

---

### 7. Search & Query

[search_and_query.ipynb](search_and_query.ipynb) is an interactive notebook demonstrating all search and query capabilities across all four collections (Reddit, Zoom, PDF, Combined):

- **Query**: Filter DataObjects by field values (`$gt`, `$eq`, `$and`, etc.) — analogous to SQL `WHERE` clauses. Examples include filtering Reddit chunks by karma threshold, PDF chunks by page range, and combined filters (karma + image-enriched).
- **Semantic Search**: Natural language queries like *"What machine learning methods work best for demand forecasting?"* that find conceptually relevant chunks via auto-generated embeddings. Uses `QUESTION_ANSWERING` task type at query time — the asymmetric counterpart to the `RETRIEVAL_DOCUMENT` task type used when the documents were indexed (see [embedding task types](#5-create-collections) in step 5).
- **Text Search**: Keyword-based matching for specific terms like *"ARIMA"* or *"CREATE MODEL"* — useful for acronyms and method names that may not have strong semantic representation.
- **Hybrid Search with RRF**: Combines semantic and text search using [Reciprocal Rank Fusion](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf). A comparison table shows how the same query produces different rankings under three weight configurations (`[1,1]`, `[3,1]`, `[1,3]`), demonstrating how weight tuning shifts results between intent-based and keyword-based relevance.
- **Filtered Semantic Search**: Pre-filters on `SemanticSearch` restrict vector similarity ranking to a metadata subset (e.g., `source_type == 'pdf'`) without affecting embedding comparison quality.
- **Crowding/Diversity Search**: Retrieves top-k results per unique value of a metadata field (e.g., 2 results per `source_type`) using the `DataObjectSearchServiceAsyncClient` to run filtered semantic searches concurrently via `asyncio.gather`. Includes a reusable `crowded_search` helper that works with any metadata field — demonstrated with both `source_type` and `source_uri` crowding.
- **Enrichment-Based Filtering**: Filter by semantic tags from step 4 (e.g., `topics`, `methods_mentioned`) to find chunks about specific subjects. Enrichment tags appear alongside structural metadata in search results, giving richer context for downstream RAG pipelines.

---

## Planned Enhancements

Future work to augment this solution:

- **Sparse Embeddings (BM25)**: Add BM25-based sparse embeddings alongside the existing dense embeddings for improved keyword-aware hybrid search. Vector Search 2.0 supports custom sparse vectors in the vector schema.
- **ANN Indexes vs kNN**: Create [ANN indexes](https://cloud.google.com/vertex-ai/docs/vector-search-2/indexes/indexes) on collections and benchmark latency/recall against the current brute-force kNN search. Demonstrate the trade-off between index build time and query performance at scale.
- **Grounded Generation with Gemini**: Connect retrieval results to Gemini for generating responses grounded in the retrieved chunks — turning the search pipeline into a full RAG (Retrieval-Augmented Generation) system.
- **Evaluation**: Set up systematic evaluation of retrieval quality and generated responses using metrics like recall@k, MRR, and LLM-as-judge for answer faithfulness and relevance.
- **ADK Agent Integration**: Connect the retrieval and generation pipeline to [Agent Development Kit (ADK)](https://google.github.io/adk-docs/) agents, enabling tool-use patterns where agents can search across collections, filter by metadata, and synthesize answers from multiple sources.
- **ADK on Vertex AI Agent Engine**: Deploy the ADK agent to [Vertex AI Agent Engine](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview) for managed hosting with built-in scaling, authentication, and monitoring.
- **ADK Agent in Gemini Enterprise**: Register the ADK agent as an extension in [Gemini for Google Cloud](https://cloud.google.com/gemini/docs/overview), making the retrieval pipeline accessible directly within the Gemini Enterprise experience.
