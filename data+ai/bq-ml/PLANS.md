<!--
This file is the operating manual for the bq-ml project. A fresh Claude session
should be able to read this file top-to-bottom and know how to add a new model,
function, workflow, or pipeline using the same conventions as every existing one.
It mirrors the structure of the sibling project data+ai/bq-ai-functions/PLANS.md.
-->

# BigQuery ML — Project Plan

## Vision

A hands-on, learn-by-running collection for **BigQuery ML**: training and using machine learning models entirely in SQL with `CREATE MODEL` and the `ML.*` functions. The audience is data practitioners who know SQL and want to do ML where their data already lives — no data movement, no separate training infrastructure.

This is the sibling project to **`../bq-ai-functions/`** (the BigQuery AI/Gemini functions). Where that project is organized **per function** (each function is independent), BigQuery ML is organized around a **model lifecycle**, so the primary unit of content is the **model type**.

Goals:
- One runnable, progressive example per model type, covering the full lifecycle
- Clear coverage of the model-free `ML.*` utility functions (preprocessing, transforms, distance, text)
- End-to-end workflows that compose these into real tasks
- Operationalization patterns (MLOps on BigQuery) via pipelines
- Reference docs (RESOURCES.md) and a map (README.md) kept in sync with the official documentation

---

## Content Architecture

Four top-level content directories. The **unit of content differs by directory** — this is the key design decision.

### 1. `models/` — Per-model-type lifecycle deep dives

One folder per model type. Each folder has `{name}.ipynb` + `{name}.sql`. The notebook walks the **full lifecycle**:

`CREATE MODEL` → `ML.EVALUATE` → (`ML.CONFUSION_MATRIX` / `ML.ROC_CURVE` / etc.) → `ML.PREDICT` (or `ML.FORECAST` / `ML.RECOMMEND`) → `ML.EXPLAIN_PREDICT` / `ML.GLOBAL_EXPLAIN` → `ML.FEATURE_INFO` / `ML.TRAINING_INFO` → hyperparameter tuning (`ML.TRIAL_INFO`)

Model **categories** (imported, remote, export) also live under `models/` because they are variations on how a model is created/stored, not separate concepts.

### 2. `functions/` — Model-free `ML.*` utilities

One folder per function, `{name}.ipynb` + `{name}.sql` — exactly the per-function style used in `bq-ai-functions/`. These are the `ML.*` functions that operate **directly on data without a model** (preprocessing, transforms, distance, text vectorization).

### 3. `workflows/` — Composed end-to-end SQL logic

One notebook per workflow. Combines preprocessing functions + a model lifecycle into a real task (e.g. churn classification end to end). **Workflows = what to do, in SQL (logic).**

### 4. `pipelines/` — Orchestration / MLOps

One folder per orchestration approach. Takes the SQL logic of a workflow and **operationalizes/schedules** it. **Pipelines = how to run it in production (orchestration).** Planned subfolders:
- `sql_scripting/` — multi-statement scripts, `BEGIN/END`, procedures
- `scheduled_queries/` — BigQuery scheduled queries for retrain/score
- `composer_airflow/` — Cloud Composer / Airflow DAGs
- `vertex_kfp/` — Vertex AI Pipelines (KFP)
- `airflow_with_kfp/` — Airflow triggering Vertex Pipelines (combined)

### Supporting files
- `README.md` — the landing-page map (tables + diagram + tree)
- `RESOURCES.md` — the deep per-item reference
- `setup/README.md` — one-stop setup reference (connections, IAM, CREATE MODEL deep dive, quotas, BigFrames)
- `overview.ipynb` — a short interactive tour (one example per category), grown as content is added

---

## Component Details

### Model `.sql` file (in `models/{name}/`)

