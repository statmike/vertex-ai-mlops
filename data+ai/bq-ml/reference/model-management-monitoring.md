![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Fdata%2Bai%2Fbq-ml%2Freference&file=model-management-monitoring.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/data%2Bai/bq-ml/reference/model-management-monitoring.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ml/reference/model-management-monitoring.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ml/reference/model-management-monitoring.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ml/reference/model-management-monitoring.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ml/reference/model-management-monitoring.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-ml/reference/model-management-monitoring.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-ml/reference/model-management-monitoring.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# Model Management & Monitoring

> Part of the [BigQuery ML — Detailed Reference](../RESOURCES.md) · [Project README](../README.md)



---

## `EXPORT MODEL`

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
| `BOOSTED_TREE_CLASSIFIER`, `BOOSTED_TREE_REGRESSOR`, `RANDOM_FOREST_CLASSIFIER`, `RANDOM_FOREST_REGRESSOR` | XGBoost Booster — **format depends on the training-time `xgboost_version`**: `model.bst` (legacy binary) at the `0.9` default, `model.ubj` (UBJSON) at `2.1`. See the version gotcha below. |
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
- **To visualize a boosted-tree/random-forest ensemble** (`EXPORT MODEL` → XGBoost Booster, `model.bst` or `model.ubj` depending on `xgboost_version`): download it and load with `xgboost.Booster().load_model(...)`, then `xgboost.plot_tree(booster, tree_idx=0)` (the older `num_trees=` keyword still works but emits a `FutureWarning` on xgboost 2.1+). See the gotchas below — they are load-bearing, not optional.
- **If the model exists only to be exported and read back in Python, train it with `xgboost_version = '2.1'`.** It turns a pinned-dependency problem into a plain file read. It is not free, though: on a `BOOSTED_TREE_*` model that trains more than 10 iterations, `'2.1'` also empties `ML.TRAINING_INFO` (measured — see that function's gotcha). `RANDOM_FOREST_*` is single-pass and pays nothing. So set it freely on random forests and on any tree model whose loss curve you don't need; on a boosted tree you're choosing between the modern export and the training history.

**Limitations:**
- Dataset and destination bucket must be in the **same location**.
- Not supported if `ARRAY`, `TIMESTAMP`, or `GEOGRAPHY` feature types were used in input/post-transform data; post-transformed data also cannot be `ARRAY<STRUCT<INT64, FLOAT64>>`.
- `MATRIX_FACTORIZATION` exports have a ~1 GB size cap (reduce `num_factors` if too large).
- AutoML model exports do not support Agent Platform online prediction.
- Models trained with `TRANSFORM` before 2023-09-18 must be retrained for Model Registry online prediction.
- Remote models and ARIMA_PLUS/time-series models cannot be exported.
- **Verified gotcha — XGBoost version compatibility, and how to avoid it entirely:** at the **default** `xgboost_version = '0.9'`, `BOOSTED_TREE_*`/`RANDOM_FOREST_*` exports use a **legacy binary format**. Modern `xgboost` (2.0+, the current `pip install xgboost` default) **cannot load `model.bst`** — `xgb.Booster().load_model(...)` raises `Check failed: str[0] == '{'`. Pin an older release to load/visualize it locally (verified working: `xgboost==1.7.6`, which emits only a compatibility warning). **Training with `xgboost_version = '2.1'` removes the problem at the source:** the export becomes `model.ubj` (UBJSON) instead of `model.bst`, and it loads cleanly in current `xgboost` with no pin and no warning at all (verified end-to-end against `xgboost` 3.3.0, classifier and regressor). The filename changes too, so any download step that hard-codes `model.bst` has to branch on the version. `2.1` reached GA on 2026-08-27 and is opt-in only — the default did not move.
- **Verified gotcha — feature names are not preserved, at either version:** the loaded booster's `feature_names` comes back `None` (generic `f0`, `f1`, ... in `get_dump()`/plots). Set `booster.feature_names` manually to the training query's non-label `SELECT` column order — this 1:1 mapping held up when checked against a model's actual split thresholds (`num_features()` matched the raw column count exactly, with no expansion for categoricals). Verified for both `BOOSTED_TREE_CLASSIFIER` and `BOOSTED_TREE_REGRESSOR`, and re-verified on a `2.1` export — **this one is not fixed by the newer library**, unlike the format gotcha above.
- **`BOOSTED_TREE_REGRESSOR`-specific, and version-dependent:** at the `0.9` default, loading the exported booster also prints `reg:linear is now deprecated in favor of reg:squarederror` — a harmless legacy-objective-name warning (in addition to the `XGBoost < 1.0.0` compatibility warning above), not an error. At `xgboost_version = '2.1'` the objective is written as `reg:squarederror` and the load is silent (verified: zero warnings captured).

**Locations:** Dataset region must equal the GCS bucket region/multi-region.

**BigFrames API:** `bigframes.ml` estimators expose `model.to_gbq(...)` for persistence in BigQuery; GCS export is performed via the SQL `EXPORT MODEL` statement or `bq extract --model`. No dedicated one-call BigFrames GCS-export helper.

**Repo example (tested):**
- `data+ai/bq-ml/models/export/export.ipynb` — the dedicated general-purpose `EXPORT MODEL` notebook: a `LOGISTIC_REG` (→ TF SavedModel, downloaded and run with `tf.saved_model.load()` + `infer(...)` entirely outside BigQuery) and a small `BOOSTED_TREE_CLASSIFIER` (trained with `xgboost_version = '2.1'`, so the export is a `model.ubj` → downloaded and scored locally with an **unpinned** `xgboost` via `booster.get_score(importance_type='gain')`; the `feature_names` gotcha below still applies and is reproduced here independently). Also demonstrates `model_registry='VERTEX_AI'` as a `CREATE MODEL`-time alternative to export (registry storage only, no live serving cost) and the `bq extract --model --destination_format=...` CLI equivalent. **Verified finding:** dropping a model registered via `model_registry='VERTEX_AI'` also cascade-deletes its Vertex AI Model Registry entry — no separate `aiplatform`/`gcloud` deletion step needed.
- `data+ai/bq-ml/models/boosted_tree_classifier/boosted_tree_classifier.sql` (Example 9) and the companion notebook (Step 7) — `xgboost_version = '2.1'` → `EXPORT MODEL` → download `model.ubj` → unpinned `xgboost` → `booster.feature_names` reassigned manually → `xgboost.plot_tree()`. Both gotchas above were caught and verified here, at both `xgboost_version` values.
- The same `EXPORT MODEL ... OPTIONS(URI = 'gs://.../model')` pattern in its other tested homes: [`models/random_forest_classifier/`](../models/random_forest_classifier/) (Example 9) and [`models/random_forest_regressor/`](../models/random_forest_regressor/) (Example 7) — XGBoost Booster format, tree visualization; [`models/boosted_tree_regressor/`](../models/boosted_tree_regressor/) (Example 7); [`models/automl_classifier/`](../models/automl_classifier/) (Example 7) and [`models/automl_regressor/`](../models/automl_regressor/) (Example 6); [`models/transform_only/`](../models/transform_only/) (Example 4) — a transform-only model exports too; [`models/remote/`](../models/remote/) (Example 1) — export as the first hop of the train-in-BQML → deploy-to-a-Vertex-endpoint → call-back-as-a-remote-model round trip.
- `PCA` and `AUTOENCODER` export as TensorFlow SavedModel by the same default path as GLMs, DNNs, `KMEANS`, and `TRANSFORM_ONLY` — see [`models/export/`](../models/export/) Example 2, which records the verified signature shape (one named input tensor **per feature column**, not one packed array, plus `{label}_probs` / `{label}_values` / `predicted_{label}` outputs and categorical vocabularies written as separate asset files).
- Inverse direction (importing a TF SavedModel back into BQML for serving): [`models/imported/`](../models/imported/) — `CREATE MODEL ... model_type = 'TENSORFLOW'`, which the file explicitly cross-references against `EXPORT MODEL`'s quirks in the other direction.


---

## Model monitoring & data validation

BigQuery ML ships four built-in functions for **training/serving skew** and **data drift** monitoring.
They are model-light: skew uses statistics saved at training time
(no original training data needed); drift compares two arbitrary datasets. None require a Cloud resource
connection. The optional `MODEL` argument only enables a Vertex AI **visualization link** and requires the
model to be registered in Vertex AI Model Registry. Two tiers exist:

- **Basic** (`ML.VALIDATE_DATA_SKEW`, `ML.VALIDATE_DATA_DRIFT`) — tabular output, anomaly flags.
- **Advanced / TFDV-compatible** (`ML.TFDV_DESCRIBE`, `ML.TFDV_VALIDATE`) — emit/consume a TensorFlow
  `DatasetFeatureStatisticsList` proto as JSON, for use with the `tensorflow-data-validation` library.

Status: **GA**. See the [Model monitoring overview](https://cloud.google.com/bigquery/docs/model-monitoring-overview).

> Cross-reference: `ML.DETECT_ANOMALIES` (anomaly detection from a trained model) and `AI.DETECT_ANOMALIES`
> (foundation-model time-series anomalies) are distinct — see the model-type entries / `../bq-ai-functions/`.

> **Profiling moved.** `ML.DESCRIBE_DATA` used to be listed here as a fifth, Basic-tier function. It answers a
> different question — *what is in this dataset*, not *has this dataset changed* — so its entry now lives with
> `ML.CORRELATION` under [Model-Free Functions → Exploratory data analysis](model-free-functions.md#exploratory-data-analysis-mldescribe_data-mlcorrelation),
> demonstrated in [`functions/exploration/`](../functions/exploration/). Profile there, monitor here.

## `ML.VALIDATE_DATA_SKEW`
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

**Best practices:** Register the model in Vertex AI (`MODEL_REGISTRY='VERTEX_AI'`) to get clickable distribution visualizations. **MAJOR GOTCHA, verified live: how you sample the comparison data matters as much as the function call itself.** `SELECT ... LIMIT N` (no `ORDER BY`) on a non-randomly-ordered table returns a non-representative slice — tested on `bigquery-public-data.ml_datasets.census_adult_income`, a `LIMIT 5000` grab flagged `education_num` as `is_anomaly=TRUE` (Jensen-Shannon divergence ~0.65 vs. a 0.3 threshold) even though it came from the exact same table the model trained on. Switching to `WHERE RAND() < p` for a true random sample dropped every column's divergence to near-zero, correctly reporting no skew. A naive `LIMIT` can manufacture a false skew alarm.
**Limitations:** Numerical metric is always Jensen-Shannon divergence (not configurable); needs a model that stored training stats.
**BigFrames API:** No direct equivalent.
**Repo example (tested):** [`functions/data_quality/`](../functions/data_quality/) Example 2 — the `LIMIT`-vs-`RAND()` sampling gotcha above, run against a self-contained scratch `LOGISTIC_REG` model. `census_adult_income` is not randomly ordered, so a `LIMIT 5000` "serving" slice of the *identical* source table makes `education_num` flag `is_anomaly = TRUE` at JS divergence ~0.65 (threshold 0.3); switching to `WHERE RAND() < 0.15` drops every column's divergence to near zero, confirming the alarm was a sampling artifact rather than real skew.

---

## `ML.VALIDATE_DATA_DRIFT`
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
**Repo example (tested):** [`functions/data_quality/`](../functions/data_quality/) Example 3 — real (non-sampling-artifact) drift on `census_adult_income`: incorporated self-employed workers (`workclass = 'Self-emp-inc'`) skew toward more education than a random population sample, correctly flagged; plus a live `categorical_metric_type` comparison showing `L_INFTY` and `JENSEN_SHANNON_DIVERGENCE` flag genuinely different columns at the same threshold (`race`/`sex` drop out under JS while `L_INFTY` flags all three), and a `thresholds` per-column override demo. **`data+ai/bq-ml/pipelines/`** uses the 3-argument form (no `MODEL` — verified live that a plain `CREATE MODEL`-trained model doesn't qualify as the "Model Registry MODEL" the optional argument requires) as the core drift-check trigger for a real conditional-retrain pipeline, re-expressed across three orchestrators: `sql_scripting/` (inside a multi-statement `BEGIN...END` script), `cloud_workflows/` (via the BigQuery connector, built across several `assign` steps due to a 400-character YAML expression limit), and `composer_airflow/` (`BigQueryInsertJobOperator` + `BranchPythonOperator` reading the result via XCom). All three find the identical real, non-contrived signal — 5 of 12 GA4 behavioral features drift genuinely (`total_engagement_time_msec` strongest), driven by a real Black Friday/Cyber Monday population shift in the underlying data, not a sampling artifact.

---

## `ML.TFDV_DESCRIBE`
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
**Repo example (tested):** [`functions/data_quality/`](../functions/data_quality/) Example 4 — `ML.TFDV_DESCRIBE` on `census_adult_income`, JSON-parsed in SQL so the proto's contents are readable without installing the `tensorflow-data-validation` Python package. Rendering the proto graphically (`tfdv.visualize_statistics`) requires that package and is outside this project's dependency set; the parsed output carries the same measurements.

---

## `ML.TFDV_VALIDATE`
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
**Repo example (tested):** [`functions/data_quality/`](../functions/data_quality/) Example 4 — both `'DRIFT'` mode (reproducing the same `education_num` signal as `ML.VALIDATE_DATA_DRIFT` above, JSON-parsed to show the actual `drift_skew_info` measurement rather than a truncated raw string) and `'SKEW'` mode (same divergence value, confirming `'SKEW'`/`'DRIFT'` differ only in the baseline schema's comparator type and semantic framing, not the underlying computation).
