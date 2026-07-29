# Forecasting & Anomaly Detection in BigQuery AI Functions

## Options

| Function | What it does | Use this when |
|----------|---------------|----------------|
| `AI.FORECAST` | Zero-training time series forecasting using BigQuery ML's built-in TimesFM model (2.0 default, or 2.5). Returns forecasted values, confidence intervals, and optionally the historical series alongside the forecast. | You want a quick forecast of future values with no `CREATE MODEL` step, no connection, no training. |
| `AI.DETECT_ANOMALIES` | Builds a TimesFM forecast baseline from historical data, then compares a separate target dataset against that baseline to flag anomalous points with a probability score. | You want to flag outliers/anomalies in a series (or across many series via `id_cols`) against expected behavior. |
| `AI.EVALUATE` | Generates a TimesFM forecast from historical data and scores it against actual observed values with MAE, MSE, RMSE, MAPE, sMAPE, and MASE. | You want to score how good a forecast was, or benchmark model/context-window configurations. |

All three are table-valued functions, GA, share the same `data_col` / `timestamp_col` / `id_cols` parameter pattern, and support TimesFM 2.0 (default) and TimesFM 2.5 — no model object is ever created or managed.

## Choosing among them

- **"I want a quick forecast with no model training"** → `AI.FORECAST`. Real limits vs. BigQuery ML's `ARIMA_PLUS`: no custom holiday effects, no external regressors (no XREG equivalent), no hierarchical reconciliation, and no direct control over forecast bounds beyond `confidence_level`. It's a fixed-architecture foundation model (TimesFM), not a trainable per-series statistical model.
- **"I want to flag outliers/anomalies in a series"** → `AI.DETECT_ANOMALIES`. Note it requires two inputs (a history table to build the baseline forecast, and a target table to test) with matching schemas — this is a materially different shape than `AI.FORECAST`'s single-input call.
- **"I want to score how good a forecast was"** → `AI.EVALUATE`. Also two-input (history + actuals), and its default `horizon` is 1024 — very different from `AI.FORECAST`'s default of 10.
- **When to reach for `../../bq-ml/models/arima_plus/` instead:** you need custom holiday regions/effects, external regressors (`ARIMA_PLUS_XREG`), hierarchical time series reconciliation, or fine-grained control over forecast intervals/bounds. `ARIMA_PLUS` is BQML's trainable alternative to the TimesFM-based `AI.FORECAST` — same underlying use case (time series forecasting) but with a `CREATE MODEL` step and per-series statistical fitting instead of a zero-training foundation model.

## Gotchas verified in this repo

- `AI.FORECAST` and `AI.EVALUATE` have wildly different default horizons — 10 vs. 1024, respectively — despite sharing the same `horizon` parameter name and range `[1, 10000]`. Don't assume symmetry.
- `AI.DETECT_ANOMALIES` silently caps evaluation at the most recent 1,024 time points regardless of how much target data you pass in; anything older is ignored (Google's own doc says to contact `bqml-feedback@google.com` for more).
- Max context differs by model version: TimesFM 2.0 tops out at 2,048 data points, TimesFM 2.5 at 15,360. Data points beyond the max are silently ignored rather than erroring.
- All three functions require a **minimum of 3 data points** — below that, expect a failure rather than a degraded forecast.
- `context_window` is auto-selected (smallest window covering your input) if you don't set it, but if you do set it, it must be one of a fixed discrete set (64/128/256/512/1024/2048 for 2.0; adds 4096/8192/15360 for 2.5) — arbitrary values aren't accepted.
- `AI.FORECAST`'s output schema changes shape entirely based on `output_historical_time_series`: `FALSE` gives you `forecast_timestamp`/`forecast_value`/bounds; `TRUE` gives you a unioned `time_series_type` ('history'/'forecast') + `time_series_data` column instead, with bounds NULL for historical rows. Don't hardcode a column list without checking which mode you used.
- Every function emits a per-row status column (`ai_forecast_status`, `ai_detect_anomalies_status`, `ai_evaluate_status`) that is empty on success and holds the error string on failure — check this column per-row rather than relying on the query failing outright, since partial failures (e.g., one bad series among many `id_cols`) surface here.
- `horizon` and `forecast_end_timestamp` are mutually exclusive on `AI.FORECAST` — pick one.
- None of these three functions have a BigFrames-native wrapper for `AI.DETECT_ANOMALIES` or `AI.EVALUATE`; only `AI.FORECAST` has a direct `bigframes.bigquery.ai.forecast()` wrapper. The BigFrames `bigframes.ml.forecasting.ARIMAPlus` class is a distinct model (ARIMA_PLUS, not TimesFM) and its `.detect_anomalies()`/`.evaluate()` methods are not equivalent to these AI.* functions.

## Canonical snippet

```sql
SELECT *
FROM AI.FORECAST(
  (SELECT date, daily_bike_trips FROM `project.dataset.bike_trips_daily`),
  data_col => 'daily_bike_trips',
  timestamp_col => 'date',
  horizon => 14,
  confidence_level => 0.90
);
```

## Go deeper

Full extracted notebook walkthroughs live in this skill's `narrative/` folder:

- [`narrative/ai_forecast.md`](../narrative/ai_forecast.md) (source: `functions/ai_forecast/`) — cross-linked bidirectionally with bq-ml's arima_plus, the trainable alternative, for a direct side-by-side comparison
- [`narrative/ai_detect_anomalies.md`](../narrative/ai_detect_anomalies.md) (source: `functions/ai_detect_anomalies/`)
- [`narrative/ai_evaluate.md`](../narrative/ai_evaluate.md) (source: `functions/ai_evaluate/`)

The `bigquery-ml` skill's `narrative/arima_plus.md` has the other half of the `AI.FORECAST` vs. `ARIMA_PLUS` comparison.

Full syntax/options tables: see RESOURCES.md in the source repo (`bq-ai-functions/RESOURCES.md`).