Progressive, runnable SQL covering the lifecycle. Conventions:
- Header comment block: title, one-line description, the lifecycle order, the dataset used, and doc links
- Each example has a `-- ===` delimiter and a comment header explaining what it demonstrates
- Use placeholders `PROJECT_ID.DATASET` (notebooks substitute real values)
- Examples build up: create → evaluate → inspect → predict → explain → TRANSFORM → tune → cleanup (commented `DROP MODEL`)

### Model `.ipynb` notebook (in `models/{name}/`)

Cell sequence (canonical skeleton — see `models/logistic_regression/` as the reference):
1. **Header** — tracking-pixel + links table (cell 0). Copy from an existing notebook and replace the path/file segments (`bq-ml`, `models/{name}`, `{name}.ipynb`). Path is URL-encoded: `data%2Bai%2Fbq-ml%2Fmodels%2F{name}`.
2. **Overview** — title, a **Lifecycle:** line (the function chain), when-to-use bullets, the dataset, and a **References:** line. Add a **Featured in:** line if any workflow/pipeline uses the model.
3. **Setup** — markdown + config code (PROJECT_ID, LOCATION, DATASET_ID=`bq_ml`) + environment markdown + install code + auth code + client code (creates dataset, loads `bigquery_magics`).
4. **Step N — {lifecycle stage}** — one markdown + code pair per stage. Materialize models with `CREATE OR REPLACE MODEL`; show metrics, predictions, explanations, plots.
5. **Examples — `%%bigquery` Magics** — one representative call.
6. **Examples — BigFrames** — the `bigframes.ml` equivalent (these exist for most model types — e.g. `bigframes.ml.linear_model.LogisticRegression`).
7. **Cleanup** — drop the models created; a commented-out full-dataset-delete cell.

### Model-free function `.sql` / `.ipynb` (in `functions/{name}/`)

Same template as `bq-ai-functions/` function notebooks: header → overview (with **Featured in:**) → setup → progressive SQL examples → magics → BigFrames → cleanup.

### Workflow `.ipynb` (in `workflows/{name}/`)

Header → overview (with **Models used:** and **Functions used:** lines) → setup → Step-by-step (data → preprocess → train → evaluate → predict/explain) → interpretation → cleanup.

### Pipeline content (in `pipelines/{approach}/`)

A notebook and/or supporting files (DAG `.py`, KFP component specs) showing how to operationalize a workflow with that orchestrator. Include a **Workflow operationalized:** line linking back to the `workflows/` notebook it schedules.

---

## Sample Data Strategy

Examples must be self-contained and runnable. Prefer **BigQuery public datasets** — no data to load, realistic results.

- **Classification / regression:** `bigquery-public-data.ml_datasets.census_adult_income` (binary label `income_bracket`), `bigquery-public-data.ml_datasets.penguins` (multiclass/regression), `iris`.
- **Clustering:** `penguins`, or any feature-rich public table.
- **Time series:** `bigquery-public-data.new_york_citibike.citibike_trips`, `bigquery-public-data.google_analytics_sample.*`, or synthetic series generated with SQL (`GENERATE_DATE_ARRAY` + trend/seasonality). Cross-link to the TimesFM-based `AI.FORECAST` work in `bq-ai-functions/`.
- **Recommendation:** `bigquery-public-data.google_analytics_sample` or MovieLens-style public data.

**Standing practice (carried over from bq-ai-functions):** validate every SQL statement with `bq query` against the real dataset **before** writing it into a notebook cell. Training models in validation is fine (drop them afterward). This catches issues like option requirements (e.g. `enable_global_explain` must be set at `CREATE MODEL` time for `ML.GLOBAL_EXPLAIN`) before a notebook is handed off for Restart & Run All.

---

## Resource Naming Strategy

All notebooks share a single dataset and use `CREATE OR REPLACE` so running them in any order is safe.

