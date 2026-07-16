![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Fdata%2Bai%2Fbq-ml%2Fsetup&file=README.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/data%2Bai/bq-ml/setup/README.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ml/setup/README.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ml/setup/README.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ml/setup/README.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ml/setup/README.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-ml/setup/README.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-ml/setup/README.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# Setup Reference

Everything you need to run the BigQuery ML notebooks. Most model types need only a project, a dataset, and your own credentials — connections are the exception, not the rule.

## Table of Contents
- [Python Environment](#python-environment)
- [Project, Dataset, and Credentials](#project-dataset-and-credentials)
- [The CREATE MODEL Statement](#the-create-model-statement)
- [Hyperparameter Tuning](#hyperparameter-tuning)
- [Connections (remote / imported / export only)](#connections-remote--imported--export-only)
- [Permissions (IAM)](#permissions-iam)
- [Quotas and Pricing](#quotas-and-pricing)
- [BigFrames (bigframes.ml)](#bigframes-bigframesml)

---

## Python Environment

Each notebook installs its own dependencies inline, so you can run any notebook standalone in Colab, Colab Enterprise, or Vertex AI Workbench with no prior setup.

If you're working locally (VSCode, JupyterLab) or want a pre-configured environment, use `uv` to set up once:

### Local setup with `uv`

```bash
# From the project root (bq-ml/)
uv sync --group dev
```

This creates a `.venv` with all packages needed across every notebook. To use it as a Jupyter kernel:

```bash
uv run python -m ipykernel install --user --name bq-ml --display-name "BQ ML"
```

Then select the **BQ ML** kernel in your notebook editor.

### How notebooks handle dependencies

Every notebook includes an install cell near the top, with a `uv` fast-path and a `pip` fallback:

```python
import subprocess, sys, shutil
def install(*packages):
    """Install packages using uv (fast) with pip fallback."""
    uv = shutil.which('uv')
    if uv:
        subprocess.check_call([uv, 'pip', 'install', '-q', '--python', sys.executable, *packages])
    else:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', '--upgrade', *packages])
install('google-cloud-bigquery', 'db-dtypes', 'bigquery-magics', 'bigframes', 'matplotlib')
```

- Uses `uv` when available (faster installs), falls back to `pip`
- Targets `sys.executable` so packages go into the active kernel's environment
- If you set up the local environment above, this cell is a fast no-op

**Packages used across notebooks:** `google-cloud-bigquery` (client), `db-dtypes` (BigQuery↔pandas types), `bigquery-magics` (`%%bigquery`), `bigframes` (`bigframes.ml`), `matplotlib` (plots). In a managed environment (Colab, Colab Enterprise, Vertex AI Workbench) these are usually present, so the install is effectively a no-op.

---

## Project, Dataset, and Credentials

Every notebook starts with the same config:

```python
PROJECT_ID = 'your-project-id'
LOCATION = 'US'
DATASET_ID = 'bq_ml'          # Shared dataset, created idempotently
CONNECTION_ID = 'bq_ml'        # Only for remote/imported/export model notebooks
```

The dataset is created with `client.create_dataset(..., exists_ok=True)`. Models and tables are created with `CREATE OR REPLACE`, so notebooks are safe to run in any order and re-run freely.

**Credentials:** in Colab, `google.colab.auth.authenticate_user()`; elsewhere, Application Default Credentials (`gcloud auth application-default login`). Standard BigQuery ML training and `ML.*` calls use **your** credentials — no service account or connection needed.

---

## The CREATE MODEL Statement

The heart of BigQuery ML. Train a model and store it in your dataset:

```sql
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.MODEL_NAME`
[TRANSFORM (...)]              -- optional in-model preprocessing
OPTIONS (
  model_type = 'LOGISTIC_REG',
  input_label_cols = ['label'],
  ...
) AS
SELECT ... FROM `source_table`;
```

- **`model_type`** picks the algorithm — see the catalog in [RESOURCES.md](../RESOURCES.md#create-model).
- **`input_label_cols`** names the target for supervised models.
- **`data_split_method`** (default `AUTO_SPLIT`) holds out an evaluation set automatically, so `ML.EVALUATE` works with no extra data.
- **`enable_global_explain = TRUE`** is required at training time if you want `ML.GLOBAL_EXPLAIN` later.
- **`TRANSFORM`** bakes preprocessing into the model so it's reapplied automatically at predict time (raw input to `ML.PREDICT`).

Training is **synchronous** from the client's perspective — `client.query(...).result()` returns when the model is ready (seconds to minutes depending on data/algorithm).

---

## Hyperparameter Tuning

BigQuery ML tunes hyperparameters natively — no external tuning service:

```sql
CREATE OR REPLACE MODEL `...`
OPTIONS(
  model_type = 'LOGISTIC_REG',
  input_label_cols = ['label'],
  num_trials = 10,                       -- enables tuning
  max_parallel_trials = 2,
  hparam_tuning_objectives = ['roc_auc'],
  l1_reg = HPARAM_RANGE(0, 1),           -- searchable option
  l2_reg = HPARAM_RANGE(0, 1)
) AS SELECT ...;
```

Inspect trials with `ML.TRIAL_INFO` (`trial_id`, `hyperparameters`, `hparam_tuning_evaluation_metrics.*`, `is_optimal`). [HP tuning overview](https://cloud.google.com/bigquery/docs/hp-tuning-overview).

---

## Connections (remote / imported / export only)

A **Cloud resource connection** is only needed for:
- **Remote models** — `CREATE MODEL ... REMOTE WITH CONNECTION ...` calling a Vertex AI endpoint.
- **Imported models** — reading TF/ONNX/XGBoost artifacts from `gs://...`.
- **`EXPORT MODEL`** — writing a model to GCS.

Standard in-BigQuery training (logistic regression, k-means, ARIMA_PLUS, etc.) needs **none** of this.

Create one idempotently via the `bq` CLI and grant its service account the needed role(s):

```python
import subprocess, json
subprocess.run(['bq', 'mk', '--connection', '--location', LOCATION,
                '--connection_type', 'CLOUD_RESOURCE',
                '--project_id', PROJECT_ID, CONNECTION_ID],
               capture_output=True, text=True)
r = subprocess.run(['bq', 'show', '--connection', '--format=json',
                    '--project_id', PROJECT_ID, '--location', LOCATION, CONNECTION_ID],
                   capture_output=True, text=True, check=True)
sa = json.loads(r.stdout)['cloudResource']['serviceAccountId']
# Remote models: roles/aiplatform.user ; GCS import/export: roles/storage.objectAdmin (or objectViewer)
subprocess.run(['gcloud', 'projects', 'add-iam-policy-binding', PROJECT_ID,
                f'--member=serviceAccount:{sa}', '--role=roles/aiplatform.user', '--quiet'],
               capture_output=True, text=True)
```

In SQL the connection is referenced as `PROJECT_ID.LOCATION.CONNECTION_ID`.

---

## Permissions (IAM)

- **Standard training + ML.* calls (your credentials):** `roles/bigquery.user` (run jobs) + `roles/bigquery.dataEditor` on the dataset (create models/tables) + read access to the source data (public datasets are world-readable).
- **Remote models:** the *connection's* service account needs `roles/aiplatform.user`.
- **Imported / exported models:** the connection's SA needs GCS access (`roles/storage.objectViewer` to import, `roles/storage.objectAdmin` to export).

---

## Quotas and Pricing

- **Training** is billed by bytes processed (on-demand) or by slots (editions/reservations). Iterative models and hyperparameter tuning process the data multiple times — tuning cost scales with `num_trials`.
- **`ML.PREDICT` / `ML.EVALUATE`** are billed like normal queries (bytes scanned).
- Public datasets used in these notebooks are small; costs for the examples are minimal. See [BigQuery ML pricing](https://cloud.google.com/bigquery/pricing#bqml).

---

## BigFrames (bigframes.ml)

BigFrames offers a scikit-learn-style Python API that creates BigQuery ML models under the hood:

```python
import bigframes.pandas as bpd
from bigframes.ml.linear_model import LogisticRegression

bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION

df = bpd.read_gbq('bigquery-public-data.ml_datasets.census_adult_income')
model = LogisticRegression(auto_class_weights=True)
model.fit(df[feature_cols], df['income_bracket'])
model.score(df[feature_cols], df['income_bracket']).to_pandas()
```

Each model notebook includes a BigFrames section mirroring its SQL workflow. [bigframes.ml reference](https://cloud.google.com/python/docs/reference/bigframes/latest/bigframes.ml).
