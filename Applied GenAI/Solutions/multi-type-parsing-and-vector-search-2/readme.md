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

### 1. Files in GCS

The workflow starts with documents in Google Cloud Storage. [upload_to_gcs.py](upload_to_gcs.py) uploads all generated files to the GCS bucket/path defined in [config.py](config.py) and sets custom metadata on each object:

| Source Type | Metadata Keys |
|-------------|--------------|
| Reddit (JSON) | `source-type`, `file-format`, `content-domain`, `subreddit`, `thread-title`, `comment-count` |
| Zoom (VTT) | `source-type`, `file-format`, `content-domain`, `cue-count` |
| PDF | `source-type`, `file-format`, `content-domain` |

Metadata is set during upload (single operation per file). The `source-type` metadata is used downstream to route files to the correct parser.

### 2. BigQuery Object Table

The pipeline involves multiple stages — parsing, chunking, augmenting metadata, and preparing Vector Search input — each adding data that relates back to source files. Rather than managing this across loose files, we use BigQuery as the central data layer:

- **Object tables** give a queryable base over GCS files with their URIs, metadata, sizes — no ETL needed
- **Relational joins** let each downstream table (chunks, embeddings, augmented metadata) key back to source files
- **Inspectability** at every stage via SQL (e.g. "which files haven't been parsed?")
- **Export** to JSONL for Vector Search input is a single `EXPORT DATA` statement

[create_object_table.py](create_object_table.py) creates the BigQuery dataset and object table over the GCS path. The table name follows the convention `{BQ_TABLE_PREFIX}_source` from [config.py](config.py).