### Config variables (every notebook)
```python
PROJECT_ID = 'your-project-id'
LOCATION = 'US'
DATASET_ID = 'bq_ml'          # Shared dataset (configurable, default: bq_ml)
CONNECTION_ID = 'bq_ml'        # Only notebooks that need one (remote/imported/export models)
```
Most BQML model types train on in-BigQuery data and need **no connection**. A connection is only required for **remote models** (Vertex endpoints), **imported models** (read artifacts from GCS), and **`EXPORT MODEL`** (write to GCS). Those notebooks add `CONNECTION_ID` and create the connection via the `bq` CLI (same pattern as bq-ai-functions, granting the connection SA the needed roles).

### Naming
- **Models / tables:** prefix with the content name, e.g. `logistic_regression_income`, `logistic_regression_income_tuned`, `kmeans_penguins`.
- **GCS (export/import):** `gs://BUCKET/bq_ml/{name}/`.
- All `CREATE OR REPLACE` — idempotent and safe to re-run.

### Cleanup
- **Per-notebook:** drop only the models/tables it created (`DROP MODEL IF EXISTS ...`). Leave the shared dataset.
- **Full:** a commented-out cell at the bottom of every notebook: `DROP SCHEMA \`PROJECT.bq_ml\` CASCADE;` (or `client.delete_dataset(..., delete_contents=True)`).

---

## Cross-Referencing Convention

Bidirectional links help users navigate. Maintain these whenever adding/updating content.

- **Model / function notebooks → consumers:** a **Featured in:** line in the overview cell listing the workflows/pipelines that use it.
- **Workflow / pipeline notebooks → components:** **Models used:** and **Functions used:** lines in the overview cell.
- **Mapping table** (below) records the current state.

### Current mapping

| Content | Type | Featured in |
|---------|------|-------------|
| logistic_regression | model | — (no workflows yet) |

(Update this table on every add. Workflows/functions/pipelines are not built yet — see Development Phases.)

---

## Development Phases

This is the **backlog** — a fresh session can pick the next unchecked item and build it using the templates above.

### Phase 1: Foundation (this bootstrap)
- [x] Folder skeleton (`models/`, `functions/`, `workflows/`, `pipelines/`, `setup/`)
- [x] PLANS.md (this operating manual)
- [x] RESOURCES.md (CREATE MODEL + lifecycle entries; full for logistic regression, stubs + doc links for the rest)
- [x] README.md + setup/README.md
- [x] **Canonical model: `models/logistic_regression/`** (full lifecycle, verified)
- [x] overview.ipynb stub
- [x] Memory entries

### Phase 2: Core supervised models
- [ ] `models/linear_regression/` (LINEAR_REG; regression metrics)
- [ ] `models/boosted_tree/` (BOOSTED_TREE_CLASSIFIER/REGRESSOR, XGBoost)
- [ ] `models/random_forest/` (RANDOM_FOREST_*)
- [ ] `models/dnn/` (DNN_CLASSIFIER/REGRESSOR) and/or wide-and-deep

### Phase 3: Unsupervised models
- [ ] `models/kmeans/` (KMEANS; `ML.CENTROIDS`, no label)
- [ ] `models/pca/` (PCA; `ML.PRINCIPAL_COMPONENTS`)
- [ ] `models/matrix_factorization/` (recommendation; `ML.RECOMMEND`)
- [ ] `models/autoencoder/` (AUTOENCODER; anomaly/embedding)

### Phase 4: Time series
- [ ] `models/arima_plus/` (ARIMA_PLUS; `ML.FORECAST`, `ML.EXPLAIN_FORECAST`) — cross-link to `bq-ai-functions` AI.FORECAST/TimesFM
- [ ] `models/arima_plus_xreg/` (with external regressors)

### Phase 5: Model categories
- [ ] `models/imported/` (TensorFlow, ONNX, XGBoost via `model_path` + connection)
- [ ] `models/remote/` (`REMOTE WITH CONNECTION` → Vertex AI endpoints) — cross-link to `bq-ai-functions` remote-model pattern (ML.GENERATE_TEXT etc.)
- [ ] `models/export/` (`EXPORT MODEL` to GCS; serve with TF Serving / Vertex)

