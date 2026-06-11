![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FMLOps%2FFeature+Store%2FSpanner&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Feature%20Store/Spanner/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Feature%2520Store/Spanner/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Feature%2520Store/Spanner/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Feature%2520Store/Spanner/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Feature%2520Store/Spanner/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
<tr>
  <td style="text-align: right">
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/MLOps/Feature%20Store/Spanner/readme.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/MLOps/Feature%20Store/Spanner/readme.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# Spanner Feature Store

> You are here: `vertex-ai-mlops/MLOps/Feature Store/Spanner/readme.md`

A SQL-powered online feature store on [Cloud Spanner](https://cloud.google.com/spanner/docs/overview). Spanner trades ~2–5ms vs Bigtable's sub-5ms for SQL at the serving layer — JOINs, secondary indexes, complex predicates, ACID transactions — plus automatic multi-region with strong consistency and a 99.999% SLA.

> **Also in this series: [Bigtable Feature Store](../Bigtable/readme.md), [BigQuery Feature Store](../BigQuery/readme.md), [Valkey Feature Store](../Valkey/readme.md), and [Vertex AI Feature Store](../vertex/readme.md)**
>
> This Spanner approach gives you **SQL at the serving layer** — secondary indexes for non-key queries, serving-time JOINs across feature tables, and multi-row ACID transactions. For sub-5ms key-based lookups with full control, see [Bigtable Feature Store](../Bigtable/readme.md). For sub-ms in-memory serving with HNSW vector search, see [Valkey Feature Store](../Valkey/readme.md). For zero-infrastructure serving with 20–200ms latency, see [BigQuery Feature Store](../BigQuery/readme.md). For a fully managed solution, see [Vertex AI Feature Store](../vertex/readme.md). All approaches use BigQuery as the offline store. See the [comparison table](../readme.md#choosing-an-approach) in the parent readme.

The data uses a 130K-entity dataset in BigQuery dataset `spanner_feature_store` — 26 entity groups (A–Z) × 5,000 entities, 224 columns spanning every BigQuery data type. Each feature store series has its own independent BigQuery dataset with the same schema.

## Presentation

A 20-slide overview of this series — positions Spanner on the latency spectrum, walks through the architecture, and shows how all 12 notebooks fit together (with measured results from a live 100 PU Enterprise instance):

- [Spanner Feature Store — Overview (PDF)](./Spanner%20Feature%20Store%20-%20Overview.pdf)
- [Spanner Feature Store — Overview (HTML)](./Spanner%20Feature%20Store%20-%20Overview.html) — to view: click the link, then use the download button (↓) to save locally and open in your browser
- [Spanner Feature Store — Overview (source)](./Spanner%20Feature%20Store%20-%20Overview.md) — Marp markdown source

## Environment Setup

### Option 1: Local environment

From this directory (`MLOps/Feature Store/Spanner/`):

**uv** (recommended)
```bash
uv sync
uv run python -m ipykernel install --user --name spanner-feature-store --display-name "Spanner Feature Store"
```

**pip**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m ipykernel install --user --name spanner-feature-store --display-name "Spanner Feature Store"
```

Then select the **Spanner Feature Store** kernel in your notebook.

### Option 2: Standalone

Each notebook includes an environment setup cell that installs required packages into your current kernel.

## Teardown / Cleanup

The Spanner instance bills continuously — **delete it when you're done.** Teardown is automated by `cleanup.py`, parameterized by a `cleanup.json` that the Environment notebook writes with this run's resource names (`cleanup.json` is gitignored).

From this directory (`MLOps/Feature Store/Spanner/`):

```bash
# Dry run — show what would be deleted (default, safe)
uv run python cleanup.py

# Delete the Spanner instance (removes database, tables, change streams)
uv run python cleanup.py --yes

# Also delete the BigQuery dataset (kept by default — it's cheap and reusable)
uv run python cleanup.py --yes --include-dataset

# Verify no continuous queries are still running (lists running BQ jobs; deletes nothing)
uv run python cleanup.py --check-jobs
```

`cleanup.py` defaults to a dry run and is idempotent (already-deleted resources are reported, not errored). The **Spanner instance is the main cost**; the BigQuery dataset is kept by default. Run the Environment notebook at least once first so `cleanup.json` exists.

The synchronization notebook demonstrates **continuous queries** (BigQuery → Spanner) that are designed to stop within the notebook run — so the teardown script doesn't manage them. `--check-jobs` lists any BigQuery jobs still in the `RUNNING` state so you can confirm none leaked; if one did, stop it with `bq cancel <job_id>`.

## Notebooks — Run in This Order

Run the Environment notebook first. After that, notebooks 1–6 build on each other sequentially. Notebooks 7–11 can be explored in any order but benefit from the concepts in earlier notebooks.

| # | Notebook | Prerequisites | What It Covers |
|---|----------|---------------|----------------|
| **0** | [Environment](./Spanner%20Feature%20Store%20-%20Environment.ipynb) | None | BigQuery dataset (creates if needed), Spanner instance (100 PU, **Enterprise edition** for vector/ANN), database, feature table with composite PK, data investigation, Processing Units, data type mapping, sample data load |
| **1** | [Fundamentals](./Spanner%20Feature%20Store%20-%20Fundamentals.ipynb) | NB0 | Full 130K entity load from BigQuery, SQL point reads, range scans, batch reads, INFORMATION_SCHEMA, EXPLAIN query plans, strong vs stale read latency baseline |
| **2** | [Synchronization](./Spanner%20Feature%20Store%20-%20Synchronization.ipynb) | NB0, NB1 | Batch sync with INSERT OR UPDATE, continuous queries (BQ → Spanner), scheduled DML, change streams for reverse sync, post-sync validation, propagation latency |
| **3** | [Secondary Indexes](./Spanner%20Feature%20Store%20-%20Secondary%20Indexes.ipynb) | NB0, NB1 | Create indexes on feature columns, non-PK queries at sub-10ms, STORING clause for covering queries, NULL_FILTERED, composite indexes, query plan analysis, write amplification |
| **4** | [Interleaved Tables](./Spanner%20Feature%20Store%20-%20Interleaved%20Tables.ipynb) | NB0 | Parent-child table co-location with INTERLEAVE IN PARENT, 2-table and 3-table JOINs, ON DELETE CASCADE, interleaved vs flat table trade-offs |
| **5** | [Transactions](./Spanner%20Feature%20Store%20-%20Transactions.ipynb) | NB0, NB1 | Read-write ACID transactions, strong vs stale reads (EXACT_STALENESS, MAX_STALENESS), batch DML, cross-table transactions, optimistic concurrency, latency benchmarks |
| **6** | [Schema Evolution](./Spanner%20Feature%20Store%20-%20Schema%20Evolution.ipynb) | NB0, NB1 | Online DDL (ADD/DROP COLUMN), backfill with partitioned DML, INFORMATION_SCHEMA for runtime discovery, schema version tracking, backward compatibility |
| **7** | [Serving Integration](./Spanner%20Feature%20Store%20-%20Serving%20Integration.ipynb) | NB0, NB1, optionally NB4 | Train model on BigQuery, serve from Spanner, serving-time JOINs, FastAPI endpoint, session pool, parameterized queries, training-serving skew detection, concurrent load test |
| **8** | [Vector Embeddings](./Spanner%20Feature%20Store%20-%20Vector%20Embeddings.ipynb) | NB0, NB1 | Store ARRAY<FLOAT64> embeddings, client-side cosine similarity, SQL pre-filtering (Spanner's unique angle), filter size vs latency benchmarks |
| **9** | [Multi-Region](./Spanner%20Feature%20Store%20-%20Multi-Region.ipynb) | NB0 | Multi-regional configs (nam3, etc.), read-write vs read-only vs witness replicas, automatic failover, stale reads for geo-local serving, cost implications |
| **10** | [Emulator](./Spanner%20Feature%20Store%20-%20Emulator.ipynb) | None | Start Spanner emulator, SPANNER_EMULATOR_HOST, same client code as production, pytest fixtures, GitHub Actions CI/CD, emulator capabilities and limitations |
| **11** | [Production Deployment](./Spanner%20Feature%20Store%20-%20Production%20Deployment.ipynb) | NB0 | Terraform (google_spanner_instance, google_spanner_database with DDL), multi-table recommendation engine capstone (user_profiles + item_catalog + user_item_interactions), SQL candidate retrieval, serving-time JOINs, transactional updates, load testing |

## Key Concepts

- **[Composite Primary Key](https://cloud.google.com/spanner/docs/schema-and-data-model#primary_keys)** — `(entity_group, entity_id)` determines row ordering and split distribution. Unlike Bigtable's concatenated row key, Spanner's composite PK is first-class.
- **[Secondary Indexes](https://cloud.google.com/spanner/docs/secondary-indexes)** — Enable sub-10ms queries on any indexed column. Bigtable can only query by row key prefix. This is Spanner's fundamental flexibility advantage for feature stores.
- **[Interleaved Tables](https://cloud.google.com/spanner/docs/schema-and-data-model#creating-interleaved-tables)** — Parent-child tables guaranteed to be stored on the same split. Makes multi-table JOINs local operations.
- **[ACID Transactions](https://cloud.google.com/spanner/docs/transactions)** — Multi-row, multi-table atomic updates. Bigtable has single-row atomicity only.
- **[Stale Reads](https://cloud.google.com/spanner/docs/reads#read_types)** — Trade consistency for latency. `EXACT_STALENESS` and `MAX_STALENESS` serve from local replicas without a leader round-trip.
- **[Continuous Queries](https://cloud.google.com/bigquery/docs/continuous-queries-introduction)** — BigQuery's native sync path to Spanner via `INSERT INTO` (not `EXPORT DATA`).
- **[INFORMATION_SCHEMA](https://cloud.google.com/spanner/docs/information-schema)** — Self-describing schema. No custom metadata row needed (unlike Bigtable's `#schema` row).

## Prerequisites

- A GCP project with billing enabled
- APIs enabled: Spanner, BigQuery, Pub/Sub
- Python >= 3.10
- The Environment notebook creates the instance at **ENTERPRISE edition** — required for the ScaNN vector indexes and ANN search in the Vector Embeddings (NB8) and Production Deployment (NB11) notebooks. STANDARD edition supports only exact KNN distance functions; those two notebooks detect the edition and fall back gracefully.

## Documentation

| Topic | Link |
|-------|------|
| Cloud Spanner overview | [Overview](https://cloud.google.com/spanner/docs/overview) |
| Schema and data model | [Schema design](https://cloud.google.com/spanner/docs/schema-and-data-model) |
| Secondary indexes | [Indexes](https://cloud.google.com/spanner/docs/secondary-indexes) |
| Transactions | [Transactions](https://cloud.google.com/spanner/docs/transactions) |
| Stale reads | [Read types](https://cloud.google.com/spanner/docs/reads) |
| Change streams | [Change streams](https://cloud.google.com/spanner/docs/change-streams) |
| Multi-region configs | [Replication](https://cloud.google.com/spanner/docs/replication) |
| Spanner emulator | [Emulator](https://cloud.google.com/spanner/docs/emulator) |
| Python client | [API reference](https://cloud.google.com/python/docs/reference/spanner/latest) |
| Spanner pricing | [Pricing](https://cloud.google.com/spanner/pricing) |
| Continuous queries to Spanner | [Continuous queries](https://cloud.google.com/bigquery/docs/continuous-queries-introduction) |
