![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FFramework+Workflows%2FR&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%20Workflows/R/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%2520Workflows/R/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%2520Workflows/R/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%2520Workflows/R/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Framework%2520Workflows/R/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/Framework%20Workflows/R/readme.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/Framework%20Workflows/R/readme.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# Running R on Google Cloud
> You are here: `vertex-ai-mlops/Framework Workflows/R/readme.md`

An R-first guide to running [**R**](https://www.r-project.org/) on Google Cloud — where R runs, how to get BigQuery data into R at any size, and how to serve an R model. Most notebooks run **one shared workflow** (a fraud-detection GLM) across different runtimes, so you can compare them for your own work. New here? Start with **R - Notebook Workflow**.

---
## Notebooks

The **Kernel** column tells you which environment to select when you open the notebook — `R` is the `R (Local)` kernel, `Python` is the `Python (r-on-gcp)` kernel (the R code runs remotely in a container). See [Setup](#setup).

| Notebook | What it does | Kernel |
|---|---|---|
| [R - Notebook Workflow](./R%20-%20Notebook%20Workflow.ipynb) | **Start here.** The shared GLM end-to-end in a notebook — read from BigQuery, train, evaluate, save. | R |
| [R - Vertex AI Custom Training Job](./R%20-%20Vertex%20AI%20Custom%20Training%20Job.ipynb) | The same workflow as a managed job — scale up data/compute, schedule or trigger, pay per run. | Python |
| [R - Dataproc Serverless Spark-R](./R%20-%20Dataproc%20Serverless%20Spark-R.ipynb) | The same workflow distributed with SparkR (`spark.glm`) when data outgrows one machine. | Python |
| [R - Vertex AI Pipelines](./R%20-%20Vertex%20AI%20Pipelines.ipynb) | The same workflow as an orchestrated KFP pipeline; two code-delivery patterns (code-as-input vs. baked image). | Python |
| [R - Reading BigQuery Iceberg Tables](./R%20-%20Reading%20BigQuery%20Iceberg%20Tables.ipynb) | Read native & Apache Iceberg tables, small to large — `bigrquery`, Storage Read API, multithreaded `arrow` over Parquet. Needs the [`data+ai/bq-iceberg`](../../data%2Bai/bq-iceberg/readme.md) setup notebook first. | R |
| [R - Serving Predictions](./R%20-%20Serving%20Predictions.ipynb) | Wrap `model.rds` in a `plumber` container; deploy & predict on a Vertex AI Endpoint and Cloud Run. | Python |

Shared scripts: [`code/train.R`](./code/train.R) (the GLM workflow) and [`code/sparkr.R`](./code/sparkr.R) (the SparkR variant).

---
## Setup

The notebooks use two kinds of kernels.

**R kernel** — for *R - Notebook Workflow* and *R - Reading BigQuery Iceberg Tables*. On a Vertex AI Workbench Instance, add R with conda, then select the **R (Local)** kernel:

```bash
conda create -n r && conda activate r
conda install -c r r-essentials
conda install -c conda-forge r-bigrquery r-bigrquerystorage r-arrow r-dbi r-dplyr r-dbplyr
```

**Python kernel** — for the four Python-driver notebooks (Custom Training, Dataproc, Pipelines, Serving), which call the Vertex AI / Dataproc / KFP SDKs. Set up a Python environment with [uv](https://docs.astral.sh/uv/) and register the kernel:

```bash
cd "Framework Workflows/R"
uv sync --group dev
uv run python -m ipykernel install --user --name r-on-gcp --display-name "Python (r-on-gcp)"
```

<details><summary>Alternative — pip instead of uv</summary>

```bash
cd "Framework Workflows/R"
python -m venv .venv && source .venv/bin/activate
pip install -e . ipykernel
python -m ipykernel install --user --name r-on-gcp --display-name "Python (r-on-gcp)"
```
</details>

> **On Colab, Colab Enterprise, or Vertex AI Workbench?** The Python-driver notebooks include an install cell that handles packages automatically — no local setup needed.

---
## The Shared Workflow

The first four notebooks run the *same* task, so the only thing that changes is the execution environment:

> A logistic-regression fraud-detection **GLM** (`glm(..., family = binomial)`) on `bigquery-public-data.ml_datasets.ulb_fraud_detection` (284,807 credit-card transactions; PCA features `V1..V28` plus `Time`/`Amount`; target `Class`).

It's factored into one script — [`code/train.R`](./code/train.R): read `TRAIN`/`TEST` splits → fit GLM → evaluate → `saveRDS` (the SparkR runtime uses [`code/sparkr.R`](./code/sparkr.R)). Data prep is done once in BigQuery into a `*_prepped` table. All reads stay on the columnar stack — **Parquet** on disk, **Arrow** in memory (Storage Read API or `arrow`), never a CSV export.

---
## Where R Runs

**Interactive environments:**
- **Vertex AI Workbench Instances** — JupyterLab; add R via a [conda environment](https://cloud.google.com/vertex-ai/docs/workbench/instances/add-environment) (see [Setup](#setup)), use the **R (Local)** kernel.
- **Cloud Workstations** — managed dev environments; a config can use [**Posit Workbench / RStudio Pro**](https://cloud.google.com/workstations/docs/develop-code-using-posit-workbench-rstudio) or a custom container.
- **BigQuery Studio / Colab Enterprise** — notebook surfaces that run R and execute notebooks programmatically.

**Managed runtimes** run the shared workflow as a job — pick by *how* you need to run it:

| Runtime | Notebook | When to use |
|---|---|---|
| Interactive notebook | [R - Notebook Workflow](./R%20-%20Notebook%20Workflow.ipynb) | Develop & run end-to-end live; the starting point |
| Vertex AI Custom Training | [R - Vertex AI Custom Training Job](./R%20-%20Vertex%20AI%20Custom%20Training%20Job.ipynb) | Scale up data/compute as a managed job; schedule or trigger; pay per run |
| Dataproc Serverless (Spark-R) | [R - Dataproc Serverless Spark-R](./R%20-%20Dataproc%20Serverless%20Spark-R.ipynb) | Data outgrows one machine; distributed read + `spark.glm` |
| Vertex AI Pipelines (KFP) | [R - Vertex AI Pipelines](./R%20-%20Vertex%20AI%20Pipelines.ipynb) | Orchestrated, reproducible R steps in an MLOps DAG |

For these same R runtimes shown beside Python and other Google Cloud ML services, see the [ml-training comparison series](../../data%2Bai/overview/ml-training/readme.md).

<details><summary>Runtime notes &amp; gotchas — containers, R-vs-Python kernel, Spark/PySpark/Spark-R</summary>

**Containers** — the job runtimes build a custom R container from the community [`rocker/r-ver`](https://rocker-project.org/images/versioned/r-ver.html) base via Cloud Build (Vertex AI's prebuilt `r-cpu` images still work but are on a deprecation path, so this series doesn't depend on them). The base image needs two things added: `libprotobuf-dev` + `libgrpc++-dev` (runtime deps of `bigrquerystorage` — without them the Storage Read API silently falls back to REST), and model output written via the **Cloud Storage FUSE mount** (`AIP_MODEL_DIR` → `/gcs/...`) rather than `gcloud`/`gsutil`, which `rocker/r-ver` does not ship.

**R vs. Python kernel** — the job-launch notebooks use a Python kernel for the Vertex AI / Dataproc / KFP SDKs. For an all-R driver, the same calls can be made from R with [`reticulate`](https://cran.r-project.org/web/packages/reticulate/vignettes/calling_python.html).

**Spark, PySpark, Spark-R** — [Apache Spark](https://spark.apache.org/) is the distributed compute engine; it exposes that one engine through several language APIs that all compile to the same plan: Scala/Java (native), PySpark (Python), SparkR (R, used here), and Spark SQL. SparkR's `spark.glm` and PySpark's `pyspark.ml` both drive Spark MLlib on the JVM — which is why the Dataproc runtime's results match the others. On Dataproc Serverless the batch *type* selects the API (`spark_r_batch`, `pyspark_batch`, …). Note **SparkR** is Apache's R API, while [`sparklyr`](https://spark.posit.co/) is a separate dplyr-style R interface. A `spark.glm` model is a **Spark MLlib model** (saved via `write.ml()` to a directory, served on Spark) — distinct from the base-R `glm` `.rds` the other runtimes produce, even with identical coefficients.

</details>

---
## Getting BigQuery Data Into R

Pick by **size** and **table type**. Guiding principle: stay on the columnar stack (**Parquet** + **Arrow**) and the BigQuery clients — no `duckdb` middle layer, no CSV round-trip. The [R - Reading BigQuery Iceberg Tables](./R%20-%20Reading%20BigQuery%20Iceberg%20Tables.ipynb) notebook works through every row of this table.

| Data size / source | Approach | Package(s) |
|---|---|---|
| Small (< ~100 MB), standard table | `bq_table_download()` / `DBI::dbGetQuery()` / `dplyr::tbl()` | `bigrquery`, `DBI`, `dplyr` |
| Large, **standard** table or query result | `bq_table_download()` over the **Storage Read API** (Arrow; fast, parallel, no staging) | `bigrquery` + `bigrquerystorage` |
| Large, **Apache Iceberg** managed table | `arrow::open_dataset()` on the table's `/data` Parquet — lazy, multithreaded across shards, projection + predicate pushdown | `arrow` |
| *(legacy — avoid)* via export | `EXPORT DATA` → CSV in GCS → parallel read (superseded by the rows above) | `bigrquery`, `data.table` |

<details><summary>Why Iceberg + <code>arrow</code>, and why not <code>duckdb</code></summary>

A BigQuery [**Apache Iceberg managed table**](https://docs.cloud.google.com/bigquery/docs/biglake-iceberg-tables-in-bigquery) (formerly *BigLake tables for Apache Iceberg in BigQuery*) keeps its data as **Parquet** in *your own* GCS bucket — a `/data` folder of shards plus an Iceberg V2 snapshot in `/metadata`. Because the bytes are open Parquet, R reads them directly and in parallel with `arrow` (lazy scans, projection/predicate pushdown, `collect()` only the result), and the same files are readable by Spark and other Iceberg engines.

**Why not `duckdb` in the middle?** It works, but `arrow` already provides a `dplyr` backend with lazy evaluation, projection, and predicate pushdown straight over Parquet, and `bigrquerystorage` already returns Arrow batches from BigQuery — so the extra engine and data hop are unnecessary here.

</details>

---
## Serving R Models

Wrap `model.rds` in an HTTP API with [`plumber`](https://www.rplumber.co/) inside a custom `rocker/r-ver` container (meeting the [Vertex AI custom container contract](https://cloud.google.com/vertex-ai/docs/predictions/custom-container-requirements)); the *same* container deploys to a **Vertex AI Endpoint** or **Cloud Run**. The [R - Serving Predictions](./R%20-%20Serving%20Predictions.ipynb) notebook covers the R-specific packaging and cross-references the exhaustive [MLOps/Serving](../../MLOps/Serving/readme.md) section for deployment depth. A GLM can also be served SQL-natively with [BigQuery ML](../../MLOps/Serving/SQL%20Inference/readme.md) — no container required.

> **Tip — trim the model for serving.** An R `glm` stores a full copy of its training data, so the saved `.rds` is far larger than needed (~164 MB → ~55 MB for this GLM). Point predictions only need the coefficients, `terms`, `family`, and `qr` — so the Notebook Workflow (optional step) and the serving Dockerfile drop the data components.

---
## Related

- [data+ai/bq-iceberg](../../data%2Bai/bq-iceberg/readme.md) — sets up the native + Iceberg tables the reads notebook uses (prerequisite).
- [data+ai/overview/ml-training](../../data%2Bai/overview/ml-training/readme.md) — the same R runtimes shown alongside Python and other Google Cloud ML services.
- [MLOps/Serving](../../MLOps/Serving/readme.md) — comprehensive model serving (Online endpoints, Cloud Run, GKE, Batch, SQL/BQML).
