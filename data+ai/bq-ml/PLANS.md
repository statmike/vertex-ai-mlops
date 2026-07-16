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
6. **Examples — BigFrames** — the `bigframes.ml` equivalent (these exist for most model types — e.g. `bigframes.ml.linear_model.LogisticRegression`). **Check parity with the SQL model's options before writing this cell** (e.g. class weighting) — don't assume the BigFrames constructor exposes every `CREATE MODEL` option; verify against the actual installed signature (`inspect.signature(...)`) rather than guessing a parameter name. If no equivalent exists, say so in the markdown rather than silently presenting a mismatched comparison (see `models/boosted_tree_classifier/`: `bigframes.ml.ensemble.XGBClassifier` has no `class_weight` param, unlike `LogisticRegression`).
7. **Cleanup** — drop the models created; a commented-out full-dataset-delete cell. If the notebook exported anything to GCS (tree visualization, etc.), delete those blobs too.

**Convention (decided 2026-06-20, `models/boosted_tree_classifier/`) — visualizing tree-ensemble models:** for any `BOOSTED_TREE_*` / `RANDOM_FOREST_*` notebook, add a step that exports the model (`EXPORT MODEL`) and renders an individual tree with `xgboost.plot_tree()`. Requires a `BUCKET` config variable (alongside `PROJECT_ID`/`LOCATION`/`DATASET_ID`) in the same location as the dataset. Two verified gotchas that MUST be called out in the notebook, not just assumed away:
1. **Pin `xgboost==1.7.6`** (or another pre-2.0 release) in that step's `install()` call — modern xgboost (2.0+) cannot load BQML's exported legacy-binary-format `model.bst`.
2. **Manually reassign `booster.feature_names`** to the training query's non-label `SELECT` column order — the export does not preserve them (`feature_names` loads as `None`).

Rendering also needs the system `graphviz` package (`dot` binary) — pre-installed in Colab; elsewhere `!apt-get install -y graphviz`. Full details in RESOURCES.md's `EXPORT MODEL` entry.

