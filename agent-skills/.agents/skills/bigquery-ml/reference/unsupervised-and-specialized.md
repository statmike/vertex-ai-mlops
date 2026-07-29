# Unsupervised & Specialized Models in BigQuery ML

## Options

| model_type | What it's for | Use this when | Key gotcha to know upfront |
|---|---|---|---|
| `KMEANS` | Unsupervised clustering — partitions rows into `k` groups by nearest centroid | You want to segment/group unlabeled rows or do distance-based anomaly detection | Retraining the identical model is genuinely non-deterministic (even with `KMEANS++`) — a single before/after comparison is not reliable evidence |
| `PCA` | Linear dimensionality reduction via eigendecomposition | You want to shrink correlated numeric/categorical features into ranked, orthogonal components, or need a cheap linear anomaly detector | Fully deterministic on its own metric, but with `pca_explained_variance_ratio` (vs. a fixed component count) downstream anomaly-detection results can swing wildly between identical retrains |
| `AUTOENCODER` | Nonlinear dimensionality reduction / latent embeddings via a neural bottleneck | PCA's linear assumption is too weak, or you want nonlinear anomaly detection / embeddings | Default `activation_fn='RELU'` can cause real dying-ReLU collapse on small/narrow networks (latent dims silently pinned to 0.0) — switch to `TANH` |
| `MATRIX_FACTORIZATION` | Collaborative-filtering recommendations from a sparse user-item interaction matrix | You have a (user, item, rating) table and want to predict/recommend for the missing pairs | Cannot train on-demand — requires a slot reservation, and it must be `ENTERPRISE`+ edition (not `STANDARD`); use an autoscale reservation, not a capacity commitment |
| `CONTRIBUTION_ANALYSIS` | Key-driver / metric-shift analysis — explains why a summable metric changed between test and control segments | You need "why did this metric move" analysis with summable/ratio/summable-by-category metrics or more dimensions than `AI.KEY_DRIVERS` supports | Output schema (columns) differs depending on the `contribution_metric` type (summable vs. ratio vs. by-category) — not documented officially |
| `ARIMA_PLUS` | Univariate time-series forecasting with automatic seasonality/holiday/trend decomposition | You have one signal over time (optionally many independent series) and want a forecast + explainable decomposition | `forecast_limit_lower_bound`/`upper_bound` silently breaks `ML.EXPLAIN_FORECAST` on that same model — needs a second model if you want both a bound and decomposition |
| `ARIMA_PLUS_XREG` | Multivariate time-series forecasting with external regressors (ARIMAX) | You have covariates known at forecast time (promotions, weather, etc.) that should improve the forecast, or need hierarchical reconciliation | `ML.FORECAST`/`ML.EXPLAIN_FORECAST` require the 3rd (future-covariates) argument — the 2-argument form errors immediately, unlike plain `ARIMA_PLUS` |

## Choosing among them

**"I want to segment/cluster rows"** → `KMEANS`. Use `ML.CENTROIDS` to profile clusters and `ML.DETECT_ANOMALIES` (with `contamination`) for distance-based outlier detection on the same model.

**"I want to reduce dimensionality / build embeddings"** → `PCA` or `AUTOENCODER`.
- Start with `PCA`: it's linear, fully deterministic, cheap, and gives you a ranked, interpretable set of components (`ML.PRINCIPAL_COMPONENTS` + `ML.PRINCIPAL_COMPONENT_INFO` for loadings and explained variance).
- Move to `AUTOENCODER` when you suspect nonlinear structure PCA can't capture, or you specifically want a compact learned latent space / nonlinear anomaly detector. Expect to tune `activation_fn` (prefer `TANH` over the RELU default for small networks) and accept that individual latent dimensions are not stable/comparable across retrains (unlike PCA's variance-ranked components).
- Both support `ML.GENERATE_EMBEDDING` to produce a single `ARRAY<FLOAT>` column for `VECTOR_SEARCH` — but you must materialize the embeddings into a real table first; `VECTOR_SEARCH` cannot consume the function call directly as its base table.

