![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Fdata%2Bai&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/data%2Bai/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/readme.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/readme.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# Data + AI

Resources for machine learning and AI across Google Cloud data services — data access, model serving, BigQuery AI functions, and database integrations.

## Contents

- **[Overview](overview/)** — Broad, cross-service overviews of Google Cloud's data and AI capabilities. Starts with [ML Training & Batch Inference](overview/ml-training/) — standalone notebooks comparing BigQuery ML, BigFrames, Dataproc Serverless, Vertex AI Training, Colab Enterprise, Model Registry, and KFP orchestration on a shared dataset.

- **[Tabular Data](tabular-data/)** — Reading tabular data efficiently for ML workflows. Compares BigQuery read approaches (query, Storage Read API, BigFrames, pandas-gbq) by cost and speed, with multi-threaded benchmarks.

- **[BigQuery Iceberg](bq-iceberg/)** — Set up a large Apache Iceberg managed table (Parquet shards in your own GCS bucket) from the Chicago Taxi public dataset, read it from Python (BigFrames + Storage Read API). Prerequisite for the R reads notebook, which reads it at scale — including multithreaded `arrow` reads parallelized across the many Parquet files.

- **[Model Serving / Inference](model-serving.md)** — Training and deploying custom ML models across Google Cloud: PyTorch serving on Vertex AI endpoints, BigQuery ML, AlloyDB, Spanner, Dataflow RunInference, TorchServe, and GPU inference benchmarks.

- **[BigQuery ML](bq-ml/)** — A learning resource for training and serving machine learning models directly in BigQuery with SQL: 16 model types (classification, regression, unsupervised/specialized), model-free `ML.*` functions, end-to-end workflows, and 8 production orchestration pipelines.

- **[BigQuery AI Functions](bq-ai-functions/)** — A learning resource for BigQuery's built-in AI functions: 20 functions, 8 multi-function workflows, 30+ notebooks, and 100 synthetic PDFs for hands-on examples.

- **[BigQuery Solutions](bq-solutions/)** — BigQuery solution patterns: continuous queries with GA4 data for real-time funnel analytics, traffic anomaly detection, and conversion monitoring.

- **[Dataflow](dataflow/)** — Dataflow streaming ML pipelines: GPU inference benchmarks comparing Local GPU vs Vertex AI Endpoint approaches, event-mode and watch-mode model hot-swap examples, and a Python-to-Java translation guide for multi-language RunInference pipelines.

- **[Dataproc (Managed Service for Apache Spark)](dataproc/)** — Spark ML inference on Dataproc: batch inference with Pandas UDFs, Structured Streaming with foreachBatch, calling Vertex AI Endpoints from Spark, and Dataproc Serverless fundamentals.

- **[Cloud Composer (Managed Service for Apache Airflow)](composer/)** — Orchestrating ML batch inference with Cloud Composer: four patterns covering Airflow → Dataproc, Dataflow, KFP, and Vertex AI Batch Prediction, plus production scheduling, backfill, and retry.

- **[AlloyDB](alloydb/)** — ML inference with AlloyDB AI using `ML.PREDICT()` to call Vertex AI Endpoints for SQL-based predictions.

- **[Spanner](spanner/)** — ML inference with Spanner ML using `ML.PREDICT()` to call Vertex AI Endpoints for SQL-based predictions.

- **[Google Cloud Databases](gcp-databases.md)** — Overview of Google Cloud's managed database portfolio (BigQuery, Cloud SQL, AlloyDB, Spanner, Bigtable, Firestore, Memorystore) and their AI/ML integration capabilities.

## Agent Skills

[`bq-ml`](bq-ml/) and [`bq-ai-functions`](bq-ai-functions/) are the source for a growing collection of packaged **Agent Skills**, centralized in [`agent-skills/`](../agent-skills/) at the repo root — use-case-organized, verified-gotcha references (plus extracted notebook narratives) distilled for AI coding agents rather than human readers. A third skill sits above both and triages which one fits a given task, including worked head-to-head comparisons already resolved in this project (e.g. `ARIMA_PLUS` vs. `AI.FORECAST`, `CONTRIBUTION_ANALYSIS` vs. `AI.KEY_DRIVERS`).

| Skill | Scope | Path |
|---|---|---|
| [`bigquery-ml`](../agent-skills/.agents/skills/bigquery-ml/SKILL.md) | Training, evaluating, deploying, and monitoring BigQuery ML models | `agent-skills/.agents/skills/bigquery-ml/` |
| [`bigquery-ai-functions`](../agent-skills/.agents/skills/bigquery-ai-functions/SKILL.md) | Calling Gemini / generative AI functions from SQL | `agent-skills/.agents/skills/bigquery-ai-functions/` |
| [`choosing-a-bigquery-ai-approach`](../agent-skills/.agents/skills/choosing-a-bigquery-ai-approach/SKILL.md) | Picking between the two above when it's unclear which fits | `agent-skills/.agents/skills/choosing-a-bigquery-ai-approach/` |

See [`agent-skills/README.md`](../agent-skills/README.md) for the full catalog, the authoring standard, and the backlog of skills planned from the rest of this repo's MLOps content.

**How to use them, by tool:**
- **Claude Code** — auto-discovered from the repo-root `.claude/skills/` (per-skill symlinks into `agent-skills/`) anywhere in this repo; no setup required. Each skill activates automatically when a request matches its description, or can be invoked explicitly.
- **Google Antigravity, Codex, and other tools that support the `SKILL.md` format** — discovered from the repo-root `.agents/skills/` symlinks, the shared convention those tools use for project skills.
- **Outside this repo** — every skill folder is self-contained (bundled reference content, no dependency on the rest of the repo to be useful). Copy an `agent-skills/.agents/skills/<name>/` folder into any other project and it still works standalone.
