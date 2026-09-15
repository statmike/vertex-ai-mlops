![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Fdata%2Bai%2Fbq-ml%2Freference&file=comparison-tables.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/data%2Bai/bq-ml/reference/comparison-tables.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ml/reference/comparison-tables.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ml/reference/comparison-tables.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ml/reference/comparison-tables.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ml/reference/comparison-tables.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-ml/reference/comparison-tables.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-ml/reference/comparison-tables.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# Comparison Tables

> Part of the [BigQuery ML — Detailed Reference](../RESOURCES.md) · [Project README](../README.md)

The fastest way to answer "which model / which function do I use?" Detailed entries live in [CREATE MODEL — Model Types](create-model-model-types.md), [Model Lifecycle Functions](model-lifecycle-functions.md), [Model-Free Functions](model-free-functions.md), and [Model Management & Monitoring](model-management-monitoring.md).

## 1. `model_type` catalog

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
| TimesFM (built-in) → `AI.FORECAST` | Time series (foundation) | `AI.FORECAST` | No | GA — see [bq-ai-functions](../../bq-ai-functions/RESOURCES.md) |

\* AutoML trains via an `ML_EXTERNAL` Vertex AI job but needs no `CREATE CONNECTION` object. \*\* Matrix factorization needs reservation/Editions (capacity) slots, not on-demand pricing — but no connection. \*\*\* The imported model itself needs no connection; the **object table** it is served over does (its service account needs `roles/storage.objectViewer` on the bucket), and the `ML.DECODE_IMAGE` family that prepares object-table images needs a **reservation** — two separate requirements, verified live in [`functions/image/`](../functions/image/).

**Reservation (Editions) required, not just recommended:** `MATRIX_FACTORIZATION` and the four image-preprocessing functions (`ML.DECODE_IMAGE`, `ML.RESIZE_IMAGE`, `ML.CONVERT_COLOR_SPACE`, `ML.CONVERT_IMAGE_TYPE`) are the only things in this project that fail outright under on-demand pricing. Everything else in these tables runs on-demand. Neither requirement needs a *commitment* — a small `ENTERPRISE` autoscale reservation with 0 baseline slots is enough, and both [`models/matrix_factorization/`](../models/matrix_factorization/) and [`functions/image/`](../functions/image/) create one in Setup and delete it in Cleanup.

## 2. Task → `ML.EVALUATE` metric columns

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

**Which evaluator?**

| You have | Function | Returns |
|---|---|---|
| A trained model and an eval set | [`ML.EVALUATE`](model-lifecycle-functions.md#mlevaluate) | The table above, including `log_loss` and `roc_auc` |
| Two columns: actual and predicted (no model) | [`ML.METRICS`](model-free-functions.md#mlmetrics) | The regression six, or `precision`/`recall`/`accuracy`/`f1_score`. No `log_loss`, no `roc_auc` |
| Raw data and no model at all | [`AI.EVALUATE`](../../bq-ai-functions/RESOURCES.md) | Same names as `ML.METRICS`, but trains TabFM/TimesFM internally and is not reproducible run to run |

> For `ML.METRICS` and `AI.EVALUATE` alike, `precision`/`recall`/`f1_score` on a **`BOOL`** label describe the positive (`TRUE`) class alone, while the **`STRING`** rendering of the same values is macro-averaged across classes. `accuracy` is identical either way. Measured on one table: precision `0.5238` versus `0.7497`.

## 3. Capability matrix (per model type)

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

## 4. Explainability / weights functions

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

## 5. Connection matrix

| Model category | Connection required? |
|---|---|
| All natively-trained models (GLM, trees, DNN, k-means, PCA, autoencoder, MF, ARIMA, contribution analysis) | **No** |
| AutoML | No (uses an internal `ML_EXTERNAL` Vertex AI job) |
| Imported (TF / TFLite / ONNX / XGBoost) | No for `ML.PREDICT`; **Yes** (Cloud Resource + reservation) only for object-table serving |
| Remote (custom Vertex AI endpoint) | **Yes** — Cloud Resource Connection |
| `EXPORT MODEL` to GCS | No (writer needs GCS write IAM, not a BQ connection) |

## 6. Which model-free function? (no `CREATE MODEL`, no connection)

| You want to know | Function | Notes |
|---|---|---|
| What is in this table — types, nulls, ranges, quantiles, top values | [`ML.DESCRIBE_DATA`](model-free-functions.md#mldescribe_data) | One relation, one row per column. `top_k` defaults to **1** and `num_quantiles` to **2**; both are usually too low. Quantiles are `APPROX_QUANTILES` and **not stable across runs**. |
| What moves with my target, across many candidate features at once | [`ML.CORRELATION`](model-free-functions.md#mlcorrelation) | One target against many numeric columns, plus `dimension_cols` for per-segment coefficients in the same query. **Preview.** |
| The correlation of exactly one pair | `CORR()` | Same number as `ML.CORRELATION`'s `PEARSON` (to ~15 significant digits). Reach for the function when you want many columns, many segments, or a rank method. |
| Whether two datasets have drifted apart | [`ML.VALIDATE_DATA_DRIFT`](model-management-monitoring.md#mlvalidate_data_drift) | Two relations. Categorical metrics are statistics of the data; the numeric metric is a divergence over two fixed-size histograms — read it next to the two ranges. |
| Whether serving data has drifted from what a model was trained on | [`ML.VALIDATE_DATA_SKEW`](model-management-monitoring.md#mlvalidate_data_skew) | One relation plus a model's stored training statistics — no copy of the training data needed. |
| How good a saved set of predictions is | [`ML.METRICS`](model-free-functions.md#mlmetrics) | See *Which evaluator?* above. |
| What a feature table knew about each entity at a past moment | [`ML.FEATURES_AT_TIME` / `ML.ENTITY_FEATURES_AT_TIME`](model-free-functions.md#point-in-time-feature-retrieval-mlfeatures_at_time-mlentity_features_at_time) | See the next table. |

> **Which rank method?** `ML.CORRELATION`'s `SPEARMAN` uses SQL `RANK()` — **competition (min) ranks** — where SciPy, R and pandas default to mid-ranks, so tied data disagrees in the second decimal (`0.172612` against `0.167215` on one census pair). Reproduce it with `pandas.Series.rank(method='min')`. `KENDALL` in the same function *is* tie-corrected (tau-b) and is genuinely **O(n²)** — sample before reaching for it.

## 7. Point-in-time feature retrieval: which of the two?

| You need | Function |
|---|---|
| One shared cutoff for every entity — serving *now*, or one snapshot date | [`ML.FEATURES_AT_TIME`](model-free-functions.md#mlfeatures_at_time) |
| A different cutoff per entity — a training set, an audit sample | [`ML.ENTITY_FEATURES_AT_TIME`](model-free-functions.md#mlentity_features_at_time) |
| Both against one feature table | That is offline/online parity — see [`workflows/feature_store/`](../workflows/feature_store/) |

> **`ignore_feature_nulls` is a property of the table's shape, not a default to copy.** On a **sparse** history it repairs entities whose latest row simply did not carry that feature; on a **dense** one it invents a value from an older, different event. Neither call errors and neither output looks wrong — [`functions/feature_store/`](../functions/feature_store/) measures both directions on the same table.
