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

A comprehensive, R-first guide to running [**R**](https://www.r-project.org/) on Google Cloud: **where R runs** (interactive environments and managed runtimes), **how to get data from BigQuery into R** at any size, and **how to serve** an R model.

The series is built around **one shared workflow** run across multiple runtimes, so you can compare them for your own work — the same philosophy as the [ml-training comparison series](../../data%2Bai/overview/ml-training/readme.md), but R-kernel and R-idiom throughout.

**Contents**
- [Environment Setup](#environment-setup)
- [The Shared Workflow](#the-shared-workflow)
- [Part 1: Where R Runs — Environments & Runtimes](#part-1-where-r-runs--environments--runtimes)
- [Part 2: Getting BigQuery Data Into R](#part-2-getting-bigquery-data-into-r)
- [Part 3: Serving R Models](#part-3-serving-r-models)
- [Notebooks In This Folder](#notebooks-in-this-folder)

---
## Environment Setup

This folder has **two kinds of notebooks**, with two kinds of kernels:

- **R-kernel notebooks** — [R - Notebook Workflow](./R%20-%20Notebook%20Workflow.ipynb) and [R - Reading BigQuery Iceberg Tables](./R%20-%20Reading%20BigQuery%20Iceberg%20Tables.ipynb). These run on an **R** kernel. On a Vertex AI Workbench Instance, add R with a conda environment (see [Part 1](#interactive-environments)): `conda create -n r && conda activate r && conda install -c r r-essentials && conda install -c conda-forge r-bigrquery r-bigrquerystorage r-arrow r-dbi r-dplyr`, then pick the **R (Local)** kernel.
- **Python-driver notebooks** — [R - Vertex AI Custom Training Job](./R%20-%20Vertex%20AI%20Custom%20Training%20Job.ipynb), [R - Dataproc Serverless Spark-R](./R%20-%20Dataproc%20Serverless%20Spark-R.ipynb), [R - Vertex AI Pipelines](./R%20-%20Vertex%20AI%20Pipelines.ipynb), and [R - Serving Predictions](./R%20-%20Serving%20Predictions.ipynb). These use a **Python** kernel for the Vertex AI / Dataproc / KFP SDKs (the R code runs remotely in a container). Set up a Python environment for them as below.

### Python environment (for the Python-driver notebooks)

Set up a virtual environment with [uv](https://docs.astral.sh/uv/):

```bash
cd "Framework Workflows/R"
uv sync --group dev
```

This installs the project dependencies and `ipykernel` (dev group). Register the environment as a Jupyter kernel:

```bash
uv run python -m ipykernel install --user --name r-on-gcp --display-name "Python (r-on-gcp)"
```

Then select the `Python (r-on-gcp)` kernel when opening a Python-driver notebook.

**Alternative — pip:**

```bash
cd "Framework Workflows/R"
python -m venv .venv && source .venv/bin/activate
pip install -e . ipykernel
python -m ipykernel install --user --name r-on-gcp --display-name "Python (r-on-gcp)"
```

> **Running on Colab, Colab Enterprise, or Vertex AI Workbench?** The Python-driver notebooks include an install cell that handles packages automatically — no local setup needed.

---
## The Shared Workflow

Every runtime notebook runs the *same* task so the only thing that changes is the execution environment:

> A logistic-regression fraud-detection **GLM** (`glm(..., family = binomial)`) on `bigquery-public-data.ml_datasets.ulb_fraud_detection` (284,807 credit-card transactions; PCA features `V1..V28` plus `Time` and `Amount`; target `Class`).

The workflow is factored into a single script, [`code/train.R`](./code/train.R) — read the `TRAIN`/`TEST` splits → fit the GLM → evaluate (confusion matrix) → `saveRDS`. The interactive notebook walks the same steps cell-by-cell; the SparkR runtime uses the distributed [`code/sparkr.R`](./code/sparkr.R). Data prep (adding `transaction_id` + `splits`) is done once in BigQuery into a `*_prepped` table so the same logic is reproducible at serving time.

All reads use the modern columnar stack — **Parquet** on disk, **Arrow** in memory — via the BigQuery Storage Read API or `arrow`, never a CSV export (see [Part 2](#part-2-getting-bigquery-data-into-r)).

---
## Part 1: Where R Runs — Environments & Runtimes

### Interactive Environments

- **Vertex AI Workbench Instances** (used throughout this repo) — JupyterLab notebooks. Add R by [creating a conda environment](https://cloud.google.com/vertex-ai/docs/workbench/instances/add-environment): `conda create -n r`, then `conda install -c r r-essentials` and add packages such as `conda install -c conda-forge r-bigrquery r-bigrquerystorage r-arrow`. Start an R notebook/console with the **R (Local)** kernel.
- **Cloud Workstations** — managed dev environments where a configuration can use [**Posit Workbench (RStudio Pro)**](https://cloud.google.com/workstations/docs/develop-code-using-posit-workbench-rstudio) as the IDE, or a custom container. Connect from local VS Code / JetBrains too.
- **BigQuery Studio / Colab Enterprise** — notebook surfaces that can run R and execute notebooks programmatically.

### Runtime Comparison — One Workflow, Many Runtimes

Each notebook runs the shared GLM workflow on a different runtime:

| Runtime | Notebook | Kernel | When to use |
|---|---|---|---|
| **Interactive notebook** | [R - Notebook Workflow](./R%20-%20Notebook%20Workflow.ipynb) | R | Develop & run end-to-end live; the starting point |
| **Vertex AI Custom Training Job** | [R - Vertex AI Custom Training Job](./R%20-%20Vertex%20AI%20Custom%20Training%20Job.ipynb) | Python (SDK) | Scale up data/compute as a managed job; schedule/trigger; pay per run |
| **Dataproc Serverless Spark-R** | [R - Dataproc Serverless Spark-R](./R%20-%20Dataproc%20Serverless%20Spark-R.ipynb) | Python (API) | Data outgrows one machine; distributed read + `spark.glm` |
| **Vertex AI Pipelines (KFP)** | [R - Vertex AI Pipelines](./R%20-%20Vertex%20AI%20Pipelines.ipynb) | Python (KFP) | Orchestrated, reproducible R steps in an MLOps DAG — two code-delivery patterns (code-as-input vs. baked image), run solo then in one pipeline |

> **Containers:** the job runtimes build a **custom R container** from the community [`rocker/r-ver`](https://rocker-project.org/images/versioned/r-ver.html) base via Cloud Build. Vertex AI's prebuilt `r-cpu` deep-learning images still work but are on a deprecation path, so this series does not depend on them. Two things the base image needs added: `libprotobuf-dev` + `libgrpc++-dev` (runtime deps of `bigrquerystorage` — without them the Storage Read API fast path silently falls back to REST), and writing model output via the **Cloud Storage FUSE mount** (`AIP_MODEL_DIR` → `/gcs/...`) rather than `gcloud`/`gsutil`, which `rocker/r-ver` does not ship.
>
> **R vs. Python kernel:** the job-launch notebooks use a Python kernel for the Vertex AI / Dataproc SDKs. For an all-R driver, the same calls can be made from R with [`reticulate`](https://cran.r-project.org/web/packages/reticulate/vignettes/calling_python.html).
>
> **Spark, PySpark, Spark-R:** [Apache Spark](https://spark.apache.org/) is the distributed compute *engine* (a Scala/JVM core that splits data and work across executors). It exposes that one engine through several **language APIs** that all compile to the same execution plan: **Scala/Java** (native), **PySpark** (Python), **SparkR** (R — used in this series, ships with Spark), and **Spark SQL**. So PySpark and SparkR are *siblings* — different front-ends over the same engine; SparkR's `spark.glm` and PySpark's `pyspark.ml` logistic regression both drive Spark MLlib on the JVM, which is why the Dataproc runtime's results match the others. On **Dataproc Serverless** the batch *type* selects the API (`spark_r_batch`, `pyspark_batch`, `spark_batch`, `spark_sql_batch`). Note that **SparkR** is Apache's R API, whereas [`sparklyr`](https://spark.posit.co/) is a separate dplyr-style R interface to the same engine. A model from `spark.glm` is a **Spark MLlib model** (saved with `write.ml()` to a directory, served on Spark) — distinct from the base-R `glm` `.rds` the other runtimes produce, even though the coefficients are identical.
>
> **Cross-reference:** for these same R runtimes shown side-by-side with Python/other services, see [data+ai/overview/ml-training](../../data%2Bai/overview/ml-training/readme.md).

---
## Part 2: Getting BigQuery Data Into R

The right way to pull BigQuery data into R depends on **size** and **table type**. The guiding principle: stay on the columnar stack — **Parquet** on disk, **Arrow** in memory — and the BigQuery clients, with **no `duckdb` middle layer** and no CSV round-trip.

### Decision Matrix

| Data size / source | Recommended approach | Package(s) | Notes |
|---|---|---|---|
| Small (< ~100 MB), standard table | `bq_table_download()`, `DBI::dbGetQuery()`, or `dplyr::tbl()` | `bigrquery`, `DBI`, `dplyr` | Simplest; REST/JSON path |
| Large, **standard** BigQuery table or query result | `bq_table_download()` with the **Storage Read API** | `bigrquery` + `bigrquerystorage` | Auto-uses Arrow when `bigrquerystorage` is installed; fast & parallel; no GCS staging |
| Large, **Apache Iceberg** managed table | `arrow::open_dataset()` on the table's `/data` Parquet | `arrow` | Direct, lazy, **multithreaded across the table's many Parquet shards**; column projection + predicate pushdown |
| *(legacy — avoid)* Any size, via export | `EXPORT DATA` to CSV in GCS → parallel read | `bigrquery`, `data.table`/`purrr` | Superseded by the Storage Read API and Iceberg/`arrow` paths above |

### Why Iceberg + `arrow`

A BigQuery [**Apache Iceberg managed table**](https://docs.cloud.google.com/bigquery/docs/biglake-iceberg-tables-in-bigquery) (formerly *BigLake tables for Apache Iceberg in BigQuery*) keeps its data as **Parquet** files in *your own* Cloud Storage bucket — a `/data` folder of Parquet shards plus an Iceberg V2 snapshot in `/metadata`. Because the bytes are already columnar Parquet, R reads them **directly and in parallel** with `arrow`: lazy scans, push down the columns and filters you need, and `collect()` only the result. The same files are simultaneously readable by Spark and other Iceberg engines — an open-format lakehouse table.

**Why not `duckdb` in the middle?** A common R pattern reads Parquet through `duckdb` and exposes it to `dplyr`. It works, but `arrow` already provides a `dplyr` backend with lazy evaluation, projection, and predicate pushdown straight over Parquet, and `bigrquerystorage` already returns Arrow batches from BigQuery — so the extra engine and data hop are unnecessary here.

➡️ Worked example: **[R - Reading BigQuery Iceberg Tables](./R%20-%20Reading%20BigQuery%20Iceberg%20Tables.ipynb)** — reads a BigQuery **native** table and an **Apache Iceberg managed table** across patterns from small to large: classic `bigrquery`, the Storage Read API, and multithreaded `arrow` directly on the Iceberg `/data` Parquet. Table setup is the prerequisite Python notebook **[`data+ai/bq-iceberg`](../../data%2Bai/bq-iceberg/readme.md)**.

---
## Part 3: Serving R Models

An R model (`model.rds`) is served by wrapping it in an HTTP API with [`plumber`](https://www.rplumber.co/) inside a custom `rocker/r-ver` container that satisfies the [Vertex AI custom container contract](https://cloud.google.com/vertex-ai/docs/predictions/custom-container-requirements). The *same* container deploys to a **Vertex AI Endpoint** or **Cloud Run**.

This series covers the **R-specific** part — packaging the `.rds` behind `plumber` — and cross-references the repo's exhaustive [MLOps/Serving](../../MLOps/Serving/readme.md) section for deployment depth (endpoint types, autoscaling, traffic splitting, Cloud Run, batch). A GLM can also be served SQL-natively with [BigQuery ML](../../MLOps/Serving/SQL%20Inference/readme.md) — no container required.

> **Tip — trim the model for serving.** An R `glm` stores a full copy of its training data, so the saved `.rds` is much larger than the model needs to be (~164 MB → ~55 MB for this GLM). Point predictions only need the coefficients, `terms`, `family`, and `qr`, so both [R - Notebook Workflow](./R%20-%20Notebook%20Workflow.ipynb) (optional save step) and the serving Dockerfile drop the data components — keeping the container image and its memory footprint small.

➡️ **[R - Serving Predictions](./R%20-%20Serving%20Predictions.ipynb)**

---
## Notebooks In This Folder

**Data access**
- **[R - Reading BigQuery Iceberg Tables](./R%20-%20Reading%20BigQuery%20Iceberg%20Tables.ipynb)** — read a native table and an Apache Iceberg managed table from small to large: `bigrquery`, the Storage Read API, and multithreaded `arrow` on the Iceberg Parquet. No CSV, no `duckdb`. Requires the [`data+ai/bq-iceberg`](../../data%2Bai/bq-iceberg/readme.md) setup notebook.

**The shared workflow across runtimes**
- **[R - Notebook Workflow](./R%20-%20Notebook%20Workflow.ipynb)** — the GLM end-to-end in an interactive R kernel.
- **[R - Vertex AI Custom Training Job](./R%20-%20Vertex%20AI%20Custom%20Training%20Job.ipynb)** — same workflow as a managed CustomJob in a custom R container.
- **[R - Dataproc Serverless Spark-R](./R%20-%20Dataproc%20Serverless%20Spark-R.ipynb)** — distributed version with SparkR on serverless Spark.
- **[R - Vertex AI Pipelines](./R%20-%20Vertex%20AI%20Pipelines.ipynb)** — the workflow as a containerized KFP component, taught two ways (code passed as a pipeline input vs. code baked into the image) and then combined into one pipeline that runs both branches in parallel.

**Serving**
- **[R - Serving Predictions](./R%20-%20Serving%20Predictions.ipynb)** — package `model.rds` behind `plumber`; deploy and run online predictions on both a Vertex AI Endpoint and Cloud Run.

**Shared code**
- [`code/train.R`](./code/train.R) — the shared GLM workflow script. · [`code/sparkr.R`](./code/sparkr.R) — the SparkR variant.

### Related Content Elsewhere In This Repo
- [data+ai/overview/ml-training](../../data%2Bai/overview/ml-training/readme.md) — the same R runtimes shown alongside Python and other Google Cloud ML services for comparison.
- [MLOps/Serving](../../MLOps/Serving/readme.md) — comprehensive model serving (Online endpoints, Cloud Run, GKE, Batch, SQL/BQML).
