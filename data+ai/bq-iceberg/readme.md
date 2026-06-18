![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Fdata%2Bai%2Fbq-iceberg&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/data%2Bai/bq-iceberg/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-iceberg/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-iceberg/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-iceberg/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-iceberg/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-iceberg/readme.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-iceberg/readme.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# BigQuery Iceberg

Set up a large **Apache Iceberg managed table** in BigQuery (and use a large public **native** table directly) to demonstrate reading BigQuery data, and read them from **Python**.

This folder owns the **setup** (the one-time infrastructure plumbing). It is a **prerequisite** for the R reads notebook, which focuses purely on read patterns:
➡️ [Framework Workflows/R/R - Reading BigQuery Iceberg Tables](../../Framework%20Workflows/R/R%20-%20Reading%20BigQuery%20Iceberg%20Tables.ipynb)

## The Notebook

- **[bq-iceberg-setup.ipynb](bq-iceberg-setup.ipynb)** — creates a BigLake Cloud Resource connection (+ IAM), a dataset, and an **Apache Iceberg managed table** from a large public dataset (so it shards into many Parquet files); the **native** table is the public source read directly (no copy). Reads both from Python with BigFrames and the BigQuery Storage Read API. Ends with a handoff cell printing the identifiers the R notebook consumes.

## BigQuery + Apache Iceberg: which table type?

BigQuery has three Iceberg-adjacent table types — it's worth being precise:

| Type | Managed by | Read/Write | Created with |
|---|---|---|---|
| **External table** (generic) | not BigQuery | read-only | `CREATE EXTERNAL TABLE ... OPTIONS(format=...)` |
| **Apache Iceberg external table** | another engine (e.g. Spark) | read-only | `CREATE EXTERNAL TABLE ... OPTIONS(format='ICEBERG', uris=[...])` |
| **Apache Iceberg managed table** ⬅️ *used here* | **BigQuery** (writes data files, compaction, metadata) | **read-write, full DML** | `CREATE TABLE ... WITH CONNECTION ... OPTIONS(file_format='PARQUET', table_format='ICEBERG', storage_uri=...)` |

This folder creates the **managed** type — formerly *BigLake tables for Apache Iceberg in BigQuery*, now **[Apache Iceberg managed tables](https://docs.cloud.google.com/bigquery/docs/biglake-iceberg-tables-in-bigquery)**. BigQuery owns the file lifecycle, but the bytes are ordinary **Parquet** in *your own* Cloud Storage bucket (a `/data` folder of Parquet shards plus an Iceberg V2 snapshot in `/metadata`) — so any Iceberg-aware engine (R `arrow`, Spark, …) can read the same files. That is exactly what the R reads notebook does.

## Environment Setup

Set up a virtual environment with [uv](https://docs.astral.sh/uv/):

```bash
cd "data+ai/bq-iceberg"
uv sync --group dev
uv run python -m ipykernel install --user --name bq-iceberg --display-name "Python (bq-iceberg)"
```

Then select the `Python (bq-iceberg)` kernel when opening the notebook.

**Alternative — pip:**

```bash
cd "data+ai/bq-iceberg"
python -m venv .venv && source .venv/bin/activate
pip install -e . ipykernel
python -m ipykernel install --user --name bq-iceberg --display-name "Python (bq-iceberg)"
```

> **Running on Colab, Colab Enterprise, or Vertex AI Workbench?** The notebook includes an install cell that handles packages automatically — no local setup needed.

## What It Creates

| Resource | Identifier (defaults) |
|---|---|
| BigLake Cloud Resource connection | `biglake-iceberg` (region `us`) |
| Dataset | `r` |
| Apache Iceberg managed table | `r.taxi_iceberg` (data at `gs://<bucket>/r/taxi_iceberg/iceberg`) |
| Native table | the public source, **read directly** — not copied into your project |

Source data: [`bigquery-public-data.chicago_taxi_trips.taxi_trips`](https://console.cloud.google.com/marketplace/product/city-of-chicago-public-data/chicago-taxi-trips) — ~212M rows / ~83 GB. Large on purpose: at this size the Iceberg managed table is written as **many** Parquet shards, which is what lets the R notebook demonstrate genuinely **multithreaded** parallel reads. Set `ROW_LIMIT` in the notebook to create a smaller/cheaper table.

> ⚠️ **Cost & runtime.** Creating the Iceberg table scans ~83 GB (~$0.40 one-time) and writes ~83 GB of Parquet to your bucket (ongoing storage until cleanup); the `CREATE TABLE` takes a few minutes. Native reads use the public table directly, so no 83 GB copy is made.

A **Cleanup** section at the end of the notebook removes the Iceberg table (and its Parquet), the connection, and GCS data.
