<!--
Detailed reference for BigQuery ML: CREATE MODEL, the model lifecycle ML.* functions,
the model-free ML.* utilities, and model management (export/import/remote).
Entries used by a built notebook are written in full; the rest are stubs with doc
links and are tracked in PLANS.md Development Phases. Keep in sync with the official
docs via the audit procedure in PLANS.md.
-->

# BigQuery ML — Detailed Reference

BigQuery ML lets you create and run machine learning models using SQL. Models are first-class dataset objects created with `CREATE MODEL` and consumed with `ML.*` table-valued functions. Most model types train on data already in BigQuery with no connection, no data movement, and no separate training service.

**How the pieces fit:**
- **`CREATE MODEL`** trains a model and stores it in a dataset. The `model_type` option selects the algorithm.
- **Lifecycle `ML.*` functions** operate on a trained model: evaluate it, predict with it, explain it, introspect it.
- **Model-free `ML.*` functions** transform data directly (preprocessing, distance, text) — no model required.
- **Model management** covers exporting models to GCS, importing external models, and calling remote Vertex AI models.

Sections:
- [CREATE MODEL](#create-model)
- [Model Lifecycle Functions](#model-lifecycle-functions)
- [Model-Free Functions](#model-free-functions)
- [Model Management](#model-management)

---

## CREATE MODEL

The `CREATE MODEL` statement trains and stores a model. Full statement reference: [The CREATE MODEL statement](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create).

**General syntax:**
```sql
CREATE [OR REPLACE] MODEL [IF NOT EXISTS] `PROJECT_ID.DATASET.MODEL_NAME`
[TRANSFORM (SELECT_LIST_WITH_PREPROCESSING)]
OPTIONS (
  model_type = 'MODEL_TYPE',
  ...                       -- model-specific and shared options
)
AS QUERY_STATEMENT;
```

**`model_type` catalog:**

| model_type | Category | Lifecycle entry point | Status | Docs |
|-----------|----------|----------------------|--------|------|
| `LINEAR_REG` | Supervised (regression) | ML.PREDICT | GA | [GLM](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-glm) |
| `LOGISTIC_REG` | Supervised (classification) | ML.PREDICT | GA | [GLM](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-glm) |
| `BOOSTED_TREE_CLASSIFIER` / `BOOSTED_TREE_REGRESSOR` | Supervised (XGBoost) | ML.PREDICT | GA | [Boosted tree](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-boosted-tree) |
| `RANDOM_FOREST_CLASSIFIER` / `RANDOM_FOREST_REGRESSOR` | Supervised | ML.PREDICT | GA | [Random forest](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-random-forest) |
| `DNN_CLASSIFIER` / `DNN_REGRESSOR` | Supervised (neural net) | ML.PREDICT | GA | [DNN](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-dnn-models) |
| `KMEANS` | Unsupervised (clustering) | ML.PREDICT / ML.CENTROIDS | GA | [K-means](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-kmeans) |
| `PCA` | Unsupervised (dim. reduction) | ML.PREDICT / ML.PRINCIPAL_COMPONENTS | GA | [PCA](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-pca) |
| `MATRIX_FACTORIZATION` | Recommendation | ML.RECOMMEND | GA | [MF](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-matrix-factorization) |
| `ARIMA_PLUS` / `ARIMA_PLUS_XREG` | Time series | ML.FORECAST | GA | [Time series](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-time-series) |
| `AUTOENCODER` | Unsupervised | ML.PREDICT | GA | [Autoencoder](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-autoencoder) |
| `TENSORFLOW` / `ONNX` / `XGBOOST` (imported) | Imported model | ML.PREDICT | GA | [Imported](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-tensorflow) |
| Remote model | Remote (Vertex endpoint) | ML.PREDICT / AI.* | GA | [Remote](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-remote-model) |

**Shared options (selected):**

| Option | Applies to | Description |
|--------|-----------|-------------|
| `input_label_cols` | Supervised | Array naming the label column(s). |
| `auto_class_weights` | Classification | Balance class weights inversely to frequency. Useful for imbalanced labels. |
| `data_split_method` | Supervised | How to split train/eval: `AUTO_SPLIT` (default), `RANDOM`, `SEQ`, `NO_SPLIT`, `CUSTOM`. |
| `data_split_eval_fraction` / `data_split_col` | Supervised | Control the eval fraction or the splitting column. |
| `enable_global_explain` | Most | **Must be `TRUE` at training time to later use `ML.GLOBAL_EXPLAIN`.** |
| `l1_reg` / `l2_reg` | GLM, others | Regularization strength. Can be a fixed value or a `HPARAM_RANGE`/`HPARAM_CANDIDATES` for tuning. |
| `max_iterations`, `learn_rate_strategy`, `early_stop` | Iterative | Training-loop controls. |

**Hyperparameter tuning** ([overview](https://cloud.google.com/bigquery/docs/hp-tuning-overview)): add `num_trials` (required to enable tuning), optionally `max_parallel_trials` and `hparam_tuning_objectives`, and express searchable options as `HPARAM_RANGE(low, high)` or `HPARAM_CANDIDATES([...])`. BigQuery runs the trials and keeps the best model by the objective; inspect trials with [`ML.TRIAL_INFO`](#mltrial_info).

**The `TRANSFORM` clause:** preprocessing placed in `TRANSFORM(...)` is stored with the model and **reapplied automatically at prediction time**, so `ML.PREDICT` accepts raw input. Use the [model-free preprocessing functions](#model-free-functions) inside it (e.g. `ML.STANDARD_SCALER(col) OVER()`).

**Locations:** Models can be created in supported BigQuery ML locations; the dataset (and any connection/GCS for remote/imported/export) must be co-located. **Pricing:** billed by bytes processed during training (or flat-rate/edition slots).

---

## Model Lifecycle Functions

Functions that operate on a trained model.

### `ML.EVALUATE`
- **Description:** Compute evaluation metrics for a model. With no input data, uses the model's evaluation split; you can also pass a table/query to evaluate on new data.
- [documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-evaluate)
- **Type:** Table-valued function

**Syntax:**
```sql
SELECT * FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.MODEL` [, { TABLE `...` | (QUERY) }] [, STRUCT(... AS threshold)]);
```

**Outputs (classification):** `precision`, `recall`, `accuracy`, `f1_score`, `log_loss`, `roc_auc`.
**Outputs (regression):** `mean_absolute_error`, `mean_squared_error`, `mean_squared_log_error`, `median_absolute_error`, `r2_score`, `explained_variance`.
(Clustering, MF, and ARIMA return their own metric sets — e.g. `davies_bouldin_index` for K-means.)

**Best practice:** call with no data argument to use the held-out eval split; pass fresh data to measure generalization.

### `ML.PREDICT`
- **Description:** Generate predictions for each input row. Output columns are prefixed `predicted_`. For classifiers, also returns per-class probabilities.
- [documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-predict)
- **Type:** Table-valued function

**Syntax:**
```sql
SELECT * FROM ML.PREDICT(MODEL `PROJECT_ID.DATASET.MODEL`, { TABLE `...` | (QUERY) } [, STRUCT(... AS threshold)]);
```

**Outputs:** `predicted_<label>` plus, for classifiers, `predicted_<label>_probs` (an array of `{label, prob}` structs). All input columns pass through. Input must contain the model's feature columns (raw, if the model has a `TRANSFORM` clause).

### `ML.EXPLAIN_PREDICT`
- **Description:** Like `ML.PREDICT`, but also returns per-row feature attributions (the contribution of each feature to that prediction). Uses Shapley/integrated-gradients depending on model type.
- [documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-explain-predict)
- **Type:** Table-valued function

**Syntax:**
```sql
SELECT * FROM ML.EXPLAIN_PREDICT(MODEL `...`, { TABLE `...` | (QUERY) }, STRUCT(N AS top_k_features [, threshold]));
```
**Outputs:** prediction columns + `top_feature_attributions` (array of `{feature, attribution}`) + baseline/approximation columns.

### `ML.GLOBAL_EXPLAIN`
- **Description:** Global feature importance aggregated across the training data.
- [documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-global-explain)
- **Type:** Table-valued function
- **Requirement:** the model must be trained with `enable_global_explain = TRUE`, otherwise this errors with "the input model was not explained when it was created."

**Syntax:** `SELECT * FROM ML.GLOBAL_EXPLAIN(MODEL `...`);`
**Outputs:** `feature`, `attribution` (sorted by importance).

### `ML.CONFUSION_MATRIX`
- **Description:** Confusion matrix (counts of predicted vs actual class) for a classifier, on the eval split or supplied data.
- [documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-confusion)
- **Outputs:** `expected_label` plus one column per predicted class.

### `ML.ROC_CURVE`
- **Description:** ROC curve points for a binary classifier across thresholds.
- [documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-roc)
- **Outputs:** `threshold`, `recall`, `false_positive_rate`, `true_positives`, `false_positives`, `true_negatives`, `false_negatives`.

### `ML.FEATURE_INFO`
- **Description:** Per-feature statistics observed during training.
- [documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-feature)
- **Outputs:** `input`, `min`, `max`, `mean`, `median`, `stddev`, `category_count`, `null_count`, `dimension` (numeric columns are populated; categorical columns populate `category_count`).

### `ML.TRAINING_INFO`
- **Description:** Per-iteration training history (loss curve), and per-trial when tuning.
- [documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-train)
- **Outputs:** `training_run`, `iteration`, `loss`, `eval_loss`, `learning_rate`, `duration_ms`.

### `ML.TRIAL_INFO`
- **Description:** One row per hyperparameter-tuning trial, with the trial's hyperparameters, objective score, and whether it was selected.
- [documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-trial-info)
- **Requirement:** model trained with `num_trials`.
- **Outputs:** `trial_id`, `hyperparameters` (JSON), `hparam_tuning_evaluation_metrics` (struct of metrics, e.g. `.roc_auc`), `training_loss`, `eval_loss`, `status`, `is_optimal`.

### `ML.FORECAST` / `ML.EXPLAIN_FORECAST` *(time series — stub)*
- Entry point for `ARIMA_PLUS` models. Returns forecast values + prediction intervals; `ML.EXPLAIN_FORECAST` decomposes into trend/seasonality. [forecast docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-forecast). *To be covered with `models/arima_plus/`.*

### `ML.RECOMMEND` *(recommendation — stub)*
- Entry point for `MATRIX_FACTORIZATION` models; returns recommended items per user. [recommend docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-recommend). *To be covered with `models/matrix_factorization/`.*

### `ML.CENTROIDS` / `ML.PRINCIPAL_COMPONENTS` / `ML.WEIGHTS` *(stubs)*
- Model-specific introspection for K-means (`ML.CENTROIDS`), PCA (`ML.PRINCIPAL_COMPONENTS`), and GLM/linear weights (`ML.WEIGHTS`). *To be covered with their respective model notebooks.*

---

## Model-Free Functions

`ML.*` functions that transform data directly — no model required. Used standalone or inside a `TRANSFORM` clause. Reference: [Preprocessing functions](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-preprocessing-functions).

### `ML.STANDARD_SCALER`
- **Description:** Standardize a numeric column to zero mean and unit variance. Used inside `TRANSFORM` as `ML.STANDARD_SCALER(col) OVER() AS col`, or standalone over a window.
- [documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-preprocessing-functions)
- **Note:** Covered inline in `models/logistic_regression/` (Step 7, TRANSFORM clause). A dedicated `functions/ml_standard_scaler/` is in the backlog.

### Other preprocessing / utility functions *(stubs — see PLANS.md Phase 6)*
`ML.MIN_MAX_SCALER`, `ML.MAX_ABS_SCALER`, `ML.ROBUST_SCALER`, `ML.BUCKETIZE`, `ML.QUANTILE_BUCKETIZE`, `ML.ONE_HOT_ENCODER`, `ML.LABEL_ENCODER`, `ML.FEATURE_CROSS`, `ML.POLYNOMIAL_EXPAND`, `ML.IMPUTER`, `ML.DISTANCE`, `ML.LP_NORM`, `ML.NGRAMS`, `ML.TF_IDF`, `ML.BAG_OF_WORDS`. All documented under the preprocessing-functions reference above; each gets a `functions/{name}/` folder when built.

---

## Model Management

### `EXPORT MODEL` *(stub)*
- Export a BigQuery ML model to Cloud Storage (TensorFlow SavedModel / XGBoost format) for serving elsewhere (TF Serving, Vertex AI). [export docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-export-model). *To be covered with `models/export/`.*

### Imported models *(stub)*
- `CREATE MODEL ... OPTIONS(model_type='TENSORFLOW'|'ONNX'|'XGBOOST', model_path='gs://...')` with a connection — run external models via `ML.PREDICT` inside BigQuery. [imported docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-tensorflow). *To be covered with `models/imported/`.*

### Remote models *(stub)*
- `CREATE MODEL ... REMOTE WITH CONNECTION ... OPTIONS(endpoint='...')` — call a Vertex AI endpoint (or hosted foundation model) from SQL. This is the same mechanism the `bq-ai-functions` project uses for `ML.GENERATE_TEXT` / `ML.GENERATE_EMBEDDING`. [remote docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-remote-model). *To be covered with `models/remote/`; cross-links to `../bq-ai-functions/`.*

---

## BigFrames (Python)

BigFrames exposes a scikit-learn-style API (`bigframes.ml`) that trains BigQuery ML models under the hood — e.g. `bigframes.ml.linear_model.LogisticRegression`, `LinearRegression`, `bigframes.ml.cluster.KMeans`, `bigframes.ml.decomposition.PCA`, `bigframes.ml.ensemble.*`. Each model notebook includes a BigFrames section showing the equivalent of its SQL workflow. [bigframes.ml reference](https://cloud.google.com/python/docs/reference/bigframes/latest/bigframes.ml).