**BigQuery Connection:** Object tables need a [Cloud Resource connection](https://cloud.google.com/bigquery/docs/create-cloud-resource-connection) — this is just a one-time setup for the project. The connection provides a service account that BigQuery uses to read from GCS on your behalf. The script handles this automatically: it checks for an existing connection (named per `BQ_CONNECTION` in [config.py](config.py)), creates one if needed, and grants its service account `objectViewer` on your GCS bucket. Nothing to configure manually.

> **Note:** The object table is a live, auto-refreshing view over GCS with [configurable staleness](https://docs.cloud.google.com/bigquery/docs/object-table-introduction#metadata_caching_for_performance).

### 3a. Parse Reddit Threads

[parse_reddit.py](parse_reddit.py) reads Reddit JSON files from GCS (discovered via the object table) and produces chunked rows in BigQuery (`{BQ_TABLE_PREFIX}_reddit_chunks`).

**Tree flattening:** Comments use `comment_id`/`parent_id` references. The parser walks up the parent chain for each comment to build a path-based text representation:
```
THREAD: Post Title | PARENT: Parent comment (truncated to 200 chars) | COMMENT: Full comment body
```
This preserves conversational context — each chunk carries its lineage from the thread root.

**SNR filtering:** Non-top-level comments shorter than `SHORT_RESPONSE_THRESHOLD` (default: 15 tokens) are dropped. Top-level comments are always kept regardless of length. This removes low-signal replies like "this" or "+1" while preserving substantive short top-level posts.

**VLM image enrichment:** When a comment has an `image_url`, Gemini generates a dense 2-3 sentence description anchored to the comment's text context. The description is appended as `| IMAGE: ...`. If the VLM call fails, the chunk is kept without an image description and `is_image_description` remains `true`.

**Output schema:** `chunk_id`, `source_uri`, `text_content`, `subreddit`, `timestamp_unix`, `karma`, `is_image_description`, `processed_at`

**Incremental:** Tracks staleness by comparing each chunk's `processed_at` timestamp against the GCS object's `updated` timestamp. On re-run, new Reddit files are parsed and appended, updated files have their old chunks replaced, and unchanged files are skipped.

### 3b. Parse Zoom Transcripts

[parse_zoom.py](parse_zoom.py) reads WebVTT files from GCS and produces chunked rows in BigQuery (`{BQ_TABLE_PREFIX}_zoom_chunks`).

**VTT parsing:** Each cue is extracted with its timestamp range and speaker label. Speaker names are split from the text content (format: `Speaker Name: dialogue text`).

**Sliding window:** Cues are grouped into overlapping windows of `WINDOW_SIZE` (default: 15) cues with `OVERLAP` (default: 5) cues shared between consecutive windows. This ensures no context is lost at chunk boundaries — each chunk overlaps with its neighbors.

**Rolling summary:** For every window after the first, Gemini generates a 15-word summary of the previous window's content. This summary is prepended as `[Summary: ...] ` to provide continuity context for downstream retrieval. The first window has no summary prefix.

**Output schema:** `chunk_id`, `source_uri`, `text_content`, `speaker_list` (repeated), `timestamp_start`, `timestamp_end`, `processed_at`

**Incremental:** Tracks staleness by comparing each chunk's `processed_at` timestamp against the GCS object's `updated` timestamp. On re-run, new VTT files are parsed and appended, updated files have their old chunks replaced, and unchanged files are skipped.

### 3c. Parse PDFs (Coming Soon)

PDF parsing will use [Document AI](https://cloud.google.com/document-ai) with LLM-powered layout parsing combined with Gemini for content enrichment. Will follow the same incremental processing pattern as the other parsers.

### 4a. Create Reddit Collection

[create_collection_reddit.py](create_collection_reddit.py) creates a [Vector Search 2.0](https://cloud.google.com/vertex-ai/docs/vector-search-2/overview) collection for Reddit thread chunks. The collection defines:

- **Data schema:** Mirrors the BigQuery `reddit_chunks` table — `chunk_id`, `text_content`, `source_uri`, `subreddit`, `timestamp_unix`, `karma`, `is_image_description`.
- **Vector schema:** A single dense embedding field (`text_content_embedding`) with [auto-embeddings](https://cloud.google.com/vertex-ai/docs/vector-search-2/data-objects/data-objects#auto-populate-embeddings) configured to embed the `text_content` field using `gemini-embedding-001` (768 dimensions, `RETRIEVAL_DOCUMENT` task type).

The script is idempotent — if the collection already exists, it skips creation and verifies the existing collection.

### 4b. Create Zoom Collection

[create_collection_zoom.py](create_collection_zoom.py) creates a Vector Search 2.0 collection for Zoom transcript chunks. Same pattern as 4a with a Zoom-specific data schema:

- **Data schema:** `chunk_id`, `text_content`, `source_uri`, `speaker_list` (array of strings), `timestamp_start`, `timestamp_end`.
- **Vector schema:** Same auto-embedding configuration as the Reddit collection — `text_content_embedding` using `gemini-embedding-001`.

Separate collections per data type enforce strict schema validation and prevent cross-type field conflicts.

### 4c. Create PDF Collection (Coming Soon)

Will follow the same pattern as 4a and 4b once PDF parsing is implemented.

### 4d. Create Combined Collection (Coming Soon)

A single collection that accepts all data types (Reddit, Zoom, PDF) with a unified schema. This enables cross-type search — e.g., finding related discussion across a Reddit thread and a Zoom meeting about the same forecasting topic.

### 5a. Import Reddit Data Objects

[import_reddit_objects.py](import_reddit_objects.py) reads all Reddit chunks from BigQuery and creates [Data Objects](https://cloud.google.com/vertex-ai/docs/vector-search-2/data-objects/data-objects) in the Reddit collection using individual creates (not batch). Each chunk becomes a DataObject with:

- **`data_object_id`:** The `chunk_id` from BigQuery.
- **`data`:** All schema fields from the chunk row.
- **`vectors`:** Empty — auto-embeddings generate the `text_content_embedding` automatically.

Uses direct (single-create) mode to simulate a continuously running system where new chunks are imported as they arrive. Existing DataObjects are skipped on re-run.

### 5b. Import Zoom Data Objects

[import_zoom_objects.py](import_zoom_objects.py) follows the same pattern as 5a for Zoom transcript chunks. Reads from the BigQuery `zoom_chunks` table and creates DataObjects in the Zoom collection with auto-generated embeddings.

### 5c. Import PDF Data Objects (Coming Soon)

Will follow the same pattern as 5a and 5b once PDF parsing and collection creation are implemented.

### 5d. Import All Data Objects to Combined Collection (Coming Soon)

Import chunks from all data types (Reddit, Zoom, PDF) into the combined collection from 4d, enabling unified cross-type retrieval.

### 6. Search & Query

[search_and_query.ipynb](search_and_query.ipynb) is an interactive notebook demonstrating all search and query capabilities across both collections:

- **Query**: Filter DataObjects by field values (`$gt`, `$eq`, `$and`, etc.) — analogous to SQL `WHERE` clauses. Examples include filtering Reddit chunks by karma threshold and combined filters (karma + image-enriched).
- **Semantic Search**: Natural language queries like *"What machine learning methods work best for demand forecasting?"* that find conceptually relevant chunks via auto-generated embeddings. Uses `QUESTION_ANSWERING` task type to pair with documents indexed as `RETRIEVAL_DOCUMENT`.
- **Text Search**: Keyword-based matching for specific terms like *"ARIMA"* or *"Prophet"* — useful for acronyms and method names that may not have strong semantic representation.
- **Hybrid Search with RRF**: Combines semantic and text search using [Reciprocal Rank Fusion](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf). A comparison table shows how the same query produces different rankings under three weight configurations (`[1,1]`, `[3,1]`, `[1,3]`), demonstrating how weight tuning shifts results between intent-based and keyword-based relevance.

## Planned Enhancements

Future work to augment this solution:

- **Sparse Embeddings (BM25)**: Add BM25-based sparse embeddings alongside the existing dense embeddings for improved keyword-aware hybrid search. Vector Search 2.0 supports custom sparse vectors in the vector schema.
- **ANN Indexes vs kNN**: Create [ANN indexes](https://cloud.google.com/vertex-ai/docs/vector-search-2/indexes/indexes) on collections and benchmark latency/recall against the current brute-force kNN search. Demonstrate the trade-off between index build time and query performance at scale.
- **Grounded Generation with Gemini**: Connect retrieval results to Gemini for generating responses grounded in the retrieved chunks — turning the search pipeline into a full RAG (Retrieval-Augmented Generation) system.
- **Evaluation**: Set up systematic evaluation of retrieval quality and generated responses using metrics like recall@k, MRR, and LLM-as-judge for answer faithfulness and relevance.
- **ADK Agent Integration**: Connect the retrieval and generation pipeline to [Agent Development Kit (ADK)](https://google.github.io/adk-docs/) agents, enabling tool-use patterns where agents can search across collections, filter by metadata, and synthesize answers from multiple sources.
- **ADK on Vertex AI Agent Engine**: Deploy the ADK agent to [Vertex AI Agent Engine](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview) for managed hosting with built-in scaling, authentication, and monitoring.
- **ADK Agent in Gemini Enterprise**: Register the ADK agent as an extension in [Gemini for Google Cloud](https://cloud.google.com/gemini/docs/overview), making the retrieval pipeline accessible directly within the Gemini Enterprise experience.
