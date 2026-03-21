# Data + AI — Plans

A living document tracking the vision, structure, and implementation plans for the `data+ai/` section of the repository.

## Vision

Tell the full **data science story on GCP**: data, ML, AI, and the solutions that combine them. Show how Google Cloud services work together across the entire lifecycle — from reading data to training models to serving predictions to applying AI functions.

## Directory Structure

Current and planned structure. Items marked `(existing)` are already built; others are planned.

```
data+ai/
├── readme.md                       # (existing) — top-level navigation
├── PLANS.md                        # this file
├── model-serving.md                # (existing) — model deployment guide
├── gcp-databases.md                # (existing) — GCP database overview
├── resources/                      # (existing) — shared images/assets
├── bq-ai-functions/                # (existing) — BigQuery AI functions
│   └── readme.md                   # (existing)
├── dataflow/                       # (existing) — Dataflow GPU benchmark
├── bq-ml/                          # planned — ML models inside BigQuery
│   └── readme.md
├── tabular-data/                   # (existing) — reading tabular data for ML
│   ├── readme.md                   # (existing)
│   └── bq-reads/                   # (existing) — BigQuery → pandas efficiently
│       ├── readme.md               # (existing)
│       ├── pyproject.toml           # (existing)
│       └── bq-reads.ipynb          # (existing)
├── ml-training/                    # planned — ML across compute environments
│   ├── readme.md
│   ├── dataproc/
│   ├── vertex-training/
│   ├── vertex-workbench/
│   ├── colab-enterprise/
│   ├── local/
│   ├── gke/
│   └── gce/
```

## Conventions

Every new piece of content must follow these rules:

1. **Every folder gets a `readme.md`** — describes what the folder contains and links to its children.
2. **Parent readmes link to children** — when a new folder is added, update the parent's `readme.md` to include a link and description.
3. **Top-level `readme.md`** — the root `data+ai/readme.md` must reflect all top-level sections. Update it whenever a new top-level folder is added.
4. **Notebook self-containment** — notebooks install their own dependencies (prefer `uv`, fallback to `pip`).
5. **Dual format where appropriate** — provide both `.ipynb` and `.sql` when SQL-centric content is involved.

## Current Priority: `tabular-data/bq-reads/`

### Goal

A single notebook (`bq-reads.ipynb`) showcasing how to efficiently read tabular data from BigQuery into pandas, comparing approaches by **cost** and **time**. Positions **Storage Read API** as the maximum-control option and **BigFrames** as the easy option that uses storage reads underneath.

### Environment Setup

- `pyproject.toml` lives at `tabular-data/bq-reads/` level
- Uses the same uv + pip fallback pattern from `bq-ai-functions/`
- `uv sync --group dev` → `ipykernel install` for local dev
- Notebooks include inline install cell for standalone use (Colab, Vertex Workbench, etc.)

### Demo Table

A large BigQuery public table with numeric columns suitable for ML — must support:
- **Large reads** for thread-count benchmarking
- **Column pruning** to show reading a subset of columns
- **Row filtering** to show filtered reads on the same table

Table: `bigquery-public-data.chicago_taxi_trips.taxi_trips` — 211M rows, 82.4 GB, 23 columns (11 numeric selected for ML). Row filter on `trip_start_timestamp` gives ~2.75M rows for benchmarking.

### Notebook Structure (as built)

The notebook follows a methodical arc: **motivate → showcase each approach → compare**.

1. **Setup** — uv/pip install cell, imports, client initialization, authentication
2. **Demo Table** — Chicago Taxi Trips: table metadata, preview, column selection (11 numeric for ML), date range discovery, row filter with memory estimation
3. **Motivation** — Cost ($6.25/TB query vs 300 TiB/month free storage reads) and speed as the two axes. Overview table with 7 columns including thread control.
4. **Approach 1: `client.query()`** — Query with `use_query_cache=False`, show bytes billed, cost estimate, 100-run projection. Note: `.to_dataframe()` auto-uses Storage API for download.
5. **Approach 2: `client.list_rows()`** — Storage read, no query cost. Sequential only. `selected_fields` for column pruning, `max_results` for row limiting.
6. **Approach 3: pandas-gbq** — Default (REST, slow) vs `use_bqstorage_api=True` (fast). Note `max_results` gotcha.
7. **Approach 4: BigFrames** — Lazy operations, `read_gbq_table()` with `columns` + `filters` + `ordering_mode="partial"` (zero cost), `read_gbq()` with SQL (has cost, faster). `to_pandas_batches()` for memory-safe chunked downloads.
8. **Approach 5: Storage Read API** — `create_read_session()` helper, column pruning savings (77%), row filter estimated bytes explanation, multi-stream architecture.
9. **Thread benchmarking** — [1, 2, 4, 8, 16, 32] threads with `ThreadPoolExecutor` and `tqdm`. Memory cleanup between runs. Thread scaling chart with speedup calculations.
10. **Async alternative** — `asyncio.to_thread()` + `asyncio.gather()` with `Semaphore`. Benchmarked against ThreadPoolExecutor. Explains why async only helps Storage API (other approaches are single blocking calls).
11. **Comparison chart** — Color-coded horizontal bar chart sorted by time: blue (Storage API, free), green (BigFrames table+filters, free), red (query cost), yellow (slow).
12. **ML Framework alternatives** — Table of BigQuery→framework paths (scikit-learn, PyTorch, JAX, Keras, TensorFlow I/O).
13. **Summary** — Recommendations table (6 approaches × cost), 9 key takeaways.

### Implementation Checklist

- [x] Create `tabular-data/` folder with `readme.md`
- [x] Create `tabular-data/bq-reads/` folder with `readme.md` and `pyproject.toml`
- [x] Create `bq-reads.ipynb` notebook
- [x] Update `tabular-data/readme.md` to link to `bq-reads/`
- [x] Update top-level `data+ai/readme.md` to add `tabular-data/` section

## Future Work

### `bq-ml/` — BigQuery ML
- Demonstrate training and using ML models directly in BigQuery SQL
- Cover model types: linear, logistic, XGBoost, DNN, time series, etc.

### `ml-training/` — ML Across Compute Environments
- Same ML task run across different GCP compute targets
- Subfolders per environment: Dataproc, Vertex Training, Vertex Workbench, Colab Enterprise, local, GKE, GCE
- Highlight trade-offs: cost, setup complexity, scale, integration

### `tabular-data/` — Additional Data Sources
- `alloydb-reads/` — reading from AlloyDB
- `spanner-reads/` — reading from Spanner
- `gcs-reads/` — reading Parquet/CSV from GCS
