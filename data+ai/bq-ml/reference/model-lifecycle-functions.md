![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Fdata%2Bai%2Fbq-ml%2Freference&file=model-lifecycle-functions.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/data%2Bai/bq-ml/reference/model-lifecycle-functions.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ml/reference/model-lifecycle-functions.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ml/reference/model-lifecycle-functions.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ml/reference/model-lifecycle-functions.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ml/reference/model-lifecycle-functions.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-ml/reference/model-lifecycle-functions.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-ml/reference/model-lifecycle-functions.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# Model Lifecycle Functions

> Part of the [BigQuery ML — Detailed Reference](../RESOURCES.md) · [Project README](../README.md)

Functions that operate on a trained model: evaluate, predict, classify-eval, explain, weights, introspect, unsupervised insight, recommend/embed, forecast, anomaly/transform.


---

## `ML.EVALUATE`
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

> **No model? Use [`ML.METRICS`](model-free-functions.md#mlmetrics).** It computes the regression and classification metric sets above from a table of actual and predicted columns, with no model argument — the case `ML.EVALUATE` structurally cannot cover, such as predictions from Vertex AI, a vendor API, or a model that has since been dropped. Measured on the same predictions, every regression metric agrees with `ML.EVALUATE`'s to at least 13 significant digits (relative gaps ~1e-16 — floating-point summation order, not a difference in definition). It does **not** return `log_loss` or `roc_auc`, and its `precision`/`recall`/`f1_score` are defined by the column type (`BOOL` binary, `STRING` macro-averaged) rather than by the model task.

**Best practices:**
- Run with no input data first to get the training eval-split metrics for free, then pass TEST/VALIDATE data to confirm generalization.
- Stack splits with `SELECT 'TEST' AS SPLIT, * FROM ML.EVALUATE(...) UNION ALL ...` to compare TRAIN/VALIDATE/TEST side by side (see repo example).
- Tune the `threshold` to your precision/recall trade-off rather than relying on 0.5; inspect the full curve with `ML.ROC_CURVE` (binary) first.
- **BigQuery ML has no native k-fold cross-validation** — `CREATE MODEL`'s `data_split_method` only supports single-split holdout (`AUTO_SPLIT`/`RANDOM`/`CUSTOM`/`SEQ`/`NO_SPLIT`). Hand-roll it: assign folds with a deterministic hash (`MOD(ABS(FARM_FINGERPRINT(TO_JSON_STRING(t))), K)` when there's no natural row-id column), train K models with `data_split_method='NO_SPLIT'` each excluding its own fold (submit concurrently — see `ML.PREDICT`'s "join needs a stable key" note below for a related gotcha when combining per-row results across models), then `ML.EVALUATE` each fold model against its own held-out fold and `UNION ALL` to see the real spread, not just one number.

**Limitations:**
- **GOTCHA, verified live — the query cache serves stale metrics after a retrain.** BigQuery's result cache keys on the **query text**, and `CREATE OR REPLACE MODEL` does not change the text of the `ML.EVALUATE` that follows it. Re-running a notebook therefore hands you the *previous* run's metrics for a model that has since been retrained on different data. Measured during the build of [`workflows/feature_store/`](../workflows/feature_store/): after a retrain that genuinely changed both arms of a comparison, each arm reported its prior `roc_auc` to four decimals — two plausible-looking numbers that were simply not from the models on disk. Nothing errors and nothing looks wrong. Defend against it wherever an evaluation follows a retrain: `bq query --nouse_cache`, or `QueryJobConfig(use_query_cache=False)` from the client library. Note this bites hardest in exactly the situation it is least visible — an iterative build loop, where the model changes on every pass and the evaluation query never does.
- `precision`/`recall` of 0 means the threshold yielded no true positives; `NaN` precision means no positive predictions at all.
- For `ARIMA_PLUS`, the no-input form is deprecated — use `ML.ARIMA_EVALUATE` for model-fitting diagnostics (`AIC`, `log_likelihood`, `variance`, `non_seasonal_p/d/q`, `seasonal_periods`, `has_holiday_effect`, ...).
- `trial_id` argument is not supported for PCA models.

**BigFrames API:** `model.score(X, y)` on any `bigframes.ml` estimator returns the same metrics as a DataFrame.

**Repo example (tested):**
- `data+ai/bq-ml/models/logistic_regression/logistic_regression.sql` (Example 2) — minimal no-input `ML.EVALUATE`.
- `data+ai/bq-ml/workflows/ensembling/ensembling.sql` — a three-way TRAIN/VALIDATE/TEST `split` column assigned by deterministic hash, then `ML.EVALUATE` on the held-out TEST split `UNION ALL`'d across three model types into one comparison table.
- `data+ai/bq-ml/models/kmeans/kmeans.sql` (Example 2) — no-input `ML.EVALUATE` returning `davies_bouldin_index` and `mean_squared_distance`.
- `data+ai/bq-ml/models/pca/pca.sql` (Example 2) and `data+ai/bq-ml/models/autoencoder/autoencoder.sql` (Example 2) — no-input `ML.EVALUATE` for unsupervised reconstruction models (`total_explained_variance_ratio` for PCA; `mean_absolute_error`/`mean_squared_error`/`mean_squared_log_error` for the autoencoder). The autoencoder example doubles as the caution that these aggregates look entirely normal while a latent unit is dead — only `ML.PREDICT`'s `latent_col_*` values expose it.
- `data+ai/bq-ml/models/arima_plus/arima_plus.sql` (Example 5) — `ML.EVALUATE` with input data plus `STRUCT(TRUE AS perform_aggregation)` for `ARIMA_PLUS` forecast-accuracy metrics; called without eval data it falls back to ARIMA-fit stats in the shape of `ML.ARIMA_EVALUATE`.
- `data+ai/bq-ml/workflows/feature_store/feature_store.ipynb` — two `LOGISTIC_REG` arms differing *only* in how their features were built, evaluated against a shared `FARM_FINGERPRINT` hash split with `data_split_method='NO_SPLIT'` so the metric gap cannot be a split artifact. Also the source of the query-cache gotcha above, and a demonstration that the *bigger* `roc_auc` (0.9387 vs 0.5194) is the wrong one: cross-evaluating the leaky model against point-in-time features collapses it to 0.5299.
- `data+ai/bq-ml/workflows/cross_validation/cross_validation.ipynb` — hand-rolled 5-fold cross-validation on `ulb_fraud_detection` (BQML has no native k-fold support): deterministic hash-based fold assignment, 5 `LOGISTIC_REG` models submitted concurrently, per-fold `ML.EVALUATE` `UNION ALL`'d to show real fold-to-fold variance (roc_auc 0.968-0.985), then compared against a same-model-type single holdout to check whether it's representative of the fold distribution.

---

## `ML.PREDICT`
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
- **GOTCHA, verified live: joining multiple models' `ML.PREDICT` outputs back together on raw feature columns (instead of a stable row ID) can silently fan out.** When stacking several models' predictions into one meta-feature table (see `workflows/ensembling/`), joining on the full feature-column set duplicated rows — a 6,587-row split fanned out to 11,027 rows, because different source rows shared identical values across every feature column. Add a synthetic `ROW_NUMBER()` row ID when the source table first materializes (before training any model) and join every downstream `ML.PREDICT` output on that instead — then sanity-check the joined row count against the expected pre-join count rather than assuming a 1:1 join.

**BigFrames API:** `model.predict(X)` on a `bigframes.ml` estimator returns a DataFrame with the predicted columns.

**Repo example (tested):**
- `data+ai/bq-ml/models/logistic_regression/logistic_regression.sql` (Example 5) — `predicted_income_bracket` + `predicted_income_bracket_probs`.
- `data+ai/bq-ml/models/kmeans/kmeans.sql` (Example 3) — `CENTROID_ID` plus `NEAREST_CENTROIDS_DISTANCE` (distance to every centroid, nearest-first), with a non-training column passed through as an external check on the clusters.
- `data+ai/bq-ml/models/pca/pca.sql` (Example 3) — `ML.PREDICT` projecting rows onto `principal_component_1..N`.
- `data+ai/bq-ml/models/autoencoder/autoencoder.sql` (Example 3) — `ML.PREDICT` returning `latent_col_*` for the autoencoder, used to aggregate min/max/zero-count per latent column and catch a collapsed unit; paired with `ML.RECONSTRUCTION_LOSS` (Example 6) for the per-row view.
- `data+ai/bq-ml/workflows/customer_segmentation/customer_segmentation.sql` (Step 4) — `ML.PREDICT` over the full RFM table, aggregated by `CENTROID_ID` into segment profiles. Its Step 2 comment carries the matching gotcha: keep the ID column out of the training query, then join it back via `ML.PREDICT`, or it becomes a raw unscaled feature that distorts every distance.
- `data+ai/bq-ml/workflows/ensembling/ensembling.ipynb` — `ML.PREDICT` from 3 heterogeneous model types (`LOGISTIC_REG`/`BOOSTED_TREE_CLASSIFIER`/`RANDOM_FOREST_CLASSIFIER`) joined into one meta-feature table for a stacked ensemble; the source of the row-ID join-fanout gotcha above.


---

## `ML.CONFUSION_MATRIX`
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
- `data+ai/bq-ml/models/logistic_regression/logistic_regression.sql` (Example 3) — `SELECT * FROM ML.CONFUSION_MATRIX(MODEL ...)` on the census income binary classifier.
- `data+ai/bq-ml/models/boosted_tree_classifier/boosted_tree_classifier.sql` (Example 3) — the same call on a `BOOSTED_TREE_CLASSIFIER`; `models/random_forest_classifier/`, `models/dnn_classifier/`, `models/wide_and_deep_classifier/`, and `models/automl_classifier/` each carry it too, so the matrix is directly comparable across classifier types on one dataset.
- `data+ai/bq-ml/workflows/churn_retention/churn_retention.sql` (Step 3) — uses the matrix to settle *which class* a metric describes: the `expected_label = true` row (FALSE=1997, TRUE=3059) confirms `ML.EVALUATE`'s `recall = 0.605` is recall on the churned class, not the retained one.
- `data+ai/bq-ml/workflows/cross_validation/cross_validation.sql` — the motivating case for k-fold: a held-out eval split with only ~15 real fraud cases (TP=13, FN=2), where a metric estimated from 15 positives is exactly the high-variance situation cross-validation exists to quantify.

---

## `ML.ROC_CURVE`
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
- `data+ai/bq-ml/models/logistic_regression/logistic_regression.sql` (Example 4) — selects `threshold, recall, false_positive_rate, true_positives, false_positives, true_negatives, false_negatives FROM ML.ROC_CURVE(...) ORDER BY threshold`.
- `data+ai/bq-ml/models/boosted_tree_classifier/boosted_tree_classifier.sql` (Example 4) — the identical projection on a `BOOSTED_TREE_CLASSIFIER`. `models/random_forest_classifier/`, `models/dnn_classifier/`, `models/wide_and_deep_classifier/`, and `models/automl_classifier/` repeat it, so the curves line up across model types.

> Note: classification eval here covers the model-bound TVFs. For unsupervised anomaly detection (PCA / k-means / autoencoder — see `models/pca/`, `models/kmeans/`, `models/autoencoder/`) and ARIMA_PLUS forecasting eval, see the `ML.DETECT_ANOMALIES`, `ML.RECONSTRUCTION_LOSS`, and forecasting entries — `ML.CONFUSION_MATRIX` / `ML.ROC_CURVE` do not apply to those model types.


---

## Explainability functions: `ML.EXPLAIN_PREDICT`, `ML.GLOBAL_EXPLAIN`, `ML.FEATURE_IMPORTANCE`

Three lifecycle functions for model interpretability. `ML.EXPLAIN_PREDICT` gives **local** (per-row) feature attributions; `ML.GLOBAL_EXPLAIN` gives **model-level** (aggregated) attributions; `ML.FEATURE_IMPORTANCE` gives **tree-specific** split-based importance for boosted-tree / random-forest models. For the underlying concepts see the [BigQuery Explainable AI overview](https://cloud.google.com/bigquery/docs/xai-overview). For the model-coefficient view (`ML.WEIGHTS` / `ML.ADVANCED_WEIGHTS`), see the weights entry; this entry covers attributions/importance only.

---

## `ML.EXPLAIN_PREDICT`
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
- `data+ai/bq-ml/models/logistic_regression/logistic_regression.sql` (Example 6) — `STRUCT(5 AS top_k_features)`, selecting `top_feature_attributions`.
- `data+ai/bq-ml/models/boosted_tree_classifier/boosted_tree_classifier.sql` (Example 6) — the same call on a `BOOSTED_TREE_CLASSIFIER`, with a `LIMIT 10` input query showing the sample-the-input best practice above.
- `data+ai/bq-ml/workflows/churn_retention/churn_retention.sql` (Step 5) — `STRUCT(3 AS top_k_features)` for per-customer driver attribution, i.e. the per-row counterpart to the model-level ranking in its Step 4.

---

## `ML.GLOBAL_EXPLAIN`
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
- `data+ai/bq-ml/models/logistic_regression/logistic_regression.sql` (Examples 1 & 7) — `enable_global_explain = TRUE` then `ML.GLOBAL_EXPLAIN(...) ORDER BY attribution DESC`.
- `data+ai/bq-ml/models/boosted_tree_classifier/boosted_tree_classifier.sql` (Example 7) — the same pattern on a boosted-tree classifier, run side by side with `ML.FEATURE_IMPORTANCE` to show the two rank features differently by design.
- `data+ai/bq-ml/workflows/churn_retention/churn_retention.sql` (Step 4) — verified live: `tenure_days` dominates (attribution 0.072), ahead of `frequency` (0.028), `recency_days` (0.015), and `age` (0.015) — account age matters more than any single RFM feature.

---

## `ML.FEATURE_IMPORTANCE`
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
- `data+ai/bq-ml/models/boosted_tree_classifier/boosted_tree_classifier.sql` (Example 7) — `ML.FEATURE_IMPORTANCE(MODEL ...) ORDER BY importance_gain DESC` on a `BOOSTED_TREE_CLASSIFIER`, paired with `ML.GLOBAL_EXPLAIN` in the same example. The other three supported types carry it too: `models/boosted_tree_regressor/`, `models/random_forest_classifier/`, `models/random_forest_regressor/`.
- `data+ai/bq-ml/workflows/churn_retention/churn_retention.sql` (Step 4) — verified live, the two rankings genuinely disagree: `return_rate` is 8th-of-9 by `ML.GLOBAL_EXPLAIN` attribution but 3rd by `importance_gain`. Gain measures how useful a feature is *when* the trees split on it, so a rarely-used feature can still score high; attribution measures typical contribution across all predictions, split frequency included. Neither ranking is "more correct."

---

## Quick comparison

| | `ML.EXPLAIN_PREDICT` | `ML.GLOBAL_EXPLAIN` | `ML.FEATURE_IMPORTANCE` |
|---|---|---|---|
| Scope | Per-row (local) | Model-level (aggregated) | Model-level (tree split stats) |
| Models | linear, logistic, tree, DNN, WnD, AutoML | same, **+ `enable_global_explain=TRUE`** | boosted-tree, random-forest only |
| Needs eval/predict input | Yes (input table) | No | No |
| Key output | `top_feature_attributions` | `feature`, `attribution` | `importance_weight/gain/cover` |
| Pre-req option | none | `enable_global_explain = TRUE` | none |


---

## `ML.WEIGHTS`
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
- `data+ai/bq-ml/models/linear_regression/linear_regression.sql` — `LINEAR_REG` on `penguins`/`body_mass_g`, trained with `DUMMY_ENCODING` specifically to keep `ML.WEIGHTS` stable and interpretable; SQL comments explain why. Example 7 immediately follows it with `ML.ADVANCED_WEIGHTS` on the same model, which is the direct way to see what `ML.WEIGHTS` alone cannot tell you — that `island`'s non-zero weights are not statistically distinguishable from zero. (`models/logistic_regression/logistic_regression.sql` covers the GLM lifecycle but not `ML.WEIGHTS` — the linear-regression file is the one to read for it; it uses `ML.ADVANCED_WEIGHTS` instead.)
- `data+ai/bq-ml/workflows/difference_in_differences/difference_in_differences.sql` (Step 3) — the coefficient *is* the answer: the `treated_post` weight is the DiD estimate. Verified −19.29 with `optimize_strategy = 'NORMAL_EQUATION'`, matching `statsmodels.OLS` exactly, versus −6.19 under the default `AUTO_STRATEGY` — read weights for inference only from a normal-equation fit.
- `data+ai/bq-ml/workflows/price_elasticity_dml/price_elasticity_dml.sql` (Steps 2 and 4) — `ML.WEIGHTS` on the naive and the double-ML model, verified −1.43 vs. −0.71: roughly half the apparent price sensitivity was confounding, visible only by comparing two weight readouts.
- `data+ai/bq-ml/workflows/synthetic_control/synthetic_control.sql` (Step 2) — `ML.WEIGHTS` used as a *diagnostic of an invalid fit*: several weights come back negative and others far above 1, none of which a real percentage blend allows, on an underdetermined system (9 pre-period weeks vs. 13 donor columns).
- `data+ai/bq-ml/workflows/survival_analysis/survival_analysis.sql` — weights on a discrete-time hazard `LOGISTIC_REG` read as hazard direction: activity features carry positive weights (faster time-to-event), `week` a small negative one.

---

## `ML.ADVANCED_WEIGHTS`
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
| `standard_error` | FLOAT64 | Standard error of the weight. `NULL` for the intercept unless `standardize=TRUE`; **`0.0`** (not `NaN`) for a dropped dummy category. |
| `p_value` | FLOAT64 | p-value of the weight. `NULL` for the intercept unless `standardize=TRUE`; **`NaN`** for a dropped dummy category. |

The intercept arrives as a final row with `processed_input = '__INTERCEPT__'` and `category = NULL`. Note the two sentinel values differ: a baseline row is `weight = 0.0`, `standard_error = 0.0`, `p_value = NaN`, so `NOT IS_NAN(p_value)` is the reliable filter — reading `standard_error = 0.0` as a measured value will silently corrupt any average.

**Best practices:**
- Train with `CALCULATE_P_VALUES = TRUE` up front — p-values/standard errors are computed at CREATE MODEL time and cannot be added later.
- Set `STANDARDIZE => TRUE` when you need inference statistics for the intercept.

**Limitations:**
- Not available for multiclass logistic regression, matrix factorization, or any non-GLM model.
- Requires `L1_REG = 0` and `DUMMY_ENCODING`; incompatible with L1 regularization.
- Dropped dummy categories report `weight = 0.0` and `standard_error = 0.0` with a `NaN` p-value.

**Gotchas (verified live):**
- **Each precondition fails differently, and three of the four fail at `CREATE MODEL` time, not at query time.** Verified error text:

  | What you got wrong | Where it fails | Message |
  |---|---|---|
  | `calculate_p_values` omitted | the TVF | `Model is not supported by ML.ADVANCED_WEIGHTS because it was not trained with calculate_p_values = true.` |
  | left the default `ONE_HOT_ENCODING` | `CREATE MODEL` | `Please specify CATEGORY_ENCODING_METHOD=DUMMY_ENCODING to enable p_values calculation.` |
  | `l1_reg > 0` | `CREATE MODEL` | `L1_REG must be zero if CALCULATE_P_VALUES=TRUE.` |
  | multiclass label | `CREATE MODEL` | `Option(s) calculate_p_values are found. P-values can only be calculated for linear regression and binary logistic regression models.` |

- **A model with categorical features emits a warning at `CREATE MODEL` time:** `Since model contains categorical values, regression statistics will not be calculated for unstandardized intercept.` This is expected, not a failure — it is why `__INTERCEPT__` returns `NULL` statistics and why `STRUCT(TRUE AS standardize)` exists.
- **The dropped `DUMMY_ENCODING` baseline is the most frequent category, not the first alphabetically.** On `penguins` the baselines are Adelie (146 rows), Biscoe (163), and `MALE` (168) — `MALE` wins despite `FEMALE` sorting earlier.
- **`standardize` does not change any p-value.** It scales `weight` and `standard_error` by the same factor, so the t-statistic is invariant. Use it to compare effect sizes on a common scale, never to change which coefficients are significant.
- **The standardized intercept is not the label mean.** Categorical features stay dummy-coded rather than centered, so it is the prediction at mean numeric features *and* baseline categories. On `penguins` it is 4110.72 while mean `body_mass_g` is 4207.06.
- **`p_value` bottoms out near `1e-15`** (double-precision floor). Below that, differences are numerical noise — do not rank features by p-value down there.
- **`category` values inherit whatever is in the data, including leading whitespace.** `census_adult_income` returns `' White'` and `' Female'`; `category = 'White'` matches nothing. Use `TRIM(category)`.

**BigFrames API:** No dedicated wrapper; call the TVF via SQL / `read_gbq`.

**Repo example (tested):** `data+ai/bq-ml/models/linear_regression/` (Example 7) and `data+ai/bq-ml/models/logistic_regression/` (Example 8) — the two model types that satisfy the constraint, each training its main model with `calculate_p_values = TRUE`, `DUMMY_ENCODING`, and `l1_reg = 0` from the start, since the options cannot be added later.

The linear example is the clean statistical read: on `penguins`, `island` is the only feature whose categories are insignificant (p ≈ 0.82 and 0.42) because Gentoo appears only on Biscoe and Chinstrap only on Dream, so `island` merely restates `species`. `ML.WEIGHTS` reports non-zero island weights and gives you no way to see this. It also runs the `STRUCT(TRUE AS standardize)` variant to recover intercept statistics and to show that `flipper_length_mm` moves from 16.24 g/mm to 227.60 g per standard deviation while its p-value is unchanged at 2.6e-06.

The logistic example is the scale read: on `census_adult_income` the model expands to 106 rows (105 coefficients plus `__INTERCEPT__`); eight are dropped baselines, leaving 97 real tests, and **54 of those come back with p > 0.05**. Verified breakdown — `native_country` 38/41 insignificant, `education` 5/15, `workclass` 4/8, `occupation` 4/14, `race` 2/4, `marital_status` 1/6, and every numeric feature significant. More than half of what a 32k-row model learned is undefendable, concentrated almost entirely in one sparse high-cardinality column, and neither `ML.WEIGHTS` nor `ML.GLOBAL_EXPLAIN` would surface it.

> Note: For boosted trees / random forest see `ML.FEATURE_IMPORTANCE` and `ML.GLOBAL_EXPLAIN`; for k-means see `ML.CENTROIDS`; for PCA/autoencoder see `ML.PRINCIPAL_COMPONENTS` / `ML.PRINCIPAL_COMPONENT_INFO`; for ARIMA_PLUS see `ML.ARIMA_COEFFICIENTS`. The tree, clustering, and forecasting model files (`models/boosted_tree_classifier/`, `models/pca/`, `models/kmeans/`, `models/autoencoder/`, `models/arima_plus/`) do NOT use `ML.WEIGHTS`. Neither do the DNN and wide-and-deep types — `models/dnn_classifier/` (Example 7) records why: no coefficients exist, so Integrated Gradients via `ML.GLOBAL_EXPLAIN` is the only mechanism available there.


---

## Model Introspection: `ML.FEATURE_INFO`, `ML.TRAINING_INFO`, `ML.TRIAL_INFO`

These three table-valued functions read metadata that BigQuery ML records *during training*. They take no input data — they describe the model itself: the features it saw, how training converged, and (for tuned models) what each hyperparameter trial did. All three are GA.

---

## `ML.FEATURE_INFO`
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
**Repo example (tested):** `data+ai/bq-ml/models/logistic_regression/logistic_regression.sql` (Example 8). The same call shape appears in every model family under `models/` — GLM (`linear_regression/`, `logistic_regression/`), tree ensembles (`boosted_tree_classifier/`, `boosted_tree_regressor/`, `random_forest_classifier/`, `random_forest_regressor/`), neural (`dnn_classifier/`, `dnn_regressor/`, `wide_and_deep_classifier/`, `wide_and_deep_regressor/`), unsupervised (`kmeans/`, `pca/`, `autoencoder/`, `matrix_factorization/`), forecasting (`arima_plus/`, `arima_plus_xreg/`), and `automl_classifier/`, `automl_regressor/`, `imported/`, `remote/`, `transform_only/` — 21 files in all, which is what makes it the cheapest first look at any model.

---

## `ML.TRAINING_INFO`
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
| Boosted tree / random forest (XGBoost-based) | `iteration` numbering starts at **1**, not 0 (unlike GLM/DNN gradient descent) — verified in `models/boosted_tree_classifier/`. The first iteration's `duration_ms` includes a one-time data-loading/indexing overhead (observed ~14 min on one run), so it is not representative of steady-state per-iteration cost; later iterations run in milliseconds. |

**Best practices:**
- `ORDER BY iteration` and chart `loss` vs `eval_loss` — divergence signals overfitting.
- For linear/logistic models, `learning_rate` can *rise* across iterations when `LEARN_RATE_STRATEGY = 'LINE_SEARCH'` (the default) — expected, not a bug.

**GOTCHA (measured, undocumented) — `ML.TRAINING_INFO` returns zero rows on a `BOOSTED_TREE_*` model trained with `xgboost_version = '2.1'` once training runs more than 10 iterations.** Nothing else about the model is affected: `CREATE MODEL` succeeds, and `ML.EVALUATE`, `ML.PREDICT`, `ML.EXPLAIN_PREDICT`, `ML.FEATURE_IMPORTANCE` and `ML.GLOBAL_EXPLAIN` all return normally. Only the training history is empty. Isolated with single-variable probes on `census_adult_income` (3 features, 5,000 rows, `early_stop = FALSE`, everything else held constant):

| `xgboost_version` | `max_iterations` | rows returned |
|---|---|---|
| `0.9` (the default) | 20 | 20 |
| `1.1` | 20 | 20 |
| `2.1` | 5 | 5 |
| `2.1` | 10 | 10 |
| `2.1` | 11 | **0** |
| `2.1` | 20 | **0** |

The boundary is exactly 10 iterations. Ruled out as causes: early stopping (disabled in the probes above, and the default `early_stop = TRUE` behaves identically), `auto_class_weights`, and `enable_global_explain` — both of the latter return rows normally at `'2.1'` with `max_iterations = 5`. Reproduced on a realistic config too: the full 11-feature `census_adult_income` classifier at default `max_iterations` returns 9 rows at `'0.9'` and 0 rows at `'2.1'`.

**Practical consequence:** on a boosted tree you get either a modern `model.ubj` export or a readable loss curve, not both. `RANDOM_FOREST_*` is unaffected — training is single-pass (one iteration), so it never reaches the boundary. To recover the curve, omit `xgboost_version` (back to the `0.9` default) or hold training to 10 iterations or fewer.

**Limitations:**
- No imported-TensorFlow support.
- Limited usefulness for ARIMA_PLUS (use `ML.ARIMA_EVALUATE` / `ML.ARIMA_COEFFICIENTS` for forecast diagnostics instead).
- Returns nothing for `BOOSTED_TREE_*` at `xgboost_version = '2.1'` past 10 iterations — see the gotcha above.

**BigFrames API:** No direct equivalent.
**Repo example (tested):**
- `data+ai/bq-ml/models/logistic_regression/logistic_regression.sql` (Example 8) — the loss curve.
- The `'2.1'` empty-result case is documented in place in `models/boosted_tree_classifier/` (Example 8 / Step 6) and `models/boosted_tree_regressor/` (Example 6 / Step 5).
- `data+ai/bq-ml/models/arima_plus/arima_plus.sql` (Example 4) — the reduced ARIMA output, paired with `ML.FEATURE_INFO`.
- `data+ai/bq-ml/models/automl_classifier/automl_classifier.sql` (Example 6, and the header note) — `duration_ms` is how the AutoML wall-clock overrun was measured: `duration_ms = 9,475,200`, i.e. 2.63 hours actual for `budget_hours = 1.0`. This is the `ML.TRAINING_INFO` use that has nothing to do with loss curves — reading the real cost of a training run after the fact.
- `data+ai/bq-ml/workflows/difference_in_differences/difference_in_differences.sql` (header gotcha) — `ML.TRAINING_INFO` as the *detection* mechanism for a silently wrong fit: with the default `AUTO_STRATEGY` the loss is still decreasing at the final iteration and no error is raised, which is the signal to force `optimize_strategy = 'NORMAL_EQUATION'` for small-sample or collinear regressions used for inference.

---

## `ML.TRIAL_INFO`
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
**Repo example (tested):** `data+ai/bq-ml/models/logistic_regression/logistic_regression.sql` (Example 10 — `NUM_TRIALS=10` + `HPARAM_RANGE`, then sorts trials by `hparam_tuning_evaluation_metrics.roc_auc` and `is_optimal`). `data+ai/bq-ml/models/boosted_tree_classifier/boosted_tree_classifier.sql` (Example 10 — tunes `learn_rate`/`max_tree_depth`; observed a transient trial `FAILED`, see gotcha above). `data+ai/bq-ml/models/random_forest_regressor/random_forest_regressor.sql` (Example 9 — observed the `is_optimal` tie, see limitation above). For the unsupervised types the tuning objective is the model's own quality metric rather than an accuracy metric: `data+ai/bq-ml/models/kmeans/kmeans.sql` sorts trials by `hparam_tuning_evaluation_metrics.davies_bouldin_index ASC`, and `data+ai/bq-ml/models/autoencoder/autoencoder.sql` by `hparam_tuning_evaluation_metrics.mean_squared_error ASC`. `models/pca/pca.sql` (Example 10) is the deliberate exception — PCA supports no tuning at all, so it uses `pca_explained_variance_ratio` to let BigQuery ML pick the component count instead.

> Related hyperparameter-tuning option reference (`NUM_TRIALS`, `HPARAM_RANGE`, `HPARAM_CANDIDATES`, `HPARAM_TUNING_OBJECTIVES`) lives with the per-model-type entries and the capability matrix.


---

## `ML.CENTROIDS`
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
**Repo example (tested):**
- `data+ai/bq-ml/models/kmeans/kmeans.sql` (Example 4) — one row per (`centroid_id`, `feature`) `ORDER BY centroid_id, feature`, read as the interpretation step: the centroid with the highest body-mass and flipper-length coordinates is the large-species cluster. Because `KMEANS` is non-deterministic (Example 7), read the profile off the coordinates, not off a remembered `centroid_id`.
- `data+ai/bq-ml/workflows/customer_segmentation/customer_segmentation.sql` (Step 3) — the same call on RFM features, feeding the aggregated segment profiles in Step 4.
- On a hyperparameter-tuned model the output also carries `trial_id`, so the row count multiplies by the number of trials (one row per feature x centroid x trial) — see `models/kmeans/kmeans.sql`'s tuning example for the tuned variant.

---

## `ML.PRINCIPAL_COMPONENTS`
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
**Repo example (tested):** `data+ai/bq-ml/models/pca/pca.sql` (Example 4) — one row per (`principal_component_id`, `feature`), so the row count is features x components. Two things it pins down: **`principal_component_id` is 0-indexed**, unlike `KMEANS`' 1-indexed `centroid_id` — indexing conventions are not consistent across unsupervised model types — and how to read a component as an axis: on the penguins model, component 0 loads negative on body mass, culmen length, and flipper length but positive on culmen depth, i.e. a body-size axis.

---

## `ML.PRINCIPAL_COMPONENT_INFO`
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
**Repo example (tested):**
- `data+ai/bq-ml/models/pca/pca.sql` (Example 5) — one row per component; on the penguins model component 0 alone explains ~69% of variance and adding component 1 brings the cumulative total to ~88%, which is how the elbow is read. Example 10 then targets `pca_explained_variance_ratio = 0.90` and BigQuery ML picks 3 components (2 reach only ~0.88, just short), landing at ~0.97 cumulative.
- **GOTCHA, verified live — prefer a fixed component count over a variance target when downstream results must be stable.** `data+ai/bq-ml/workflows/anomaly_fraud_detection/anomaly_fraud_detection.sql` (Step 1) trains PCA on `ulb_fraud_detection`: with `pca_explained_variance_ratio` (a *variable* component count chosen to hit a variance target), three runs of the identical `CREATE OR REPLACE MODEL` statement gave `ML.DETECT_ANOMALIES` true-positive counts of 3, 235, and 279 out of 492 real frauds — while `total_explained_variance_ratio` stayed bit-for-bit stable at ~0.95473 every time. Near-threshold eigenvalues flip which components get retained, which swings per-row reconstruction error even though the aggregate variance captured looks identical. Switching to a fixed `num_principal_components = 10` was substantially more stable (TP 114-124 across independent runs). The aggregate metric is not a stability check.

---

## `ML.RECONSTRUCTION_LOSS`
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
**Repo example (tested):** `data+ai/bq-ml/models/autoencoder/autoencoder.sql` (Example 6) — returns `mean_absolute_error`, `mean_squared_error`, and `mean_squared_log_error` per input row (the same three metrics `ML.EVALUATE` reports in aggregate), `ORDER BY mean_squared_error DESC` to surface the rows the model reconstructs worst. That is the manual, row-level view of exactly the signal `ML.DETECT_ANOMALIES` automates in the same file's Example 8. On a hyperparameter-tuned model the output also carries `trial_id`.

---

> Cross-reference: for anomaly detection from these models see `ML.DETECT_ANOMALIES`; for extracting embeddings from a trained PCA/AUTOENCODER/MATRIX_FACTORIZATION model see the in-scope `ML.GENERATE_EMBEDDING` lifecycle entry. Foundation-model (text/multimodal) embedding generation lives in [../bq-ai-functions](../../bq-ai-functions/RESOURCES.md).


---

## `ML.RECOMMEND`
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

**Repo example (tested):**
- `data+ai/bq-ml/models/matrix_factorization/matrix_factorization.sql` — the full lifecycle on Google Merchandise Store `ga_sessions_*` data with `feedback_type = 'IMPLICIT'` (42,178 users x 320 items, ~1.3M interactions): create → evaluate → recommend → inspect factors → generate embeddings → item-item similarity via `VECTOR_SEARCH` → introspect → tune.
- `data+ai/bq-ml/workflows/recommendation/recommendation.sql` (Step 3) — top-N per user done properly: `ROW_NUMBER() OVER (PARTITION BY visitor_id ORDER BY predicted_view_count_confidence DESC)` filtered to `rank <= 5`, rather than a global `ORDER BY ... LIMIT`.
- **Is the personalization real?** The same file (Step 4) answers it quantitatively rather than assuming: a real visitor's personalized top-10 overlapped the global most-viewed top-10 by **0 of 10** items.
- **GOTCHA, verified live: `ML.RECOMMEND` on a user absent from training does not error — it silently returns a ranking.** `workflows/recommendation/recommendation.sql` (Step 5) proves that ranking is not personalized by showing two different absent user IDs receive an identical top-5. Cold-start users need to be detected upstream; the function will not signal them.
- **Retraining variance:** `models/matrix_factorization/matrix_factorization.sql` (Example 2) records that WALS training is not deterministic — repeated identical runs landed at ~0.873 and ~0.860 — comparable to `models/kmeans/` and `RANDOM_FOREST_*`, unlike PCA's determinism.

---

## `ML.GENERATE_EMBEDDING` (from a BQML PCA / AUTOENCODER / MATRIX_FACTORIZATION model)

> **Scope note:** This entry covers ONLY the in-house BQML-model use of `ML.GENERATE_EMBEDDING` — extracting embeddings from a trained `PCA`, `AUTOENCODER`, or `MATRIX_FACTORIZATION` model. The **foundation/remote-model (text & multimodal) use** of `ML.GENERATE_EMBEDDING` / `AI.GENERATE_EMBEDDING` is owned by `../bq-ai-functions/` — see that doc; do not duplicate here.

- **Description:** Produces a single `ARRAY<FLOAT>` embedding column from a trained BQML model, meant for use with `VECTOR_SEARCH`. The function delegates internally: PCA/autoencoder route through `ML.PREDICT`; matrix factorization routes through `ML.WEIGHTS`.
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
- **Verified: `VECTOR_SEARCH` does NOT accept `ML.GENERATE_EMBEDDING`'s output passed directly as its base-table argument** — `VECTOR_SEARCH(ML.GENERATE_EMBEDDING(...), ...)` errors with `"Unsupported query pattern"` (`models/autoencoder/`). Materialize the embeddings into a real table (or view) first, then run `VECTOR_SEARCH` against that table. Also verified: `ML.GENERATE_EMBEDDING` does NOT normalize its output — the raw result is bit-for-bit identical to hand-computing the same values via `ML.PREDICT`'s latent/projection columns; if `VECTOR_SEARCH` uses `COSINE` distance, no separate `ML.NORMALIZER` step is needed (`COSINE` and manual-normalize+`DOT_PRODUCT` give mathematically identical rankings).
- Matrix-factorization embeddings are per-entity (user/item), not per-row feature embeddings.

**BigFrames API:** No direct single-call `generate_embedding` wrapper for these in-house model types; equivalent results come from `PCA.transform()`, the autoencoder `predict()` latent output, and `MatrixFactorization` weights via the respective `bigframes.ml` classes. (Foundation embeddings: `bigframes.ml.llm.TextEmbeddingGenerator` — cross-link out.)

**Repo example (tested):**
- `data+ai/bq-ml/models/pca/pca.sql` (Example 8) — wraps the same projection Example 3 gets from `ML.PREDICT` into one `ml_generate_embedding_result ARRAY<FLOAT>` column. Verified: the array values match `ML.PREDICT`'s `principal_component_1/2` exactly, in order.
- `data+ai/bq-ml/models/autoencoder/autoencoder.sql` (Example 9) — the same for the autoencoder latent space; the array matches `ML.PREDICT`'s `latent_col_*` exactly, in order. Example 10 then compares the manual route (`ML.PREDICT` → wrap into an ARRAY → optional `ML.NORMALIZER`) against the wrapper, feeding both into `VECTOR_SEARCH`.
- `data+ai/bq-ml/models/matrix_factorization/matrix_factorization.sql` — the per-entity (user/item) case, used for item-item similarity via `VECTOR_SEARCH`.
- `data+ai/bq-ml/functions/distance/distance.sql` — `ML.DISTANCE` as the brute-force alternative for a one-off pairwise comparison, without building a vector index.

The wrapper packages what `ML.PREDICT` already returns into a single array column purpose-built for `VECTOR_SEARCH`; the two are verified equivalent above, so choose by what consumes the output.


---

## ARIMA_PLUS forecasting lifecycle functions

These five table-valued functions consume a trained `ARIMA_PLUS` (univariate) or `ARIMA_PLUS_XREG`
(multivariate) model. The forecast and time-series decomposition are computed **at `CREATE MODEL`
time**; these functions retrieve the stored results and compute confidence/prediction intervals on
demand. They are **GA**, require **no connection**, and have no foundation-model dependency.

> For the foundation-model forecaster (`AI.FORECAST` / TimesFM, zero training, no `CREATE MODEL`),
> see [`../bq-ai-functions/RESOURCES.md` → AI.FORECAST](../../bq-ai-functions/RESOURCES.md). The
> entries below are the classic, statistical ARIMA_PLUS path that lives in bq-ml.

---

## `ML.FORECAST`
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
**Repo example (tested):**
- `data+ai/bq-ml/models/arima_plus/arima_plus.sql` (Example 6) — `STRUCT(28 AS horizon, 0.9 AS confidence_level)` over a multi-series Citibike-style model built with `time_series_id_col`, selecting the forecast plus both prediction-interval bounds. Example 1 shows the single-series form with only `STRUCT(28 AS horizon)`.
- `data+ai/bq-ml/models/arima_plus_xreg/arima_plus_xreg.sql` — the same call for the covariate model, where future feature values must be supplied to forecast at all.

---

## `ML.EXPLAIN_FORECAST`
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
**Repo example (tested):**
- `data+ai/bq-ml/models/arima_plus/arima_plus.sql` (Example 7) — selects `time_series_type`, `time_series_data`, `time_series_adjusted_data`, `trend`, `seasonal_period_weekly`, `seasonal_period_yearly`, and `holiday_effect` for one series out of a multi-series model.
- Custom holidays (Example 10 in the same file) surface as a `holiday_effect_<holiday_name>` column. Reported honestly: with only 4 occurrences in the training history the estimated effect came out at **0.0** — statistically indistinguishable from no effect. The column existing is not evidence the effect is real.
- **GOTCHA, verified: `forecast_limit_lower_bound` / `forecast_limit_upper_bound` are incompatible with `ML.EXPLAIN_FORECAST`.** `ML.FORECAST` and every other lifecycle function are unaffected — only this one is blocked, which is why the multi-series model in that file deliberately does not set a bound.

---

## `ML.ARIMA_EVALUATE`
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
**Repo example (tested):** `data+ai/bq-ml/models/arima_plus/arima_plus.sql` (Example 3) — the full per-series model-selection table for a multi-series model. Example 10 in the same file uses it as the *verification* of a manual order: training with `auto_arima = FALSE` and `non_seasonal_order = STRUCT(2 AS p, 1 AS d, 1 AS q)`, then reading `non_seasonal_p/d/q` back to confirm auto.ARIMA was actually bypassed.

---

## `ML.ARIMA_COEFFICIENTS`
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
**Repo example (tested):** `data+ai/bq-ml/models/arima_plus/arima_plus.sql` (Example 8) — per-series `ar_coefficients` / `ma_coefficients` / `intercept_or_drift`, sitting directly after `ML.ARIMA_EVALUATE` (Example 3) so the `(p,d,q)` order and the coefficient vector lengths can be read against each other.

---

## `ML.HOLIDAY_INFO`
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
**Repo example (tested):**
- `data+ai/bq-ml/models/arima_plus/arima_plus.sql` (Example 9) — filtered to `region = 'US'` over a bounded `primary_date` range, which is the practical shape given how many rows the unfiltered output spans.
- Example 10 in the same file registers a **custom holiday** via the `holiday_region`/custom-holiday input and then reads it back with `WHERE holiday_name = 'NYCMarathon'` — the way to confirm a custom calendar entry was actually accepted by the model.

---

### Forecast `ML.EVALUATE` metrics (ARIMA_PLUS)
When `ML.EVALUATE` is called on an ARIMA_PLUS model **with** test data and `perform_aggregation=TRUE`,
it returns per-series: `mean_absolute_error`, `mean_squared_error`, `root_mean_squared_error`,
`mean_absolute_percentage_error`, `symmetric_mean_absolute_percentage_error`,
`mean_absolute_scaled_error`. With
`perform_aggregation=FALSE` it returns per-timestamp metrics; with no input data it returns the
in-training ARIMA metrics (see `ML.ARIMA_EVALUATE`). Anomaly detection on the same model uses
[`ML.DETECT_ANOMALIES`](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-detect-anomalies)
with `anomaly_prob_threshold` (repo example: same notebook, cell 57).


---

## `ML.DETECT_ANOMALIES`
- **Description:** Performs unsupervised anomaly detection against a trained BQML model. Returns each input row flagged `is_anomaly` (TRUE/FALSE) plus the score the flag is based on. The detection mechanism and threshold parameter differ by model family: error/distance-cutoff for IID models (PCA, AUTOENCODER, KMEANS) and prediction-interval probability for time-series models (ARIMA_PLUS, ARIMA_PLUS_XREG).
- **Use cases:**
  - Fraud / outlier detection on tabular data using a PCA, autoencoder, or k-means model (reconstruction error / distance from centroid).
  - Detecting anomalous points in a forecasted time series (value falls outside the model's prediction interval).
  - Turning an unsupervised dimensionality-reduction / clustering model into a binary anomaly classifier without labels.
- **documentation:** https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-detect-anomalies
- **Type:** Table-valued function.
- **Applies to models:** `PCA`, `AUTOENCODER`, `KMEANS` (use `contamination`); `ARIMA_PLUS`, `ARIMA_PLUS_XREG` (use `anomaly_prob_threshold`). Not applicable to supervised regression/classification model types.

> Cross-link (do NOT duplicate): for foundation-model / TimesFM time-series anomaly detection see `AI.DETECT_ANOMALIES` in [../bq-ai-functions/](../../bq-ai-functions/RESOURCES.md).

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

\* For ARIMA_PLUS, scoring historical (training) data requires `decompose_time_series = TRUE` (the default) at CREATE MODEL time; scoring new data requires `anomaly_prob_threshold`. **Verified: all three IID model types (`KMEANS`, `PCA`, `AUTOENCODER`) require this 3rd argument** — omitting it errors immediately with `"DETECT_ANOMALIES expects 3 arguments for <model_type> models but 2 were passed"` (`models/kmeans/`, `models/pca/`, `models/autoencoder/`).

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
- Set `contamination` to a domain-informed expected outlier rate. [`workflows/anomaly_fraud_detection/`](../workflows/anomaly_fraud_detection/) computes it from the training-data positive-class rate (`TRAIN_FRAUD_PCT ≈ 0.00174`) and passes it as `STRUCT(TRAIN_FRAUD_PCT AS contamination)`.
- For evaluation, map `is_anomaly` to 0/1 and build a confusion matrix against known labels (`CASE WHEN is_anomaly ... END`, as in `workflows/anomaly_fraud_detection/`).
- For ARIMA_PLUS, keep `decompose_time_series = TRUE` so forecast errors are retained for historical anomaly scoring.

**Limitations:**
- `contamination` and `anomaly_prob_threshold` are mutually exclusive — each applies only to its model family.
- IID detection is purely error/distance-rank based: a row is "anomalous" only relative to the chosen contamination cutoff, not an absolute judgement.
- Recall on rare classes is typically low (fraud notebooks show high precision-0 / low recall-1), since these are unsupervised methods.

**BigFrames API:** `model.detect_anomalies(X, contamination=...)` on `bigframes.ml.decomposition.PCA`, `bigframes.ml.cluster.KMeans`, and the autoencoder/forecasting estimators.

**Repo example (tested):**
- `data+ai/bq-ml/models/kmeans/kmeans.sql` (Example 6) — `STRUCT(0.05 AS contamination)`, ranked by `normalized_distance` from the nearest centroid.
- `data+ai/bq-ml/models/pca/pca.sql` (Example 7) — the same contamination cutoff, ranked by `mean_squared_error` (reconstruction error).
- `data+ai/bq-ml/models/autoencoder/autoencoder.sql` (Example 8) — reconstruction-based detection; its Example 6 shows the manual `ML.RECONSTRUCTION_LOSS` view of the same underlying signal.
- `data+ai/bq-ml/models/arima_plus/arima_plus.sql` (Example 11) — the time-series form, `STRUCT(0.95 AS anomaly_prob_threshold)` with `is_anomaly` / `anomaly_probability`. `models/arima_plus_xreg/` carries the covariate variant.
- **The ground-truth check the mechanism demos can't give you:** `data+ai/bq-ml/workflows/anomaly_fraud_detection/anomaly_fraud_detection.sql` runs PCA and AUTOENCODER detection on `ulb_fraud_detection` (284,807 rows, 492 real frauds at 0.17%) trained on features only, then scores real precision/recall against the withheld `Class` label and contrasts it with a supervised `BOOSTED_TREE_CLASSIFIER` trained *with* the label. That file is also the source of the PCA variable-component-count instability documented under `ML.PRINCIPAL_COMPONENT_INFO`.
- **Not the same thing as data-quality monitoring, despite the name.** `ML.DETECT_ANOMALIES` finds row-level outliers *within* one dataset; `ML.VALIDATE_DATA_SKEW` / `ML.VALIDATE_DATA_DRIFT` in `functions/data_quality/` compare whole datasets or time windows to each other. Different concept, similar name.

---

## `ML.TRANSFORM` (applying a saved transform)
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
- **GOTCHA (verified live, `models/transform_only/`):** any column present in the input query but **not** referenced anywhere in the `TRANSFORM` clause passes straight through untouched, appended after the transform outputs — the "exactly the columns produced by TRANSFORM" description above is true for referenced columns, but unreferenced extras ride along too. Useful for carrying an id/label column through without re-listing it in the pipeline, but easy to mistake for the pipeline itself re-emitting a raw column.
- **GOTCHA (verified live, `models/transform_only/`):** a downstream model trained on `ML.TRANSFORM` output but with no *embedded* `TRANSFORM` of its own does not know to re-apply the pipeline at predict time. Calling `ML.PREDICT` on it with raw (untransformed) data does **not** error — it silently predicts using values on the wrong scale. Reproduced live: every row predicted the same class regardless of true label until the raw input was re-wrapped in `ML.TRANSFORM` first.

**BigFrames API:** Transform reuse is handled implicitly by pipeline/estimator objects; no standalone one-to-one `ML.TRANSFORM` call needed in typical BigFrames pipelines.

**Repo example (tested):**
- `data+ai/bq-ml/models/transform_only/transform_only.ipynb` — both gotchas above reproduced live; a `TRANSFORM_ONLY` pipeline (`ML.IMPUTER` + scalers + `ML.ONE_HOT_ENCODER`) feeding a downstream `LOGISTIC_REG` with no embedded `TRANSFORM`.
- `data+ai/bq-ml/models/logistic_regression/logistic_regression.sql` (Example 9) — `CREATE MODEL ... TRANSFORM(ML.STANDARD_SCALER(age) OVER() AS age, ...)`; the scaler is saved with the model and reapplied automatically at predict time (the SQL comments note no need to repeat it in `ML.PREDICT`) — this is the embedded-`TRANSFORM` case, which does NOT need the re-application `ML.TRANSFORM` gotcha above applies to.