### Phase 6: Model-free functions
- [ ] Preprocessing: `ML.STANDARD_SCALER`, `ML.MIN_MAX_SCALER`, `ML.MAX_ABS_SCALER`, `ML.ROBUST_SCALER`
- [ ] Bucketizing: `ML.BUCKETIZE`, `ML.QUANTILE_BUCKETIZE`
- [ ] Encoding: `ML.ONE_HOT_ENCODER`, `ML.LABEL_ENCODER`
- [ ] Feature engineering: `ML.FEATURE_CROSS`, `ML.POLYNOMIAL_EXPAND`, `ML.IMPUTER`
- [ ] Distance/vectors: `ML.DISTANCE`, `ML.LP_NORM`
- [ ] Text: `ML.NGRAMS`, `ML.TF_IDF`, `ML.BAG_OF_WORDS`
- [ ] Model-agnostic introspection: `ML.FEATURE_INFO`, `ML.TRAINING_INFO`, `ML.TRIAL_INFO` (also shown inline in model notebooks)

### Phase 7: Workflows
- [ ] End-to-end classification (preprocess → train → evaluate → predict → explain)
- [ ] Customer segmentation (kmeans + feature prep)
- [ ] Demand forecasting (arima_plus)
- [ ] Recommendation (matrix factorization)

### Phase 8: Pipelines (MLOps on BigQuery)
- [ ] `pipelines/sql_scripting/` (multi-statement train+score script / stored procedure)
- [ ] `pipelines/scheduled_queries/` (scheduled retrain + scheduled scoring)
- [ ] `pipelines/composer_airflow/` (Airflow DAG)
- [ ] `pipelines/vertex_kfp/` (Vertex AI Pipeline)
- [ ] `pipelines/airflow_with_kfp/` (Airflow triggering a Vertex Pipeline)

---

## Maintenance & Audit

Keep our content in sync with the official BigQuery ML documentation. Mirrors the bq-ai-functions audit discipline.

### Change types and checklists

#### New model type
- [ ] `RESOURCES.md`: Add a full entry in the CREATE MODEL catalog + the lifecycle functions it uses; update any comparison table
- [ ] `README.md`: Add a row to the Models table; update the diagram if needed
- [ ] Create `models/{name}/` with `{name}.ipynb` (full lifecycle template) + `{name}.sql` (progressive examples)
- [ ] Pre-validate all SQL with `bq query` (train + drop validation models)
- [ ] Cross-reference: add **Featured in:** if used by a workflow/pipeline
- [ ] `PLANS.md`: check the Development Phases item; update the mapping table; add an audit-log entry

#### New model-free function
- [ ] `RESOURCES.md`: Add a full entry in the Model-Free Functions section
- [ ] `README.md`: Add to the Functions table
- [ ] Create `functions/{name}/` with `{name}.ipynb` + `{name}.sql`
- [ ] Cross-reference + `PLANS.md` mapping + audit-log entry

#### New workflow
- [ ] Create `workflows/{name}/` notebook
- [ ] `README.md`: Add to the Workflows table
- [ ] Cross-reference: **Models used:** / **Functions used:** in the workflow; **Featured in:** on each component
- [ ] `PLANS.md`: mapping table + audit-log entry

#### New pipeline
- [ ] Create `pipelines/{approach}/` content
- [ ] `README.md`: Add to the Pipelines table
- [ ] Cross-reference: **Workflow operationalized:** link
- [ ] `PLANS.md`: mapping table + audit-log entry

#### Status / capability change (Preview→GA, new option, new model_type, etc.)
- [ ] Update `RESOURCES.md` entry (status, options, syntax, outputs, limitations)
- [ ] Update `README.md` status labels and tables
- [ ] If it affects a built notebook, revise + re-run (Restart & Run All) before review
- [ ] `PLANS.md`: audit-log entry

