![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Fdata%2Bai%2Fbq-ml&file=RESOURCES.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/data%2Bai/bq-ml/RESOURCES.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ml/RESOURCES.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ml/RESOURCES.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ml/RESOURCES.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ml/RESOURCES.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-ml/RESOURCES.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-ml/RESOURCES.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# BigQuery ML — Detailed Reference

BigQuery ML lets you create and run machine learning models using SQL. Models are first-class dataset objects created with `CREATE MODEL` and consumed with `ML.*` table-valued functions. Most model types train on data already in BigQuery — no connection, no data movement, and no separate training service.

This is the deep per-item reference for the project. For the map (tables + diagram + tree) see [README.md](README.md); for conventions, templates, the backlog, and the audit procedure see [PLANS.md](PLANS.md).

**How the pieces fit:**
- **`CREATE MODEL`** trains a model and stores it in a dataset. The `model_type` option selects the algorithm.
- **Lifecycle `ML.*` functions** operate on a trained model: evaluate it, predict with it, explain it, introspect it.
- **Model-free `ML.*` functions** transform data directly (preprocessing, distance, text, image) — no model required.
- **Model management** covers exporting models to GCS, importing external models, calling remote endpoints, and monitoring.

For each item below we collect: a description and use cases, the documentation URL (a research-retrieval page for audits), syntax, inputs, outputs, the models it applies to / lifecycle functions it supports, best practices, limitations, the BigFrames equivalent, and a **tested repo example** wherever one exists.

## Sections
- [Scope & Cross-References](#scope--cross-references)
- [Comparison Tables](#comparison-tables)
- [CREATE MODEL — Model Types](#create-model--model-types)
- [Model Lifecycle Functions](#model-lifecycle-functions)
- [Model-Free Functions](#model-free-functions)
- [Model Management & Monitoring](#model-management--monitoring)

---

## Scope & Cross-References

This project (`bq-ml`) covers the **`CREATE MODEL` + `ML.*` lifecycle** — training models in SQL and the functions that evaluate, predict with, explain, and introspect them, plus model-free preprocessing and model management/monitoring.

Its sibling project **[`../bq-ai-functions/`](../bq-ai-functions/RESOURCES.md)** covers the **generative-AI / foundation-model `AI.*` (and LLM `ML.*`) functions** (Gemini-in-SQL, embeddings, TimesFM forecasting, document processing). Where a topic is owned there, this reference **hyperlinks out rather than duplicating it**:

| Topic encountered in bq-ml | Cross-link to bq-ai-functions (not duplicated here) |
|---|---|
| Contribution analysis (`CONTRIBUTION_ANALYSIS` model) | [`AI.KEY_DRIVERS`](../bq-ai-functions/RESOURCES.md) — the model-free equivalent |
| TimesFM forecasting (built-in foundation forecaster) | [`AI.FORECAST`, `AI.EVALUATE`, `AI.DETECT_ANOMALIES`](../bq-ai-functions/RESOURCES.md) |
| Document processing | [`ML.DOCUMENT_PROCESS`](../bq-ai-functions/RESOURCES.md) |
| LLM text generation | [`ML.GENERATE_TEXT`, `AI.GENERATE_*`](../bq-ai-functions/RESOURCES.md) |
| Foundation-model embeddings | [foundation `ML.GENERATE_EMBEDDING` / `AI.GENERATE_EMBEDDING`](../bq-ai-functions/RESOURCES.md) |
| Remote-model LLM endpoints | [the remote-model LLM pattern](../bq-ai-functions/RESOURCES.md) |

**Nuances kept in-scope here:** `ML.GENERATE_EMBEDDING` used to extract embeddings *from a trained `PCA` / `AUTOENCODER` / `MATRIX_FACTORIZATION` model* is a lifecycle use of a BQML model and is documented here; the foundation-model (text/multimodal) use cross-links out. The remote-model *mechanism* (`CREATE MODEL ... REMOTE WITH CONNECTION` querying a custom Vertex AI endpoint with `ML.PREDICT`) is documented here; LLM endpoint *usage* cross-links out.

---

## Comparison Tables

The fastest way to answer "which model / which function do I use?" Detailed entries follow in later sections.

### 1. `model_type` catalog

| model_type | Category | Lifecycle entry | Connection? | Status |
|-----------|----------|-----------------|-------------|--------|
| `LINEAR_REG` | Supervised (regression) | `ML.PREDICT` | No | GA |
| `LOGISTIC_REG` | Supervised (classification) | `ML.PREDICT` | No | GA |
| `BOOSTED_TREE_CLASSIFIER` / `_REGRESSOR` | Supervised (XGBoost) | `ML.PREDICT` | No | GA |
| `RANDOM_FOREST_CLASSIFIER` / `_REGRESSOR` | Supervised (XGBoost) | `ML.PREDICT` | No | GA |
| `DNN_CLASSIFIER` / `_REGRESSOR` | Supervised (neural net) | `ML.PREDICT` | No | GA |
| `DNN_LINEAR_COMBINED_CLASSIFIER` / `_REGRESSOR` | Supervised (wide-and-deep) | `ML.PREDICT` | No | GA |
| `AUTOML_CLASSIFIER` / `_REGRESSOR` | Supervised (AutoML Tables) | `ML.PREDICT` | No* | GA |
| `KMEANS` | Unsupervised (clustering) | `ML.PREDICT` / `ML.CENTROIDS` | No | GA |
| `PCA` | Unsupervised (dim. reduction) | `ML.PREDICT` / `ML.PRINCIPAL_COMPONENTS` | No | GA |
| `AUTOENCODER` | Unsupervised | `ML.PREDICT` / `ML.RECONSTRUCTION_LOSS` | No | GA |
| `MATRIX_FACTORIZATION` | Recommendation | `ML.RECOMMEND` | No** | GA |
| `ARIMA_PLUS` | Time series (univariate) | `ML.FORECAST` | No | GA |
| `ARIMA_PLUS_XREG` | Time series (+ regressors) | `ML.FORECAST` | No | GA |
| `CONTRIBUTION_ANALYSIS` | Insight / key drivers | `ML.GET_INSIGHTS` | No | GA |
| `TENSORFLOW` / `TENSORFLOW_LITE` / `ONNX` / `XGBOOST` | Imported (from GCS) | `ML.PREDICT` | No*** | GA |
| Remote model (custom endpoint) | Remote (Vertex AI endpoint) | `ML.PREDICT` | **Yes** | GA |
| `TRANSFORM_ONLY` | Preprocessing-only | `ML.TRANSFORM` | No | GA |
| TimesFM (built-in) → `AI.FORECAST` | Time series (foundation) | `AI.FORECAST` | No | GA — see [bq-ai-functions](../bq-ai-functions/RESOURCES.md) |

\* AutoML trains via an `ML_EXTERNAL` Vertex AI job but needs no `CREATE CONNECTION` object. \*\* Matrix factorization needs reservation/Editions (capacity) slots, not on-demand pricing — but no connection. \*\*\* Imported models need a connection only when served over an object table (reservation pricing).

### 2. Task → `ML.EVALUATE` metric columns

| Task / model family | `ML.EVALUATE` metric columns |
|---|---|
| Regression (`LINEAR_REG`, tree/DNN/WnD regressors) | `mean_absolute_error`, `mean_squared_error`, `mean_squared_log_error`, `median_absolute_error`, `r2_score`, `explained_variance` |
| Classification (`LOGISTIC_REG`, tree/DNN/WnD/AutoML classifiers) | `precision`, `recall`, `accuracy`, `f1_score`, `log_loss`, `roc_auc` |
| K-means | `davies_bouldin_index`, `mean_squared_distance` |
| Matrix factorization — explicit | `mean_absolute_error`, `mean_squared_error`, `mean_squared_log_error`, `r2_score`, `explained_variance` |
| Matrix factorization — implicit | `mean_average_precision`, `mean_squared_error`, `normalized_discounted_cumulative_gain`, `average_rank` |
| PCA | `total_explained_variance_ratio` |
| Autoencoder | `mean_absolute_error`, `mean_squared_error`, `mean_squared_log_error` |
| Time series (ARIMA_PLUS, with test data) | `mean_absolute_error`, `mean_squared_error`, `root_mean_squared_error`, `mean_absolute_percentage_error`, `symmetric_mean_absolute_percentage_error`, `mean_absolute_scaled_error` |

A `trial_id` column is prepended for hyperparameter-tuned models.

### 3. Capability matrix (per model type)

| Model type | TRANSFORM | HP tuning | `enable_global_explain` | Weights fn | Feature attributions | `ML.DETECT_ANOMALIES` |
|---|---|---|---|---|---|---|
| `LINEAR_REG` / `LOGISTIC_REG` | ✅ | ✅ | ✅ | `ML.WEIGHTS` / `ML.ADVANCED_WEIGHTS` | `ML.EXPLAIN_PREDICT`, `ML.GLOBAL_EXPLAIN` | — |
| `BOOSTED_TREE_*` | ✅ | ✅ | ✅ | — | `ML.FEATURE_IMPORTANCE`, `ML.EXPLAIN_PREDICT`, `ML.GLOBAL_EXPLAIN` | — |
| `RANDOM_FOREST_*` | ✅ | ✅ | ✅ | — | `ML.FEATURE_IMPORTANCE`, `ML.EXPLAIN_PREDICT`, `ML.GLOBAL_EXPLAIN` | — |
| `DNN_*` | ✅ | ✅ | ✅ | — | `ML.EXPLAIN_PREDICT`, `ML.GLOBAL_EXPLAIN` (Integrated Gradients) | — |
| `DNN_LINEAR_COMBINED_*` | ✅ | ✅ | ✅ | — | `ML.EXPLAIN_PREDICT`, `ML.GLOBAL_EXPLAIN` | — |
| `AUTOML_*` | — | (internal) | (auto) | — | `ML.GLOBAL_EXPLAIN` only | — |
| `KMEANS` | ✅ | ✅ (`num_clusters`) | — | `ML.CENTROIDS` | — | ✅ (`contamination`) |
| `PCA` | ✅ | — | — | `ML.PRINCIPAL_COMPONENTS` / `_INFO` | — | ✅ (`contamination`) |
| `AUTOENCODER` | ✅ | ✅ | — | — | — | ✅ (`contamination`) |
| `MATRIX_FACTORIZATION` | — | ✅ | — | `ML.WEIGHTS` | — | — |
| `ARIMA_PLUS` / `_XREG` | ✅* | (auto.ARIMA) | — | `ML.ARIMA_COEFFICIENTS` | `ML.EXPLAIN_FORECAST` | ✅ (`anomaly_prob_threshold`) |
| Imported (`TENSORFLOW`/`ONNX`/`XGBOOST`/`TFLITE`) | — | — | — | — | `ML.FEATURE_IMPORTANCE` (XGBOOST), `ML.EXPLAIN_PREDICT` (TF) | — |
| Remote (custom endpoint) | — | — | — | — | — | — |

\* ARIMA_PLUS supports `TRANSFORM` except when modeling custom holidays; `ARIMA_PLUS_XREG` does not support `TRANSFORM`.

### 4. Explainability / weights functions

| Function | Scope | Applies to | Key output | Pre-req |
|---|---|---|---|---|
| `ML.EXPLAIN_PREDICT` | Per-row (local) | linear, logistic, tree, DNN, WnD, AutoML | `top_feature_attributions` | input table |
| `ML.GLOBAL_EXPLAIN` | Model-level | same supervised types | `feature`, `attribution` | `enable_global_explain = TRUE` |
| `ML.FEATURE_IMPORTANCE` | Model-level (tree splits) | boosted-tree, random-forest, imported XGBOOST | `importance_weight/gain/cover` | none |
| `ML.WEIGHTS` | Coefficients | `LINEAR_REG`, `LOGISTIC_REG`, `MATRIX_FACTORIZATION` | `weight` / `factor_weights` | none |
| `ML.ADVANCED_WEIGHTS` | Coefficients + stats | `LINEAR_REG`, binary `LOGISTIC_REG` | `standard_error`, `p_value` | `calculate_p_values=TRUE`, `DUMMY_ENCODING`, `l1_reg=0` |
| `ML.CENTROIDS` | Cluster centers | `KMEANS` | per-feature centroid values | none |
| `ML.PRINCIPAL_COMPONENTS` / `_INFO` | Loadings / variance | `PCA` | eigenvectors / eigenvalues | none |
| `ML.ARIMA_COEFFICIENTS` | AR/MA coefficients | `ARIMA_PLUS`, `_XREG` | `ar_coefficients`, `ma_coefficients` | none |

### 5. Connection matrix

| Model category | Connection required? |
|---|---|
| All natively-trained models (GLM, trees, DNN, k-means, PCA, autoencoder, MF, ARIMA, contribution analysis) | **No** |
| AutoML | No (uses an internal `ML_EXTERNAL` Vertex AI job) |
| Imported (TF / TFLite / ONNX / XGBoost) | No for `ML.PREDICT`; **Yes** (Cloud Resource + reservation) only for object-table serving |
| Remote (custom Vertex AI endpoint) | **Yes** — Cloud Resource Connection |
| `EXPORT MODEL` to GCS | No (writer needs GCS write IAM, not a BQ connection) |

---


## CREATE MODEL — Model Types

The `CREATE MODEL` statement trains and stores a model; the `model_type` option selects the algorithm. Full statement reference: [The CREATE MODEL statement](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create). Entries below are grouped supervised → unsupervised → recommendation → time series → insight → imported → remote → transform-only.


---

### `LINEAR_REG` / `LOGISTIC_REG`  (Generalized Linear Models)

- **Description:** BigQuery ML's generalized linear models. `LINEAR_REG` fits a linear-regression model for predicting a continuous numeric label. `LOGISTIC_REG` fits a logistic-regression model that estimates class probabilities (via the logit / log-odds link) for **binary or multiclass** classification. Both share one `CREATE MODEL` reference page because they are the same GLM family with different link functions.
- **When to use:**
  - Fast, interpretable baseline before reaching for trees/AutoML — weights and p-values are directly readable.
  - `LINEAR_REG`: continuous targets (revenue, weight, demand). Also the workhorse for **regression-based forecasting** (lagged-feature design matrix).
  - `LOGISTIC_REG`: yes/no, churn, fraud, multiclass labels; need calibrated class probabilities.
  - Wide, mostly-linear feature relationships; when explainability/statistical inference (standard errors, p-values) matters.
- **Category:** supervised-regression (`LINEAR_REG`) | supervised-classification (`LOGISTIC_REG`).
- **Connection required:** No. (A connection is only needed for the optional `EXPORT MODEL` to GCS or remote/imported models — not for GLM training.)
- **Status:** GA.
- **documentation:** [CREATE MODEL for GLMs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-glm) · journey links: [ML.EVALUATE](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-evaluate), [ML.PREDICT](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-predict), [ML.WEIGHTS](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-weights), [ML.ADVANCED_WEIGHTS](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-advanced-weights), [ML.GLOBAL_EXPLAIN](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-global-explain), [ML.EXPLAIN_PREDICT](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-explain-predict), [ML.CONFUSION_MATRIX](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-confusion), [ML.ROC_CURVE](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-roc), [HP tuning](https://cloud.google.com/bigquery/docs/hp-tuning-overview).

**CREATE MODEL syntax:**
```sql
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.MODEL_NAME`
[TRANSFORM(...)]
OPTIONS(
  model_type = 'LOGISTIC_REG',          -- or 'LINEAR_REG'
  input_label_cols = ['label_col'],
  auto_class_weights = TRUE,            -- LOGISTIC_REG only; balances classes
  calculate_p_values = TRUE,           -- enables ML.ADVANCED_WEIGHTS (see gotchas)
  category_encoding_method = 'DUMMY_ENCODING',
  enable_global_explain = TRUE,        -- required for ML.GLOBAL_EXPLAIN
  data_split_method = 'AUTO_SPLIT'
) AS
SELECT feature1, feature2, ..., label_col
FROM `PROJECT_ID.DATASET.training_table`;
```

**Options (model-specific):**

| Option | Type | Required | Default | Range / Values | Description |
|--------|------|----------|---------|----------------|-------------|
| `model_type` | STRING | Yes | — | `LINEAR_REG`, `LOGISTIC_REG` | Selects the GLM family. |
| `input_label_cols` | ARRAY\<STRING\> | No | `['label']` | column name(s) | Label column. If absent, a column named `label` must exist. |
| `optimize_strategy` | STRING | No | `AUTO_STRATEGY` | `AUTO_STRATEGY`, `BATCH_GRADIENT_DESCENT`, `NORMAL_EQUATION` | Training solver. AUTO picks NORMAL_EQUATION for small/unregularized problems, else BATCH_GRADIENT_DESCENT (e.g. when `l1_reg` set, `warm_start`=TRUE, feature cardinality \> 10,000, or over-fitting risk). |
| `l1_reg` | FLOAT64 | No | `0` (none) | \>= 0 | L1 regularization. **Tunable** (`HPARAM_RANGE`/`HPARAM_CANDIDATES`). |
| `l2_reg` | FLOAT64 | No | `0` (none) | \>= 0 | L2 regularization. **Tunable**. |
| `max_iterations` | INT64 | No | `20` | \>= 1 | Max gradient-descent steps. **Tunable**. |
| `learn_rate_strategy` | STRING | No | `LINE_SEARCH` | `LINE_SEARCH`, `CONSTANT` | How learning rate is set (gradient descent only). **Tunable**. |
| `learn_rate` | FLOAT64 | No | `0.1` | \> 0 | Used when strategy is `CONSTANT`. **Tunable**. |
| `ls_init_learn_rate` | FLOAT64 | No | `0.1` | \> 0 | Initial rate for `LINE_SEARCH`. **Tunable**. |
| `early_stop` | BOOL | No | `TRUE` | TRUE/FALSE | Stop when improvement \< `min_rel_progress`. |
| `min_rel_progress` | FLOAT64 | No | `0.01` | \> 0 | Min relative loss improvement to continue. |
| `data_split_method` | STRING | No | `AUTO_SPLIT` | `AUTO_SPLIT`, `RANDOM`, `CUSTOM`, `SEQ`, `NO_SPLIT` | How eval data is held out. |
| `data_split_eval_fraction` | FLOAT64 | No | `0.2` | 0–1 | Eval fraction for RANDOM/SEQ. |
| `data_split_col` | STRING | No | — | column name | With `CUSTOM`: BOOL col, `TRUE`=eval, `FALSE`=train (excluded from features). |
| `auto_class_weights` | BOOL | No | `FALSE` | TRUE/FALSE | `LOGISTIC_REG` only — balance classes inversely to frequency. |
| `class_weights` | ARRAY\<STRUCT\> | No | — | (label, weight) | `LOGISTIC_REG` only — manual per-class weights (mutually exclusive with `auto_class_weights`). |
| `calculate_p_values` | BOOL | No | `FALSE` | TRUE/FALSE | Compute standard errors + p-values (read via `ML.ADVANCED_WEIGHTS`). See gotchas. |
| `fit_intercept` | BOOL | No | `TRUE` | TRUE/FALSE | Include the `__INTERCEPT__` term. |
| `category_encoding_method` | STRING | No | `ONE_HOT_ENCODING` | `ONE_HOT_ENCODING`, `DUMMY_ENCODING` | Categorical encoding. `DUMMY_ENCODING` required for p-values; also recommended whenever reading `ML.WEIGHTS` (see best practices below). With `DUMMY_ENCODING`, the dropped baseline category (pinned `weight: 0.0`) is not user-configurable — **observed** (2 runs, `models/linear_regression/`, different random `AUTO_SPLIT`s each time) to be deterministic per dataset and to consistently pick the most-frequent category, not the alphabetically-first one (e.g. `sex`: `MALE` (168 rows) was the baseline both times, not `FEMALE` (165 rows), despite `FEMALE` < `MALE` alphabetically). |
| `enable_global_explain` | BOOL | No | `FALSE` | TRUE/FALSE | Must be TRUE to later call `ML.GLOBAL_EXPLAIN`. |
| `warm_start` | BOOL | No | `FALSE` | TRUE/FALSE | Continue training an existing model with new data/options. |
| `num_trials` / `max_parallel_trials` / `hparam_tuning_objectives` | — | No | — | — | Enable hyperparameter tuning (see below). |

**Supported lifecycle functions:** `ML.EVALUATE`, `ML.PREDICT`, `ML.WEIGHTS`, `ML.ADVANCED_WEIGHTS`, `ML.GLOBAL_EXPLAIN`, `ML.EXPLAIN_PREDICT`, `ML.FEATURE_INFO`, `ML.TRAINING_INFO`, `ML.TRIAL_INFO` (when tuned), `EXPORT MODEL`. **Classification-only:** `ML.CONFUSION_MATRIX`; **binary-classification-only:** `ML.ROC_CURVE`. (`ML.FEATURE_IMPORTANCE` is for tree/forest models, not GLMs — use `ML.WEIGHTS`/`ML.GLOBAL_EXPLAIN`.)

**ML.EVALUATE output metrics (this type):**
- `LINEAR_REG` (regression): `mean_absolute_error`, `mean_squared_error`, `mean_squared_log_error`, `median_absolute_error`, `r2_score`, `explained_variance`.
- `LOGISTIC_REG` (classification): `precision`, `recall`, `accuracy`, `f1_score`, `log_loss`, `roc_auc`.

**Preprocessing support:** automatic (BQML auto-standardizes numeric features and encodes categoricals) **or** explicit via the `TRANSFORM` clause — preprocessing (e.g. `ML.STANDARD_SCALER`, `ML.BUCKETIZE`, `ML.QUANTILE_BUCKETIZE`) is saved with the model and reapplied automatically at `ML.PREDICT`/`ML.EVALUATE` time.

**Hyperparameter tuning:** Supported. Set `num_trials` (+ optional `max_parallel_trials`, `hparam_tuning_objectives`). Tunable options: `l1_reg`, `l2_reg`, `learn_rate`, `learn_rate_strategy`, `ls_init_learn_rate`, `max_iterations`, `dropout`-n/a. Use `HPARAM_RANGE(lo, hi)` or `HPARAM_CANDIDATES([...])`. Default tuning objective: `r2_score` (LINEAR_REG), `roc_auc` (LOGISTIC_REG). Inspect with `ML.TRIAL_INFO`.

**Explainability / weights:**
- `ML.WEIGHTS` — model coefficients (incl. `__INTERCEPT__`; `category_weights` array for categoricals).
- `ML.ADVANCED_WEIGHTS` — superset adding `standard_error` and `p_value` (requires `calculate_p_values = TRUE`).
- `ML.GLOBAL_EXPLAIN` — overall feature attributions (requires `enable_global_explain = TRUE` at train time).
- `ML.EXPLAIN_PREDICT` — per-row feature attributions (`STRUCT(k AS top_k_features)`).

**Best practices:**
- Set `enable_global_explain = TRUE` at train time if you'll want global attributions — it cannot be added afterward.
- For imbalanced classification (e.g. fraud), use `auto_class_weights = TRUE`.
- Use `data_split_method = 'CUSTOM'` with a BOOL split column to reproduce TRAIN/VALIDATE/TEST exactly.
- `NORMAL_EQUATION` (auto-selected for small unregularized problems) trains in one pass — no iterations to tune; `ML.TRAINING_INFO` returns a single row with `eval_loss = NULL` (no per-iteration eval curve like gradient descent produces).
- **Use `category_encoding_method = 'DUMMY_ENCODING'` whenever you plan to read `ML.WEIGHTS`.** With the default `ONE_HOT_ENCODING`, every category is one-hot encoded *and* the model keeps an intercept, so the design matrix is collinear (rank-deficient) for any categorical feature — the individual `category_weights` are not uniquely identified. **Verified by training the same model twice** (`models/linear_regression/`, `penguins`/`body_mass_g`, identical `SELECT`, only `AUTO_SPLIT`'s random draw differing): an `island` category's weight swung from **+305 / +353 / +340 in one run to −39 / −4 / +8.6 in another** — different scale, different sign — while `ML.PREDICT` and `ML.EVALUATE` stayed effectively unchanged. `DUMMY_ENCODING` drops one baseline category per feature (pinned to `weight: 0.0`) and makes every other category's weight a stable, well-defined delta from it.

**Limitations:**
- `ML.ADVANCED_WEIGHTS` p-values require **all** of: `calculate_p_values = TRUE`, `category_encoding_method = 'DUMMY_ENCODING'`, `l1_reg = 0`, **and** total feature cardinality \< 1,000. Only linear and **binary** logistic regression are supported (not multiclass).
- `ML.ROC_CURVE` is binary-only; `ML.CONFUSION_MATRIX` is classification-only.
- Linear models capture only linear relationships — engineer interaction/polynomial features (via `TRANSFORM`) for nonlinearity, or use boosted trees.
- `ML.WEIGHTS`/`ML.GLOBAL_EXPLAIN` attributions for a given category can shift materially between training runs when using `ONE_HOT_ENCODING` (see the `DUMMY_ENCODING` best practice above) — don't treat one run's per-category numbers as ground truth unless trained with `DUMMY_ENCODING`.

**Locations:** Available in all BigQuery ML regions/multi-regions. `EXPORT MODEL` (to GCS, TensorFlow SavedModel format) and Vertex AI Model Registry registration are supported.

**BigFrames API:** `bigframes.ml.linear_model.LinearRegression()` and `bigframes.ml.linear_model.LogisticRegression()` — `.fit(X, y)` / `.predict()` / `.score()`.

**Repo example (tested):**
- `data+ai/bq-ml/models/logistic_regression/logistic_regression.sql` — progressive LOGISTIC_REG lifecycle on `census_adult_income`: create → ML.EVALUATE → ML.CONFUSION_MATRIX → ML.ROC_CURVE → ML.PREDICT → ML.EXPLAIN_PREDICT → ML.GLOBAL_EXPLAIN → ML.FEATURE_INFO/TRAINING_INFO → TRANSFORM → HP tuning.
- `data+ai/bq-ml/models/linear_regression/linear_regression.sql` — progressive LINEAR_REG lifecycle on `penguins`/`body_mass_g`: create (with `DUMMY_ENCODING`) → ML.EVALUATE → ML.PREDICT → ML.EXPLAIN_PREDICT → ML.GLOBAL_EXPLAIN → **ML.WEIGHTS** → ML.FEATURE_INFO/TRAINING_INFO → TRANSFORM → HP tuning. Confirmed the `NORMAL_EQUATION` single-pass behavior and the `ONE_HOT_ENCODING` category-weight instability documented above.
- `03 - BigQuery ML (BQML)/03a - BQML Logistic Regression.ipynb` — binary fraud classifier with `auto_class_weights`, `calculate_p_values`, `CUSTOM` split, `ML.ADVANCED_WEIGHTS` (standard errors + p-values), Vertex AI Model Registry registration, endpoint serving, `EXPORT MODEL`.
- `Applied Forecasting/BQML Regression Based Forecasting.ipynb` — LINEAR_REG used for forecasting via lagged-feature design matrix; shows regression `ML.EVALUATE` columns and recursive vs. direct multi-step prediction.


---

### `BOOSTED_TREE_CLASSIFIER` / `BOOSTED_TREE_REGRESSOR`
- **Description:** Gradient-boosted decision tree ensembles trained with the [XGBoost](https://xgboost.readthedocs.io/) library. `BOOSTED_TREE_CLASSIFIER` handles binary and multiclass classification; `BOOSTED_TREE_REGRESSOR` handles regression. Boosting trains a sequence of trees where each tree learns the residual error of the prior ensemble. Setting `num_parallel_tree > 1` turns the model into a boosted random forest.
- **When to use:**
  - Structured/tabular data where high accuracy matters more than interpretability of a single equation.
  - Non-linear feature interactions that a linear/logistic model can't capture.
  - You want built-in per-prediction (local) and per-model (global) feature attributions for a tree model.
  - You want to export an XGBoost (`.bst`) artifact or auto-register the model to Vertex AI for online serving.
- **Category:** supervised-classification | supervised-regression.
- **Connection required:** No for training/eval/predict. A Cloud Storage URI (not a connection) is needed only for `EXPORT MODEL`; Vertex AI registration uses `MODEL_REGISTRY`/`VERTEX_AI_MODEL_ID` options, not a connection.
- **Status:** GA.
- **documentation:** [CREATE MODEL for boosted trees](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-boosted-tree). Journey-page group: [E2E user journey](https://cloud.google.com/bigquery/docs/e2e-journey) · [ML.EVALUATE](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-evaluate) · [ML.PREDICT](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-predict) · [ML.EXPLAIN_PREDICT](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-explain-predict) · [ML.GLOBAL_EXPLAIN](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-global-explain) · [ML.FEATURE_IMPORTANCE](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-importance).

**CREATE MODEL syntax:**
```sql
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.MODEL_NAME`
[TRANSFORM(...)]
OPTIONS(
  model_type = 'BOOSTED_TREE_CLASSIFIER',   -- or 'BOOSTED_TREE_REGRESSOR'
  input_label_cols = ['label_col'],
  booster_type = 'GBTREE',                  -- 'GBTREE' | 'DART'
  num_parallel_tree = 1,                    -- >1 => boosted random forest
  max_iterations = 30,
  tree_method = 'HIST',
  subsample = 0.85,
  early_stop = TRUE,
  min_rel_progress = 0.01,
  enable_global_explain = TRUE,
  auto_class_weights = TRUE                  -- classifier only
) AS
SELECT * EXCEPT(id_col) FROM `PROJECT_ID.DATASET.TABLE`;
```

**Options (model-specific):**

| Option | Type | Required | Default | Range / Values | Description |
|--------|------|----------|---------|----------------|-------------|
| `model_type` | STRING | Yes | — | `BOOSTED_TREE_CLASSIFIER`, `BOOSTED_TREE_REGRESSOR` | Selects classifier vs regressor. |
| `input_label_cols` | ARRAY\<STRING\> | No | `['label']` | column name(s) | Label column. Boosted trees support exactly one label column. |
| `booster_type` | STRING | No | `GBTREE` | `GBTREE`, `DART` | Booster. `HPARAM_CANDIDATES` eligible. |
| `num_parallel_tree` | INT64 | No | `1` | `>= 1` (`>=2` for forest) | Trees built per iteration; `>1` => boosted random forest. HP-tunable. |
| `dart_normalize_type` | STRING | No | `TREE` | `TREE`, `FOREST` | DART normalization; only valid when `booster_type='DART'`. Conditional HP candidate. |
| `dropout` | FLOAT64 | No | `0.0` | `[0.0, 1.0]` | DART dropout rate; only with `booster_type='DART'`. HP-tunable (conditional on DART). |
| `tree_method` | STRING | No | `AUTO` | `AUTO`, `EXACT`, `APPROX`, `HIST` | Tree construction algorithm. `AUTO` is the default (`HIST` is recommended for large data — fastest). |
| `max_iterations` | INT64 | No | `20` | `>= 1` | Max boosting rounds. HP-tunable (`HPARAM_RANGE`). |
| `max_tree_depth` | INT64 | No | `6` | `>= 1` | Max depth per tree. HP-tunable. |
| `min_tree_child_weight` | INT64 | No | `1` | `>= 0` | Min sum of instance weight in a child. HP-tunable. |
| `min_split_loss` | FLOAT64 | No | `0.0` | `>= 0` | Min loss reduction to split (gamma). HP-tunable. |
| `subsample` | FLOAT64 | No | `1.0` | `(0, 1]` | Row subsample ratio per tree. HP-tunable. |
| `colsample_bytree` | FLOAT64 | No | `1.0` | `(0, 1]` | Column subsample per tree. HP-tunable. |
| `colsample_bylevel` | FLOAT64 | No | `1.0` | `(0, 1]` | Column subsample per level. HP-tunable. |
| `colsample_bynode` | FLOAT64 | No | `1.0` | `(0, 1]` | Column subsample per node. HP-tunable. |
| `learn_rate` | FLOAT64 | No | `0.3` | `[0, 1]` | Boosting shrinkage/step size. HP-tunable. |
| `l1_reg` | FLOAT64 | No | `0.0` | `>= 0` | L1 regularization. HP-tunable. |
| `l2_reg` | FLOAT64 | No | `1.0` | `>= 0` | L2 regularization. HP-tunable. |
| `early_stop` | BOOL | No | `TRUE` | `TRUE`/`FALSE` | Stop when `min_rel_progress` not met. |
| `min_rel_progress` | FLOAT64 | No | `0.01` | `>= 0` | Min relative loss improvement to continue when `early_stop=TRUE`. |
| `auto_class_weights` | BOOL | No | `FALSE` | `TRUE`/`FALSE` | Classifier only. Balance class weights inversely to frequency (useful for imbalanced data). |
| `class_weights` | ARRAY\<STRUCT\<STRING,FLOAT64\>\> | No | — | per-class weights | Classifier only. Mutually exclusive with `auto_class_weights`. |
| `instance_weight_col` | STRING | No | — | column name | Per-row weight column. |
| `enable_global_explain` | BOOL | No | `FALSE` | `TRUE`/`FALSE` | Must be `TRUE` at training time to use `ML.GLOBAL_EXPLAIN`. |
| `approx_global_feature_contrib` | BOOL | No | TRUE when `enable_global_explain`=TRUE and `num_parallel_tree`\>=10, else FALSE | `TRUE`/`FALSE` | Use fast approximate global feature contributions (XGBoost passthrough); relevant for boosted random forests (`num_parallel_tree`\>1). |
| `xgboost_version` | STRING | No | `0.9` | `0.9`, `1.1` | XGBoost library version used for training. |
| `data_split_method` | STRING | No | `AUTO_SPLIT` | `AUTO_SPLIT`, `RANDOM`, `CUSTOM`, `SEQ`, `NO_SPLIT` | How to split train/eval data. |
| `data_split_col` | STRING | No | — | column name | With `CUSTOM`: `TRUE` rows => eval, `FALSE` => train. With `SEQ`: ordering column. |
| `num_trials` | INT64 | No | — | `1`–`100` | Enables hyperparameter tuning; total trials to run. |
| `max_parallel_trials` | INT64 | No | `1` | `1`–`5` | Concurrent tuning trials. |
| `hparam_tuning_objectives` | ARRAY\<STRING\> | No | type default | e.g. `ROC_AUC`, `R2_SCORE` | Metric(s) optimized during tuning. |
| `model_registry` | STRING | No | — | `VERTEX_AI` | Auto-register trained model to Vertex AI Model Registry. |
| `vertex_ai_model_id` / `vertex_ai_model_version_aliases` | STRING / ARRAY | No | — | — | Vertex AI model id and version aliases. |

(HP-tuning-eligible options accept `HPARAM_RANGE(min, max)` for numeric ranges or `HPARAM_CANDIDATES([...])` for discrete sets; `dart_normalize_type`/`dropout` are conditional on `booster_type` candidates including `DART`.)

**Supported lifecycle functions:** `ML.EVALUATE`, `ML.PREDICT`, `ML.EXPLAIN_PREDICT`, `ML.GLOBAL_EXPLAIN`, `ML.FEATURE_IMPORTANCE`, `ML.FEATURE_INFO`, `ML.TRAINING_INFO`, `EXPORT MODEL`. Classifier additionally: `ML.CONFUSION_MATRIX` and (binary) `ML.ROC_CURVE`. With `num_trials`: `ML.TRIAL_INFO`. Note: `ML.WEIGHTS`/`ML.ADVANCED_WEIGHTS` do **not** apply (tree models have no linear coefficients — use `ML.FEATURE_IMPORTANCE` instead).

**ML.EVALUATE output metrics (this type):**
- Classifier: `precision`, `recall`, `accuracy`, `f1_score`, `log_loss`, `roc_auc`.
- Regressor: `mean_absolute_error`, `mean_squared_error`, `mean_squared_log_error`, `median_absolute_error`, `r2_score`, `explained_variance`.

**Preprocessing support:** automatic by default; manual via the `TRANSFORM` clause (e.g. `ML.LABEL_ENCODER`, `ML.STANDARD_SCALER`, `ML.MIN_MAX_SCALER`, `ML.ROBUST_SCALER`, `ML.MAX_ABS_SCALER`, plus `EXTRACT()` on dates). `TRANSFORM` logic travels with the exported/registered model (preventing training-serving skew).

**Hyperparameter tuning:** Supported. Set `num_trials` (and optionally `max_parallel_trials`, `hparam_tuning_objectives`). Tunable options include `learn_rate`, `max_tree_depth`, `subsample`, `colsample_bytree`/`bylevel`/`bynode`, `min_split_loss`, `min_tree_child_weight`, `l1_reg`, `l2_reg`, `max_iterations`, `num_parallel_tree`, `booster_type`, and (conditional on DART) `dart_normalize_type`/`dropout`.

**Explainability / weights:** `ML.EXPLAIN_PREDICT` (local, per-row top feature attributions — tree SHAP based), `ML.GLOBAL_EXPLAIN` (requires `enable_global_explain=TRUE` at training), and `ML.FEATURE_IMPORTANCE` (XGBoost `importance_weight`/`importance_gain`/`importance_cover`). `ML.WEIGHTS`/`ML.ADVANCED_WEIGHTS` are N/A.

**Best practices:**
- Use `tree_method='HIST'` for large datasets (much faster).
- For imbalanced classification set `auto_class_weights=TRUE` (the fraud notebook uses it on a ~0.17% positive class).
- Keep `early_stop=TRUE` with a sensible `min_rel_progress` to avoid over-training and wasted slots.
- Set `enable_global_explain=TRUE` at training if you'll need global attributions — it can't be added afterward.
- Watch cost: boosted-tree training scans/processes data per iteration (the fraud run processed ~16.8 GB); HP tuning multiplies this by `num_trials`.

**Limitations:**
- Exactly one label column; no multi-label.
- `ML.WEIGHTS`/`ML.ADVANCED_WEIGHTS` unavailable (no linear coefficients).
- DART-only options (`dart_normalize_type`, `dropout`) are ignored unless `booster_type='DART'`.
- Training is not available in every region — see Locations.

**Locations:** Boosted-tree training is not supported in all BigQuery ML regions/multi-regions; check the [BigQuery ML locations](https://cloud.google.com/bigquery/docs/locations) list. Vertex AI registration defaults to the region matching the BQ location (e.g. `EU` multi-region maps to `europe-west4`).

**BigFrames API:** `bigframes.ml.ensemble.XGBClassifier` / `bigframes.ml.ensemble.XGBRegressor` — `model = XGBClassifier(); model.fit(X, y); model.predict(X)`. **Verified: the constructor has no `class_weight`/`auto_class_weights` parameter** (checked the installed signature directly — `n_estimators`, `booster`, `max_depth`, `learning_rate`, `reg_alpha`/`reg_lambda`, etc., but no class-weighting option), unlike `bigframes.ml.linear_model.LogisticRegression` which exposes sklearn-style `class_weight`. A BigFrames `XGBClassifier` trained on an imbalanced label with no manual reweighting will not match a SQL `BOOSTED_TREE_CLASSIFIER` trained with `auto_class_weights = TRUE` — expect higher precision / lower recall from the unweighted BigFrames model, not a bug.

**Repo example (tested):**
- `/home/user/git/vertex-ai-mlops/data+ai/bq-ml/models/boosted_tree_classifier/boosted_tree_classifier.sql` + notebook — `BOOSTED_TREE_CLASSIFIER` on `census_adult_income` (same data/label as `models/logistic_regression/`, for direct technique comparison), with the full lifecycle incl. the tree-visualization step (`EXPORT MODEL` → `xgboost.plot_tree()`).
- `/home/user/git/vertex-ai-mlops/data+ai/bq-ml/models/boosted_tree_regressor/boosted_tree_regressor.sql` + notebook — `BOOSTED_TREE_REGRESSOR` on `penguins`/`body_mass_g` (same data/label as `models/linear_regression/`); `r2_score` 0.968 vs. linear regression's 0.875 on identical data. `TRANSFORM` uses `ML.LABEL_ENCODER`. Same tree-visualization step; confirmed the extra `reg:linear` deprecation warning on load (regressor-specific, see gotcha above).
- `/home/user/git/vertex-ai-mlops/03 - BigQuery ML (BQML)/03b - BQML Boosted Trees.ipynb` — `BOOSTED_TREE_CLASSIFIER` on imbalanced fraud data with `auto_class_weights`, `data_split_method='CUSTOM'`, `enable_global_explain`, Vertex AI registration; then `ML.EVALUATE`, `ML.CONFUSION_MATRIX`, `ML.ROC_CURVE`, `ML.PREDICT`, `ML.EXPLAIN_PREDICT`, `ML.GLOBAL_EXPLAIN`, `ML.FEATURE_IMPORTANCE`, `EXPORT MODEL` (produces `model.bst` XGBoost artifact), and Vertex AI Endpoint serving.
- `/home/user/git/vertex-ai-mlops/03 - BigQuery ML (BQML)/BQML Feature Engineering - Create Model With Transpose.ipynb` — `BOOSTED_TREE_REGRESSOR` with an inline `TRANSFORM` clause (`ML.LABEL_ENCODER`, scalers, date `EXTRACT`), `num_parallel_tree=25`, `l1_reg`/`l2_reg`; shows `TRANSFORM` traveling into the exported `/model` + `/model/transform` artifacts and Vertex AI serving.


---

### `RANDOM_FOREST_CLASSIFIER` / `RANDOM_FOREST_REGRESSOR`
- **Description:** Bagged ensemble of decision trees, trained with the XGBoost library (a "boosted random forest": `num_parallel_tree` trees built in parallel per iteration, on row + column subsamples drawn with replacement). `RANDOM_FOREST_CLASSIFIER` predicts a categorical label (binary or multiclass); `RANDOM_FOREST_REGRESSOR` predicts a numeric value. Distinct from `BOOSTED_TREE_*` (which sequentially boosts) — random forest sets `num_parallel_tree >= 2` and trains a single iteration.
- **When to use:**
  - Tabular classification/regression where you want a robust, low-tuning ensemble that resists overfitting via bagging.
  - When you need built-in feature attributions (`ML.GLOBAL_EXPLAIN`, `ML.EXPLAIN_PREDICT`) and XGBoost feature importances.
  - Mixed numeric + categorical features with automatic preprocessing, or custom preprocessing via `TRANSFORM`.
  - As a variance-reduction alternative to a single tree or to `BOOSTED_TREE_*` when boosting overfits.
- **Category:** supervised-classification | supervised-regression.
- **Connection required:** No. (A Cloud connection is only needed for the optional `MODEL_REGISTRY = 'VERTEX_AI'` registration / online serving step, not for training, evaluation, or `ML.PREDICT`.)
- **Status:** GA.
- **documentation:** [CREATE MODEL for random forest models](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-random-forest) · related: [boosted tree CREATE MODEL](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-boosted-tree) (shared XGBoost option set) · [XAI overview](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-xai-overview) · [HP tuning overview](https://cloud.google.com/bigquery/docs/hp-tuning-overview)

**CREATE MODEL syntax:**
```sql
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.MODEL_NAME`
[TRANSFORM(
  ML.STANDARD_SCALER(feature1) OVER() AS feature1,
  ML.IMPUTER(cat_feature, 'most_frequent') OVER() AS cat_feature,
  label_col
)]
OPTIONS(
  model_type = 'RANDOM_FOREST_CLASSIFIER',   -- or 'RANDOM_FOREST_REGRESSOR'
  input_label_cols = ['label_col'],
  num_parallel_tree = 100,                    -- >= 2 for random forest
  tree_method = 'HIST',
  subsample = 0.85,
  colsample_bytree = 0.9,
  auto_class_weights = TRUE,                  -- classifier only
  enable_global_explain = TRUE,
  data_split_method = 'AUTO_SPLIT'
) AS
SELECT * EXCEPT(id_col)
FROM `PROJECT_ID.DATASET.TRAINING_TABLE`;
```

**Options (model-specific):**

| Option | Type | Required | Default | Range / Values | Description |
|--------|------|----------|---------|----------------|-------------|
| `model_type` | STRING | Yes | — | `RANDOM_FOREST_CLASSIFIER`, `RANDOM_FOREST_REGRESSOR` | Selects classification vs regression. |
| `input_label_cols` | ARRAY\<STRING\> | No | `['label']` | column name(s) | Label column(s) in the training query. |
| `num_parallel_tree` | INT64 | No | 100 | \>= 2 (or `HPARAM_RANGE`/`HPARAM_CANDIDATES`) | Trees built in parallel per iteration; this is what makes it a forest. |
| `tree_method` | STRING | No | `AUTO` | `AUTO`, `EXACT`, `APPROX`, `HIST` | XGBoost split-finding algorithm; `HIST` is fastest on large data. |
| `subsample` | FLOAT64 | No | 0.8 (RF) | (0, 1.0] (or HP range) | Row subsample ratio per tree (bagging). |
| `colsample_bytree` | FLOAT64 | No | 1.0 | [0, 1.0] (or HP range) | Column subsample ratio per tree. |
| `colsample_bylevel` | FLOAT64 | No | 1.0 | [0, 1.0] (or HP range) | Column subsample ratio per depth level. |
| `colsample_bynode` | FLOAT64 | No | 0.8 (RF) | [0, 1.0] (or HP range) | Column subsample ratio per split node. |
| `max_tree_depth` | INT64 | No | 6 | (or `HPARAM_RANGE`/`HPARAM_CANDIDATES`) | Max depth of each tree. |
| `min_tree_child_weight` | INT64 | No | 1 | \>= 0 (or HP) | Min sum of instance weight in a child to keep splitting. |
| `min_split_loss` | FLOAT64 | No | 0 | \>= 0 (or HP) | Min loss reduction (gamma) required to split. |
| `l1_reg` | FLOAT64 | No | 0 | \>= 0 (or HP) | L1 regularization on weights. |
| `l2_reg` | FLOAT64 | No | 1.0 | \>= 0 (or HP) | L2 regularization on weights. |
| `auto_class_weights` | BOOL | No | FALSE | TRUE / FALSE | Classifier only: balance classes by inverse frequency. |
| `class_weights` | ARRAY\<STRUCT\<STRING,FLOAT64\>\> | No | — | per-class weights | Classifier only; mutually exclusive with `auto_class_weights`. |
| `instance_weight_col` | STRING | No | — | column name | Per-row weight column. |
| `enable_global_explain` | BOOL | No | FALSE | TRUE / FALSE | Required to use `ML.GLOBAL_EXPLAIN` / `ML.EXPLAIN_PREDICT`. |
| `approx_global_feature_contrib` | BOOL | No | TRUE when `enable_global_explain`=TRUE and `num_parallel_tree`\>=10, else FALSE | TRUE / FALSE | Fast approximate feature contributions (XGBoost passthrough). |
| `category_encoding_method` | STRING | No | `LABEL_ENCODING` | `LABEL_ENCODING`, `DUMMY_ENCODING` | Encoding for non-numeric features. |
| `data_split_method` | STRING | No | `AUTO_SPLIT` | `AUTO_SPLIT`, `RANDOM`, `CUSTOM`, `SEQ`, `NO_SPLIT` | How eval data is held out. |
| `data_split_col` | STRING | No | — | column name | With `CUSTOM`: BOOL col (TRUE=eval); with `SEQ`: ordering col. |
| `data_split_eval_fraction` | FLOAT64 | No | 0.2 | [0, 1.0] | Eval fraction for `RANDOM`/`SEQ`. |
| `early_stop` | BOOL | No | TRUE | TRUE / FALSE | Stop early on small relative progress. |
| `min_rel_progress` | FLOAT64 | No | 0.01 | \>= 0 | Min relative loss improvement when `early_stop`=TRUE. |
| `num_trials` | INT64 | No | — | \>= 1 | Enables hyperparameter tuning (number of trials). |
| `model_registry` | STRING | No | — | `VERTEX_AI` | Register the trained model in Vertex AI Model Registry. |

(HP-tuning-eligible options accept `HPARAM_RANGE(min, max)` or `HPARAM_CANDIDATES([...])`: `num_parallel_tree`, `tree_method`, `subsample`, `colsample_bytree`/`bylevel`/`bynode`, `max_tree_depth`, `min_tree_child_weight`, `min_split_loss`, `l1_reg`, `l2_reg`.)

**Supported lifecycle functions:** `ML.PREDICT`, `ML.EVALUATE`, `ML.CONFUSION_MATRIX` (classifier), `ML.ROC_CURVE` (binary classifier), `ML.EXPLAIN_PREDICT` (needs `enable_global_explain`), `ML.GLOBAL_EXPLAIN` (needs `enable_global_explain`), `ML.FEATURE_IMPORTANCE`, `ML.FEATURE_INFO`, `ML.TRAINING_INFO`, `ML.TRIAL_INFO` (when `num_trials` set), `EXPORT MODEL`, `ALTER MODEL`, `ML.VALIDATE_DATA_SKEW` / `ML.VALIDATE_DATA_DRIFT` (monitoring). Note: `ML.WEIGHTS` / `ML.ADVANCED_WEIGHTS` do **not** apply (tree model, not linear) — use `ML.FEATURE_IMPORTANCE` / `ML.GLOBAL_EXPLAIN` instead.

**ML.EVALUATE output metrics (this type):**
- Classifier: `precision`, `recall`, `accuracy`, `f1_score`, `log_loss`, `roc_auc`.
- Regressor: `mean_absolute_error`, `mean_squared_error`, `mean_squared_log_error`, `median_absolute_error`, `r2_score`, `explained_variance`.

**Preprocessing support:** automatic (BQML auto-preprocessing for numeric + categorical) | manual | `TRANSFORM` supported (preprocessing baked into the model so it is reapplied at predict time — see monitoring SQL example using `ML.ROBUST_SCALER`, `ML.STANDARD_SCALER`, `ML.QUANTILE_BUCKETIZE`, `ML.IMPUTER`).

**Hyperparameter tuning:** Supported. Set `num_trials` (and optionally `max_parallel_trials`, `hparam_tuning_algorithm`, `hparam_tuning_objectives`). Tunable options listed above. Default tuning objective: `roc_auc` (classifier), `r2_score` (regressor). Inspect trials with `ML.TRIAL_INFO`.

**Explainability / weights:** `ML.GLOBAL_EXPLAIN` (global feature attributions) and `ML.EXPLAIN_PREDICT` (per-row attributions) — both require `enable_global_explain = TRUE` at training time. `ML.FEATURE_IMPORTANCE` returns XGBoost `importance_weight` (split count), `importance_gain` (accuracy gain), `importance_cover` (rows covered) and needs no special option. `ML.WEIGHTS` / `ML.ADVANCED_WEIGHTS` are N/A for tree models.

**Best practices:**
- With `enable_global_explain=TRUE`, forests of `num_parallel_tree` >= 10 automatically use fast approximate global feature contributions (`approx_global_feature_contrib`); larger forests reduce variance at higher train cost/time.
- Use `tree_method = 'HIST'` for large tables (the repo fraud example trained 200 trees on ~9.4 GB in ~25 min).
- For imbalanced classification (e.g. fraud), set `auto_class_weights = TRUE`.
- Use `subsample` + `colsample_*` < 1.0 to strengthen bagging and generalization.
- Bake preprocessing into `TRANSFORM` so serving and monitoring reuse identical logic.
- **For tree visualization (`EXPORT MODEL` → `xgboost.plot_tree()`), train a small, separate illustrative forest** (e.g. `num_parallel_tree=10`, `max_tree_depth=3`) rather than trying to render a tree from your full-power model — see the limitation below.
- On a small dataset, random forest can genuinely underperform boosted trees (or even a GLM) — **verified**: `RANDOM_FOREST_REGRESSOR` on `penguins`/`body_mass_g` (333 rows) reached only `r2_score ≈ 0.74` (≈ 0.76 best-tuned) vs. `BOOSTED_TREE_REGRESSOR`'s ≈ 0.97 and `LINEAR_REG`'s ≈ 0.88 on identical data. Don't assume random forest is always the stronger tree ensemble — bagging's variance reduction needs enough data to pay off.

**Limitations:**
- Random forest training is **not available in all regions** — check BigQuery ML locations before choosing a dataset region.
- `ML.WEIGHTS` does not apply (no linear coefficients).
- Explainability functions require `enable_global_explain = TRUE` set at training; cannot be added afterward without retraining.
- `ML.ROC_CURVE` is binary-classification only.
- **Verified: `max_iterations` is not a valid option for `RANDOM_FOREST_CLASSIFIER`/`RANDOM_FOREST_REGRESSOR` at all** — `CREATE MODEL` errors immediately with `Option(s) MAX_ITERATIONS are not supported for RANDOM_FOREST_* model training` if you set it (unlike `BOOSTED_TREE_*`, where `max_iterations` is a central hyperparameter). This is a hard API-level guarantee that random forest training is single-pass, not just a documented convention — there is no way to accidentally train a "boosted random forest" via this option; `num_parallel_tree` alone defines the forest. Confirmed by `ML.TRAINING_INFO`: always exactly one row (`iteration = 1`), `learning_rate = 1.0`.
- **Verified gotcha — trees are too dense to visualize at default settings.** Unlike a `BOOSTED_TREE_*` tree (a shallow stage fit on residuals), *every* `RANDOM_FOREST_*` tree is a complete, independently-trained tree. A default-settings forest's tree 0 (`num_parallel_tree=50`, `max_tree_depth=6`) had 2,435 dump lines and depth 15 — `xgboost.plot_tree()` triggers `graph is too large for cairo-renderer bitmaps` and produces an illegible image (confirmed even with SVG output, which sidesteps the bitmap-size limit but is still too dense to read at a glance). Fix: train a dedicated shallow illustrative forest for the diagram only (see best practices above).
- With heavy default column subsampling (`colsample_bynode = 0.8`) over a small feature set, some features can end up with **zero** `ML.FEATURE_IMPORTANCE`/`ML.GLOBAL_EXPLAIN` — verified on the 6-feature `penguins` regressor (`island`, `culmen_length_mm` both zero, reproduced identically across two independent runs). Not a bug; a real effect of bagging variance when there are few features relative to `colsample_bynode`.
- **Verified: retraining an identical `RANDOM_FOREST_*` model (same query, same options) is genuinely non-deterministic** — unlike `BOOSTED_TREE_*` (which reproduced predictions/loss curves essentially bit-for-bit across separate runs in testing, since it doesn't subsample by default), random forest always bags row/column subsamples (`subsample`/`colsample_bynode` default to 0.8, not 1.0), and there is no exposed random seed. Observed on `penguins`: two separate trainings of the same `RANDOM_FOREST_REGRESSOR` config produced visibly different tree structures, predictions, and `ML.GLOBAL_EXPLAIN` rankings (though `r2_score` stayed in a similar range, ~0.74–0.75). Don't expect exact reproducibility run-to-run the way GLMs or boosted trees (mostly) provide.

**Locations:** Subject to region restrictions (random forest not supported in every BQML region/multi-region); see [BigQuery ML locations](https://cloud.google.com/bigquery/docs/locations).

**BigFrames API:** `bigframes.ml.ensemble.RandomForestClassifier` / `bigframes.ml.ensemble.RandomForestRegressor` — `.fit(X, y)` / `.predict()` / `.score()`; integrates with `bigframes.ml.pipeline` for TRANSFORM-equivalent preprocessing. **Verified: `RandomForestClassifier` has no `class_weight`/`auto_class_weights` parameter** (checked the installed signature directly — same gap as `XGBClassifier`), unlike `LogisticRegression`. A BigFrames comparison against a SQL model trained with `auto_class_weights = TRUE` is not apples-to-apples.

**Repo example (tested):**
- `/home/user/git/vertex-ai-mlops/data+ai/bq-ml/models/random_forest_classifier/random_forest_classifier.sql` + notebook — `RANDOM_FOREST_CLASSIFIER` on `census_adult_income` (same data/label as `logistic_regression`/`boosted_tree_classifier`, for a three-way technique comparison), incl. a dedicated shallow illustrative forest for tree visualization.
- `/home/user/git/vertex-ai-mlops/data+ai/bq-ml/models/random_forest_regressor/random_forest_regressor.sql` + notebook — `RANDOM_FOREST_REGRESSOR` on `penguins`/`body_mass_g` (same data/label as `linear_regression`/`boosted_tree_regressor`); the `r2_score ≈ 0.74` underperformance vs. boosting is discussed directly in the notebook as a genuine finding.
- `/home/user/git/vertex-ai-mlops/03 - BigQuery ML (BQML)/03c - BQML Random Forest.ipynb` — full `RANDOM_FOREST_CLASSIFIER` workflow on the credit-card fraud table: `CREATE MODEL` with `num_parallel_tree=200`, `tree_method='HIST'`, `subsample=0.85`, `colsample_bytree=0.9`, `auto_class_weights=TRUE`, `enable_global_explain=TRUE`, `CUSTOM` split via a derived BOOL column; then `ML.FEATURE_INFO`, `ML.TRAINING_INFO`, `ML.EVALUATE`, `ML.CONFUSION_MATRIX`, `ML.ROC_CURVE`, `ML.PREDICT`, `ML.EXPLAIN_PREDICT`, `ML.GLOBAL_EXPLAIN`, `ML.FEATURE_IMPORTANCE`, Vertex AI registration + endpoint serving, and `EXPORT MODEL` (exports an XGBoost `model.bst`).
- `/home/user/git/vertex-ai-mlops/MLOps/Model Monitoring/model_monitoring_job.sql` — `RANDOM_FOREST_CLASSIFIER` with `TRANSFORM(...)` preprocessing, `AUTO_CLASS_WEIGHTS=FALSE`, `NUM_PARALLEL_TREE=150`, used as the monitored/retrained model with `ML.VALIDATE_DATA_SKEW`, `ML.VALIDATE_DATA_DRIFT`, and `ML.EVALUATE` (reads `accuracy`).


---

### `DNN_CLASSIFIER` / `DNN_REGRESSOR`
- **Description:** Deep neural network models trained with TensorFlow inside BigQuery. Fully-connected feed-forward networks with one or more hidden layers, capturing non-linear relationships between features and the label. `DNN_CLASSIFIER` does binary or multiclass classification; `DNN_REGRESSOR` predicts a continuous numeric value.
- **When to use:**
  - Non-linear feature/label relationships that linear or tree models underfit.
  - Medium-to-large structured/tabular data where extra capacity (depth/width) helps.
  - You want built-in feature attributions (Integrated Gradients) and easy Vertex AI Model Registry export for online serving.
  - Prefer Boosted Tree or AutoML first for most tabular tasks; reach for DNN when you specifically want a neural net or need TensorFlow export artifacts.
- **Category:** supervised-classification | supervised-regression.
- **Connection required:** No (in-BigQuery training). A connection is only relevant for downstream `EXPORT MODEL` to GCS or Vertex AI serving, not for training/eval/predict.
- **Status:** GA.
- **documentation:** [CREATE MODEL for DNN models](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-dnn-models) · journey-page group: [E2E model journey](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-e2e-journey), [XAI overview](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-xai-overview), [HP tuning](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-hp-tuning-overview).

**CREATE MODEL syntax:**
```sql
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.MODEL_NAME`
[TRANSFORM(ML.STANDARD_SCALER(Amount) OVER() AS Amount, * EXCEPT(Amount))]
OPTIONS(
  model_type = 'DNN_CLASSIFIER',         -- or 'DNN_REGRESSOR'
  input_label_cols = ['label'],
  hidden_units = [64, 32],
  activation_fn = 'RELU',
  optimizer = 'ADAGRAD',
  learn_rate = 0.01,
  batch_size = 100,
  dropout = 0.15,
  max_iterations = 20,
  early_stop = TRUE,
  auto_class_weights = FALSE,            -- classifier only
  enable_global_explain = TRUE,
  integrated_gradients_num_steps = 30,
  data_split_method = 'AUTO_SPLIT'
) AS
SELECT * EXCEPT(id) FROM `PROJECT_ID.DATASET.TRAINING_TABLE`;
```

**Options (model-specific):**

| Option | Type | Required | Default | Range / Values | Description |
|--------|------|----------|---------|----------------|-------------|
| `model_type` | STRING | Yes | — | `DNN_CLASSIFIER`, `DNN_REGRESSOR` | Algorithm to train. |
| `input_label_cols` | ARRAY\<STRING\> | No | `['label']` | column name(s) | Label column(s). |
| `hidden_units` | ARRAY\<INT64\> | No | single layer, auto-sized (\<=128 units) | e.g. `[128,64,32]` | Units per fully-connected hidden layer; array length = number of layers. Tunable via `HPARAM_CANDIDATES` only (`ARRAY<STRUCT<ARRAY<INT64>>>`). |
| `activation_fn` | STRING | No | `RELU` | `RELU`,`RELU6`,`CRELU`,`ELU`,`SELU`,`SIGMOID`,`TANH` | Hidden-layer activation. Tunable (`HPARAM_CANDIDATES`). |
| `optimizer` | STRING | No | `ADAM` | `ADAGRAD`,`ADAM`,`FTRL`,`RMSPROP`,`SGD` | Gradient optimizer. Tunable (`HPARAM_CANDIDATES`). |
| `learn_rate` | FLOAT64 | No | `0.001` | \>0 | Step size. Tunable (`HPARAM_RANGE`/`HPARAM_CANDIDATES`). |
| `batch_size` | INT64 | No | auto (\<=1024) | \>0 | Mini-batch size. Tunable. |
| `dropout` | FLOAT64 | No | `0` | [0,1) | Per-coordinate drop probability (regularization). Tunable. |
| `max_iterations` | INT64 | No | `20` | \>0 | Max training iterations (epochs). Tunable. |
| `early_stop` | BOOL | No | `TRUE` | TRUE/FALSE | Stop when `min_rel_progress` not met. |
| `min_rel_progress` | FLOAT64 | No | `0.01` | \>0 | Min relative loss improvement to continue when `early_stop=TRUE`. |
| `l1_reg` | FLOAT64 | No | `0` | \>=0 | L1 regularization. Tunable. |
| `l2_reg` | FLOAT64 | No | `0` | \>=0 | L2 regularization. Tunable. |
| `warm_start` | BOOL | No | `FALSE` | TRUE/FALSE | Retrain from existing weights (same feature schema). |
| `auto_class_weights` | BOOL | No | `FALSE` | TRUE/FALSE | Classifier only: balance classes by inverse frequency. |
| `class_weights` | STRUCT array | No | — | per-label weights | Classifier only: manual class weights (mutually exclusive with `auto_class_weights`). |
| `data_split_method` | STRING | No | `AUTO_SPLIT` | `AUTO_SPLIT`,`RANDOM`,`CUSTOM`,`SEQ`,`NO_SPLIT` | Train/eval split strategy. |
| `data_split_col` | STRING | No | — | column name | With `CUSTOM` (BOOL: TRUE=eval) or `SEQ`; column excluded from features. |
| `data_split_eval_fraction` | FLOAT64 | No | `0.2` | [0,1) | Eval fraction for `RANDOM`/`SEQ`. |
| `enable_global_explain` | BOOL | No | `FALSE` | TRUE/FALSE | Required to use `ML.GLOBAL_EXPLAIN`; enables Integrated Gradients attributions. |
| `integrated_gradients_num_steps` | INT64 | No | `25` | \>0 | Steps for Integrated Gradients attribution. |
| `num_trials` | INT64 | No | — | \<=100 | Enables HP tuning (max trials). |
| `max_parallel_trials` | INT64 | No | `1` | — | Trials run concurrently. |
| `hparam_tuning_algorithm` | STRING | No | `VIZIER_DEFAULT` | `VIZIER_DEFAULT`,`RANDOM_SEARCH`,`GRID_SEARCH` | Search strategy for tuning. |
| `hparam_tuning_objectives` | ARRAY\<STRING\> | No | classifier `ROC_AUC`, regressor `R2_SCORE` | metric names | Objective(s) to optimize during tuning. |
| `model_registry` | STRING | No | — | `VERTEX_AI` | Auto-register to Vertex AI Model Registry. |
| `vertex_ai_model_id` / `vertex_ai_model_version_aliases` | STRING / ARRAY\<STRING\> | No | — | — | Registry model id / version aliases. |

**Supported lifecycle functions:** `ML.EVALUATE`, `ML.PREDICT`, `ML.TRAINING_INFO`, `ML.FEATURE_INFO`, `ML.EXPLAIN_PREDICT` (local attributions), `ML.GLOBAL_EXPLAIN` (requires `enable_global_explain=TRUE`), `ML.CONFUSION_MATRIX` (classifier only), `ML.ROC_CURVE` (binary classifier only), `EXPORT MODEL` (TensorFlow SavedModel). With HP tuning: `ML.TRIAL_INFO`. NOT supported: `ML.WEIGHTS`/`ML.ADVANCED_WEIGHTS` (no coefficient weights for DNNs — use the explain functions), `ML.FEATURE_IMPORTANCE` (tree-only).

**ML.EVALUATE output metrics:**
- **DNN_CLASSIFIER:** `precision`, `recall`, `accuracy`, `f1_score`, `log_loss`, `roc_auc` (verified in repo notebook).
- **DNN_REGRESSOR:** `mean_absolute_error`, `mean_squared_error`, `mean_squared_log_error`, `median_absolute_error`, `r2_score`, `explained_variance`.

**Preprocessing support:** Automatic (standardization of numeric features, one-hot of categoricals) happens internally; `TRANSFORM` clause IS supported and recommended for explicit feature engineering (e.g. `ML.STANDARD_SCALER`). Normalizing numeric inputs materially helps gradient-based training.

**Hyperparameter tuning:** Supported. Tunable options: `hidden_units` (HPARAM_CANDIDATES only — `ARRAY<STRUCT<ARRAY<INT64>>>`), `activation_fn`, `optimizer` (HPARAM_CANDIDATES), and `learn_rate`, `batch_size`, `dropout`, `l1_reg`, `l2_reg`, `max_iterations` (HPARAM_RANGE or HPARAM_CANDIDATES). Set `num_trials` to enable; tune objective via `hparam_tuning_objectives`.

**Explainability / weights:** `ML.EXPLAIN_PREDICT` (per-row Integrated Gradients attributions, `top_k_features` STRUCT param) and `ML.GLOBAL_EXPLAIN` (model-wide attributions; needs `enable_global_explain=TRUE`). `ML.WEIGHTS`/`ML.ADVANCED_WEIGHTS` and `ML.FEATURE_IMPORTANCE` do NOT apply.

**Best practices:**
- Set `enable_global_explain=TRUE` at train time — it cannot be added later without retraining.
- Normalize numeric features (TRANSFORM + `ML.STANDARD_SCALER`) — good general practice, but verified **not sufficient on its own** for small datasets (see the limitation below); don't assume scaling alone fixes a badly-converging small-data DNN.
- For imbalanced classification use `auto_class_weights=TRUE` (or `class_weights`); the repo fraud example trains with it FALSE and still achieves strong ROC AUC. Verified separately: even with unscaled numeric inputs and no scaling, a `DNN_CLASSIFIER` can still reach a competitive `roc_auc` — classification loss surfaces tolerate unscaled features far better than regression does.
- Training is expensive: the repo run trained ~937s over ~16.7 GB processed for `[64,32]` / 10 iterations — start small and use `early_stop`. Verified independently in `models/dnn_classifier/`/`models/dnn_regressor/`: a single `CREATE MODEL` took 12-46 minutes even on small training sets (~32K and 333 rows) — the per-iteration cost itself is small (~20-45s), so most of this is fixed DNN-worker startup overhead, not data volume.
- Wrapping `TRANSFORM` keeps preprocessing baked into `ML.PREDICT`/serving so inference matches training.
- `hidden_units` HP tuning syntax, verified working: `hidden_units = HPARAM_CANDIDATES([STRUCT([64, 32]), STRUCT([32, 16])])` — each candidate is a `STRUCT` wrapping a whole layer-sizes array.

**Limitations:**
- Exported/trained model size limit ~256 MB.
- DNN training is NOT available in all regions/multi-regions — check BigQuery ML locations.
- No coefficient weights; rely on Integrated Gradients explanations.
- `hidden_units` tuning only via `HPARAM_CANDIDATES` (not `HPARAM_RANGE`).
- `class_weights` and `auto_class_weights` are mutually exclusive and classifier-only.
- **Small datasets can silently fail to converge (verified, important):** on a 333-row regression dataset, the default `learn_rate=0.001` combined with `early_stop=TRUE` (default) caused training to stop after only **2 iterations**, producing a badly broken model (`r2_score≈-27.5`, far worse than predicting the mean) — with no error, warning, or job failure. Scaling the numeric features with `ML.STANDARD_SCALER` did **not** fix this (`r2_score` still ≈-27.4) — the binding constraint was the learn rate, not feature scale. Raising `learn_rate` well above default (0.05, i.e. 50x) plus more `max_iterations` headroom fixed it (`r2_score≈0.86`, verified reproducible bit-for-bit across separate retrains — see the `ML.TRIAL_INFO` gotcha below on why). Takeaway: always check `ML.TRAINING_INFO` for the actual iteration count on small data — if `early_stop` triggers after only 1-2 iterations, don't trust the resulting metrics without first trying a substantially higher `learn_rate`.
- **DNN training itself — not just HP tuning — reproduces bit-for-bit across separate retrains of the same model name (verified across three full runs of `models/dnn_regressor/`):** the baseline model's `ML.EVALUATE` (`r2_score = -27.351799`) and `ML.TRAINING_INFO` loss curve, the scaled+higher-learn-rate fix model's `ML.EVALUATE` (`r2_score = 0.861626`), and the tuned model's `ML.TRIAL_INFO` (identical sampled `learn_rate` values to 17 significant digits, same optimal trial) all matched exactly across independent `CREATE OR REPLACE MODEL` calls under the same name, with no explicit seed set anywhere. A separate ad-hoc validation model with a *different* name but the identical tuning search-space config (`HPARAM_RANGE(0.001, 0.1)`, `num_trials=4`) explored a completely different, worse set of `learn_rate` values (0.001-0.008) and stayed stuck at the catastrophic `r2_score≈-27` baseline. Practical implication: don't expect variation across reruns of the identical `CREATE OR REPLACE MODEL` statement under a fixed name (evaluation metrics, loss curves, and tuning trials will all reproduce) — but don't assume a result (good or bad) will transfer if you rename or duplicate the statement, since a different model name can follow a different training/search trajectory. The exact mechanism (e.g. a deterministic `AUTO_SPLIT` hash and/or a Vizier study ID derived from the model's resource path) isn't confirmed, only the practical behavior.

**Locations:** Subject to the BigQuery ML locations list for DNN training (more restricted than basic models). Confirm region support before training.

**BigFrames API:** Verified (checked the live BigFrames API reference across every `bigframes.ml` module — `linear_model`, `ensemble`, `cluster`, `decomposition`, `forecasting`, `imported`, `llm`): **no first-class DNN/neural-network class exists anywhere in `bigframes.ml`**. This is a permanent gap, not a version-specific omission. `bigframes.ml.imported.TensorFlowModel` only *serves* an already-trained external TensorFlow model — it does not train a BQML `DNN_CLASSIFIER`/`DNN_REGRESSOR`. Use the SQL `CREATE MODEL` interface directly; there is no BigFrames comparison path for this model type.

**Repo example (tested):** `/home/user/git/vertex-ai-mlops/03 - BigQuery ML (BQML)/03d - BQML Deep Neural Network (DNN).ipynb` — end-to-end `DNN_CLASSIFIER` on the credit-card fraud table (`hidden_units=[64,32]`, `optimizer='SGD'`, `dropout=0.15`, `CUSTOM` split via a derived BOOL `custom_splits` column, `enable_global_explain=TRUE`, Vertex AI registry), covering `ML.TRAINING_INFO`, `ML.FEATURE_INFO`, `ML.EVALUATE`, `ML.CONFUSION_MATRIX`, `ML.ROC_CURVE`, `ML.PREDICT`, `ML.EXPLAIN_PREDICT`, `ML.GLOBAL_EXPLAIN`, `EXPORT MODEL`, and Vertex AI Endpoint serving. Also see this project's own `models/dnn_classifier/` and `models/dnn_regressor/` for a from-scratch, fully pre-validated build on the same comparison datasets used by every other model type in this project.


---

### `DNN_LINEAR_COMBINED_CLASSIFIER` / `DNN_LINEAR_COMBINED_REGRESSOR`  (Wide-and-Deep)

- **Description:** Jointly trained neural network combining a *wide* linear model (memorizes feature interactions / sparse categorical patterns) with a *deep* DNN (generalizes). Built on TensorFlow inside BigQuery ML. `DNN_LINEAR_COMBINED_CLASSIFIER` handles binary and multiclass classification; `DNN_LINEAR_COMBINED_REGRESSOR` handles regression.
- **When to use:**
  - Large, sparse categorical features (high-cardinality IDs) common in ranking and recommendation problems.
  - You want both memorization of specific feature combinations and generalization to unseen ones.
  - Tabular problems where a plain DNN underfits sparse signals but linear-only underfits interactions.
  - You need a TensorFlow SavedModel artifact (exportable, deployable to Vertex AI) trained from SQL.
- **Category:** supervised-classification | supervised-regression.
- **Connection required:** No (training/eval/predict run natively in BigQuery). A connection is only needed for unrelated remote/imported models, not for this type. Vertex AI Model Registry registration and `EXPORT MODEL` to GCS need the usual IAM, not a BigQuery connection.
- **Status:** GA.
- **documentation:** [CREATE MODEL for Wide-and-Deep models](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-wnd-models) · journey: [E2E user journey for models](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-e2e-journey) · [XAI overview](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-xai-overview) · [Hyperparameter tuning](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-hyperparameter-tuning)

**CREATE MODEL syntax:**
```sql
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.MODEL_NAME`
[TRANSFORM(...)]
OPTIONS(
  model_type = 'DNN_LINEAR_COMBINED_CLASSIFIER',   -- or DNN_LINEAR_COMBINED_REGRESSOR
  input_label_cols = ['label'],
  hidden_units = [64, 32],
  activation_fn = 'RELU',
  batch_size = 100,
  dropout = 0.05,
  optimizer = 'ADAGRAD',
  learn_rate = 0.001,
  max_iterations = 10,
  early_stop = FALSE,
  enable_global_explain = TRUE,
  data_split_method = 'AUTO_SPLIT'
) AS
SELECT * FROM `PROJECT_ID.DATASET.TABLE`;
```

**Options (model-specific):**

| Option | Type | Required | Default | Range / Values | Description |
|--------|------|----------|---------|----------------|-------------|
| `model_type` | string | Yes | — | `DNN_LINEAR_COMBINED_CLASSIFIER` \| `DNN_LINEAR_COMBINED_REGRESSOR` | Selects classifier vs regressor. |
| `input_label_cols` | array\<string\> | No | `['label']` | column name(s) | Label column(s); one label required. |
| `hidden_units` | array\<int64\> | No | single layer `min(128, num_samples/(10*(num_in+num_out)))` | e.g. `[64,32]` | Deep-side hidden layer sizes. Tunable via `HPARAM_CANDIDATES`. |
| `activation_fn` | string | No | `RELU` | `RELU`,`RELU6`,`CRELU`,`ELU`,`SELU`,`SIGMOID`,`TANH` | Deep-side activation. |
| `batch_size` | int64 | No | auto (\<=1024) | \>0 | Mini-batch size. Tunable. |
| `dropout` | float64 | No | auto | `[0,1)` | Dropout probability on deep units. Tunable. |
| `optimizer` | array\<struct\> or string | No | `[STRUCT('dnn','ADAM'), STRUCT('linear','FTRL')]` | `ADAGRAD`,`ADAM`,`FTRL`,`RMSPROP`,`SGD` | Training optimizer. Can be set per model part, e.g. `[STRUCT('dnn','ADAGRAD'), STRUCT('linear','SGD')]`. Tunable. |
| `learn_rate` | array\<struct\> or float64 | No | `0.001` (both parts) | \>0 | Learning rate. Settable per part, e.g. `[STRUCT('dnn',0.001), STRUCT('linear',0.01)]`. Tunable via `HPARAM_RANGE`. |
| `l1_reg` / `l2_reg` | float64 | No | `0` | \>=0 | L1 / L2 regularization. Tunable. |
| `max_iterations` | int64 | No | `20` | \>=1 | Max training iterations (epochs). |
| `early_stop` | bool | No | `TRUE` | — | Stop when relative loss gain \< `min_rel_progress`. |
| `min_rel_progress` | float64 | No | `0.01` | — | Min relative loss improvement to continue when `early_stop=TRUE`. |
| `warm_start` | bool | No | `FALSE` | — | Continue training from an existing model. |
| `auto_class_weights` | bool | No | `FALSE` | classifier only | Balance class weights inversely to frequency. |
| `class_weights` | array\<struct\> | No | — | classifier only | Manual per-class weights (mutually exclusive with `auto_class_weights`). |
| `data_split_method` | string | No | `AUTO_SPLIT` | `AUTO_SPLIT`,`RANDOM`,`CUSTOM`,`SEQ`,`NO_SPLIT` | Train/eval split strategy. |
| `data_split_col` | string | No | — | column name | With `CUSTOM`: `FALSE`=train, `TRUE`=eval. With `SEQ`: ordering column. |
| `data_split_eval_fraction` | float64 | No | `0.2` | `[0,1)` | Eval fraction for `RANDOM`/`SEQ`. |
| `enable_global_explain` | bool | No | `FALSE` | — | Must be `TRUE` to enable `ML.GLOBAL_EXPLAIN` / `ML.EXPLAIN_PREDICT` (integrated gradients). |
| `integrated_gradients_num_steps` | int64 | No | `25` | \>=1 | Steps for integrated-gradients attribution. |
| `num_trials` | int64 | No | — | \>=1 | Enables hyperparameter tuning; max trials to run. |
| `max_parallel_trials` | int64 | No | `1` | — | Concurrent HP-tuning trials. |
| `hparam_tuning_objectives` | array\<string\> | No | classifier `ROC_AUC`, regressor `R2_SCORE` | one objective | Metric optimized during tuning. |
| `model_registry` / `vertex_ai_model_id` / `vertex_ai_model_version_aliases` | string/array | No | — | — | Auto-register the model in Vertex AI Model Registry. |

**Supported lifecycle functions:** `ML.PREDICT`, `ML.EVALUATE`, `ML.TRAINING_INFO`, `ML.FEATURE_INFO`, `ML.EXPLAIN_PREDICT` (local attributions), `ML.GLOBAL_EXPLAIN` (needs `enable_global_explain=TRUE`), `EXPORT MODEL`. Classifier also: `ML.CONFUSION_MATRIX`, `ML.ROC_CURVE` (binary). Not supported: `ML.WEIGHTS`/`ML.ADVANCED_WEIGHTS` (no linear-coefficient export for this type) and `ML.FEATURE_IMPORTANCE` (that is tree-model only — use `ML.GLOBAL_EXPLAIN` instead).

**ML.EVALUATE output metrics (this type):**
- Classifier: `precision`, `recall`, `accuracy`, `f1_score`, `log_loss`, `roc_auc` (tested, see repo example). Adds `trial_id` when HP tuning was used.
- Regressor: `mean_absolute_error`, `mean_squared_error`, `mean_squared_log_error`, `median_absolute_error`, `r2_score`, `explained_variance`. Adds `trial_id` when HP tuning was used.

**Preprocessing support:** automatic (BQML auto-encodes numeric standardization and categorical encoding) | manual feature engineering | `TRANSFORM` clause supported (preprocessing is saved with the model and reapplied at predict time).

**Hyperparameter tuning:** Supported. Set `num_trials` (rule of thumb \>= 10 * num_hyperparameters). Tunable options include `hidden_units`, `batch_size`, `dropout`, `learn_rate`, `optimizer`, `l1_reg`, `l2_reg` via `HPARAM_RANGE(...)` / `HPARAM_CANDIDATES([...])`. Default objective: classifier `ROC_AUC`, regressor `R2_SCORE`.

**Explainability / weights:** Use `ML.EXPLAIN_PREDICT` (per-row integrated-gradients attributions, `STRUCT(k AS top_k_features)`) and `ML.GLOBAL_EXPLAIN` (aggregate feature influence). Both require `enable_global_explain=TRUE` at CREATE time. `ML.WEIGHTS`, `ML.ADVANCED_WEIGHTS`, and `ML.FEATURE_IMPORTANCE` do **not** apply.

**Best practices:**
- Set `enable_global_explain=TRUE` at training time — it cannot be added afterward without retraining.
- For imbalanced classification (e.g. fraud), prefer `auto_class_weights=TRUE` or explicit `class_weights`; the repo example trains on a 0.17%-positive fraud set.
- Training is relatively expensive (TensorFlow): repo run took ~967s over ~24 GB processed for [64,32] on ~256k rows. Start small (few layers, modest `max_iterations`) before tuning.
- Use `data_split_method='CUSTOM'` with a boolean split column to align eval data with your own TRAIN/VALIDATE/TEST scheme.

**Limitations:**
- No coefficient/weights extraction (`ML.WEIGHTS` unsupported) — explainability is attribution-based only.
- Slower and costlier to train than `LINEAR_REG`/`LOGISTIC_REG` or boosted trees for similar tabular tasks.
- `auto_class_weights` and `class_weights` are mutually exclusive and classifier-only.

**Locations:** Available in all BigQuery ML regions/multi-regions; for Vertex AI registration / endpoint serving keep model and Vertex resources co-located (repo uses `us-central1`).

**BigFrames API:** `bigframes.ml.linear_model` has no wide-and-deep class; closest neural option is via `CREATE MODEL` SQL. Use `bigframes.ml.imported`/raw SQL for this type — no direct first-class `DNN_LINEAR_COMBINED` wrapper.

**Repo example (tested):** `/home/user/git/vertex-ai-mlops/03 - BigQuery ML (BQML)/03e - BQML Wide-And-Deep Networks.ipynb` — trains `DNN_LINEAR_COMBINED_CLASSIFIER` on the credit-card fraud table with `hidden_units=[64,32]`, `optimizer='SGD'`, `dropout=0.05`, `CUSTOM` split, `enable_global_explain=TRUE`; then runs `ML.FEATURE_INFO`, `ML.TRAINING_INFO`, `ML.EVALUATE` (precision/recall/accuracy/f1_score/log_loss/roc_auc), `ML.CONFUSION_MATRIX`, `ML.ROC_CURVE`, `ML.PREDICT`, `ML.EXPLAIN_PREDICT`, `ML.GLOBAL_EXPLAIN`, Vertex AI Model Registry registration + endpoint deploy, and `EXPORT MODEL` (TensorFlow SavedModel).


---

### `AUTOML_CLASSIFIER` / `AUTOML_REGRESSOR`
- **Description:** BigQuery ML wrappers that train a [Vertex AI AutoML Tables](https://cloud.google.com/vertex-ai/docs/tabular-data/overview) model directly from SQL. The AutoML service searches multiple model architectures, performs its own feature engineering and hyperparameter tuning, and ensembles candidates to produce a single tabular classification (`AUTOML_CLASSIFIER`) or regression (`AUTOML_REGRESSOR`) model. The user supplies training data and a time budget; AutoML does the rest.
- **When to use:**
  - You want a strong tabular baseline without choosing/tuning the algorithm yourself.
  - You can trade longer, higher-cost training (1–72 hours) for accuracy.
  - You want a model you can export and serve on Vertex AI endpoints.
  - You do NOT need fast, iterative, in-BigQuery retraining (use `BOOSTED_TREE_*` / `DNN_*` / `LINEAR_REG`/`LOGISTIC_REG` for that).
- **Category:** automl (supervised-classification / supervised-regression).
- **Connection required:** No. Training runs as a BigQuery `ML_EXTERNAL` job that invokes Vertex AI on your behalf — no `CREATE CONNECTION` object is needed (unlike remote/imported models). The Vertex AI API must be enabled in the project.
- **Status:** GA.
- **documentation:** [CREATE MODEL for AutoML models](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-automl) · journey links: [E2E user journey for models](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-e2e-journey) · [Vertex AI tabular classification/regression overview](https://cloud.google.com/vertex-ai/docs/tabular-data/classification-regression/overview) · [Manage BQML models in Vertex AI](https://cloud.google.com/bigquery/docs/managing-models-vertex) · [Export BQML models](https://cloud.google.com/bigquery/docs/exporting-models).

**CREATE MODEL syntax:**
```sql
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.MODEL_NAME`
OPTIONS(
  model_type = 'AUTOML_CLASSIFIER',          -- or 'AUTOML_REGRESSOR'
  input_label_cols = ['label_column'],
  budget_hours = 1.0,
  optimization_objective = 'MAXIMIZE_AU_PRC', -- classifier objective (see below)
  data_split_col = 'splits'
) AS
SELECT * EXCEPT(id_column)
FROM `PROJECT_ID.DATASET.TRAINING_TABLE`;
```

**Options (model-specific):**

| Option | Type | Required | Default | Range / Values | Description |
|--------|------|----------|---------|----------------|-------------|
| `model_type` | STRING | Yes | — | `'AUTOML_CLASSIFIER'` \| `'AUTOML_REGRESSOR'` | Selects AutoML Tables classification or regression. |
| `input_label_cols` | ARRAY\<STRING\> | No | `['label']` | one column name | Label column. Classifier label may be STRING or numeric; regressor label is numeric. |
| `budget_hours` | FLOAT64 | No | `1.0` | `1.0`–`72.0` | Training time budget in hours. Model compression after training can add up to ~50% more wall-clock time, which is NOT counted against the budget. |
| `optimization_objective` | STRING or STRUCT | No | task default | see values below | Objective AutoML optimizes. Binary classification may use a STRUCT to set a recall/precision target. |
| `data_split_col` | STRING | No | — | column name | Column that assigns each row to a split. Values map to AutoML splits (e.g. `TRAIN`/`VALIDATE`/`TEST`). |
| `data_split_method` | STRING | No | AutoML auto-split | — | AutoML manages splitting; prefer `data_split_col` for explicit control. |
| `kms_key_name` | STRING | No | — | KMS key resource name | CMEK for the model. |
| `vertex_ai_model_id` | STRING | No | — | model id | Registers the trained model in the Vertex AI Model Registry at creation time. |
| `vertex_ai_model_version_aliases` | ARRAY\<STRING\> | No | — | alias strings | Version aliases applied in the Vertex AI Model Registry. |

`optimization_objective` values:
- **`AUTOML_CLASSIFIER`:** `MAXIMIZE_AU_ROC` (default), `MINIMIZE_LOG_LOSS`, `MAXIMIZE_AU_PRC`, and (binary only) `MAXIMIZE_PRECISION_AT_RECALL` / `MAXIMIZE_RECALL_AT_PRECISION` via a STRUCT supplying the target value.
- **`AUTOML_REGRESSOR`:** `MINIMIZE_RMSE` (default), `MINIMIZE_MAE`, `MINIMIZE_RMSLE`.

**Supported lifecycle functions:** `ML.PREDICT`, `ML.EVALUATE`, `ML.GLOBAL_EXPLAIN` (model-level only; requires no `enable_global_explain` option — AutoML produces attributions automatically), `ML.FEATURE_INFO`, `ML.TRAINING_INFO`. Classification additionally supports `ML.CONFUSION_MATRIX` and (binary) `ML.ROC_CURVE`. `EXPORT MODEL` is supported (TensorFlow SavedModel / XGBoost). NOT supported: `ML.WEIGHTS` / `ML.ADVANCED_WEIGHTS`, `ML.FEATURE_IMPORTANCE`, `ML.EXPLAIN_PREDICT` (AutoML is an opaque ensemble; use `ML.GLOBAL_EXPLAIN` for feature attributions).

**ML.EVALUATE output metrics (this type):**
- **`AUTOML_CLASSIFIER`:** `precision`, `recall`, `accuracy`, `f1_score`, `log_loss`, `roc_auc`.
- **`AUTOML_REGRESSOR`:** `mean_absolute_error`, `mean_squared_error`, `mean_squared_log_error`, `median_absolute_error`, `r2_score`, `explained_variance`.

**Preprocessing support:** automatic (AutoML standardizes numeric columns, one-hot encodes categoricals, and extracts components from timestamps internally). The `TRANSFORM` clause is NOT supported for AutoML model types — do any custom feature engineering in the training `SELECT`.

**Hyperparameter tuning:** Not user-configurable via `NUM_TRIALS` / `HPARAM_RANGE` / `HPARAM_CANDIDATES`. AutoML performs its own architecture search and hyperparameter tuning internally; the user lever is `budget_hours`.

**Explainability / weights:** `ML.GLOBAL_EXPLAIN` only, returning model-level mean absolute feature attributions (columns `feature`, `attribution`). For AutoML, `class_level_explain` is ignored — only model-level importance is available for both classifier and regressor. `ML.WEIGHTS`, `ML.ADVANCED_WEIGHTS`, and `ML.EXPLAIN_PREDICT` do not apply.

**Best practices:**
- Budget cost vs. accuracy: start at `budget_hours = 1.0` to validate the pipeline, then raise toward 72.0 only if the lift justifies the cost.
- Use `data_split_col` with a pre-computed split column for reproducible, leakage-free TRAIN/VALIDATE/TEST partitioning.
- For imbalanced classification (e.g. fraud), prefer `MAXIMIZE_AU_PRC` over `MAXIMIZE_AU_ROC`.
- Register to Vertex AI at training time via `vertex_ai_model_id` instead of exporting/uploading separately.

**Limitations:**
- Trains as an `ML_EXTERNAL` job on Vertex AI (not in-BigQuery `QUERY`); on flat-rate/reservations the project must accommodate `ML_EXTERNAL`. Evaluation/prediction run as standard `QUERY` jobs.
- Classifier label cardinality is capped at 1,000 unique classes (contact bqml-feedback@google.com for more).
- Feature column names must be 125 characters or fewer.
- Default max 5 concurrent AutoML training jobs per project (raising Vertex AI quota does not change this; submit a request to raise it).
- Wall-clock time exceeds `budget_hours` because of model compression and data movement to/from AutoML.
- No `TRANSFORM`, no `ML.WEIGHTS`, no `ML.EXPLAIN_PREDICT`, no user HP-tuning.

**Locations:** AutoML model availability differs by region/multi-region; check [BigQuery ML locations](https://cloud.google.com/bigquery/docs/locations). Training data, model, and the Vertex AI region must be compatible.

**BigFrames API:** `bigframes.ml.llm` no; use `bigframes.ml.imported`/AutoML via `bigframes.ml` — for tabular AutoML use `from bigframes.ml.ensemble`? No direct AutoML estimator class is exposed as of this writing; create via SQL `CREATE MODEL` or the `bigframes.ml.linear_model`/tree estimators for in-BQ alternatives. Treat as: no direct BigFrames AutoML estimator — use SQL.

**Repo example (tested):** `/home/user/git/vertex-ai-mlops/02 - Vertex AI AutoML/BQML AutoML.ipynb` — trains an `AUTOML_CLASSIFIER` on the `fraud_prepped` table with `budget_hours = 1`, `optimization_objective = 'MAXIMIZE_AU_PRC'`, `input_label_cols = ['Class']`, and `data_split_col = 'splits'`; then runs `ML.FEATURE_INFO`, `ML.TRAINING_INFO`, `ML.EVALUATE` (showing `precision`/`recall`/`accuracy`/`f1_score`/`log_loss`/`roc_auc`), `ML.CONFUSION_MATRIX`, `ML.ROC_CURVE`, and `EXPORT MODEL` to GCS for Vertex AI Model Registry upload. Note: the run took ~1.51 hours wall-clock for a 1-hour budget, illustrating the compression overhead.


---

### `KMEANS`
- **Description:** Unsupervised clustering algorithm that partitions `n` observations into `k` clusters, assigning each row to the cluster with the nearest centroid (mean). Trained with `CREATE MODEL ... OPTIONS(model_type='KMEANS')`. Beyond clustering, a trained k-means model also powers `ML.DETECT_ANOMALIES` (rows far from their nearest centroid are anomalies).
- **When to use:**
  - Customer / market segmentation and grouping unlabeled records.
  - Exploratory analysis to discover natural structure in data.
  - Unsupervised anomaly / outlier detection (distance-to-centroid based).
  - When you have no labels and want fast, in-SQL clustering at BigQuery scale.
- **Category:** unsupervised (clustering).
- **Connection required:** No. (A connection is only needed for unrelated remote/imported models, not for k-means.)
- **Status:** GA.
- **Documentation:** [CREATE MODEL for K-means](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-kmeans) · journey/tutorial group: [k-means tutorial (London bike hires)](https://cloud.google.com/bigquery/docs/kmeans-tutorial) · [E2E user journey for models](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-e2e-journey)

**CREATE MODEL syntax:**
```sql
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.MODEL_NAME`
[TRANSFORM(...)]
OPTIONS(
  model_type           = 'KMEANS',
  num_clusters         = 4,            -- or HPARAM_RANGE(2, 100) / HPARAM_CANDIDATES([...])
  kmeans_init_method   = 'KMEANS++',
  distance_type        = 'EUCLIDEAN',
  standardize_features = TRUE,
  max_iterations       = 20,
  early_stop           = TRUE,
  min_rel_progress     = 0.01
) AS
SELECT * EXCEPT(id_col, label_col)
FROM `PROJECT_ID.DATASET.TABLE`;
```

**Options (model-specific):**

| Option | Type | Required | Default | Range / Values | Description |
|--------|------|----------|---------|----------------|-------------|
| `model_type` | STRING | Yes | — | `'KMEANS'` | Selects k-means. |
| `num_clusters` | INT64 | No | reasonable default from row count | `2`–`100` (typical) | Number of clusters `k`. Accepts `HPARAM_RANGE`/`HPARAM_CANDIDATES` for tuning. |
| `kmeans_init_method` | STRING | No | `'RANDOM'` | `'RANDOM'`, `'KMEANS++'`, `'CUSTOM'` | Centroid seeding. `KMEANS++` gives slower init but faster convergence and repeatably better results. |
| `kmeans_init_col` | STRING | No | — | name of a `BOOL` column | Only with `CUSTOM`. Rows where the column is `TRUE` become initial centroids; count of `TRUE` rows must equal `num_clusters`. Auto-excluded as a feature. |
| `distance_type` | STRING | No | `'EUCLIDEAN'` | `'EUCLIDEAN'`, `'COSINE'` | Distance metric between points. |
| `standardize_features` | BOOL | No | `TRUE` | `TRUE`/`FALSE` | Standardize numeric features before clustering (recommended; scale-sensitive). |
| `max_iterations` | INT64 | No | `20` | \<positive int\> | Max training iterations. |
| `min_rel_progress` | FLOAT64 | No | `0.01` | \<float\> | Min relative loss improvement to continue when `early_stop=TRUE`. |
| `early_stop` | BOOL | No | `TRUE` | `TRUE`/`FALSE` | Stop early once improvement \< `min_rel_progress`. |
| `warm_start` | BOOL | No | `FALSE` | `TRUE`/`FALSE` | Continue training from existing centroids on retrain. |

HP-tuning-eligible option: `num_clusters` (use `HPARAM_RANGE`/`HPARAM_CANDIDATES`), plus tuning controls `num_trials`, `max_parallel_trials`, `hparam_tuning_algorithm`, `hparam_tuning_objectives`.

**Supported lifecycle functions:** `ML.EVALUATE`, `ML.PREDICT` (returns `CENTROID_ID` + `NEAREST_CENTROIDS_DISTANCE`), `ML.CENTROIDS` (centroid coordinates per feature), `ML.DETECT_ANOMALIES`, `ML.FEATURE_INFO`, `ML.TRIAL_INFO` (HP tuning), `EXPORT MODEL` (exports as TensorFlow SavedModel). Not applicable: `ML.CONFUSION_MATRIX`, `ML.ROC_CURVE`, `ML.WEIGHTS`/`ML.ADVANCED_WEIGHTS`, `ML.GLOBAL_EXPLAIN`, `ML.FEATURE_IMPORTANCE` (no coefficients/attributions for clustering).

**ML.EVALUATE output metrics (this type):** `davies_bouldin_index`, `mean_squared_distance`. (With HP tuning, a `trial_id` column is prepended.)

**Preprocessing support:** automatic (BQML standardizes numeric features by default via `standardize_features`); `TRANSFORM` clause supported for in-model feature engineering.

**Hyperparameter tuning:** Supported. Primary tunable option is `num_clusters` (e.g. `HPARAM_RANGE(2, 100)`); objective `davies_bouldin_index` (minimize). Uses Vertex AI Vizier (`VIZIER_DEFAULT`).

**Explainability / weights:** None of `ML.WEIGHTS`/`ML.ADVANCED_WEIGHTS`/`ML.GLOBAL_EXPLAIN`/`ML.FEATURE_IMPORTANCE`/`ML.EXPLAIN_PREDICT` apply. Interpret clusters via `ML.CENTROIDS` (per-feature centroid values) and `ML.PREDICT` distances. `enable_global_explain` is not applicable.

**Best practices:**
- Keep `standardize_features = TRUE` (default) — k-means is scale-sensitive.
- Prefer `kmeans_init_method = 'KMEANS++'` for stable, better-converging results.
- Tune `num_clusters` with `HPARAM_RANGE` + `davies_bouldin_index` objective rather than guessing `k`.
- HP tuning can be expensive/slow (e.g. tens of trials over hundreds of thousands of rows ran ~46 min in the repo example) — bound `num_trials` and use `max_parallel_trials`.
- Exclude id/label columns from the feature set (`SELECT * EXCEPT(...)`).

**Limitations:**
- No supervised metrics or feature attributions (unsupervised).
- `kmeans_init_col` (CUSTOM) requires exactly `num_clusters` TRUE rows.
- `COSINE` distance changes geometry — choose deliberately.
- HP-tuned models return per-trial rows in `ML.EVALUATE`/`ML.PREDICT`; downstream queries must handle/filter `trial_id`.

**Locations:** Available in all BigQuery ML regions/multi-regions; no special location constraint (no connection required).

**BigFrames API:** `bigframes.ml.cluster.KMeans` — e.g. `KMeans(n_clusters=4).fit(X)` then `.predict(X)`.

**Repo example (tested):** `/home/user/git/vertex-ai-mlops/03 - BigQuery ML (BQML)/03h - BQML k-means with Anomaly Detection.ipynb` — trains `KMEANS` on the fraud dataset with `num_clusters = HPARAM_RANGE(2, 100)`, `kmeans_init_method='KMEANS++'`, `distance_type='EUCLIDEAN'`, `standardize_features=TRUE`, tuned on `davies_bouldin_index` (20 trials); demonstrates `ML.EVALUATE`, `ML.CENTROIDS`, `ML.TRIAL_INFO`, `ML.FEATURE_INFO`, `ML.PREDICT`, `ML.DETECT_ANOMALIES` (with `contamination`), Vertex AI Model Registry registration, endpoint serving, and `EXPORT MODEL` (TensorFlow SavedModel).


---

### `PCA`
- **Description:** Principal Component Analysis — an unsupervised, linear dimensionality-reduction model. It transforms a set of correlated numeric/categorical features into a smaller set of orthogonal (uncorrelated) **principal components** ordered by the amount of variance each explains, preserving as much information as possible. Components are derived from the eigendecomposition of the (optionally scaled) feature covariance matrix.
- **When to use:**
  - Reduce dimensionality before training another model, or for visualization of high-dimensional data.
  - Unsupervised **anomaly detection** via `ML.DETECT_ANOMALIES` (reconstruction-loss based), e.g. fraud detection without labels.
  - Generate compact embeddings of structured rows for downstream similarity / clustering.
  - Inspect feature loadings to understand which features drive the most variance.
- **Category:** unsupervised (dimensionality reduction).
- **Connection required:** No. (A connection is only involved if you add `MODEL_REGISTRY = 'VERTEX_AI'` for registry/serving, or `EXPORT MODEL` to GCS — neither is required to train or use the model in BQ.)
- **Status:** GA.
- **documentation:** [CREATE MODEL for PCA](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-pca) · weights/output functions: [ML.PRINCIPAL_COMPONENTS](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-principal-components), [ML.PRINCIPAL_COMPONENT_INFO](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-principal-component-info)

**CREATE MODEL syntax:**
```sql
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.MODEL_NAME`
OPTIONS(
  model_type = 'PCA',
  -- specify EXACTLY ONE of the next two:
  num_principal_components = 2,            -- OR
  -- pca_explained_variance_ratio = 0.90,
  scale_features = TRUE,
  pca_solver = 'AUTO'
) AS
SELECT * EXCEPT(id_col, label_col)         -- PCA ignores no column automatically; SELECT only the features
FROM `PROJECT_ID.DATASET.TABLE`
WHERE splits = 'TRAIN';
```

**Options (model-specific):**

| Option | Type | Required | Default | Range / Values | Description |
|--------|------|----------|---------|----------------|-------------|
| `model_type` | STRING | Yes | — | `'PCA'` | Selects the PCA algorithm. |
| `num_principal_components` | INT64 | One of these two | — | 1 .. 10,000 | Number of components to keep. Mutually exclusive with `pca_explained_variance_ratio`. |
| `pca_explained_variance_ratio` | FLOAT64 | One of these two | — | (0, 1) | Keep the fewest components whose cumulative explained-variance ratio meets this target (computed under the 10,000-component cap). Mutually exclusive with `num_principal_components`. |
| `scale_features` | BOOL | No | `TRUE` | `TRUE` \| `FALSE` | Scale numeric features to unit variance. Features are always mean-centered regardless; categoricals are one-hot encoded. |
| `pca_solver` | STRING | No | `'AUTO'` | `'FULL'` \| `'RANDOMIZED'` \| `'AUTO'` | Eigendecomposition strategy. `FULL` = exact; `RANDOMIZED` = approximate (large cardinality); `AUTO` picks based on post-one-hot feature cardinality (threshold typically ~1,000–1,500). |

You must specify **exactly one** of `num_principal_components` / `pca_explained_variance_ratio`. None of the PCA options accept `HPARAM_RANGE` / `HPARAM_CANDIDATES` (no HP tuning — see below). Registry/serving options (`model_registry`, `vertex_ai_model_id`, `vertex_ai_model_version_aliases`) are model-agnostic and shown working in the repo example.

**Supported lifecycle functions:** `ML.EVALUATE`, `ML.PREDICT` (projects rows onto the components), `ML.DETECT_ANOMALIES` (reconstruction-loss anomaly detection with a `contamination` STRUCT param), `ML.GENERATE_EMBEDDING` / `AI.GENERATE_EMBEDDING` (in-scope here: extract embeddings FROM the trained PCA model), `ML.PRINCIPAL_COMPONENTS`, `ML.PRINCIPAL_COMPONENT_INFO`, `ML.FEATURE_INFO`, `ML.TRAINING_INFO`, `EXPORT MODEL`. Not applicable: `ML.CONFUSION_MATRIX`, `ML.ROC_CURVE`, `ML.GLOBAL_EXPLAIN`, `ML.WEIGHTS`, `ML.FEATURE_IMPORTANCE`, `ML.CENTROIDS`, `ML.RECOMMEND`, `ML.FORECAST`.

**ML.EVALUATE output metrics (this type):**

| Column | Description |
|--------|-------------|
| `total_explained_variance_ratio` | FLOAT64 — fraction of total variance captured by the retained components. |

**Preprocessing support:** Automatic — numeric features are mean-centered (and unit-scaled when `scale_features = TRUE`); categorical features are automatically one-hot encoded. `TRANSFORM` is supported for custom feature engineering and the transforms are stored with the model so they auto-apply at `ML.PREDICT` / `ML.DETECT_ANOMALIES` time.

**Hyperparameter tuning:** Not supported (`num_trials` / HP tuning is N/A for PCA). To search over component counts, train multiple models or use `pca_explained_variance_ratio` to let the variance target choose the count.

**Explainability / weights:** Use the dedicated **weights functions** instead of the standard explainers. `ML.PRINCIPAL_COMPONENTS` returns the per-feature loadings (eigenvectors) for each component; `ML.PRINCIPAL_COMPONENT_INFO` returns each component's `eigenvalue`, `explained_variance_ratio`, and `cumulative_explained_variance_ratio`. `ML.GLOBAL_EXPLAIN` / `ML.WEIGHTS` / `ML.FEATURE_IMPORTANCE` do not apply.

**Best practices:**
- Set `scale_features = TRUE` (default) when features are on different units/scales so high-variance features don't dominate.
- Prefer `pca_explained_variance_ratio` (e.g. 0.90) when you care about retained information rather than a fixed component count.
- For anomaly detection, set `contamination` to your expected outlier rate (e.g. the training-set positive rate) — the repo example derives this from the training fraud rate.
- Use `ML.PRINCIPAL_COMPONENT_INFO` to choose a sensible component count via the cumulative explained-variance "elbow."

**Limitations:**
- Maximum 10,000 principal components.
- `FULL`/`AUTO` solvers cap post-one-hot feature cardinality dynamically (~1,000–1,500); high-cardinality categorical inputs can force `RANDOMIZED`.
- Exactly one of `num_principal_components` / `pca_explained_variance_ratio` must be set.
- Linear method only — does not capture nonlinear structure (consider `AUTOENCODER` for nonlinear dimensionality reduction / anomaly detection).
- No `ML.EVALUATE` label-based metrics; evaluation is variance-based only.

**Locations:** Available in all BigQuery ML regions/multi-regions. `MODEL_REGISTRY = 'VERTEX_AI'` registration and online serving require a Vertex AI-supported region (repo example uses `us-central1`).

**BigFrames API:** `bigframes.ml.decomposition.PCA` (`fit` / `transform`; `n_components` maps to `num_principal_components`; `.predict()` corresponds to projection).

**Repo example (tested):** `/home/user/git/vertex-ai-mlops/03 - BigQuery ML (BQML)/03g - BQML - PCA with Anomaly Detection.ipynb` — trains `model_type='PCA'` with `pca_explained_variance_ratio=0.90, scale_features=TRUE, pca_solver='AUTO'` on the credit-card `fraud_prepped` table; shows `ML.EVALUATE` (`total_explained_variance_ratio` ≈ 0.923), `ML.PRINCIPAL_COMPONENT_INFO`, `ML.PRINCIPAL_COMPONENTS`, `ML.PREDICT` (per-row component projections), `ML.DETECT_ANOMALIES` with `STRUCT(<train_fraud_rate> AS contamination)` for fraud detection, plus Vertex AI registry registration, endpoint deployment, and `EXPORT MODEL` (exports as a TensorFlow SavedModel).


---

### `AUTOENCODER`
- **Description:** A symmetric feed-forward neural network that learns to compress (encode) input rows into a lower-dimensional latent space and then reconstruct (decode) them. The middle hidden layer defines the latent dimension. Quality is measured by reconstruction loss (how closely outputs match inputs).
- **When to use:**
  - Unsupervised anomaly detection on tabular data (high reconstruction error = anomaly) via `ML.DETECT_ANOMALIES`.
  - Dimensionality reduction / nonlinear feature compression where a linear method (PCA) is insufficient.
  - Producing row-level embeddings (latent vectors) for similarity search, recommendation, or outlier detection.
  - Data sanitation: flag/repair records that the model cannot reconstruct well.
- **Category:** unsupervised.
- **Connection required:** No (in-BigQuery training). A Cloud connection/Vertex AI is only needed for the optional `MODEL_REGISTRY = 'VERTEX_AI'` registration or `EXPORT MODEL` to GCS — not for training/eval/predict.
- **Status:** GA.
- **documentation:** [CREATE MODEL for autoencoder](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-autoencoder) · [ML.RECONSTRUCTION_LOSS](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-reconstruction-loss) · journey links: [Anomaly detection](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-detect-anomalies), [Hyperparameter tuning](https://cloud.google.com/bigquery/docs/hp-tuning-overview), [E2E user journeys](https://cloud.google.com/bigquery/docs/e2e-journey).

**CREATE MODEL syntax:**
```sql
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.MODEL_NAME`
[TRANSFORM(...)]
OPTIONS(
  model_type = 'AUTOENCODER',
  hidden_units = [128, 64, 8, 64, 128],   -- middle value = latent dimension
  activation_fn = 'RELU',
  batch_size = 30,
  dropout = 0.5,
  learn_rate = 0.001,
  optimizer = 'ADAM',
  max_iterations = 30,
  early_stop = TRUE,
  min_rel_progress = 0.001
) AS
SELECT * EXCEPT(label_or_id_cols)            -- no label column; unsupervised
FROM `PROJECT_ID.DATASET.TABLE`
WHERE splits = 'TRAIN';
```

**Options (model-specific):**

| Option | Type | Required | Default | Range / Values | Description |
|--------|------|----------|---------|----------------|-------------|
| `model_type` | STRING | Yes | — | `'AUTOENCODER'` | Selects the model. |
| `hidden_units` | ARRAY\<INT64\> | No | network auto-sized | e.g. `[128,64,8,64,128]` | Layer sizes; symmetric. **Middle element = latent-space dimension.** Tunable via `HPARAM_CANDIDATES([struct([...]), ...])`. |
| `activation_fn` | STRING | No | `'RELU'` | `RELU`, `RELU6`, `ELU`, `SELU`, `SIGMOID`, `TANH` (no `CRELU`) | Hidden-layer activation. Tunable (`HPARAM_CANDIDATES`). |
| `batch_size` | INT64 | No | auto (\<=1024) | \>0 | Mini-batch size. Tunable (`HPARAM_RANGE`/`HPARAM_CANDIDATES`). |
| `dropout` | FLOAT64 | No | 0 | tuning range `[0, 1.0)`, default tuning range `[0, 0.8]` | Dropout rate. Tunable. |
| `learn_rate` | FLOAT64 | No | 0.001 | \>0 | Optimizer learning rate. Tunable. |
| `learn_rate_strategy` | STRING | No | `'LINE_SEARCH'` | `LINE_SEARCH`, `CONSTANT` | How learn rate evolves. |
| `optimizer` | STRING | No | `'ADAM'` | `ADAGRAD`, `ADAM`, `FTRL`, `RMSPROP`, `SGD` | Training optimizer. Tunable. |
| `l1_reg_activation` | FLOAT64 | No | 0 | \>=0 | L1 regularization of the activation output (autoencoder-specific; **note: not `l1_reg`/`l2_reg`**). Tunable. |
| `max_iterations` | INT64 | No | 20 | \>0 | Max training iterations (epochs). |
| `early_stop` | BOOL | No | TRUE | TRUE/FALSE | Stop when `min_rel_progress` not met. |
| `min_rel_progress` | FLOAT64 | No | 0.01 | \>0 | Min relative loss improvement to continue (when `early_stop=TRUE`). |
| `warm_start` | BOOL | No | FALSE | TRUE/FALSE | Continue training existing model. |
| `kms_key_name` | STRING | No | — | Cloud KMS key | CMEK for the model. |
| `model_registry` | STRING | No | — | `'VERTEX_AI'` | Register model in Vertex AI Model Registry. |
| `vertex_ai_model_id` | STRING | No | — | string | Vertex AI model id (with `model_registry`). |
| `vertex_ai_model_version_aliases` | ARRAY\<STRING\> | No | — | strings | Version aliases in Vertex AI. |

HP-tuning options (used when `num_trials` set): `num_trials`, `max_parallel_trials`, `hparam_tuning_algorithm` (e.g. `'VIZIER_DEFAULT'`), `hparam_tuning_objectives` (e.g. `['mean_absolute_error']`). Tunable hyperparameters: `hidden_units`, `activation_fn`, `batch_size`, `dropout`, `learn_rate`, `optimizer`, `l1_reg_activation`.

**Supported lifecycle functions:** `ML.EVALUATE`, `ML.RECONSTRUCTION_LOSS`, `ML.PREDICT` (returns `latent_col_N` latent vector + input columns), [`ML.GENERATE_EMBEDDING`](../bq-ai-functions/RESOURCES.md) (latent space as a single `ml_generate_embedding_result` ARRAY — in-scope here as a lifecycle use of a trained BQML model), `ML.DETECT_ANOMALIES` (with `STRUCT(<contamination> AS contamination)`), `ML.FEATURE_INFO`, `ML.TRAINING_INFO`, `ML.TRIAL_INFO` (HP tuning), `EXPORT MODEL`. Pair with `ML.NORMALIZER` + `VECTOR_SEARCH` for similarity. No `ML.WEIGHTS`/`ML.GLOBAL_EXPLAIN`/`ML.CONFUSION_MATRIX`/`ML.ROC_CURVE`/`ML.CENTROIDS`/`ML.PRINCIPAL_COMPONENTS`.

**ML.EVALUATE output metrics (this type):** `mean_absolute_error`, `mean_squared_error`, `mean_squared_log_error`. (For HP-tuned models the output also includes a `trial_id` column, one row per trial.) `ML.RECONSTRUCTION_LOSS` returns the same three metric columns **per input row** (plus `trial_id` for tuned models) alongside the input columns.

**Preprocessing support:** automatic (standardization of numeric features) | manual | TRANSFORM (supported; if TRANSFORM is used, `ML.PREDICT`/`ML.RECONSTRUCTION_LOSS` accept only the pre-TRANSFORM input columns).

**Hyperparameter tuning:** Supported. Set `num_trials` and use `HPARAM_RANGE`/`HPARAM_CANDIDATES` on `hidden_units`, `activation_fn`, `batch_size`, `dropout`, `learn_rate`, `optimizer`, `l1_reg_activation`. Default algorithm `VIZIER_DEFAULT` (Vertex AI Vizier); objective defaults to the key metric, override with `hparam_tuning_objectives` (e.g. `mean_absolute_error`). Recommended trials >= 10 x number of tuned hyperparameters. Tuned models expose results via `ML.TRIAL_INFO` and add a `trial_id` column to evaluate/predict output.

**Explainability / weights:** None of `ML.WEIGHTS`, `ML.ADVANCED_WEIGHTS`, `ML.GLOBAL_EXPLAIN`, `ML.FEATURE_IMPORTANCE`, or `ML.EXPLAIN_PREDICT` apply (`enable_global_explain` not supported for autoencoders). Interpretability comes from per-row reconstruction loss and the latent representation.

**Best practices:**
- Set the latent dimension via the middle of `hidden_units` (e.g. `[128,64,8,64,128]` => 8-dim latent / embedding).
- Train on clean/normal data only for anomaly detection; pass the expected fraud/anomaly rate as `contamination` to `ML.DETECT_ANOMALIES`.
- Normalize latent vectors (`ML.NORMALIZER(..., 2)`) before `VECTOR_SEARCH`; use `DOT_PRODUCT` distance on L2-normalized embeddings.
- HP tuning scans large data per trial — autoencoder training is compute/byte heavy (the repo example processed ~1.9 TB across 40 trials); cap `num_trials`/`max_parallel_trials` and use `early_stop`.

**Limitations:**
- Unsupervised — no label column; exclude id/label/split columns from the training SELECT.
- No model weight/feature-attribution functions; no `enable_global_explain`.
- `ML.RECONSTRUCTION_LOSS` does not support imported TensorFlow models.
- Exported model is TensorFlow SavedModel format.

**Locations:** Available in BigQuery ML regions/multi-regions; Vertex AI registration/online serving requires a matching Vertex AI region (notebooks use `us-central1`).

**BigFrames API:** `bigframes.ml.imported`/`bigframes.ml.decomposition` have no direct autoencoder class; no direct BigFrames equivalent — use SQL `CREATE MODEL ... AUTOENCODER`.

**Repo example (tested):**
- `/home/user/git/vertex-ai-mlops/03 - BigQuery ML (BQML)/03i - BQML Autoencoder with Anomaly Detection.ipynb` — full lifecycle: HP-tuned `AUTOENCODER` (`HPARAM_CANDIDATES`/`HPARAM_RANGE`, `num_trials=40`), `ML.FEATURE_INFO`, `ML.TRIAL_INFO`, `ML.EVALUATE`, `ML.RECONSTRUCTION_LOSS`, `ML.PREDICT` (latent_col_*), `ML.DETECT_ANOMALIES` for fraud, Vertex AI registry/endpoint serving, `EXPORT MODEL`.
- `/home/user/git/vertex-ai-mlops/Applied GenAI/Embeddings/BQML Autoencoder As Table Embedding.ipynb` — single-config train, `ML.EVALUATE` per split, latent space as embeddings via `ML.PREDICT` and `ML.GENERATE_EMBEDDING`, `ML.NORMALIZER`, and `VECTOR_SEARCH` (IVF/TREE_AH index) for row similarity.


---

### `MATRIX_FACTORIZATION`
- **Description:** Collaborative-filtering recommendation model. Learns low-dimensional latent factor vectors for users and items by factorizing the sparse user-item rating matrix, then predicts ratings/confidences for the (mostly missing) user-item pairs. Explicit feedback uses Alternating Least Squares (ALS); implicit feedback uses Weighted ALS (WALS).
- **When to use:**
  - Build product / content / movie recommenders from a (user, item, rating) interaction table.
  - You have explicit ratings (e.g., 1-5 stars) → `FEEDBACK_TYPE = 'EXPLICIT'`.
  - You only have implicit signals (clicks, views, session/engagement time, purchase counts) → `FEEDBACK_TYPE = 'IMPLICIT'`.
  - You want to score all missing user-item pairs at scale with `ML.RECOMMEND` without enumerating them.
- **Category:** recommendation
- **Connection required:** No. BUT see *Limitations* — `MATRIX_FACTORIZATION` is the one model type that does **not** run on BigQuery on-demand pricing; it requires a slot reservation/edition (capacity-based pricing).
- **Status:** GA.
- **documentation:** [CREATE MODEL (matrix factorization)](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-matrix-factorization) · [ML.RECOMMEND](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-recommend) · Journey/tutorials: [Explicit feedback tutorial](https://cloud.google.com/bigquery/docs/bigqueryml-mf-explicit-tutorial), [Implicit feedback tutorial](https://cloud.google.com/bigquery/docs/bigqueryml-mf-implicit-tutorial)

**CREATE MODEL syntax:**
```sql
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.MODEL_NAME`
OPTIONS(
  model_type        = 'MATRIX_FACTORIZATION',
  feedback_type     = 'EXPLICIT',          -- or 'IMPLICIT'
  user_col          = 'user_id',
  item_col          = 'item_id',
  rating_col        = 'rating',            -- default 'rating'
  num_factors       = 34,
  l2_reg            = 9.83
  -- wals_alpha = 40   -- IMPLICIT only
) AS
SELECT user_id, item_id, rating
FROM `PROJECT_ID.DATASET.ratings`;
```
The training query must produce three columns: a user column, an item column, and a rating column. There is no `TRANSFORM` clause / feature engineering for this model type.

**Options (model-specific):**

| Option | Type | Required | Default | Range / Values | Description |
|--------|------|----------|---------|----------------|-------------|
| `model_type` | STRING | Yes | — | `'MATRIX_FACTORIZATION'` | Selects the model algorithm. |
| `feedback_type` | STRING | No | `'EXPLICIT'` | `'EXPLICIT'` \| `'IMPLICIT'` | EXPLICIT → ALS (user-supplied ratings); IMPLICIT → WALS (proxy signals like clicks/engagement). |
| `user_col` | STRING | No | `'user'` | column name | The user column in the input. |
| `item_col` | STRING | No | `'item'` | column name | The item column in the input. |
| `rating_col` | STRING | No | `'rating'` | column name | The rating/feedback column. Names the output column of `ML.RECOMMEND` (`predicted_\<rating_col\>`). |
| `num_factors` | INT64 | No | model-chosen | \>= 0 | Number of latent factors. Higher → more capacity, more cost/overfit risk. **HP-tunable** (`HPARAM_RANGE`/`HPARAM_CANDIDATES`). |
| `l2_reg` | FLOAT64 | No | `1.0` | \> 0 | L2 regularization strength. **HP-tunable**. |
| `wals_alpha` | FLOAT64 | No | `40` | \> 0 | IMPLICIT only: confidence weight on observed interactions. **HP-tunable**. Ignored for EXPLICIT. |
| `max_iterations` | INT64 | No | `20` | \>= 1 | Max training iterations. |
| `early_stop` | BOOL | No | `TRUE` | TRUE/FALSE | Stop when improvement \< `min_rel_progress`. |
| `min_rel_progress` | FLOAT64 | No | `0.01` | \> 0 | Minimum relative loss improvement to continue when `early_stop=TRUE`. |
| `data_split_method` | STRING | No | `'AUTO_SPLIT'` (`'RANDOM'` semantics) | `'AUTO_SPLIT'`,`'RANDOM'`,`'CUSTOM'`,`'SEQ'`,`'NO_SPLIT'` | How to carve out an eval set. |
| `data_split_eval_fraction` | FLOAT64 | No | `0.2` | 0–1 | Fraction reserved for evaluation. |
| `data_split_test_fraction` | FLOAT64 | No | — | 0–1 | Test fraction (used with HP tuning). |

**Supported lifecycle functions:**
- `ML.RECOMMEND` — primary inference function (predict ratings/confidence for user-item pairs).
- `ML.EVALUATE` — quality metrics (differ by feedback type, below).
- `ML.WEIGHTS` — returns the learned user and item latent factor vectors (the embeddings + intercept). Useful for similarity / nearest-neighbor item search.
- `ML.GENERATE_EMBEDDING` — extract the per-user / per-item factor embeddings from the trained MF model (in-scope here: lifecycle use of a BQML model, not the foundation-model use).
- `ML.TRAINING_INFO`, `ML.FEATURE_INFO` — training/iteration and input column stats.
- `ML.TRIAL_INFO` / `ML.EVALUATE(..., TRIAL_ID)` — when trained with hyperparameter tuning.
- Not applicable: `ML.PREDICT` (use `ML.RECOMMEND` instead), `ML.CONFUSION_MATRIX`, `ML.ROC_CURVE`, `ML.GLOBAL_EXPLAIN`, `ML.FEATURE_IMPORTANCE`, `ML.EXPLAIN_PREDICT`.

**ML.EVALUATE output metrics (this type):**
- **EXPLICIT** (regression-style): `mean_absolute_error`, `mean_squared_error`, `mean_squared_log_error`, `median_absolute_error`, `r2_score`, `explained_variance`.
- **IMPLICIT** (ranking-style): `mean_average_precision`, `mean_squared_error`, `normalized_discounted_cumulative_gain`, `average_rank`.

**Preprocessing support:** None. No `TRANSFORM` clause; input is the raw (user, item, rating) triple. Aggregate/derive your rating signal in the training `SELECT`.

**Hyperparameter tuning:** Supported. Tunable options: `num_factors`, `l2_reg`, and (IMPLICIT only) `wals_alpha`, via `HPARAM_RANGE` / `HPARAM_CANDIDATES` with `num_trials`. Default `hparam_tuning_objective`: `MEAN_SQUARED_ERROR` for EXPLICIT, `MEAN_AVERAGE_PRECISION` for IMPLICIT.

**Explainability / weights:** No feature attributions (`ML.GLOBAL_EXPLAIN` / `ML.EXPLAIN_PREDICT` / `ML.FEATURE_IMPORTANCE` do not apply; `enable_global_explain` is not used). The model's interpretability surface is `ML.WEIGHTS` (latent factor vectors for users and items) and the embeddings via `ML.GENERATE_EMBEDDING`.

**Best practices:**
- Choose `feedback_type` to match your data: explicit star ratings → EXPLICIT; behavioral proxies → IMPLICIT (and tune `wals_alpha`).
- For IMPLICIT, engineer the rating signal (e.g., capped session duration, view/purchase counts) in the training query.
- `ML.RECOMMEND` output scales as users × items — write results to a table rather than scanning interactively; filter to a user (or item) subset when you only need targeted recommendations.
- Use `ML.WEIGHTS` factor vectors for fast item-item similarity instead of recomputing full recommendation matrices.
- Tune `num_factors` and `l2_reg` together — more factors needs more regularization.

**Limitations:**
- **Pricing/slots:** Unlike every other BQML model type, `MATRIX_FACTORIZATION` cannot train under on-demand (per-byte) pricing. You must use a reservation / BigQuery Editions (capacity-based) slots. Evaluation and `ML.RECOMMEND` run as standard `QUERY` jobs.
- No `TRANSFORM` / automatic feature engineering.
- Cold start: cannot recommend for users or items absent from the training data (no factors learned for them).
- Output volume from `ML.RECOMMEND` can be very large (full sparse matrix).

**Locations:** Model-type availability varies by region; check [BigQuery ML locations](https://cloud.google.com/bigquery/docs/locations). Reservation availability in the model's region is required (see pricing note).

**BigFrames API:** `bigframes.ml.decomposition.MatrixFactorization` — `.fit(X)` on a (user, item, rating) DataFrame, then `.predict()` for recommendations.

**Repo example (tested):** No matrix-factorization notebook exists in the repo yet. The closest tested BQML reference is [`/home/user/git/vertex-ai-mlops/02 - Vertex AI AutoML/BQML AutoML.ipynb`](/home/user/git/vertex-ai-mlops/02%20-%20Vertex%20AI%20AutoML/BQML%20AutoML.ipynb), which documents the BQML slot/job-type model and explicitly calls out that `model_type = 'MATRIX_FACTORIZATION'` is the exception that does **not** run on on-demand pricing (requires a flat-rate/reservation). It demonstrates the general `CREATE MODEL` → `ML.FEATURE_INFO` → `ML.TRAINING_INFO` → `ML.EVALUATE` lifecycle pattern reused by MF.

---

#### `ML.RECOMMEND` (inference function for this model type)

**Type:** Table-valued function. **Applies to:** `MATRIX_FACTORIZATION` models only.

**Syntax:**
```sql
ML.RECOMMEND(
  MODEL `PROJECT_ID.DATASET.MODEL_NAME`
  [, { TABLE `PROJECT_ID.DATASET.TABLE` | (query_statement) }]
  [, STRUCT(trial_id AS trial_id)]
)
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `MODEL` | model | Yes | — | The trained matrix factorization model. |
| `TABLE` / `query_statement` | table/query | No | all user-item pairs | Optional input. If it has only the user column → all items scored for those users; only the item column → all users scored for those items; both → that specific pair. User/item column names and types must match the model. |
| `trial_id` | INT64 | No | optimal trial | Only when the model was trained with HP tuning; selects which trial to use. |

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| `\<user_col\>` | (matches input) | The user. |
| `\<item_col\>` | (matches input) | The item. |
| `predicted_\<rating_col\>` | FLOAT64 | EXPLICIT models: predicted rating (≈ the input rating range; values just outside are normal). |
| `predicted_\<rating_col\>_confidence` | FLOAT64 | IMPLICIT models: relative confidence (≈ 0–1 if converged). |

**Examples:**
```sql
-- Every user-item pair (no input data; can be very large)
SELECT * FROM ML.RECOMMEND(MODEL `PROJECT_ID.DATASET.MODEL_NAME`);

-- Top recommendations for one user (EXPLICIT model)
SELECT * FROM ML.RECOMMEND(
  MODEL `PROJECT_ID.DATASET.MODEL_NAME`,
  (SELECT 'user_123' AS user_id))
ORDER BY predicted_rating DESC
LIMIT 5;

-- IMPLICIT model: order by confidence
SELECT * FROM ML.RECOMMEND(
  MODEL `PROJECT_ID.DATASET.MODEL_NAME`,
  (SELECT 'user_123' AS user_id))
ORDER BY predicted_rating_confidence DESC
LIMIT 5;
```

**Best practices:** Save large outputs to a table; filter to target users/items; for similarity use cases prefer `ML.WEIGHTS` factor vectors.
**Limitations:** Output can be huge (users × items); cannot recommend for unseen users/items.
**BigFrames API:** `MatrixFactorization.predict()`.


---

### `ARIMA_PLUS`  (univariate time series forecasting)

- **Description:** A univariate time series forecasting model built on the auto.ARIMA algorithm wrapped in an automated pipeline ("PLUS"). Beyond fitting ARIMA (autoregressive `p`, integrated `d`, moving-average `q`), it automatically infers data frequency, handles irregular intervals, deduplicates timestamps (mean), interpolates missing/absent data points linearly, cleans spikes and dips, adjusts abrupt step changes, decomposes trend + multiple seasonalities (STL + double-exponential smoothing), and models holiday effects. auto.ARIMA trains dozens of candidate models in parallel and selects the one with the lowest AIC.
- **When to use:**
  - You have a single demand signal over time (one `time` + one `value` column) and want a forecast plus prediction intervals.
  - You want to forecast many independent series in one query (one model per `time_series_id_col` group, up to 100,000,000 series).
  - You want interpretable decomposition (trend, seasonality, holiday, spikes/dips, step changes) via `ML.EXPLAIN_FORECAST`.
  - You want in-database time series anomaly detection via `ML.DETECT_ANOMALIES`.
  - For zero-config foundation-model forecasting, prefer `AI.FORECAST` (TimesFM) instead — see the cross-link below.
- **Category:** time-series.
- **Connection required:** No.
- **Status:** GA. (Note: the plain `ARIMA` model type is deprecated; use `ARIMA_PLUS`.)
- **documentation:** [CREATE MODEL for ARIMA_PLUS](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-time-series) · [ML.FORECAST](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-forecast) · [ML.ARIMA_EVALUATE](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-arima-evaluate) · [ML.EXPLAIN_FORECAST](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-explain-forecast) · [ML.ARIMA_COEFFICIENTS](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-arima-coefficients) · single / multiple time-series tutorials.

> **Cross-links (owned by `../bq-ai-functions/`, not duplicated here):** TimesFM foundation-model forecasting — [`AI.FORECAST`, `AI.EVALUATE`, `AI.DETECT_ANOMALIES`](../bq-ai-functions/RESOURCES.md). For the multivariate variant with external regressors, see `ARIMA_PLUS_XREG` ([CREATE MODEL ARIMA_PLUS_XREG](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-multivariate-time-series)).

**CREATE MODEL syntax:**
```sql
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.MODEL_NAME`
OPTIONS(
  model_type = 'ARIMA_PLUS',
  time_series_timestamp_col = 'starttime',   -- TIMESTAMP/DATE/DATETIME
  time_series_data_col      = 'num_trips',   -- INT64/NUMERIC/BIGNUMERIC/FLOAT64
  time_series_id_col        = 'start_station_name', -- optional; many series at once
  data_frequency            = 'DAILY',
  horizon                   = 28,
  auto_arima_max_order      = 5,
  holiday_region            = ['GLOBAL', 'US']
) AS
SELECT start_station_name, starttime, num_trips
FROM `PROJECT_ID.DATASET.forecasting_data`
WHERE splits IN ('TRAIN','VALIDATE');   -- ARIMA+ is univariate; fold VALIDATE into training
```

**Options (model-specific):**

| Option | Type | Required | Default | Range / Values | Description |
|--------|------|----------|---------|----------------|-------------|
| `model_type` | STRING | Yes | — | `'ARIMA_PLUS'` | Model type. |
| `time_series_timestamp_col` | STRING | Yes | — | col of TIMESTAMP/DATE/DATETIME | Time points column. |
| `time_series_data_col` | STRING | Yes | — | col of INT64/NUMERIC/BIGNUMERIC/FLOAT64 | Value to forecast. |
| `time_series_id_col` | STRING or ARRAY\<STRING\> | No | — | STRING/INT64/ARRAY of those | ID column(s); fit+forecast multiple series in one query. |
| `horizon` | INT64 | No | `1000` | max `10000` | Number of future time points to forecast (per series). |
| `auto_arima` | BOOL | No | `TRUE` | TRUE/FALSE | Auto-tune p,d,q (and drift). Must be `TRUE` for multiple series. |
| `auto_arima_max_order` | INT64 | No | `2` | `1`–`5` | Max of non-seasonal p+q search space. Higher = more accurate, slower/costlier. |
| `auto_arima_min_order` | INT64 | No | `0` | INT64 | Min of non-seasonal p+q search space. |
| `non_seasonal_order` | (INT64,INT64,INT64) | No | — | p,q in `0`–`5`; d in `0`–`2` | Manual (p,d,q); requires `auto_arima=FALSE`; single series only. |
| `data_frequency` | STRING | No | `'AUTO_FREQUENCY'` | AUTO_FREQUENCY, PER_MINUTE, HOURLY, DAILY, WEEKLY, MONTHLY, QUARTERLY, YEARLY | Frequency of the series. |
| `include_drift` | BOOL | No | `FALSE` | TRUE/FALSE | Linear drift term (only when d=1, and `auto_arima=FALSE`). |
| `holiday_region` | STRING or ARRAY\<STRING\> | No | none | GLOBAL, continental (NA/JAPAC/EMEA/LAC), or country codes | Model holiday effects. Only used for DAILY/WEEKLY series longer than a year. |
| `clean_spikes_and_dips` | BOOL | No | `TRUE` | TRUE/FALSE | Detect+interpolate spike/dip outliers. |
| `adjust_step_changes` | BOOL | No | `TRUE` | TRUE/FALSE | Detect+adjust abrupt step (level) changes. |
| `decompose_time_series` | BOOL | No | `TRUE` | TRUE/FALSE | Save components for `ML.EXPLAIN_FORECAST` / confidence intervals. |
| `time_series_length_fraction` | FLOAT64 | No | use all points | `(0,1)` | Fraction of (recent) points used for trend modeling (speedup). Not with `max_time_series_length`. |
| `min_time_series_length` | INT64 | No | `20` | `>=4` | Min trend points; requires `time_series_length_fraction`. |
| `max_time_series_length` | INT64 | No | none (try `30`) | `>=4` | Cap trend points; not with the fraction/min options. |
| `trend_smoothing_window_size` | INT64 | No | none | positive INT64 | Centered moving-average smoothing of trend (display only; doesn't change forecast). |
| `forecast_limit_lower_bound` | FLOAT64 | No | none | FLOAT64 | Hard lower bound on forecast values (e.g. `0` for non-negative demand). |
| `forecast_limit_upper_bound` | FLOAT64 | No | none | FLOAT64 | Hard upper bound on forecast values. |
| `seasonalities` | ARRAY\<STRING\> | No | auto | seasonality names | Override auto-detected seasonal patterns. |
| `hierarchical_time_series_cols` | ARRAY\<STRING\> | No | — | id col subset | Dimensions to roll up + reconcile (bottom-up hierarchical forecasts). |
| `kms_key_name` | STRING | No | — | KMS key | CMEK for the model. |

HP-tuning note: ARIMA_PLUS does **not** use the `num_trials` HP-tuning framework; `auto_arima` is its built-in hyperparameter search over (p,d,q). `auto_arima_max_order` / `auto_arima_min_order` control the search space.

**Supported lifecycle functions:**
`ML.FORECAST` (forecast + intervals), `ML.EXPLAIN_FORECAST` (forecast + decomposition; needs `decompose_time_series=TRUE`), `ML.EVALUATE` (forecast accuracy metrics, optional eval data), `ML.ARIMA_EVALUATE` (per-series model selection diagnostics), `ML.ARIMA_COEFFICIENTS` (AR/MA coefficients + drift), `ML.DETECT_ANOMALIES` (anomaly probability per point), `ML.FEATURE_INFO`, `ML.TRAINING_INFO`, `ML.HOLIDAY_INFO` (modeled holidays when `holiday_region` set). Not applicable: `ML.PREDICT`, `ML.GLOBAL_EXPLAIN`, `ML.WEIGHTS`, `ML.CONFUSION_MATRIX`, `ML.ROC_CURVE`, `ML.CENTROIDS`.

**ML.EVALUATE output metrics (this type):** `mean_absolute_error`, `mean_squared_error`, `root_mean_squared_error`, `mean_absolute_percentage_error`, `symmetric_mean_absolute_percentage_error`. Metric granularity depends on inputs: with eval data and `perform_aggregation = TRUE` (default), metrics are per `time_series_id_col`; with `FALSE`, per timestamp. Without eval data, ARIMA-fit metrics (e.g. AIC, variance, log_likelihood) are returned per series instead.

**ML.ARIMA_EVALUATE output columns:** `non_seasonal_p`, `non_seasonal_d`, `non_seasonal_q`, `has_drift`, `log_likelihood`, `AIC`, `variance`, `seasonal_periods` (e.g. `[WEEKLY, YEARLY]` or `[NO_SEASONALITY]`), `has_holiday_effect`, `has_spikes_and_dips`, `has_step_changes`, `error_message` (+ the id column). `show_all_candidate_models` (BOOL, default FALSE) returns every candidate instead of only the selected model.

**ML.FORECAST output columns:** id col, `forecast_timestamp`, `forecast_value`, `standard_error`, `confidence_level`, `prediction_interval_lower_bound`, `prediction_interval_upper_bound`, `confidence_interval_lower_bound`, `confidence_interval_upper_bound`. Args: `STRUCT(<n> AS horizon, <p> AS confidence_level)` — default `horizon` is 3, so set it to the trained horizon.

**ML.EXPLAIN_FORECAST adds:** `time_series_type` (`history`/`forecast`), `time_series_data`, `time_series_adjusted_data`, plus decomposition columns `trend`, `seasonal_period_{weekly,daily,monthly,quarterly,yearly}`, `holiday_effect` (and per-holiday columns like `holiday_effect_US_Thanksgiving`), `spikes_and_dips`, `step_changes`.

**Preprocessing support:** Automatic (the entire ARIMA_PLUS pipeline). `TRANSFORM` is supported but **not** when doing custom holiday modeling.

**Hyperparameter tuning:** N/A in the `num_trials` sense. Built-in auto.ARIMA search; tune via `auto_arima_max_order`/`auto_arima_min_order`. `non_seasonal_order` disables the search for a single series.

**Explainability / weights:** No `ML.WEIGHTS`/`ML.GLOBAL_EXPLAIN`/`ML.FEATURE_IMPORTANCE`. Explainability is via `ML.EXPLAIN_FORECAST` (time series decomposition) and `ML.ARIMA_COEFFICIENTS` (`ar_coefficients`, `ma_coefficients`, `intercept_or_drift`).

**Best practices:**
- ARIMA+ is univariate and ignores a validation split — fold `VALIDATE` rows into the training data (repo notebook trains on `TRAIN`+`VALIDATE`).
- Set `horizon` at training to cover test + future; remember `ML.FORECAST`/`ML.EXPLAIN_FORECAST` default `horizon` is 3.
- For 10k+ series, first time a 1k-series query to estimate cost/runtime; lower `auto_arima_max_order` to cut runtime (1 vs 2 cuts runtime >50%); use `time_series_length_fraction`/`max_time_series_length` to trim trend-modeling points; wrap in multi-statement queries.
- Cost scales with the number of candidate models (`auto_arima_max_order`/`min_order`) since input bytes are multiplied per candidate.
- Use `forecast_limit_lower_bound = 0` for non-negative demand.

**Limitations:**
- Min series length 3 time points. Max length 500,000 points when `decompose_time_series=TRUE`, 1,000,000 when FALSE (per series). Max series simultaneously: 100,000,000. Max forecast points: 10,000.
- Holiday effect modeling only for DAILY/WEEKLY series longer than ~1 year; effective for ~5 years. Custom holidays only for `DAILY`/`AUTO_FREQUENCY`(daily) and not with `TRANSFORM`.
- Will **not** aggregate to a coarser granularity: requesting `data_frequency='WEEKLY'` on daily data errors `400 Invalid time series: All input time intervals must be no less than the interval unit specified by data_frequency (WEEKLY)`. Requesting a *finer* granularity (e.g. `HOURLY` on daily data) is allowed and interpolates the gaps.
- Missing/absent time points (null values or absent rows) are linearly interpolated between observed values based on the detected/declared frequency.
- Invalid series (e.g. single point) are silently skipped from forecasts; retrieve their `error_message` via `ML.ARIMA_EVALUATE`.

**Locations:** Available in BigQuery ML non-remote-model locations (regions and multi-regions). See "Locations for non-remote models."

**BigFrames API:** [`bigframes.ml.forecasting.ARIMAPlus`](https://cloud.google.com/python/docs/reference/bigframes/latest/bigframes.ml.forecasting.ARIMAPlus) — `model = ARIMAPlus(horizon=..., auto_arima=True, data_frequency="daily", holiday_region=...)`, `model.fit(X_timestamp_df, y_value_df)`, then `model.predict(horizon=..., confidence_level=0.95)` (= `ML.FORECAST`), `model.predict_explain(...)` (= `ML.EXPLAIN_FORECAST`), `model.coef_` (= `ML.ARIMA_COEFFICIENTS`), `model.register(...)`.

**Repo example (tested):**
- `/home/user/git/vertex-ai-mlops/Applied Forecasting/BQML Univariate Forecasting with ARIMA+.ipynb` — end-to-end: multi-series CREATE MODEL with `time_series_id_col`, `holiday_region=['GLOBAL','US']`, `horizon = HORIZON + TEST`; then `ML.ARIMA_COEFFICIENTS`, `ML.FEATURE_INFO`, `ML.TRAINING_INFO`, `ML.EVALUATE` (`perform_aggregation=TRUE`), `ML.ARIMA_EVALUATE`, `ML.HOLIDAY_INFO`, `ML.FORECAST`, `ML.EXPLAIN_FORECAST`, custom SQL MAPE/MAE/RMSE, and `ML.DETECT_ANOMALIES`.
- `/home/user/git/vertex-ai-mlops/Applied Forecasting/Notes - BQML ARIMA+ Handling of Granularity and Missing Data.ipynb` — demonstrates missing/absent-point interpolation and the granularity rules (WEEKLY-on-daily error; HOURLY-on-daily interpolation).


---

### `ARIMA_PLUS_XREG`  (multivariate time series with external regressors)
- **Description:** Multivariate time-series forecasting model = an `ARIMA_PLUS` model plus *linear external regressors* (side features / covariates). Internally it fits a linear regression on the supplied covariates and models the regression residuals with the full `ARIMA_PLUS` pipeline (auto-ARIMA order selection, holiday effects, spike/dip cleaning, step-change adjustment, seasonal & trend decomposition). Conceptually "ARIMAX": ARIMA's `p`/`d`/`q` plus `b` linear-regressor weights.
- **When to use:**
  - You have a target series **and** time-varying covariates (e.g. promotions, weather, capacity) that improve forecast accuracy.
  - Covariate values **are known/available for the forecast horizon** (required at forecast time — see Limitations).
  - You want ARIMA_PLUS automation (holidays, seasonality, anomaly handling) but with explanatory regressors.
  - You want per-regressor attributions in the forecast (`ML.EXPLAIN_FORECAST`).
- **Category:** time-series.
- **Connection required:** No.
- **Status:** GA. (Multiple-series support via `time_series_id_col` and `ML.DETECT_ANOMALIES` support were both added after the original 2023 Preview; the repo notebook predates these and documents them as "future" — see Repo example notes.)
- **documentation:** [CREATE MODEL for ARIMA_PLUS_XREG](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-multivariate-time-series) · journey/tutorials: [single series tutorial](https://cloud.google.com/bigquery/docs/arima-plus-xreg-single-time-series-forecasting-tutorial), [multiple series tutorial](https://cloud.google.com/bigquery/docs/arima-plus-xreg-multiple-time-series-forecasting-tutorial), [E2E user journey](https://cloud.google.com/bigquery/docs/e2e-journey). Related univariate model: [`ARIMA_PLUS`](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-time-series).

> Built-in foundation forecasting (TimesFM via `AI.FORECAST`) is owned by `../bq-ai-functions/` — see [AI.FORECAST / AI.DETECT_ANOMALIES there](../bq-ai-functions/RESOURCES.md). `ARIMA_PLUS_XREG` is the in-scope BQML *trained-model* forecaster.

**CREATE MODEL syntax:**
```sql
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.MODEL_NAME`
OPTIONS(
  model_type                = 'ARIMA_PLUS_XREG',
  time_series_timestamp_col = 'starttime',
  time_series_data_col      = 'num_trips',
  time_series_id_col        = 'start_station_name',   -- optional: one OR an array of cols -> many series
  data_frequency            = 'DAILY',
  auto_arima_max_order      = 5,
  holiday_region            = ['GLOBAL', 'US'],
  horizon                   = 28
) AS
SELECT starttime, num_trips, avg_tripduration, pct_subscriber, ratio_gender, capacity
FROM `PROJECT_ID.DATASET.forecasting_data_prepped`;
-- every selected column that is NOT the timestamp / data / id col is treated as an external regressor (covariate)
```
The covariates are defined implicitly by the `SELECT` list: any column other than the timestamp, data, and id column(s) becomes a linear external regressor.

**Options (model-specific):**

| Option | Type | Required | Default | Range / Values | Description |
|--------|------|----------|---------|----------------|-------------|
| `model_type` | STRING | Yes | — | `'ARIMA_PLUS_XREG'` | Selects the multivariate ARIMA+ model. |
| `time_series_timestamp_col` | STRING | Yes | — | column name | Timestamp/date column defining the series order. |
| `time_series_data_col` | STRING | Yes | — | column name | Target (data) column to forecast. |
| `time_series_id_col` | STRING or ARRAY\<STRING\> | No | (single series) | one or more column names | Identifies distinct series; enables forecasting many series in one model. |
| `horizon` | INT64 | No | `1000` | \> 0 | Max number of future time points the model can forecast (also fit cost driver). |
| `auto_arima` | BOOL | No | `TRUE` | TRUE/FALSE | Auto-select non-seasonal `p,d,q`. |
| `auto_arima_max_order` | INT64 | No | `5` | typically 1–5 | Upper bound on `p+q` search; higher = slower, more candidates. |
| `auto_arima_min_order` | INT64 | No | `0` | ≥ 0 | Lower bound on order search. |
| `data_frequency` | STRING | No | `'AUTO_FREQUENCY'` | `AUTO_FREQUENCY`, `PER_MINUTE`, `HOURLY`, `DAILY`, `WEEKLY`, `MONTHLY`, `QUARTERLY`, `YEARLY` | Granularity of input rows. |
| `holiday_region` | STRING or ARRAY\<STRING\> | No | (none) | e.g. `'US'`, `['GLOBAL','US']` | Enables holiday-effect modeling for the given region(s). |
| `clean_spikes_and_dips` | BOOL | No | `TRUE` | TRUE/FALSE | Detect & clean outliers before fitting. |
| `adjust_step_changes` | BOOL | No | `TRUE` | TRUE/FALSE | Detect & adjust level/step changes. |
| `decompose_time_series` | BOOL | No | `TRUE` | TRUE/FALSE | Store decomposition (trend/seasonal/holiday) so `ML.EXPLAIN_FORECAST` returns components. |
| `seasonalities` | ARRAY\<STRING\> | No | auto | `NO_SEASONALITY`,`DAILY`,`WEEKLY`,`MONTHLY`,`QUARTERLY`,`YEARLY` | Override auto seasonality detection. |
| `time_series_length_fraction` | FLOAT64 | No | auto | (0,1] | Fraction of series used for trend modeling. |
| `min_time_series_length` | INT64 | No | auto | ≥ 0 | Min points required for trend modeling. |
| `max_time_series_length` | INT64 | No | auto | ≥ 0 | Cap on most-recent points used for trend modeling. |
| `trend_smoothing_window_size` | INT64 | No | auto | ≥ 0 | Trend smoothing window. |
| `kms_key_name` | STRING | No | (none) | KMS resource | CMEK for the model. |

**Supported lifecycle functions:** `ML.FORECAST`, `ML.EXPLAIN_FORECAST` (forecast + trend/seasonal/holiday components + **per-regressor attributions**), `ML.EVALUATE`, `ML.ARIMA_EVALUATE` (per-series ARIMA stats), `ML.ARIMA_COEFFICIENTS` (AR/MA coefficients **plus the external-regressor weights**), `ML.FEATURE_INFO`, `ML.TRAINING_INFO`, `ML.HOLIDAY_INFO`, `ML.DETECT_ANOMALIES` (anomaly detection; added post-2023). No `ML.PREDICT`, no `ML.WEIGHTS`/`ML.GLOBAL_EXPLAIN`/`ML.FEATURE_IMPORTANCE`.

**ML.EVALUATE output metrics (this type):** `mean_absolute_error`, `mean_squared_error`, `root_mean_squared_error`, `mean_absolute_percentage_error`, `symmetric_mean_absolute_percentage_error`. With `time_series_id_col`, `ML.EVALUATE` evaluates each series independently. Behavior depends on inputs: if eval (test) data is supplied, forecast-accuracy metrics are returned; `perform_aggregation = TRUE` gives metrics per series, `FALSE` gives per-timestamp. (For ARIMA model-fit stats — `AIC`, `log_likelihood`, `variance`, `p/d/q`, `seasonal_periods`, `has_holiday_effect`, `has_spikes_and_dips`, `has_step_changes` — use `ML.ARIMA_EVALUATE`.)

**Preprocessing support:** automatic (ARIMA+ pipeline: missing-value handling, spike/dip cleaning, step-change adjustment, holiday & seasonal decomposition). Covariates are consumed directly from the `SELECT` list. TRANSFORM is **not** supported for this model type.

**Hyperparameter tuning:** Not supported (`num_trials`/HP tuning N/A for ARIMA_PLUS_XREG). Order selection is handled internally by `auto_arima`; tune `auto_arima_max_order` / `auto_arima_min_order` manually if needed.

**Explainability / weights:** `ML.GLOBAL_EXPLAIN` / `ML.FEATURE_IMPORTANCE` / `ML.WEIGHTS` do not apply. Explainability comes from (1) `ML.ARIMA_COEFFICIENTS` — returns AR/MA coefficients and the **regression `weight` per processed input** (incl. `__INTERCEPT__`); and (2) `ML.EXPLAIN_FORECAST` — returns trend, seasonal, holiday effects, spikes/dips, step changes, and `attribution_<regressor>` columns per timestamp. No `enable_global_explain` option.

**Best practices:**
- Provide covariate values for the **entire forecast horizon** — `ML.FORECAST`/`ML.EXPLAIN_FORECAST` require the side features as input (the target column is omitted in that input).
- Include validation data in training: ARIMA is fit on the historical series and does not consume a separate validation split — fold TRAIN+VALIDATE into the training `SELECT` (notebook does this).
- Set `horizon` at/above the largest forecast you'll request; `ML.FORECAST` default `horizon` is small (3) and must be passed via `STRUCT(... AS horizon)`.
- Drop covariates that are all-NULL for some series before training a multi-series model (notebook drops `capacity` for that reason).
- Use `ML.ARIMA_EVALUATE` (not the console Evaluation tab) to inspect all series — the console shows only the first 100.

**Limitations:**
- Covariates must be known at forecast time (no built-in handling of unknown future covariates).
- Invalid series (e.g. single-point) are silently skipped in multi-series fits; a warning is surfaced via `ML.ARIMA_EVALUATE.error_message`.
- No TRANSFORM, no HP tuning, no `ML.PREDICT`.
- Multi-series cost scales with series count and `horizon` (notebook: ~34 s single series; ~5 min for 12 series via `EXECUTE IMMEDIATE` loop).
- Regressors are **linear**; non-linear effects must be feature-engineered into covariates.

**Locations:** Available in BigQuery ML regions/multi-regions; no external connection needed. CMEK via `kms_key_name`.

**BigFrames API:** `bigframes.ml.forecasting.ARIMAPlus` covers univariate ARIMA_PLUS; external-regressor (XREG) multivariate forecasting is best driven via SQL `CREATE MODEL`. (No dedicated `ARIMAPlusXReg` class — treat as "use SQL.")

**Repo example (tested):** `/home/user/git/vertex-ai-mlops/Applied Forecasting/BQML Multivariate Forecasting with ARIMA+ XREG.ipynb` — Citibike daily trips near Central Park with covariates (`avg_tripduration`, `pct_subscriber`, `ratio_gender`, `capacity`). Shows full lifecycle: CREATE MODEL with `holiday_region=['GLOBAL','US']` + `auto_arima_max_order=5`; `ML.ARIMA_COEFFICIENTS` (regressor weights), `ML.FEATURE_INFO`, `ML.TRAINING_INFO`, `ML.EVALUATE` (the 5 forecast metrics), `ML.ARIMA_EVALUATE`, `ML.HOLIDAY_INFO`, `ML.FORECAST` (covariates supplied for horizon), `ML.EXPLAIN_FORECAST` (61 cols incl. `attribution_*`), and custom SQL metrics (MAPE/MAE/pMAE/MSE/RMSE/pRMSE). NOTE: notebook predates GA `time_series_id_col` for XREG — it forecasts one series via `WHERE` and demonstrates two multi-series workarounds (`EXECUTE IMMEDIATE FOR..IN` loop; async Python client jobs). Today a single model with `time_series_id_col=['...']` replaces the workaround.


---

### `CONTRIBUTION_ANALYSIS`
- **Description:** Trains a contribution analysis (a.k.a. key-driver) model that detects which segments of multi-dimensional data most explain a change in a summable metric, by comparing a **test** set against a **control** set. It is not a predictive model — there is no `ML.PREDICT`; you create the model and then read insights from it with `ML.GET_INSIGHTS`.
- **When to use:**
  - Explain *why* a metric moved (e.g., revenue, conversions) across two periods or two cohorts.
  - Surface the specific dimension combinations (segments) driving the largest / most-unexpected changes.
  - You need capabilities beyond the model-free `AI.KEY_DRIVERS` — i.e., **summable-by-ratio** or **summable-by-category** metrics, or more dimensions than `AI.KEY_DRIVERS` supports.
- **Category:** unsupervised (insight/segment analysis).
- **Connection required:** No.
- **Status:** GA (GA announced 2025-05-12; Preview since 2024-09).
- **documentation:** [CREATE MODEL for contribution analysis](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-contribution-analysis) · [Contribution analysis overview](https://cloud.google.com/bigquery/docs/contribution-analysis) · [Get insights (summable)](https://cloud.google.com/bigquery/docs/get-contribution-analysis-insights)

> **SCOPE / CROSS-LINK:** The simplified, model-free equivalent — `AI.KEY_DRIVERS` (a single TVF, no `CREATE MODEL`) — is OWNED by `../bq-ai-functions/RESOURCES.md` (`AI.KEY_DRIVERS` entry, incl. inputs/outputs and the "model vs. function" comparison table). For most key-driver use cases that function is recommended (simpler, faster, auto-pruning). Reach for the `CONTRIBUTION_ANALYSIS` **model** documented here only when you need summable-by-ratio / summable-by-category metrics or more dimensions than `AI.KEY_DRIVERS` allows. **Do not duplicate the AI.KEY_DRIVERS reference here.**

**CREATE MODEL syntax:**
```sql
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.MODEL_NAME`
OPTIONS(
  model_type = 'CONTRIBUTION_ANALYSIS',
  contribution_metric = 'SUM(sales)/COUNT(DISTINCT user_id)',
  dimension_id_cols = ['device_category', 'country', 'site_traffic_source'],
  is_test_col = 'is_test',
  top_k_insights_by_apriori_support = 15,
  pruning_method = 'PRUNE_REDUNDANT_INSIGHTS'
) AS
SELECT * FROM `PROJECT_ID.DATASET.input_data`;
```
The input query must contain **exactly** the columns referenced in `contribution_metric`, `dimension_id_cols`, and `is_test_col`.

**Options (model-specific):**

| Option | Type | Required | Default | Range / Values | Description |
|--------|------|----------|---------|----------------|-------------|
| `model_type` | STRING | Yes | — | `'CONTRIBUTION_ANALYSIS'` | Selects the contribution analysis model. |
| `contribution_metric` | STRING | Yes | — | `SUM(x)` (summable); `SUM(num)/SUM(den)` (summable-ratio); `SUM(x)/COUNT(DISTINCT cat)` (summable-by-category) | Metric to analyze. Metric column values must be non-negative unless `min_apriori_support = 0`. |
| `dimension_id_cols` | ARRAY\<STRING\> | No | all non-metric / non-test cols | columns of type INT64, BOOL, or STRING | Dimension columns used to form segments. Rows with NULL dimension values are dropped. |
| `is_test_col` | STRING | Yes | — | a BOOL column | Flags each row as test (`TRUE`) vs. control (`FALSE`). |
| `min_apriori_support` | FLOAT64 | No | `0.1` | `[0, 1]` | Min segment-size support to include a segment. Mutually exclusive with `top_k_insights_by_apriori_support`. |
| `top_k_insights_by_apriori_support` | INT64 | No | — | positive integer | Return the top-K insights by apriori support; model sets the threshold automatically. Mutually exclusive with `min_apriori_support`. |
| `pruning_method` | STRING | No | `'NO_PRUNING'` | `'NO_PRUNING'` \| `'PRUNE_REDUNDANT_INSIGHTS'` | `PRUNE_REDUNDANT_INSIGHTS` drops a segment whose dimensions are a subset of a more descriptive segment with an equal metric value (the `all` row is never pruned). |

**Supported lifecycle functions:** `ML.GET_INSIGHTS` (the only insight-retrieval function for this type). Standard model-management applies (`ML.MODEL_INFO` via `INFORMATION_SCHEMA`, drop/rename). **Not supported:** `ML.PREDICT`, `ML.EVALUATE`, `ML.WEIGHTS`, `ML.GLOBAL_EXPLAIN`, `ML.FEATURE_IMPORTANCE`, hyperparameter tuning, `TRANSFORM`.

**ML.GET_INSIGHTS output metrics (this type):**

| Column | Description |
|--------|-------------|
| `contributors` | The dimension segment, e.g. `vendor_name=SAZERAC COMPANY INC`; `all` for the overall row. |
| `metric_test` | Metric value over the test set. |
| `metric_control` | Metric value over the control set. |
| `difference` | Raw change (`metric_test` − `metric_control`). |
| `relative_difference` | Proportional change. |
| `unexpected_difference` | Change beyond what the overall growth rate predicts. |
| `relative_unexpected_difference` | `unexpected_difference` as a proportion. |
| `apriori_support` | Segment-size support (`1.0` for the `all` row). |
| `contribution` | `ABS(difference)`; output is sorted by this descending. |

**Preprocessing support:** N/A — no `TRANSFORM` clause; the input query columns are consumed directly.

**Hyperparameter tuning:** Not supported.

**Explainability / weights:** N/A — the model *is* the explanation; insights come from `ML.GET_INSIGHTS`, not from the `ML.WEIGHTS` / `ML.GLOBAL_EXPLAIN` family.

**Best practices:**
- Prefer `top_k_insights_by_apriori_support` for predictable runtime/output size; it lets the model auto-tune the apriori threshold.
- Use `PRUNE_REDUNDANT_INSIGHTS` to remove subset-redundant segments and keep the most descriptive rows.
- Sort/filter insights by `contribution` (biggest movers) or `unexpected_difference` (segments defying the overall trend).
- For straightforward summable-metric key-driver questions, evaluate `AI.KEY_DRIVERS` first (see cross-link) — it skips the `CREATE MODEL` step.

**Limitations:**
- Metric column values must be non-negative unless `min_apriori_support = 0`.
- `min_apriori_support` and `top_k_insights_by_apriori_support` are mutually exclusive.
- Dimension columns must be INT64, BOOL, or STRING; NULL-dimension rows are removed.
- No `ML.PREDICT` / `ML.EVALUATE`; produces insights only.

**Locations:** Standard BigQuery ML region/multi-region support; no external connection or endpoint involved.

**BigFrames API:** No dedicated class; run the `CREATE MODEL` / `ML.GET_INSIGHTS` SQL via `session.read_gbq_query()` or `%%bigquery` magics.

**Repo example (tested):** None yet — no tested `CONTRIBUTION_ANALYSIS` example found in the bq-ml repo scout. (Add a notebook/SQL path here once built.)


---

### Imported models (TENSORFLOW, TENSORFLOW_LITE, ONNX, XGBOOST)

Imported models let you bring a model trained **outside** BigQuery — in TensorFlow, TensorFlow Lite,
ONNX, or XGBoost — into BigQuery ML from Cloud Storage and run inference with `ML.PREDICT` natively
inside BigQuery compute. This is the BigQuery ML **Inference Engine**: same SQL API, no Vertex AI
endpoint to deploy, manage, or pay for. Contrast with **remote models** (`CREATE MODEL ... REMOTE WITH
CONNECTION`), where the model runs on an external endpoint and BigQuery calls out to it — imported
models run in BigQuery itself but are size-limited and require pre-formatted (often numeric/ARRAY)
inputs.

- **Common shape:** all four are `CREATE MODEL ... OPTIONS(MODEL_TYPE='...', MODEL_PATH='gs://...')`.
- **Connection required:** **No connection** for reading the GCS model file (BigQuery uses the
  credentials of the user running `CREATE MODEL`). A connection *is* required only when serving an
  imported model over an **object table** (capacity/reservation pricing only).
- **No training, no preprocessing, no `TRANSFORM`, no HP tuning, no `ML.EVALUATE`.** The model is
  frozen at import; you supply inputs already in the model's expected schema/format.
- **documentation:** [Imported models journey](https://cloud.google.com/bigquery/docs/e2e-journey-import)
  · [Inference overview](https://cloud.google.com/bigquery/docs/inference-overview)
  · [ML.PREDICT](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-predict)

**Capability summary (all imported types):**

| Capability | Imported models |
|---|---|
| TRANSFORM clause | No |
| Hyperparameter tuning | No |
| `enable_global_explain` | No |
| `ML.EVALUATE` / `ML.CONFUSION_MATRIX` / `ML.ROC_CURVE` | No |
| Weights / feature attribution | Only `ML.FEATURE_IMPORTANCE` (XGBOOST only) |
| `ML.EXPLAIN_PREDICT` | TENSORFLOW only (memory-heavy; can OOM) |
| `ML.FEATURE_INFO` | No |
| Object-table serving | Yes — capacity/reservation pricing only (no on-demand) |

---

### `TENSORFLOW`
- **Description:** Imports a TensorFlow **SavedModel** for inference inside BigQuery ML.
- **When to use:**
  - You trained a TF model elsewhere (Vertex AI, on-prem) and want SQL-native serving.
  - You need feature-level attributions for a TF model via `ML.EXPLAIN_PREDICT`.
  - Your inputs include `tf.train.Example` / SparseTensor features BigQuery can auto-convert.
- **Category:** imported. **Connection required:** No (object-table serving needs reservations). **Status:** GA.
- **documentation:** [CREATE MODEL (TensorFlow)](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-tensorflow)

**CREATE MODEL syntax:**
```sql
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.MODEL_NAME`
OPTIONS(
  MODEL_TYPE = 'TENSORFLOW',
  MODEL_PATH = 'gs://bucket/path/to/saved_model/*'
  -- [, KMS_KEY_NAME = 'projects/.../cryptoKeys/my_key']
);
```

**Options:**

| Option | Type | Required | Default | Values | Description |
|--------|------|----------|---------|--------|-------------|
| `MODEL_TYPE` | STRING | Yes | — | `'TENSORFLOW'` | Model type. |
| `MODEL_PATH` | STRING | Yes | — | `gs://...` URI (often ends `/*`) | GCS URI of the SavedModel to import. |
| `KMS_KEY_NAME` | STRING | No | — | CMEK resource name | Customer-managed encryption key for the model. |

**Supported lifecycle functions:** `ML.PREDICT`, `ML.EXPLAIN_PREDICT`. Inputs may be dense Tensors,
SparseTensors (pass as dense arrays — BQ converts), or `tf.train.Example` (BQ auto-maps columns).
RaggedTensors are not supported.
**Not supported:** `ML.CONFUSION_MATRIX`, `ML.EVALUATE`, `ML.FEATURE_INFO`, `ML.ROC_CURVE`, `ML.TRAINING_INFO`, `ML.WEIGHTS`.

**Data types:** `tf.int*`/`tf.uint*` → `INT64`; `tf.float16/32/64`, `tf.bfloat16` → `FLOAT64`;
`tf.bool` → `BOOL`; `tf.string` → `STRING`. Complex, quantized (`qint`/`quint`), `tf.resource`, `tf.variant` unsupported.

**Limitations:** Must be a SavedModel that already exists in GCS; frozen at import. 450 MB file-size
limit. In-RAM prediction memory limit ~250 MB (`ML.EXPLAIN_PREDICT` can trigger *TensorFlow worker out
of memory*). GraphDef \< v20, unreleased TF versions, custom/`tf.contrib` ops, and RaggedTensors are
unsupported. Object-table use is reservation-only.
**BigFrames API:** `bigframes.ml.imported.TensorFlowModel(model_path=...)`.
**Repo example (tested):** No TensorFlow-import notebook in repo; the ONNX path below is the repo's tested import workflow.

---

### `TENSORFLOW_LITE`
- **Description:** Imports a TensorFlow Lite (`.tflite`) model for inference.
- **When to use:** Edge/quantized TF Lite artifacts you want to serve in SQL; TF Text-based preprocessing graphs (within op limits).
- **Category:** imported. **Connection required:** No (object-table serving needs reservations). **Status:** GA.
- **documentation:** [CREATE MODEL (TFLite)](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-tflite)

**CREATE MODEL syntax:**
```sql
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.MODEL_NAME`
OPTIONS(
  MODEL_TYPE = 'TENSORFLOW_LITE',
  MODEL_PATH = 'gs://bucket/path/to/tflite_model/*'
);
```

**Options:** identical set to TENSORFLOW (`MODEL_TYPE='TENSORFLOW_LITE'`, `MODEL_PATH`, optional `KMS_KEY_NAME`).

**Supported lifecycle functions:** `ML.PREDICT` **only**.
**Data types:** integer types → `INT64`; `FLOAT16/32/64` → `FLOAT64`; `BOOL` → `BOOL`; `STRING` → `STRING`. Complex, `RESOURCE`, `VARIANT` unsupported.
**Limitations:** Must be `.tflite` format, stored in GCS, exists before import. **450 MB** size limit.
Only TensorFlow core ops + TensorFlow Text ops supported; **SentencePiece operators not supported**;
sparse tensors not supported. Object-table use is reservation-only (no on-demand).
**BigFrames API:** No direct equivalent class (use TensorFlow/ONNX imported-model classes for the TF/ONNX paths).
**Repo example (tested):** None in repo.

---

### `ONNX`
- **Description:** Imports an Open Neural Network Exchange (`.onnx`) model — the framework-agnostic
  interchange format. Lets you serve scikit-learn, PyTorch, XGBoost, etc. once converted to ONNX.
- **When to use:**
  - You have a scikit-learn / PyTorch model and want SQL-native inference without an endpoint.
  - Inputs are numeric/tabular or pre-tokenized ARRAYs (best fit for ONNX import).
  - You want one portable format across frameworks.
- **Category:** imported. **Connection required:** No (object-table serving needs reservations). **Status:** GA.
- **documentation:** [CREATE MODEL (ONNX)](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-onnx)
  · Tutorials: [scikit-learn → ONNX](https://cloud.google.com/bigquery/docs/making-predictions-with-sklearn-models-in-onnx-format)

**CREATE MODEL syntax:**
```sql
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.MODEL_NAME`
OPTIONS(
  MODEL_TYPE = 'ONNX',
  MODEL_PATH = 'gs://bucket/path/to/onnx_model/*'   -- or '.../model.onnx'
);
```

**Options:** `MODEL_TYPE='ONNX'`, `MODEL_PATH` (accepts a directory wildcard `/*` or a direct
`model.onnx` path), optional `KMS_KEY_NAME`.

**Supported lifecycle functions:** `ML.PREDICT` **only**. (`ML.FEATURE_INFO` is *not* supported — verify
import via the Python/BigFrames client, e.g. `bq.get_model(...)`.)
**Data types:** ONNX **Tensor** type only. Int/uint element types → `INT64`; `FLOAT16/BFLOAT16/FLOAT/DOUBLE` → `FLOAT64`; `BOOL` → `BOOL`; `STRING` → `STRING`. Map, Opaque, Sequence, Optional, Sparse-tensor value types unsupported.
**Limitations:** `.onnx` format only; `ML.PREDICT` only; **450 MB** size limit. Runs on **ONNX Runtime
1.12.0** — your model's opset/IR version must be compatible (the repo HuggingFace notebook downgrades
IR version to 8 to satisfy this). Only the Tensor value type is supported. Object-table use is reservation-only.
**Gotcha (scikit-learn classifiers):** sklearn-onnx emits a *sequence of map* for probabilities by
default → import error `unsupported ONNX type: ONNX_TYPE_SEQUENCE`. Fix at conversion time with
`zipmap=False` (or `zipmap='columns'`). The repo notebook does exactly this.
**BigFrames API:** `bigframes.ml.imported.ONNXModel(model_path=...)`.
**Repo examples (tested):**
- `/home/user/git/vertex-ai-mlops/03 - BigQuery ML (BQML)/BQML Import Model - scikit-learn.ipynb` —
  scikit-learn Pipeline → ONNX (`skl2onnx.convert_sklearn(..., options={id(model): {'zipmap': False}})`),
  uploaded to GCS, then `CREATE OR REPLACE MODEL ... OPTIONS(MODEL_TYPE='ONNX', MODEL_PATH='gs://.../*')`
  and `ML.PREDICT` returning `label` + `probabilities`.
- `/home/user/git/vertex-ai-mlops/MLOps/Serving/SQL Inference/BQML Import Model via ONNX.ipynb` —
  HuggingFace DistilBERT (PyTorch) → ONNX via `torch.onnx.export`, float16 + `ir_version=8` to fit the
  250 MB practical/450 MB hard limit and ONNX Runtime 1.12; pre-tokenized ARRAY inputs
  (`input_ids`, `attention_mask`); `ML.PREDICT` returns `logits` (softmax/argmax done in SQL). Shows
  the import-vs-remote tradeoff: ONNX import needs the caller to tokenize and fits small numeric models.

---

### `XGBOOST`
- **Description:** Imports an XGBoost Booster model (`.bst` or `.json`) for inference.
- **When to use:**
  - You trained XGBoost outside BigQuery and want SQL serving plus tree feature importance.
  - You need an explicit input/output schema mapping (`INPUT(...) OUTPUT(...)`).
- **Category:** imported. **Connection required:** No (object-table serving needs reservations). **Status:** GA.
- **documentation:** [CREATE MODEL (XGBoost)](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-xgboost)

**CREATE MODEL syntax:**
```sql
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.MODEL_NAME`
INPUT(f1 INT64, f2 FLOAT64, f3 FLOAT64)
OUTPUT(predicted_label FLOAT64)
OPTIONS(
  MODEL_TYPE = 'XGBOOST',
  MODEL_PATH = 'gs://bucket/path/to/xgboost_model/*'
);
```

**Options & clauses:**

| Option / Clause | Type | Required | Description |
|---|---|---|---|
| `MODEL_TYPE` | STRING | Yes | `'XGBOOST'`. |
| `MODEL_PATH` | STRING | Yes | GCS URI of the `.bst`/`.json` Booster file. |
| `KMS_KEY_NAME` | STRING | No | CMEK to encrypt the model. |
| `INPUT(field_name field_type, …)` | clause | Conditional | Input schema. **Optional only if** `feature_names` AND `feature_types` are both stored in the model file (see XGBoost Model IO / JSON Schema). Input types must be supported numeric types; names must match `feature_names`. |
| `OUTPUT(field_name field_type, …)` | clause | Conditional | Output schema. Output type must be `FLOAT64`. |

**Supported lifecycle functions:** `ML.PREDICT` and **`ML.FEATURE_IMPORTANCE`** (the only imported type
that supports a feature-attribution function).
**Limitations:** `.bst` or `.json` (Booster) format only; model must exist in GCS before import.
**250 MB** size limit; **840 MB** memory limit to load+run (reduce trees / depth, or save via XGBoost's
default `save_model` to shrink). Object-table use is reservation-only.
**BigFrames API:** `bigframes.ml.imported.XGBoostModel(model_path=..., input=..., output=...)`.
**Repo example (tested):** None in repo (scikit-learn/PyTorch are imported via the ONNX path above).

---

**Connection matrix note:** Imported models occupy the "imported" column of the connection matrix —
**no connection** for standard `ML.PREDICT` on the GCS-loaded model; a Cloud Resource connection +
reservation pricing only when serving against an object table.


---

### `REMOTE` (Remote model over a Vertex AI endpoint — the mechanism)

- **Description:** A remote model registers an external prediction service as a BigQuery ML model so it can be queried in-warehouse with `ML.PREDICT`. This entry covers the **generic mechanism**: `CREATE MODEL ... REMOTE WITH CONNECTION` pointing at a **custom model deployed to a Vertex AI prediction endpoint** (any framework — TensorFlow, PyTorch, scikit-learn, XGBoost, custom container). BigQuery sends rows to the endpoint through a Cloud Resource Connection and merges the returned predictions back into the result set. No model artifacts live in BigQuery; the model runs on the endpoint's infrastructure (incl. GPUs).
- **When to use:**
  - The model is already hosted on a Vertex AI endpoint for online serving and you want SQL-native inference.
  - The model is too large to import into BigQuery (the ONNX/imported path caps at ~250 MB) or needs GPU/custom-container serving.
  - You want one SQL inference surface (`ML.PREDICT`) over a model whose framework BigQuery can't train or import.
  - You want scheduled queries for automated batch scoring without a separate Python serving step.
- **Category:** remote.
- **Connection required:** **Yes** — a BigQuery **Cloud Resource Connection** (`CLOUD_RESOURCE`). `DEFAULT` connection is also accepted.
- **Status:** GA.
- **documentation:**
  - CREATE MODEL (custom models on Vertex AI endpoints): https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-remote-model-https
  - Remote model index (LLMs / embeddings / Cloud AI services variants): https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-remote-model
  - Tutorial — Make predictions with remote models on Vertex AI: https://cloud.google.com/bigquery/docs/bigquery-ml-remote-model-tutorial
  - Cloud Resource Connection: https://cloud.google.com/bigquery/docs/create-cloud-resource-connection
  - `ML.PREDICT`: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-predict

> **Scope note (foundation / LLM endpoints):** Remote models over Vertex AI **foundation/LLM** endpoints (Gemini text generation, foundation-model embeddings, Cloud AI services, fine-tuned Gemini) are documented in `../bq-ai-functions/` — see the remote-model LLM pattern there, plus `ML.GENERATE_TEXT`, `AI.GENERATE_*`, foundation-model `ML.GENERATE_EMBEDDING` / `AI.GENERATE_EMBEDDING`, and `ML.DOCUMENT_PROCESS`. This entry covers ONLY the custom-endpoint mechanism queried with `ML.PREDICT`.

**CREATE MODEL syntax:**
```sql
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.MODEL_NAME`
INPUT  (field_name field_type [, ...])
OUTPUT (field_name field_type [, ...])
REMOTE WITH CONNECTION `PROJECT_ID.REGION.CONNECTION_ID`   -- or:  REMOTE WITH CONNECTION DEFAULT
OPTIONS(
  ENDPOINT = 'https://REGION-aiplatform.googleapis.com/v1/projects/PROJECT_ID/locations/REGION/endpoints/ENDPOINT_ID'
);
```

**Options:**

| Option | Type | Required | Default | Range / Values | Description |
|--------|------|----------|---------|----------------|-------------|
| `ENDPOINT` | STRING | Yes | — | Shared public endpoint URL `https://\<region\>-aiplatform.googleapis.com/v1/projects/\<project\>/locations/\<region\>/endpoints/\<endpoint_id\>` | The Vertex AI endpoint serving the custom model. Dedicated public endpoints, Private Service Connect endpoints, and private endpoints are NOT supported. |

(No HP-tuning options apply — a remote model is a registration, not a training run. The request batch size is managed by BigQuery; the endpoint receives batches of instances, defaulting to ~128 instances per request.)

**INPUT / OUTPUT clauses (required for custom endpoints):**

| Clause | Rule |
|--------|------|
| `INPUT (...)` | Must list the fields BigQuery sends as the `instances` payload. Field **names must match** the endpoint request's field names. Supported types incl. `INT64`, `FLOAT64`, `STRING`, `BOOL`, `ARRAY\<...\>`. |
| `OUTPUT (...)` | Must list the fields BigQuery reads from each `predictions` element. Field **names must match** the endpoint response's field names. **Single-output special case:** if the endpoint returns one unnamed output, any name may be used. |

BigQuery wraps each row's `INPUT` columns into one element of the `instances` array, and unpacks each `predictions` element back into the `OUTPUT` columns. `ML.PREDICT` also returns a `remote_model_status` column reporting per-row call status.

**Supported lifecycle functions:** **`ML.PREDICT` only.** Training/evaluation lifecycle functions do not apply — the model is not trained in BigQuery, so `ML.EVALUATE`, `ML.WEIGHTS`/`ML.ADVANCED_WEIGHTS`, `ML.GLOBAL_EXPLAIN`, `ML.FEATURE_IMPORTANCE`, `ML.EXPLAIN_PREDICT`, `ML.CONFUSION_MATRIX`, etc. are N/A. (You can compute evaluation metrics yourself in SQL over `ML.PREDICT` output joined to labels.)

**ML.EVALUATE output metrics (this type):** N/A — `ML.EVALUATE` is not supported for remote models over custom endpoints.

**Preprocessing support:** None inside BigQuery. `TRANSFORM` is not applied; any feature engineering must happen in the `ML.PREDICT` input subquery or inside the served container.

**Hyperparameter tuning:** N/A — no training occurs.

**Explainability / weights:** N/A in BigQuery (no `enable_global_explain`, no weights). Explanations, if any, must be produced by the Vertex AI endpoint and surfaced as `OUTPUT` fields.

**Best practices:**
- Two-step setup: (1) create a `CLOUD_RESOURCE` connection, (2) grant its auto-provisioned service account `roles/aiplatform.user`, then create the model. IAM propagation can take up to ~60s — retry `CREATE MODEL` if it fails with a permission error.
- Keep the connection in the **same location/region as the dataset** holding the model (location requirement).
- Reuse one connection across multiple remote models.
- Make `OUTPUT` names/types exactly mirror the endpoint response to avoid silent NULLs.
- Push filters/limits into the `ML.PREDICT` input subquery to control endpoint call volume and cost.

**Limitations:**
- `INPUT` and `OUTPUT` are **required** for custom-model endpoints.
- Only **shared public** Vertex AI endpoints — dedicated public, PSC, and private endpoints are unsupported.
- Only `ML.PREDICT` is supported; no evaluation/explainability/weights lifecycle functions.
- Cost has two parts: Vertex AI endpoint compute + the BigQuery query; latency includes a network round-trip per batch.

**Locations:** Connection must match the dataset's BigQuery location (e.g., dataset in `US` → connection in `US`). Endpoint region is encoded in the `ENDPOINT` URL.

**BigFrames API:** No direct training equivalent; remote-endpoint inference is generally orchestrated via SQL/`ML.PREDICT` or the Vertex AI SDK (`aiplatform.Endpoint.predict`).

**Repo example (tested):**
- `/home/user/git/vertex-ai-mlops/03 - BigQuery ML (BQML)/BQML Remote Model on Vertex AI Endpoint.ipynb` — registers an existing autoencoder endpoint as a remote model: derives `INPUT`/`OUTPUT` from the TF SavedModel signature, creates a `CLOUD_RESOURCE` connection with `bq mk --connection`, grants `roles/aiplatform.user`, then `CREATE OR REPLACE MODEL ... INPUT(...) OUTPUT(...) REMOTE WITH CONNECTION ... OPTIONS(endpoint=...)` and scores via `ML.PREDICT`.
- `/home/user/git/vertex-ai-mlops/MLOps/Serving/SQL Inference/BQML Remote Model on Vertex AI Endpoint.ipynb` — end-to-end: deploys a HuggingFace sentiment container to a Vertex AI endpoint, creates the connection via `ConnectionServiceClient`, then `INPUT (text STRING) OUTPUT (label STRING, score FLOAT64) REMOTE WITH CONNECTION ... OPTIONS(endpoint=...)`. Shows single-row, multi-row (`UNNEST`), and table batch scoring with business logic; output includes the `remote_model_status` column. Also contrasts remote model vs ONNX import.


---

### `TRANSFORM_ONLY`
- **Description:** A model that contains *only* a `TRANSFORM` clause and no learning algorithm. It captures a set of feature‑preprocessing rules (plus the statistics computed at creation time, e.g. the mean/stddev used by `ML.STANDARD_SCALER`) as a reusable, exportable model object. There is no training of a predictive estimator — the model output is the preprocessed data, materialized via `ML.TRANSFORM`.
- **When to use:**
  - Decouple feature engineering from model training so the same preprocessing can be reused across many models and serving paths.
  - Build modular, feature‑level (feature‑store‑like) transforms and chain them into a pipeline with CTEs (`WITH`) or a view.
  - Guarantee training/serving consistency — computed statistics are frozen at creation, eliminating training/serving skew.
  - Run large‑scale batch feature transformations efficiently.
- **Category:** transform-only.
- **Connection required:** No. (A connection is only needed if you later `EXPORT MODEL` to GCS or register to Vertex AI — those are optional lifecycle steps.)
- **Status:** GA.
- **documentation:** [CREATE MODEL for transform-only models](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-transform) · [ML.TRANSFORM function](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-transform) · [TRANSFORM clause](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create#transform) · [Perform feature engineering with the TRANSFORM clause](https://cloud.google.com/bigquery/docs/bigqueryml-transform)

**CREATE MODEL syntax:**
```sql
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.MODEL_NAME`
TRANSFORM(
  -- pass-through columns + transformed columns (named aliases required)
  species, island, sex,
  ML.ROBUST_SCALER(body_mass_g) OVER() AS body_mass_g,
  ML.STANDARD_SCALER(culmen_length_mm) OVER() AS culmen_length_mm
)
OPTIONS(
  model_type = 'TRANSFORM_ONLY'
  -- optional: model_registry = 'VERTEX_AI', VERTEX_AI_MODEL_ID = '...'
)
AS SELECT * FROM `PROJECT_ID.DATASET.SOURCE_TABLE`;
```

**Options (model-specific):**

| Option | Type | Required | Default | Range / Values | Description |
|--------|------|----------|---------|----------------|-------------|
| `model_type` | STRING | Yes | — | `'TRANSFORM_ONLY'` | Selects the transform-only model. No learning options apply. |
| `model_registry` | STRING | No | none | `'VERTEX_AI'` | Optionally register the transform model to Vertex AI Model Registry. |
| `vertex_ai_model_id` | STRING | No | none | any | Model ID used in the registry when `model_registry='VERTEX_AI'`. |
| `vertex_ai_model_version_aliases` | ARRAY\<STRING\> | No | none | any | Version aliases for the registered model. |

(No HP‑tuning, label, data‑split, or learning options exist for this type — there is no estimator to train. Any unsupported learning option causes an error.)

**TRANSFORM clause rules (the `select_list`):**
- Pass columns through untransformed via `*`, `* EXCEPT(...)`, or by naming them.
- Transform columns with preprocessing functions; every transformed/derived column **must** have a named alias (anonymous expressions like `a + b` are not allowed; `a + b AS c` is).
- Omitting a `query_statement` column from `TRANSFORM` drops it from the output.
- Output columns may be any BigQuery‑supported type.
- Analytic preprocessing functions (scalers, imputer, etc.) use the `... OVER()` syntax so statistics are computed over the creation data and frozen into the model.

**Applying the model (consume with `ML.TRANSFORM`):**
```sql
SELECT * FROM ML.TRANSFORM(
  MODEL `PROJECT_ID.DATASET.MODEL_NAME`,
  (SELECT * FROM `PROJECT_ID.DATASET.NEW_DATA`)  -- or TABLE `...`
);
```
Input column names must match the names in the model's `TRANSFORM` clause, with implicitly coercible types. `ML.TRANSFORM` returns exactly the columns the `TRANSFORM` clause produces.

**Supported lifecycle functions:** `ML.TRANSFORM` (the primary/only way to apply it), `ML.FEATURE_INFO` (pre‑transform summary stats), `EXPORT MODEL`, and BQ model management (`ALTER MODEL`, `DROP MODEL`, `bq ls`). NOT supported: `ML.PREDICT`, `ML.EVALUATE`, `ML.WEIGHTS`/`ML.ADVANCED_WEIGHTS`, `ML.GLOBAL_EXPLAIN`, `ML.FEATURE_IMPORTANCE`, `ML.EXPLAIN_PREDICT` — there is no trained estimator to predict/evaluate/explain.

**ML.EVALUATE output metrics (this type):** N/A — `ML.EVALUATE` is not applicable (no estimator, no labels).

**Preprocessing support:** This IS the preprocessing primitive. Supports the full BQML preprocessing function family inside `TRANSFORM`: general (`ML.IMPUTER`); numeric (`ML.STANDARD_SCALER`, `ML.ROBUST_SCALER`, `ML.MIN_MAX_SCALER`, `ML.MAX_ABS_SCALER`, `ML.NORMALIZER`, `ML.BUCKETIZE`, `ML.QUANTILE_BUCKETIZE`, `ML.POLYNOMIAL_EXPAND`); categorical (`ML.ONE_HOT_ENCODER`, `ML.MULTI_HOT_ENCODER`, `ML.LABEL_ENCODER`, `ML.FEATURE_CROSS`, `ML.HASH_BUCKETIZE`); text (`ML.NGRAMS`, `ML.BAG_OF_WORDS`, `ML.TF_IDF`); image (`ML.DECODE_IMAGE`, `ML.RESIZE_IMAGE`, `ML.CONVERT_IMAGE_TYPE`, `ML.CONVERT_COLOR_SPACE`).

**Hyperparameter tuning:** N/A — no learner, nothing to tune.

**Explainability / weights:** N/A — none of the explainability/weights functions apply (no model parameters). For attribution, apply the transform then train a separate estimator that supports explainability.

**Best practices:**
- Build one transform model per logical step (impute, then scale) and compose them in order with CTEs; or wrap the whole pipeline in a view for reuse.
- Build feature‑specific transform‑only models for feature‑store‑style modularity.
- Train downstream estimators on the *output* of the transform pipeline; the estimator then has no embedded `TRANSFORM`, so you must re‑apply the same `ML.TRANSFORM` pipeline before `ML.PREDICT`/`ML.EVALUATE`.
- Prefer transform‑only models for large batch feature jobs.
- Note the contrast vs. an *embedded* `TRANSFORM` (TRANSFORM clause on a predictive model): embedded transforms auto‑apply at predict time (no re‑application needed) but are not reusable across models; transform‑only models are reusable but must be explicitly re‑applied.

**Limitations:**
- Cannot predict, evaluate, or explain — it is a preprocessing object only.
- Consumed almost exclusively through `ML.TRANSFORM`; column names/types must align with the `TRANSFORM` clause.
- No labels, no data split, no learning options.
- Anonymous (unaliased) transformed columns are rejected.

**Locations:** Available in BigQuery ML regions/multi-regions generally; same location rules as `CREATE MODEL`. Vertex AI registration/export follow standard cross-service location requirements.

**BigFrames API:** No single direct `TRANSFORM_ONLY` class. Equivalent functionality is the `bigframes.ml.preprocessing` transformers (e.g. `StandardScaler`, `MaxAbsScaler`, `OneHotEncoder`, `LabelEncoder`) and `bigframes.ml.pipeline.Pipeline`/`ColumnTransformer`, which compile to BQML preprocessing under the hood. A persisted transform-only model can be read with `bigframes.pandas.read_gbq_model`.

**Repo example (tested):** `/home/user/git/vertex-ai-mlops/03 - BigQuery ML (BQML)/BQML Feature Engineering - reusable and modular.ipynb` — full tested walkthrough on `bigquery-public-data.ml_datasets.penguins`: (1) embedded `TRANSFORM` on a `BOOSTED_TREE_CLASSIFIER`; (2) reuse of any model's transform via `ML.TRANSFORM`; (3) separate `TRANSFORM_ONLY` models for imputation and for scaling, chained with CTEs and exposed as a view; (4) per‑feature `TRANSFORM_ONLY` models (feature‑store style); (5) feeding the pipeline output into a `CREATE MODEL`; (6) `ML.FEATURE_INFO`; (7) `EXPORT MODEL` to GCS (transform‑only exports a `transform/saved_model.pb`); (8) Vertex AI registration + endpoint serving; (9) consuming via BigFrames `read_gbq_model().predict()`.


---

### TimesFM (built-in foundation forecaster) — see `bq-ai-functions`

> **Cross-link only.** The TimesFM univariate forecaster is a *pretrained* foundation model invoked through the `AI.*` function family, which is owned by the sibling project. For the full entry (syntax, options, inputs/outputs, status), see **[`../bq-ai-functions/RESOURCES.md`](../bq-ai-functions/RESOURCES.md)** → `AI.FORECAST`, `AI.EVALUATE`, `AI.DETECT_ANOMALIES`.

- **What it is:** A built-in, pretrained univariate time-series foundation model ([Google Research TimesFM](https://docs.cloud.google.com/bigquery/docs/timesfm-model)). Unlike `ARIMA_PLUS` / `ARIMA_PLUS_XREG`, there is **no `CREATE MODEL` step** — you call `AI.FORECAST` directly on a table or query. Supported model versions: TimesFM 2.0 (default) and TimesFM 2.5.
- **Category:** time-series (foundation model). Belongs to the `AI.*` family, **not** the BQML `CREATE MODEL` + `ML.*` lifecycle documented in this file.
- **Connection required:** No.
- **Status:** `AI.FORECAST` and `AI.EVALUATE` — **GA** (Nov 2025). `AI.DETECT_ANOMALIES` — **Preview**.

**Why it lives in `bq-ai-functions`, not here:** TimesFM is not a `model_type` you train with `CREATE MODEL`, and it does **not** use the `ML.*` lifecycle functions (`ML.FORECAST`, `ML.EVALUATE`, `ML.EXPLAIN_FORECAST`, `ML.DETECT_ANOMALIES`). It has no feature preprocessing, no hyperparameter tuning, no model weights, and AI-explanation is N/A. Those `ML.*` lifecycle functions ARE in scope here, but only for the trainable forecasters below.

**In-scope alternative in this file — the trainable forecasters:**

| If you want… | Use (in this file) | Notes |
|---|---|---|
| Zero-training forecast, no `CREATE MODEL` | TimesFM via `AI.FORECAST` → cross-link out | foundation model; `AI.*` family |
| Trained univariate model, full `ML.*` lifecycle + explainability | `ARIMA_PLUS` | supports `ML.FORECAST`, `ML.EVALUATE`, `ML.EXPLAIN_FORECAST`, `ML.DETECT_ANOMALIES` |
| Trained model with external regressors (covariates) | `ARIMA_PLUS_XREG` | adds side features to the ARIMA_PLUS workflow |

**documentation:**
- End-to-end forecasting journey: <https://docs.cloud.google.com/bigquery/docs/e2e-journey-forecast>
- TimesFM model: <https://docs.cloud.google.com/bigquery/docs/timesfm-model>
- `AI.FORECAST` reference: <https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-forecast>
- Forecasting overview (model-type comparison): <https://docs.cloud.google.com/bigquery/docs/forecasting-overview>

**Repo example (tested):** None found in the repo scout — no tested TimesFM/`AI.FORECAST` example exists in `data+ai/bq-ml/` yet.


## Model Lifecycle Functions

Functions that operate on a trained model: evaluate, predict, classify-eval, explain, weights, introspect, unsupervised insight, recommend/embed, forecast, anomaly/transform.


---

### `ML.EVALUATE`
- **Description:** Computes evaluation metrics for a trained BigQuery ML model. Returns a single row of metrics whose columns depend on the model type. Called with no input data, it returns the metrics computed on the model's reserved evaluation split at training time; called with input data, it scores that new dataset.
- **Use cases:**
  - Read training-time metrics off the reserved eval split (no input data).
  - Score a held-out TEST/VALIDATE set or fresh data to check generalization / drift.
  - Compare metrics across splits, model versions, or hyperparameter trials.
- **documentation:** https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-evaluate (evaluation overview: https://cloud.google.com/bigquery/docs/evaluate-overview)
- **Type:** Table-valued function.
- **Applies to models:** Supervised — `LINEAR_REG`, `LOGISTIC_REG`, `BOOSTED_TREE_*`, `RANDOM_FOREST_*`, `DNN_*`, `WIDE_AND_DEEP_*`, `AUTOML_*`. Unsupervised — `KMEANS`, `PCA`, `AUTOENCODER`, `MATRIX_FACTORIZATION`. Time series — `ARIMA_PLUS`, `ARIMA_PLUS_XREG` (with input data; no-input form is deprecated — use `ML.ARIMA_EVALUATE`).

**Syntax:**
```sql
ML.EVALUATE(
  MODEL `PROJECT_ID.DATASET.MODEL_NAME`
  [, { TABLE `PROJECT_ID.DATASET.TABLE` | (query_statement) }]
  [, STRUCT(threshold_value AS threshold [, trial_id AS trial_id])]
)
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `MODEL` | model ref | Yes | — | The trained model to evaluate. |
| `TABLE` / `query_statement` | table / subquery | No | training eval split | Evaluation data. Column names must match the model's features and label; with a `TRANSFORM` model only the raw `TRANSFORM` inputs are required. Omit to read training-time metrics. |
| `threshold` | FLOAT64 | No | 0.5 | Binary-classification cutoff between the two labels. Classification models only. |
| `trial_id` | INT64 | No | optimal trial | Selects a specific hyperparameter-tuning trial. Only valid when the model was trained with `NUM_TRIALS`. Not allowed for PCA models. |

**Outputs (metric columns vary by model type):**

| Model task | ML.EVALUATE metric columns |
|---|---|
| Regression (`LINEAR_REG`, tree/DNN regressors) | `mean_absolute_error`, `mean_squared_error`, `mean_squared_log_error`, `median_absolute_error`, `r2_score`, `explained_variance` |
| Classification (`LOGISTIC_REG`, tree/DNN classifiers) | `precision`, `recall`, `accuracy`, `f1_score`, `log_loss`, `roc_auc` (macro-averaged for multiclass) |
| K-means (`KMEANS`) | `davies_bouldin_index`, `mean_squared_distance` |
| Matrix factorization (`MATRIX_FACTORIZATION`) — explicit feedback | `mean_absolute_error`, `mean_squared_error`, `mean_squared_log_error`, `r2_score`, `explained_variance` (a regression metric set) |
| Matrix factorization (`MATRIX_FACTORIZATION`) — implicit feedback | `recall`, `mean_squared_error`, `normalized_discounted_cumulative_gain`, `average_rank` |
| PCA (`PCA`) | `total_explained_variance_ratio` |
| Autoencoder (`AUTOENCODER`) | `mean_absolute_error`, `mean_squared_error`, `mean_squared_log_error` |
| Time series (`ARIMA_PLUS`/`ARIMA_PLUS_XREG`, with input data + `perform_aggregation=TRUE`) | `mean_absolute_error`, `mean_squared_error`, `root_mean_squared_error`, `mean_absolute_percentage_error`, `symmetric_mean_absolute_percentage_error`, `mean_absolute_scaled_error` |

> A `trial_id` column is prepended to the output when the model was trained with hyperparameter tuning.

**Best practices:**
- Run with no input data first to get the training eval-split metrics for free, then pass TEST/VALIDATE data to confirm generalization.
- Stack splits with `SELECT 'TEST' AS SPLIT, * FROM ML.EVALUATE(...) UNION ALL ...` to compare TRAIN/VALIDATE/TEST side by side (see repo example).
- Tune the `threshold` to your precision/recall trade-off rather than relying on 0.5; inspect the full curve with `ML.ROC_CURVE` (binary) first.

**Limitations:**
- `precision`/`recall` of 0 means the threshold yielded no true positives; `NaN` precision means no positive predictions at all.
- For `ARIMA_PLUS`, the no-input form is deprecated — use `ML.ARIMA_EVALUATE` for model-fitting diagnostics (`AIC`, `log_likelihood`, `variance`, `non_seasonal_p/d/q`, `seasonal_periods`, `has_holiday_effect`, ...).
- `trial_id` argument is not supported for PCA models.

**BigFrames API:** `model.score(X, y)` on any `bigframes.ml` estimator returns the same metrics as a DataFrame.

**Repo example (tested):**
- `03 - BigQuery ML (BQML)/03a - BQML Logistic Regression.ipynb` and `03b - BQML Boosted Trees.ipynb` — three-way TRAIN/VALIDATE/TEST `ML.EVALUATE` over a `SPLITS` column via `UNION ALL`.
- `03 - BigQuery ML (BQML)/03h - BQML k-means with Anomaly Detection.ipynb` — no-input `ML.EVALUATE` returning `davies_bouldin_index`, `mean_squared_distance`.
- `03 - BigQuery ML (BQML)/03g - BQML - PCA with Anomaly Detection.ipynb` and `03i - BQML Autoencoder with Anomaly Detection.ipynb` — no-input `ML.EVALUATE` for unsupervised reconstruction models.
- `Applied Forecasting/BQML Univariate Forecasting with ARIMA+.ipynb` — `ML.EVALUATE` with input data for `model_type = 'ARIMA_PLUS'` forecast-accuracy metrics.
- `data+ai/bq-ml/models/logistic_regression/logistic_regression.sql` (Example 2) — minimal no-input `ML.EVALUATE`.

---

### `ML.PREDICT`
- **Description:** Generates predictions (inference) from a trained model over an input table or query. Output has one row per input row, carrying the model's prediction columns plus pass-through input columns. Any `TRANSFORM` clause baked into the model is reapplied automatically — no need to repeat preprocessing.
- **Use cases:**
  - Batch-score new data with a classification/regression model.
  - Assign cluster membership with k-means; project rows onto principal components with PCA.
  - Produce the inputs for downstream `ML.EXPLAIN_PREDICT` / business logic.
- **documentation:** https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-predict
- **Type:** Table-valued function.
- **Applies to models:** `LINEAR_REG`, `LOGISTIC_REG`, `BOOSTED_TREE_*`, `RANDOM_FOREST_*`, `DNN_*`, `WIDE_AND_DEEP_*`, `KMEANS`, `PCA`, `AUTOENCODER`, `AUTOML_*`, and imported models (`TENSORFLOW`, `TENSORFLOW_LITE`, `ONNX`, `XGBOOST`). Note: time-series models use `ML.FORECAST`, matrix factorization uses `ML.RECOMMEND`.

**Syntax:**
```sql
ML.PREDICT(
  MODEL `PROJECT_ID.DATASET.MODEL_NAME`,
  { TABLE `PROJECT_ID.DATASET.TABLE` | (query_statement) }
  [, STRUCT(threshold_value AS threshold
            [, keep_original_columns_value AS keep_original_columns]
            [, trial_id AS trial_id])]
)
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `MODEL` | model ref | Yes | — | The trained model used for inference. |
| `TABLE` / `query_statement` | table / subquery | Yes | — | Rows to score. Input columns must match the model's features (or, for a `TRANSFORM` model, only the raw `TRANSFORM` inputs). Unused columns are passed through. |
| `threshold` | FLOAT64 | No | 0.5 | Binary-classification cutoff. Classification models only. |
| `keep_original_columns` | BOOL | No | FALSE | k-means only — also emit the original (non-standardized) feature columns alongside the cluster output. |
| `trial_id` | INT64 | No | optimal trial | Selects a hyperparameter-tuning trial. Only valid when trained with `NUM_TRIALS`. |

**Outputs (vary by model type; all input columns are appended):**

| Model task | ML.PREDICT output columns |
|---|---|
| Classification | `predicted_<label>` (chosen class); `predicted_<label>_probs` — `ARRAY<STRUCT<label, prob>>` of per-class probabilities |
| Regression | `predicted_<label>` (FLOAT64) |
| K-means | `centroid_id` (INT64); `nearest_centroids_distance` — `ARRAY<STRUCT<centroid_id, distance>>` for the nearest min(`num_clusters`, 5) clusters |
| PCA | `principal_component_<index>` — projection of the row onto each kept component |
| Autoencoder | `latent_col_<index>` — one column per bottleneck dimension (encoded low-dimensional representation); original input columns appended after |

**Best practices:**
- Prefer the `TRANSFORM` clause at `CREATE MODEL` time so preprocessing travels with the model and `ML.PREDICT` stays a plain `SELECT *` — no manual feature engineering at inference.
- Select only the columns you need (`predicted_<label>`, `predicted_<label>_probs`) instead of `SELECT *` on wide tables to cut bytes scanned.
- For k-means segmentation, read the closest distance with `nearest_centroids_distance[OFFSET(0)].distance`.

**Limitations:**
- Not for time-series (`ML.FORECAST`) or matrix-factorization (`ML.RECOMMEND`) models.
- Object-table / image inputs must be decoded with `ML.DECODE_IMAGE`; imported-model inputs must coerce to the model's expected types.
- `keep_original_columns` applies to k-means only.

**BigFrames API:** `model.predict(X)` on a `bigframes.ml` estimator returns a DataFrame with the predicted columns.

**Repo example (tested):**
- `03 - BigQuery ML (BQML)/03a - BQML Logistic Regression.ipynb` / `03b - BQML Boosted Trees.ipynb` — `ML.PREDICT` over the TEST split returning `predicted_<label>` + `_probs`.
- `03 - BigQuery ML (BQML)/03h - BQML k-means with Anomaly Detection.ipynb` — `ML.PREDICT` returning `centroid_id` / `nearest_centroids_distance`.
- `03 - BigQuery ML (BQML)/03g - BQML - PCA with Anomaly Detection.ipynb` — `ML.PREDICT` projecting onto principal components.
- `03 - BigQuery ML (BQML)/03i - BQML Autoencoder with Anomaly Detection.ipynb` — `ML.PREDICT` for the autoencoder (paired with `ML.RECONSTRUCTION_LOSS`).
- `data+ai/bq-ml/models/logistic_regression/logistic_regression.sql` (Example 5) — `predicted_income_bracket` + `predicted_income_bracket_probs`.


---

### `ML.CONFUSION_MATRIX`
- **Description:** Returns a confusion matrix for a trained classification model — rows of actual (expected) labels vs. counts of predicted labels — computed over evaluation/input data.
- **Use cases:**
  - Inspect per-class correct vs. incorrect predictions beyond a single accuracy number.
  - Diagnose class imbalance and which classes a model confuses (multiclass).
  - Validate the effect of a custom decision `threshold` on binary classifiers.
- **documentation:** https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-confusion
- **Type:** Table-valued function (TVF).
- **Applies to models:** Classification models only — `LOGISTIC_REG` (binary + multiclass), `BOOSTED_TREE_CLASSIFIER`, `RANDOM_FOREST_CLASSIFIER`, `DNN_CLASSIFIER`, `DNN_LINEAR_COMBINED_CLASSIFIER` (wide-and-deep), and `AUTOML_CLASSIFIER`. Does **not** support imported TensorFlow models, regression, clustering, MF, PCA, autoencoder, ARIMA_PLUS, or remote/LLM models.

**Syntax:**
```sql
ML.CONFUSION_MATRIX(
  MODEL `PROJECT_ID.DATASET.MODEL_NAME`
  [, { TABLE `PROJECT_ID.DATASET.TABLE` | (QUERY_STATEMENT) }]
  [, STRUCT([THRESHOLD AS threshold] [, TRIAL_ID AS trial_id])]
)
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `MODEL` | model ref | Yes | — | A trained classification model. |
| `TABLE` / `QUERY_STATEMENT` | table or query | No\* | eval/training split | Input data whose columns match the model's features plus the label column. If omitted, uses the held-out eval split (or the full training data if no split). \*Required for some models, and required if you set `threshold`. |
| `threshold` | FLOAT64 (in STRUCT) | No | 0.5 | Custom positive-class cutoff. **Binary only** — error if used on a multiclass model. Requires TABLE/QUERY also be supplied. |
| `trial_id` | INT64 (in STRUCT) | No | optimal trial | Select a specific hyperparameter-tuning trial; defaults to the optimal trial. |

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| `expected_label` | (label type) | Actual label value; one row per class. Exact value/type as passed in the label column. |
| \<one column per class\> | INT64 | Count of rows with that actual label predicted as this class. Column name is the class label (if it conforms to BigQuery column-naming rules). |

**Best practices:**
- Call without input args right after training to use the held-out eval split; pass your own TABLE for an independent test set.
- For binary models, sweep `threshold` (e.g. 0.3 / 0.5 / 0.7) to see precision/recall trade-offs as integer counts.
- Pair with `ML.EVALUATE` (scalar metrics) and `ML.ROC_CURVE` (threshold curve) for a complete classification picture.

**Limitations:**
- Classification models only; no regression/clustering/imported-TF.
- `threshold` is binary-only and requires explicit input data.
- Column names derive from class labels; labels not matching column-naming rules get sanitized names.

**BigFrames API:** `model.confusion_matrix(X, y)` on a `bigframes.ml` classifier (e.g. `LogisticRegression`, `XGBoostClassifier`).
**Repo example (tested):**
- `/home/user/git/vertex-ai-mlops/data+ai/bq-ml/models/logistic_regression/logistic_regression.sql` (Example 3) — `SELECT * FROM ML.CONFUSION_MATRIX(MODEL ...)` on the census income binary classifier.
- `/home/user/git/vertex-ai-mlops/03 - BigQuery ML (BQML)/03a - BQML Logistic Regression.ipynb` and `03b - BQML Boosted Trees.ipynb` — confusion matrix on logistic-regression and boosted-tree classifiers with an explicit input query.

---

### `ML.ROC_CURVE`
- **Description:** Returns ROC-curve points for a **binary** classification model — one row per threshold with recall (true positive rate), false positive rate, and the raw TP/FP/TN/FN counts.
- **Use cases:**
  - Plot the ROC curve and reason about the threshold that best balances recall vs. false positives.
  - Build a precision-recall curve from the returned TP/FP counts.
  - Choose an operating threshold for downstream `ML.PREDICT` decisions.
- **documentation:** https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-roc
- **Type:** Table-valued function (TVF).
- **Applies to models:** **Binary classification only** — `LOGISTIC_REG` (binary), `BOOSTED_TREE_CLASSIFIER` (binary), `RANDOM_FOREST_CLASSIFIER` (binary), `DNN_CLASSIFIER` (binary), wide-and-deep classifier (binary), `AUTOML_CLASSIFIER` (binary). Not for multiclass models, regression, or unsupervised models.

**Syntax:**
```sql
ML.ROC_CURVE(
  MODEL `PROJECT_ID.DATASET.MODEL_NAME`
  [, { TABLE `PROJECT_ID.DATASET.TABLE` | (QUERY_STATEMENT) }]
  [, GENERATE_ARRAY(THRESHOLDS)]
  [, STRUCT(TRIAL_ID AS trial_id)]
)
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `MODEL` | model ref | Yes | — | A trained binary classification model. |
| `TABLE` / `QUERY_STATEMENT` | table or query | No\* | eval/training split | Evaluation data matching the model's features + label column. If omitted, uses the held-out eval split (or full training data if unsplit). \*Required for some models. |
| `GENERATE_ARRAY(THRESHOLDS)` | ARRAY\<FLOAT64\> | No | 100 approx. quantiles | Explicit threshold values to evaluate, e.g. `GENERATE_ARRAY(0.4, 0.6, 0.01)`. If omitted, thresholds are chosen automatically from ~100 quantiles of the prediction scores. |
| `trial_id` | INT64 (in STRUCT) | No | optimal trial | Select a specific hyperparameter-tuning trial. |

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| `threshold` | FLOAT64 | The decision cutoff for this row. |
| `recall` | FLOAT64 | True positive rate at this threshold. |
| `false_positive_rate` | FLOAT64 | FP / (FP + TN) at this threshold (plot vs. recall for the ROC curve). |
| `true_positives` | INT64 | Count of correctly predicted positives. |
| `false_positives` | INT64 | Count of negatives predicted positive. |
| `true_negatives` | INT64 | Count of correctly predicted negatives. |
| `false_negatives` | INT64 | Count of positives predicted negative. |

**Best practices:**
- `ORDER BY threshold` for clean plotting; let thresholds default unless you need a fine sweep over a narrow band (use `GENERATE_ARRAY`).
- Derive precision-recall directly: `true_positives / (true_positives + false_positives) AS precision`.
- The `roc_auc` summary value comes from `ML.EVALUATE`; use `ML.ROC_CURVE` for the full curve / threshold selection.

**Limitations:**
- Binary classification only — no multiclass.
- Some older models require explicit input data or return an error.
- With a TRANSFORM clause, the input query needs only the pre-TRANSFORM input columns.

**BigFrames API:** `model.roc_curve(X, y)` on a `bigframes.ml` binary classifier (returns fpr / tpr / thresholds).
**Repo example (tested):**
- `/home/user/git/vertex-ai-mlops/data+ai/bq-ml/models/logistic_regression/logistic_regression.sql` (Example 4) — selects `threshold, recall, false_positive_rate, true_positives, false_positives, true_negatives, false_negatives FROM ML.ROC_CURVE(...) ORDER BY threshold`.
- `/home/user/git/vertex-ai-mlops/03 - BigQuery ML (BQML)/03a - BQML Logistic Regression.ipynb` and `03b - BQML Boosted Trees.ipynb` — ROC curve queried and plotted for binary classifiers.

> Note: classification eval here covers the model-bound TVFs. For unsupervised anomaly detection (PCA / k-means / autoencoder in `03g`–`03i`) and ARIMA_PLUS forecasting eval, see the `ML.DETECT_ANOMALIES`, `ML.RECONSTRUCTION_LOSS`, and forecasting entries — `ML.CONFUSION_MATRIX` / `ML.ROC_CURVE` do not apply to those model types.


---

### Explainability functions: `ML.EXPLAIN_PREDICT`, `ML.GLOBAL_EXPLAIN`, `ML.FEATURE_IMPORTANCE`

Three lifecycle functions for model interpretability. `ML.EXPLAIN_PREDICT` gives **local** (per-row) feature attributions; `ML.GLOBAL_EXPLAIN` gives **model-level** (aggregated) attributions; `ML.FEATURE_IMPORTANCE` gives **tree-specific** split-based importance for boosted-tree / random-forest models. For the underlying concepts see the [BigQuery Explainable AI overview](https://cloud.google.com/bigquery/docs/xai-overview). For the model-coefficient view (`ML.WEIGHTS` / `ML.ADVANCED_WEIGHTS`), see the weights entry; this entry covers attributions/importance only.

---

### `ML.EXPLAIN_PREDICT`
- **Description:** An extended `ML.PREDICT` that returns, for each input row, the prediction plus the top-k feature attributions explaining how each feature pushed the prediction away from a baseline.
- **Use cases:**
  - Explain an individual prediction ("why did this customer get scored as churn?").
  - Debug surprising predictions by inspecting per-row contributions.
  - Surface row-level reason codes for downstream apps.
- **documentation:** https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-explain-predict
- **Type:** Table-valued function.
- **Applies to models:** `LINEAR_REG`, `LOGISTIC_REG`, `BOOSTED_TREE_*`, `RANDOM_FOREST_*`, `DNN_*`, `WIDE_AND_DEEP_*`, and AutoML Tables models. Attribution method varies by type: exact (Shapley/tree) where `baseline_prediction_value + sum(attributions) = prediction_value` (linear, tree models), and integrated gradients (approximate) for DNN / Wide-and-Deep. Does NOT apply to unsupervised models (k-means, PCA, autoencoder, matrix factorization) or ARIMA_PLUS.

**Syntax:**
```sql
ML.EXPLAIN_PREDICT(
  MODEL `PROJECT_ID.DATASET.MODEL_NAME`,
  { TABLE `PROJECT_ID.DATASET.TABLE` | (QUERY_STATEMENT) },
  STRUCT(
    [<top_k_features> AS top_k_features]
    [, <threshold> AS threshold]
    [, <integrated_gradients_num_steps> AS integrated_gradients_num_steps]
    [, <approx_feature_contrib> AS approx_feature_contrib]
  )
)
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| MODEL | model | Yes | — | The trained model to explain. |
| TABLE / QUERY_STATEMENT | table/query | Yes | — | Rows to predict and explain (must contain the model's feature columns). |
| top_k_features | INT64 | No | 5 | Number of top features (by absolute attribution) returned per row. If larger than the feature count, all features are returned. |
| threshold | FLOAT64 | No | 0.5 | Binary-classification cutoff (0.0–1.0); predictions above are positive. Attributions returned for the predicted label. |
| integrated_gradients_num_steps | INT64 | No | 25 | Steps sampled between the example and its baseline for integrated-gradients attribution (DNN / Wide-and-Deep). Higher = more precise but slower. |
| approx_feature_contrib | BOOL | No | FALSE | Use XGBoost's approximate feature-contribution method. Boosted-tree / random-forest models only. |

**Outputs:** (passthrough input columns, plus)

| Column | Type | Description |
|--------|------|-------------|
| predicted_\<label\> | STRING/numeric | Predicted label class (classification) or value (regression). |
| probability | FLOAT64 | Probability of the predicted class (classification models only). |
| top_feature_attributions | ARRAY\<STRUCT\<feature STRING, attribution FLOAT64\>\> | Top-k features and their signed contribution to the prediction. |
| baseline_prediction_value | FLOAT64 | The baseline (expected) prediction the attributions are measured against. |
| prediction_value | FLOAT64 | The raw prediction value being explained. |
| approximation_error | FLOAT64 | 0 for exact methods (linear/tree); \>0 for integrated gradients (DNN). |

**Best practices:**
- Keep `top_k_features` small for readability; raise only when you need the full attribution vector.
- For DNN/WnD, increase `integrated_gradients_num_steps` if `approximation_error` is large.
- Run on a sampled/`LIMIT`ed input — it is per-row and can be expensive over large tables.

**Limitations:**
- Not available for unsupervised or ARIMA_PLUS models.
- `approx_feature_contrib` applies only to tree ensembles; `integrated_gradients_num_steps` only to DNN/WnD.

**BigFrames API:** `model.predict_explain(X, top_k_features=...)` on supported supervised estimators in `bigframes.ml`.

**Repo example (tested):**
- `/home/user/git/vertex-ai-mlops/03 - BigQuery ML (BQML)/03a - BQML Logistic Regression.ipynb` — `ML.EXPLAIN_PREDICT(MODEL ..., (SELECT * ... WHERE splits='TEST'), STRUCT(10 as top_k_features))` on a logistic-regression model.
- `/home/user/git/vertex-ai-mlops/03 - BigQuery ML (BQML)/03b - BQML Boosted Trees.ipynb` — same call on a `BOOSTED_TREE_CLASSIFIER`.
- `/home/user/git/vertex-ai-mlops/data+ai/bq-ml/models/logistic_regression/logistic_regression.sql` (Example 6) — `STRUCT(5 AS top_k_features)`, selecting `top_feature_attributions`.

---

### `ML.GLOBAL_EXPLAIN`
- **Description:** Returns model-level feature importance by averaging the absolute local attributions across the evaluation data. Requires the model to have been trained with `enable_global_explain = TRUE`.
- **Use cases:**
  - Rank which features matter most to the model overall.
  - Compare feature influence across model versions.
  - Per-class importance for classification (with `class_level_explain`).
- **documentation:** https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-global-explain
- **Type:** Table-valued function.
- **Applies to models:** Same supervised types as `ML.EXPLAIN_PREDICT` (`LINEAR_REG`, `LOGISTIC_REG`, `BOOSTED_TREE_*`, `RANDOM_FOREST_*`, `DNN_*`, `WIDE_AND_DEEP_*`) **trained with `enable_global_explain = TRUE`**. Not supported for k-means, PCA, autoencoder, matrix factorization, imported XGBoost, or AutoML models.

**Prerequisite (CREATE MODEL):**
```sql
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.MODEL_NAME`
OPTIONS(
  model_type = 'LOGISTIC_REG',
  input_label_cols = ['label'],
  enable_global_explain = TRUE   -- computed at training time; required here
) AS SELECT ... ;
```

**Syntax:**
```sql
ML.GLOBAL_EXPLAIN(
  MODEL `PROJECT_ID.DATASET.MODEL_NAME`
  [, STRUCT(<class_level_explain> AS class_level_explain)]
)
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| MODEL | model | Yes | — | Model trained with `enable_global_explain = TRUE`. |
| class_level_explain | BOOL | No | FALSE | If TRUE, return importances per class (non-AutoML classification models only); otherwise one importance per feature for the whole model. |

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| feature | STRING | Input feature name. |
| attribution | FLOAT64 | Mean absolute attribution of the feature across the evaluation set. |
| class_label | STRING | Class the importance applies to — present only when `class_level_explain = TRUE`. |

**Best practices:**
- Always set `enable_global_explain = TRUE` at `CREATE MODEL` time for supported models — you cannot enable it after training without retraining.
- `ORDER BY attribution DESC` to rank features.

**Limitations:**
- Errors ("input model was not explained when it was created") if `enable_global_explain` was not set at training.
- `class_level_explain` is ignored/invalid for regression and AutoML Tables models.
- Global explanations are computed once at training time, not at call time.

**BigFrames API:** `model.global_explain()` on supported supervised estimators in `bigframes.ml`.

**Repo example (tested):**
- `/home/user/git/vertex-ai-mlops/03 - BigQuery ML (BQML)/03a - BQML Logistic Regression.ipynb` — model trained with `enable_global_explain = TRUE`, then `SELECT * FROM ML.GLOBAL_EXPLAIN(MODEL ...)`.
- `/home/user/git/vertex-ai-mlops/03 - BigQuery ML (BQML)/03b - BQML Boosted Trees.ipynb` — same pattern on a boosted-tree classifier.
- `/home/user/git/vertex-ai-mlops/data+ai/bq-ml/models/logistic_regression/logistic_regression.sql` (Examples 1 & 7) — `enable_global_explain = TRUE` then `ML.GLOBAL_EXPLAIN(...) ORDER BY attribution DESC`.

---

### `ML.FEATURE_IMPORTANCE`
- **Description:** Returns XGBoost split-based feature importance (weight, gain, cover) for tree-ensemble models. Reflects how the trees actually used each feature during training — distinct from attribution-based explanations.
- **Use cases:**
  - Rank features for boosted-tree / random-forest models.
  - Feature selection / pruning based on gain.
  - Cross-check tree usage against `ML.GLOBAL_EXPLAIN` attributions.
- **documentation:** https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-importance
- **Type:** Table-valued function.
- **Applies to models:** `BOOSTED_TREE_CLASSIFIER`, `BOOSTED_TREE_REGRESSOR`, `RANDOM_FOREST_CLASSIFIER`, `RANDOM_FOREST_REGRESSOR` only. Does NOT require `enable_global_explain`.

**Syntax:**
```sql
ML.FEATURE_IMPORTANCE(MODEL `PROJECT_ID.DATASET.MODEL_NAME`)
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| MODEL | model | Yes | — | A boosted-tree or random-forest model. |

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| feature | STRING | Input feature name. |
| importance_weight | FLOAT64 | Number of splits the feature was used in across all trees. |
| importance_gain | FLOAT64 | Improvement in accuracy from splits using the feature (usually the most informative). |
| importance_cover | FLOAT64 | Number of data rows covered by splits using the feature. |

**Best practices:**
- Prefer `importance_gain` for judging predictive value; `weight`/`cover` describe usage frequency/coverage.
- Use alongside `ML.GLOBAL_EXPLAIN` (attribution-based) for a fuller picture.

**Limitations:**
- Tree-ensemble models only — not valid for linear, DNN, or unsupervised models (use `ML.WEIGHTS` or `ML.GLOBAL_EXPLAIN` instead).

**BigFrames API:** Tree-ensemble estimators expose `model.feature_importances_` in `bigframes.ml`.

**Repo example (tested):**
- `/home/user/git/vertex-ai-mlops/03 - BigQuery ML (BQML)/03b - BQML Boosted Trees.ipynb` — `SELECT * FROM ML.FEATURE_IMPORTANCE(MODEL ...)` on `BOOSTED_TREE_CLASSIFIER`, documenting weight/gain/cover columns.

---

### Quick comparison

| | `ML.EXPLAIN_PREDICT` | `ML.GLOBAL_EXPLAIN` | `ML.FEATURE_IMPORTANCE` |
|---|---|---|---|
| Scope | Per-row (local) | Model-level (aggregated) | Model-level (tree split stats) |
| Models | linear, logistic, tree, DNN, WnD, AutoML | same, **+ `enable_global_explain=TRUE`** | boosted-tree, random-forest only |
| Needs eval/predict input | Yes (input table) | No | No |
| Key output | `top_feature_attributions` | `feature`, `attribution` | `importance_weight/gain/cover` |
| Pre-req option | none | `enable_global_explain = TRUE` | none |


---

### `ML.WEIGHTS`
- **Description:** Returns the learned model parameters (weights/coefficients) of a trained linear regression, logistic regression, or matrix factorization model. For GLMs it returns one weight per processed feature (plus the intercept); for matrix factorization it returns the latent factor weights per user/item.
- **Use cases:**
  - Inspect feature coefficients to understand direction/magnitude of each feature's effect.
  - Compare relative feature importance using `STANDARDIZE => TRUE` (puts all weights on a comparable scale).
  - Extract user/item latent factors and intercepts from a matrix factorization recommender.
- **documentation:** https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-weights · weights overview: https://cloud.google.com/bigquery/docs/weights-overview
- **Type:** Table-valued function.
- **Applies to models:** `LINEAR_REG`, `LOGISTIC_REG` (binary and multiclass), `MATRIX_FACTORIZATION`. NOT supported for boosted trees, random forest, DNN, wide-and-deep, k-means, PCA, autoencoder, ARIMA_PLUS, or AutoML (export the model and inspect externally, or use `ML.FEATURE_IMPORTANCE` / `ML.GLOBAL_EXPLAIN` / `ML.CENTROIDS` / `ML.PRINCIPAL_COMPONENTS` / `ML.ARIMA_COEFFICIENTS` as appropriate).

**Syntax:**
```sql
-- GLM (linear / logistic regression)
SELECT *
FROM ML.WEIGHTS(MODEL `PROJECT_ID.DATASET.MODEL_NAME`
                [, STRUCT(TRUE AS standardize)]);

-- Matrix factorization (no standardize argument)
SELECT *
FROM ML.WEIGHTS(MODEL `PROJECT_ID.DATASET.MODEL_NAME`);
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `MODEL` | model ref | Yes | — | The trained model. |
| `STANDARDIZE` | BOOL (in STRUCT) | No | `FALSE` | Standardize weights as if all features had mean 0 / std 1 so magnitudes are comparable. Applies to linear and logistic regression only (ignored / N/A for matrix factorization). |

**Outputs (linear & logistic regression):**

| Column | Type | Description |
|--------|------|-------------|
| `trial_id` | INT64 | HP-tuning trial ID. Only present if the model was trained with hyperparameter tuning. |
| `processed_input` | STRING | Feature input column name (matches the training query column). |
| `weight` | FLOAT64 | Weight for a numeric feature; NULL when the feature is categorical (see `category_weights`). Intercept appears as processed_input `__INTERCEPT__`. |
| `category_weights` | ARRAY\<STRUCT\> | For non-numeric (one-hot/dummy-encoded) columns: per-category weights. NULL for numeric columns. |
| `category_weights.category` | STRING | Category name. |
| `category_weights.weight` | FLOAT64 | Weight for that category. |
| `class_label` | STRING | Only for multiclass models; one row per `\<class_label, processed_input\>` pair. |

**Outputs (matrix factorization):**

| Column | Type | Description |
|--------|------|-------------|
| `processed_input` | STRING | Name of the user or item column. |
| `feature` | STRING | The specific user/item value. |
| `factor_weights` | ARRAY\<STRUCT\> | Latent factors and their weights. |
| `factor_weights.factor` | INT64 | Latent factor index (1..`NUM_FACTORS`). |
| `factor_weights.weight` | FLOAT64 | Weight of that factor for the feature. |
| `intercept` | FLOAT64 | Bias term for the feature. A `global__intercept__` row (NULL `processed_input`/`factor_weights`) is also returned; it is 0 for implicit-feedback models. |

**Querying nested `category_weights`:**
```sql
SELECT category, weight
FROM UNNEST((
  SELECT category_weights
  FROM ML.WEIGHTS(MODEL `PROJECT_ID.DATASET.MODEL_NAME`)
  WHERE processed_input = 'occupation'));
```

**Best practices:**
- Use `STRUCT(TRUE AS standardize)` to rank feature importance by absolute weight magnitude.
- With a `TRANSFORM` clause, weights are reported on the TRANSFORM output features (denormalized by default).
- **Train with `category_encoding_method = 'DUMMY_ENCODING'` if you intend to read `category_weights`.** The default `ONE_HOT_ENCODING` makes every categorical feature's dummies collinear with the intercept, so individual category weights are not uniquely identified — **verified**: retraining an identical `LINEAR_REG` model twice (same query, different `AUTO_SPLIT` draw) swung one category's weight from +305/+353/+340 to −39/−4/+8.6 between runs. `DUMMY_ENCODING` pins one category per feature to `weight: 0.0` and makes the rest stable, well-defined deltas. See `models/linear_regression/`.

**Limitations:**
- Tree/DNN/clustering/forecast/AutoML models are not supported (use type-specific functions or export).
- Categorical columns split their weights into the nested `category_weights` array, so a flat `SELECT *` shows NULL in `weight` for those rows.
- With `ONE_HOT_ENCODING` (the default), per-category weights are not uniquely identified and can vary substantially run-to-run (see best practice above) — this does not affect `ML.PREDICT`/`ML.EVALUATE`, only the individual weight breakdown.

**BigFrames API:** `model.global_explain()` covers attribution; raw coefficients via the underlying model are exposed through the BigQuery SQL function. No dedicated `ml_weights()` wrapper — call `ML.WEIGHTS` via `bigframes.pandas.read_gbq(...)` over the TVF.

**Repo example (tested):**
- `/home/user/git/vertex-ai-mlops/03 - BigQuery ML (BQML)/03a - BQML Logistic Regression.ipynb` — `SELECT * FROM ML.WEIGHTS(MODEL ...)` on a `LOGISTIC_REG` model trained with `CATEGORY_ENCODING_METHOD='DUMMY_ENCODING'`.
- `/home/user/git/vertex-ai-mlops/data+ai/bq-ml/models/linear_regression/linear_regression.sql` — `LINEAR_REG` on `penguins`/`body_mass_g`, trained with `DUMMY_ENCODING` specifically to keep `ML.WEIGHTS` stable and interpretable; SQL comments explain why. (Note: `data+ai/bq-ml/models/logistic_regression/logistic_regression.sql` does NOT demonstrate `ML.WEIGHTS` — that citation was a research-pass error, corrected here.)

---

### `ML.ADVANCED_WEIGHTS`
- **Description:** Extended version of `ML.WEIGHTS` for **linear regression** and **binary logistic regression** models. Returns the same weights plus per-weight **standard errors** and **p-values** (statistical significance). Its output is a superset of `ML.WEIGHTS`.
- **Use cases:**
  - Statistical inference on coefficients (significance testing) for econometric / explanatory modeling.
  - Identify which features have weights statistically distinguishable from zero.
- **documentation:** https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-advanced-weights
- **Type:** Table-valued function.
- **Applies to models:** `LINEAR_REG` and **binary** `LOGISTIC_REG` only. Multiclass logistic regression and matrix factorization are NOT supported. Model must be trained with `CALCULATE_P_VALUES = TRUE`, `CATEGORY_ENCODING_METHOD = 'DUMMY_ENCODING'`, and `L1_REG = 0`.

**Syntax:**
```sql
SELECT *
FROM ML.ADVANCED_WEIGHTS(MODEL `PROJECT_ID.DATASET.MODEL_NAME`
                         [, STRUCT(TRUE AS standardize)]);
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `MODEL` | model ref | Yes | — | Linear or binary logistic regression model trained with the required options above. |
| `STANDARDIZE` | BOOL (in STRUCT) | No | `FALSE` | Standardize weights (mean 0 / std 1). Set TRUE to obtain a standard error and p-value for the intercept. |

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| `processed_input` | STRING | Feature input column name. |
| `weight` | FLOAT64 | Weight for a numeric feature; NULL for categorical (see `category`). |
| `category` | STRING | Category name for non-numeric/dummy-encoded inputs (NULL for numeric). |
| `standard_error` | FLOAT64 | Standard error of the weight. NULL/absent for the intercept unless `standardize=TRUE`; `NaN` for a dropped dummy category. |
| `p_value` | FLOAT64 | p-value of the weight. Same intercept / dropped-category caveats as `standard_error`. |

**Best practices:**
- Train with `CALCULATE_P_VALUES = TRUE` up front — p-values/standard errors are computed at CREATE MODEL time and cannot be added later.
- Set `STANDARDIZE => TRUE` when you need inference statistics for the intercept.

**Limitations:**
- Not available for multiclass logistic regression, matrix factorization, or any non-GLM model.
- Requires `L1_REG = 0` and `DUMMY_ENCODING`; incompatible with L1 regularization.
- Dropped dummy categories report `weight = 0.0` with `NaN` standard error and p-value.

**BigFrames API:** No dedicated wrapper; call the TVF via SQL / `read_gbq`.

**Repo example (tested):**
- `/home/user/git/vertex-ai-mlops/03 - BigQuery ML (BQML)/03a - BQML Logistic Regression.ipynb` — model trained with `calculate_p_values = TRUE` and `CATEGORY_ENCODING_METHOD = 'DUMMY_ENCODING'`, then `SELECT * FROM ML.ADVANCED_WEIGHTS(MODEL ...)` to retrieve weights with p-values.

> Note: For boosted trees / random forest see `ML.FEATURE_IMPORTANCE` and `ML.GLOBAL_EXPLAIN`; for k-means see `ML.CENTROIDS`; for PCA/autoencoder see `ML.PRINCIPAL_COMPONENTS` / `ML.PRINCIPAL_COMPONENT_INFO`; for ARIMA_PLUS see `ML.ARIMA_COEFFICIENTS`. These tree/clustering/forecast notebooks (`03b`, `03g`, `03h`, `03i`, `BQML Univariate Forecasting with ARIMA+.ipynb`) do NOT use ML.WEIGHTS.


---

### Model Introspection: `ML.FEATURE_INFO`, `ML.TRAINING_INFO`, `ML.TRIAL_INFO`

These three table-valued functions read metadata that BigQuery ML records *during training*. They take no input data — they describe the model itself: the features it saw, how training converged, and (for tuned models) what each hyperparameter trial did. All three are GA.

---

### `ML.FEATURE_INFO`
- **Description:** Returns summary statistics for each input feature column the model saw during training — conceptually the model's equivalent of pandas `describe()`.
- **Use cases:**
  - Sanity-check the data a model actually trained on (ranges, nulls, cardinality).
  - Verify preprocessing worked (e.g. `null_count = 0` after `ML.IMPUTER`).
  - Document feature distributions for model cards / governance.
- **documentation:** https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-feature
- **Type:** Table-valued.
- **Applies to models:** Almost all trained model types (LINEAR_REG, LOGISTIC_REG, BOOSTED_TREE_*, RANDOM_FOREST_*, DNN_*, KMEANS, PCA, AUTOENCODER, MATRIX_FACTORIZATION, ARIMA_PLUS, etc.). **Not** supported on imported TensorFlow models. Remote models have no local features.

**Syntax:**
```sql
SELECT * FROM ML.FEATURE_INFO(MODEL `PROJECT_ID.DATASET.MODEL_NAME`);
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `MODEL` | model ref | Yes | — | The trained model to introspect. |

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| `input` | STRING | Name of the feature column. |
| `min` | FLOAT64 | Minimum value; NULL for non-numeric inputs. |
| `max` | FLOAT64 | Maximum value; NULL for non-numeric inputs. |
| `mean` | FLOAT64 | Average value; NULL for non-numeric inputs. |
| `median` | FLOAT64 | Median value; NULL for non-numeric inputs. |
| `stddev` | FLOAT64 | Standard deviation; NULL for non-numeric inputs. |
| `category_count` | INT64 | Number of distinct categories; NULL for non-categorical columns. |
| `null_count` | INT64 | Number of NULL values in the input column. |
| `dimension` | INT64 | For ARRAY-type feature columns, the array dimension. |

**Best practices:**
- Run it right after `CREATE MODEL` as a data-quality gate before trusting metrics.
- With a `TRANSFORM` clause, output describes the **pre-transform** columns from the `query_statement` — pair it with `ML.FEATURE_IMPORTANCE`/`ML.WEIGHTS` to see post-transform behavior.

**Limitations:**
- No imported-TensorFlow support.
- Stats are point-in-time from training; they do not reflect new serving data.

**BigFrames API:** No direct equivalent (inspect the model object / run the SQL via `bigframes`).
**Repo example (tested):** `data+ai/bq-ml/models/logistic_regression/logistic_regression.sql` (Example 8). Also in `03 - BigQuery ML (BQML)/03a - BQML Logistic Regression.ipynb`, `03b - BQML Boosted Trees.ipynb`, `03g - BQML - PCA with Anomaly Detection.ipynb`, `03h - BQML k-means with Anomaly Detection.ipynb`, `03i - BQML Autoencoder with Anomaly Detection.ipynb`, and `Applied Forecasting/BQML Univariate Forecasting with ARIMA+.ipynb` — same call shape across every model family.

---

### `ML.TRAINING_INFO`
- **Description:** Returns per-iteration training statistics (the loss/convergence curve), one row per iteration per training run.
- **Use cases:**
  - Plot the training vs. eval loss curve to diagnose under/over-fitting.
  - Confirm convergence and inspect `learning_rate` evolution.
  - Track training cost via `duration_ms`.
- **documentation:** https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-train
- **Type:** Table-valued.
- **Applies to models:** Iterative learners (LINEAR_REG, LOGISTIC_REG, KMEANS, MATRIX_FACTORIZATION, DNN_*, AUTOENCODER, BOOSTED_TREE_* / RANDOM_FOREST_* via XGBoost iterations) and time-series (ARIMA_PLUS, reduced output). **Not** supported on imported TensorFlow models.

**Syntax:**
```sql
SELECT iteration, loss, eval_loss, learning_rate, duration_ms
FROM ML.TRAINING_INFO(MODEL `PROJECT_ID.DATASET.MODEL_NAME`)
ORDER BY iteration;
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `MODEL` | model ref | Yes | — | The trained model to introspect. |

**Outputs (standard models):**

| Column | Type | Description |
|--------|------|-------------|
| `training_run` | INT64 | Training-run index. Multiple runs occur with warm-start or HP tuning. |
| `iteration` | INT64 | Iteration number within the training run. |
| `loss` | FLOAT64 | Loss on the training data after this iteration (e.g. log loss for logistic reg). |
| `eval_loss` | FLOAT64 | Loss on the holdout data. NULL when `DATA_SPLIT_METHOD = 'NO_SPLIT'`. |
| `learning_rate` | FLOAT64 | Learning rate used this iteration. |
| `duration_ms` | INT64 | Iteration duration in milliseconds. |

**Model-specific output differences:**

| Model family | Difference |
|---|---|
| K-means | No `eval_loss`; adds `cluster_info` ARRAY\<STRUCT\> with `centroid_id`, `cluster_radius`, `cluster_size` (computed on standardized features). |
| Time-series (ARIMA_PLUS) | Returns only `training_run`, `iteration`, `duration_ms`; no per-iteration metrics, and not broken out per time series; `duration_ms` is total cost. |

**Best practices:**
- `ORDER BY iteration` and chart `loss` vs `eval_loss` — divergence signals overfitting.
- For linear/logistic models, `learning_rate` can *rise* across iterations when `LEARN_RATE_STRATEGY = 'LINE_SEARCH'` (the default) — expected, not a bug.

**Limitations:**
- No imported-TensorFlow support.
- Limited usefulness for ARIMA_PLUS (use `ML.ARIMA_EVALUATE` / `ML.ARIMA_COEFFICIENTS` for forecast diagnostics instead).

**BigFrames API:** No direct equivalent.
**Repo example (tested):** `data+ai/bq-ml/models/logistic_regression/logistic_regression.sql` (Example 8, loss curve). Also `03a - BQML Logistic Regression.ipynb`, `03b - BQML Boosted Trees.ipynb`, `03g - BQML - PCA with Anomaly Detection.ipynb`, and `Applied Forecasting/BQML Univariate Forecasting with ARIMA+.ipynb` (reduced 3-column ARIMA output).

---

### `ML.TRIAL_INFO`
- **Description:** Returns one row per hyperparameter-tuning trial, with the hyperparameters tried, the objective metrics achieved, and which trial is optimal. Only meaningful for models trained with `NUM_TRIALS > 0`.
- **Use cases:**
  - Compare trials and see the search space the tuner explored.
  - Identify the optimal trial (`is_optimal`) used by default at serving time.
  - Debug `INFEASIBLE` trials (invalid hyperparameter combinations).
- **documentation:** https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-trial-info
- **Type:** Table-valued.
- **Applies to models:** Any model type that supports hyperparameter tuning **and** was created with `NUM_TRIALS` set (LINEAR_REG, LOGISTIC_REG, KMEANS, MATRIX_FACTORIZATION, BOOSTED_TREE_*, RANDOM_FOREST_*, DNN_*, AUTOENCODER, PCA, etc.).

**Syntax:**
```sql
SELECT
  trial_id,
  hyperparameters,
  hparam_tuning_evaluation_metrics,
  is_optimal
FROM ML.TRIAL_INFO(MODEL `PROJECT_ID.DATASET.MODEL_NAME`)
ORDER BY trial_id;
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `MODEL` | model ref | Yes | — | A model trained with `NUM_TRIALS > 0`. |

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| `trial_id` | INT64 | Trial ID in approximate execution order; starts at 1. |
| `hyperparameters` | STRUCT | The hyperparameter values used in this trial. |
| `hparam_tuning_evaluation_metrics` | STRUCT | Eval metrics matching the `hparam_tuning_objectives`; computed on eval data. |
| `training_loss` | FLOAT64 | Final training loss for the trial. |
| `eval_loss` | FLOAT64 | Final eval loss for the trial. |
| `status` | STRING | Trial state — e.g. `SUCCEEDED`, `INFEASIBLE` (invalid hyperparameter combo), `FAILED` (see gotcha below). |
| `error_message` | STRING | Error message if the trial did not succeed. |
| `is_optimal` | BOOL | TRUE for the best-objective trial; used by default at serving (override with `TRIAL_ID` arg). |

**Best practices:**
- Reach into the metric STRUCT to sort, e.g. `hparam_tuning_evaluation_metrics.roc_auc`.
- The optimal trial is used automatically by `ML.PREDICT`/`ML.EVALUATE` etc.; pass a `TRIAL_ID` to those functions to force a different trial.

**Limitations:**
- Returns nothing meaningful (errors) on models trained without `NUM_TRIALS`.
- **Corrected (was unverified speculation, now disproven by direct observation): `is_optimal = TRUE` is NOT guaranteed to mark exactly one row.** Verified on `models/random_forest_regressor/`: 2 of 6 trials (different `num_parallel_tree`/`max_tree_depth` combos) tied on `r2_score` and **both** showed `is_optimal = TRUE` simultaneously. Don't assume `WHERE is_optimal` returns a single row — `LIMIT 1` or an explicit tiebreak (e.g. smallest `trial_id`) if you need exactly one.
- **Verified**: a trial can transiently `FAILED` with `error_message = "An internal error happened during trial training."` — its objective metric column is `NULL` in `ML.TRIAL_INFO`, but this does **not** fail the overall `CREATE MODEL` job; BigQuery still selects `is_optimal` from among the successful trials (`models/boosted_tree_classifier/`, 1 of 6 trials failed this way; `models/random_forest_classifier/`, 2 of 6 failed under concurrent notebook execution — job completed normally both times). Check `status`/`error_message` before assuming a `NULL` metric means a bad hyperparameter combination.
- **Verified (DNN): the search order for a given model name is reproducible, not freshly randomized on each retrain — and this extends to DNN training generally, not just tuning.** Three full runs of `models/dnn_regressor/` (identical SQL, no seed) reproduced bit-for-bit identical `ML.TRIAL_INFO` sampled hyperparameters and `is_optimal` trial, plus bit-identical `ML.EVALUATE` results on the non-tuned baseline and fix models. A differently-named model with the same search-space config explored a different, worse region. Don't assume renaming/duplicating a `CREATE MODEL` with `NUM_TRIALS` will reproduce a known-good (or known-bad) search outcome from a differently-named model — see the `DNN_CLASSIFIER`/`DNN_REGRESSOR` entry for details.

**BigFrames API:** No direct equivalent.
**Repo example (tested):** `data+ai/bq-ml/models/logistic_regression/logistic_regression.sql` (Example 10 — `NUM_TRIALS=10` + `HPARAM_RANGE`, then sorts trials by `hparam_tuning_evaluation_metrics.roc_auc` and `is_optimal`). `data+ai/bq-ml/models/boosted_tree_classifier/boosted_tree_classifier.sql` (Example 10 — tunes `learn_rate`/`max_tree_depth`; observed a transient trial `FAILED`, see gotcha above). `data+ai/bq-ml/models/random_forest_regressor/random_forest_regressor.sql` (Example 9 — observed the `is_optimal` tie, see limitation above). Also `03 - BigQuery ML (BQML)/03h - BQML k-means with Anomaly Detection.ipynb` and `03i - BQML Autoencoder with Anomaly Detection.ipynb`.

> Related hyperparameter-tuning option reference (`NUM_TRIALS`, `HPARAM_RANGE`, `HPARAM_CANDIDATES`, `HPARAM_TUNING_OBJECTIVES`) lives with the per-model-type entries and the capability matrix.


---

### `ML.CENTROIDS`
- **Description:** Returns the learned centroid (cluster center) coordinates of a trained `KMEANS` model — one row per feature per centroid, so you can inspect what each cluster "looks like."
- **Use cases:**
  - Profile/interpret clusters by comparing each centroid's feature values.
  - Compare centroids across hyperparameter-tuning trials (one `trial_id` per tuned model).
  - Feed centroid coordinates into downstream segmentation/labeling logic.
- **documentation:** https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-centroids
- **Type:** Table-valued function (model weights function).
- **Applies to models:** `KMEANS` only.

**Syntax:**
```sql
SELECT *
FROM ML.CENTROIDS(MODEL `PROJECT_ID.DATASET.MODEL_NAME`
  [, STRUCT(standardize AS standardize)]);
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `MODEL` | model ref | Yes | — | A trained `KMEANS` model. |
| `standardize` | BOOL | No | `TRUE` | Whether to return centroid feature values in standardized (`TRUE`) or original (`FALSE`) space. |

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| `centroid_id` | INT64 | The cluster (centroid) identifier. |
| `feature` | STRING | The feature/column name. |
| `numerical_value` | FLOAT64 | Centroid value for numeric features (else NULL). |
| `categorical_value` | ARRAY\<STRUCT\<category STRING, value FLOAT64\>\> | Centroid values for categorical (one-hot) features. |
| `trial_id` | INT64 | Present only for hyperparameter-tuned models; identifies the trial. |

**Best practices:** Use `standardize = FALSE` to read centroids in the original feature units when profiling clusters for business stakeholders.
**Limitations:** `KMEANS` only — not valid for PCA/autoencoder/MF or supervised models. Numeric vs. categorical features land in separate columns; `UNNEST(categorical_value)` to flatten one-hot categories.
**BigFrames API:** `bigframes.ml.cluster.KMeans().cluster_centers_` (centroid attribute).
**Repo example (tested):** `/home/user/git/vertex-ai-mlops/03 - BigQuery ML (BQML)/03h - BQML k-means with Anomaly Detection.ipynb` — `ML.CENTROIDS` over a Vizier-tuned `KMEANS` model returns 32,910 rows (one feature x centroid x trial), with `trial_id` present because the model was HP-tuned.

---

### `ML.PRINCIPAL_COMPONENTS`
- **Description:** Returns the principal components (eigenvectors) of a trained `PCA` model — the per-feature loadings that define each component direction.
- **Use cases:**
  - Interpret which original features dominate each component (loadings).
  - Reconstruct/inspect the linear transform the model applies.
  - Combine with `ML.PRINCIPAL_COMPONENT_INFO` (eigenvalues) to rank components.
- **documentation:** https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-principal-components
- **Type:** Table-valued function (model weights function).
- **Applies to models:** `PCA` only.

**Syntax:**
```sql
SELECT *
FROM ML.PRINCIPAL_COMPONENTS(MODEL `PROJECT_ID.DATASET.MODEL_NAME`);
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `MODEL` | model ref | Yes | — | A trained `PCA` model. |

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| `principal_component_id` | INT64 | The principal component identifier (0-based). |
| `feature` | STRING | The feature/column name. |
| `numerical_value` | FLOAT64 | Loading for numeric features (else NULL). |
| `categorical_value` | ARRAY\<STRUCT\<category STRING, value FLOAT64\>\> | Loadings for categorical (one-hot) features. |

**Best practices:** Output is ordered descending by eigenvalue (most-explanatory component first). Join/compare against `ML.PRINCIPAL_COMPONENT_INFO` on `principal_component_id` to weight loadings by variance explained.
**Limitations:** `PCA` only. Categorical features are one-hot encoded — flatten `categorical_value` with `UNNEST`.
**BigFrames API:** `bigframes.ml.decomposition.PCA().components_`.
**Repo example (tested):** `/home/user/git/vertex-ai-mlops/03 - BigQuery ML (BQML)/03g - BQML - PCA with Anomaly Detection.ipynb` — `ML.PRINCIPAL_COMPONENTS` returns 780 rows (30 features x 26 components) for a model trained with `pca_explained_variance_ratio = 0.90`.

---

### `ML.PRINCIPAL_COMPONENT_INFO`
- **Description:** Returns per-component statistics (eigenvalue, explained variance ratio, cumulative explained variance ratio) for a trained `PCA` model.
- **Use cases:**
  - Decide how many components to keep (scree / cumulative-variance analysis).
  - Quantify how much information each component captures.
  - Pair with `ML.PRINCIPAL_COMPONENTS` to interpret loadings weighted by variance.
- **documentation:** https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-principal-component-info
- **Type:** Table-valued function (model weights function).
- **Applies to models:** `PCA` only.

**Syntax:**
```sql
SELECT *
FROM ML.PRINCIPAL_COMPONENT_INFO(MODEL `PROJECT_ID.DATASET.MODEL_NAME`);
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `MODEL` | model ref | Yes | — | A trained `PCA` model. |

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| `principal_component_id` | INT64 | The principal component (rows ordered descending by eigenvalue). |
| `eigenvalue` | FLOAT64 | Scaling factor of the eigenvector (same concept as the component's variance). |
| `explained_variance_ratio` | FLOAT64 | This component's variance / total variance. |
| `cumulative_explained_variance_ratio` | FLOAT64 | Running sum of `explained_variance_ratio` through this component. |

**Best practices:** Use `cumulative_explained_variance_ratio` to pick a component count. Note `ML.EVALUATE` on a PCA model returns the single complementary metric `total_explained_variance_ratio`.
**Limitations:** `PCA` only.
**BigFrames API:** `bigframes.ml.decomposition.PCA().explained_variance_` / `.explained_variance_ratio_`.
**Repo example (tested):** `/home/user/git/vertex-ai-mlops/03 - BigQuery ML (BQML)/03g - BQML - PCA with Anomaly Detection.ipynb` — returns 26 rows whose `cumulative_explained_variance_ratio` reaches 0.923, matching `ML.EVALUATE`'s `total_explained_variance_ratio = 0.923`.

---

### `ML.RECONSTRUCTION_LOSS`
- **Description:** Computes per-row reconstruction error between the input and the autoencoder's reconstructed output. The magnitude of the error is the basis for anomaly scoring.
- **Use cases:**
  - Score how poorly each row reconstructs (high error = candidate anomaly).
  - Data sanitation / outlier detection on new data.
  - Inspect the error distribution feeding `ML.DETECT_ANOMALIES`.
- **documentation:** https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-reconstruction-loss
- **Type:** Table-valued function (evaluation function).
- **Applies to models:** `AUTOENCODER` only. (PCA does NOT support it — use `ML.EVALUATE`'s `total_explained_variance_ratio` for PCA quality. Imported TensorFlow models are not supported.)

**Syntax:**
```sql
SELECT *
FROM ML.RECONSTRUCTION_LOSS(
  MODEL `PROJECT_ID.DATASET.MODEL_NAME`,
  { TABLE `PROJECT_ID.DATASET.TABLE` | (QUERY_STATEMENT) });
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `MODEL` | model ref | Yes | — | A trained `AUTOENCODER` model. |
| `TABLE` / `QUERY_STATEMENT` | table or query | Yes | — | Input rows to reconstruct; column names/types must match the model (or the `TRANSFORM` clause inputs if one was used). |

**Outputs:** (input columns are passed through alongside these error metrics)

| Column | Type | Description |
|--------|------|-------------|
| `mean_absolute_error` | FLOAT64 | Per-row mean absolute reconstruction error. |
| `mean_squared_error` | FLOAT64 | Per-row mean squared reconstruction error. |
| `mean_squared_log_error` | FLOAT64 | Per-row mean squared log reconstruction error. |
| `trial_id` | INT64 | Present for hyperparameter-tuned models; identifies the optimal trial used. |

**Best practices:** For anomaly detection prefer `ML.DETECT_ANOMALIES` (handles contamination thresholding) and reserve `ML.RECONSTRUCTION_LOSS` for inspecting the raw error distribution. Larger errors indicate rows the model could not reconstruct (likely anomalous).
**Limitations:** `AUTOENCODER` only; no imported TensorFlow models. If `TRANSFORM` was used at training, the input may only reference the `TRANSFORM` input columns.
**BigFrames API:** No direct equivalent (`bigframes.ml` autoencoder reconstruction-loss helper not exposed); use the SQL function.
**Repo example (tested):** `/home/user/git/vertex-ai-mlops/03 - BigQuery ML (BQML)/03i - BQML Autoencoder with Anomaly Detection.ipynb` — `ML.RECONSTRUCTION_LOSS` over the TEST split returns `mean_absolute_error`, `mean_squared_error`, `mean_squared_log_error`, plus `trial_id` (the model was HP-tuned) and the passed-through input columns.

---

> Cross-reference: for anomaly detection from these models see `ML.DETECT_ANOMALIES`; for extracting embeddings from a trained PCA/AUTOENCODER/MATRIX_FACTORIZATION model see the in-scope `ML.GENERATE_EMBEDDING` lifecycle entry. Foundation-model (text/multimodal) embedding generation lives in [../bq-ai-functions](../bq-ai-functions/RESOURCES.md).


---

### `ML.RECOMMEND`
- **Description:** Generates recommendations (predicted ratings or confidences) from a trained `MATRIX_FACTORIZATION` model for user-item pairs. Because the training input is a sparse matrix, the function fills in predictions for the missing user-item entries.
- **Use cases:**
  - Score every item for a given user (top-N recommendations).
  - Score a specific user-item pair (predicted rating / confidence).
  - Batch-generate the full user x item recommendation matrix for offline serving.
- **documentation:** https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-recommend
- **Type:** Table-valued function.
- **Applies to models:** `MATRIX_FACTORIZATION` only (explicit or implicit `feedback_type`).

**Syntax:**
```sql
SELECT *
FROM ML.RECOMMEND(
  MODEL `PROJECT_ID.DATASET.MODEL_NAME`
  [, { TABLE `PROJECT_ID.DATASET.INPUT` | (QUERY_STATEMENT) }]
  [, STRUCT(TRIAL_ID AS trial_id)]
);
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `MODEL` | model | Yes | — | A trained `MATRIX_FACTORIZATION` model. |
| `TABLE` / `QUERY_STATEMENT` | table/query | No | all user x item pairs | Input rows. If both user and item columns are present, returns one rating per pair; if only the user (or only the item) column is present, returns all item (or user) ratings; if omitted, returns predictions for every user-item combination. Column names/types must match the model's user and item columns (implicit coercion applies). |
| `trial_id` | INT64 | No | optimal trial | Selects a specific hyperparameter-tuning trial; only valid if the model was trained with HP tuning. |

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| \<user_col\> | matches model | The user identifier column (named as in the model). |
| \<item_col\> | matches model | The item identifier column (named as in the model). |
| `predicted_`\<rating_col\> | FLOAT64 | EXPLICIT feedback: predicted rating, roughly in the range of the original input ratings (values outside the range are normal). |
| `predicted_`\<rating_col\>`_confidence` | FLOAT64 | IMPLICIT feedback: relative confidence, approximately 0-1 when the model has converged. |
| `trial_id` | INT64 | Present only when the model was trained with HP tuning. |

**Best practices:**
- Output can be very large (all user x item pairs); write results to a table rather than streaming.
- For top-N, `ORDER BY predicted_<rating_col>[_confidence] DESC LIMIT N` per user.
- Pin `trial_id` only when you need a non-optimal HP-tuning trial.

**Limitations:**
- Matrix factorization models require reservation/flat-rate (slot) capacity to train; `ML.RECOMMEND` itself runs as a standard query but the upstream model has that prerequisite.
- Input user/item columns must align with the model's training columns.

**BigFrames API:** `bigframes.ml.decomposition.MatrixFactorization.predict()` (DataFrame in/out) is the recommendation equivalent.

**Repo example (tested):** No matrix-factorization notebook exists among the assigned repo files; the closest tested lifecycle parallels are the `ML.PREDICT` patterns in `/home/user/git/vertex-ai-mlops/03 - BigQuery ML (BQML)/03g - BQML - PCA with Anomaly Detection.ipynb` and the supervised `ML.PREDICT` flow in `/home/user/git/vertex-ai-mlops/03 - BigQuery ML (BQML)/03a - BQML Logistic Regression.ipynb`. ML.RECOMMEND syntax above is sourced from Google Cloud docs.

---

### `ML.GENERATE_EMBEDDING` (from a BQML PCA / AUTOENCODER / MATRIX_FACTORIZATION model)

> **Scope note:** This entry covers ONLY the in-house BQML-model use of `ML.GENERATE_EMBEDDING` — extracting embeddings from a trained `PCA`, `AUTOENCODER`, or `MATRIX_FACTORIZATION` model. The **foundation/remote-model (text & multimodal) use** of `ML.GENERATE_EMBEDDING` / `AI.GENERATE_EMBEDDING` is owned by `../bq-ai-functions/` — see that doc; do not duplicate here.

- **Description:** Produces a single `ARRAY<FLOAT>` embedding column from a trained BQML model so the result can be consumed directly by `VECTOR_SEARCH`. The function delegates internally: PCA/autoencoder route through `ML.PREDICT`; matrix factorization routes through `ML.WEIGHTS`.
- **Use cases:**
  - Turn PCA principal-component projections into a single vector column for similarity search.
  - Extract autoencoder latent-space (bottleneck) representations as embeddings.
  - Extract matrix-factorization user/item factor weights as entity embeddings.
- **documentation:** https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-generate-embedding
- **Type:** Table-valued function.
- **Applies to models:** `PCA`, `AUTOENCODER`, `MATRIX_FACTORIZATION` (this entry); plus remote/foundation embedding models (cross-link out).

**Syntax:**
```sql
SELECT *
FROM ML.GENERATE_EMBEDDING(
  MODEL `PROJECT_ID.DATASET.MODEL_NAME`,
  { TABLE `PROJECT_ID.DATASET.INPUT` | (QUERY_STATEMENT) }
  [, STRUCT(TRIAL_ID AS trial_id)]
);
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `MODEL` | model | Yes | — | A trained `PCA`, `AUTOENCODER`, or `MATRIX_FACTORIZATION` model. |
| `TABLE` / `QUERY_STATEMENT` | table/query | Yes | — | Input rows. For PCA/autoencoder, columns must match the model's training features. For matrix factorization, provide the user or item entities. |
| `trial_id` | INT64 | No | optimal trial | Select a specific HP-tuning trial (only when trained with HP tuning). |

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| `ml_generate_embedding_result` | ARRAY\<FLOAT\> | The embedding. PCA: one element per principal component (set by `num_principal_components`, or variable when `pca_explained_variance_ratio` is used). AUTOENCODER: dimension = the middle (bottleneck) entry of `hidden_units`. MATRIX_FACTORIZATION: the factor weights plus the intercept/bias as the last element; length = `num_factors` (+1 for intercept). |
| `processed_input` | STRING | Matrix factorization only: the name of the user or item column the embedding represents. |
| `trial_id` | INT64 | Present only when the model was trained with HP tuning. |
| *(passthrough)* | — | Input columns are carried through alongside the embedding. |

**Best practices:**
- The single `ml_generate_embedding_result` column is purpose-built for `VECTOR_SEARCH` — keep it as the array and avoid unnesting before indexing.
- For autoencoders, the bottleneck size (middle of `hidden_units`) directly sets the embedding dimension — choose it deliberately at train time.
- `AI.GENERATE_EMBEDDING` is the newer simplified variant; it emits the result in an `embedding` column instead of `ml_generate_embedding_result`. Use `ML.GENERATE_EMBEDDING` when you need the granular PCA / matrix-factorization control.

**Limitations:**
- Embeddings reflect only what the underlying model learned (linear components for PCA; reconstruction-driven latents for autoencoders; collaborative factors for matrix factorization) — not semantic text/image meaning (use the foundation-model path for that).
- Matrix-factorization embeddings are per-entity (user/item), not per-row feature embeddings.

**BigFrames API:** No direct single-call `generate_embedding` wrapper for these in-house model types; equivalent results come from `PCA.transform()`, the autoencoder `predict()` latent output, and `MatrixFactorization` weights via the respective `bigframes.ml` classes. (Foundation embeddings: `bigframes.ml.llm.TextEmbeddingGenerator` — cross-link out.)

**Repo example (tested):**
- PCA projections (the values `ML.GENERATE_EMBEDDING` arrays for a PCA model) come from `ML.PREDICT` — see `/home/user/git/vertex-ai-mlops/03 - BigQuery ML (BQML)/03g - BQML - PCA with Anomaly Detection.ipynb` (CREATE MODEL `model_type='PCA'`, then `ML.PREDICT` yielding `principal_component_1..N`; serving payload returns `principal_component_projections`).
- Autoencoder latent space (the embedding source for an autoencoder model) — see `/home/user/git/vertex-ai-mlops/03 - BigQuery ML (BQML)/03i - BQML Autoencoder with Anomaly Detection.ipynb` (CREATE MODEL `model_type='AUTOENCODER'` with `hidden_units=[...,8,...]`; `ML.PREDICT` returns `latent_col_1..8`; `ML.RECONSTRUCTION_LOSS` for quality).

These notebooks demonstrate the underlying `ML.PREDICT` mechanics; the `ML.GENERATE_EMBEDDING` wrapper packages those same outputs into one array column. The k-means anomaly-detection notebook (`03h`) is a sibling unsupervised example. The `ML.GENERATE_EMBEDDING` array-output syntax above is sourced from Google Cloud docs.


---

### ARIMA_PLUS forecasting lifecycle functions

These five table-valued functions consume a trained `ARIMA_PLUS` (univariate) or `ARIMA_PLUS_XREG`
(multivariate) model. The forecast and time-series decomposition are computed **at `CREATE MODEL`
time**; these functions retrieve the stored results and compute confidence/prediction intervals on
demand. They are **GA**, require **no connection**, and have no foundation-model dependency.

> For the foundation-model forecaster (`AI.FORECAST` / TimesFM, zero training, no `CREATE MODEL`),
> see [`../bq-ai-functions/RESOURCES.md` → AI.FORECAST](../bq-ai-functions/RESOURCES.md). The
> entries below are the classic, statistical ARIMA_PLUS path that lives in bq-ml.

---

### `ML.FORECAST`
- **Description:** Returns forecasted values with standard error and prediction/confidence intervals for a trained `ARIMA_PLUS` or `ARIMA_PLUS_XREG` time-series model.
- **Use cases:**
  - Produce point forecasts + intervals over a future horizon.
  - Serve demand/volume forecasts directly in BigQuery (one row per `forecast_timestamp` per series).
  - Multivariate forecasting using future covariate values (`ARIMA_PLUS_XREG`).
- **documentation:** https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-forecast
- **Type:** Table-valued.
- **Applies to models:** `ARIMA_PLUS`, `ARIMA_PLUS_XREG`. **Status:** GA.

**Syntax:**
```sql
-- ARIMA_PLUS (univariate):
SELECT *
FROM ML.FORECAST(
  MODEL `PROJECT_ID.DATASET.MODEL_NAME`,
  STRUCT(14 AS horizon, 0.95 AS confidence_level)
);

-- ARIMA_PLUS_XREG (multivariate) — future feature values are REQUIRED:
SELECT *
FROM ML.FORECAST(
  MODEL `PROJECT_ID.DATASET.MODEL_NAME`,
  STRUCT(30 AS horizon, 0.8 AS confidence_level),
  (SELECT date, temperature, wind_speed
   FROM `PROJECT_ID.DATASET.future_features`)
);
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `horizon` | INT64 | No | 3 | Number of future time points to forecast. Max = `horizon` set in `CREATE MODEL` (or 1000 if unset). Set `horizon` at model creation to save query time. |
| `confidence_level` | FLOAT64 | No | 0.95 | Fraction of future values expected within the prediction interval. Range `[0, 1)`. |
| `TABLE`/`QUERY_STATEMENT` | table/query | `ARIMA_PLUS_XREG` only | — | Future covariate values; column names/types must match the model. Ignored extra columns are dropped. |

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| `\<time_series_id_col\>` | (varies) | Series id column(s), present only when the model was trained with `time_series_id_col`. |
| `forecast_timestamp` | TIMESTAMP | Forecast point (rows sorted chronologically per series). |
| `forecast_value` | FLOAT64 | Point forecast (midpoint of the prediction interval). |
| `standard_error` | FLOAT64 | Standard error of the forecast. |
| `confidence_level` | FLOAT64 | Echoes the input confidence level. |
| `prediction_interval_lower_bound` / `prediction_interval_upper_bound` | FLOAT64 | Prediction interval bounds (depend on `standard_error` and `confidence_level`). |
| `confidence_interval_lower_bound` / `confidence_interval_upper_bound` | FLOAT64 | Confidence interval bounds (legacy columns; equal the prediction bounds). |

**Best practices:** Set `horizon` (and `holiday_region`) at `CREATE MODEL` time. Use the forecast-with-`LIMIT` pattern instead of post-filtering large outputs.
**Limitations:** Adding computation on top of large outputs (min/max, arithmetic, filters) can raise "Resources exceeded during query execution". `ARIMA_PLUS_XREG` requires future feature values to forecast.
**BigFrames API:** `bigframes.ml.forecasting.ARIMAPlus().predict(X)`.
**Repo example (tested):** `/home/user/git/vertex-ai-mlops/Applied Forecasting/BQML Univariate Forecasting with ARIMA+.ipynb` (cell 45) — `STRUCT(1 AS horizon, 0.95 AS confidence_level)` over a multi-series Citibike model.

---

### `ML.EXPLAIN_FORECAST`
- **Description:** Superset of `ML.FORECAST`: returns the forecast **plus** the full time-series decomposition (trend, seasonality per period, holiday effects, spikes/dips, step changes, residual) for both history and forecast rows. Enabled by `decompose_time_series = TRUE` (the ARIMA_PLUS default).
- **Use cases:**
  - Explain *why* a forecast moves (trend vs. weekly seasonality vs. a holiday).
  - Recover the cleaned/adjusted fit (`time_series_adjusted_data`) for plotting and custom metrics.
  - Per-holiday and per-feature (XREG) attribution.
- **documentation:** https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-explain-forecast
- **Type:** Table-valued. **Applies to models:** `ARIMA_PLUS`, `ARIMA_PLUS_XREG`. **Status:** GA.

**Syntax:**
```sql
SELECT *
FROM ML.EXPLAIN_FORECAST(
  MODEL `PROJECT_ID.DATASET.MODEL_NAME`,
  STRUCT(28 AS horizon, 0.95 AS confidence_level)
);
```

**Inputs:** same `horizon` / `confidence_level` STRUCT as `ML.FORECAST` (`ARIMA_PLUS_XREG` also takes a future-features table/query).

**Outputs (in addition to the `ML.FORECAST` columns):**

| Column | Type | Description |
|--------|------|-------------|
| `time_series_timestamp` | TIMESTAMP | Point in time (history or forecast). |
| `time_series_type` | STRING | `history` or `forecast`. |
| `time_series_data` | FLOAT64 | Observed (history) or forecast value, including noise components. |
| `time_series_adjusted_data` | FLOAT64 | Cleaned fit (excludes `spikes_and_dips`, `step_changes`, `residual`). |
| `trend` | FLOAT64 | Long-term level. |
| `seasonal_period_yearly`/`_quarterly`/`_monthly`/`_weekly`/`_daily` | FLOAT64 | Per-period seasonal effect; NULL if that period isn't detected. |
| `holiday_effect` | FLOAT64 | Total holiday effect = sum of `holiday_effect_\<holiday_name\>` subcolumns (one column per detected holiday). |
| `spikes_and_dips` | FLOAT64 | Outlier component (history only). |
| `step_changes` | FLOAT64 | Abrupt level-shift component (history only). |
| `residual` | FLOAT64 | Unexplained remainder (history only). |
| `attribution_feature_\<name\>` | FLOAT64 | Per-covariate contribution (`ARIMA_PLUS_XREG` only). |

Decomposition identity: `time_series_data = trend + Σ seasonal_period_* + holiday_effect + spikes_and_dips + step_changes + residual`. For `forecast` rows, `spikes_and_dips`/`step_changes`/`residual` are not applicable, so `time_series_data` and `time_series_adjusted_data` coincide.

**Best practices:** Use `time_series_adjusted_data WHERE time_series_type='forecast'` as the fitted forecast for custom SQL metrics (MAPE/MAE/RMSE).
**Limitations:** Decomposition components for spikes/step/residual exist only for history. Same large-output memory caveat as `ML.FORECAST`.
**BigFrames API:** No direct equivalent (use `ML.EXPLAIN_FORECAST` via SQL).
**Repo example (tested):** `/home/user/git/vertex-ai-mlops/Applied Forecasting/BQML Univariate Forecasting with ARIMA+.ipynb` (cells 47, 53, 55) — drives both the forecast funnel chart and SQL-computed MAPE/MAE/pMAE/MSE/RMSE/pRMSE.

---

### `ML.ARIMA_EVALUATE`
- **Description:** Returns the auto-ARIMA model selection results and quality metrics, one row per time series (the candidate chosen by auto.ARIMA, or all candidates with `show_all_candidate_models`).
- **Use cases:**
  - Inspect the selected `(p,d,q)` order, drift, and AIC per series.
  - See which decomposition features fired (`has_holiday_effect`, `has_spikes_and_dips`, `has_step_changes`) and detected seasonalities.
  - Surface per-series training failures via `error_message`.
- **documentation:** https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-arima-evaluate
- **Type:** Table-valued. **Applies to models:** `ARIMA_PLUS`, `ARIMA_PLUS_XREG`. **Status:** GA.

**Syntax:**
```sql
SELECT *
FROM ML.ARIMA_EVALUATE(
  MODEL `PROJECT_ID.DATASET.MODEL_NAME`,
  STRUCT(FALSE AS show_all_candidate_models)
);
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `show_all_candidate_models` | BOOL | No | FALSE | If TRUE, returns every candidate ARIMA model evaluated by auto.ARIMA; if FALSE, only the selected model per series. |

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| `\<time_series_id_col\>` | (varies) | Series id (when trained with `time_series_id_col`). |
| `non_seasonal_p` / `non_seasonal_d` / `non_seasonal_q` | INT64 | ARIMA order (AR lags, differencing degree, MA terms). |
| `has_drift` | BOOL | Whether a drift term is included. |
| `log_likelihood` | FLOAT64 | Model log-likelihood. |
| `AIC` | FLOAT64 | Akaike Information Criterion (lower is better; selection criterion). |
| `variance` | FLOAT64 | Variance of the model residuals. |
| `seasonal_periods` | ARRAY\<STRING\> | Detected seasonalities, e.g. `[WEEKLY]`, `[WEEKLY, YEARLY]`, `[NO_SEASONALITY]`. |
| `has_holiday_effect` | BOOL | Holiday effect detected (when `holiday_region` set). |
| `has_spikes_and_dips` | BOOL | Spike/dip outliers detected. |
| `has_step_changes` | BOOL | Step (level) changes detected. |
| `error_message` | STRING | Per-series training error, empty when successful. |

**Best practices:** Order by the series id column for stable review; check `error_message` for short/failed series.
**Limitations:** `seasonal_periods`, `has_holiday_effect`, etc. depend on `CREATE MODEL` options (e.g. `holiday_region`).
**BigFrames API:** No direct equivalent.
**Repo example (tested):** `/home/user/git/vertex-ai-mlops/Applied Forecasting/BQML Univariate Forecasting with ARIMA+.ipynb` (cell 41) — full per-station ARIMA evaluation table.

---

### `ML.ARIMA_COEFFICIENTS`
- **Description:** Returns the fitted ARIMA coefficients per time series — the "weights" function for ARIMA_PLUS models.
- **Use cases:** Inspect AR/MA coefficient vectors and the intercept/drift; audit/export fitted model parameters.
- **documentation:** https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-arima-coefficients
- **Type:** Table-valued (model-weights family). **Applies to models:** `ARIMA_PLUS`, `ARIMA_PLUS_XREG`. **Status:** GA.

**Syntax:**
```sql
SELECT *
FROM ML.ARIMA_COEFFICIENTS(MODEL `PROJECT_ID.DATASET.MODEL_NAME`);
```

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| `\<time_series_id_col\>` | (varies) | Series id (when trained with `time_series_id_col`). |
| `ar_coefficients` | ARRAY\<FLOAT64\> | Autoregressive (AR) coefficients; length = `non_seasonal_p`. Empty `[]` when p=0. |
| `ma_coefficients` | ARRAY\<FLOAT64\> | Moving-average (MA) coefficients; length = `non_seasonal_q`. Empty `[]` when q=0. |
| `intercept_or_drift` | FLOAT64 | Constant (intercept) or drift term of the model. |

**Best practices:** Join with `ML.ARIMA_EVALUATE` on the series id to pair `(p,d,q)` with the coefficient vectors.
**Limitations:** Output is the ARIMA-specific analog of `ML.WEIGHTS`; standard `ML.WEIGHTS` does not apply to ARIMA_PLUS.
**BigFrames API:** `bigframes.ml.forecasting.ARIMAPlus().coef_` (or `.summary()`).
**Repo example (tested):** `/home/user/git/vertex-ai-mlops/Applied Forecasting/BQML Univariate Forecasting with ARIMA+.ipynb` (cell 32) — per-station `ar_coefficients` / `ma_coefficients` / `intercept_or_drift`.

---

### `ML.HOLIDAY_INFO`
- **Description:** Lists the holidays modeled by an ARIMA_PLUS model and the holiday effects it detected, expanded by date across the modeled range.
- **Use cases:** Audit which holidays/regions the model accounts for; align holiday windows with observed effects.
- **documentation:** https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-holiday-info
- **Type:** Table-valued. **Applies to models:** `ARIMA_PLUS`, `ARIMA_PLUS_XREG` trained with `holiday_region`. **Status:** GA.

**Syntax:**
```sql
SELECT *
FROM ML.HOLIDAY_INFO(MODEL `PROJECT_ID.DATASET.MODEL_NAME`);
```

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| `region` | STRING | Holiday region from `CREATE MODEL` `holiday_region` (e.g. `GLOBAL`, `US`). |
| `holiday_name` | STRING | Name of the holiday with a modeled/detected effect. |
| `primary_date` | DATE | Calendar date of that holiday occurrence. |
| `preholiday_days` | INT64 | Days before `primary_date` included in the holiday window. |
| `postholiday_days` | INT64 | Days after `primary_date` included in the holiday window. |

**Best practices:** Requires `holiday_region` (one or many, e.g. `['GLOBAL','US']`) at `CREATE MODEL`. Output spans many years/holidays — aggregate or filter by `region`/`holiday_name` for review.
**Limitations:** Empty if the model was trained without `holiday_region`. Returns the holiday calendar/windows, not the numeric effect (use `ML.EXPLAIN_FORECAST` `holiday_effect_*` columns for magnitudes).
**BigFrames API:** No direct equivalent.
**Repo example (tested):** `/home/user/git/vertex-ai-mlops/Applied Forecasting/BQML Univariate Forecasting with ARIMA+.ipynb` (cell 43; model trained with `holiday_region = ['GLOBAL', 'US']`) — 1,624 region/holiday/date rows.

---

#### Forecast `ML.EVALUATE` metrics (ARIMA_PLUS)
When `ML.EVALUATE` is called on an ARIMA_PLUS model **with** test data and `perform_aggregation=TRUE`,
it returns per-series: `mean_absolute_error`, `mean_squared_error`, `root_mean_squared_error`,
`mean_absolute_percentage_error`, `symmetric_mean_absolute_percentage_error`,
`mean_absolute_scaled_error`. With
`perform_aggregation=FALSE` it returns per-timestamp metrics; with no input data it returns the
in-training ARIMA metrics (see `ML.ARIMA_EVALUATE`). Anomaly detection on the same model uses
[`ML.DETECT_ANOMALIES`](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-detect-anomalies)
with `anomaly_prob_threshold` (repo example: same notebook, cell 57).


---

### `ML.DETECT_ANOMALIES`
- **Description:** Performs unsupervised anomaly detection against a trained BQML model. Returns each input row flagged `is_anomaly` (TRUE/FALSE) plus the score the flag is based on. The detection mechanism and threshold parameter differ by model family: error/distance-cutoff for IID models (PCA, AUTOENCODER, KMEANS) and prediction-interval probability for time-series models (ARIMA_PLUS, ARIMA_PLUS_XREG).
- **Use cases:**
  - Fraud / outlier detection on tabular data using a PCA, autoencoder, or k-means model (reconstruction error / distance from centroid).
  - Detecting anomalous points in a forecasted time series (value falls outside the model's prediction interval).
  - Turning an unsupervised dimensionality-reduction / clustering model into a binary anomaly classifier without labels.
- **documentation:** https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-detect-anomalies
- **Type:** Table-valued function.
- **Applies to models:** `PCA`, `AUTOENCODER`, `KMEANS` (use `contamination`); `ARIMA_PLUS`, `ARIMA_PLUS_XREG` (use `anomaly_prob_threshold`). Not applicable to supervised regression/classification model types.

> Cross-link (do NOT duplicate): for foundation-model / TimesFM time-series anomaly detection see `AI.DETECT_ANOMALIES` in [../bq-ai-functions/](../bq-ai-functions/RESOURCES.md).

**Syntax (IID models — PCA / AUTOENCODER / KMEANS):**
```sql
SELECT *
FROM ML.DETECT_ANOMALIES(
  MODEL `PROJECT_ID.DATASET.MODEL_NAME`,
  STRUCT(0.02 AS contamination),
  (SELECT * FROM `PROJECT_ID.DATASET.NEW_DATA`)
);
```

**Syntax (time-series models — ARIMA_PLUS / ARIMA_PLUS_XREG):**
```sql
SELECT *
FROM ML.DETECT_ANOMALIES(
  MODEL `PROJECT_ID.DATASET.MODEL_NAME`,
  STRUCT(0.95 AS anomaly_prob_threshold)
  -- optional new_data: , (SELECT ts_id, ts_timestamp, ts_value FROM `PROJECT_ID.DATASET.NEW_DATA`)
);
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `MODEL` | model | Yes | — | A trained PCA, AUTOENCODER, KMEANS, ARIMA_PLUS, or ARIMA_PLUS_XREG model. |
| `contamination` | FLOAT64 | No (IID only) | — | Proportion `[0, 0.5]` of rows expected to be anomalous; sets the cutoff on the target metric (MSE for PCA/AUTOENCODER, normalized distance for KMEANS). e.g. `0.1` flags the top 10% highest-error rows. |
| `anomaly_prob_threshold` | FLOAT64 | No (time-series only) | `0.95` | Probability cutoff in range `[0, 1)`. A point is anomalous if its `anomaly_probability` exceeds this; also sets the width of `lower_bound`/`upper_bound`. |
| `new_data` (query/TABLE) | table | No\* | — | Data to score. If omitted for time-series, the training data is scored. For IID models the data expression is supplied as the 3rd argument. |

\* For ARIMA_PLUS, scoring historical (training) data requires `decompose_time_series = TRUE` (the default) at CREATE MODEL time; scoring new data requires `anomaly_prob_threshold`.

**Outputs (IID — PCA / AUTOENCODER / KMEANS):**

| Column | Type | Description |
|--------|------|-------------|
| `is_anomaly` | BOOL | TRUE if the row's target metric exceeds the `contamination`-derived cutoff. |
| `mean_squared_error` | FLOAT64 | Reconstruction error (PCA, AUTOENCODER). |
| `normalized_distance` | FLOAT64 | Distance from nearest centroid (KMEANS). |
| `CENTROID_ID` | INT64 | Nearest centroid (KMEANS). |
| (passthrough) | — | All input columns are echoed back (e.g. `Time`, `V1`…`V28`, `Amount`, plus `trial_id` for HP-tuned models). |

**Outputs (time-series — ARIMA_PLUS / ARIMA_PLUS_XREG):**

| Column | Type | Description |
|--------|------|-------------|
| `is_anomaly` | BOOL | TRUE if `anomaly_probability` \> `anomaly_prob_threshold`. |
| `anomaly_probability` | FLOAT64 | Probability the point is an anomaly. |
| `lower_bound` / `upper_bound` | FLOAT64 | Prediction-interval bounds (width grows with the threshold). |
| `time_series_timestamp` / `time_series_data` | — | The timestamp and observed value (plus the `time_series_id_col` value when present). |

**Best practices:**
- Set `contamination` to a domain-informed expected outlier rate. The repo notebooks compute it from the training-data positive-class rate (`TRAIN_FRAUD_PCT ≈ 0.00174`) and pass it as `STRUCT(TRAIN_FRAUD_PCT AS contamination)`.
- For evaluation, map `is_anomaly` to 0/1 and build a confusion matrix against known labels (the notebooks do this with `CASE WHEN is_anomaly ... END`).
- For ARIMA_PLUS, keep `decompose_time_series = TRUE` so forecast errors are retained for historical anomaly scoring.

**Limitations:**
- `contamination` and `anomaly_prob_threshold` are mutually exclusive — each applies only to its model family.
- IID detection is purely error/distance-rank based: a row is "anomalous" only relative to the chosen contamination cutoff, not an absolute judgement.
- Recall on rare classes is typically low (fraud notebooks show high precision-0 / low recall-1), since these are unsupervised methods.

**BigFrames API:** `model.detect_anomalies(X, contamination=...)` on `bigframes.ml.decomposition.PCA`, `bigframes.ml.cluster.KMeans`, and the autoencoder/forecasting estimators.

**Repo example (tested):**
- `03 - BigQuery ML (BQML)/03g - BQML - PCA with Anomaly Detection.ipynb` — PCA + `STRUCT(TRAIN_FRAUD_PCT AS contamination)`, confusion matrix from `is_anomaly`.
- `03 - BigQuery ML (BQML)/03h - BQML k-means with Anomaly Detection.ipynb` — KMEANS (HP-tuned), output includes `normalized_distance`, `CENTROID_ID`, `trial_id`.
- `03 - BigQuery ML (BQML)/03i - BQML Autoencoder with Anomaly Detection.ipynb` — AUTOENCODER (HP-tuned); see also `ML.RECONSTRUCTION_LOSS` for the underlying MSE.
- `Applied Forecasting/BQML Univariate Forecasting with ARIMA+.ipynb` — ARIMA_PLUS with `STRUCT(0.95 AS anomaly_prob_threshold)`, filtering `WHERE anomaly_probability >= 0.95`; output has `is_anomaly`, `anomaly_probability`, `lower_bound`, `upper_bound`.

---

### `ML.TRANSFORM` (applying a saved transform)
- **Description:** Applies the preprocessing captured in a model's `TRANSFORM` clause to new data and returns the transformed feature columns only — no prediction. The transformation statistics (scaler mins/maxes, bucket edges, encoder vocabularies, etc.) computed at training time are reused, so training and serving see identical preprocessing.
- **Use cases:**
  - Inspect exactly what a model feeds its algorithm after preprocessing (debugging feature engineering).
  - Reuse a saved transform (especially a `model_type = 'TRANSFORM_ONLY'` model) to preprocess data feeding a *different* model's training or `ML.PREDICT`.
  - Materialize preprocessed features for downstream non-BQML use.
- **documentation:** https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-transform
- **Type:** Table-valued function.
- **Applies to models:** Any model created with a `TRANSFORM(...)` clause, including transform-only models (`model_type = 'TRANSFORM_ONLY'`).

> Automatic application: you usually do NOT need `ML.TRANSFORM`. A `TRANSFORM` clause defined in `CREATE MODEL` is applied automatically inside `ML.PREDICT`, `ML.EVALUATE`, `ML.DETECT_ANOMALIES`, `ML.RECONSTRUCTION_LOSS`, and online serving — call raw columns and BQML re-preprocesses them. `ML.TRANSFORM` is for the cases where you want the preprocessed output by itself.

**Syntax:**
```sql
SELECT *
FROM ML.TRANSFORM(
  MODEL `PROJECT_ID.DATASET.MODEL_NAME`,
  (SELECT * FROM `PROJECT_ID.DATASET.NEW_DATA`)
);
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `MODEL` | model | Yes | — | Must have been created with a `TRANSFORM` clause. |
| `query_statement` / `TABLE` | table | Yes | — | Data to preprocess. Column names must match the inputs of the model's `TRANSFORM` clause; types must be coercion-compatible. |

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| (transform output) | varies | Exactly the columns produced by the model's `TRANSFORM` clause (scaled numerics, encoded categoricals, etc.). Label/passthrough columns named in `TRANSFORM` are returned as-is. |

**Best practices:**
- Pair with a `TRANSFORM_ONLY` model to centralize and version preprocessing once, then feed `ML.TRANSFORM(...)` output into multiple downstream model trainings / predictions.
- Pull required input column names/types from the model metadata (feature columns) before calling.

**Limitations:**
- Fails if the model has no `TRANSFORM` clause.
- Input column names must match the `TRANSFORM` clause inputs.

**BigFrames API:** Transform reuse is handled implicitly by pipeline/estimator objects; no standalone one-to-one `ML.TRANSFORM` call needed in typical BigFrames pipelines.

**Repo example (tested):** `data+ai/bq-ml/models/logistic_regression/logistic_regression.sql` (Example 9) — `CREATE MODEL ... TRANSFORM(ML.STANDARD_SCALER(age) OVER() AS age, ...)`; the scaler is saved with the model and reapplied automatically at predict time (the SQL comments note no need to repeat it in `ML.PREDICT`).


## Model-Free Functions

`ML.*` functions that transform data directly — no model required. Used standalone or inside a `TRANSFORM` clause. Reference: [Manual preprocessing](https://cloud.google.com/bigquery/docs/manual-preprocessing).


---

### Numerical scalers: `ML.STANDARD_SCALER`, `ML.MIN_MAX_SCALER`, `ML.MAX_ABS_SCALER`, `ML.ROBUST_SCALER`, `ML.NORMALIZER`

- **Description:** Manual feature-preprocessing functions that rescale numerical inputs into ML-ready features. The first four are **analytic** functions that compute column statistics across all rows and therefore require an empty `OVER()` clause; `ML.NORMALIZER` is a row-wise **scalar** function that normalizes each numerical ARRAY independently (no `OVER()`). All five can be used standalone in SQL or inside the `TRANSFORM` clause of `CREATE MODEL`, where the learned statistics are stored with the model and re-applied automatically at `ML.PREDICT` (no training/serving skew).
- **Use cases:**
  - Put numerical features on a common scale for distance/gradient-based models (`KMEANS`, `LINEAR_REG`/`LOGISTIC_REG`, `DNN_*`, `PCA`).
  - `ML.ROBUST_SCALER` for columns with outliers (centers on median, scales by IQR).
  - `ML.MAX_ABS_SCALER` to preserve sparsity / sign (no centering).
  - `ML.NORMALIZER` to give each row's feature vector unit norm (e.g. text/embedding-like vectors).
- **documentation:** [Manual feature preprocessing](https://cloud.google.com/bigquery/docs/manual-preprocessing) · [STANDARD_SCALER](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-standard-scaler) · [MIN_MAX_SCALER](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-min-max-scaler) · [MAX_ABS_SCALER](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-max-abs-scaler) · [ROBUST_SCALER](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-robust-scaler) · [NORMALIZER](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-normalizer)
- **Type:** Analytic (STANDARD / MIN_MAX / MAX_ABS / ROBUST) · Scalar (NORMALIZER).
- **Status:** GA.
- **Applies to models:** Any model type that supports manual preprocessing; used as raw SQL or in a `TRANSFORM` clause. Exportable with the model's transform when used in `TRANSFORM` (the scaler transforms accompany exported models / Vertex AI Model Registry).

**Transformation reference:**

| Function | Output range | Formula (per value `x`) | Centers data? | Notes |
|----------|--------------|--------------------------|---------------|-------|
| `ML.STANDARD_SCALER` | unbounded (~mean 0, std 1) | `(x - AVG(x)) / STDDEV(x)` (z-score) | Yes (mean) | Stores AVG/STDDEV for `ML.PREDICT`. |
| `ML.MIN_MAX_SCALER` | `[0, 1]` | `(x - MIN) / (MAX - MIN)` | No | Caps prediction inputs to 0 or 1 when outside the training range. |
| `ML.MAX_ABS_SCALER` | `[-1, 1]` | `x / MAX(ABS(x))` | No | Preserves sign and sparsity; no shift. |
| `ML.ROBUST_SCALER` | unbounded | `(x - median) / (q_hi - q_lo)` | Optional (median) | Outlier-robust; quantile range default `[25, 75]`. |
| `ML.NORMALIZER` | unit-norm vector | `x_i / \|\|vector\|\|_p` | No | Row-wise on an ARRAY; default p=2. |

**Syntax:**
```sql
-- Analytic scalers (require empty OVER())
ML.STANDARD_SCALER(numerical_expression) OVER()
ML.MIN_MAX_SCALER(numerical_expression)  OVER()
ML.MAX_ABS_SCALER(numerical_expression)  OVER()
ML.ROBUST_SCALER(numerical_expression [, quantile_range] [, with_median] [, with_quantile_range]) OVER()

-- Scalar normalizer (no OVER(); operates on an ARRAY per row)
ML.NORMALIZER(array_expression [, p])
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `numerical_expression` | numeric | Yes | — | The numeric column/expression to scale (scaler functions). |
| `quantile_range` | ARRAY\<INT64\> (2 elems) | No | `[25, 75]` | ROBUST only. Lower/upper percentile boundaries; min 0, max 100; 2nd \> 1st. |
| `with_median` | BOOL | No | `TRUE` | ROBUST only. Subtract the median before scaling. |
| `with_quantile_range` | BOOL | No | `TRUE` | ROBUST only. Divide by the quantile range. |
| `array_expression` | ARRAY\<numeric\> | Yes | — | NORMALIZER only. The numeric vector to give unit norm. |
| `p` | FLOAT64 | No | `2` | NORMALIZER only. p-norm; accepts `0`, `>= 1`, or `+inf` via `CAST('+inf' AS FLOAT64)`. |

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| (scaler result) | FLOAT64 | Scaled value of `numerical_expression`. |
| (normalizer result) | ARRAY\<FLOAT64\> | Input array rescaled to unit p-norm. |

**Best practices:**
- Prefer the `TRANSFORM` clause over preprocessing in the source query so the learned statistics travel with the model and are reapplied at prediction (avoids training/serving skew). Tested example in [`BQML Feature Engineering.ipynb`](../../03%20-%20BigQuery%20ML%20(BQML)/BQML%20Feature%20Engineering.ipynb) scales ~16 columns inside one `TRANSFORM` and aliases each (`... OVER() as scale_flourAmt`).
- Choose the scaler to match the data: `ROBUST` for outliers, `MAX_ABS` for sparse/sign-bearing data, `STANDARD` for roughly Gaussian features, `MIN_MAX` when a bounded `[0,1]` range is needed.
- Validate `ML.STANDARD_SCALER` equals `(x - AVG) / STDDEV` and `ML.NORMALIZER` against `np.linalg.norm` — both verified in the preprocessing-functions notebook.

**Limitations / gotchas:**
- The four analytic scalers MUST use an empty `OVER()`; omitting it errors. `ML.NORMALIZER` must NOT use `OVER()`.
- An analytic function cannot be an argument to another analytic function, but scalar functions (e.g. `ML.NORMALIZER`, `ML.IMPUTER` results) can be nested as arguments — see the compounding example in the preprocessing-functions notebook.
- `ML.NORMALIZER` normalizes across the elements of each row's ARRAY (row-wise), not down a column — semantically different from the column scalers.
- `ML.MIN_MAX_SCALER` caps prediction-time inputs to `[0, 1]` when they fall outside the training min/max.
- Imputation of NULLs is not done by scalers; pair with `ML.IMPUTER` (impute in the input query or earlier in the transform chain).

**BigFrames API:** `bigframes.ml.preprocessing.StandardScaler`, `MinMaxScaler`, `MaxAbsScaler` (and `compose.ColumnTransformer`); not every scaler has a 1:1 class — use SQL `TRANSFORM` for full parity.

**Repo examples (tested):**
- [`03 - BigQuery ML (BQML)/BQML Feature Engineering - preprocessing functions.ipynb`](../../03%20-%20BigQuery%20ML%20(BQML)/BQML%20Feature%20Engineering%20-%20preprocessing%20functions.ipynb) — standalone demos of all five with verified outputs (e.g. `ML.STANDARD_SCALER([0..10]) OVER()` matches manual z-score; `ML.ROBUST_SCALER` with `[25,75]`, `with_median`, `with_quantile_range` toggles; `ML.NORMALIZER` p ∈ {0, 1, 2, +inf}).
- [`03 - BigQuery ML (BQML)/BQML Feature Engineering.ipynb`](../../03%20-%20BigQuery%20ML%20(BQML)/BQML%20Feature%20Engineering.ipynb) — all four scalers inside a `TRANSFORM` of `LINEAR_REG` and `BOOSTED_TREE_REGRESSOR` models (registered to Vertex AI Model Registry).
- [`03 - BigQuery ML (BQML)/BQML Feature Engineering - reusable and modular.ipynb`](../../03%20-%20BigQuery%20ML%20(BQML)/BQML%20Feature%20Engineering%20-%20reusable%20and%20modular.ipynb) — `ML.ROBUST_SCALER` (outlier column) + `ML.STANDARD_SCALER` (other numerics) embedded in a `TRANSFORM` with `ML.IMPUTER` done in the input query.


---

### `ML.BUCKETIZE`
- **Description:** Bucketizes a continuous numerical value into a string-named bucket using a manually supplied array of split points (bin boundaries).
- **Use cases:**
  - Convert a numeric column (age, price) into categorical bins for linear/logistic models.
  - Encode domain knowledge as explicit boundaries (e.g. age brackets).
  - Inside `TRANSFORM` so the same boundaries are reapplied at `ML.PREDICT`.
- **documentation:** [ML.BUCKETIZE](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-bucketize)
- **Type:** Scalar (operates row-by-row; no `OVER()`).
- **Applies to models:** Any model type that supports manual feature preprocessing (linear/logistic regression, boosted trees, DNN, k-means, etc.) when used in `TRANSFORM`; also usable in plain SQL.

**Syntax:**
```sql
ML.BUCKETIZE(numerical_expression, array_split_points[, exclude_boundaries[, output_format]])
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `numerical_expression` | NUMERIC/FLOAT64 | Yes | — | The numerical value to bucketize. |
| `array_split_points` | ARRAY\<numeric\> | Yes | — | Sorted points at which to split into buckets. |
| `exclude_boundaries` | BOOL | No | `FALSE` | If `TRUE`, drops the implicit lower (`-inf`) and upper (`+inf`) overflow buckets so only interior bins remain. |
| `output_format` | STRING | No | `"bucket_names"` | `"bucket_names"` → `bin_<i>` (index starts at 1); `"bucket_ranges"` → `[lower, upper)`; `"bucket_ranges_json"` → `{"start":"..","end":".."}`. |

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| (scalar result) | STRING | Bucket label, e.g. `bin_3` or `[2, 3)` depending on `output_format`. |

**Best practices:**
- Generate boundaries dynamically with `GENERATE_ARRAY(start, end, step)` for evenly spaced bins.
- Place inside `TRANSFORM` so the bin definition travels with the model to serving/export.
- Use `exclude_boundaries = TRUE` to suppress overflow buckets when out-of-range values are not expected.

**Limitations:**
- Split points must be numeric and sorted; behavior with NULL `numerical_expression` returns NULL.
- Boundaries are fixed (no data-driven balancing) — for equal-frequency bins use `ML.QUANTILE_BUCKETIZE`.

**BigFrames API:** `bigframes.ml.preprocessing.KBinsDiscretizer` (strategy-dependent; not a 1:1 of explicit split points).
**Repo example (tested):** `/home/user/git/vertex-ai-mlops/03 - BigQuery ML (BQML)/BQML Feature Engineering - preprocessing functions.ipynb` — `ML.BUCKETIZE(input_column, [2, 5, 7])` and with `exclude_boundaries = TRUE`. Also `/home/user/git/vertex-ai-mlops/03 - BigQuery ML (BQML)/BQML Feature Engineering.ipynb`.

---

### `ML.QUANTILE_BUCKETIZE`
- **Description:** Bucketizes a continuous numerical value into `num_buckets` buckets of approximately equal frequency, with boundaries computed from quantiles across all rows.
- **Use cases:**
  - Equal-frequency binning of skewed numeric features without choosing boundaries by hand.
  - Inside `TRANSFORM` — the training-time quantiles are stored and reapplied at prediction.
- **documentation:** [ML.QUANTILE_BUCKETIZE](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-quantile-bucketize)
- **Type:** Analytic (requires an empty `OVER()` clause; computes statistics over all rows).
- **Applies to models:** Any model type supporting manual feature preprocessing when used in `TRANSFORM`; also usable in plain SQL with `OVER()`.

**Syntax:**
```sql
ML.QUANTILE_BUCKETIZE(numerical_expression, num_buckets[, output_format]) OVER()
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `numerical_expression` | NUMERIC/FLOAT64 | Yes | — | The numerical value to bucketize. |
| `num_buckets` | INT64 | Yes | — | Number of quantile buckets to split into. |
| `output_format` | STRING | No | `"bucket_names"` | `"bucket_names"` → `bin_<i>` (index starts at 1); `"bucket_ranges"` → interval notation, e.g. `(-inf, 2.5)`, `[2.5, 4.6)`, `[4.6, +inf)`; `"bucket_ranges_json"` → JSON, e.g. `{"start":"2.5","end":"4.6"}`. |

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| (analytic result) | STRING | Quantile bucket label for the row. |

**Best practices:**
- ALWAYS use an empty `OVER()` clause — this is required for ML analytic functions and ensures statistics are collected over the whole column.
- Prefer over `ML.BUCKETIZE` when you want balanced bin populations rather than fixed cut points.

**Limitations:**
- Must use `OVER()` (empty); other window framing is not supported.
- Quantile estimates are approximate on very large inputs.

**BigFrames API:** `bigframes.ml.preprocessing.KBinsDiscretizer(strategy="quantile")`.
**Repo example (tested):** `/home/user/git/vertex-ai-mlops/03 - BigQuery ML (BQML)/BQML Feature Engineering - preprocessing functions.ipynb` — `ML.QUANTILE_BUCKETIZE(input_column, 2) OVER() AS feature_column`. Also in `BQML Feature Engineering.ipynb`.

---

### `ML.HASH_BUCKETIZE`
- **Description:** Deterministically hashes a string and bucketizes it by taking the hash modulo `hash_bucket_size`, producing an INT64 bucket id. With `hash_bucket_size = 0` it hashes without bucketizing.
- **Use cases:**
  - Hash high-cardinality categorical/string features into a fixed number of buckets (the hashing trick).
  - Stable, deterministic feature encoding that needs no vocabulary fitting.
- **documentation:** [ML.HASH_BUCKETIZE](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-hash-bucketize)
- **Type:** Scalar (row-by-row; no `OVER()`).
- **Applies to models:** Any model type supporting manual feature preprocessing when used in `TRANSFORM`; also usable in plain SQL.

**Syntax:**
```sql
ML.HASH_BUCKETIZE(string_expression, hash_bucket_size)
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `string_expression` | STRING | Yes | — | The categorical string value to hash/bucketize. |
| `hash_bucket_size` | INT64 | Yes | — | Number of buckets (must be `>= 0`). If `0`, the value is hashed without taking the modulo (no bucketizing). |

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| (scalar result) | INT64 | Bucket id = `hash(string) mod hash_bucket_size`, or the raw hash when `hash_bucket_size = 0`. |

**Best practices:**
- Choose `hash_bucket_size` large enough to limit collisions for high-cardinality columns.
- Use inside `TRANSFORM` so the same hashing is applied automatically at serving.

**Limitations:**
- Hash collisions are unavoidable when distinct values exceed `hash_bucket_size`.
- Returns INT64 (unlike `ML.BUCKETIZE`/`ML.QUANTILE_BUCKETIZE` which return STRING bin labels); operates on strings, not numerics.

**BigFrames API:** No direct equivalent.
**Repo example (tested):** `/home/user/git/vertex-ai-mlops/03 - BigQuery ML (BQML)/BQML Feature Engineering - preprocessing functions.ipynb` — `ML.HASH_BUCKETIZE(input_column, 0)` (hash only) and `ML.HASH_BUCKETIZE(input_column, 3)`. Also in `BQML Feature Engineering.ipynb`.

---

**Family note:** All three are exportable feature-preprocessing functions when used in the `TRANSFORM` clause, so the transformation is reapplied automatically during `ML.PREDICT` and accompanies exported / Vertex-registered models. `ML.BUCKETIZE` and `ML.HASH_BUCKETIZE` are scalar; `ML.QUANTILE_BUCKETIZE` is analytic and requires an empty `OVER()` clause. See the [Manual feature preprocessing](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-preprocessing-functions) reference.


---

### `ML.ONE_HOT_ENCODER` / `ML.MULTI_HOT_ENCODER` / `ML.LABEL_ENCODER`

- **Description:** Categorical-encoding preprocessing functions. `ML.ONE_HOT_ENCODER` encodes a scalar `STRING` into a one-hot (or, with `drop`, dummy) sparse vector. `ML.MULTI_HOT_ENCODER` encodes an `ARRAY<STRING>` into a multi-hot sparse vector (one feature per unique element, useful for bag/tag columns). `ML.LABEL_ENCODER` maps a scalar `STRING` to an ordinal `INT64` in `[0, n]`. All three are **analytic (window) functions** — they require an `OVER()` clause to compute the vocabulary across the partition.
- **Use cases:**
  - One-hot encode nominal categoricals for linear/logistic/boosted-tree models that don't auto-encode the way you want.
  - Multi-hot encode array columns (tags, skus, multi-select fields) where a row has many categories.
  - Label-encode high-cardinality categoricals into a single compact integer column (ordinal — only appropriate where order is meaningful or for tree models).
  - Cap vocabulary explosion with `top_k` / `frequency_threshold`; the same fitted vocabulary is reused at prediction time when called inside `TRANSFORM`.
- **documentation:** [ML.ONE_HOT_ENCODER](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-one-hot-encoder) · [ML.MULTI_HOT_ENCODER](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-multi-hot-encoder) · [ML.LABEL_ENCODER](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-label-encoder) · [Preprocessing functions overview](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-preprocessing-functions)
- **Type:** Analytic (window) scalar functions — must be used with `OVER()`. Not table-valued; not aggregate.
- **Applies to models:** Any model type that supports **manual preprocessing**, used either as a standalone query transform or inside the `TRANSFORM` clause of `CREATE MODEL`. (When used in `TRANSFORM`, the fitted vocabulary + `top_k`/`frequency_threshold`/`drop` choices are stored with the model and auto-applied during `ML.PREDICT`/`ML.EVALUATE`.) Exportable with the model via [TRANSFORM-function export](https://cloud.google.com/bigquery/docs/exporting-models#export-transform-functions). No connection required.
- **Status:** GA.

**Syntax:**
```sql
-- scalar STRING -> one-hot / dummy sparse vector
ML.ONE_HOT_ENCODER(string_expression [, drop] [, top_k] [, frequency_threshold]) OVER()

-- ARRAY<STRING> -> multi-hot sparse vector
ML.MULTI_HOT_ENCODER(array_expression [, top_k] [, frequency_threshold]) OVER()

-- scalar STRING -> ordinal INT64
ML.LABEL_ENCODER(string_expression [, top_k] [, frequency_threshold]) OVER()
```

**Inputs:**

| Parameter | Type | Required | Default | Applies to | Description |
|-----------|------|----------|---------|------------|-------------|
| `string_expression` | STRING | Yes | — | ONE_HOT, LABEL | Scalar categorical value to encode. |
| `array_expression` | ARRAY\<STRING\> | Yes | — | MULTI_HOT | Array of categorical values to multi-hot encode. |
| `drop` | STRING | No | `'none'` | ONE_HOT only | `'none'` retains all categories; `'most_frequent'` drops the most frequent category (dummy encoding). |
| `top_k` | INT64 | No | `32000` | all three | Keep only the `top_k` most frequent categories; rarer categories encode to 0. Must be \< 1,000,000. |
| `frequency_threshold` | INT64 | No | `5` | all three | Keep only categories with frequency \>= threshold; rarer categories encode to 0. |

**Outputs:**

| Function | Output column type | Description |
|----------|--------------------|-------------|
| `ML.ONE_HOT_ENCODER` | ARRAY\<STRUCT\<index INT64, value DOUBLE\>\> | Sparse one-hot vector; vocabulary sorted alphabetically. NULL / out-of-vocab / dropped category -> `index 0`. |
| `ML.MULTI_HOT_ENCODER` | ARRAY\<STRUCT\<index INT64, value DOUBLE\>\> | Sparse multi-hot vector across unique array elements. NULL / out-of-vocab -> `index 0`. |
| `ML.LABEL_ENCODER` | INT64 | Ordinal code in `[0, n]`, vocabulary sorted alphabetically. NULL / out-of-vocab / excluded -> `0`. |

**Best practices:**
- Use inside `TRANSFORM` so the vocabulary fit at train time is automatically reapplied at prediction — avoids train/serve skew and manual re-encoding.
- Use `top_k` and `frequency_threshold` together to bound dimensionality on high-cardinality columns; both push trimmed categories to bucket `0` (shared with NULL/unseen).
- Prefer `ML.ONE_HOT_ENCODER` for nominal features fed to linear/logistic models; `ML.LABEL_ENCODER` only where an ordinal integer is acceptable (e.g., tree models) since it imposes an arbitrary alphabetical order.
- Reserve `ML.MULTI_HOT_ENCODER` for genuine array/multi-value columns rather than splitting a string yourself.

**Limitations:**
- All three are window functions: an `OVER()` clause is mandatory; omitting it is a syntax error.
- `top_k` must be less than 1,000,000 to avoid high-dimensionality issues.
- Bucket `0` is overloaded (NULL + below-`top_k` + below-`frequency_threshold` + unseen-at-predict), so you cannot distinguish those cases downstream.
- `drop` is unique to `ML.ONE_HOT_ENCODER`; `ML.LABEL_ENCODER` and `ML.MULTI_HOT_ENCODER` have no `drop` argument.
- Note: older repo notebooks cite default `top_k = 1,000,000` / `frequency_threshold = 0`; current docs specify `top_k = 32,000` / `frequency_threshold = 5`.

**BigFrames API:** `bigframes.ml.preprocessing.OneHotEncoder`, `bigframes.ml.preprocessing.LabelEncoder` (and the broader `bigframes.ml.preprocessing` module); these compile to the corresponding `ML.*` encoders.

**Repo example (tested):**
- `03 - BigQuery ML (BQML)/BQML Feature Engineering - preprocessing functions.ipynb` — standalone examples of all three over `UNNEST([...])` literals, e.g. `ML.LABEL_ENCODER(input_column, 3, 3) OVER()`, `ML.MULTI_HOT_ENCODER(input_column, 1, 2) OVER()`, and `ML.ONE_HOT_ENCODER(input_column, 'most_frequent', 3, 3) OVER()`.
- `03 - BigQuery ML (BQML)/BQML Feature Engineering.ipynb` — `ML.ONE_HOT_ENCODER` and `ML.LABEL_ENCODER` worked examples with `top_k`/`frequency_threshold` positional args.


---

### Feature engineering: standalone preprocessing functions

These are **manual feature preprocessing** functions. They can be used two ways:
1. **Inline in a query / standalone** — plain SQL to shape data before `CREATE MODEL` (the model then does *automatic* preprocessing on the result).
2. **Inside the `TRANSFORM` clause** of `CREATE MODEL` — the computed statistics are stored with the model and **re-applied automatically at serving** by `ML.PREDICT` / `ML.TRANSFORM`, and travel with [exported models](https://cloud.google.com/bigquery/docs/exporting-models) and Vertex AI Model Registry registrations. This is the recommended way to prevent training-serving skew.

> **Analytic vs scalar.** Functions that compute statistics across *all* rows (mean, median, mode, min/max, quantiles, stddev) are **analytic** and require an empty `OVER()` clause. Functions that operate row-by-row (e.g. `ML.FEATURE_CROSS`, `ML.POLYNOMIAL_EXPAND`, `ML.BUCKETIZE`) are **scalar** and take no `OVER()`. An analytic function cannot be nested as the argument of another analytic function, but a scalar/analytic result can be wrapped by a scalar function.

> **Note on `ML.TRANSPOSE`:** there is **no `ML.TRANSPOSE` function** in BigQuery ML. The repo notebook "BQML Feature Engineering - Create Model With Transpose" refers to the inline `TRANSFORM` clause technique (transposing preprocessing *into* the model), not a function. See the `TRANSFORM` clause pointer at the end of this section. The full catalog of manual preprocessing functions (encoders, scalers, bucketizers, text/image functions) lives in the **Manual preprocessing** reference: <https://cloud.google.com/bigquery/docs/manual-preprocessing>.

---

### `ML.IMPUTER`
- **Description:** Replaces `NULL` values in a numerical or categorical (string) expression with a computed statistic.
- **Use cases:**
  - Fill missing numeric values with `mean` or `median`.
  - Fill missing categorical values with `most_frequent` (mode).
  - Stable imputation at serving — the train-time statistic is reused.
- **documentation:** <https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-imputer>
- **Type:** Analytic (requires empty `OVER()`).
- **Category:** General manual preprocessing.
- **Applies to models:** Any model type, via `TRANSFORM` or pre-query. **Exportable** in `TRANSFORM`.

**Syntax:**
```sql
ML.IMPUTER(expression, strategy) OVER()
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `expression` | `INT64`/`FLOAT64` or `STRING` | Yes | — | Numerical or categorical column to impute. |
| `strategy` | `STRING` | Yes | — | `'mean'` or `'median'` (numerical only), or `'most_frequent'` (numerical or string). |

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| (result) | `FLOAT64` (numeric) or `STRING` (categorical) | Original value, or the imputed statistic where input was `NULL`. |

**Best practices:** Choose `median` for skewed numeric data; `most_frequent` is the only valid strategy for strings. Use inside `TRANSFORM` so prediction reuses training statistics.
**Limitations:** `mean`/`median` reject string inputs. Requires `OVER()` (empty window).
**BigFrames API:** `bigframes.ml.impute.SimpleImputer`.
**Repo example (tested):** `/home/user/git/vertex-ai-mlops/03 - BigQuery ML (BQML)/BQML Feature Engineering - preprocessing functions.ipynb` — imputes a numeric column three ways and a string column by mode:
```sql
SELECT
  num_column,
  ML.IMPUTER(num_column, 'mean')   OVER() AS num_imputed_mean,
  ML.IMPUTER(num_column, 'median') OVER() AS num_imputed_median,
  ML.IMPUTER(num_column, 'most_frequent') OVER() AS num_imputed_mode,
  ML.IMPUTER(string_column, 'most_frequent') OVER() AS string_imputed_mode
FROM UNNEST([1,1,2,3,4,5,NULL]) AS num_column WITH OFFSET p1,
     UNNEST(['a','a','b','c','d','e',NULL]) AS string_column WITH OFFSET p2
WHERE p1 = p2;
```

---

### `ML.FEATURE_CROSS`
- **Description:** Given a `STRUCT` of categorical (string) features, returns a `STRUCT` of all feature-cross combinations up to `degree`. Each output field is the concatenated source values (e.g. `'a_A'`), useful as interaction features.
- **Use cases:**
  - Capture interactions between categorical columns (e.g. `region` × `device`).
  - Generate crosses for linear / logistic models that don't learn interactions natively.
- **documentation:** <https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-feature-cross>
- **Type:** Scalar (no `OVER()`).
- **Category:** Categorical manual preprocessing.
- **Applies to models:** Any model type. **Not exportable** in `TRANSFORM` (cannot accompany an exported / Vertex-registered model).

**Syntax:**
```sql
ML.FEATURE_CROSS(struct_categorical_features [, degree])
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `struct_categorical_features` | `STRUCT` of `STRING` | Yes | — | Named categorical columns to cross (use `STRUCT(col1, col2, ...)`). |
| `degree` | `INT64` | No | `2` | Highest combination degree; range `[2, 4]`. |

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| (result) | `STRUCT<STRING>` | One field per crossed combination, named `\<col_a\>_\<col_b\>`, valued `\<val_a\>_\<val_b\>`. |

**Best practices:** Keep `degree` low (2) — combinations grow combinatorially and can explode cardinality. Pre-bucketize numeric columns to strings before crossing.
**Limitations:** Categorical (string) inputs only; `degree` capped at 4. **Not exportable** in `TRANSFORM`, so a model that needs portability/serving outside BQ must compute crosses in the input query instead.
**BigFrames API:** No direct equivalent (build via DataFrame ops).
**Repo example (tested):** `/home/user/git/vertex-ai-mlops/03 - BigQuery ML (BQML)/BQML Feature Engineering - preprocessing functions.ipynb`:
```sql
SELECT
  input_column_1, input_column_2, input_column_3,
  ML.FEATURE_CROSS(STRUCT(input_column_1, input_column_2, input_column_3)) AS feature_column
FROM UNNEST(['a','b','c']) AS input_column_1 WITH OFFSET p1,
     UNNEST(['A','B','C']) AS input_column_2 WITH OFFSET p2,
     UNNEST(['1','2','3']) AS input_column_3 WITH OFFSET p3
WHERE p1 = p2 AND p2 = p3;
-- e.g. {'input_column_1_input_column_2':'c_C','input_column_1_input_column_3':'c_3','input_column_2_input_column_3':'C_3'}
```

---

### `ML.POLYNOMIAL_EXPAND`
- **Description:** Given a `STRUCT` of numerical features, returns a `STRUCT` of all polynomial combinations (including the originals) up to `degree`. Field names concatenate the source feature names (e.g. `x1`, `x1_x1`, `x1_x2`, `x2`, `x2_x2`).
- **Use cases:**
  - Add squared/cubic and interaction terms so linear models can fit curvature.
  - Quick polynomial feature generation without manual `col*col` expressions.
- **documentation:** <https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-polynomial-expand>
- **Type:** Scalar (no `OVER()`).
- **Category:** Numerical manual preprocessing.
- **Applies to models:** Any model type. **Not exportable** in `TRANSFORM`.

**Syntax:**
```sql
ML.POLYNOMIAL_EXPAND(struct_numerical_features [, degree])
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `struct_numerical_features` | `STRUCT` of numeric | Yes | — | Named numeric features (`STRUCT(col1, col2, ...)`); **≤ 10** features, no duplicates, all named. |
| `degree` | `INT64` | No | `2` | Highest combination degree; range `[1, 4]`. |

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| (result) | `STRUCT<FLOAT64>` | All polynomial combinations up to `degree`, including the original terms. |

**Best practices:** Combine with `ML.IMPUTER`/scaling first; wrap an imputed (analytic) column inside the `STRUCT` since `ML.POLYNOMIAL_EXPAND` is scalar and can take an analytic argument.
**Limitations:** ≤ 10 input features, no unnamed/duplicate features; `degree` ≤ 4. **Not exportable** in `TRANSFORM`.
**BigFrames API:** `bigframes.ml.preprocessing.PolynomialFeatures`.
**Repo example (tested):** `/home/user/git/vertex-ai-mlops/03 - BigQuery ML (BQML)/BQML Feature Engineering - preprocessing functions.ipynb` — also shows the **compounded** pattern (impute → expand):
```sql
SELECT
  input_column,
  ML.POLYNOMIAL_EXPAND(
    STRUCT(ML.IMPUTER(CAST(input_column AS FLOAT64), 'mean') OVER() AS num_imputed_mean),
    2
  ) AS imputed_expanded
FROM UNNEST(['1','1','2','3','4','5',NULL]) AS input_column;
-- e.g. {'num_imputed_mean':2.6667,'num_imputed_mean_num_imputed_mean':7.111}
```

---

### `ML.TRANSPOSE` — not a function (pointer)
`ML.TRANSPOSE` does not exist in BigQuery ML. To "transpose" preprocessing into the model so it serves automatically, use the **`TRANSFORM` clause** of `CREATE MODEL`:
- `TRANSFORM` clause reference: <https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create#transform>
- Feature engineering with `TRANSFORM`: <https://cloud.google.com/bigquery/docs/bigqueryml-transform>
- Inspect the preprocessed output of a model's `TRANSFORM` with `ML.TRANSFORM` (function): <https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-transform>

**Repo example (tested) — TRANSFORM in a real `CREATE MODEL`:** `/home/user/git/vertex-ai-mlops/03 - BigQuery ML (BQML)/BQML Feature Engineering - Create Model With Transpose.ipynb` trains a `BOOSTED_TREE_REGRESSOR` whose `TRANSFORM` mixes scalers, `ML.LABEL_ENCODER`, and `EXTRACT(...)` date parts; the model is registered to Vertex AI and exported (the export yields a `/model` plus a `/model/transform` saved model — i.e. preprocessing travels with the model):
```sql
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.MODEL_NAME`
TRANSFORM (
  JUDGE_A,
  ML.LABEL_ENCODER(contestant_id) OVER() AS contestant,
  EXTRACT(YEAR FROM airdate) AS year,
  EXTRACT(ISOWEEK FROM airdate) AS week,
  ML.MIN_MAX_SCALER(flourAmt)   OVER() AS scale_flourAmt,
  ML.ROBUST_SCALER(saltAmt)     OVER() AS scale_saltAmt,
  ML.STANDARD_SCALER(water1Amt) OVER() AS scale_water1Amt
)
OPTIONS (
  model_type = 'BOOSTED_TREE_REGRESSOR',
  input_label_cols = ['JUDGE_A'],
  enable_global_explain = TRUE,
  MODEL_REGISTRY = 'VERTEX_AI'
) AS
SELECT * FROM `PROJECT_ID.DATASET.bread`;
```


---

### Text preprocessing functions: `ML.NGRAMS`, `ML.TF_IDF`, `ML.BAG_OF_WORDS`

These three model-free functions turn tokenized text (an `ARRAY<STRING>` of tokens) into ML
features. They are part of BigQuery ML [manual preprocessing](https://cloud.google.com/bigquery/docs/manual-preprocessing)
and can be used standalone in SQL or inside the [`TRANSFORM`](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create#transform)
clause of `CREATE MODEL` (so they re-apply automatically at `ML.PREDICT` time). They all operate
on pre-tokenized input — produce tokens first with GoogleSQL text functions such as
[`ML.BAG_OF_WORDS` upstream tokenizers](https://cloud.google.com/bigquery/docs/reference/standard-sql/text-analysis-functions)
(e.g. `BAG_OF_WORDS`, `TEXT_ANALYZE`) or simple `SPLIT(...)`.

> NUANCE: BigQuery also has same-named **text-analysis** functions (`TF_IDF`, `BAG_OF_WORDS`) under
> GoogleSQL — those return term strings as the dictionary index and order by frequency. The `ML.*`
> versions documented here return integer dictionary indices, order the dictionary alphabetically,
> and reserve index `0` for the unknown term. Use the `ML.*` versions for feature engineering / `TRANSFORM`.

---

### `ML.NGRAMS`
- **Description:** Given an array of token strings, returns an array of concatenated n-grams for the requested size range.
- **Use cases:**
  - Build word/character n-gram features from tokenized text before bag-of-words or TF-IDF.
  - Capture local token order (bigrams, trigrams) that single tokens lose.
- **documentation:** https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ngrams
- **Type:** Scalar (row-wise — no `OVER()` needed; operates within a single array).
- **Applies to models:** Any model type, via `TRANSFORM` or pre-computed input columns. Exportable in `TRANSFORM`.

**Syntax:**
```sql
ML.NGRAMS(array_input, range [, separator])
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `array_input` | `ARRAY<STRING>` | Yes | — | Tokens to merge into n-grams. |
| `range` | `ARRAY<INT64>` | Yes | — | `[min, max]` n-gram sizes. A single int `x` means `[x, x]`. |
| `separator` | `STRING` | No | `' '` (space) | Joins adjacent tokens in each output n-gram. |

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| (result) | `ARRAY<STRING>` | All n-grams within `range`, each a `separator`-joined string. |

**Best practices:** Keep `range` tight (e.g. `[1, 2]`) — wide ranges explode feature cardinality. Tokenize and lowercase upstream for consistency.
**Limitations:** Scalar over one array per row; does not aggregate across rows. Order is preserved from the input array.
**BigFrames API:** No direct equivalent (use SQL / `bigframes.bigquery` passthrough).
**Repo example (tested):** `03 - BigQuery ML (BQML)/BQML Feature Engineering - preprocessing functions.ipynb` (cell `ML.NGRAMS`) and `03 - BigQuery ML (BQML)/BQML Feature Engineering.ipynb` — `ML.NGRAMS(input_column, [2, 4])` on `['a','b','c','d']` returns `[a b, a b c, a b c d, b c, b c d, c d]`.

---

### `ML.TF_IDF`
- **Description:** Computes term frequency–inverse document frequency relevance scores for terms across a set of tokenized documents.
- **Use cases:**
  - Weight terms by importance (frequent-in-doc but rare-across-corpus) for sparse text features.
  - Feed sparse TF-IDF vectors to linear / logistic regression (`LINEAR_REG`, `LOGISTIC_REG`) for text classification.
- **documentation:** https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-tf-idf
- **Type:** Analytic — **requires `OVER ()`** (IDF is computed across the whole window of documents).
- **Applies to models:** Any model type via `TRANSFORM` or precomputed columns.

**Syntax:**
```sql
ML.TF_IDF(tokenized_document [, top_k] [, frequency_threshold]) OVER ()
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `tokenized_document` | `ARRAY<STRING>` | Yes | — | One document's tokens. |
| `top_k` | `INT64` | No | 32000 (max 1048576) | Dictionary size excluding the unknown term; keeps the `top_k` terms appearing in the most documents. |
| `frequency_threshold` | `INT64` | No | 5 | Minimum number of documents a term must appear in to enter the dictionary. |

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| (result) | `ARRAY<STRUCT<index INT64, value FLOAT64>>` | TF-IDF score per dictionary term for the document. `index 0` = unknown term (tokens not in dictionary); remaining indices map to the dictionary ordered alphabetically. |

**Best practices:** Same `top_k` / `frequency_threshold` across train and serve (use inside `TRANSFORM` so the dictionary is fixed in the model). Drop rare/noise terms via `frequency_threshold`.
**Limitations:** Must use empty `OVER ()`; the dictionary is built over the analytic window, so apply over the full training corpus. Index `0` always reserved for unknown.
**BigFrames API:** No direct equivalent.
**Repo example (tested):** Not yet demonstrated in repo notebooks (the preprocessing notebook covers `ML.NGRAMS` but not `ML.TF_IDF`). Doc example: `ML.TF_IDF(f, 3, 1) OVER ()` over four short documents returns per-doc arrays of `{index, value}` scores.

---

### `ML.BAG_OF_WORDS`
- **Description:** Computes a bag-of-words (per-document term-frequency) representation of tokenized documents.
- **Use cases:**
  - Produce sparse count features for text classification when raw frequency (not IDF weighting) is wanted.
  - Quick baseline text features feeding `LOGISTIC_REG` / `BOOSTED_TREE_*`.
- **documentation:** https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-bag-of-words
- **Type:** Analytic — **requires `OVER ()`** (dictionary is built across the document window).
- **Applies to models:** Any model type via `TRANSFORM` or precomputed columns.

**Syntax:**
```sql
ML.BAG_OF_WORDS(tokenized_document [, top_k] [, frequency_threshold]) OVER ()
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `tokenized_document` | `ARRAY<STRING>` | Yes | — | One document's tokens. |
| `top_k` | `INT64` | No | 32000 (max 1048576) | Dictionary size excluding the unknown term; keeps the `top_k` terms appearing in the most documents. |
| `frequency_threshold` | `INT64` | No | 5 | Minimum number of documents a term must appear in to enter the dictionary. |

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| (result) | `ARRAY<STRUCT<index INT64, value INT64>>` | Per-document term counts. `index 0` = unknown term; remaining indices map to the alphabetically ordered dictionary; `value` is the count of that term in the document. |

**Best practices:** Use inside `TRANSFORM` so the dictionary is frozen with the model and re-applied at predict time. Combine with `ML.NGRAMS` upstream for n-gram bags. Use `top_k` to cap dimensionality.
**Limitations:** Empty `OVER ()` required; counts depend on the analytic window — apply over the full corpus. Index `0` reserved for unknown.
**BigFrames API:** No direct equivalent.
**Repo example (tested):** Not yet demonstrated in repo notebooks. Doc example: `ML.BAG_OF_WORDS(f, 2, 1) OVER ()` over two short token arrays returns per-doc `{index, value}` count arrays.

---

**Status:** All three are **GA**. **Connection required:** No.

**Typical pipeline:** tokenize (GoogleSQL `TEXT_ANALYZE`/`SPLIT`) → optional `ML.NGRAMS` → `ML.BAG_OF_WORDS`
or `ML.TF_IDF` (in `TRANSFORM`) → train classifier. Note: `ML.TF_IDF`/`ML.BAG_OF_WORDS` are analytic
(`OVER ()`) and an analytic function cannot be an argument of another analytic function — chain via
subqueries/CTEs, not nesting (consistent with the repo's note for `ML.STANDARD_SCALER` etc.).


---

### `ML.DISTANCE`
- **Description:** Model-free scalar function that computes the distance between two equal-length numeric vectors (`ARRAY<FLOAT64>` / `ARRAY<INT64>`). Supports Euclidean, Manhattan, and Cosine distance. No model is required.
- **Use cases:**
  - Nearest-neighbor / similarity scoring between embedding vectors (e.g., cosine similarity as `1 - ML.DISTANCE(..., 'COSINE')`).
  - Pairwise distance for lookalike, dedup, and recommendation candidate ranking.
  - Building custom clustering / KNN logic outside of a trained model.
  - Ad-hoc distance computation in `SELECT` without `ML.PREDICT`.
- **documentation:** https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-distance
- **Type:** Scalar.
- **Applies to models:** None — model-free utility (operates on raw vectors, not a model).

**Syntax:**
```sql
ML.DISTANCE(vector1, vector2 [, type])
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `vector1` | `ARRAY<FLOAT64>` or `ARRAY<INT64>` | Yes | — | First vector. Must be same length as `vector2`. |
| `vector2` | `ARRAY<FLOAT64>` or `ARRAY<INT64>` | Yes | — | Second vector. Must be same length as `vector1`. |
| `type` | `STRING` | No | `'EUCLIDEAN'` | Distance metric: `'EUCLIDEAN'`, `'MANHATTAN'`, or `'COSINE'`. |

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| (scalar) | `FLOAT64` | Distance between the two vectors. Returns `NULL` if either input vector is `NULL`. |

**Best practices:**
- For cosine *similarity*, compute `1 - ML.DISTANCE(v1, v2, 'COSINE')` (the function returns cosine *distance*).
- Pre-filter/limit candidate pairs before pairwise distance to control cost on large cross joins.
- `'EUCLIDEAN'` is applied when `type` is omitted — pass it explicitly for readability.

**Limitations:**
- Both vectors must be non-`NULL` and the same length; mismatched lengths error.
- Only the three metrics above are supported; other metrics (e.g., Jaccard) must be derived manually (see `ML.LP_NORM`).
- This is brute-force distance, not an index — for scalable ANN search use `VECTOR_SEARCH` / a vector index instead.

**BigFrames API:** No direct equivalent (use array math or `VECTOR_SEARCH`).

**Repo example (tested):** Not used in the bq-ml feature-engineering notebooks (`/home/user/git/vertex-ai-mlops/03 - BigQuery ML (BQML)/BQML Feature Engineering*.ipynb` cover preprocessing, not distance). Real tested usage of the cosine pattern lives in the sibling project: `/home/user/git/vertex-ai-mlops/data+ai/bq-ai-functions/functions/ai_embed/ai_embed.sql` (lines 67, 136) — `1 - ML.DISTANCE(a.vec, b.vec, 'COSINE') AS cosine_similarity`.

---

### `ML.LP_NORM`
- **Description:** Model-free scalar function that computes the Lp norm (vector magnitude) of a single numeric vector for a given `degree`. `degree = 1.0` gives the Manhattan (L1) norm; `degree = 2.0` gives the Euclidean (L2) norm.
- **Use cases:**
  - Vector normalization (divide a vector by its norm to get a unit vector).
  - Feature magnitude / regularization-style measures.
  - Deriving metrics not built into `ML.DISTANCE` — e.g., Jaccard on binary vectors via dot products and the L1 (Manhattan) norm.
- **documentation:** https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-lp-norm
- **Type:** Scalar.
- **Applies to models:** None — model-free utility.

**Syntax:**
```sql
ML.LP_NORM(vector, degree)
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `vector` | `ARRAY<FLOAT64>` or `ARRAY<INT64>` | Yes | — | Vector to compute the norm of. |
| `degree` | `FLOAT64` (or `INT64`) | Yes | — | The p in the Lp norm. `1.0` = Manhattan/L1, `2.0` = Euclidean/L2; any p ≥ 0 supported. |

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| (scalar) | `FLOAT64` | The Lp norm of the vector. Returns `NULL` if `vector` is `NULL`. |

**Best practices:**
- Use `degree = 2.0` for standard L2 normalization; `degree = 1.0` for L1.
- Combine with `ML.DISTANCE` only when you need a metric not directly supported (e.g., Jaccard).

**Limitations:**
- Operates on a single vector (a norm), not a pair — use `ML.DISTANCE` for pairwise distance.
- `degree` is required (no implicit default).
- Brute-force scalar computation; not an index.

**BigFrames API:** No direct equivalent.

**Repo example (tested):** Not present in the bq-ml feature-engineering notebooks or elsewhere in this repo (no `ML.LP_NORM` occurrences found). Documentation example pattern: `SELECT ML.LP_NORM([1.0, 2.0, 3.0], 2.0)`.


---

### Image preprocessing functions: `ML.DECODE_IMAGE`, `ML.RESIZE_IMAGE`, `ML.CONVERT_IMAGE_TYPE`, `ML.CONVERT_COLOR_SPACE`

These four model-free functions form the image-preprocessing pipeline in BigQuery ML
[manual preprocessing](https://cloud.google.com/bigquery/docs/manual-preprocessing). They turn
image bytes stored in an [object table](https://cloud.google.com/bigquery/docs/object-tables) into the
multi-dimensional numeric `STRUCT` representation that an imported/remote vision model expects. They can
be used directly inside `ML.PREDICT`, written to an intermediate table column, or placed inside the
[`TRANSFORM`](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create#transform)
clause of `CREATE MODEL` so the preprocessing re-applies automatically at prediction time.

> **Pipeline order:** `ML.DECODE_IMAGE` is always the entry point (bytes → image `STRUCT`). Its output
> feeds `ML.RESIZE_IMAGE`, `ML.CONVERT_IMAGE_TYPE`, and/or `ML.CONVERT_COLOR_SPACE` in any combination,
> e.g. `ML.CONVERT_COLOR_SPACE(ML.RESIZE_IMAGE(ML.DECODE_IMAGE(data), 224, 280, TRUE), 'YIQ')`.
> All four are **scalar, row-wise** functions — no `OVER()` clause (they operate on a single image per
> row, not on statistics across rows), so they nest freely inside one another and inside `TRANSFORM`.

> **Scope note:** These are BQML preprocessing primitives for *running a vision model on image bytes*
> (in-scope here). The foundation-model multimodal path — `ML.ANNOTATE_IMAGE`, multimodal
> `ML.GENERATE_TEXT`/`AI.GENERATE_*` over images — is owned by `../bq-ai-functions/`; cross-link there,
> do not duplicate.

> **Output-size gotcha (all four):** an image `STRUCT` can be large (decoded value must be `<= 60 MB`).
> Referencing these functions directly in the BigQuery editor can fail to display; write results to a
> table instead. Object-table image files must be `< 20 MB`, JPEG/PNG/BMP, and total `< 1 TB`.

---

### `ML.DECODE_IMAGE`
- **Description:** Converts image bytes (from an object table's `data` column) into a multi-dimensional `STRUCT` of shape + pixel values that downstream image functions and vision models consume. This is the required entry point of the image pipeline.
- **Use cases:**
  - Decode JPEG/PNG/BMP bytes from an object table before inference with an imported/remote vision model.
  - Produce a reusable decoded-image column to feed `ML.RESIZE_IMAGE` / `ML.CONVERT_*`.
- **documentation:** [ML.DECODE_IMAGE](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-decode-image) · [Run inference on image object tables](https://cloud.google.com/bigquery/docs/object-table-inference)
- **Type:** Scalar (row-wise; no `OVER()`).
- **Applies to models:** Imported/remote vision models via `ML.PREDICT`, or any model's `TRANSFORM` that takes image input. Operates on object-table image bytes, not on a trained BQML model.

**Syntax:**
```sql
ML.DECODE_IMAGE(image_bytes)
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `image_bytes` | BYTES | Yes | — | Image bytes, typically the `data` column of an object table over JPEG/PNG/BMP files. |

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| (result) | STRUCT\<ARRAY\<INT64\> shape, ARRAY\<FLOAT64\> values\> | Decoded image: a shape array (e.g. `[height, width, channels]`) plus flattened pixel values. Must be `<= 60 MB`. |

**Best practices:**
- When passing `ML.DECODE_IMAGE` output **directly** into `ML.PREDICT`, alias it with the model's expected input field name (e.g. `... AS input`).
- For repeated use, persist the decoded column to a table to avoid re-decoding.
**Limitations:**
- Output `STRUCT` must be `<= 60 MB`; large images can exceed editor display limits — write to a table.
- Only JPEG/PNG/BMP object-table files are supported.
**BigFrames API:** No direct equivalent (use SQL / object tables).
**Repo example (tested):** None — no `ML.DECODE_IMAGE` usage found in this repo's notebooks (the BQML Feature Engineering notebooks cover tabular/text preprocessing only). Doc pattern: `ML.DECODE_IMAGE(data)` over an object table's `data` column.

---

### `ML.RESIZE_IMAGE`
- **Description:** Resizes a decoded image to a target height/width, optionally preserving aspect ratio.
- **Use cases:**
  - Match the fixed input resolution a vision model was trained on (e.g. 224×224).
  - Downscale large images to bound the decoded `STRUCT` size.
- **documentation:** [ML.RESIZE_IMAGE](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-resize-image)
- **Type:** Scalar (row-wise; no `OVER()`).
- **Applies to models:** Same as the family — `ML.PREDICT` input or `TRANSFORM`; consumes `ML.DECODE_IMAGE` output.

**Syntax:**
```sql
ML.RESIZE_IMAGE(decoded_image, target_height, target_width, preserve_aspect_ratio)
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `decoded_image` | STRUCT (from `ML.DECODE_IMAGE`) | Yes | — | The decoded image to resize. |
| `target_height` | INT64 | Yes | — | Target height in pixels (max height if `preserve_aspect_ratio = TRUE`). |
| `target_width` | INT64 | Yes | — | Target width in pixels (max width if `preserve_aspect_ratio = TRUE`). |
| `preserve_aspect_ratio` | BOOL | Yes | — | If `TRUE`, returns the largest image within the height/width bounds that keeps the original aspect ratio. |

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| (result) | STRUCT (same form as input image) | The resized image. |

**Best practices:** Resize to the model's exact expected dimensions; use `preserve_aspect_ratio = TRUE` when distortion would hurt accuracy.
**Limitations:** Output-size/display gotcha as above; takes a decoded image (chain after `ML.DECODE_IMAGE`).
**BigFrames API:** No direct equivalent.
**Repo example (tested):** None — not used in this repo's notebooks. Doc pattern: `ML.RESIZE_IMAGE(ML.DECODE_IMAGE(data), 480, 480, FALSE) AS input`.

---

### `ML.CONVERT_IMAGE_TYPE`
- **Description:** Converts the floating-point pixel values produced by `ML.DECODE_IMAGE` into integers in the range `[0, 255)`, as required by some models.
- **Use cases:**
  - Feed integer-input vision models (e.g. SSD MobileNet V2, which expects `tf.uint8`).
- **documentation:** [ML.CONVERT_IMAGE_TYPE](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-convert-image-type)
- **Type:** Scalar (row-wise; no `OVER()`).
- **Applies to models:** Same as the family; consumes `ML.DECODE_IMAGE` (or other image-function) output.

**Syntax:**
```sql
ML.CONVERT_IMAGE_TYPE(decoded_image)
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `decoded_image` | STRUCT (from `ML.DECODE_IMAGE`) | Yes | — | Image whose float pixel values are converted to integers `[0, 255)`. |

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| (result) | STRUCT (same form, integer pixel values) | Image with integer pixel values. |

**Best practices:** Apply only when the target model requires integer pixels; leave float output for models trained on `[0,1]` floats.
**Limitations:** Output-size/display gotcha as above; integer range is `[0, 255)`.
**BigFrames API:** No direct equivalent.
**Repo example (tested):** None — not used in this repo's notebooks. Doc pattern: `ML.CONVERT_IMAGE_TYPE(ML.DECODE_IMAGE(data)) AS image`.

---

### `ML.CONVERT_COLOR_SPACE`
- **Description:** Converts an RGB image to a different color space.
- **Use cases:**
  - Match the color space a vision model was trained on (e.g. grayscale or YIQ input).
- **documentation:** [ML.CONVERT_COLOR_SPACE](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-convert-color-space)
- **Type:** Scalar (row-wise; no `OVER()`).
- **Applies to models:** Same as the family; consumes `ML.DECODE_IMAGE`/`ML.RESIZE_IMAGE` output (input must be RGB).

**Syntax:**
```sql
ML.CONVERT_COLOR_SPACE(rgb_image, target_color_space)
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `rgb_image` | STRUCT (RGB, from `ML.DECODE_IMAGE`/`ML.RESIZE_IMAGE`) | Yes | — | Image in RGB color space. |
| `target_color_space` | STRING | Yes | — | Target color space: `'HSV'`, `'YIQ'`, `'YUV'`, or `'GRAYSCALE'`. |

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| (result) | STRUCT (same form, converted color space) | Image in the requested color space. |

**Best practices:** Only convert when the model expects a non-RGB color space; input must be RGB.
**Limitations:** Source must be RGB; only `HSV` / `YIQ` / `YUV` / `GRAYSCALE` targets. Output-size/display gotcha as above.
**BigFrames API:** No direct equivalent.
**Repo example (tested):** None — not used in this repo's notebooks. Doc pattern: `ML.CONVERT_COLOR_SPACE(ML.RESIZE_IMAGE(ML.DECODE_IMAGE(data), 224, 280, TRUE), 'YIQ') AS input`.

---

**Status:** All four are **GA**. **Connection required:** No (the function itself; the object table over the image files and the vision model may require a connection — see the model entry).

**TRANSFORM-clause behavior:** All four are exportable preprocessing functions usable inside `TRANSFORM`, so the decode/resize/type/color-space steps are stored with the model and re-applied automatically at `ML.PREDICT`. Because they are scalar (no `OVER()`), they nest directly and impose no analytic-window constraints — unlike the analytic scalers/encoders/text functions documented in this folder.

**Typical pipeline:** object table (`data` BYTES) → `ML.DECODE_IMAGE` → optional `ML.RESIZE_IMAGE` → optional `ML.CONVERT_IMAGE_TYPE` / `ML.CONVERT_COLOR_SPACE` → vision model via `ML.PREDICT` (or all of it inside `TRANSFORM`).

**Sources:** [ML.DECODE_IMAGE](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-decode-image) · [ML.RESIZE_IMAGE](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-resize-image) · [ML.CONVERT_IMAGE_TYPE](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-convert-image-type) · [ML.CONVERT_COLOR_SPACE](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-convert-color-space) · [Run inference on image object tables](https://cloud.google.com/bigquery/docs/object-table-inference)


## Model Management & Monitoring



---

### `EXPORT MODEL`

- **Description:** Statement that copies a trained BigQuery ML model out of BigQuery into a Cloud Storage folder so it can be served outside of BigQuery (locally, in a container, or on Vertex AI Prediction / Agent Platform). The automatic preprocessing learned at training time (standardization, label/one-hot encoding, imputation, etc.) is baked into the exported artifact, so no manual preprocessing is needed before inference on the exported model.
- **Use cases:**
  - Serve a BQML-trained model outside BigQuery (custom container, edge, online endpoint).
  - Hand a model to a downstream team in a portable format (TensorFlow SavedModel or XGBoost Booster).
  - Promote a specific hyperparameter-tuning trial to production (via `TRIAL_ID`).
- **documentation:** [EXPORT MODEL statement](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-export-model) · [Exporting models](https://cloud.google.com/bigquery/docs/exporting-models)
- **Type:** DDL-style statement (model management). Equivalent CLI/API: `bq extract --model` / an extract job.
- **Applies to models:** Most natively-trained model types (see export-format table below). NOT remote models (`REMOTE WITH CONNECTION`), and ARIMA_PLUS / time-series, ONNX-imported, and TFLite-imported models are not exportable. Imported `TENSORFLOW` models export back the exact files that were imported.

**Syntax:**
```sql
EXPORT MODEL `PROJECT_ID.DATASET.MODEL_NAME`
OPTIONS (
  URI = 'gs://BUCKET/path/to/model',   -- destination folder; must match dataset location
  TRIAL_ID = 2                          -- optional; HP-tuning models only
);
```

CLI equivalents:
```bash
# TensorFlow SavedModel (default)
bq extract --model 'DATASET.MODEL_NAME' gs://BUCKET/model_folder
# XGBoost Booster
bq extract --model --destination_format ML_XGBOOST_BOOSTER 'DATASET.MODEL_NAME' gs://BUCKET/model_folder
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `MODEL_NAME` | identifier | Yes | — | Backtick-qualified model (`project.dataset.model`). |
| `URI` | STRING | Yes | — | Cloud Storage destination folder, `gs://bucket/folder`. Bucket must be in the same location as the dataset. |
| `TRIAL_ID` | INT64 | No | optimal trial | For HP-tuning models, the trial to export. If omitted, the optimal trial is exported. |
| `--destination_format` (CLI) | enum | No | `ML_TF_SAVED_MODEL` | `ML_TF_SAVED_MODEL` or `ML_XGBOOST_BOOSTER`. Not set in SQL — format is chosen by model type. |

**Outputs:** No result rows. Writes model artifact files to the `URI` folder in GCS. Export format by model type:

| Model type(s) | Export format |
|---|---|
| `LINEAR_REGRESSOR`, `LOGISTIC_REG`, `KMEANS`, `PCA`, `MATRIX_FACTORIZATION`, `AUTOENCODER`, `DNN_*`, `DNN_LINEAR_COMBINED_*`, `TRANSFORM_ONLY` | TensorFlow SavedModel (TF 1.15+) |
| `AUTOML_CLASSIFIER`, `AUTOML_REGRESSOR` | TensorFlow SavedModel (TF 2.1.0) |
| `BOOSTED_TREE_CLASSIFIER`, `BOOSTED_TREE_REGRESSOR`, `RANDOM_FOREST_CLASSIFIER`, `RANDOM_FOREST_REGRESSOR` | XGBoost Booster (XGBoost 0.82) |
| `TENSORFLOW` (imported) | TensorFlow SavedModel — the exact imported files |

> Note: ONNX is an **import**-only format (`CREATE MODEL ... model_type='ONNX'`), not an EXPORT MODEL output format. EXPORT MODEL produces only TensorFlow SavedModel or XGBoost Booster. See the import-model entries for ONNX.

> TRANSFORM clause: when a model is trained with a `TRANSFORM` clause, the preprocessing model is exported **separately** as a TensorFlow SavedModel (TF 2.5+) under a `transform/` subdirectory of the export folder, alongside the main model artifact (which may itself be XGBoost Booster). Both must be served together for end-to-end inference.

**Status:** GA.
**Connection required:** No (writer needs GCS write permission, not a BigQuery connection).

**Inference-on-exported-model notes:**
- All numerical values in the exported signatures are cast to `FLOAT64`.
- `STRUCT` fields must be flattened: field `f1` in `STRUCT f2` becomes a separate column `f2_f1`.
- All exported models support batch (multi-row) prediction.
- If the model's `TRANSFORM` clause uses Date/Datetime/Time/Timestamp functions, the serving container must include the `bigquery-ml-utils` library (not needed when deploying via Vertex AI Model Registry).

**Best practices:**
- Version exports by writing to a timestamped folder (e.g. `.../models/{TIMESTAMP}/model`) so each export is immutable and reproducible.
- For HP-tuning models, export the chosen `TRIAL_ID` explicitly rather than relying on the implicit optimal trial when you need a pinned, auditable artifact.
- Keep dataset and bucket co-located to avoid the cross-location error — in practice a `US` multi-region dataset **is** compatible with a `US-CENTRAL1` (or other US-region) bucket (verified: export succeeded across that pairing).
- **To visualize a boosted-tree/random-forest ensemble** (`EXPORT MODEL` → XGBoost Booster `model.bst`): download it and load with `xgboost.Booster().load_model(...)`, then `xgboost.plot_tree(booster, num_trees=0)`. See the two gotchas below — both are load-bearing, not optional.

**Limitations:**
- Dataset and destination bucket must be in the **same location**.
- Not supported if `ARRAY`, `TIMESTAMP`, or `GEOGRAPHY` feature types were used in input/post-transform data; post-transformed data also cannot be `ARRAY<STRUCT<INT64, FLOAT64>>`.
- `MATRIX_FACTORIZATION` exports have a ~1 GB size cap (reduce `num_factors` if too large).
- AutoML model exports do not support Agent Platform online prediction.
- Models trained with `TRANSFORM` before 2023-09-18 must be retrained for Model Registry online prediction.
- Remote models and ARIMA_PLUS/time-series models cannot be exported.
- **Verified gotcha — XGBoost version compatibility:** `BOOSTED_TREE_*`/`RANDOM_FOREST_*` exports use **XGBoost 0.82's legacy binary format**. Modern `xgboost` (2.0+, the current `pip install xgboost` default) **cannot load `model.bst`** — `xgb.Booster().load_model(...)` raises `Check failed: str[0] == '{'`. Pin an older release to load/visualize it locally (verified working: `xgboost==1.7.6`, which emits only a compatibility warning).
- **Verified gotcha — feature names are not preserved:** the loaded booster's `feature_names` comes back `None` (generic `f0`, `f1`, ... in `get_dump()`/plots). Set `booster.feature_names` manually to the training query's non-label `SELECT` column order — this 1:1 mapping held up when checked against a model's actual split thresholds (`num_features()` matched the raw column count exactly, with no expansion for categoricals). Verified for both `BOOSTED_TREE_CLASSIFIER` and `BOOSTED_TREE_REGRESSOR`.
- **`BOOSTED_TREE_REGRESSOR`-specific:** loading the exported booster also prints `reg:linear is now deprecated in favor of reg:squarederror` — a harmless legacy-objective-name warning (in addition to the `XGBoost < 1.0.0` compatibility warning above), not an error.

**Locations:** Dataset region must equal the GCS bucket region/multi-region.

**BigFrames API:** `bigframes.ml` estimators expose `model.to_gbq(...)` for persistence in BigQuery; GCS export is performed via the SQL `EXPORT MODEL` statement or `bq extract --model`. No dedicated one-call BigFrames GCS-export helper.

**Repo example (tested):**
- `/home/user/git/vertex-ai-mlops/data+ai/bq-ml/models/boosted_tree_classifier/boosted_tree_classifier.sql` (Example 9) and the companion notebook (Step 7) — `EXPORT MODEL` → download `model.bst` → `xgboost==1.7.6` (pinned) → `booster.feature_names` reassigned manually → `xgboost.plot_tree()`. Both gotchas above were caught and verified here.
- `/home/user/git/vertex-ai-mlops/03 - BigQuery ML (BQML)/03b - BQML Boosted Trees.ipynb` — exports a `BOOSTED_TREE` model to a timestamped GCS folder (`EXPORT MODEL ... OPTIONS(URI = 'gs://.../models/{TIMESTAMP}/model')`), i.e. XGBoost Booster format.
- `/home/user/git/vertex-ai-mlops/03 - BigQuery ML (BQML)/03g - BQML - PCA with Anomaly Detection.ipynb` and `/home/user/git/vertex-ai-mlops/03 - BigQuery ML (BQML)/03i - BQML Autoencoder with Anomaly Detection.ipynb` — export `PCA` and `AUTOENCODER` models (TensorFlow SavedModel) with the same `EXPORT MODEL ... OPTIONS(URI=...)` pattern.
- Inverse direction (importing a TF SavedModel back into BQML for serving): `/home/user/git/vertex-ai-mlops/MLOps/Serving/SQL Inference/Serve TensorFlow SavedModel Format With BigQuery.ipynb` — useful context for the round-trip, but it demonstrates `CREATE MODEL ... MODEL_TYPE='TENSORFLOW'` (import), not EXPORT MODEL.


---

### Model monitoring & data validation

BigQuery ML ships five built-in functions for **training/serving skew** and **data drift** monitoring,
plus descriptive-statistics helpers. They are model-light: skew uses statistics saved at training time
(no original training data needed); drift compares two arbitrary datasets. None require a Cloud resource
connection. The optional `MODEL` argument only enables a Vertex AI **visualization link** and requires the
model to be registered in Vertex AI Model Registry. Two tiers exist:

- **Basic** (`ML.DESCRIBE_DATA`, `ML.VALIDATE_DATA_SKEW`, `ML.VALIDATE_DATA_DRIFT`) — tabular output, anomaly flags.
- **Advanced / TFDV-compatible** (`ML.TFDV_DESCRIBE`, `ML.TFDV_VALIDATE`) — emit/consume a TensorFlow
  `DatasetFeatureStatisticsList` proto as JSON, for use with the `tensorflow-data-validation` library.

Status: **GA**. See the [Model monitoring overview](https://cloud.google.com/bigquery/docs/model-monitoring-overview).

> Cross-reference: `ML.DETECT_ANOMALIES` (anomaly detection from a trained model) and `AI.DETECT_ANOMALIES`
> (foundation-model time-series anomalies) are distinct — see the model-type entries / `../bq-ai-functions/`.

---

### `ML.DESCRIBE_DATA`
- **Description:** Computes descriptive statistics (count, min/max, mean, stdev, median, quantiles, unique, top values) for each column of a table or subquery. First step of a monitoring workflow to sanity-check a dataset.
- **Use cases:**
  - Profile training or serving data before/after model creation.
  - Compare two snapshots manually before formal skew/drift checks.
  - Feature-engineering exploration.
- **documentation:** https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-describe-data
- **Type:** Table-valued function.
- **Applies to models:** N/A (operates on data, not a model).

**Syntax:**
```sql
SELECT *
FROM ML.DESCRIBE_DATA(
  { TABLE `PROJECT_ID.DATASET.TABLE_NAME` | (query_statement) }
  [, STRUCT(
       num_quantiles AS num_quantiles,
       num_array_length_quantiles AS num_array_length_quantiles,
       top_k AS top_k
     )]
);
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| input data | `TABLE` ref or `(query_statement)` | Yes | — | Data to profile. |
| `num_quantiles` | INT64 | No | 4 | Quantiles for numerical columns. Range \[2, 100000\]. |
| `num_array_length_quantiles` | INT64 | No | 10 | Quantiles for ARRAY lengths. Range \[1, 100000\]. |
| `top_k` | INT64 | No | 1 | Top values returned for categorical columns. Range \[1, 10000\]. |

**Outputs:** one row per input column.

| Column | Type | Description |
|--------|------|-------------|
| `name` | STRING | Input column name. |
| `num_rows` | INT64 | Total rows for the column. |
| `min` / `max` | STRING | MIN / MAX value. |
| `mean` / `stdev` / `median` | FLOAT64 | Numerical only; NULL for categorical. |
| `quantiles` | ARRAY\<FLOAT64\> | Numerical only (APPROX_QUANTILES). |
| `unique` | INT64 | Categorical only (APPROX_COUNT_DISTINCT). |
| `top_values` | ARRAY\<STRUCT\<value STRING, count INT64\>\> | Categorical only; `top_k` entries. |
| `min/max/avg/total_array_length` | INT64/FLOAT64 | ARRAY columns only. |
| `array_length_quantiles` | ARRAY\<INT64\> | ARRAY columns only. |

**Best practices:** Run on a representative slice (filter by date) rather than the full table to control cost.
**Limitations:** ARRAY columns are unnested before stats; `ARRAY<STRUCT<INT64, numerical>>` treated as sparse `ARRAY<numerical>`.
**BigFrames API:** Use `bigframes.pandas.DataFrame.describe()` for comparable profiling; no 1:1 wrapper.
**Repo example (tested):** `MLOps/Model Monitoring/bqml-model-monitoring-tutorial.ipynb` — `ML.DESCRIBE_DATA(TABLE ...)` and with `STRUCT(3 AS top_k, 4 AS num_quantiles)` on a TRAIN split.

---

### `ML.VALIDATE_DATA_SKEW`
- **Description:** Detects **training/serving skew** — compares statistics of new (serving) data against the **training statistics saved inside the model** at creation time. Original training data is not required.
- **Use cases:**
  - Catch serving inputs that diverge from what the model was trained on.
  - Trigger retraining when feature distributions shift from baseline.
- **documentation:** https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-validate-data-skew
- **Type:** Table-valued function.
- **Applies to models:** Any model trained on structured columns whose training statistics were stored (standard BQML model_types with feature columns).

**Syntax:**
```sql
SELECT *
FROM ML.VALIDATE_DATA_SKEW(
  MODEL `PROJECT_ID.DATASET.MODEL_NAME`,           -- baseline = stored training stats
  (query_statement)                                 -- compare = serving data
  [, STRUCT(
       categorical_default_threshold AS categorical_default_threshold,
       numerical_default_threshold   AS numerical_default_threshold,
       categorical_metric_type       AS categorical_metric_type,
       thresholds                    AS thresholds,
       num_rank_histogram_buckets    AS num_rank_histogram_buckets,
       TRUE AS enable_visualization_link
     )]
);
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `MODEL` | model ref | Yes | — | Supplies the baseline (stored training) statistics. |
| compare data | `(query_statement)` | Yes | — | Serving data to validate. Only columns matching training feature columns are compared. |
| `categorical_default_threshold` | FLOAT64 | No | 0.3 | Anomaly threshold for categorical features. Range \[0, 1). |
| `numerical_default_threshold` | FLOAT64 | No | 0.3 | Anomaly threshold for numerical features. Range \[0, 1). |
| `categorical_metric_type` | STRING | No | `L_INFTY` | `L_INFTY` or `JENSEN_SHANNON_DIVERGENCE`. |
| `thresholds` | ARRAY\<STRUCT\<STRING, FLOAT64\>\> | No | — | Per-column overrides, e.g. `[('col_a', 0.1)]`. |
| `num_rank_histogram_buckets` | INT64 | No | 50 | Buckets for categorical rank histogram. Range \[1, 10000\]. |
| `enable_visualization_link` | BOOL | No | FALSE | Emits `visualization_link` (model must be Vertex-registered). |

**Outputs:** see shared output schema under `ML.VALIDATE_DATA_DRIFT`.

**Best practices:** Register the model in Vertex AI (`MODEL_REGISTRY='VERTEX_AI'`) to get clickable distribution visualizations.
**Limitations:** Numerical metric is always Jensen-Shannon divergence (not configurable); needs a model that stored training stats.
**BigFrames API:** No direct equivalent.
**Repo example (tested):** `MLOps/Model Monitoring/bqml-model-monitoring-tutorial.ipynb` and `model_monitoring_job.sql` — `ML.VALIDATE_DATA_SKEW(MODEL ..., (serving query), STRUCT(TRUE AS enable_visualization_link))`.

---

### `ML.VALIDATE_DATA_DRIFT`
- **Description:** Detects **data drift** — compares statistics between **two datasets** (typically two serving windows) to flag anomalous distribution changes over time. The `MODEL` argument here is optional and only adds the visualization link.
- **Use cases:**
  - Compare last week vs. this week of serving data.
  - Compare training data vs. current serving data as a manual skew check (no stored stats needed).
  - Drift on model-transformed features by wrapping inputs in `ML.TRANSFORM`.
- **documentation:** https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-validate-data-drift
- **Type:** Table-valued function.
- **Applies to models:** Any (model is optional, used only for the visualization link).

**Syntax:**
```sql
SELECT *
FROM ML.VALIDATE_DATA_DRIFT(
  (base_query_statement),       -- baseline window
  (compare_query_statement),    -- comparison window
  [STRUCT(
     categorical_default_threshold AS categorical_default_threshold,
     numerical_default_threshold   AS numerical_default_threshold,
     categorical_metric_type       AS categorical_metric_type,
     thresholds                    AS thresholds,
     num_rank_histogram_buckets    AS num_rank_histogram_buckets
   )]
  [, MODEL `PROJECT_ID.DATASET.MODEL_NAME`]   -- optional: enables visualization_link
);
```

**Inputs:** same STRUCT options as `ML.VALIDATE_DATA_SKEW` (defaults: categorical/numerical threshold `0.3`,
`categorical_metric_type='L_INFTY'`, `num_rank_histogram_buckets=50`). Pass `STRUCT()` to accept all defaults.
The two positional args are both `(query_statement)` (base, compare).

**Outputs (shared by SKEW and DRIFT):** one row per compared column.

| Column | Type | Description |
|--------|------|-------------|
| `input` | STRING | Input (feature) column name. |
| `metric` | STRING | Comparison metric: `JENSEN_SHANNON_DIVERGENCE` (numerical), `L_INFTY` or `JENSEN_SHANNON_DIVERGENCE` (categorical). |
| `value` | FLOAT64 | Computed statistical difference between the two datasets. |
| `threshold` | FLOAT64 | Threshold applied to `value`. |
| `is_anomaly` | BOOL | TRUE when `value` > `threshold`. |
| `visualization_link` | STRING | Present only when `MODEL` / `enable_visualization_link` is supplied; URL to Vertex AI monitoring visualization. |

**Best practices:** Filter `WHERE is_anomaly = True` to drive alerts/retraining (see job SQL). Use `ML.TRANSFORM(MODEL, data)` as the inputs to monitor drift on engineered features rather than raw columns.
**Limitations:** No schema validation between the two inputs (mismatched columns are ignored). For categorical, choosing `JENSEN_SHANNON_DIVERGENCE` changes which features appear in the report vs. `L_INFTY`.
**BigFrames API:** No direct equivalent.
**Repo example (tested):** `MLOps/Model Monitoring/bqml-model-monitoring-tutorial.ipynb` — drift on two serving windows with `STRUCT(0.03 AS categorical_default_threshold, 0.03 AS numerical_default_threshold)` and `MODEL ...`; also `STRUCT('JENSEN_SHANNON_DIVERGENCE' AS categorical_metric_type)`, and drift over `ML.TRANSFORM` outputs. `model_monitoring_job.sql` wraps it in a scheduled-query retrain/alert loop.

---

### `ML.TFDV_DESCRIBE`
- **Description:** Computes fine-grained descriptive statistics emitted as a TensorFlow Data Validation `DatasetFeatureStatisticsList` proto (JSON). Same behavior as `tfdv.generate_statistics_from_csv`.
- **Use cases:**
  - Produce TFDV-compatible stats for `tfdv.visualize_statistics` / `display_anomalies`.
  - Persist serving-stats snapshots over time for later drift comparison.
  - Feed `ML.TFDV_VALIDATE`.
- **documentation:** https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-tfdv-describe
- **Type:** Table-valued function.
- **Applies to models:** N/A (operates on data).

**Syntax:**
```sql
SELECT *
FROM ML.TFDV_DESCRIBE(
  { TABLE `PROJECT_ID.DATASET.TABLE_NAME` | (query_statement) }
  [, STRUCT(...)]
);
```

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| `dataset_feature_statistics_list` | JSON/STRING | TFDV `DatasetFeatureStatisticsList` proto serialized as JSON. Parse with `json_format.ParseDict` into `tfmd.proto.statistics_pb2.DatasetFeatureStatisticsList`. |

**Best practices:** Store the output column into a snapshot table (`t TIMESTAMP, dataset_feature_statistics_list ...`) to enable historical drift.
**Limitations:** Output is a proto blob, not tabular per-feature rows; needs the `tensorflow-data-validation` / `tensorflow-metadata` Python libs to render.
**BigFrames API:** No direct equivalent.
**Repo example (tested):** `MLOps/Model Monitoring/bqml-model-monitoring-tutorial.ipynb` — `ML.TFDV_DESCRIBE((SELECT ... TRAIN))`, JSON-parsed and passed to `tfdv.visualize_statistics`.

---

### `ML.TFDV_VALIDATE`
- **Description:** Compares two `DatasetFeatureStatisticsList` protos to identify anomalous differences; returns a TFDV `Anomalies` proto (JSON). Supports `SKEW` (training vs. serving) and `DRIFT` (serving vs. serving) modes.
- **Use cases:**
  - TFDV-native anomaly detection inside BigQuery.
  - Integrate BQML monitoring with an existing TFDV/TFX pipeline.
- **documentation:** https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-tfdv-validate
- **Type:** Scalar function (returns one proto value).
- **Applies to models:** N/A.

**Syntax:**
```sql
SELECT ML.TFDV_VALIDATE(
  base_stats,        -- DatasetFeatureStatisticsList (from ML.TFDV_DESCRIBE or a stored column)
  compare_stats,     -- DatasetFeatureStatisticsList
  'SKEW'             -- or 'DRIFT'
  [, categorical_default_threshold FLOAT64
   , categorical_metric_type STRING
   , numerical_default_threshold FLOAT64
   , numerical_metric_type STRING
   , thresholds ARRAY<STRUCT<STRING, FLOAT64>> ]
) AS validate;
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| base / compare stats | `DatasetFeatureStatisticsList` (JSON) | Yes | — | From `ML.TFDV_DESCRIBE` or a persisted snapshot column. |
| validation type | STRING | Yes | — | `'SKEW'` or `'DRIFT'`. |
| `categorical_default_threshold` | FLOAT64 | No | 0.3 | — |
| `categorical_metric_type` | STRING | No | `L_INFTY` | `L_INFTY` / `JENSEN_SHANNON_DIVERGENCE`. |
| `numerical_default_threshold` | FLOAT64 | No | 0.3 | — |
| `numerical_metric_type` | STRING | No | `JENSEN_SHANNON_DIVERGENCE` | — |
| `thresholds` | ARRAY\<STRUCT\<STRING, FLOAT64\>\> | No | — | Per-feature overrides. |

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| (scalar) | JSON/STRING | TFDV `Anomalies` proto as JSON. Parse with `json_format.ParseDict` into `tfmd.proto.anomalies_pb2.Anomalies`; render via `tfdv.display_anomalies`. |

**Best practices:** Reuse stored `ML.TFDV_DESCRIBE` snapshots as one input to avoid recomputing baseline stats.
**Limitations:** No schema validation; choosing `JENSEN_SHANNON_DIVERGENCE` as the default threshold metric can exclude a feature from the report. Requires TFDV Python libs to visualize.
**BigFrames API:** No direct equivalent.
**Repo example (tested):** `MLOps/Model Monitoring/bqml-model-monitoring-tutorial.ipynb` — `ML.TFDV_VALIDATE((SELECT * FROM ML.TFDV_DESCRIBE(TABLE TRAIN)), (SELECT * FROM ML.TFDV_DESCRIBE(TABLE SERVE)), 'SKEW')`, parsed and rendered with `tfdv.display_anomalies`.


---

## BigFrames (Python)

BigFrames exposes a scikit-learn-style API (`bigframes.ml`) that trains BigQuery ML models under the hood — e.g. `bigframes.ml.linear_model.LinearRegression`/`LogisticRegression`, `bigframes.ml.ensemble.XGBClassifier`/`RandomForestClassifier`, `bigframes.ml.cluster.KMeans`, `bigframes.ml.decomposition.PCA`/`MatrixFactorization`, `bigframes.ml.forecasting.ARIMAPlus`, `bigframes.ml.preprocessing.*`, and `bigframes.ml.imported.{TensorFlowModel,ONNXModel,XGBoostModel}`. Each entry above lists its BigFrames equivalent (or notes when none exists and SQL is the path). [bigframes.ml reference](https://cloud.google.com/python/docs/reference/bigframes/latest/bigframes.ml).
