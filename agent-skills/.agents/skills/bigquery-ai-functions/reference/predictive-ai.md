# Predictive AI in BigQuery AI Functions

Zero-training prediction from two pre-trained foundation models: **TimesFM** for time series (`AI.FORECAST`, `AI.DETECT_ANOMALIES`, and the forecast branch of `AI.EVALUATE`) and **TabFM** for tabular rows (`AI.PREDICT`, and the tabular branch of `AI.EVALUATE`). Neither requires `CREATE MODEL`, a connection, an endpoint, or any persisted model object.

Contents: [Options](#options) · [Choosing among them](#choosing-among-them) · [Gotchas verified in this repo](#gotchas-verified-in-this-repo) · [Canonical snippets](#canonical-snippets) · [Go deeper](#go-deeper)

## Options

| Function | What it does | Use this when |
|----------|---------------|----------------|
| `AI.FORECAST` | Zero-training time series forecasting on TimesFM. Returns forecasted values, confidence intervals, and optionally the historical series alongside the forecast. | You want a quick forecast of future values with no `CREATE MODEL` step, no connection, no training. |
| `AI.DETECT_ANOMALIES` | Builds a TimesFM forecast baseline from historical data, then compares a separate target dataset against that baseline to flag anomalous points with a probability score. | You want to flag outliers/anomalies in a series (or across many series via `id_cols`) against expected behavior. |
| `AI.PREDICT` | Zero-shot regression **or** classification on tabular rows using TabFM, a pre-trained tabular foundation model. Learns in-context from a training relation at query time; nothing is fitted or stored. | You want a prediction on structured rows immediately, with no training step — a baseline, a one-off, or a gap-fill on a column. |
| `AI.EVALUATE` | **Two distinct branches.** Forecast branch: generates a TimesFM forecast from history and scores it against actuals (MAE, MSE, RMSE, MAPE, sMAPE, MASE). Tabular branch: scores an `AI.PREDICT`-shaped call by passing `label_col`. | You want to score a forecast, benchmark context-window configurations, or measure TabFM accuracy on held-out rows. |

## Choosing among them

- **"I want a quick forecast with no model training"** → `AI.FORECAST`. Real limits vs. BigQuery ML's `ARIMA_PLUS`: no custom holiday effects, no external regressors (no XREG equivalent), no hierarchical reconciliation, and no direct control over forecast bounds beyond `confidence_level`. It's a fixed-architecture foundation model, not a trainable per-series statistical model.
- **"I want to flag outliers/anomalies in a series"** → `AI.DETECT_ANOMALIES`. It requires two inputs (a history table to build the baseline forecast, and a target table to test) with matching schemas — a materially different shape than `AI.FORECAST`'s single-input call.
- **"I want to know where the series *changed*, not which points are odd"** → neither of the above. `ML.DETECT_CHANGE_POINTS` (sibling `bigquery-ml` skill, Preview 2026-08-20) finds windows where the level shifted *and stayed shifted*, with no model and no forecast baseline; `ML.TREND`/`ML.SEASONALITY` decompose the series the same way. A spike that returns to normal the next day is an anomaly and not a change point; a permanent step up in volume is a change point that may never register as an anomaly. Measured on one shared series: 79 row-level `AI.DETECT_ANOMALIES` hits against 2 change windows, **zero overlap** — orthogonal detectors, not two sensitivities of one. Caveat before recommending it: all three of those TVFs gap-fill each series to its own span first, so on a series with a data outage the interpolation manufactures the structural break they then report. Profile the gaps first.
- **"I want to predict a column on structured rows"** → `AI.PREDICT`. Task type is inferred from the label column's **type**, not from a parameter (see gotchas — this is the single easiest thing to get wrong).
- **"I want to score how good a prediction was"** → `AI.EVALUATE`, but pick the right branch. Passing forecast-shaped and tabular-shaped arguments together fails.
- **When to reach for `../../bq-ml/` instead:** you need training-time control, scheduled retraining, interpretable coefficients, or a model artifact you can version and serve. `ARIMA_PLUS` is BQML's trainable alternative to `AI.FORECAST`; `LINEAR_REG`/`LOGISTIC_REG`/`BOOSTED_TREE_*` are the trainable alternatives to `AI.PREDICT`.

## Gotchas verified in this repo

### TimesFM (forecasting)

- **The default model version is TimesFM 2.5, not 2.0.** This flipped without a release note. Confirmed by running the same `AI.FORECAST` query three ways against `bigquery-public-data.new_york_citibike.citibike_trips`: unpinned and `'TimesFM 2.5'` agree to the last digit, while `'TimesFM 2.0'` differs (e.g. 24125.2324 vs 24596.082 on the first forecast point). **Pin `model` explicitly** so a future default move cannot shift your numbers — any unpinned forecast written before this flip now returns different values. The flip applies to all three TimesFM functions: `AI.FORECAST`, `AI.EVALUATE` and `AI.DETECT_ANOMALIES`.
- **Pinning is not the same as reproducibility, and for two of the three functions it does not deliver it.** `AI.EVALUATE` and `AI.DETECT_ANOMALIES` return a different answer on a minority of runs even with `model` **and** `context_window` both pinned and the query cache off. Measured on a deterministic synthetic series: 2 of 16 `AI.EVALUATE` runs returned `mean_absolute_error` `0.5913808905590097` where the other 14 returned `0.8652198481135486` — a ~32% swing, roughly 1 in 8. The **majority value is the correct one**: it equals MAE computed by hand from `AI.FORECAST` output over the same history and horizon. `AI.FORECAST` itself is stable (12/12). Not explained by the context window (every legal value swept), horizon truncation, or version mixing — it occurs on 2.0 and 2.5 alike. **The mechanism is unknown; do not offer one.** Advise materializing the metric once and reading the stored table rather than re-running the function, and recomputing from `AI.FORECAST` output with ordinary SQL when a number has to be defensible.
- **When testing any of this yourself, the query cache will lie to you.** Re-running identical SQL returns the cached first result, so an unstable function looks perfectly stable; changing only the `SELECT` list creates a different cache entry, so two "identical" loops can disagree for reasons unrelated to the model. Several variants in one `UNION ALL` mislead the same way — three TimesFM variants in one query returned three distinct values where isolated jobs showed two of them bit-identical. Run **one variant per job with `--nouse_cache`**, compare *value sets* over ~10 runs rather than single draws, and cross-check against a function that is deterministic.
- **BigFrames lags the SQL surface here.** `bigframes.bigquery.ai.forecast()` still hardcodes `model="TimesFM 2.0"`, so the same logical call returns different answers from Python than from SQL. Verify the wrapper's default rather than assuming parity.
- `AI.FORECAST` and `AI.EVALUATE` have wildly different default horizons — 10 vs. 1024 — despite sharing the same `horizon` parameter name and range `[1, 10000]`. Don't assume symmetry.
- `AI.DETECT_ANOMALIES` silently caps evaluation at the most recent 1,024 time points regardless of how much target data you pass in; anything older is ignored.
- Max context differs by model version: TimesFM 2.0 tops out at 2,048 data points, TimesFM 2.5 at 15,360. Data points beyond the max are silently ignored rather than erroring.
- All three TimesFM functions require a **minimum of 3 data points**.
- `context_window` is auto-selected (smallest window covering your input) if unset, but if you do set it, it must be one of a fixed discrete set (64/128/256/512/1024/2048 for 2.0; adds 4096/8192/15360 for 2.5).
- `AI.FORECAST`'s output schema changes shape entirely based on `output_historical_time_series`: `FALSE` gives `forecast_timestamp`/`forecast_value`/bounds; `TRUE` gives a unioned `time_series_type` ('history'/'forecast') + `time_series_data` column instead, with bounds NULL for historical rows.
- Each TimesFM function emits a per-row status column (`ai_forecast_status`, `ai_detect_anomalies_status`, `ai_evaluate_status`) holding the error string on failure — check it per-row, since partial failures (one bad series among many `id_cols`) surface there rather than failing the query. **The three columns are not consistent about what "success" looks like** (verified live 2026-09-02): `ai_evaluate_status` and `ai_detect_anomalies_status` return **`NULL`** on success, while `ai_forecast_status` returns a genuine **zero-length empty string**. So `WHERE ai_evaluate_status = ''` matches nothing, and `WHERE ai_evaluate_status <> ''` silently drops **every successful row** — the `NULL` comparison is unknown, not true. **Filter with `IS NOT NULL` / `IS NULL`**, which is correct for all three.
- `horizon` and `forecast_end_timestamp` are mutually exclusive on `AI.FORECAST`.

### TabFM (`AI.PREDICT`)

- **Task type comes from the label column's type, not a parameter.** A categorical label encoded as `INT64` silently trains a *regression* and returns a continuous number instead of a class. Cast coded categoricals to `STRING` before passing them.
- **Output is not deterministic, and `FARM_FINGERPRINT` does not fix it.** A deterministic split pins *which rows* train and predict; it does nothing to the predictions. Repeating a byte-identical `AI.PREDICT` call returns slightly different numbers, consistent with the model averaging shuffled ensemble passes (`n_ensembles`, value undocumented). Measured: regression MAE 236.52 / 236.35 / 235.84 and classification accuracy 0.9468 / 0.9362 / 0.9468 across repeated identical runs — under 1% regression drift, about 1pp on classification. Consequence: `AI.EVALUATE` scores its *own* fresh predictions, not the rows you materialized, so its metrics will not match a recomputation from your stored prediction table. **Materialize predictions once and join to them; never re-run to reproduce a number.** Drift is input-dependent — a 6-row prediction relation reproduced exactly across two runs — so no observed drift on a tiny input is not evidence of determinism.
- **Large training relations fail on query memory, not on a documented cap.** The error is `resourcesExceeded` — *"The query could not be executed in the allotted memory. Peak usage: 124% of limit"*, with 91% of that usage reported as `other/unattributed`. Measured on a two-feature relation whose *prediction* side was only 2 rows, so the training relation alone drives it: 1,000 rows OK (44s), 5,000 OK (82s), 8,000 OK (70s), 10,000 fails, 50,000 fails, 200,000 fails. Failures burn ~1.37M slot_ms before dying versus ~210K for a run that succeeds. All measured **on-demand with no reservation**; untested under an Enterprise reservation, where the memory limit may differ. Size the training relation with this ceiling in mind and expect it to move with pricing model and column count.
- Hard limits: **20 feature columns** and **10 classes** for classification. Exceeding either errors.
- **Only six column types are accepted** (`STRING`, `BOOL`, `INT64`, `FLOAT64`, `NUMERIC`, `BIGNUMERIC`). `DATE`, `TIMESTAMP`, `BYTES`, `JSON`, `GEOGRAPHY`, `ARRAY`, and `STRUCT` are all rejected — extract date parts to `INT64` (e.g. `EXTRACT(MONTH FROM d)`) before passing them.
- `label_col` defaults to a column literally named `label`; pass it explicitly otherwise.
- **The documentation has a bug here:** the reference page says passthrough columns come from the *training* table. Observed behavior returns the *prediction* rows. Trust the behavior.
- Latency is 30–95s per call. A notebook with several `AI.PREDICT` examples is a multi-minute run, not an interactive one.
- Pricing (effective 2026-10-30) is token-based on a formula, not per-row: `input_tokens = (train_rows * columns + predict_rows * (columns - 1)) * n_ensembles`, `output_tokens = predict_rows * n_ensembles`, at $0.05/mtok in and $0.20/mtok out. Training-relation size drives cost on *every* call, since there is no reusable fitted model.
- There is **no BigFrames wrapper** — no `bbq.ai.predict`. Use `read_gbq_query` with the SQL.

### `AI.EVALUATE` across both branches

- **The two branches are mutually exclusive** — mixing forecast-shaped and tabular-shaped arguments in one call errors. Choose by which model family you are scoring.
- The tabular branch is just `AI.PREDICT`'s two relations plus `label_col`; the correspondence is exact, which makes it easy to score a prediction you already wrote.
- **Only the TimesFM branch returns `ai_evaluate_status`.** The tabular branch's output has no status column — don't write a per-row status check against it.
- The tabular branch returns **no `log_loss`, no `roc_auc`, and no confusion matrix** for classification. If you need those, use BigQuery ML's `ML.EVALUATE` on a trained classifier instead.
- **The label column's TYPE silently decides what `precision`/`recall`/`f1_score` mean, and nothing in the output says which convention you got.** A `BOOL` `label_col` is scored **binary** — the positive (`TRUE`) class alone. The `STRING` rendering of the identical values is scored **multiclass and macro-averaged**, even at two classes. `accuracy` is the same either way. Measured on one imbalanced problem (12 positives of 62 rows; TabFM confusion matrix TP 12 / FP 11 / FN 0 / TN 39): `BOOL` returned precision `0.5217` and recall `1.0`, `STRING` returned `0.7609` and `0.89` — the two-class means. Four isolated runs of each agreed. **This is a BigQuery-wide convention rather than an `AI.EVALUATE` behavior** — BigQuery ML's `ML.METRICS` follows the identical rule, measured side by side (see the sibling `bigquery-ml` skill's `narrative/evaluation.md`). On balanced data the two nearly coincide, which is how it hides until the classes are lopsided; fix the type deliberately and say which convention a published number uses.

## Canonical snippets

```sql
-- TimesFM: forecast a daily series
SELECT *
FROM AI.FORECAST(
  (SELECT date, daily_bike_trips FROM `project.dataset.bike_trips_daily`),
  data_col => 'daily_bike_trips',
  timestamp_col => 'date',
  model => 'TimesFM 2.5',   -- pin it; the default flipped from 2.0
  horizon => 14,
  confidence_level => 0.90
);
```

```sql
-- TabFM: zero-shot prediction, no CREATE MODEL anywhere
SELECT *
FROM AI.PREDICT(
  (SELECT species, island, culmen_length_mm, body_mass_g
   FROM `bigquery-public-data.ml_datasets.penguins` WHERE body_mass_g IS NOT NULL),
  (SELECT species, island, culmen_length_mm
   FROM `bigquery-public-data.ml_datasets.penguins` WHERE body_mass_g IS NULL),
  label_col => 'body_mass_g'
);
```

## Go deeper

Full extracted notebook walkthroughs live in this skill's `narrative/` folder:

- [`narrative/ai_forecast.md`](../narrative/ai_forecast.md) (source: `functions/ai_forecast/`) — cross-linked bidirectionally with bq-ml's arima_plus, the trainable alternative, for a direct side-by-side comparison
- [`narrative/ai_detect_anomalies.md`](../narrative/ai_detect_anomalies.md) (source: `functions/ai_detect_anomalies/`)
- [`narrative/ai_predict.md`](../narrative/ai_predict.md) (source: `functions/ai_predict/`)
- [`narrative/ai_evaluate.md`](../narrative/ai_evaluate.md) (source: `functions/ai_evaluate/`) — covers both branches
- [`narrative/time_series_intelligence.md`](../narrative/time_series_intelligence.md) — the TimesFM functions composed end-to-end
- [`narrative/tabular_prediction.md`](../narrative/tabular_prediction.md) — the TabFM functions composed end-to-end, with a head-to-head against trained BigQuery ML models

The `bigquery-ml` skill's `narrative/arima_plus.md` has the other half of the `AI.FORECAST` vs. `ARIMA_PLUS` comparison.

Full syntax/options tables: see the source repo at `bq-ai-functions/reference/predictive-ai.md`, indexed from `bq-ai-functions/RESOURCES.md`.