**"I want to explain why an aggregate metric changed between two segments/time periods"** → `CONTRIBUTION_ANALYSIS`. Define a test/control split (`is_test_col`), a `contribution_metric` (summable, summable-ratio, or summable-by-category), and dimension columns; read results via `ML.GET_INSIGHTS`. Consider `AI.KEY_DRIVERS` first if your metric is a simple summable metric and you have ≤12 dimensions — it's model-free and much faster; reach for the `CONTRIBUTION_ANALYSIS` model only when you need ratio/category metrics or more dimensions.

**"I want to forecast a time series"** → `ARIMA_PLUS` for a single covariate-free signal (or many independent series via `time_series_id_col`), with built-in holiday/seasonality/spike handling and optional hierarchical bottom-up reconciliation (`hierarchical_time_series_cols`). Move to `ARIMA_PLUS_XREG` when you have external regressors whose future values you'll actually know at forecast time (promotions, weather, capacity, etc.) — it fits a linear regression on those covariates and models the residuals with the same ARIMA_PLUS pipeline, adding per-regressor attribution via `ML.EXPLAIN_FORECAST`/`ML.ARIMA_COEFFICIENTS`. Consider `AI.FORECAST` (TimesFM) first if you want zero-config forecasting without custom holidays, external regressors, or hierarchy needs.

**"I want product/user recommendations from an interaction matrix"** → `MATRIX_FACTORIZATION`. Requires a `(user, item, rating)` triple and — unlike every other model type in this bucket — a slot reservation to train at all (see gotchas below). Use `ML.RECOMMEND` for scoring and `ML.WEIGHTS`/`ML.GENERATE_EMBEDDING` for the learned factor vectors (item-item similarity, etc.).

## Gotchas verified in this repo

- **`MATRIX_FACTORIZATION` cannot train under on-demand pricing at all** — `CREATE MODEL` fails instantly with `"Training Matrix Factorization models is not available for on-demand usage."` It needs a reservation.
- **The reservation must be `ENTERPRISE` edition or higher, not `STANDARD`.** A `STANDARD` reservation still fails BQML training specifically (`"Using BQML related functionalities is disallowed in STANDARD edition."`) even though it works fine for regular queries.
- **No capacity commitment is needed** — an autoscale reservation (`--edition=ENTERPRISE --autoscale_max_slots=N`, baseline `--slots=0`, no `--capacity_commitment`) is sufficient and pay-per-second. A freshly created/assigned reservation needs ~90 seconds to propagate before `CREATE MODEL` will succeed against it. Measured real cost for one full lifecycle (base model + 4-trial tuning + a BigFrames retrain) was ~6.4 cumulative slot-hours.
- **`KMEANS` cluster assignments and quality metrics are genuinely non-deterministic across retrains**, even with `kmeans_init_method='KMEANS++'` — `davies_bouldin_index` ranged ~0.87–1.02 across identical retrains of the same 342-row dataset, and which cluster aligned with a given external label shifted between runs. A lower `davies_bouldin_index` also does not by itself mean more meaningful clusters — it only measures internal separation, not alignment with any domain-meaningful grouping. Don't trust a single before/after comparison or a single HP-tuning run's chosen `num_clusters` as definitive.
- **`PCA` is fully deterministic on its own `ML.EVALUATE` metric** (bit-for-bit reproducible, even from an independently-trained BigFrames model) — but using `pca_explained_variance_ratio` (a variable component count) instead of a fixed `num_principal_components` can make *downstream* `ML.DETECT_ANOMALIES` results wildly unstable: three identical retrains at `pca_explained_variance_ratio=0.95` produced true-positive counts of 3, 235, and 279 (out of 492 known anomalies) despite `total_explained_variance_ratio` staying stable at ~0.95473. Switching to a fixed `num_principal_components` cut that swing to a 114–132 TP range.
- **PCA and KMEANS use different, inconsistent indexing conventions**: `principal_component_id` is 0-indexed, `centroid_id` is 1-indexed, and `ML.PREDICT`'s own `principal_component_N` output columns are 1-indexed. Don't assume a consistent convention across (or even within) unsupervised model types.
- **`AUTOENCODER`'s default `activation_fn='RELU'` caused real dying-ReLU collapse** on a small `hidden_units=[3,2,3]` network — 40–65% of rows had both latent dimensions clipped to exactly 0.0 across three retrains, invisible in `ML.EVALUATE`'s aggregate metrics (which looked normal every time). Switching to `TANH` fixed it every time tested, landing `mean_squared_error` around ~0.21 vs. RELU's highly variable ~0.66–0.94.
- **All three unsupervised IID model types (`KMEANS`, `PCA`, `AUTOENCODER`) require the 3rd (input-data) argument to `ML.DETECT_ANOMALIES`** — omitting it errors immediately (`"DETECT_ANOMALIES expects 3 arguments for <model_type> models but 2 were passed"`), even though the syntax reads as if it might be optional.
- **`ML.GENERATE_EMBEDDING` never normalizes its output** for PCA/AUTOENCODER (bit-for-bit identical to the raw `ML.PREDICT` projection/latent columns) and does not accept `VECTOR_SEARCH` as a direct downstream call — materialize embeddings to a real table first. For `MATRIX_FACTORIZATION`, `ML.GENERATE_EMBEDDING` takes only the model (no input table — passing one errors) and returns an array of `num_factors + 1` elements (the extra element is the per-entity intercept), not `num_factors`.
- **`MATRIX_FACTORIZATION` cold start does not error** — recommending for a never-seen user/item ID returns a full, populated ranked list (falling back to item-side bias/popularity), not an error, contrary to the intuitive expectation.
- **`ARIMA_PLUS`'s `forecast_limit_lower_bound`/`upper_bound` silently breaks `ML.EXPLAIN_FORECAST`** on that same model (`"...EXPLAIN_FORECAST is not supported"`) while `ML.FORECAST` keeps working fine — not documented officially. `ARIMA_PLUS_XREG` handles this differently: it rejects the option outright at `CREATE MODEL` time rather than silently breaking a downstream function later.
- **`CONTRIBUTION_ANALYSIS`'s `ML.GET_INSIGHTS` output schema changes shape depending on the metric type** — summable metrics get `difference`/`unexpected_difference`; ratio metrics get `aumann_shapley_attribution` (and `contribution` there means `ABS(aumann_shapley_attribution)`, not `ABS(difference)`); summable-by-category gets `_over_population` columns instead of `unexpected_difference`. `PRUNE_REDUNDANT_INSIGHTS` had a dramatic verified effect: 1,559 rows with `NO_PRUNING` collapsed to exactly 15 with pruning + `top_k=15` on identical data.