### How to run an audit
1. **Prepare** — review the audit log; note Google Cloud Next / release-note announcements since last audit.
2. **Fetch and compare by category** — for each documented item, fetch its doc URL (table below) and compare against `RESOURCES.md`: status, options/parameters, syntax, outputs, limitations, new `model_type` values, new `ML.*` functions.
3. **Classify each change** and apply the relevant checklist above.
4. **Update files in order:** RESOURCES.md entries → RESOURCES.md comparison tables → README.md tables/diagram → PLANS.md (URLs table, mapping, audit log).
5. **Check for new items** — new model types or `ML.*` functions. If docs exist, add full coverage; if only announced, add to Tracked-upcoming.
6. **Verify consistency** — grep status labels across RESOURCES/README/PLANS; confirm the URL table is complete.
7. **Identify notebook impacts** — list notebooks needing a fresh Restart & Run All.

### Documentation URLs

| Item | Documentation URL |
|------|-------------------|
| The CREATE MODEL statement | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create |
| CREATE MODEL (GLM: linear & logistic reg) | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-glm |
| CREATE MODEL (Boosted Tree) | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-boosted-tree |
| CREATE MODEL (Random Forest) | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-random-forest |
| CREATE MODEL (DNN) | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-dnn-models |
| CREATE MODEL (K-means) | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-kmeans |
| CREATE MODEL (PCA) | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-pca |
| CREATE MODEL (Matrix Factorization) | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-matrix-factorization |
| CREATE MODEL (ARIMA_PLUS) | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-time-series |
| CREATE MODEL (Autoencoder) | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-autoencoder |
| CREATE MODEL (Imported TF/ONNX/XGBoost) | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-tensorflow |
| CREATE MODEL (Remote) | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-remote-model |
| Hyperparameter tuning | https://cloud.google.com/bigquery/docs/hp-tuning-overview |
| ML.EVALUATE | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-evaluate |
| ML.PREDICT | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-predict |
| ML.FORECAST | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-forecast |
| ML.RECOMMEND | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-recommend |
| ML.EXPLAIN_PREDICT | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-explain-predict |
| ML.GLOBAL_EXPLAIN | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-global-explain |
| ML.CONFUSION_MATRIX | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-confusion |
| ML.ROC_CURVE | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-roc |
| ML.FEATURE_INFO | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-feature |
| ML.TRAINING_INFO | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-train |
| ML.TRIAL_INFO | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-trial-info |
| ML.TRANSFORM / preprocessing functions | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-preprocessing-functions |
| EXPORT MODEL | https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-export-model |
| BigFrames ML (bigframes.ml) | https://cloud.google.com/python/docs/reference/bigframes/latest/bigframes.ml |

### Tracked upcoming

Items announced but without published reference docs, or not yet covered. Move to full coverage when ready.

| Item | Category | Status | Notes |
|------|----------|--------|-------|
| (none yet) | | | |

### Audit log

| Date | Scope | Changes |
|------|-------|---------|
| 2026-06-19 | Project bootstrap | Created the bq-ml project parallel to bq-ai-functions: folder skeleton (models/functions/workflows/pipelines/setup), PLANS.md operating manual, RESOURCES.md (CREATE MODEL catalog + lifecycle/model-free/management sections; full entries for logistic regression and the functions it uses, stubs + doc links for the rest), README.md map, setup/README.md. Built the canonical reference model `models/logistic_regression/` (notebook + SQL) on `census_adult_income`, covering CREATE MODEL → ML.EVALUATE → confusion matrix/ROC → ML.PREDICT → ML.EXPLAIN_PREDICT → ML.GLOBAL_EXPLAIN → ML.FEATURE_INFO/TRAINING_INFO → TRANSFORM clause → hyperparameter tuning (ML.TRIAL_INFO) → magics → BigFrames → cleanup. All SQL pre-validated against BigQuery (caught: ML.GLOBAL_EXPLAIN requires enable_global_explain=TRUE at CREATE MODEL time). Backlog for all other models/functions/workflows/pipelines recorded in Development Phases. |