**`RANDOM_FOREST_*`-specific addendum (decided 2026-06-21, `models/random_forest_classifier/`):** do NOT try to render a tree from the notebook's main (full-power) model — verified that a default-settings forest's tree is far too dense (thousands of dump lines, depth 15+) and produces an illegible `xgboost.plot_tree()` image (confirmed even with SVG output). Instead, train a small, separate **illustrative forest** (e.g. `num_parallel_tree=10`, `max_tree_depth=3`) just for the visualization step, clearly labeled as such in the markdown, and drop it in cleanup alongside the other models. This does not apply to `BOOSTED_TREE_*` — its early-round trees are shallow (residual-fitting stages) and render cleanly by default.

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
CONNECTION_ID = 'bq_ml'        # Only notebooks that need one (remote/imported models)
BUCKET = 'your-bucket-name'    # Only notebooks that use EXPORT MODEL (e.g. tree visualization) -- same location as DATASET_ID
```
Most BQML model types train on in-BigQuery data and need **no connection**. A connection is only required for **remote models** (Vertex endpoints) and **imported models** (read artifacts from GCS). Those notebooks add `CONNECTION_ID` and create the connection via the `bq` CLI (same pattern as bq-ai-functions, granting the connection SA the needed roles).

**Verified: `EXPORT MODEL` does NOT need a connection** — it only needs GCS write IAM on the credentials running the query (confirmed by testing an export against a `US-CENTRAL1` bucket from a `US` multi-region dataset with no connection object at all). Notebooks that call `EXPORT MODEL` (e.g. tree visualization) add `BUCKET` instead of `CONNECTION_ID`.

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
| linear_regression | model | — (no workflows yet) |
| boosted_tree_classifier | model | — (no workflows yet) |
| boosted_tree_regressor | model | — (no workflows yet) |
| random_forest_classifier | model | — (no workflows yet) |
| random_forest_regressor | model | — (no workflows yet) |

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

**Convention (decided 2026-06-20):** when a technique pairs a classifier and a regressor `model_type` (boosted tree, random forest, DNN, wide-and-deep), build **separate folders/notebooks per `model_type`** — mirroring the `models/logistic_regression/` + `models/linear_regression/` precedent — rather than one combined notebook per technique. Each notebook stays tightly focused and matches the canonical skeleton exactly; RESOURCES.md can still document the pair under one combined heading (as it already does for GLM). Folder names follow the `model_type` lowercased (e.g. `BOOSTED_TREE_CLASSIFIER` → `models/boosted_tree_classifier/`).

- [x] `models/linear_regression/` (LINEAR_REG; regression metrics) — built 2026-06-20, `penguins`/`body_mass_g`
- [x] `models/boosted_tree_classifier/` (BOOSTED_TREE_CLASSIFIER, XGBoost) — built + fully verified 2026-06-20, `census_adult_income` (same data/label as `logistic_regression`); includes tree visualization via EXPORT MODEL (Step 7)
- [x] `models/boosted_tree_regressor/` (BOOSTED_TREE_REGRESSOR, XGBoost) — built + fully verified 2026-06-20, `penguins`/`body_mass_g` (same data/label as `linear_regression`); includes tree visualization via EXPORT MODEL
- [x] `models/random_forest_classifier/` (RANDOM_FOREST_CLASSIFIER) — built 2026-06-21, `census_adult_income` (same data/label as `logistic_regression`/`boosted_tree_classifier`); tree visualization uses a dedicated shallow illustrative forest
- [x] `models/random_forest_regressor/` (RANDOM_FOREST_REGRESSOR) — built 2026-06-21, `penguins`/`body_mass_g` (same data/label as `linear_regression`/`boosted_tree_regressor`); genuinely underperforms boosting here (r2≈0.74 vs ≈0.97), discussed honestly in the notebook
- [ ] `models/dnn_classifier/` (DNN_CLASSIFIER)
- [ ] `models/dnn_regressor/` (DNN_REGRESSOR)
- [ ] `models/wide_and_deep_classifier/` (DNN_LINEAR_COMBINED_CLASSIFIER) — stretch goal, may move to a later phase
- [ ] `models/wide_and_deep_regressor/` (DNN_LINEAR_COMBINED_REGRESSOR) — stretch goal, may move to a later phase

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
| 2026-06-20 | RESOURCES.md full build (docs-first) | Replaced the stub RESOURCES.md (198 lines) with a comprehensive reference (~4,400 lines) built docs-first via an exhaustive multi-agent research pass (Google Cloud BQML docs as source of truth + this repo's tested notebooks/SQL for real syntax). Locked an entry schema first (per-model-type Template A, per-function Template B) + a scope-boundary policy (cross-link, don't duplicate, bq-ai-functions-owned topics: contribution analysis→AI.KEY_DRIVERS, TimesFM→AI.FORECAST/AI.EVALUATE/AI.DETECT_ANOMALIES, doc processing, LLM text/foundation embeddings, remote-LLM). Coverage: 5 comparison tables (model_type catalog, task→eval metrics, capability matrix, explainability, connection) + full entries for **all** model types (GLM, boosted tree, random forest, DNN, wide-and-deep, AutoML, k-means, PCA, autoencoder, matrix factorization, ARIMA_PLUS, ARIMA_PLUS_XREG, contribution analysis, imported TF/TFLite/ONNX/XGBoost, remote mechanism, transform-only) + all lifecycle functions (EVALUATE/PREDICT/CONFUSION_MATRIX/ROC_CURVE/EXPLAIN_PREDICT/GLOBAL_EXPLAIN/FEATURE_IMPORTANCE/WEIGHTS/ADVANCED_WEIGHTS/FEATURE_INFO/TRAINING_INFO/TRIAL_INFO/CENTROIDS/PRINCIPAL_COMPONENTS/_INFO/RECONSTRUCTION_LOSS/RECOMMEND/GENERATE_EMBEDDING(in-house)/FORECAST/EXPLAIN_FORECAST/ARIMA_EVALUATE/ARIMA_COEFFICIENTS/HOLIDAY_INFO/DETECT_ANOMALIES/TRANSFORM) + model-free families (scalers, bucketizers, encoders, feateng, text, distance, image) + management/monitoring (EXPORT MODEL, DESCRIBE_DATA, VALIDATE_DATA_SKEW/DRIFT, TFDV_DESCRIBE/VALIDATE). Each entry cites a tested repo example where one exists; gaps with no example flagged (ML.RECOMMEND, CONTRIBUTION_ANALYSIS, TF_IDF/BAG_OF_WORDS, image fns, LP_NORM). Research-discovered corrections: `ML.TRANSPOSE` is NOT a real function (it's the TRANSFORM-clause technique); encoder defaults now top_k=32000/frequency_threshold=5. Per-notebook RESOURCES refinement from running code remains the standing practice as notebooks are built. |
| 2026-06-20 | Phase 2: `models/linear_regression/` | Built the second model type: `LINEAR_REG` on `bigquery-public-data.ml_datasets.penguins` (label `body_mass_g`; rows with NULL label or unrecorded `sex` filtered out; 333 clean rows). Notebook + SQL mirror the `logistic_regression` skeleton, swapping classification-only steps (confusion matrix/ROC) for `ML.WEIGHTS` (interpretable regression coefficients — a differentiator from the classifier example). Lifecycle: CREATE MODEL → ML.EVALUATE → ML.PREDICT → ML.EXPLAIN_PREDICT → ML.GLOBAL_EXPLAIN → ML.WEIGHTS → ML.FEATURE_INFO/TRAINING_INFO → TRANSFORM clause → hyperparameter tuning (ML.TRIAL_INFO) → magics → BigFrames → cleanup. All SQL pre-validated end-to-end against BigQuery via `bq query` (confirmed: BQML auto-selects the `NORMAL_EQUATION` solver for this small/unregularized problem — a single closed-form training pass with no `eval_loss`, matching the RESOURCES.md GLM entry's note). Notebook cells built with validated source but not yet executed in a live kernel — needs a Restart & Run All pass to populate outputs before being treated as a second verified canonical reference. |
| 2026-06-20 | RESOURCES.md refinement from running code (task standing practice) | User ran `models/linear_regression/linear_regression.ipynb` (Restart & Run All); reviewing the real outputs against a second independent `bq query` pre-validation run surfaced a genuine, non-obvious BQML gotcha: with the default `category_encoding_method = 'ONE_HOT_ENCODING'`, `ML.WEIGHTS`/`ML.GLOBAL_EXPLAIN` per-category values for a GLM are **not uniquely identified** (one-hot dummies + intercept are collinear) — confirmed by retraining the identical model twice and watching an `island` category's weight swing from +305/+353/+340 to −39/−4/+8.6 between runs (different scale, different sign) while `ML.PREDICT`/`ML.EVALUATE` stayed stable. Fix: `category_encoding_method = 'DUMMY_ENCODING'` pins one baseline category per feature to `weight: 0.0`, making the rest stable, well-defined deltas. Updated `linear_regression.sql`/`.ipynb` (added the option to `CREATE MODEL`, explained why in cell markdown, cleared now-stale outputs pending a fresh Restart & Run All) and `RESOURCES.md` (GLM entry best-practices/limitations, `ML.WEIGHTS` entry best-practices/limitations/repo-example). Also caught and fixed a research-pass citation error: the `ML.WEIGHTS` entry had cited `data+ai/bq-ml/models/logistic_regression/logistic_regression.sql` as a `ML.WEIGHTS` example — that file does not use `ML.WEIGHTS` (only the repo's separate `03a - BQML Logistic Regression.ipynb` does); corrected to cite `linear_regression.sql` instead, which now legitimately demonstrates it. |
| 2026-06-20 | Phase 2: `models/linear_regression/` — final verification | User re-ran the notebook (Restart & Run All) after the `DUMMY_ENCODING` fix. Reviewed all outputs: `ML.WEIGHTS` now shows clean baselines (`species`=Adelie, `island`=Biscoe, `sex`=MALE all pinned to `weight: 0.0`) with stable deltas for every other category; this ties out exactly with `ML.EXPLAIN_PREDICT`, where Adelie-species rows correctly show a `species` attribution of `0.0`. `ML.EVALUATE`'s `r2_score` (0.875223) and all `ML.PREDICT` values are bit-for-bit identical to the pre-fix run, confirming `DUMMY_ENCODING` changed only weight interpretability, not model fit. Noted one more nuance for RESOURCES.md: across 2 independent runs with different random `AUTO_SPLIT`s, `DUMMY_ENCODING`'s dropped baseline category was identical both times and was consistently the *most frequent* category rather than the alphabetically-first one (`sex`: `MALE`, not alphabetically-earlier `FEMALE`, was the baseline both times) — added to the `category_encoding_method` option description. `models/linear_regression/` is now a fully verified second canonical reference alongside `models/logistic_regression/`. |
| 2026-06-20 | Phase 2 backlog: classifier/regressor split convention | Decided the structuring convention for the remaining Phase 2 techniques (boosted tree, random forest, DNN, wide-and-deep — each pairs a classifier + regressor `model_type`): build **separate folders/notebooks per `model_type`**, mirroring the `logistic_regression`/`linear_regression` precedent, rather than one combined notebook per technique. Expanded the Phase 2 backlog from 3 combined bullets to 6 explicit items (`boosted_tree_classifier`/`_regressor`, `random_forest_classifier`/`_regressor`, `dnn_classifier`/`_regressor`) plus 2 stretch items for wide-and-deep. RESOURCES.md continues to document each classifier/regressor pair under one combined heading (as it already does for GLM) — only the notebook/folder structure splits. |
| 2026-06-20 | Phase 2: `models/boosted_tree_classifier/` | Built the third model type: `BOOSTED_TREE_CLASSIFIER` on `bigquery-public-data.ml_datasets.census_adult_income` — deliberately reusing the exact data/label from `models/logistic_regression/` so the two notebooks form a direct "same problem, different technique" comparison (e.g. `roc_auc` side by side). Notebook + SQL mirror the `logistic_regression` skeleton, adding `ML.FEATURE_IMPORTANCE` (tree-specific split-based importance; N/A for GLMs) alongside `ML.GLOBAL_EXPLAIN`, and noting the two can rank features differently (attribution vs. split-based — expected, not a bug). TRANSFORM step uses `ML.QUANTILE_BUCKETIZE` (new preprocessing function for this project, vs. `ML.STANDARD_SCALER` in the GLM notebooks) to also broaden preprocessing-function coverage. Lifecycle: CREATE MODEL → ML.EVALUATE → ML.CONFUSION_MATRIX/ROC_CURVE → ML.PREDICT → ML.EXPLAIN_PREDICT → ML.GLOBAL_EXPLAIN/ML.FEATURE_IMPORTANCE → ML.FEATURE_INFO/TRAINING_INFO → TRANSFORM → HP tuning (ML.TRIAL_INFO) → magics → BigFrames → cleanup. All SQL pre-validated end-to-end against BigQuery via `bq query`. Confirmed a real runtime characteristic worth noting: `ML.TRAINING_INFO` iteration numbering starts at **1** (not 0, as in the GLM notebooks), and the first boosting iteration pays a large one-time data-loading/indexing cost (~14 min observed) before subsequent iterations run in milliseconds — documented in the notebook so it doesn't read as a stall. Also caught during HP-tuning validation: 1 of 6 trials transiently `FAILED` (`error_message = "An internal error happened during trial training."`, `NULL` objective metric) without failing the overall job — documented as a general `ML.TRIAL_INFO` gotcha (not boosted-tree-specific) in both the notebook/SQL and RESOURCES.md's `ML.TRIAL_INFO` entry. Notebook built with validated source but not yet executed live — pending a Restart & Run All pass. |
| 2026-06-20 | Phase 2: `models/boosted_tree_classifier/` — review + tree-visualization add | User ran Restart & Run All; reviewed all outputs (clean, matched pre-validation). Caught and fixed three issues: **(1)** a stale cross-reference — Step 1's markdown pointed to "(Step 8)" for `ML.TRAINING_INFO`, which actually lives in Step 6 (the notebook's Step numbering merges/splits differently than the `.sql` file's Example numbering; the two must each be internally self-consistent, not copied across); **(2)** the BigFrames comparison cell trained a plain `XGBClassifier()` with no class balancing while the SQL model uses `auto_class_weights=TRUE` — verified via `inspect.signature()` that `bigframes.ml.ensemble.XGBClassifier` has **no** `class_weight` parameter at all (unlike `LogisticRegression`, which does), so this is a real, permanent parity gap, not a fixable omission — documented inline rather than silently misleading; **(3)** added a new **Step 7 — Visualize a tree by exporting the model** per the user's suggestion, fully validated end-to-end first (`EXPORT MODEL` → download `model.bst` → load with `xgboost` → `xgboost.plot_tree()`). Verified two real gotchas in the process: exported boosted-tree/random-forest models use XGBoost 0.82's legacy binary format, unreadable by modern xgboost 2.0+ (must pin `xgboost==1.7.6`); and the export does not preserve `feature_names` (reassigned manually from the training query's column order, confirmed correct against actual split thresholds). Added a `BUCKET` config variable. Also corrected a stale, incorrect claim in this file's Resource Naming Strategy section (`EXPORT MODEL` does NOT need a connection — verified by testing; it already correctly said so in RESOURCES.md but this file had drifted). Documented all of this in RESOURCES.md (`EXPORT MODEL` entry, boosted-tree `BigFrames API` line) and as a new standing convention here (tree-ensemble notebooks get a visualization step; BigFrames parity must be checked against the actual installed signature, not assumed). `models/boosted_tree_classifier/` notebook updated with all fixes + the new step; cleared outputs, pending one more Restart & Run All. |
| 2026-06-20 | Phase 2: `models/boosted_tree_classifier/` — final verification | User re-ran the notebook (Restart & Run All) after all fixes. Reviewed every cell, including extracting and visually inspecting the rendered tree PNG from Step 7: it renders correctly with all 11 real feature names, and the run printed the expected `Loading model from XGBoost < 1.0.0` compatibility warning — confirming the `xgboost==1.7.6` pin works exactly as designed against a real (not toy) model. Cleanup deleted all 13 exported model files from GCS. All other steps (evaluate/confusion-matrix/predict/explain/importance/introspect/transform/HP-tuning/magics) matched the prior run's values exactly — boosted trees don't exhibit the GLM one-hot/intercept collinearity instability seen in `linear_regression`. `models/boosted_tree_classifier/` is now a fully verified third canonical reference. |
| 2026-06-20 | Phase 2: `models/boosted_tree_regressor/` | Built the fourth model type: `BOOSTED_TREE_REGRESSOR` on `bigquery-public-data.ml_datasets.penguins` (label `body_mass_g`) — deliberately reusing the exact data/label from `models/linear_regression/` for a direct technique comparison (`r2_score` 0.968 vs. 0.875 on identical data). Notebook + SQL copy the `boosted_tree_classifier` template (incl. the tree-visualization step) with regression-appropriate swaps: no `auto_class_weights` (regression has no class-weighting option), `TRANSFORM` uses `ML.LABEL_ENCODER` (a function not yet demonstrated in a model notebook) instead of `ML.QUANTILE_BUCKETIZE`. All SQL pre-validated end-to-end via `bq query`, including a standalone confirmatory export+load+plot test against the actual trained regressor (not just reusing the classifier's validation) — found one new, regressor-specific nuance: loading the exported booster prints an extra `reg:linear is now deprecated in favor of reg:squarederror` warning (harmless), documented alongside the shared `XGBoost < 1.0.0` warning in RESOURCES.md and the notebook. HP tuning this time had zero failed trials (contrast with `boosted_tree_classifier`'s 1-of-6, reinforcing that the earlier failure was transient/occasional, not systemic). Unlike the BigFrames caveat needed for the classifier, the regressor's BigFrames comparison is genuinely apples-to-apples (no weighting option is used in either the SQL or BigFrames path for regression). Notebook built with validated source; pending user Restart & Run All. |
| 2026-06-21 | Phase 2: `models/boosted_tree_regressor/` — final verification | User re-ran the notebook (Restart & Run All). Reviewed every cell and extracted/visually inspected the rendered tree PNG from Step 6: it matches the standalone pre-validation render exactly (`species<3` → `sex<2` → identical leaf values), and both expected warnings printed on load (`reg:linear` deprecation + `XGBoost < 1.0.0` compatibility). All other steps (evaluate/predict/explain/importance/introspect/transform/magics/BigFrames) matched pre-validation exactly, including the BigFrames step now being genuinely apples-to-apples with the SQL model (identical metrics on both sides — confirms the earlier fix was correct). HP tuning found a notably better model this run (`r2_score` 0.988 at `max_tree_depth=8`, vs. 0.968 in pre-validation) — expected run-to-run variability from random hyperparameter search, not a bug. Also reproducibly observed (both in pre-validation and this run) that `ML.TRAINING_INFO`'s `eval_loss` displays identically to `loss` at every iteration for this small dataset — a benign numerical curiosity, not documented further since it doesn't affect correctness or usage. Cleanup deleted all 8 exported GCS files. `models/boosted_tree_regressor/` is now a fully verified fourth canonical reference. |
| 2026-06-21 | Phase 2: `models/random_forest_classifier/` + `models/random_forest_regressor/` | Built the fifth and sixth model types together: `RANDOM_FOREST_CLASSIFIER` on `census_adult_income` (same data/label as `logistic_regression`/`boosted_tree_classifier`, three-way comparison) and `RANDOM_FOREST_REGRESSOR` on `penguins`/`body_mass_g` (same data/label as `linear_regression`/`boosted_tree_regressor`). Trained both in parallel background jobs to save wall-clock time; random forest trains notably faster than boosted trees (single-pass — ~5-7 min each vs. boosted trees' ~14-23 min) once past the first-job overhead. Three significant, verified findings from this pair: **(1)** `max_iterations` is not a valid `CREATE MODEL` option for `RANDOM_FOREST_*` at all — errors immediately (confirmed via `ML.TRAINING_INFO`: always exactly 1 iteration, `learning_rate=1.0`) — corrected an assumption from initial drafting (first attempt included it and failed). **(2)** A full-power random forest tree is far too dense to visualize (2,435 dump lines, depth 15 on the classifier's default-settings model) — `xgboost.plot_tree()` produces an illegible image even as SVG (which sidesteps the cairo bitmap-size limit but not the density). Fixed by training a small, separate shallow illustrative forest (`num_parallel_tree=10`, `max_tree_depth=3`) dedicated to the visualization step — verified this renders a clean, legible diagram — and recorded as a new standing addendum to the tree-visualization convention (RF-specific; does not apply to `BOOSTED_TREE_*`, whose early trees are naturally shallow). **(3)** On the small 333-row `penguins` dataset, `RANDOM_FOREST_REGRESSOR` genuinely underperforms both `BOOSTED_TREE_REGRESSOR` and `LINEAR_REG` (`r2_score` ≈ 0.74, best-tuned ≈ 0.76, vs. ≈ 0.97 and ≈ 0.88 respectively) — a real, reproducible comparison point (confirmed via HP tuning across a reasonable range), presented honestly in the notebook rather than hidden or hyperparameter-fished away. Also confirmed `bigframes.ml.ensemble.RandomForestClassifier` has no `class_weight` param (same gap as `XGBClassifier`) — same BigFrames caveat applied as `boosted_tree_classifier`. All SQL pre-validated end-to-end via `bq query` for both models including TRANSFORM (`ML.QUANTILE_BUCKETIZE` for classifier, `ML.LABEL_ENCODER` for regressor) and HP tuning (tuning `num_parallel_tree`/`max_tree_depth`). Both notebooks built with validated source; pending user Restart & Run All. |
| 2026-06-22 | Phase 2: `models/random_forest_classifier/` + `models/random_forest_regressor/` — final verification | User ran both notebooks (Restart & Run All), concurrently rather than back-to-back (longer per-cell wall-clock times observed, consistent with shared-project slot contention, not a defect). Reviewed every cell in both, including extracting and visually inspecting both rendered tree PNGs: both illustrative-forest diagrams are clean and legible (no `graph is too large` warning this time, confirming the fix), though the classifier's specific split structure matched an earlier standalone test exactly while the regressor's did not — leading to a new, useful finding (see below). Confirmed both zero-importance features (`island`, `culmen_length_mm`) reproduced exactly on the regressor. HP tuning showed a higher trial-failure rate under concurrent execution (2 of 6 failed on the classifier, vs. 1 of 6 in `boosted_tree_classifier`'s single-notebook run) — consistent with, not contradicting, the documented "occasional transient failure" gotcha. **New finding, and a correction to previously-recorded (but never actually verified) information:** the regressor's tuned model showed **two trials simultaneously marked `is_optimal = TRUE`** (tied `r2_score`) — disproving RESOURCES.md's prior unverified claim that "the smallest `trial_id` wins" implies a single `TRUE` row; corrected to state plainly that ties can produce multiple `TRUE` rows and callers needing exactly one should add an explicit tiebreak. Investigating this also surfaced the root cause of several "close but not bit-identical" values seen throughout this pair's validation and review: **`RANDOM_FOREST_*` retraining is inherently non-deterministic** (default `subsample`/`colsample_bynode` = 0.8, no exposed random seed) — unlike `BOOSTED_TREE_*`, which reproduced almost exactly across separate runs in earlier testing. Documented as a new RESOURCES.md limitation so it isn't mistaken for a bug in future model notebooks. Both `models/random_forest_classifier/` and `models/random_forest_regressor/` are now fully verified fifth/sixth canonical references. |
