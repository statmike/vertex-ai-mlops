![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Fdata%2Bai%2Fbq-ml%2Freference&file=create-model-model-types.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/data%2Bai/bq-ml/reference/create-model-model-types.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ml/reference/create-model-model-types.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ml/reference/create-model-model-types.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ml/reference/create-model-model-types.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ml/reference/create-model-model-types.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-ml/reference/create-model-model-types.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-ml/reference/create-model-model-types.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# CREATE MODEL — Model Types

> Part of the [BigQuery ML — Detailed Reference](../RESOURCES.md) · [Project README](../README.md)

The `CREATE MODEL` statement trains and stores a model; the `model_type` option selects the algorithm. Full statement reference: [The CREATE MODEL statement](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create). Entries below are grouped supervised → unsupervised → recommendation → time series → insight → imported → remote → transform-only.

> **MAJOR GOTCHA, verified live (`pipelines/cloud_workflows/`) — BigQuery's automatic query result cache does NOT reliably invalidate when a referenced MODEL is replaced via `CREATE OR REPLACE MODEL`.** Running the identical `SELECT ... FROM ML.EVALUATE(MODEL X)` (or any other model-reading query) as a separate top-level query job before and after retraining `X` can silently return a `cacheHit: true` **stale result from before the retrain** — the two calls looked identical in application code but returned bit-for-bit the same numbers even though the model had genuinely changed. Confirmed directly: with caching left on, a "before" and "after" retrain check both returned `roc_auc = 0.7688881118881119`; adding `bq query --nouse_cache` (or, via API, `configuration.query.useQueryCache: false`) to the *same* query text against the *same* retrained model returned the correct, different value (`0.729021978021978`, matching the pre-retrain model). This risk is specific to issuing separate standalone query jobs (exactly what an external orchestrator like Cloud Workflows, a custom monitoring script, or a notebook cell does) — it was *not* observed inside a single multi-statement BigQuery script (`pipelines/sql_scripting/`), where the equivalent before/after `ML.EVALUATE` sub-queries reliably differed every time. **Any pipeline that reads a model's metrics via separate queries before/after a `CREATE OR REPLACE MODEL` step should set `useQueryCache: false` on those reads**, not just trust that a real change to the model will bust the cache.
>
> **Follow-on GOTCHA, verified live (`pipelines/vertex_kfp/`) — the `google_cloud_pipeline_components` prebuilt `Bigquery*JobOp` components silently drop `useQueryCache: false` if you pass it as a Python `bool`.** These components accept a `job_configuration_query={'useQueryCache': False}` override to disable caching (e.g. on `BigqueryEvaluateModelJobOp`, exposed to the exact staleness bug above since it re-runs the same `ML.EVALUATE` text against a repeatedly-retrained model). But the library's own JSON-cleanup step (`recursive_remove_empty`, in `google_cloud_pipeline_components.container.v1.gcp_launcher.utils.json_util`) strips any key whose value is falsy under plain Python truthiness (`if v:`) — and `False` is falsy — so the override is silently deleted before the job is ever submitted, and caching stays on with no error or warning. Confirmed both ways via `INFORMATION_SCHEMA.JOBS_BY_PROJECT`: `job_configuration_query={'useQueryCache': False}` still showed `cache_hit: true`; the BigQuery REST API itself accepts the **string** `'false'` for this boolean field and genuinely disables caching (`cache_hit: false`, confirmed both via a direct REST call and inside a real pipeline run). **Fix: pass `job_configuration_query={'useQueryCache': 'false'}` — the string `'false'`, not the Python bool `False`.**
>
> **Not every Google API wrapper has this bug — verify per library.** `pipelines/composer_airflow/`'s `BigQueryInsertJobOperator` (Airflow provider) is exposed to the identical at-risk pattern (re-running `ML.EVALUATE` against a repeatedly-retrained model) but its `configuration={'query': {..., 'useQueryCache': False}}` — a real Python `bool` — works correctly (`cache_hit: false`, confirmed via `INFORMATION_SCHEMA.JOBS_BY_PROJECT`). It submits jobs through the standard `google-cloud-bigquery` client's own `QueryJob.from_api_repr()`, not the buggy custom JSON-cleanup logic above. Don't assume the KFP-components bug generalizes to every BigQuery-adjacent Python wrapper.


---

## `LINEAR_REG` / `LOGISTIC_REG`  (Generalized Linear Models)

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
- `ML.ADVANCED_WEIGHTS` — superset adding `standard_error` and `p_value`, one flat row per coefficient (requires `calculate_p_values = TRUE` + `DUMMY_ENCODING` + `l1_reg = 0`, all at train time). This is the only way to learn that a weight is indistinguishable from zero; `ML.WEIGHTS` and `ML.GLOBAL_EXPLAIN` will happily report a confident-looking number for a coefficient the model cannot defend.
- `ML.GLOBAL_EXPLAIN` — overall feature attributions (requires `enable_global_explain = TRUE` at train time).
- `ML.EXPLAIN_PREDICT` — per-row feature attributions (`STRUCT(k AS top_k_features)`).

**Best practices:**
- Set `enable_global_explain = TRUE` at train time if you'll want global attributions — it cannot be added afterward.
- For imbalanced classification (e.g. fraud), use `auto_class_weights = TRUE`.
- Use `data_split_method = 'CUSTOM'` with a BOOL split column to reproduce TRAIN/VALIDATE/TEST exactly.
- `NORMAL_EQUATION` (auto-selected for small unregularized problems) trains in one pass — no iterations to tune; `ML.TRAINING_INFO` returns a single row with `eval_loss = NULL` (no per-iteration eval curve like gradient descent produces).
- **Use `category_encoding_method = 'DUMMY_ENCODING'` whenever you plan to read `ML.WEIGHTS` or `ML.ADVANCED_WEIGHTS`** (the latter requires it outright). With the default `ONE_HOT_ENCODING`, every category is one-hot encoded *and* the model keeps an intercept, so the design matrix is collinear (rank-deficient) for any categorical feature — the individual `category_weights` are not uniquely identified. **Verified by training the same model twice** (`models/linear_regression/`, `penguins`/`body_mass_g`, identical `SELECT`, only `AUTO_SPLIT`'s random draw differing): an `island` category's weight swung from **+305 / +353 / +340 in one run to −39 / −4 / +8.6 in another** — different scale, different sign — while `ML.PREDICT` and `ML.EVALUATE` stayed effectively unchanged. `DUMMY_ENCODING` drops one baseline category per feature (pinned to `weight: 0.0`) and makes every other category's weight a stable, well-defined delta from it.

**Limitations:**
- `ML.ADVANCED_WEIGHTS` p-values require **all** of: `calculate_p_values = TRUE`, `category_encoding_method = 'DUMMY_ENCODING'`, `l1_reg = 0`, **and** total feature cardinality \< 1,000. Only linear and **binary** logistic regression are supported (not multiclass). None of this is retrofittable — the statistics are computed during training, so a model trained without `calculate_p_values` must be retrained, and three of the four preconditions fail at `CREATE MODEL` time rather than when you call the TVF. See that function's entry for the verified error text of each.
- `ML.ROC_CURVE` is binary-only; `ML.CONFUSION_MATRIX` is classification-only.
- Linear models capture only linear relationships — engineer interaction/polynomial features (via `TRANSFORM`) for nonlinearity, or use boosted trees.
- `ML.WEIGHTS`/`ML.GLOBAL_EXPLAIN` attributions for a given category can shift materially between training runs when using `ONE_HOT_ENCODING` (see the `DUMMY_ENCODING` best practice above) — don't treat one run's per-category numbers as ground truth unless trained with `DUMMY_ENCODING`.

**Locations:** Available in all BigQuery ML regions/multi-regions. `EXPORT MODEL` (to GCS, TensorFlow SavedModel format) and Vertex AI Model Registry registration are supported.

**BigFrames API:** `bigframes.ml.linear_model.LinearRegression()` and `bigframes.ml.linear_model.LogisticRegression()` — `.fit(X, y)` / `.predict()` / `.score()`.

**Repo example (tested):**
- `data+ai/bq-ml/models/logistic_regression/logistic_regression.sql` — progressive LOGISTIC_REG lifecycle on `census_adult_income`: create → ML.EVALUATE → ML.CONFUSION_MATRIX → ML.ROC_CURVE → ML.PREDICT → ML.EXPLAIN_PREDICT → ML.GLOBAL_EXPLAIN → **ML.ADVANCED_WEIGHTS** → ML.FEATURE_INFO/TRAINING_INFO → TRANSFORM → HP tuning. Trained with `calculate_p_values`/`DUMMY_ENCODING`/`l1_reg = 0` so the significance read is available; Example 8 finds 54 of 97 testable coefficients insignificant at p > 0.05.
- `data+ai/bq-ml/models/linear_regression/linear_regression.sql` — progressive LINEAR_REG lifecycle on `penguins`/`body_mass_g`: create (with `DUMMY_ENCODING`) → ML.EVALUATE → ML.PREDICT → ML.EXPLAIN_PREDICT → ML.GLOBAL_EXPLAIN → **ML.WEIGHTS** → **ML.ADVANCED_WEIGHTS** → ML.FEATURE_INFO/TRAINING_INFO → TRANSFORM → HP tuning. Confirmed the `NORMAL_EQUATION` single-pass behavior and the `ONE_HOT_ENCODING` category-weight instability documented above. Example 7 pairs `ML.WEIGHTS` with `ML.ADVANCED_WEIGHTS` on the same model, including the `STRUCT(TRUE AS standardize)` variant, and shows `island` failing significance once `species` is present.
- `data+ai/bq-ml/workflows/regression_based_forecasting/regression_based_forecasting.ipynb` — `LINEAR_REG` used for forecasting via a lagged-feature design matrix; shows the regression `ML.EVALUATE` columns and recursive vs. direct multi-step prediction, benchmarked against `ARIMA_PLUS` on the same series.
- `data+ai/bq-ml/workflows/cross_validation/cross_validation.sql` and `data+ai/bq-ml/workflows/ensembling/ensembling.sql` — `LOGISTIC_REG` reused as a fold-level and base-learner model respectively; `data+ai/bq-ml/workflows/propensity_score_matching/` and `data+ai/bq-ml/workflows/survival_analysis/` use the same mechanics for causal and hazard estimation rather than prediction.
- Options this section documents that the lifecycles above cover elsewhere: registry registration, `EXPORT MODEL`, and endpoint serving are covered end-to-end in `data+ai/bq-ml/models/export/` and `data+ai/bq-ml/models/remote/`.


---

## `BOOSTED_TREE_CLASSIFIER` / `BOOSTED_TREE_REGRESSOR`
- **Description:** Gradient-boosted decision tree ensembles trained with the [XGBoost](https://xgboost.readthedocs.io/) library. `BOOSTED_TREE_CLASSIFIER` handles binary and multiclass classification; `BOOSTED_TREE_REGRESSOR` handles regression. Boosting trains a sequence of trees where each tree learns the residual error of the prior ensemble. Setting `num_parallel_tree > 1` turns the model into a boosted random forest.
- **When to use:**
  - Structured/tabular data where high accuracy matters more than interpretability of a single equation.
  - Non-linear feature interactions that a linear/logistic model can't capture.
  - You want built-in per-prediction (local) and per-model (global) feature attributions for a tree model.
  - You want to export an XGBoost Booster artifact (`.bst`, or `.ubj` when trained with `xgboost_version = '2.1'`) or auto-register the model to Vertex AI for online serving.
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
| `xgboost_version` | STRING | No | `0.9` | `0.9`, `1.1`, `2.1` | XGBoost library version used for training. `2.1` added 2026-08-27. **The default is still `0.9`** — a 2019 release — and it is what you get when you omit the option (verified: the option comes back as `xgboostVersion: "0.9"` in a model's training options even when never specified). The value list above is the error message's own enumeration, read back by passing an unsupported value. This option changes the `EXPORT MODEL` artifact — see the [EXPORT MODEL](model-management-monitoring.md#export-model) gotchas. **It also costs you `ML.TRAINING_INFO`:** at `'2.1'`, that function returns zero rows once training runs more than 10 iterations (measured; see the [`ML.TRAINING_INFO` gotcha](model-lifecycle-functions.md#mltraining_info)). Every other lifecycle function is unaffected. |
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
- **GOTCHA (verified):** a single `BOOSTED_TREE_REGRESSOR` model trains in **~2.5–4.5 minutes even on a training table with fewer than 1,000 rows** — a large, fixed overhead compared to `LINEAR_REG` on the same data (~15 seconds). Verified directly this is not something tunable away: lowering `max_iterations` and setting `early_stop=FALSE` made a model take *longer*, not shorter, and training the identical model under a temporary BigQuery Editions autoscale reservation made no measurable difference (the job's own query plan showed it actively consuming slot-time throughout, not queued waiting for capacity). Appears to be a fixed cost of this model type's training path in BigQuery ML. Matters most for any workflow that trains many small `BOOSTED_TREE_REGRESSOR` models in a loop (e.g. one per forecast horizon day) — see `workflows/regression_based_forecasting/`, which works around it by submitting distinctly-named `CREATE MODEL` jobs concurrently (verified live: BigQuery runs them in true parallel from one client, so a batch finishes in roughly one model's training time, not the sum).
- **This fixed overhead is a floor, not a ceiling — real training time still scales with data/feature size once both grow substantially.** Verified with `BOOSTED_TREE_CLASSIFIER` on a genuinely large table (~1M rows, up to 771 features including two `ARRAY<FLOAT64>` embedding columns): training took **19–40 minutes per model**, not the ~270s floor seen on trivial data. Three models submitted concurrently still finished in the time of the slowest one (~40 min), not the sum (~75 min) — see `workflows/embeddings_classification/`.
- **`ARRAY<FLOAT64>` columns can be passed directly to `CREATE MODEL` as feature columns for `BOOSTED_TREE_CLASSIFIER`/`REGRESSOR`** — verified live; no need to unnest an embedding vector into individual `col_0, col_1, ...` columns first. `ML.FEATURE_INFO` reports a `dimension` value for these columns. Confirmed at 256- and 512-dimension embedding columns in `workflows/embeddings_classification/`. (Elementwise arithmetic between two same-length arrays, e.g. an absolute-difference feature, still has no native operator — compute it via `UNNEST(a) WITH OFFSET` joined to `UNNEST(b) WITH OFFSET` on position, reaggregated with `ARRAY(...)`.)

**Locations:** Boosted-tree training is not supported in all BigQuery ML regions/multi-regions; check the [BigQuery ML locations](https://cloud.google.com/bigquery/docs/locations) list. Vertex AI registration defaults to the region matching the BQ location (e.g. `EU` multi-region maps to `europe-west4`).

**BigFrames API:** `bigframes.ml.ensemble.XGBClassifier` / `bigframes.ml.ensemble.XGBRegressor` — `model = XGBClassifier(); model.fit(X, y); model.predict(X)`. **Verified: the constructor has no `class_weight`/`auto_class_weights` parameter** (checked the installed signature directly — `n_estimators`, `booster`, `max_depth`, `learning_rate`, `reg_alpha`/`reg_lambda`, etc., but no class-weighting option), unlike `bigframes.ml.linear_model.LogisticRegression` which exposes sklearn-style `class_weight`. A BigFrames `XGBClassifier` trained on an imbalanced label with no manual reweighting will not match a SQL `BOOSTED_TREE_CLASSIFIER` trained with `auto_class_weights = TRUE` — expect higher precision / lower recall from the unweighted BigFrames model, not a bug.

**Repo example (tested):**
- `data+ai/bq-ml/models/boosted_tree_classifier/boosted_tree_classifier.sql` + notebook — `BOOSTED_TREE_CLASSIFIER` on `census_adult_income` (same data/label as `models/logistic_regression/`, for direct technique comparison), with the full lifecycle incl. the tree-visualization step (`EXPORT MODEL` → `xgboost.plot_tree()`).
- `data+ai/bq-ml/models/boosted_tree_regressor/boosted_tree_regressor.sql` + notebook — `BOOSTED_TREE_REGRESSOR` on `penguins`/`body_mass_g` (same data/label as `models/linear_regression/`); `r2_score` 0.983 vs. `RANDOM_FOREST_REGRESSOR`'s 0.922 and linear regression's 0.875 on identical data. `TRANSFORM` uses `ML.LABEL_ENCODER`. Same tree-visualization step; the `reg:linear` deprecation warning on load is a `0.9`-era artifact and is gone at `xgboost_version = '2.1'` (see gotcha above).
- `data+ai/bq-ml/workflows/regression_based_forecasting/regression_based_forecasting.ipynb` — 28 `BOOSTED_TREE_REGRESSOR` models (one per forecast horizon day, direct multi-step forecasting) trained concurrently in batches to work around the per-model training-time GOTCHA above; got the best MAPE of any technique in that notebook's comparison, including the `ARIMA_PLUS` reference, despite a worse MAE/RMSE.
- `data+ai/bq-ml/workflows/embeddings_classification/embeddings_classification.ipynb` — 3 `BOOSTED_TREE_CLASSIFIER` models trained on a ~1M-row (product × hierarchy-node) table with `AI.EMBED`-generated 256-dim embeddings passed as `ARRAY<FLOAT64>` feature columns directly (verified: no unnesting needed); demonstrates the real-data-scale training-time finding above (19-40 min/model, not the ~270s trivial-data floor) and that raw `ML.EVALUATE` metrics don't always rank models the same way as an applied top-1 resolution accuracy computed via `ML.PREDICT` + `UNNEST`/`QUALIFY`. Also includes two baselines that outperform this whole pairwise approach: a direct multiclass `BOOSTED_TREE_CLASSIFIER` (no cross-join, trains in minutes not tens of minutes, ~69-70% category accuracy vs. the pairwise approach's ~42-48%) and a zero-training `VECTOR_SEARCH` lookup (~52% category accuracy) — **verified `VECTOR_SEARCH` needs no vector index at small scale (38 hierarchy nodes)**, it silently falls back to an exact brute-force scan; a two-stage hierarchical resolution pattern (nearest department first, then nearest category filtered to that department's children via `WHERE base.hierarchy_node_parent = query.pred_department`) mirrors the `ML.PREDICT`-based resolution used for the classifiers, but with zero training cost. A real gotcha hit while building this: `top_k` on the second-stage `VECTOR_SEARCH` call must cover *all* candidate nodes (not just a small top-k like 5), since filtering by parent happens *after* `top_k` truncation — a small `top_k` can silently drop products whose true category isn't among the globally-nearest few before the parent filter ever runs.
- `data+ai/bq-ml/workflows/anomaly_fraud_detection/anomaly_fraud_detection.ipynb` — `BOOSTED_TREE_CLASSIFIER` with `auto_class_weights` on genuinely imbalanced data (`bigquery-public-data.ml_datasets.ulb_fraud_detection`, 492 fraud cases), the setting that option exists for; scored against the unsupervised `PCA` and `AUTOENCODER` detectors on the same table.
- `data+ai/bq-ml/models/export/export.sql` — `EXPORT MODEL` on a `BOOSTED_TREE_CLASSIFIER`, which exports as an XGBoost Booster (`model.bst`) rather than the TensorFlow SavedModel the GLMs/DNNs produce; `data+ai/bq-ml/models/remote/` then deploys to a Vertex AI Endpoint. Note that when the model carries a `TRANSFORM` clause the preprocessing travels with it, landing beside the model as a separate `/model/transform` artifact so the exported model reapplies it at serving time.


---

## `RANDOM_FOREST_CLASSIFIER` / `RANDOM_FOREST_REGRESSOR`
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
| `xgboost_version` | STRING | No | `0.9` | `0.9`, `1.1`, `2.1` | XGBoost library version used for training — random forests accept it on the same terms as `BOOSTED_TREE_*` (verified live on both `RANDOM_FOREST_CLASSIFIER` and `RANDOM_FOREST_REGRESSOR`; the default reads back as `0.9`). Changes the `EXPORT MODEL` artifact — see the [`BOOSTED_TREE_*` entry](#boosted_tree_classifier--boosted_tree_regressor) and the [EXPORT MODEL](model-management-monitoring.md#export-model) gotchas. Unlike `BOOSTED_TREE_*`, random forests pay no `ML.TRAINING_INFO` penalty for `'2.1'` — training is single-pass, so it never crosses the 10-iteration boundary where that function goes empty (measured; see the [`ML.TRAINING_INFO` gotcha](model-lifecycle-functions.md#mltraining_info)). |
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
- **Set `xgboost_version = '2.1'` explicitly on any random forest.** The default is `0.9`, and on the regressor that default measurably under-grows the forest — see the limitation below. At `2.1`, `RANDOM_FOREST_REGRESSOR` on `penguins`/`body_mass_g` (333 rows) reaches `r2_score` ≈ 0.922, against `BOOSTED_TREE_REGRESSOR`'s ≈ 0.983 and `LINEAR_REG`'s ≈ 0.875 on identical data — second of the three, and it gets there untuned (the best of six tuning trials, ≈ 0.917, did not beat the default). Boosting still leads on this data; the margin is narrow, not the wide gap the `0.9` default suggests.

**Limitations:**
- Random forest training is **not available in all regions** — check BigQuery ML locations before choosing a dataset region.
- `ML.WEIGHTS` does not apply (no linear coefficients).
- Explainability functions require `enable_global_explain = TRUE` set at training; cannot be added afterward without retraining.
- `ML.ROC_CURVE` is binary-classification only.
- **Verified: `max_iterations` is not a valid option for `RANDOM_FOREST_CLASSIFIER`/`RANDOM_FOREST_REGRESSOR` at all** — `CREATE MODEL` errors immediately with `Option(s) MAX_ITERATIONS are not supported for RANDOM_FOREST_* model training` if you set it (unlike `BOOSTED_TREE_*`, where `max_iterations` is a central hyperparameter). This is a hard API-level guarantee that random forest training is single-pass, not just a documented convention — there is no way to accidentally train a "boosted random forest" via this option; `num_parallel_tree` alone defines the forest. Confirmed by `ML.TRAINING_INFO`: always exactly one row (`iteration = 1`), `learning_rate = 1.0`.
- **Verified gotcha — trees are too dense to visualize at default settings.** Unlike a `BOOSTED_TREE_*` tree (a shallow stage fit on residuals), *every* `RANDOM_FOREST_*` tree is a complete, independently-trained tree. A default-settings forest's tree 0 (`num_parallel_tree=50`, `max_tree_depth=6`) had 2,435 dump lines and depth 15 — `xgboost.plot_tree()` triggers `graph is too large for cairo-renderer bitmaps` and produces an illegible image (confirmed even with SVG output, which sidesteps the bitmap-size limit but is still too dense to read at a glance). Fix: train a dedicated shallow illustrative forest for the diagram only (see best practices above).
- **GOTCHA (measured, undocumented): `RANDOM_FOREST_REGRESSOR` accuracy jumps sharply at `xgboost_version = '2.1'`.** Single-variable sweep on `penguins`/`body_mass_g` (333 rows, `num_parallel_tree = 50`, `tree_method = 'HIST'`, `AUTO_SPLIT`, nothing else changed):

  | `xgboost_version` | `r2_score` | summed `importance_weight` (all 6 features) |
  |---|---|---|
  | `0.9` (default) | 0.7314, 0.7413 | 82 splits |
  | `1.1` | 0.7442 | — |
  | `2.1` | 0.9212, 0.9207 | 2,482 splits |

  The split count is the mechanism signature: at the `0.9` default the forest is drastically under-grown, and at that size two of the six features (`island`, `culmen_length_mm`) come back at exactly **zero** `ML.FEATURE_IMPORTANCE`/`ML.GLOBAL_EXPLAIN` — at `2.1` every feature is non-zero (`island` lowest at `importance_weight` 245). Hyperparameter tuning does not close the gap at `0.9` (best tuned trial ≈ 0.755); at `2.1` all six trials land ≈ 0.907–0.917. `RANDOM_FOREST_CLASSIFIER` shows no comparable shift (`roc_auc` 0.883998 at `0.9` vs. 0.884439 at `2.1`), nor does `BOOSTED_TREE_CLASSIFIER` (0.888965 vs. 0.888313). Treat any zero-importance feature on a `0.9` random forest as a symptom of an under-grown forest, not as evidence the feature carries no signal.
- **Verified: retraining an identical `RANDOM_FOREST_*` model (same query, same options) is genuinely non-deterministic** — unlike `BOOSTED_TREE_*` (which reproduced predictions/loss curves essentially bit-for-bit across separate runs in testing, since it doesn't subsample by default), random forest always bags row/column subsamples (`subsample`/`colsample_bynode` default to 0.8, not 1.0), and there is no exposed random seed. Observed on `penguins`: two separate trainings of the same `RANDOM_FOREST_REGRESSOR` config produced visibly different tree structures, predictions, and `ML.GLOBAL_EXPLAIN` rankings (though `r2_score` stayed in a similar range within a fixed `xgboost_version` — ~0.73–0.75 at the `0.9` default, ~0.921 at `2.1`). Don't expect exact reproducibility run-to-run the way GLMs or boosted trees (mostly) provide.

**Locations:** Subject to region restrictions (random forest not supported in every BQML region/multi-region); see [BigQuery ML locations](https://cloud.google.com/bigquery/docs/locations).

**BigFrames API:** `bigframes.ml.ensemble.RandomForestClassifier` / `bigframes.ml.ensemble.RandomForestRegressor` — `.fit(X, y)` / `.predict()` / `.score()`; integrates with `bigframes.ml.pipeline` for TRANSFORM-equivalent preprocessing. **Verified: `RandomForestClassifier` has no `class_weight`/`auto_class_weights` parameter** (checked the installed signature directly — same gap as `XGBClassifier`), unlike `LogisticRegression`. A BigFrames comparison against a SQL model trained with `auto_class_weights = TRUE` is not apples-to-apples.

**Repo example (tested):**
- `data+ai/bq-ml/models/random_forest_classifier/random_forest_classifier.sql` + notebook — `RANDOM_FOREST_CLASSIFIER` on `census_adult_income` (same data/label as `logistic_regression`/`boosted_tree_classifier`, for a three-way technique comparison), incl. a dedicated shallow illustrative forest for tree visualization.
- `data+ai/bq-ml/models/random_forest_regressor/random_forest_regressor.sql` + notebook — `RANDOM_FOREST_REGRESSOR` on `penguins`/`body_mass_g` (same data/label as `linear_regression`/`boosted_tree_regressor`); the `xgboost_version` sensitivity (`r2_score` ≈ 0.92 at `2.1` vs. ≈ 0.74 at the `0.9` default, 2,482 vs. 82 splits) is measured and discussed directly in the notebook.
- `data+ai/bq-ml/workflows/ensembling/ensembling.sql` — `RANDOM_FOREST_CLASSIFIER` as one of three base learners (with `LOGISTIC_REG` and `BOOSTED_TREE_CLASSIFIER`) on the same `census_adult_income` data, so the forest's standalone metrics above can be read against its contribution in an ensemble.
- To put a tree ensemble behind a monitoring/retraining loop: `data+ai/bq-ml/functions/data_quality/` covers `ML.VALIDATE_DATA_SKEW` and `ML.VALIDATE_DATA_DRIFT` against a training baseline, and `data+ai/bq-ml/pipelines/sql_scripting/` wires drift-check → conditional `CREATE OR REPLACE MODEL` → `ML.EVALUATE` into a single scheduled script (on a `BOOSTED_TREE_CLASSIFIER`; the pattern is model-type-agnostic).


---

## `DNN_CLASSIFIER` / `DNN_REGRESSOR`
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
- **DNN_CLASSIFIER:** `precision`, `recall`, `accuracy`, `f1_score`, `log_loss`, `roc_auc` (verified in [`models/dnn_classifier/`](../models/dnn_classifier/)).
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

**Repo example (tested):** `data+ai/bq-ml/models/dnn_classifier/` and `data+ai/bq-ml/models/dnn_regressor/` — from-scratch, fully pre-validated builds on the same comparison datasets every other model type in this project uses (`census_adult_income` for the classifier, `penguins`/`body_mass_g` for the regressor), so the DNN's metrics can be read directly against the GLM, tree, and wide-and-deep results. Between them they cover `ML.TRAINING_INFO`, `ML.FEATURE_INFO`, `ML.EVALUATE`, `ML.CONFUSION_MATRIX`, `ML.ROC_CURVE`, `ML.PREDICT`, `ML.EXPLAIN_PREDICT`, `ML.GLOBAL_EXPLAIN`, `ML.FEATURE_IMPORTANCE`, `ML.ADVANCED_WEIGHTS`, and HP tuning (`ML.TRIAL_INFO`), with `auto_class_weights`, `enable_global_explain`, and an explicit `data_split_method`. For `EXPORT MODEL` (DNNs export as a TensorFlow SavedModel) and Vertex AI Endpoint serving, see `data+ai/bq-ml/models/export/` and `data+ai/bq-ml/models/remote/`.


---

## `DNN_LINEAR_COMBINED_CLASSIFIER` / `DNN_LINEAR_COMBINED_REGRESSOR`  (Wide-and-Deep)

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
| `optimizer` | array\<struct\> or string | No | `[STRUCT('dnn','ADAM'), STRUCT('linear','FTRL')]` | `ADAGRAD`,`ADAM`,`FTRL`,`RMSPROP`,`SGD` | Training optimizer. Can be set per model part, e.g. `[STRUCT('dnn','ADAGRAD'), STRUCT('linear','SGD')]`. **NOT tunable** (verified — see gotcha below; the generic "Tunable" claim that applies to plain `DNN_*` does not hold here). |
| `learn_rate` | array\<struct\> or float64 | No | `0.001` (both parts) | \>0 | Learning rate. Settable per part, e.g. `[STRUCT('dnn',0.001), STRUCT('linear',0.01)]`. **NOT tunable** (verified — `CREATE MODEL` errors immediately with `"Unsupported hyperparameter learn_rate for model_type DNN_LINEAR_COMBINED_CLASSIFIER"` when passed `HPARAM_RANGE`; see gotcha below). |
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

**Hyperparameter tuning:** Supported. Set `num_trials` (rule of thumb \>= 10 * num_hyperparameters). **Verified tunable:** `hidden_units` (via `HPARAM_CANDIDATES([STRUCT([64,32]), STRUCT([32,16])])` — same nested-STRUCT syntax as plain `DNN_*`), `dropout`, `batch_size`, `l1_reg`, `l2_reg` via `HPARAM_RANGE(...)`. **Verified NOT tunable (gotcha, contradicts a naive reading of the per-option "Tunable" docs, which describe plain `DNN_*` behavior):** `learn_rate` and `optimizer` both fail immediately with `"Unsupported hyperparameter <name> for model_type DNN_LINEAR_COMBINED_CLASSIFIER"` when given `HPARAM_RANGE`/`HPARAM_CANDIDATES`. If you need a specific learn rate, set it as a fixed literal (`learn_rate = 0.05`) alongside tuning the options that ARE tunable. Default objective: classifier `ROC_AUC`, regressor `R2_SCORE`.

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
- **Same small-dataset convergence failure as `DNN_REGRESSOR` (verified, `models/wide_and_deep_regressor/`):** on a 333-row regression dataset, unscaled numeric features + the default `learn_rate=0.001` + `early_stop=TRUE` produced a badly broken model (`r2_score≈-27.4`, 2 iterations) — same fix works (scale + raise `learn_rate` to 0.05): `r2_score≈0.79` untuned with `hidden_units=[64,32]`, notably lower than `DNN_REGRESSOR`'s ~0.86 with the equivalent fix on the identical data — hyperparameter tuning (below) closes most of the gap, finding `hidden_units=[32,16]` reaches `r2_score≈0.87`. Unlike `DNN_REGRESSOR`, `learn_rate` cannot be tuned here (see the tuning gotcha above), so if the default doesn't converge on your data you must set a higher `learn_rate` as a fixed literal — you can't discover a better one via `HPARAM_RANGE`.
- `learn_rate` and `optimizer` are not tunable (see Hyperparameter tuning above) — a real gap relative to plain `DNN_CLASSIFIER`/`DNN_REGRESSOR`, where both are tunable.

**Locations:** Available in all BigQuery ML regions/multi-regions; for Vertex AI registration / endpoint serving keep model and Vertex resources co-located (repo uses `us-central1`).

**BigFrames API:** Verified (checked the live BigFrames API reference across every `bigframes.ml` module) — **no first-class wide-and-deep class exists anywhere in `bigframes.ml`**, same permanent gap as `DNN_CLASSIFIER`/`DNN_REGRESSOR`. Use the SQL `CREATE MODEL` interface directly.

**Repo example (tested):** `data+ai/bq-ml/models/wide_and_deep_classifier/` and `data+ai/bq-ml/models/wide_and_deep_regressor/` — from-scratch, fully pre-validated builds on the same comparison datasets every other model type in this project uses (`census_adult_income` and `penguins`/`body_mass_g`), which is what makes the wide-and-deep result readable against the plain DNN directly above it. Between them they cover `ML.FEATURE_INFO`, `ML.TRAINING_INFO`, `ML.EVALUATE` (precision/recall/accuracy/f1_score/log_loss/roc_auc), `ML.CONFUSION_MATRIX`, `ML.ROC_CURVE`, `ML.PREDICT`, `ML.EXPLAIN_PREDICT`, `ML.GLOBAL_EXPLAIN`, `ML.FEATURE_IMPORTANCE`, `ML.ADVANCED_WEIGHTS`, and HP tuning, with `auto_class_weights`, `enable_global_explain`, and an explicit `data_split_method`. `EXPORT MODEL` produces a TensorFlow SavedModel — see `data+ai/bq-ml/models/export/`, and `data+ai/bq-ml/models/remote/` for Endpoint deployment.


---

## `AUTOML_CLASSIFIER` / `AUTOML_REGRESSOR`
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

**GOTCHA (verified): the zero-argument form of `ML.CONFUSION_MATRIX` — `ML.CONFUSION_MATRIX(MODEL ...)`, relying on AutoML's own internal held-out eval split — fails immediately and consistently with a generic internal error (`Error: 21631273`, "This is usually caused by a transient issue") on an `AUTOML_CLASSIFIER` model.** Reproduced on 100+ consecutive attempts via both the `bq` CLI and the Python client — it is NOT actually transient, and the `google-cloud-bigquery` client's default retry logic treats it as retryable, so a `client.query(...).result()` call appears to hang for a very long time instead of failing fast. **`ML.EVALUATE` and `ML.ROC_CURVE`'s zero-argument forms both work fine on the identical model** — this is isolated specifically to `ML.CONFUSION_MATRIX`. **Fix: always pass an explicit data argument** — `ML.CONFUSION_MATRIX(MODEL ..., (SELECT ...))` — which works normally (confirmed in seconds against the model's own training table). If a notebook/script hits this, interrupt/cancel the call rather than waiting — it will not resolve on its own.

**GOTCHA (verified): the zero-argument `ML.EVALUATE` aggregate for AutoML model types contains at least one field that does not reduce to a straightforward, reconcilable statistic.** For `AUTOML_CLASSIFIER`, `accuracy=0.5` was returned alongside `roc_auc=0.930` — the model's own metadata (`bq show --model`) confirmed evaluation ran against a class-balanced ~6,416-row internal eval set (3,208 per class, not the natural class distribution), but `accuracy=0.5`/`precision`/`recall` didn't match ANY of the model's 203 confidence-threshold rows in its own `binaryConfusionMatrixList` (whose threshold=0.5 row shows `accuracy=0.844`, not `0.5`) — the exact Vertex AI methodology behind the aggregate isn't visible from BigQuery's side. For `AUTOML_REGRESSOR`, `median_absolute_error` and `explained_variance` both returned exactly `0.0` while `mean_absolute_error`/`mean_squared_error`/`r2_score` looked genuine and self-consistent (`mean_squared_error` matched `ML.TRAINING_INFO`'s `eval_loss` exactly) — this couldn't be root-caused as deeply since the model had already been dropped by the time it was reviewed. **Fix/workaround for both:** pass an explicit data argument — `ML.EVALUATE(MODEL ..., (SELECT ...))` — which returns standard, reconcilable metrics (confirmed for the classifier: `accuracy=0.8508` against the training table, matching a directly-computed confusion matrix exactly). Prefer `roc_auc`/`log_loss` (classifier) or `mean_squared_error`/`r2_score` (regressor) — both threshold-independent and verified trustworthy — over the zero-argument `accuracy`/`median_absolute_error`/`explained_variance` fields for this model type.

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
- **Verified: training data must contain at least 1,000 rows.** `CREATE MODEL` fails immediately with `"Input data contains N rows. The minimum number of input rows for AutoML Tables models is 1000."` if fewer — this applies regardless of `budget_hours` and is not called out in the official reference. Small demo datasets used elsewhere in this project (e.g. `penguins`, ~333 rows) cannot train an AutoML model at all; see `models/automl_regressor/` for a real example of hitting this and switching datasets.
- Trains as an `ML_EXTERNAL` job on Vertex AI (not in-BigQuery `QUERY`); on flat-rate/reservations the project must accommodate `ML_EXTERNAL`. Evaluation/prediction run as standard `QUERY` jobs.
- Classifier label cardinality is capped at 1,000 unique classes (contact bqml-feedback@google.com for more).
- Feature column names must be 125 characters or fewer.
- Default max 5 concurrent AutoML training jobs per project (raising Vertex AI quota does not change this; submit a request to raise it).
- Wall-clock time exceeds `budget_hours` because of model compression and data movement to/from AutoML.
- No `TRANSFORM`, no `ML.WEIGHTS`, no `ML.EXPLAIN_PREDICT`, no user HP-tuning.

**Locations:** AutoML model availability differs by region/multi-region; check [BigQuery ML locations](https://cloud.google.com/bigquery/docs/locations). Training data, model, and the Vertex AI region must be compatible.

**BigFrames API:** Verified (checked the live BigFrames API reference across every `bigframes.ml` module: `linear_model`, `ensemble`, `cluster`, `decomposition`, `forecasting`, `imported`, `llm`) — **no first-class AutoML estimator class exists anywhere in `bigframes.ml`**, the same permanent gap as `DNN_CLASSIFIER`/`DNN_REGRESSOR`/wide-and-deep. Use the SQL `CREATE MODEL` interface directly.

**Repo example (tested):** `data+ai/bq-ml/models/automl_classifier/` (same `census_adult_income` data as the other classifiers) and `data+ai/bq-ml/models/automl_regressor/` (a real `bigquery-public-data.samples.natality` regression, NOT the usual `penguins` — see the minimum-row-count limitation above). Between them they cover `ML.FEATURE_INFO`, `ML.TRAINING_INFO`, `ML.EVALUATE` (`precision`/`recall`/`accuracy`/`f1_score`/`log_loss`/`roc_auc`), `ML.CONFUSION_MATRIX`, `ML.ROC_CURVE`, `ML.PREDICT`, `ML.EXPLAIN_PREDICT`, `ML.GLOBAL_EXPLAIN`, and `ML.WEIGHTS`. Both were validated via `bq query --dry_run` (free syntax check) rather than a throwaway paid pre-validation run, given this model type's real dollar cost (~$21.25/node-hour).

**Budget the wall-clock at 2-3× the stated budget.** `budget_hours = 1.0` produced **2.63 hours** wall-clock for the classifier and **2.25 hours** for the regressor, both verified via `ML.TRAINING_INFO`'s `duration_ms`. The overhead is not a small fixed margin on top of the budget — it more than doubled it in both measured runs, so a "1-hour" AutoML job should be planned as a 2-3 hour job.


---

## `KMEANS`
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
- Tune `num_clusters` with `HPARAM_RANGE` + `davies_bouldin_index` objective rather than guessing `k` — but verified (`models/kmeans/`) that this is itself subject to the non-determinism below: one run of `HPARAM_RANGE(2, 10)` selected the domain-correct answer (3, matching the 3 real penguin species in the training data) as optimal; a separate run of the identical tuning config selected 2 instead. Don't treat a single tuning run's chosen `num_clusters` as definitive — if the choice matters, tune more than once (or with more trials) and look for a value that wins consistently.
- HP tuning can be expensive/slow (e.g. tens of trials over hundreds of thousands of rows ran ~46 min in the repo example) — bound `num_trials` and use `max_parallel_trials`.
- Exclude id/label columns from the feature set (`SELECT * EXCEPT(...)`).
- **Verified: K-means retraining is genuinely non-deterministic, even with `kmeans_init_method = 'KMEANS++'` (`models/kmeans/`).** Retraining the identical `CREATE OR REPLACE MODEL` statement (same SQL, same options, no seed exposed) multiple times produced meaningfully different `davies_bouldin_index` values each time (observed range ~0.87–1.02 on a 342-row dataset) and different specific cluster-to-external-label alignment (which cluster cleanly separates a given group shifted between runs) — a third independent training via `bigframes.ml.cluster.KMeans` on the same config reproduced yet a different value again. **Practical implication: a single before/after comparison (e.g. "does adding this feature improve clustering?") is not reliable evidence of a causal effect** — the same magnitude of change can come from ordinary retraining variance. Retrain each configuration multiple times and look at the range before drawing a conclusion.
- **Verified, still true independent of the point above: a lower `davies_bouldin_index` does NOT by itself mean more meaningful clusters.** It only measures internal cluster separation/compactness in whatever feature space you give it — it says nothing about whether clusters line up with any domain-meaningful grouping. When you have any external signal to check against (even one not used in training), use it — don't rely on the intrinsic metric alone to judge whether a clustering is useful, and combine it with the non-determinism point above (check the metric's range across retrains, not a single value) before trusting any comparison.

**Limitations:**
- No supervised metrics or feature attributions (unsupervised).
- `kmeans_init_col` (CUSTOM) requires exactly `num_clusters` TRUE rows.
- `COSINE` distance changes geometry — choose deliberately.
- **Verified gotcha: `ML.DETECT_ANOMALIES`'s input-data argument is REQUIRED for `KMEANS`, not optional.** Calling it with only `(MODEL, STRUCT(contamination))` (2 arguments) errors immediately: `"DETECT_ANOMALIES expects 3 arguments for KMEANS models but 2 were passed."` Always pass the scoring data as the 3rd argument. Verified since on `models/pca/` and `models/autoencoder/` as well: the requirement is not KMEANS-specific — it holds for all three IID model types, with the model name substituted into the same error. See the general `ML.DETECT_ANOMALIES` entry, whose syntax block shows the 3-argument form but does not mark it mandatory.
- HP-tuned models return per-trial rows in `ML.EVALUATE`/`ML.PREDICT`; downstream queries must handle/filter `trial_id`.

**Locations:** Available in all BigQuery ML regions/multi-regions; no special location constraint (no connection required).

**BigFrames API:** `bigframes.ml.cluster.KMeans` — e.g. `KMeans(n_clusters=4).fit(X)` then `.predict(X)`.

**Repo example (tested):**
- `data+ai/bq-ml/models/kmeans/` — `KMEANS` on `penguins` with `num_clusters` swept via `HPARAM_RANGE` and `standardize_features=TRUE`, tuned across trials; covers `ML.EVALUATE`, `ML.CENTROIDS`, `ML.TRIAL_INFO`, `ML.FEATURE_INFO`, `ML.PREDICT`, and `ML.DETECT_ANOMALIES` (with `contamination`).
- `data+ai/bq-ml/workflows/customer_segmentation/customer_segmentation.ipynb` — the same model type on a real problem: RFM (recency/frequency/monetary) features engineered from raw `thelook_ecommerce` order history, then `KMEANS` at a fixed `num_clusters = 4`. The deliberate contrast with `models/kmeans/`'s `penguins` run is mechanism demo vs. applied segmentation.
- `EXPORT MODEL` (a `KMEANS` model exports as a TensorFlow SavedModel) and Endpoint serving are covered in `data+ai/bq-ml/models/export/` and `data+ai/bq-ml/models/remote/`.


---

## `PCA`
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

**BigFrames API:** `bigframes.ml.decomposition.PCA` (`n_components` maps to `num_principal_components`, `svd_solver` maps to `pca_solver`). **Verified: `.fit(X)` then `.predict(X)`** — unlike scikit-learn, there is no `.transform()`/`.fit_transform()`; `.predict()` returns the projected components, matching `ML.PREDICT`'s convention. `.score(X)` returns `total_explained_variance_ratio`, matching `ML.EVALUATE` (`models/pca/`).

**Verified (`models/pca/`):**
- **PCA is fully deterministic** — retraining the identical `CREATE OR REPLACE MODEL` statement (same SQL, same options) reproduces `total_explained_variance_ratio` bit-for-bit every time. Unlike `KMEANS` (see its entry above), PCA is a closed-form eigendecomposition with no random initialization, so there's no retraining variance to guard against. A third independent confirmation: training via `bigframes.ml.decomposition.PCA` — a completely different, independently-named model — reproduces the exact same value again, a contrast to `KMEANS`, where BigFrames' independently-trained model produces yet a different value each time.
- **MAJOR NUANCE (verified live, `workflows/anomaly_fraud_detection/`):** the determinism above covers `ML.EVALUATE`'s own metric — it does **not** guarantee stable *downstream* `ML.DETECT_ANOMALIES` results when using `pca_explained_variance_ratio` (a variable component **count**, chosen to hit a variance target) instead of a fixed `num_principal_components`. On a 30-feature, 284K-row real dataset, three otherwise-identical retrainings with `pca_explained_variance_ratio = 0.95` produced true-positive counts of 3, 235, and 279 (out of 492 known anomalies) — even though `total_explained_variance_ratio` stayed bit-for-bit stable (~0.95473) across all three. Near-threshold eigenvalues can flip exactly which components get retained between runs, which swings per-row reconstruction error dramatically despite the aggregate captured variance looking identical. **Mitigation:** use a fixed `num_principal_components` instead — substantially more stable across retrainings (two independent runs both landed in a TP=114-132 range, versus the 3-279 swing above).
- **`principal_component_id` (in `ML.PRINCIPAL_COMPONENTS`/`ML.PRINCIPAL_COMPONENT_INFO`) is 0-indexed** (0, 1, 2, ...) — unlike `KMEANS`' `centroid_id`, which is 1-indexed, and unlike `ML.PREDICT`'s own output columns (`principal_component_1`, `principal_component_2`, ...), which are 1-indexed. Don't assume a consistent indexing convention across unsupervised model types or even within the same model type's own functions.
- **`ML.DETECT_ANOMALIES` requires the 3rd (input-data) argument for PCA**, same as `KMEANS` — see the general `ML.DETECT_ANOMALIES` entry.
- **`ML.GENERATE_EMBEDDING` on a PCA model** wraps `ML.PREDICT`'s projection into a single `ml_generate_embedding_result` ARRAY<FLOAT> column; the array values match `ML.PREDICT`'s `principal_component_1`/`principal_component_2` columns exactly, in order.

**Repo example (tested):**
- `data+ai/bq-ml/models/pca/` — `model_type='PCA'` on `penguins`, covering `ML.EVALUATE` (`total_explained_variance_ratio`), `ML.PRINCIPAL_COMPONENT_INFO`, `ML.PRINCIPAL_COMPONENTS`, `ML.PREDICT` (per-row component projections), `ML.GENERATE_EMBEDDING`, `ML.FEATURE_INFO`, and `ML.DETECT_ANOMALIES` with an explicit `contamination`.
- `data+ai/bq-ml/workflows/anomaly_fraud_detection/anomaly_fraud_detection.ipynb` — the same technique used for real fraud detection on `bigquery-public-data.ml_datasets.ulb_fraud_detection`, with `contamination` set from the training fraud rate and precision/recall scored against the true label, alongside `AUTOENCODER` and a supervised `BOOSTED_TREE_CLASSIFIER`.
- `data+ai/bq-ml/functions/distance/` — uses a `PCA` model's projections as the input to `ML.DISTANCE` / `ML.LP_NORM` / `ML.NORMALIZER`.
- `EXPORT MODEL` (`PCA` exports as a TensorFlow SavedModel) and Endpoint deployment: `data+ai/bq-ml/models/export/` and `data+ai/bq-ml/models/remote/`.

**Repo example (tested):** `data+ai/bq-ml/workflows/anomaly_fraud_detection/anomaly_fraud_detection.ipynb` — trains `PCA` with `num_principal_components=10` on `bigquery-public-data.ml_datasets.ulb_fraud_detection` (the real ULB/Kaggle fraud dataset, 492 genuine fraud cases) and measures real precision/recall against the true `Class` label — the source of the `pca_explained_variance_ratio` non-determinism finding above; contrasts with `AUTOENCODER` and a supervised `BOOSTED_TREE_CLASSIFIER`.


---

## `AUTOENCODER`
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

**Supported lifecycle functions:** `ML.EVALUATE`, `ML.RECONSTRUCTION_LOSS`, `ML.PREDICT` (returns `latent_col_N` latent vector + input columns), [`ML.GENERATE_EMBEDDING`](../../bq-ai-functions/RESOURCES.md) (latent space as a single `ml_generate_embedding_result` ARRAY — in-scope here as a lifecycle use of a trained BQML model), `ML.DETECT_ANOMALIES` (with `STRUCT(<contamination> AS contamination)`), `ML.FEATURE_INFO`, `ML.TRAINING_INFO`, `ML.TRIAL_INFO` (HP tuning), `EXPORT MODEL`. Pair with `ML.NORMALIZER` + `VECTOR_SEARCH` for similarity. No `ML.WEIGHTS`/`ML.GLOBAL_EXPLAIN`/`ML.CONFUSION_MATRIX`/`ML.ROC_CURVE`/`ML.CENTROIDS`/`ML.PRINCIPAL_COMPONENTS`.

**ML.EVALUATE output metrics (this type):** `mean_absolute_error`, `mean_squared_error`, `mean_squared_log_error`. (For HP-tuned models the output also includes a `trial_id` column, one row per trial.) `ML.RECONSTRUCTION_LOSS` returns the same three metric columns **per input row** (plus `trial_id` for tuned models) alongside the input columns.

**Preprocessing support:** automatic (standardization of numeric features) | manual | TRANSFORM (supported; if TRANSFORM is used, `ML.PREDICT`/`ML.RECONSTRUCTION_LOSS` accept only the pre-TRANSFORM input columns).

**Hyperparameter tuning:** Supported. Set `num_trials` and use `HPARAM_RANGE`/`HPARAM_CANDIDATES` on `hidden_units`, `activation_fn`, `batch_size`, `dropout`, `learn_rate`, `optimizer`, `l1_reg_activation`. Default algorithm `VIZIER_DEFAULT` (Vertex AI Vizier); objective defaults to the key metric, override with `hparam_tuning_objectives` (e.g. `mean_absolute_error`). Recommended trials >= 10 x number of tuned hyperparameters. Tuned models expose results via `ML.TRIAL_INFO` and add a `trial_id` column to evaluate/predict output.

**Explainability / weights:** None of `ML.WEIGHTS`, `ML.ADVANCED_WEIGHTS`, `ML.GLOBAL_EXPLAIN`, `ML.FEATURE_IMPORTANCE`, or `ML.EXPLAIN_PREDICT` apply (`enable_global_explain` not supported for autoencoders). Interpretability comes from per-row reconstruction loss and the latent representation.

**Best practices:**
- Set the latent dimension via the middle of `hidden_units` (e.g. `[128,64,8,64,128]` => 8-dim latent / embedding).
- Train on clean/normal data only for anomaly detection; pass the expected fraud/anomaly rate as `contamination` to `ML.DETECT_ANOMALIES`.
- **Verified: `ML.NORMALIZER` + `DOT_PRODUCT` is unnecessary for `VECTOR_SEARCH`** — `distance_type='COSINE'` on the raw, un-normalized `ML.GENERATE_EMBEDDING` output gives mathematically equivalent rankings (`COSINE` distance = `1 - cosine_similarity` = `DOT_PRODUCT` distance on unit vectors, up to sign) without a manual normalization step. Reach for `ML.NORMALIZER` only if you need normalized vectors for something other than `VECTOR_SEARCH`, or need `DOT_PRODUCT` specifically (e.g. a vector index type that doesn't support `COSINE`).
- HP tuning scans large data per trial — autoencoder training is compute/byte heavy (the repo example processed ~1.9 TB across 40 trials); cap `num_trials`/`max_parallel_trials` and use `early_stop`.

**Limitations:**
- Unsupervised — no label column; exclude id/label/split columns from the training SELECT.
- No model weight/feature-attribution functions; no `enable_global_explain`.
- `ML.RECONSTRUCTION_LOSS` does not support imported TensorFlow models.
- Exported model is TensorFlow SavedModel format.

**Locations:** Available in BigQuery ML regions/multi-regions; Vertex AI registration/online serving requires a matching Vertex AI region (notebooks use `us-central1`).

**BigFrames API:** `bigframes.ml.imported`/`bigframes.ml.decomposition` have no direct autoencoder class; no direct BigFrames equivalent — use SQL `CREATE MODEL ... AUTOENCODER` (confirmed against the live BigFrames API reference, `models/autoencoder/`).

**Verified (`models/autoencoder/`):**
- **The default `activation_fn = 'RELU'` genuinely breaks small, narrow networks — a real dying-ReLU collapse, not a theoretical concern.** On a `hidden_units = [3, 2, 3]` network (2-dim latent), a substantial and highly variable share of rows have BOTH latent dimensions simultaneously clipped to exactly `0.0` — verified across three independent retrains, with wildly different severity each time (observed `n_both_zero`/`n_total` rates: 40%, 50%, 65%) and different specific shapes (sometimes one entire latent column pinned to `0.0` for every row, sometimes the zeros spread unevenly across both columns). `ML.EVALUATE`'s aggregate metrics look like a normally-trained model every time — the collapse is only visible by directly inspecting `ML.PREDICT`'s `latent_col_*` output. **Fix: switch `activation_fn` to `'TANH'`** (no dead zone) — this fixed the collapse every time it was tested and consistently landed `mean_squared_error` around ~0.21, well below the RELU baseline's own highly variable range (~0.66-0.94 observed) — the exact improvement ratio isn't fixed (it depends on how badly RELU happened to collapse that retrain), but the direction and TANH's ~0.21 landing point are consistent.
- **`ML.EVALUATE`'s reconstruction metrics are reproducible bit-for-bit under a fixed model name** (same as `DNN_*`), but the **latent-space values are not** — two retrains of the identical model produced identical aggregate metrics but different specific `latent_col_*` values/ranges. Unlike `PCA`'s uniquely-ordered, variance-ranked components, a generic autoencoder bottleneck has no constraint forcing a stable, canonical basis — any invertible transform of the latent space paired with the inverse transform in the decoder reconstructs identically. Don't treat individual `latent_col_N` values as stable/comparable across retrains the way `PCA`'s `principal_component_N` is.
- **`ML.DETECT_ANOMALIES` requires the 3rd (input-data) argument for `AUTOENCODER` too** — same as `KMEANS` and `PCA`; all three unsupervised model types in this project share this requirement.
- **HP tuning over `activation_fn`/`learn_rate` did NOT reliably confirm `TANH` beats `RELU` — a claim from initial testing that did not survive retesting.** One 4-trial run sampled mostly `TANH` and found it winning; a second 4-trial run (the real notebook execution) sampled mostly `RELU` and found a `RELU` trial winning instead, with **all 4 trials scoring worse than both the untuned RELU baseline and the untuned TANH fix**. With only 4 trials spread across two hyperparameters simultaneously, the search is too sparse to reliably explore either dimension — the same small-trial-budget limitation already documented for `DNN_*`. The direct, controlled, same-`learn_rate` comparison (RELU vs. TANH, nothing else changed) remains the reliable evidence that TANH fixes the collapse; a small-budget joint HP search over both hyperparameters does not reproduce that conclusion reliably and shouldn't be read as confirming or refuting it either way.
- **`ML.GENERATE_EMBEDDING` does NOT normalize its output.** Its raw `ml_generate_embedding_result` is bit-for-bit identical to `ML.PREDICT`'s un-normalized latent columns — confirmed by applying `ML.NORMALIZER` independently to both and getting the exact same normalized vector either way. Its real convenience over the manual `ML.PREDICT` + hand-built `ARRAY[latent_col_1, ...]` path is not having to enumerate the latent columns yourself, not automatic normalization.
- **`VECTOR_SEARCH` does not accept `ML.PREDICT`/`ML.GENERATE_EMBEDDING` output directly as its base-table argument** (`"Unsupported query pattern"`) — materialize embeddings into a real table first.
- **Manually normalizing + `DOT_PRODUCT` is unnecessary** — `distance_type='COSINE'` on the raw `ML.GENERATE_EMBEDDING` output gives mathematically equivalent `VECTOR_SEARCH` rankings (verified: identical top-k neighbors, with distances that convert exactly via `COSINE = 1 - cosine_similarity` and `DOT_PRODUCT = -cosine_similarity` on unit vectors).

**Repo example (tested):**
- `data+ai/bq-ml/models/autoencoder/` — full lifecycle on `penguins`: HP-tuned `AUTOENCODER` (`HPARAM_CANDIDATES`/`HPARAM_RANGE` over `num_trials`), `ML.FEATURE_INFO`, `ML.TRIAL_INFO`, `ML.EVALUATE`, `ML.RECONSTRUCTION_LOSS`, `ML.PREDICT` (the `latent_col_*` outputs), and `ML.DETECT_ANOMALIES` with `contamination`. The same notebook covers the second use of this model type — the latent space *as* a table embedding, via `ML.GENERATE_EMBEDDING` plus `ML.NORMALIZER`, then `VECTOR_SEARCH` for row-to-row similarity.
- `EXPORT MODEL` (`AUTOENCODER` exports as a TensorFlow SavedModel) and Endpoint serving: `data+ai/bq-ml/models/export/` and `data+ai/bq-ml/models/remote/`.
- `data+ai/bq-ml/workflows/anomaly_fraud_detection/anomaly_fraud_detection.ipynb` — trains on the real ULB/Kaggle fraud dataset (`bigquery-public-data.ml_datasets.ulb_fraud_detection`, 492 genuine fraud cases) and measures real precision/recall against the true label — contrasts with `PCA` (comparable performance here, not dramatically different) and a supervised `BOOSTED_TREE_CLASSIFIER` (far higher recall).


---

## `MATRIX_FACTORIZATION`
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
- Output volume from `ML.RECOMMEND` can be very large (full sparse matrix).

**Locations:** Model-type availability varies by region; check [BigQuery ML locations](https://cloud.google.com/bigquery/docs/locations). Reservation availability in the model's region is required (see pricing note).

**BigFrames API:** `bigframes.ml.decomposition.MatrixFactorization(feedback_type=..., num_factors=..., user_col=..., item_col=..., rating_col=..., l2_reg=...)` — `.fit(X)` on a single (user, item, rating) DataFrame (all three columns together, no separate `y`), then `.score(X)` for evaluation metrics. **Verified: no `wals_alpha` parameter exists on this wrapper** (confirmed via the live installed constructor signature) — for `feedback_type='implicit'`, BigFrames always uses BigQuery ML's default `wals_alpha` (40) with no way to override it; use SQL directly if you need to tune it.

**Verified (`models/matrix_factorization/`):**
- **The on-demand pricing block is real and immediate** — `CREATE MODEL` without a reservation fails instantly with `"Training Matrix Factorization models is not available for on-demand usage."` This is the only model type in this project that hits this error.
- **The reservation's edition matters, not just its existence.** A `STANDARD` edition reservation still fails to train — with a *different* error: `"Using BQML related functionalities is disallowed in STANDARD edition."` `ENTERPRISE` (or higher) is required for any BQML training. A `STANDARD`-edition reservation is otherwise valid for regular `QUERY` jobs — it's specifically BQML that's blocked.
- **No capacity commitment is required** — a reservation created with `--edition=ENTERPRISE --autoscale_max_slots=N` (no `--capacity_commitment` flag; baseline `--slots=0`) is a pay-per-second, no-minimum-term BigQuery Editions reservation, and is sufficient to unblock `MATRIX_FACTORIZATION` training.
- **A freshly created reservation assignment needs time to propagate** — `CREATE MODEL` failed on the first attempt immediately after creating and assigning a brand-new reservation, and succeeded only after waiting (~90 seconds observed).
- **Real, measured cost:** building and validating this notebook (one base model, one 4-trial tuning job, one BigFrames retrain) consumed ~6.4 cumulative slot-hours under `ENTERPRISE` autoscale. Check current BigQuery Editions pricing before running — this is not a hypothetical cost like every other on-demand model type in this project.
- **Cold start does NOT error, contradicting the intuitive reading of "cannot recommend for absent users/items."** Calling `ML.RECOMMEND` with a `user_col`/`item_col` value never seen in training returns a full ranked list with no error — verified by comparing a confirmed real trained user's recommendations against an obviously fake user ID, which produced a completely different (but still populated) top-5 list, consistent with the unseen entity falling back to item-side bias/popularity alone rather than genuine personalization.
- **`ML.WEIGHTS` includes one extra row beyond per-user/per-item factors**: `processed_input=NULL`, `feature='global__INTERCEPT__'` — the single global bias term, separate from every user's/item's own intercept.
- **`ML.GENERATE_EMBEDDING` has a different argument count for this model type than PCA/AUTOENCODER.** It takes ONLY the model — no input table/query argument. Passing one errors: `"Function ML.GENERATE_EMBEDDING for MATRIX_FACTORIZATION models only expects 1 argument but 2 were passed."` It returns embeddings for every user AND item in the model in a single call (`processed_input`/`feature`/`ml_generate_embedding_result`), mirroring `ML.WEIGHTS`' shape rather than `ML.PREDICT`'s per-query-row shape.
- **The embedding array has `num_factors + 1` elements, not `num_factors`** — verified: with `num_factors=16`, `ML.GENERATE_EMBEDDING`'s array had 17 elements, one more than `ML.WEIGHTS`' `factor_weights` array for the same model (confirmed 16 elements there). The extra element is almost certainly the per-user/per-item `intercept` appended onto the raw factor vector. Don't assume the embedding array length equals `num_factors` for this model type.
- **`ML.EVALUATE` on a tuned model takes no `STRUCT(trial_id)` argument** — unlike `ML.RECOMMEND`, which accepts one. Calling `ML.EVALUATE(MODEL, STRUCT(trial_id AS trial_id))` errors (`"argument 2 must be a relation"`); calling `ML.EVALUATE(MODEL)` alone returns every trial's metrics in one result, one row per `trial_id`.
- **`ML.TRAINING_INFO`'s `eval_loss` column is `NULL` throughout** for this model type, unlike the supervised model types in this project.
- **Retraining shows measurable variance, similar to `KMEANS`/`RANDOM_FOREST_*`.** Retraining the identical `CREATE OR REPLACE MODEL` statement (same name, same SQL) does not reproduce `mean_average_precision` exactly — observed 0.873 and 0.860 across two runs. Unlike `PCA` (fully deterministic) or the `DNN_*` family (bit-for-bit reproducible under a fixed name), matrix factorization's WALS training has real run-to-run variance.
- **HP tuning produced a genuine, positive result in every run tested — though not with reproducible exact numbers.** 4 trials over `num_factors`/`l2_reg`/`wals_alpha` beat the untuned baseline both times, but the specific winning config and margin varied: one run's best trial reached `mean_average_precision=0.899` against a `0.860` baseline; a separate run's best trial reached `0.915` against a `0.873` baseline (same `num_factors`/`l2_reg`, a different `wals_alpha`). The qualitative finding — tuning beats the untuned baseline — held both times; the exact numbers didn't. A real contrast either way to `models/autoencoder/`'s equally-sized 4-trial search, which failed to beat its own untuned baseline at all.

**Repo example (tested):** `data+ai/bq-ml/models/matrix_factorization/` — full lifecycle on `bigquery-public-data.google_analytics_sample` (IMPLICIT feedback), including the temporary-reservation setup/teardown pattern this model type forces on you. `data+ai/bq-ml/workflows/recommendation/` then applies it end-to-end. The on-demand pricing exception is documented in *Pricing/slots* and *Limitations* above — this is the one model type that cannot train under on-demand pricing at all.

---

### `ML.RECOMMEND` (inference function for this model type)

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

## `ARIMA_PLUS`  (univariate time series forecasting)

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

> **Cross-links (owned by `../bq-ai-functions/`, not duplicated here):** TimesFM foundation-model forecasting — [`AI.FORECAST`, `AI.EVALUATE`, `AI.DETECT_ANOMALIES`](../../bq-ai-functions/RESOURCES.md). For the multivariate variant with external regressors, see `ARIMA_PLUS_XREG` ([CREATE MODEL ARIMA_PLUS_XREG](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-multivariate-time-series)).

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
`ML.FORECAST` (forecast + intervals), `ML.EXPLAIN_FORECAST` (forecast + decomposition; needs `decompose_time_series=TRUE`; **verified incompatible with `forecast_limit_lower_bound`/`forecast_limit_upper_bound`** — see GOTCHA below), `ML.EVALUATE` (forecast accuracy metrics, optional eval data), `ML.ARIMA_EVALUATE` (per-series model selection diagnostics), `ML.ARIMA_COEFFICIENTS` (AR/MA coefficients + drift), `ML.DETECT_ANOMALIES` (anomaly probability per point), `ML.FEATURE_INFO`, `ML.TRAINING_INFO`, `ML.HOLIDAY_INFO` (modeled holidays when `holiday_region` set). Not applicable: `ML.PREDICT`, `ML.GLOBAL_EXPLAIN`, `ML.WEIGHTS`, `ML.CONFUSION_MATRIX`, `ML.ROC_CURVE`, `ML.CENTROIDS`.

**GOTCHA (verified): `forecast_limit_lower_bound`/`forecast_limit_upper_bound` are incompatible with `ML.EXPLAIN_FORECAST`.** A model trained with either bound set fails `ML.EXPLAIN_FORECAST` with `"This model was trained with either 'forecast_limit_lower_bound' or 'forecast_limit_upper_bound' being specified. In this case, EXPLAIN_FORECAST is not supported."` `ML.FORECAST` and every other lifecycle function are unaffected — only `ML.EXPLAIN_FORECAST` is blocked. Not documented in the official options reference. If a notebook/pipeline needs both a forecast floor/ceiling and decomposition, they require two separate models.

**`hierarchical_time_series_cols` — verified mechanics.** Given an ordered list of grouping columns (e.g. `['neighborhood', 'station']`), `CREATE MODEL` trains the base-level series as usual, then `ML.FORECAST`/`ML.EVALUATE` return one row per hierarchy level: base-level rows (every id column set), each intermediate rollup level (finer id columns `NULL`), and one overall-total row (all id columns `NULL`). **Verified directly (exact match to the penny, every forecast day): reconciliation is bottom-up only** — the rolled-up value at any level is the plain sum of its children's forecasts; the base-level forecasts themselves are never adjusted to make higher levels more accurate. There is no built-in top-down option (disaggregating a higher-level forecast down through the hierarchy) — that requires a custom implementation; see `workflows/hierarchical_forecasting/` for a from-scratch top-down (forecast-proportions) approach compared against this built-in bottom-up one.

**ML.EVALUATE output metrics (this type):** `mean_absolute_error`, `mean_squared_error`, `root_mean_squared_error`, `mean_absolute_percentage_error`, `symmetric_mean_absolute_percentage_error`, and **`mean_absolute_scaled_error`** (verified present in a real call with explicit eval data + `perform_aggregation=TRUE` — not previously listed here). Metric granularity depends on inputs: with eval data and `perform_aggregation = TRUE` (default), metrics are per `time_series_id_col`; with `FALSE`, per timestamp. Without eval data, ARIMA-fit metrics (e.g. AIC, variance, log_likelihood) are returned per series instead — same shape as `ML.ARIMA_EVALUATE`, confirmed identical.

**ML.ARIMA_EVALUATE output columns:** `non_seasonal_p`, `non_seasonal_d`, `non_seasonal_q`, `has_drift`, `log_likelihood`, `AIC`, `variance`, `seasonal_periods` (e.g. `[WEEKLY, YEARLY]` or `[NO_SEASONALITY]`), `has_holiday_effect`, `has_spikes_and_dips`, `has_step_changes`, `error_message` (+ the id column). `show_all_candidate_models` (BOOL, default FALSE) returns every candidate instead of only the selected model.

**ML.FORECAST output columns:** id col, `forecast_timestamp`, `forecast_value`, `standard_error`, `confidence_level`, `prediction_interval_lower_bound`, `prediction_interval_upper_bound`, `confidence_interval_lower_bound`, `confidence_interval_upper_bound`. Args: `STRUCT(<n> AS horizon, <p> AS confidence_level)` — default `horizon` is 3, so set it to the trained horizon.

**ML.EXPLAIN_FORECAST adds:** `time_series_type` (`history`/`forecast`), `time_series_data`, `time_series_adjusted_data`, plus decomposition columns `trend`, `seasonal_period_{weekly,daily,monthly,quarterly,yearly}`, `holiday_effect` (and per-holiday columns like `holiday_effect_US_Thanksgiving`), `spikes_and_dips`, `step_changes`.

**Preprocessing support:** Automatic (the entire ARIMA_PLUS pipeline). `TRANSFORM` is supported but **not** when doing custom holiday modeling.

**Hyperparameter tuning:** N/A in the `num_trials` sense. Built-in auto.ARIMA search; tune via `auto_arima_max_order`/`auto_arima_min_order`. `non_seasonal_order` disables the search for a single series.

**Explainability / weights:** No `ML.WEIGHTS`/`ML.GLOBAL_EXPLAIN`/`ML.FEATURE_IMPORTANCE`. Explainability is via `ML.EXPLAIN_FORECAST` (time series decomposition) and `ML.ARIMA_COEFFICIENTS` (`ar_coefficients`, `ma_coefficients`, `intercept_or_drift`).

**Custom holiday modeling (verified, exact syntax):** `holiday_region` only covers built-in regional holidays. To model an event that matters for a specific series but isn't a public holiday, `CREATE MODEL`'s `AS` clause takes a special two-block form — **no `WITH` keyword**, and `training_data`/`custom_holiday` are required block names (not ordinary CTEs you can rename):
```sql
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.MODEL_NAME`
OPTIONS(model_type = 'ARIMA_PLUS', holiday_region = 'US', time_series_timestamp_col = 'date', time_series_data_col = 'value', horizon = 7)
AS (
  training_data AS (
    SELECT date, value FROM `PROJECT_ID.DATASET.SOURCE_TABLE`
  ),
  custom_holiday AS (
    SELECT 'US' AS region, 'MyEvent' AS holiday_name, primary_date, 1 AS preholiday_days, 1 AS postholiday_days
    FROM UNNEST([DATE('2016-11-06'), DATE('2017-11-05')]) AS primary_date
  )
);
```
`custom_holiday` columns: `region` (existing region code to supplement, or an arbitrary custom region name), `holiday_name` (must be a valid column-name string — no spaces, since it becomes `holiday_effect_<holiday_name>` in `ML.EXPLAIN_FORECAST`), `primary_date`, `preholiday_days`/`postholiday_days` (window size, ≥1). Verified: `ML.HOLIDAY_INFO` lists the custom holiday alongside built-ins, and `ML.EXPLAIN_FORECAST` gains a `holiday_effect_<holiday_name>` column. Can combine with `time_series_id_col` for multi-series. Max 50,000 rows in the `custom_holiday` query.

**Manual ARIMA order (verified):** `auto_arima = FALSE` with `non_seasonal_order = STRUCT(<p> AS p, <d> AS d, <q> AS q)` pins an exact order instead of searching — confirmed `ML.ARIMA_EVALUATE` reports back exactly the specified `(p,d,q)`. Single-series only (fails with `time_series_id_col`).

**Best practices:**
- ARIMA+ is univariate and ignores a validation split — fold any `VALIDATE` rows into the training data. [`models/arima_plus/`](../models/arima_plus/) uses a plain two-way TRAIN/TEST split for exactly this reason.
- Set `horizon` at training to cover test + future; remember `ML.FORECAST`/`ML.EXPLAIN_FORECAST` default `horizon` is 3.
- For 10k+ series, first time a 1k-series query to estimate cost/runtime; lower `auto_arima_max_order` to cut runtime (1 vs 2 cuts runtime >50%); use `time_series_length_fraction`/`max_time_series_length` to trim trend-modeling points; wrap in multi-statement queries.
- Cost scales with the number of candidate models (`auto_arima_max_order`/`min_order`) since input bytes are multiplied per candidate.
- Use `forecast_limit_lower_bound = 0` for non-negative demand — but only on a model where `ML.EXPLAIN_FORECAST` isn't needed (see the `ML.EXPLAIN_FORECAST` incompatibility GOTCHA above); `ML.FORECAST` still works fine with a bound set.

**Limitations:**
- Min series length 3 time points. Max length 500,000 points when `decompose_time_series=TRUE`, 1,000,000 when FALSE (per series). Max series simultaneously: 100,000,000. Max forecast points: 10,000.
- Holiday effect modeling only for DAILY/WEEKLY series longer than ~1 year; effective for ~5 years. Custom holidays only for `DAILY`/`AUTO_FREQUENCY`(daily) and not with `TRANSFORM`.
- Will **not** aggregate to a coarser granularity: requesting `data_frequency='WEEKLY'` on daily data errors `400 Invalid time series: All input time intervals must be no less than the interval unit specified by data_frequency (WEEKLY)`. Requesting a *finer* granularity (e.g. `HOURLY` on daily data) is allowed and interpolates the gaps.
- Missing/absent time points (null values or absent rows) are linearly interpolated between observed values based on the detected/declared frequency. **Verified: this has no special-case handling for very long gaps** — a real ~6-month gap (confirmed in `bigquery-public-data.new_york_citibike.citibike_trips`, October 2016 – March 2017) is linearly interpolated across its *entire* span with no different treatment than a 1-2 day gap (confirmed: a station's value declined by a constant per-day amount for all ~183 missing days, in `ML.DETECT_ANOMALIES`'s and `ML.EXPLAIN_FORECAST`'s output `time_series_data`) — a straight 6-month line necessarily discards all the weekly/seasonal structure that would have occurred in between. Treat any value inside a long gap as a crude placeholder, not a real observation.
- Invalid series (e.g. single point) are silently skipped from forecasts; retrieve their `error_message` via `ML.ARIMA_EVALUATE`.

**Locations:** Available in BigQuery ML non-remote-model locations (regions and multi-regions). See "Locations for non-remote models."

**BigFrames API:** [`bigframes.ml.forecasting.ARIMAPlus`](https://cloud.google.com/python/docs/reference/bigframes/latest/bigframes.ml.forecasting.ARIMAPlus) — `model = ARIMAPlus(horizon=..., auto_arima=True, data_frequency="daily", holiday_region=...)`, `model.fit(X_timestamp_df, y_value_df)`, then `model.predict(horizon=..., confidence_level=0.95)` (= `ML.FORECAST`), `model.predict_explain(...)` (= `ML.EXPLAIN_FORECAST`), `model.coef_` (= `ML.ARIMA_COEFFICIENTS`), `model.register(...)`.

**Repo example (tested):**
- `data+ai/bq-ml/functions/time_series/` — the model-free `ML.TREND`, `ML.SEASONALITY`, and `ML.DETECT_CHANGE_POINTS` on the same Citi Bike series, for the questions that need no `CREATE MODEL` at all.
- The interpolation and granularity behavior — missing/absent points linearly interpolated, `WEEKLY` requested on daily data rejected, `HOURLY` on daily interpolated — is stated in *Limitations* above and verified in `models/arima_plus/`; there is no separate notebook for it.
- This project's own `models/arima_plus/` — from-scratch build on 5 real `bigquery-public-data.new_york_citibike.citibike_trips` stations (daily trip counts), single-series then multi-series via `time_series_id_col`; folds the granularity/missing-data gotchas above into the main notebook (verified a real gap day's linearly-interpolated value exactly: `(141+363)/2=252`) rather than keeping them in a separate notes file; adds a dedicated step verifying the custom-holiday syntax, manual `non_seasonal_order`, `forecast_limit_lower_bound` (as small standalone single-station models, kept separate from the main model specifically because of the `ML.EXPLAIN_FORECAST` incompatibility above — discovered when the main model was first built with the bound set and `ML.EXPLAIN_FORECAST` broke), and `hierarchical_time_series_cols` (a separate 6-station table grouped into 2 real Manhattan neighborhoods, since the main 5-station table has no real hierarchy) — verified bottom-up reconciliation exact to the penny at every level.
- `data+ai/bq-ml/workflows/hierarchical_forecasting/` — hierarchical forecasting on `bigquery-public-data.iowa_liquor_sales.sales` (real State/County/City/Store hierarchy): built-in bottom-up reconciliation via `hierarchical_time_series_cols`, compared head-to-head at every hierarchy level against a from-scratch top-down disaggregation (forecast proportions) that BigQuery ML has no built-in option for. Uses weekly granularity — real per-store *daily* coverage is only ~15-30%, so daily would force heavy interpolation. Modernizes and replaces the retired `Applied ML/Forecasting/BigQuery ML For Hierarchical Forecasting.ipynb`, deleted 2026-07-21 after the rebuild was verified feature-for-feature.


---

## `ARIMA_PLUS_XREG`  (multivariate time series with external regressors)
- **Description:** Multivariate time-series forecasting model = an `ARIMA_PLUS` model plus *linear external regressors* (side features / covariates). Internally it fits a linear regression on the supplied covariates and models the regression residuals with the full `ARIMA_PLUS` pipeline (auto-ARIMA order selection, holiday effects, spike/dip cleaning, step-change adjustment, seasonal & trend decomposition). Conceptually "ARIMAX": ARIMA's `p`/`d`/`q` plus `b` linear-regressor weights.
- **When to use:**
  - You have a target series **and** time-varying covariates (e.g. promotions, weather, capacity) that improve forecast accuracy.
  - Covariate values **are known/available for the forecast horizon** (required at forecast time — see Limitations).
  - You want ARIMA_PLUS automation (holidays, seasonality, anomaly handling) but with explanatory regressors.
  - You want per-regressor attributions in the forecast (`ML.EXPLAIN_FORECAST`).
- **Category:** time-series.
- **Connection required:** No.
- **Status:** GA. Multiple-series support via `time_series_id_col` and `ML.DETECT_ANOMALIES` support were both added after the original 2023 Preview; both are exercised live in [`models/arima_plus_xreg/`](../models/arima_plus_xreg/) (Example 2 trains all five stations as one multi-series model; Example 10 runs `ML.DETECT_ANOMALIES` against it).
- **documentation:** [CREATE MODEL for ARIMA_PLUS_XREG](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-multivariate-time-series) · journey/tutorials: [single series tutorial](https://cloud.google.com/bigquery/docs/arima-plus-xreg-single-time-series-forecasting-tutorial), [multiple series tutorial](https://cloud.google.com/bigquery/docs/arima-plus-xreg-multiple-time-series-forecasting-tutorial), [E2E user journey](https://cloud.google.com/bigquery/docs/e2e-journey). Related univariate model: [`ARIMA_PLUS`](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-time-series).

> Built-in foundation forecasting (TimesFM via `AI.FORECAST`) is owned by `../bq-ai-functions/` — see [AI.FORECAST / AI.DETECT_ANOMALIES there](../../bq-ai-functions/RESOURCES.md). `ARIMA_PLUS_XREG` is the in-scope BQML *trained-model* forecaster.

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

**ML.EVALUATE output metrics (this type):** `mean_absolute_error`, `mean_squared_error`, `root_mean_squared_error`, `mean_absolute_percentage_error`, `symmetric_mean_absolute_percentage_error`. **Verified: unlike plain `ARIMA_PLUS`, this does NOT include `mean_absolute_scaled_error`** — confirmed by comparing the actual output columns of both types side by side on the same underlying data. With `time_series_id_col`, `ML.EVALUATE` evaluates each series independently. Behavior depends on inputs: if eval (test) data is supplied, forecast-accuracy metrics are returned; `perform_aggregation = TRUE` gives metrics per series, `FALSE` gives per-timestamp. (For ARIMA model-fit stats — `AIC`, `log_likelihood`, `variance`, `p/d/q`, `seasonal_periods`, `has_holiday_effect`, `has_spikes_and_dips`, `has_step_changes` — use `ML.ARIMA_EVALUATE`.)

**GOTCHA (verified): `ML.FORECAST`'s 2-argument form (`MODEL`, `STRUCT`) fails immediately** with `"Model type ARIMA_PLUS_XREG requires three parameters in ML.FORECAST."` — the third argument (a table/query supplying covariate values for the forecast horizon) is mandatory, not merely recommended. `ML.EXPLAIN_FORECAST` has the same 3-argument requirement.

**GOTCHA (verified): `forecast_limit_lower_bound`/`forecast_limit_upper_bound` are not a supported option AT ALL for this model type** — `CREATE MODEL` rejects it outright at training time: `"Option(s) FORECAST_LIMIT_LOWER_BOUND are not supported for ARIMA_PLUS_XREG model training."` This is a **different** limitation from plain `ARIMA_PLUS`, where the option is accepted but breaks `ML.EXPLAIN_FORECAST` (see that entry) — do not assume the two model types share identical option compatibility.

**GOTCHA (verified): custom holiday modeling and manual `non_seasonal_order` both work identically to `ARIMA_PLUS`** (same two-block `AS (training_data AS (...), custom_holiday AS (...))` syntax; same `auto_arima = FALSE` + `non_seasonal_order = STRUCT(p,d,q)`) — see that entry for the full syntax.

**GOTCHA (verified): a covariate with a few NULL values (not an entire series) does not block training.** A partial-NULL covariate (e.g. a handful of days with an undefined ratio due to `0/0`) triggers a warning — `"The input data has NULL values in one or more columns: <col>. ... For NULLs in the time_series_data column, BQML replaces them with meaningful values using local linear interpolation."` — but `CREATE MODEL` still succeeds and produces a real (non-NULL) regression weight for that covariate. This is a different situation from the existing "all-NULL for some series" limitation below, which does block training and requires dropping the covariate.

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
- **GOTCHA (verified): gap handling differs from plain `ARIMA_PLUS`.** Plain `ARIMA_PLUS` linearly interpolates a real numeric value across an entire missing-data gap, however long (see that entry's Limitations). `ARIMA_PLUS_XREG` does not — confirmed directly against a real ~6-month gap (`bigquery-public-data.new_york_citibike.citibike_trips`, October 2016 – March 2017): `ML.DETECT_ANOMALIES` returns `NULL` for the target/anomaly columns on every day inside the gap, rather than an interpolated value. Don't assume identical gap-handling behavior between the two model types just because they share most lifecycle functions and options. A third behavior exists on the same gap: the model-free TVFs (`ML.TREND`/`ML.SEASONALITY`/`ML.DETECT_CHANGE_POINTS`, see *Model-Free Time-Series Functions* below) gap-fill each series to its own span before computing, which is what makes `ML.DETECT_CHANGE_POINTS` report the gap's edges as change points. Establish which of the three surfaces produced a value before trusting anything inside a gap.

**Locations:** Available in BigQuery ML regions/multi-regions; no external connection needed. CMEK via `kms_key_name`.

**BigFrames API:** `bigframes.ml.forecasting.ARIMAPlus` covers univariate ARIMA_PLUS; external-regressor (XREG) multivariate forecasting is best driven via SQL `CREATE MODEL`. (No dedicated `ARIMAPlusXReg` class — treat as "use SQL.")

**Repo example (tested):** `data+ai/bq-ml/models/arima_plus_xreg/` — from-scratch build on Citi Bike daily trips using native `time_series_id_col` from the start, on the same 5 stations and TEST window as `models/arima_plus/` so the two are directly comparable on forecast accuracy. Uses `holiday_region=['GLOBAL','US']` and 3 covariates (a `capacity` covariate was dropped — it needed a join and was NULL for some stations). Covers `ML.ARIMA_COEFFICIENTS` (regressor weights), `ML.FEATURE_INFO`, `ML.TRAINING_INFO`, `ML.EVALUATE`, `ML.ARIMA_EVALUATE`, `ML.HOLIDAY_INFO`, `ML.FORECAST` (covariates supplied for the horizon), `ML.EXPLAIN_FORECAST` (including the `attribution_*` columns), `ML.DETECT_ANOMALIES`, and custom SQL MAPE/MAE/pMAE/MSE/RMSE/pRMSE.

Several cross-model-type differences from plain `ARIMA_PLUS` were verified here: no `mean_absolute_scaled_error` in the metrics; `forecast_limit_lower_bound` is rejected outright rather than merely breaking `ML.EXPLAIN_FORECAST`; and `ML.FORECAST` / `ML.EXPLAIN_FORECAST` both strictly require the 3-argument covariate form. Note that multi-series XREG once required a workaround (one model per series via an `EXECUTE IMMEDIATE FOR..IN` loop or async client jobs) — `time_series_id_col` is GA for XREG now and a single model replaces it.


---

## `CONTRIBUTION_ANALYSIS`
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

**Verified: the output schema is NOT fixed — it differs by `contribution_metric` type.** This is not called out in the official reference at the time this was tested; confirmed directly by training all three metric forms on identical data/dimensions.

*Summable metric* (`SUM(x)`):

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

*Summable-ratio metric* (`SUM(a)/SUM(b)`) — verified DIFFERENT columns:

| Column | Description |
|--------|-------------|
| `metric_test_over_metric_control` | Ratio of test to control metric for the segment. |
| `metric_test_over_complement` | Segment's test metric relative to the rest of the test set. |
| `metric_control_over_complement` | Segment's control metric relative to the rest of the control set. |
| `aumann_shapley_attribution` | Shapley-value-based attribution of the overall ratio change to this segment. |
| `contribution` | **Equals `ABS(aumann_shapley_attribution)`** here, NOT `ABS(difference)` — `difference`/`relative_difference`/`unexpected_difference`/`relative_unexpected_difference` don't appear at all for this metric type. |

*Summable-by-category metric* (`SUM(a)/COUNT(DISTINCT b)`) — verified a THIRD schema:

| Column | Description |
|--------|-------------|
| `difference`, `relative_difference` | Same meaning as the summable case. |
| `metric_test_over_population` | Segment's test metric as a share of the full test population's metric. |
| `metric_control_over_population` | Segment's control metric as a share of the full control population's metric. |
| `contribution` | `ABS(difference)` again (like summable) — but `unexpected_difference`/`relative_unexpected_difference` are absent, replaced by the `_over_population` columns. |

All three forms also return each dimension broken out into its own column (e.g. `usertype`, `gender`), and `apriori_support`.

**Preprocessing support:** N/A — no `TRANSFORM` clause (verified: errors immediately with `"Transform clause is not supported for the model type CONTRIBUTION_ANALYSIS"`); the input query columns are consumed directly.

**Hyperparameter tuning:** Not supported.

**Explainability / weights:** N/A — the model *is* the explanation; insights come from `ML.GET_INSIGHTS`, not from the `ML.WEIGHTS` / `ML.GLOBAL_EXPLAIN` family.

**Best practices:**
- Prefer `top_k_insights_by_apriori_support` for predictable runtime/output size; it lets the model auto-tune the apriori threshold.
- Use `PRUNE_REDUNDANT_INSIGHTS` to remove subset-redundant segments and keep the most descriptive rows — **verified dramatic effect**: `NO_PRUNING` + `min_apriori_support=0.001` on a 3-dimension model returned 1,559 insight rows; `PRUNE_REDUNDANT_INSIGHTS` + `top_k=15` on the identical data returned exactly 15.
- Sort/filter insights by `contribution` (biggest movers) or `unexpected_difference` (segments defying the overall trend, summable/category metrics only — ratio metrics have no such column, see above).
- For straightforward summable-metric key-driver questions, evaluate `AI.KEY_DRIVERS` first (see cross-link) — it skips the `CREATE MODEL` step.
- **Verified: more than 12 dimensions works** (beyond `AI.KEY_DRIVERS`' cap) — 13 low-cardinality dimensions trained successfully, though it took ~13 minutes vs. ~5 seconds for a 3-dimension model on the same data. Keep per-dimension cardinality low when using many dimensions: a separate attempt with 13 dimensions where several were high-cardinality (raw station IDs, individual bike/user IDs) ran over 18 minutes and then failed with a generic internal-error message (framed by BigQuery as "usually a transient issue") rather than a clean validation error.

**Limitations:**
- Metric column values must be non-negative unless `min_apriori_support = 0`.
- `min_apriori_support` and `top_k_insights_by_apriori_support` are mutually exclusive — verified: specifying both errors immediately (`"Please specify only one of the MIN_APRIORI_SUPPORT or TOP_K_INSIGHTS_BY_APRIORI_SUPPORT options."`).
- Dimension columns must be INT64, BOOL, or STRING; NULL-dimension rows are removed.
- No `ML.PREDICT` / `ML.EVALUATE`; produces insights only. **Verified: the actual error messages don't clearly say "not supported for this model type"** — `ML.PREDICT` complains a `contributors` column is missing from the input; `ML.EVALUATE` progressively asks for input data, then a `label` column, neither of which this model type has.
- **Verified: the training query may contain ONLY the columns referenced by `contribution_metric`, `dimension_id_cols`, and `is_test_col`** — any extra column errors immediately (`"Only is_test, dimension id, and contribution metric columns are allowed as input columns for CONTRIBUTION_ANALYSIS models"`), unlike most other model types which tolerate extra passthrough columns.
- Ratio/category `contribution_metric` syntax is strict: `"aliases in the query statement are not supported, please use column names directly"` — reference real columns, not `SELECT ... AS alias` names.

**Locations:** Standard BigQuery ML region/multi-region support; no external connection or endpoint involved.

**BigFrames API:** No dedicated class — verified by listing every submodule of the live installed `bigframes.ml` package (`cluster`, `decomposition`, `ensemble`, `forecasting`, `linear_model`, `remote`, etc. — no contribution-analysis module). Run the `CREATE MODEL` / `ML.GET_INSIGHTS` SQL via `session.read_gbq_query()` or `%%bigquery` magics.

**Repo example (tested):** `models/contribution_analysis/` (this project) — full lifecycle on `bigquery-public-data.new_york_citibike.citibike_trips`, using the same test/control split as the `AI.KEY_DRIVERS` sibling notebook (`../bq-ai-functions/functions/ai_key_drivers/`) for direct comparison, plus all three metric-type schemas, the >12-dimension test, and the pruning/mutual-exclusivity options.


---

## Imported models (TENSORFLOW, TENSORFLOW_LITE, ONNX, XGBOOST)

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

## `TENSORFLOW`
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

**Supported lifecycle functions:** `ML.PREDICT`, `ML.EXPLAIN_PREDICT` (per official docs — **not reproduced live**, see the correction below). Inputs may be dense Tensors,
SparseTensors (pass as dense arrays — BQ converts), or `tf.train.Example` (BQ auto-maps columns).
RaggedTensors are not supported.
**Not supported:** `ML.CONFUSION_MATRIX`, `ML.EVALUATE`, `ML.FEATURE_INFO`, `ML.ROC_CURVE`, `ML.TRAINING_INFO`, `ML.WEIGHTS`.

**Correction (verified live, `models/imported/`, 2026-07-22):** calling `ML.EXPLAIN_PREDICT` on a live imported `TENSORFLOW` model (a small Keras classifier with a baked-in `Normalization` layer) returns `"TENSORFLOW model is unsupported in ml.explain_predict."` — an outright rejection, not the documented (if memory-heavy) support. Treat the official docs' claim as unverified/stale until reproduced against a model that actually supports it.

**Data types:** `tf.int*`/`tf.uint*` → `INT64`; `tf.float16/32/64`, `tf.bfloat16` → `FLOAT64`;
`tf.bool` → `BOOL`; `tf.string` → `STRING`. Complex, quantized (`qint`/`quint`), `tf.resource`, `tf.variant` unsupported.

**Limitations:** Must be a SavedModel that already exists in GCS; frozen at import. 450 MB file-size
limit. In-RAM prediction memory limit ~250 MB (`ML.EXPLAIN_PREDICT` can trigger *TensorFlow worker out
of memory*). GraphDef \< v20, unreleased TF versions, custom/`tf.contrib` ops, and RaggedTensors are
unsupported. Object-table use is reservation-only.
**BigFrames API:** `bigframes.ml.imported.TensorFlowModel(model_path=...)`.
**Repo example (tested):** `data+ai/bq-ml/models/imported/imported.ipynb` (Step 4) — a small Keras `Sequential` classifier with a `tf.keras.layers.Normalization` layer baked in (so raw feature values work directly, since imported models support no `TRANSFORM`), exported via `model.export(...)`, imported with `MODEL_TYPE='TENSORFLOW'`, scored with `ML.PREDICT` (`ARRAY<FLOAT64>` input named `"input"`, auto-named `output_0` output).

---

## `TENSORFLOW_LITE`
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
**Repo example (tested):** `data+ai/bq-ml/models/imported/imported.ipynb` (Step 5) — `tf.lite.TFLiteConverter.from_saved_model(...)` on the exact SavedModel used for the `TENSORFLOW` example, then imported with `MODEL_TYPE='TENSORFLOW_LITE'`. Verified predictions match the `TENSORFLOW` import to ~7 significant figures (not bit-for-bit — ordinary float32 kernel differences between the TF runtime and the TFLite interpreter, since no quantization was applied) — same `ARRAY<FLOAT64>` input contract, same auto-named `output_0` output.

---

## `ONNX`
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
1.12.0** — your model's opset/IR version must be compatible ([`models/imported/`](../models/imported/) sets
`onnx_model.ir_version = 8` and `target_opset = 13` before upload to satisfy this). Only the Tensor value
type is supported. Object-table use is reservation-only.
**Gotcha (scikit-learn classifiers):** sklearn-onnx emits a *sequence of map* for probabilities by
default → import error `unsupported ONNX type: ONNX_TYPE_SEQUENCE`. Fix at conversion time with
`zipmap=False` (or `zipmap='columns'`) — [`models/imported/`](../models/imported/) does exactly this.
**BigFrames API:** `bigframes.ml.imported.ONNXModel(model_path=...)`.
**Repo examples (tested):**
- A scikit-learn Pipeline converts with `skl2onnx.convert_sklearn(..., options={id(model): {'zipmap': False}})`
  — the `zipmap=False` is what avoids the sequence-of-map gotcha above — then uploads to GCS and imports
  with `CREATE OR REPLACE MODEL ... OPTIONS(MODEL_TYPE='ONNX', MODEL_PATH='gs://.../*')`, and `ML.PREDICT`
  returns `label` + `probabilities`.
- **A transformer is the case where ONNX import stops being the right tool.** Exporting a PyTorch
  DistilBERT via `torch.onnx.export` takes float16 plus `ir_version=8` just to fit the 250 MB
  practical / 450 MB hard limit and ONNX Runtime 1.12; inputs arrive pre-tokenized as ARRAYs
  (`input_ids`, `attention_mask`) and `ML.PREDICT` returns raw `logits`, leaving softmax/argmax to SQL.
  That is the import-vs-remote tradeoff: ONNX import suits small numeric models and pushes tokenization
  onto the caller, while a `REMOTE` model over an Endpoint (below) keeps the whole pipeline server-side.
- `data+ai/bq-ml/models/imported/imported.ipynb` (Step 2) —
  scikit-learn `LogisticRegression` → ONNX via `skl2onnx.convert_sklearn(..., target_opset=13)`, then
  `onnx_model.ir_version = 8` set explicitly (both needed: a modern skl2onnx defaults to IR version 10
  and opset 22, both too new for ONNX Runtime 1.12). `zipmap=False` avoids the sequence-of-map gotcha.
  Single `ARRAY<FLOAT64>` input named `"input"`, `ML.PREDICT` returns `label` + `probabilities`.

---

## `XGBOOST`
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
| `MODEL_PATH` | STRING | Yes | GCS URI of the Booster file. Use a `.json` or `.ubj` extension — a `.bst` upload is rejected regardless of contents (see the gotcha below). |
| `KMS_KEY_NAME` | STRING | No | CMEK to encrypt the model. |
| `INPUT(field_name field_type, …)` | clause | Conditional | Input schema. **Optional only if** `feature_names` AND `feature_types` are both stored in the model file (see XGBoost Model IO / JSON Schema). Input types must be supported numeric types; names must match `feature_names`. |
| `OUTPUT(field_name field_type, …)` | clause | Conditional | Output schema. Output type must be `FLOAT64`. |

**Supported lifecycle functions:** `ML.PREDICT` and **`ML.FEATURE_IMPORTANCE`** (the only imported type
that supports a feature-attribution function).
**Limitations:** Booster format only, uploaded as `.json` or `.ubj`; model must exist in GCS before import.
**250 MB** size limit; **840 MB** memory limit to load+run (reduce trees / depth, or save via XGBoost's
default `save_model` to shrink). Object-table use is reservation-only.

**GOTCHA (verified live, undocumented as of this writing):** what the importer accepts is decided by
the artifact's **file extension**, not by the library version that wrote it. Measured by saving one
Booster from `xgboost` 3.3.0 three ways and importing each:

| Uploaded as | Result |
|---|---|
| `model.json` | Imports; `ML.PREDICT` and `ML.FEATURE_IMPORTANCE` both work |
| `model.ubj` | Imports |
| `model.bst` | Rejected — `Invalid XGBoost model: could not load model from file`, a JSON parse error at character position 1 |

The `.bst` and `.ubj` uploads were **byte-identical** in that test (current xgboost writes UBJSON under
either extension), so the difference is the name, not the contents. **Save as `.json` or `.ubj` and no
version pin is needed.** This retires an earlier reading of this behavior as a blanket "Booster must
come from XGBoost ≤ 1.5.1" cap — a modern booster imports fine under the right extension.

Note the matching quirk in the other direction: `EXPORT MODEL` writes `model.bst` at the
`xgboost_version = '0.9'` default and `model.ubj` at `'2.1'` — so a BQML-exported tree ensemble is
re-importable as-is only when it was trained at `2.1`.

**BigFrames API:** `bigframes.ml.imported.XGBoostModel(model_path=..., input=..., output=...)`.
**Repo example (tested):** `data+ai/bq-ml/models/imported/imported.ipynb`
(Step 3) — a binary classifier (`objective='binary:logistic'`) trained natively with `xgboost.train()`
on an unpinned current `xgboost`, saved as `.json`, imported with explicit `INPUT`/`OUTPUT` (a `multi:softprob`
objective also predicts fine but silently returns an ARRAY despite a scalar `OUTPUT` declaration — a
binary objective keeps the declared type honest). `ML.FEATURE_IMPORTANCE` verified working here.

---

**Connection matrix note:** Imported models occupy the "imported" column of the connection matrix —
**no connection** for standard `ML.PREDICT` on the GCS-loaded model; a Cloud Resource connection +
reservation pricing only when serving against an object table.


---

## `REMOTE` (Remote model over a Vertex AI endpoint — the mechanism)

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
- Two-step setup: (1) create a `CLOUD_RESOURCE` connection, (2) grant its auto-provisioned service account `roles/aiplatform.user`, then create the model. IAM propagation is variable and **verified live to exceed two minutes** in one case despite the grant itself succeeding immediately — retry `CREATE MODEL` on a permission error with a loop (several attempts, ~20s apart), not a single fixed sleep.
- Keep the connection in the **same location/region as the dataset** holding the model (location requirement).
- Reuse one connection across multiple remote models.
- Make `OUTPUT` names/types exactly mirror the endpoint response to avoid silent NULLs.
- Push filters/limits into the `ML.PREDICT` input subquery to control endpoint call volume and cost.

**Limitations:**
- `INPUT` and `OUTPUT` are **required** for custom-model endpoints.
- Only **shared public** Vertex AI endpoints — dedicated public, PSC, and private endpoints are unsupported.
- Only `ML.PREDICT` is supported; no evaluation/explainability/weights lifecycle functions.
- Cost has two parts: Vertex AI endpoint compute + the BigQuery query; latency includes a network round-trip per batch.
- **The `model_registry='VERTEX_AI'` shortcut (see `CREATE MODEL` general options) is NOT currently a working alternative to the manual export+upload path above, for at least `LOGISTIC_REG`.** Verified live: a model registered this way carries an unconditional Sampled-Shapley `explanationSpec` (confirmed via `gcloud ai models describe` — present even with no explainability options set), and deploying it to an Endpoint fails with `InvalidArgument: 400 Error occurred in Explanation preprocessing. ValueError: NodeDef mentions attr 'debug_name' not in Op<name=VarHandleOp...>`. This is a confirmed, currently-open Google issue — [vertex-ai-samples#2723](https://github.com/GoogleCloudPlatform/vertex-ai-samples/issues/2723), filed against Google's own official BQML-online-prediction sample notebook, closed "not planned." The manually-exported-and-uploaded model (no baked-in explanation spec) is the reliable path until this is fixed. `REMOTE` itself is not limited to models that ever touched BigQuery ML — any model registered to Vertex AI Model Registry (any framework, any training origin) can back a `REMOTE WITH CONNECTION` model once deployed to an endpoint.

**Locations:** Connection must match the dataset's BigQuery location (e.g., dataset in `US` → connection in `US`). Endpoint region is encoded in the `ENDPOINT` URL.

**BigFrames API:** No direct training equivalent; remote-endpoint inference is generally orchestrated via SQL/`ML.PREDICT` or the Vertex AI SDK (`aiplatform.Endpoint.predict`).

**Repo example (tested):**
- `data+ai/bq-ml/models/remote/` — the full path, picking up where `models/export/` leaves off: `CREATE MODEL` → `EXPORT MODEL` → deploy to a Vertex AI Endpoint → register that Endpoint as a `REMOTE` model → `ML.PREDICT`. Derives `INPUT`/`OUTPUT` from the exported SavedModel signature, creates the `CLOUD_RESOURCE` connection, grants `roles/aiplatform.user` to the connection's service agent, then `CREATE OR REPLACE MODEL ... INPUT(...) OUTPUT(...) REMOTE WITH CONNECTION ... OPTIONS(endpoint=...)`. Covers single-row, multi-row, and batch table scoring, and reads the per-row `remote_model_status` column (verified: 0 errors across 200 rows). Carries a real, small dollar cost for as long as the Endpoint stays deployed — the notebook tears it down.
- The signature is not restricted to numeric features: an `INPUT (text STRING) OUTPUT (label STRING, score FLOAT64)` model over a text-classification container is the same mechanism, and is the alternative to ONNX import above when you want tokenization to stay server-side.
- `data+ai/bq-ml/models/remote/remote.ipynb` — the full round trip from a BQML model: trains a `LOGISTIC_REG` → `EXPORT MODEL` (TF SavedModel) → `aiplatform.Model.upload()` with the pre-built `tf2-cpu.2-15` serving container (no Dockerfile) → deploys to a minimal `n1-standard-2` Endpoint → creates a `CLOUD_RESOURCE` connection + grants `roles/aiplatform.user` → `CREATE MODEL ... INPUT(...) OUTPUT(...) REMOTE WITH CONNECTION ... OPTIONS(endpoint=...)` → `ML.PREDICT` (single-row + 200-row batch, verified 0 `remote_model_status` errors). Verified the TF-serving container's response uses the exact field names the SavedModel signature itself exposes (`{label}_probs`/`{label}_values`/`predicted_{label}`), so `OUTPUT` can mirror them directly. Endpoint torn down within a few minutes of deployment — cross-link this entry with [`models/export/`](../models/export/), which this notebook picks up from. Also demonstrates, as a documented live failure, the `model_registry='VERTEX_AI'` shortcut's Explanation-preprocessing bug described above (Step 4), and proves the mechanism is framework-agnostic by registering (not deploying) an XGBoost model trained entirely outside BigQuery with the `xgboost-cpu.2-1` container (Step 5).


---

## `TRANSFORM_ONLY`
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

**Repo example (tested):**
- `data+ai/bq-ml/models/transform_only/transform_only.ipynb` — dedicated `TRANSFORM_ONLY` notebook on `penguins`: one pipeline chaining `ML.IMPUTER` + `ML.STANDARD_SCALER`/`ML.ROBUST_SCALER`/`ML.ONE_HOT_ENCODER`, applied via `ML.TRANSFORM`, feeding a downstream `LOGISTIC_REG` with no embedded `TRANSFORM` of its own. **Two verified findings:** (1) `ML.TRANSFORM` silently passes through any input column not referenced by the `TRANSFORM` clause, appended after the transform outputs — useful (carry an id/label through) but easy to mistake for pipeline output; (2) calling `ML.PREDICT` on the downstream model with *raw* (untransformed) data does **not** error — it silently predicts using values on the wrong scale, reproduced live: every row predicted the same class ("Gentoo penguin") regardless of true label until the input was re-wrapped in `ML.TRANSFORM`. Also confirms `EXPORT MODEL` on a transform-only model (`transform/saved_model.pb`, no predictive weights since there's no estimator).
- **Composition patterns this model type enables**, beyond the single-pipeline case above: one `TRANSFORM_ONLY` model per preprocessing *stage* (imputation, then scaling), chained with CTEs and exposed as a view so downstream queries see one clean surface; or one per *feature*, feature-store style, so a transform can be versioned and reused independently of any estimator. Either way the output feeds a `CREATE MODEL` that carries no `TRANSFORM` of its own, and `ML.TRANSFORM` reapplies the exact learned statistics at scoring time. `ML.FEATURE_INFO` reports the pre-transform summary stats, and a transform-only model can also be consumed from BigFrames via `read_gbq_model().predict()`.


---

## TimesFM (built-in foundation forecaster) — see `bq-ai-functions`

> **Cross-link only.** The TimesFM univariate forecaster is a *pretrained* foundation model invoked through the `AI.*` function family, which is owned by the sibling project. For the full entry (syntax, options, inputs/outputs, status), see **[`../bq-ai-functions/RESOURCES.md`](../../bq-ai-functions/RESOURCES.md)** → `AI.FORECAST`, `AI.EVALUATE`, `AI.DETECT_ANOMALIES`.

- **What it is:** A built-in, pretrained univariate time-series foundation model ([Google Research TimesFM](https://docs.cloud.google.com/bigquery/docs/timesfm-model)). Unlike `ARIMA_PLUS` / `ARIMA_PLUS_XREG`, there is **no `CREATE MODEL` step** — you call `AI.FORECAST` directly on a table or query. Supported model versions: TimesFM 2.0 (default) and TimesFM 2.5.
- **Category:** time-series (foundation model). Belongs to the `AI.*` family, **not** the BQML `CREATE MODEL` + `ML.*` lifecycle documented in this project.
- **Connection required:** No.
- **Status:** `AI.FORECAST` and `AI.EVALUATE` — **GA** (Nov 2025). `AI.DETECT_ANOMALIES` — **Preview**.

**Why it lives in `bq-ai-functions`, not here:** TimesFM is not a `model_type` you train with `CREATE MODEL`, and it does **not** use the `ML.*` lifecycle functions (`ML.FORECAST`, `ML.EVALUATE`, `ML.EXPLAIN_FORECAST`, `ML.DETECT_ANOMALIES`). It has no feature preprocessing, no hyperparameter tuning, no model weights, and AI-explanation is N/A. Those `ML.*` lifecycle functions ARE in scope here, but only for the trainable forecasters below.

**In-scope alternative in this project — the trainable forecasters:**

| If you want… | Use (in this project) | Notes |
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