## Canonical snippet

```sql
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.MODEL_NAME`
OPTIONS(
  model_type           = 'KMEANS',
  num_clusters         = 4,
  kmeans_init_method   = 'KMEANS++',
  distance_type        = 'EUCLIDEAN',
  standardize_features = TRUE
) AS
SELECT * EXCEPT(id_col, label_col)
FROM `PROJECT_ID.DATASET.TABLE`;
```

## Go deeper

Full extracted notebook walkthroughs live in this skill's `narrative/` folder — no need to be inside the source repo:

- [`narrative/kmeans.md`](../narrative/kmeans.md) (source: `models/kmeans/`)
- [`narrative/pca.md`](../narrative/pca.md) (source: `models/pca/`)
- [`narrative/autoencoder.md`](../narrative/autoencoder.md) (source: `models/autoencoder/`)
- [`narrative/matrix_factorization.md`](../narrative/matrix_factorization.md) (source: `models/matrix_factorization/`)
- [`narrative/contribution_analysis.md`](../narrative/contribution_analysis.md) (source: `models/contribution_analysis/`)
- [`narrative/arima_plus.md`](../narrative/arima_plus.md) (source: `models/arima_plus/`)
- [`narrative/arima_plus_xreg.md`](../narrative/arima_plus_xreg.md) (source: `models/arima_plus_xreg/`)

Full syntax/options tables: see RESOURCES.md in the source repo (`bq-ml/RESOURCES.md`).

`bq-ai-functions`'s `AI.FORECAST` and `AI.KEY_DRIVERS` are zero-setup generative alternatives to `ARIMA_PLUS` and `CONTRIBUTION_ANALYSIS` respectively, worth considering when you don't need `ARIMA_PLUS`'s custom holidays/external regressors/hierarchy or `CONTRIBUTION_ANALYSIS`'s SQL-native aggregate-level analysis.
