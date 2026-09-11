![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Fdata%2Bai%2Fbq-ai-functions%2Freference&file=predictive-ai.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/data%2Bai/bq-ai-functions/reference/predictive-ai.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/reference/predictive-ai.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/reference/predictive-ai.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/reference/predictive-ai.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/reference/predictive-ai.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-ai-functions/reference/predictive-ai.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-ai-functions/reference/predictive-ai.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# Predictive AI

> Part of the [BigQuery AI Functions Resources](../RESOURCES.md) · [Project README](../README.md)

These functions make predictions from historical or tabular data using BigQuery ML's built-in foundation models. None of them require creating, training, or managing a model object -- the model is built in.

Two model families sit behind this section:

- **TimesFM** -- a time series foundation model, used by `AI.FORECAST`, `AI.DETECT_ANOMALIES`, and `AI.EVALUATE`. These three share a common parameter pattern (`data_col`, `timestamp_col`, `id_cols`) and the same model versions.
- **TabFM** -- a tabular foundation model, used by `AI.PREDICT` and by `AI.EVALUATE`'s second syntax. TabFM does zero-shot regression and classification by in-context learning: you hand it a training table and a prediction table in the same call, and it never persists a model.

> **Cross-links (owned by `../bq-ml/`, not duplicated here):** model-free time-series description --- [`ML.TREND`, `ML.SEASONALITY`, `ML.DETECT_CHANGE_POINTS`](../../bq-ml/RESOURCES.md) (Preview 2026-08-20), built in [`../bq-ml/functions/time_series/`](../../bq-ml/functions/time_series/). These need no `CREATE MODEL` *and* no foundation model: they decompose a series into trend and seasonal components and locate sustained structural shifts. Reach for them when the question is *what has this series been doing* rather than *what will it do next*. The trainable statistical alternative to `AI.FORECAST` is [`ARIMA_PLUS`/`ARIMA_PLUS_XREG`](../../bq-ml/RESOURCES.md).
>
> **Anomaly vs. change point** --- `AI.DETECT_ANOMALIES` flags individual points that deviate from a TimesFM forecast baseline; `ML.DETECT_CHANGE_POINTS` finds windows where the level shifted *and stayed shifted*, with no model and no baseline. A spike that returns to normal the next day is an anomaly and not a change point; a permanent step up in volume is a change point that may never register as an anomaly. Measured on one shared series: 79 row-level anomalies against 2 change windows, zero overlap.

**Key relationships:**
- `AI.FORECAST` generates future time series values from historical data.
- `AI.DETECT_ANOMALIES` compares target data against a forecast baseline from historical data to identify anomalous points.
- `AI.PREDICT` predicts a label column for unlabeled rows, given a labeled training table. Regression or classification, chosen automatically from the label column's type.
- `AI.EVALUATE` is dual-purpose: it computes forecasting metrics for a TimesFM forecast, **or** regression/classification metrics for a TabFM prediction. Which branch runs is determined by the arguments you pass.

| Attribute | AI.FORECAST | AI.DETECT_ANOMALIES | AI.PREDICT | AI.EVALUATE |
|-----------|-------------|---------------------|------------|-------------|
| **Status** | GA | GA | Preview | GA (TabFM branch Preview) |
| **Model family** | TimesFM | TimesFM | TabFM | TimesFM or TabFM |
| **Purpose** | Forecast future values | Detect anomalies | Predict a label for unlabeled rows | Evaluate a forecast or a prediction |
| **Input data sources** | 1 (history) | 2 (history + target) | 2 (training + prediction) | 2 (history + actuals, or training + prediction) |
| **Supported Models** | TimesFM 2.5 (default), TimesFM 2.0 | TimesFM 2.5 (default), TimesFM 2.0 | TabFM (not selectable) | TimesFM 2.5 (default), TimesFM 2.0; TabFM on the prediction branch |
| **Default Horizon** | 10 | N/A | N/A | 1024 |
| **Min Data Points** | 3 | 3 | Not specified | 3 |
| **Max Data Points** | 2,048 (2.0) / 15,360 (2.5) | 1,024 (most recent) | See AI.PREDICT limitations | Not specified |
| **Context Window** | Yes (auto-selected) | Yes (auto-selected) | N/A | Yes (auto-selected) |

> **Default model version changed.** All three TimesFM functions -- `AI.FORECAST`, `AI.EVALUATE` and `AI.DETECT_ANOMALIES` -- now default to **TimesFM 2.5** (previously TimesFM 2.0). Google made this change on the reference pages without a release note. Confirmed against live queries with the query cache off, one variant per job: an unpinned call returns values identical to `model => 'TimesFM 2.5'` and different from `model => 'TimesFM 2.0'`, on all three functions. Any existing unpinned query silently changes behavior -- pin `model` explicitly so a future default move cannot shift your numbers.

> **Pinning `model` does not make `AI.EVALUATE` or `AI.DETECT_ANOMALIES` reproducible.** These two return a different answer on a minority of runs even with `model` **and** `context_window` pinned, the query cache off, and a deterministic input. Measured on a synthetic 335-point series forecast 31 points ahead: 2 of 16 `AI.EVALUATE` runs returned a `mean_absolute_error` of `0.5913808905590097` where the other 14 returned `0.8652198481135486` -- a ~32% swing in the headline metric at roughly 1 in 8. The **majority value is the correct one**: MAE computed by hand from `AI.FORECAST` output over the same history and horizon equals `0.8652198481135486` to the last digit. `AI.DETECT_ANOMALIES` behaves the same way; `AI.FORECAST` itself is stable across runs. Not explained by the context window (every legal value was swept), by horizon truncation, or by version mixing -- it occurs on 2.0 and 2.5 alike. The mechanism is not known and is not guessed at here.
>
> **What to do about it.** Treat any `AI.EVALUATE` or `AI.DETECT_ANOMALIES` metric as a *draw*, not a value. Materialize the result once and read the stored table rather than re-running the function, exactly as with `AI.PREDICT`. When a number has to be defensible, recompute it from `AI.FORECAST` output with ordinary SQL -- that path is deterministic and it is how the correct value above was established. If you must re-run, run several times and take the mode rather than the last answer.
>
> **How this was measured, and why it matters for your own testing.** The BigQuery **query cache** hides this entirely: re-running identical SQL returns the cached first result, so an unstable function looks perfectly stable, and changing only the `SELECT` list creates a *different* cache entry, so two "identical" comparison loops can disagree for reasons that have nothing to do with the model. Putting several variants in one `UNION ALL` is equally misleading -- three TimesFM variants in one query returned three distinct values where isolated jobs showed two of them bit-identical. For any determinism or default-version question: **one variant per job, `--nouse_cache` on every job**, collect a value set over ~10 runs and compare *sets* rather than single draws, and cross-check the answer against a function that is deterministic.

---

## `AI.FORECAST`
- **Description:** Table-valued time series forecasting function. Forecasts a time series using BigQuery ML's built-in TimesFM model without requiring model creation or training.
- **Use cases:** Forecasting future values (e.g., daily bike trips), forecasting multiple independent time series using ID columns (e.g., forecast by user type), generating prediction intervals, comparing historical vs forecasted data.
- [documentation](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-forecast)
- **Type:** Table-valued function

**Syntax:**
```sql
SELECT *
FROM AI.FORECAST(
  { TABLE TABLE | (QUERY_STATEMENT) },
  data_col => 'DATA_COL',
  timestamp_col => 'TIMESTAMP_COL'
  [, model => 'MODEL']
  [, id_cols => ID_COLS]
  [, { horizon => HORIZON | forecast_end_timestamp => FORECAST_END_TIMESTAMP }]
  [, confidence_level => CONFIDENCE_LEVEL]
  [, output_historical_time_series => OUTPUT_HISTORICAL_TIME_SERIES]
  [, context_window => CONTEXT_WINDOW]
)
```

**Inputs:**

| Parameter | Type | Required | Default | Range | Description |
|-----------|------|----------|---------|-------|-------------|
| `TABLE` / `QUERY_STATEMENT` | Table/Query | Required | -- | -- | Input data to forecast |
| `data_col` | STRING | Required | -- | -- | Name of the data column. Must be INT64, NUMERIC, BIGNUMERIC, or FLOAT64. |
| `timestamp_col` | STRING | Required | -- | -- | Name of the timestamp column. Must be TIMESTAMP, DATE, or DATETIME. |
| `model` | STRING | Optional | `'TimesFM 2.5'` | -- | `'TimesFM 2.0'` or `'TimesFM 2.5'`. Recommended: TimesFM 2.5 for all new work. |
| `id_cols` | ARRAY\<STRING\> | Optional | -- | -- | ID columns identifying unique time series. Must be STRING, INT64, ARRAY\<STRING\>, or ARRAY\<INT64\>. |
| `horizon` | INT64 | Optional | 10 | [1, 10000] | Number of time series data points to forecast. Mutually exclusive with `forecast_end_timestamp`. |
| `forecast_end_timestamp` | TIMESTAMP | Optional | -- | -- | End timestamp for forecasted values. Horizon is calculated from the end timestamp and input frequency. Mutually exclusive with `horizon`. Valid calculated horizon range: [1, 10000]. |
| `confidence_level` | FLOAT64 | Optional | 0.95 | [0, 1) | Percentage of future values that fall in the prediction interval |
| `output_historical_time_series` | BOOL | Optional | FALSE | -- | When TRUE, returns input data along with forecasted data |
| `context_window` | INT64 | Optional | Auto-selected | See below | Context window length for the TimesFM model |

**Context Window Supported Values:**

| Model | Supported Context Window Lengths |
|-------|----------------------------------|
| TimesFM 2.0 | 64, 128, 256, 512, 1024, 2048 |
| TimesFM 2.5 | 64, 128, 256, 512, 1024, 2048, 4096, 8192, 15360 |

When not specified, the smallest window covering the input data points is auto-selected.

**Outputs (when `output_historical_time_series = FALSE`):**

| Column | Type | Description |
|--------|------|-------------|
| *id_cols* | (inherited) | Time series identifiers |
| `forecast_timestamp` | TIMESTAMP | Timestamps of the forecasted time series |
| `forecast_value` | FLOAT64 | 50% quantile (median) value of the forecast |
| `confidence_level` | FLOAT64 | The confidence level value |
| `prediction_interval_lower_bound` | FLOAT64 | Lower bound of prediction interval |
| `prediction_interval_upper_bound` | FLOAT64 | Upper bound of prediction interval |
| `ai_forecast_status` | STRING | Empty string (zero-length, not `NULL`) if successful; error string if unsuccessful. This is the *only* one of the three TimesFM status columns that behaves this way -- `ai_evaluate_status` and `ai_detect_anomalies_status` return `NULL` on success. |

**Outputs (when `output_historical_time_series = TRUE`):**

| Column | Type | Description |
|--------|------|-------------|
| *id_cols* | (inherited) | Time series identifiers |
| `time_series_type` | STRING | `'history'` or `'forecast'` |
| `time_series_timestamp` | TIMESTAMP | Timestamps |
| `time_series_data` | FLOAT64 | Historical value or forecast median |
| `confidence_level` | FLOAT64 | The confidence level value |
| `prediction_interval_lower_bound` | FLOAT64 | Lower bound (NULL for historical points) |
| `prediction_interval_upper_bound` | FLOAT64 | Upper bound (NULL for historical points) |
| `ai_forecast_status` | STRING | Status |

**Supported models:** TimesFM 2.5 (default), TimesFM 2.0.

**Best practices:** Set `output_historical_time_series` to TRUE to compare historical values with forecasted values. Minimum 3 data points required.

**Limitations:** TimesFM 2.0 max context: 2,048 data points. TimesFM 2.5 max context: 15,360 data points. Additional data points beyond the max are ignored. Minimum 3 data points.

**Locations:** All supported BigQuery ML locations.

**Provisioned throughput:** Not specified. Billed at the evaluation, inspection, and prediction rate (BigQuery ML on-demand pricing).

**BigFrames API:** `bigframes.bigquery.ai.forecast(df, data_col=..., timestamp_col=...)` — Wraps `AI.FORECAST` SQL directly. No model object needed. Supports `id_cols`, `horizon`, `confidence_level`, `context_window`, and `model` parameters. Note: `bigframes.ml.forecasting.ARIMAPlus` is a different model (ARIMA_PLUS, not TimesFM).

> **Wrapper skew:** the BigFrames wrapper still declares `model: str = "TimesFM 2.0"` and its docstring claims 2.0 is the only supported value. The SQL function now defaults to TimesFM 2.5 and accepts both. Calling `bbq.ai.forecast()` without specifying `model` therefore gives you **2.0**, while the equivalent SQL gives you **2.5**. Pass `model` explicitly from BigFrames.

---

## `AI.DETECT_ANOMALIES`
- **Description:** Table-valued function that detects anomalies in time series data using BigQuery ML's built-in TimesFM model. Forecasts expected values from historical data, then compares target data against those forecasts to identify anomalous data points.
- **Use cases:** Detecting anomalous spikes or drops in time series (e.g., sales, bike trips), detecting anomalies across multiple time series simultaneously, computing anomaly probability.
- [documentation](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-detect-anomalies)
- **Type:** Table-valued function -- GA

**Syntax:**
```sql
SELECT *
FROM AI.DETECT_ANOMALIES(
  { TABLE HISTORY_TABLE | (HISTORY_QUERY_STATEMENT) },
  { TABLE TARGET_TABLE | (TARGET_QUERY_STATEMENT) },
  data_col => 'DATA_COL',
  timestamp_col => 'TIMESTAMP_COL'
  [, model => 'MODEL']
  [, id_cols => ID_COLS]
  [, anomaly_prob_threshold => ANOMALY_PROB_THRESHOLD]
  [, context_window => CONTEXT_WINDOW]
)
```

**Inputs:**

| Parameter | Type | Required | Default | Range | Description |
|-----------|------|----------|---------|-------|-------------|
| `HISTORY_TABLE` / `HISTORY_QUERY_STATEMENT` | Table/Query | Required | -- | -- | Historical data used to generate a forecast baseline |
| `TARGET_TABLE` / `TARGET_QUERY_STATEMENT` | Table/Query | Required | -- | -- | Data in which to detect anomalies. Schema must match historical data. |
| `data_col` | STRING | Required | -- | -- | Data column name. Must be INT64, NUMERIC, BIGNUMERIC, or FLOAT64. |
| `timestamp_col` | STRING | Required | -- | -- | Timestamp column name. Must be TIMESTAMP, DATE, or DATETIME. |
| `model` | STRING | Optional | `'TimesFM 2.5'` | -- | `'TimesFM 2.0'` or `'TimesFM 2.5'`. Recommended: TimesFM 2.5 for all new work. |
| `id_cols` | ARRAY\<STRING\> | Optional | -- | -- | ID columns identifying unique time series |
| `anomaly_prob_threshold` | FLOAT64 | Optional | 0.95 | [0, 1) | Threshold for anomaly detection. A target value is anomalous if its anomaly probability exceeds this threshold. |
| `context_window` | INT64 | Optional | Auto-selected | See AI.FORECAST | Context window length for the TimesFM model. Same supported values as AI.FORECAST per model version. |

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| *id_cols* | (inherited) | Time series identifiers |
| `time_series_timestamp` | STRING | Timestamp column |
| `time_series_data` | FLOAT64 | Data column value |
| `is_anomaly` | BOOL | Whether the value is an anomaly |
| `lower_bound` | FLOAT64 | Lower bound of prediction |
| `upper_bound` | FLOAT64 | Upper bound of prediction |
| `anomaly_probability` | FLOAT64 | Probability that the value is an anomaly |
| `ai_detect_anomalies_status` | STRING | **`NULL` on success** -- not an empty string (verified live 2026-09-02); error string if unsuccessful. Test with `IS NOT NULL`, not `<> ''` -- see the note under [`AI.EVALUATE`](#aievaluate)'s forecast outputs. |

**Supported models:** TimesFM 2.5 (default), TimesFM 2.0.

**Best practices:** Historical and target data schemas must match. Use `id_cols` to break anomalies down by dimensions.

**Limitations:** **Not reproducible run to run, and pinning `model` does not fix it** -- a minority of runs return a different anomaly set and different baselines even with `model` and `context_window` pinned and the query cache off, the same behavior measured in detail on `AI.EVALUATE`. Materialize the result once rather than re-running the function; see the reproducibility note at the top of this section. Only the most recent 1,024 time points are evaluated (contact bqml-feedback@google.com for more). Minimum 3 data points required.

**Locations:** All supported BigQuery ML locations.

**Provisioned throughput:** Not specified. Billed at the evaluation, inspection, and prediction rate.

**BigFrames API:** No direct equivalent for TimesFM-based anomaly detection. Use `%%bigquery` magics or `session.read_gbq_query()` to execute AI.DETECT_ANOMALIES SQL from BigFrames. Note: `bigframes.ml.forecasting.ARIMAPlus.detect_anomalies()` exists but uses ARIMA_PLUS, not TimesFM.

---

## `AI.PREDICT`
- **Description:** (Preview) Table-valued function that performs zero-shot regression and classification on structured data using TabFM, Google's pre-trained tabular foundation model. You pass a labeled training table and an unlabeled prediction table in a single call; the model learns in context. There is no `CREATE MODEL`, no training job, no connection, no endpoint, and no persisted model object.
- **Use cases:** Predicting a numeric or categorical column without building a model, filling in missing structured attributes, quick baselines before investing in a trained model, prediction inside an analytics pipeline where a model artifact would be overhead.
- [documentation](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-predict)
- **Type:** Table-valued function (TVF) -- Preview

**Syntax:**
```sql
AI.PREDICT(
  { TABLE TRAINING_TABLE | (TRAINING_QUERY) },
  { TABLE PREDICTION_TABLE | (PREDICTION_QUERY) }
  [, label_col => 'LABEL_COL' ]
)
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `TRAINING_TABLE` / `TRAINING_QUERY` | Table/Query | Required | -- | Labeled training data. Must contain the label column; **every other column is treated as a feature**. |
| `PREDICTION_TABLE` / `PREDICTION_QUERY` | Table/Query | Required | -- | Rows to predict. Must contain all training feature columns; extra columns are allowed. |
| `label_col` | Named arg, STRING | Optional | `'label'` | Name of the label column in the training data. A column literally named `label` needs no argument. |

Feature and label columns must be `STRING`, `BOOL`, `INT64`, `FLOAT64`, `NUMERIC`, or `BIGNUMERIC`. `DATE`, `TIMESTAMP`, `BYTES`, `JSON`, `GEOGRAPHY`, `ARRAY`, and `STRUCT` are rejected -- `EXTRACT` date parts into integers first.

**Task selection is implicit and type-driven.** There is no `task_type` argument:

| Label column type | Task | Added output columns |
|---|---|---|
| `INT64`, `FLOAT64`, `NUMERIC`, `BIGNUMERIC` | Regression | `predicted_<label>` (same type as the label) |
| `BOOL`, `STRING` | Classification | `predicted_<label>`, plus `predicted_<label>_probs` as `ARRAY<STRUCT<label STRING, prob FLOAT64>>` |

> **Cast your label.** A categorical encoded as INT64 (0/1, or a 1–5 rating) is silently treated as *regression* and you get fractional predictions with no probabilities. Cast it to `STRING` or `BOOL` to get classification. This consequence follows from the documented rule but is not itself documented.

The `label` subfield of `predicted_<label>_probs` is typed `STRING` even when the label column is `BOOL`. Array element ordering is not documented.

**Outputs:** The prediction input's columns plus the predicted column(s) above.

> **Doc bug.** The reference page states that AI.PREDICT "returns the columns from the training table or query result". Both of Google's own worked examples contradict this -- the returned rows are the *prediction* rows. Trust the behavior, not the sentence.

**Supported models:** TabFM only. Not selectable -- there is no `model` argument and no version pinning.

**Best practices:** Keep the feature set tight; the 20-column cap is a hard limit, not a guideline. Split train/predict deterministically (e.g. `FARM_FINGERPRINT`) so that the same rows train and predict on every run -- note this pins the *split* only; the predictions themselves are not reproducible (see Limitations). Pair every AI.PREDICT call with `AI.EVALUATE` on a held-out set -- without a metric you have no idea whether the zero-shot prediction is any good. Use it as a baseline: if a trained `CREATE MODEL` beats it materially, the training cost is justified; if not, you have saved a model lifecycle.

**Limitations:**
- **Output is not deterministic.** Repeating a byte-identical `AI.PREDICT` call over the same `FARM_FINGERPRINT` split returns slightly different predictions -- consistent with the model averaging shuffled ensemble passes (`n_ensembles`, whose value Google does not document). Demonstrated by `functions/ai_predict/ai_predict.ipynb` cells 25 and 28, whose top-5 multisets differ (`5760` vs `5728` in one slot) despite identical SQL and an `ORDER BY value DESC LIMIT 5`, so tie-breaking cannot explain it. The `workflows/tabular_prediction/` notebook shows the downstream consequence: `AI.EVALUATE` scores its *own* fresh TabFM predictions rather than the rows you materialized, so the two disagree (measured across four runs: regression MAE 236.52 / 236.35 / 235.84, classification accuracy 0.9468 / 0.9362 / 0.9468 -- regression drift well under 1%, classification drift about 1pp, or 2 rows in 94). **Materialize results once and join to them; do not re-run the prediction to reproduce a number.** Drift appears to be input-dependent -- `workflows/data_enrichment/` reproduced exactly across two runs on a 6-row prediction relation -- so absence of drift on a small input is not evidence of determinism.
- **20 feature columns** maximum (documented). Escalation path is emailing bqml-feedback@google.com.
- **10 classification categories** maximum (documented).
- **Practical row ceiling, undocumented but observed:** a call with 10,000 training rows fails with `Resources exceeded ... allotted memory`; 8,000 rows succeeds. Budget for roughly 5,000 training rows on on-demand slots.
- **Latency is flat and high:** 30--95 seconds per call regardless of input size. A notebook with several AI.PREDICT calls takes minutes, not seconds.
- Max prediction rows, max input size, timeouts, concurrency, NULL handling, categorical encoding, and the `n_ensembles` value are all **undocumented**. AI.PREDICT does not appear in any table on the BigQuery quotas page.
- Whether these limits also bind `AI.EVALUATE`'s TabFM branch is undocumented, though it runs the same model.

**Locations:** Not stated on the AI.PREDICT page. The AI.EVALUATE page says TabFM is available in all supported BigQuery ML locations (non-remote models), plus the US and EU multi-regions.

**Pricing:** Today, standard BigQuery slot / bytes-processed pricing. **From 2026-10-30**, TabFM moves to token-based pricing: you are charged for TabFM tokens plus slots/bytes for the non-inference parts of the query.

```
Input tokens  = (train_rows * columns + predict_rows * (columns - 1)) * n_ensembles
Output tokens = predict_rows * n_ensembles
```

at $0.05 / mtok input and $0.20 / mtok output. Note that `n_ensembles` -- the number of shuffled passes the model averages -- is a multiplier on your bill that Google does not document the value of.

**Provisioned throughput:** Not specified.

**BigFrames API:** No wrapper. `bigframes.bigquery.ai` has `forecast` but no `predict` -- checked against **bigframes 2.39.0**, this project's pin in `uv.lock` and the version that executed `functions/ai_predict/ai_predict.ipynb`. Use `%%bigquery` magics or `session.read_gbq_query()`.

---

## `AI.EVALUATE`
- **Description:** Dual-purpose table-valued function. Given history and actuals it evaluates a **TimesFM forecast** (MAE, MSE, RMSE, MAPE, sMAPE, MASE). Given training and prediction inputs plus a `label_col` it evaluates a **TabFM prediction** (regression or classification metrics). Which branch runs is selected entirely by which arguments you pass.
- **Use cases:** Evaluating forecast accuracy, benchmarking model configurations, comparing forecast quality across multiple time series, scoring AI.PREDICT output against a held-out set.
- [documentation](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-evaluate)
- **Type:** Table-valued function -- GA (the TabFM branch is Preview)

**Branch selection:**

| You pass | Branch | Model |
|---|---|---|
| `data_col` + `timestamp_col` | Forecast evaluation | TimesFM |
| `label_col` | Prediction evaluation | TabFM |

**Syntax (TimesFM -- forecast evaluation):**
```sql
SELECT *
FROM AI.EVALUATE(
  { TABLE HISTORY_TABLE | (HISTORY_QUERY_STATEMENT) },
  { TABLE ACTUAL_TABLE | (ACTUAL_QUERY_STATEMENT) },
  data_col => 'DATA_COL',
  timestamp_col => 'TIMESTAMP_COL'
  [, model => 'MODEL']
  [, id_cols => ID_COLS]
  [, horizon => HORIZON]
  [, context_window => CONTEXT_WINDOW]
)
```

**Syntax (TabFM -- prediction evaluation, Preview):**
```sql
SELECT *
FROM AI.EVALUATE(
  { TABLE TRAINING_TABLE | (TRAINING_QUERY) },
  { TABLE PREDICTION_TABLE | (PREDICTION_QUERY) },
  label_col => 'LABEL_COL'
)
```

**Inputs -- TimesFM:**

| Parameter | Type | Required | Default | Range | Description |
|-----------|------|----------|---------|-------|-------------|
| `HISTORY_TABLE` / `HISTORY_QUERY_STATEMENT` | Table/Query | Required | -- | -- | Historical time series data used to generate a forecast |
| `ACTUAL_TABLE` / `ACTUAL_QUERY_STATEMENT` | Table/Query | Required | -- | -- | Actual time series data to evaluate the forecast against |
| `data_col` | STRING | Required | -- | -- | Data column name. Must be INT64, NUMERIC, BIGNUMERIC, or FLOAT64. |
| `timestamp_col` | STRING | Required | -- | -- | Timestamp column name. Must be TIMESTAMP, DATE, or DATETIME. |
| `model` | STRING | Optional | `'TimesFM 2.5'` | -- | `'TimesFM 2.0'` or `'TimesFM 2.5'`. Recommended: TimesFM 2.5 for all new work. |
| `id_cols` | ARRAY\<STRING\> | Optional | -- | -- | ID columns identifying unique time series |
| `horizon` | INT64 | Optional | 1024 | [1, 10000] | Number of forecasted time points to evaluate |
| `context_window` | INT64 | Optional | Auto-selected | See AI.FORECAST | Context window length for the TimesFM model. Same supported values as AI.FORECAST per model version. |

**Inputs -- TabFM:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `TRAINING_TABLE` / `TRAINING_QUERY` | Table/Query | Required | -- | Labeled training data. Every column other than the label is a feature. |
| `PREDICTION_TABLE` / `PREDICTION_QUERY` | Table/Query | Required | -- | Labeled evaluation data. Must contain all training feature columns. |
| `label_col` | STRING | **Required** | none | Label column name. **Unlike AI.PREDICT, this has no default** -- AI.PREDICT falls back to `'label'`, AI.EVALUATE does not. A `STRING`/`BOOL` label evaluates classification; a numeric label evaluates regression. |

The TabFM branch accepts no `model`, `horizon`, `id_cols`, `context_window`, `data_col`, or `timestamp_col`.

**Outputs -- TimesFM:**

| Column | Type | Description |
|--------|------|-------------|
| *id_cols* | (inherited) | Time series identifiers |
| `mean_absolute_error` | FLOAT64 | MAE for the time series |
| `mean_squared_error` | FLOAT64 | MSE for the time series |
| `root_mean_squared_error` | FLOAT64 | RMSE for the time series |
| `mean_absolute_percentage_error` | FLOAT64 | MAPE for the time series |
| `symmetric_mean_absolute_percentage_error` | FLOAT64 | sMAPE for the time series |
| `mean_absolute_scaled_error` | FLOAT64 | MASE for the time series |
| `ai_evaluate_status` | STRING | **`NULL` on success** -- not an empty string; error string if unsuccessful. A common value is `The time series data is too short.` |

> **Test this column with `IS NOT NULL`, not `<> ''`.** The three TimesFM status columns are *not* consistent with each other, verified live 2026-09-02: `ai_evaluate_status` and `ai_detect_anomalies_status` come back **`NULL`** on success (`IS NULL` is `true`, `LENGTH` is `NULL`), while `ai_forecast_status` comes back as a genuine **zero-length empty string** (`IS NULL` is `false`, `LENGTH` is `0`). So on AI.EVALUATE and AI.DETECT_ANOMALIES, `WHERE ai_evaluate_status = ''` matches nothing at all, and `WHERE ai_evaluate_status <> ''` silently drops **every successful row** -- three-valued logic makes the `NULL` comparison unknown, not true. Select failures with `IS NOT NULL` and successes with `IS NULL`. Only AI.FORECAST's column behaves the way the empty-string wording suggests.

**Outputs -- TabFM regression** (6 columns; no `ai_evaluate_status`, no id passthrough):

| Column | Type | Description |
|--------|------|-------------|
| `mean_absolute_error` | FLOAT64 | MAE for the data |
| `mean_squared_error` | FLOAT64 | MSE for the data |
| `mean_squared_log_error` | FLOAT64 | Mean squared logarithmic error |
| `median_absolute_error` | FLOAT64 | Median absolute error |
| `r2_score` | FLOAT64 | Coefficient of determination |
| `explained_variance` | FLOAT64 | Explained variance |

**Outputs -- TabFM classification** (4 columns):

| Column | Type | Description |
|--------|------|-------------|
| `precision` | FLOAT64 | Precision -- macro-averaged across classes for a `STRING` label, the positive (`TRUE`) class alone for a `BOOL` label |
| `recall` | FLOAT64 | Recall -- same rule as `precision` |
| `accuracy` | FLOAT64 | Accuracy of the prediction; identical under either label type |
| `f1_score` | FLOAT64 | F1 -- same rule as `precision`. When macro-averaged it is the mean of the per-class F1s, not the F1 of the macro precision and recall |

> **GOTCHA -- the label column's TYPE decides which convention you get, and it is not announced anywhere in the output.** A `BOOL` `label_col` is scored as **binary**: `precision`, `recall` and `f1_score` describe the positive (`TRUE`) class only. The `STRING` rendering of the identical values is scored as **multiclass and macro-averaged**, even with exactly two classes. `accuracy` is the same either way. Measured on one imbalanced problem (12 positives of 62 rows, TabFM confusion matrix TP 12 / FP 11 / FN 0 / TN 39): the `BOOL` label returned precision `0.5217391304347826` and recall `1.0`, the `STRING` label returned `0.7608695652173914` and `0.89` -- the two-class means. Four isolated runs of each agreed. On balanced data the two nearly coincide, which is how this hides until the classes are lopsided. **This is a BigQuery-wide convention, not an `AI.EVALUATE` behavior** -- `ML.METRICS` follows the identical rule, measured side by side in [`bq-ml/functions/evaluation/`](../../bq-ml/functions/evaluation/).

> Note what is **missing** relative to `ML.EVALUATE` on a trained classification model: TabFM's AI.EVALUATE returns no `log_loss` and no `roc_auc`, and no confusion matrix. If you need threshold-tuning or ranking metrics, this function will not give them to you.

**Supported models:** TimesFM 2.5 (default), TimesFM 2.0 on the forecast branch. TabFM on the prediction branch, where the `model` argument is not accepted.

**Best practices:** For forecasting, split data into historical (for forecasting) and actual (for comparison) portions using date-based filtering, and use `id_cols` to evaluate across multiple time series. For prediction, pass AI.EVALUATE exactly the same training and holdout inputs you passed AI.PREDICT -- the pair is only meaningful if the split matches.

**Limitations:** **Not reproducible run to run on either branch, and pinning `model` does not fix it** -- a minority of runs (measured at 2 of 16, with `model` and `context_window` both pinned and the query cache off) return a materially different metric, a ~32% swing in `mean_absolute_error` in the measured case. The majority value is the correct one, verified by recomputing MAE from `AI.FORECAST` output. See the reproducibility note at the top of this section for the full measurement and the workaround. Minimum 3 data points required on the forecast branch. Default horizon is 1,024 (unlike AI.FORECAST which defaults to 10). TimesFM silently ignores data points beyond the max context (2,048 for 2.0, 15,360 for 2.5). On the TabFM branch, AI.PREDICT's documented caps -- **20 feature columns** and **10 classification categories** -- apply to the same model, though the AI.EVALUATE page has no Limitations section and does not restate them.

**Locations:** All supported BigQuery ML locations.

**Provisioned throughput:** Not specified. Billed at the evaluation, inspection, and prediction rate.

**BigFrames API:** No direct equivalent for either branch. Use `%%bigquery` magics or `session.read_gbq_query()` to execute AI.EVALUATE SQL from BigFrames. Note: `bigframes.ml.forecasting.ARIMAPlus.evaluate()` exists but uses ARIMA_PLUS, not TimesFM.
