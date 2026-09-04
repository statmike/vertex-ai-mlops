![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Fdata%2Bai%2Fbq-ml%2Freference&file=model-free-functions.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/data%2Bai/bq-ml/reference/model-free-functions.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ml/reference/model-free-functions.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ml/reference/model-free-functions.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ml/reference/model-free-functions.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ml/reference/model-free-functions.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-ml/reference/model-free-functions.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-ml/reference/model-free-functions.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# Model-Free Functions

> Part of the [BigQuery ML — Detailed Reference](../RESOURCES.md) · [Project README](../README.md)

`ML.*` functions that transform data directly — no model required. Used standalone or inside a `TRANSFORM` clause. Reference: [Manual preprocessing](https://cloud.google.com/bigquery/docs/manual-preprocessing).


---

## Numerical scalers: `ML.STANDARD_SCALER`, `ML.MIN_MAX_SCALER`, `ML.MAX_ABS_SCALER`, `ML.ROBUST_SCALER`, `ML.NORMALIZER`

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
| `ML.STANDARD_SCALER` | unbounded (~mean 0, std 1) | `(x - AVG(x)) / STDDEV_POP(x)` (z-score) | Yes (mean) | Stores AVG/STDDEV for `ML.PREDICT`. **Verified live: uses population stddev (`STDDEV_POP`, ÷N), NOT the sample stddev (`STDDEV`/`STDDEV_SAMP`, ÷N-1) BigQuery's plain `STDDEV()` computes by default** — a manual "sanity check" using `STDDEV(x)` will NOT match. |
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
- Prefer the `TRANSFORM` clause over preprocessing in the source query so the learned statistics travel with the model and are reapplied at prediction (avoids training/serving skew). Scale each column inside one `TRANSFORM` and alias each result (`ML.STANDARD_SCALER(col) OVER() AS col_scaled`) — see `functions/scalers/scalers.sql` (Example 8).
- Choose the scaler to match the data: `ROBUST` for outliers, `MAX_ABS` for sparse/sign-bearing data, `STANDARD` for roughly Gaussian features, `MIN_MAX` when a bounded `[0,1]` range is needed.
- Validate `ML.STANDARD_SCALER` equals `(x - AVG) / STDDEV_POP` (not the default `STDDEV`/`STDDEV_SAMP`) — verified live in `functions/scalers/scalers.sql` (Example 1).

**Limitations / gotchas:**
- The four analytic scalers MUST use an empty `OVER()`; omitting it errors. `ML.NORMALIZER` must NOT use `OVER()`.
- An analytic function cannot be an argument to another analytic function, but a scalar function can take an analytic function's result as an argument (e.g. `ML.POLYNOMIAL_EXPAND` wrapping `ML.IMPUTER(...) OVER()`) — see `functions/feature_engineering/feature_engineering.sql` (Example 6).
- `ML.NORMALIZER` normalizes across the elements of each row's ARRAY (row-wise), not down a column — semantically different from the column scalers.
- `ML.MIN_MAX_SCALER` caps prediction-time inputs to `[0, 1]` when they fall outside the training min/max.
- Imputation of NULLs is not done by scalers; pair with `ML.IMPUTER` (impute in the input query or earlier in the transform chain).

**BigFrames API:** `bigframes.ml.preprocessing.StandardScaler`, `MinMaxScaler`, `MaxAbsScaler` (and `compose.ColumnTransformer`); not every scaler has a 1:1 class — use SQL `TRANSFORM` for full parity.

**Repo examples (tested):**
- [`functions/scalers/`](../functions/scalers/) — all five scalers on `penguins`, standalone (Examples 1–5) and side-by-side on one column (Example 7). Covers `ML.ROBUST_SCALER` with all three optional parameters (`[10,90]` custom range, `with_median = FALSE`, `with_quantile_range = FALSE`) and `ML.NORMALIZER` at p ∈ {0, 1, 2, +inf} on `[3.0, 4.0]`, then on a real per-penguin measurement vector. Verifies the `STDDEV_POP` gotcha above (Example 1), `ML.MIN_MAX_SCALER`'s prediction-time capping via a live `CREATE MODEL` + `ML.TRANSFORM` test — 20.0 → 0.0 and 100.0 → 1.0 against a training range of `[32.1, 59.6]` (Example 2) — and `ML.ROBUST_SCALER`'s outlier robustness against `ML.STANDARD_SCALER` on an injected outlier (500 among 10–14): standard compresses the normal points into −0.35…−0.32, robust keeps them spread across −0.8…0.8 (Example 4). Example 6 shows NULLs passing through untouched. Example 8 ends with a `LOGISTIC_REG` embedding the `TRANSFORM` directly (roc_auc = 1.0), so `ML.PREDICT` on raw unscaled input works — contrast with `models/transform_only/`, whose standalone pipeline needs explicit re-application.
- Scalers inside a real `TRANSFORM` of an estimator, across model types: [`models/linear_regression/`](../models/linear_regression/) and [`models/dnn_regressor/`](../models/dnn_regressor/) (`ML.STANDARD_SCALER` on the measurement columns), [`models/dnn_classifier/`](../models/dnn_classifier/), [`models/wide_and_deep_regressor/`](../models/wide_and_deep_regressor/), [`models/wide_and_deep_classifier/`](../models/wide_and_deep_classifier/), [`models/logistic_regression/`](../models/logistic_regression/), [`models/kmeans/`](../models/kmeans/).
- [`models/transform_only/`](../models/transform_only/) — `ML.IMPUTER` + scaling + one-hot encoding in one `TRANSFORM_ONLY` model, the reusable/modular pattern: the preprocessing statistics are frozen at creation time and reapplied via `ML.TRANSFORM` for any downstream model.
- [`workflows/customer_segmentation/`](../workflows/customer_segmentation/) — `ML.STANDARD_SCALER` on RFM features before `KMEANS` (Step 2) — raw scale would let `monetary`, which ranges into the thousands, dominate the distance calculation. Carries the verified gotcha that `user_id` must be kept out of the training query or it becomes an unscaled feature distorting every distance.


---

## `ML.BUCKETIZE`
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
- **GOTCHA, verified live — `exclude_boundaries=TRUE` does NOT null out-of-range values.** It's easy to misread "drops the implicit lower/upper overflow buckets" as "values outside the split-point range become NULL." What actually happens: the **outermost split points are dropped entirely**, merging the overflow bucket into its nearest interior neighbor. With split points `[10, 20, 30]`: default gives 4 bins `(-inf,10)` `[10,20)` `[20,30)` `[30,+inf)`; with `exclude_boundaries=TRUE` this becomes just 2 bins `(-inf,20)` `[20,+inf)` — the `10` and `30` split points disappear, leaving only `20` as the sole effective boundary. No value ever becomes NULL from this option alone.

**BigFrames API:** `bigframes.ml.preprocessing.KBinsDiscretizer` (strategy-dependent; not a 1:1 of explicit split points).
**Repo example (tested):** [`functions/bucketizing/`](../functions/bucketizing/) — Example 1 runs all three `output_format` values against the same `[3000, 4000, 5000]` split points on `penguins.body_mass_g`; Example 2 is the `exclude_boundaries` clarification above, proven live with `[10, 20, 30]`; Example 5 embeds `ML.QUANTILE_BUCKETIZE` and `ML.HASH_BUCKETIZE` together in a real `LOGISTIC_REG` `TRANSFORM` (accuracy ~0.81).

---

## `ML.QUANTILE_BUCKETIZE`
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
**Repo example (tested):** [`functions/bucketizing/`](../functions/bucketizing/) — Example 3 runs `ML.QUANTILE_BUCKETIZE(culmen_length_mm, 4) OVER()` in both `bucket_names` and `bucket_ranges` form side by side; Example 5 embeds it in a `LOGISTIC_REG` `TRANSFORM` alongside `ML.HASH_BUCKETIZE`, where the training-time quantiles are stored with the model.

---

## `ML.HASH_BUCKETIZE`
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
**Repo example (tested):** [`functions/bucketizing/`](../functions/bucketizing/) — Example 4 contrasts `ML.HASH_BUCKETIZE(island, 0)` (hash only, no modulo) with `ML.HASH_BUCKETIZE(island, 3)` over `penguins`' distinct islands; Example 5 embeds it at `hash_bucket_size = 10` alongside `ML.QUANTILE_BUCKETIZE` in a real `LOGISTIC_REG` `TRANSFORM`, where BQML auto-encodes the INT64 hash bucket as an ordinary feature.

---

**Family note:** All three are exportable feature-preprocessing functions when used in the `TRANSFORM` clause, so the transformation is reapplied automatically during `ML.PREDICT` and accompanies exported / Vertex-registered models. `ML.BUCKETIZE` and `ML.HASH_BUCKETIZE` are scalar; `ML.QUANTILE_BUCKETIZE` is analytic and requires an empty `OVER()` clause. See the [Manual feature preprocessing](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-preprocessing-functions) reference.


---

## `ML.ONE_HOT_ENCODER` / `ML.MULTI_HOT_ENCODER` / `ML.LABEL_ENCODER`

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
- **MAJOR GOTCHA, verified live — the default discrepancy is not just a docs footnote, it changes real output:** older documentation cites default `top_k = 1,000,000` / `frequency_threshold = 0`; current docs (and current live behavior) specify `top_k = 32,000` / `frequency_threshold = 5`. Tested with categories occurring 6x/7x/3x: under the **current** default, the category with only 3 occurrences (below the frequency-5 threshold) silently collapses into bucket `0` — indistinguishable from `NULL`/unseen-at-predict, no error or warning. Under `frequency_threshold=0` (the old default), that same category keeps its own index. **Any real dataset with a rare-but-meaningful category (fewer than 5 total occurrences) will silently lose it under current defaults** unless `frequency_threshold` is explicitly lowered.

**BigFrames API:** `bigframes.ml.preprocessing.OneHotEncoder`, `bigframes.ml.preprocessing.LabelEncoder` (and the broader `bigframes.ml.preprocessing` module); these compile to the corresponding `ML.*` encoders.

**Repo example (tested):**
- [`functions/encoding/`](../functions/encoding/) — Example 1 puts `ML.ONE_HOT_ENCODER` default, dummy (`'most_frequent'`), and `'none', 32000, 0` side by side over an `UNNEST([...])` literal with a 6x/7x/3x frequency spread; Example 3 runs `ML.ONE_HOT_ENCODER` + `ML.LABEL_ENCODER` on `penguins.island` and `ML.MULTI_HOT_ENCODER(arr, 100, 0) OVER()` on a real `ARRAY<STRING>` (one feature per unique element across all rows, not per row).
- [`functions/encoding/`](../functions/encoding/) Example 2 — live proof of the default discrepancy above: the 3-occurrence category collapses into bucket `0` under the current default, and keeps its own index under `frequency_threshold = 0`. Example 4 embeds `ML.ONE_HOT_ENCODER` + `ML.LABEL_ENCODER` in a real `LOGISTIC_REG` `TRANSFORM` (accuracy ~0.71 from `island` + `sex` alone).
- [`models/transform_only/`](../models/transform_only/) — one-hot encoding as part of a reusable `TRANSFORM_ONLY` preprocessing pipeline, with the vocabulary frozen at creation time.


---

## Feature engineering: standalone preprocessing functions

These are **manual feature preprocessing** functions. They can be used two ways:
1. **Inline in a query / standalone** — plain SQL to shape data before `CREATE MODEL` (the model then does *automatic* preprocessing on the result).
2. **Inside the `TRANSFORM` clause** of `CREATE MODEL` — the computed statistics are stored with the model and **re-applied automatically at serving** by `ML.PREDICT` / `ML.TRANSFORM`, and travel with [exported models](https://cloud.google.com/bigquery/docs/exporting-models) and Vertex AI Model Registry registrations. This is the recommended way to prevent training-serving skew.

> **Analytic vs scalar.** Functions that compute statistics across *all* rows (mean, median, mode, min/max, quantiles, stddev) are **analytic** and require an empty `OVER()` clause. Functions that operate row-by-row (e.g. `ML.FEATURE_CROSS`, `ML.POLYNOMIAL_EXPAND`, `ML.BUCKETIZE`) are **scalar** and take no `OVER()`. An analytic function cannot be nested as the argument of another analytic function, but a scalar/analytic result can be wrapped by a scalar function.

> **Note on `ML.TRANSPOSE`:** there is **no `ML.TRANSPOSE` function** in BigQuery ML. Material that speaks of "transposing" refers to the inline `TRANSFORM` clause technique (transposing preprocessing *into* the model), not a function. See the `TRANSFORM` clause pointer at the end of this section. The full catalog of manual preprocessing functions (encoders, scalers, bucketizers, text/image functions) lives in the **Manual preprocessing** reference: <https://cloud.google.com/bigquery/docs/manual-preprocessing>.

---

## `ML.IMPUTER`
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
**Repo example (tested):** [`functions/feature_engineering/`](../functions/feature_engineering/) — Example 1 imputes a numeric column two ways and a string column by mode, on real `penguins` data:
```sql
SELECT
  ML.IMPUTER(body_mass_g, 'mean')   OVER() AS imputed_mean,
  ML.IMPUTER(body_mass_g, 'median') OVER() AS imputed_median,
  ML.IMPUTER(sex, 'most_frequent')  OVER() AS sex_imputed_mode
FROM `bigquery-public-data.ml_datasets.penguins`;
```
Example 2 embeds it in a real `LOGISTIC_REG` `TRANSFORM` (unlike `ML.FEATURE_CROSS`/`ML.POLYNOMIAL_EXPAND`, `ML.IMPUTER` **is** exportable) — verified that predicting with a `NULL` `body_mass_g` at predict time auto-imputes with the training-time mean rather than erroring. Also [`models/transform_only/`](../models/transform_only/) Example 1, where `ML.IMPUTER` opens a reusable preprocessing pipeline (and where its required strategy argument is contrasted against the single-argument scalers).

---

## `ML.FEATURE_CROSS`
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
**Limitations:** Categorical (string) inputs only; `degree` capped at 4. **Not exportable** in `TRANSFORM`. **Verified live:** a `CREATE MODEL ... TRANSFORM(ML.FEATURE_CROSS(...))` trains and predicts (`ML.PREDICT`) completely normally — the limitation only bites at `EXPORT MODEL` time, which fails with `"400 Model TRANSFORM contains unsupported function for exporting."` A model needing portability/serving outside BQ (`EXPORT MODEL`, `model_registry='VERTEX_AI'`, remote-model deployment) must compute crosses in the input query instead.
**BigFrames API:** No direct equivalent (build via DataFrame ops).
**Repo example (tested):** [`functions/feature_engineering/`](../functions/feature_engineering/) — Example 3 crosses `penguins`' `island` × `sex`:
```sql
SELECT island, sex,
  ML.FEATURE_CROSS(STRUCT(island, sex)) AS crossed
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE sex IS NOT NULL;
-- e.g. {'island_sex': 'Dream_FEMALE'} -- one field per crossed combination,
-- named <col_a>_<col_b>, valued <val_a>_<val_b>. Scalar function, no OVER().
```
Example 4 then plugs it into a live `CREATE MODEL` — training and `ML.PREDICT` work normally, and only the subsequent `EXPORT MODEL` fails, with the exact error captured.

---

## `ML.POLYNOMIAL_EXPAND`
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
**Limitations:** ≤ 10 input features, no unnamed/duplicate features; `degree` ≤ 4. **Not exportable** in `TRANSFORM`, same verified failure mode as `ML.FEATURE_CROSS` above (`EXPORT MODEL` rejects it with "Model TRANSFORM contains unsupported function for exporting" — training/`ML.PREDICT` are unaffected).
**BigFrames API:** `bigframes.ml.preprocessing.PolynomialFeatures`.
**Repo example (tested):** [`functions/feature_engineering/`](../functions/feature_engineering/) — Example 5 expands `penguins`' `culmen_length_mm`/`culmen_depth_mm` at `degree = 2`, yielding e.g. `{'length':36.6,'depth':18.4,'length_length':1339.56,'length_depth':673.44,'depth_depth':338.56}`. Example 6 shows the **compounded** pattern (impute → expand), which works because a scalar function may take an analytic function's result as an argument:
```sql
SELECT
  body_mass_g,
  ML.POLYNOMIAL_EXPAND(
    STRUCT(ML.IMPUTER(body_mass_g, 'mean') OVER() AS mass_imputed),
    2
  ) AS expanded
FROM `bigquery-public-data.ml_datasets.penguins`
ORDER BY body_mass_g IS NULL DESC;
```

---

## `ML.TRANSPOSE` — not a function (pointer)
`ML.TRANSPOSE` does not exist in BigQuery ML. To "transpose" preprocessing into the model so it serves automatically, use the **`TRANSFORM` clause** of `CREATE MODEL`:
- `TRANSFORM` clause reference: <https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create#transform>
- Feature engineering with `TRANSFORM`: <https://cloud.google.com/bigquery/docs/bigqueryml-transform>
- Inspect the preprocessed output of a model's `TRANSFORM` with `ML.TRANSFORM` (function): <https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-transform>

**Repo examples (tested) — `TRANSFORM` in a real `CREATE MODEL`:**
- [`models/transform_only/`](../models/transform_only/) — the fullest version of the pattern: one `TRANSFORM` mixing `ML.IMPUTER`, two scalers, and `ML.ONE_HOT_ENCODER`, packaged as a `TRANSFORM_ONLY` model with no estimator, so the same preprocessing (and its frozen train-time statistics) can be reused by any downstream model:
```sql
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.transform_only_penguins`
TRANSFORM(
  species,
  island,
  ML.IMPUTER(body_mass_g, 'mean') OVER() AS body_mass_g,
  ML.STANDARD_SCALER(culmen_length_mm) OVER() AS culmen_length_mm,
  ML.STANDARD_SCALER(culmen_depth_mm) OVER() AS culmen_depth_mm,
  ML.ROBUST_SCALER(flipper_length_mm) OVER() AS flipper_length_mm,
  ML.ONE_HOT_ENCODER(sex) OVER() AS sex_encoded
)
OPTIONS(model_type = 'TRANSFORM_ONLY') AS
SELECT species, island, sex, body_mass_g, culmen_length_mm, culmen_depth_mm, flipper_length_mm
FROM `bigquery-public-data.ml_datasets.penguins`;
```
  Example 4 exports it (a transform-only model exports like any other); Examples 6 and 7 are the payoff — predicting on raw data through a *standalone* pipeline silently gives garbage unless `ML.TRANSFORM` is re-applied first.
- [`functions/scalers/`](../functions/scalers/) Example 8 — the contrasting case: the `TRANSFORM` is embedded directly in a `LOGISTIC_REG`, so `ML.PREDICT` on raw unscaled input auto-applies the scaling and no re-application step exists to forget.
- [`models/export/`](../models/export/) Example 5 — `model_registry = 'VERTEX_AI'` with `vertex_ai_model_id`, registering the model at `CREATE MODEL` time rather than exporting it.


---

## Text preprocessing functions: `ML.NGRAMS`, `ML.TF_IDF`, `ML.BAG_OF_WORDS`

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

## `ML.NGRAMS`
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
| `range` | `ARRAY<INT64>` | Yes | — | `[min, max]` n-gram sizes. **Correction, verified live: `range` must always be an `ARRAY<INT64>` — a bare `INT64` (the docs' claimed "single int `x` means `[x, x]`" shorthand) errors outright** (`"Unable to coerce type INT64 to expected type ARRAY<INT64>"`). Use `[x, x]` explicitly for a single size. |
| `separator` | `STRING` | No | `' '` (space) | Joins adjacent tokens in each output n-gram. |

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| (result) | `ARRAY<STRING>` | All n-grams within `range`, each a `separator`-joined string. |

**Best practices:** Keep `range` tight (e.g. `[1, 2]`) — wide ranges explode feature cardinality. Tokenize and lowercase upstream for consistency.
**Limitations:** Scalar over one array per row; does not aggregate across rows. Order is preserved from the input array.
**BigFrames API:** No direct equivalent (use SQL / `bigframes.bigquery` passthrough).
**Repo example (tested):** [`functions/text/`](../functions/text/) — Example 1 tokenizes first (all three text functions require `ARRAY<STRING>`); Example 2 runs `ML.NGRAMS(tokens, [2, 3])` on a real tokenized product name (`SPLIT(LOWER('Low Profile Dyed Cotton Cap'), ' ')`) to produce bigrams and trigrams in one call.

---

## `ML.TF_IDF`
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
**Limitations:** Must use empty `OVER ()`; the dictionary is built over the analytic window, so apply over the full training corpus. Index `0` always reserved for unknown. **MAJOR GOTCHA, verified live — shares the exact same `frequency_threshold=5` default trap as `ML.ONE_HOT_ENCODER`/`ML.LABEL_ENCODER` (see that entry):** on a small corpus, any term appearing in fewer than 5 documents collapses into the unknown bucket (index `0`), indistinguishable from a truly unseen term — tested with 6 tiny documents where a word appearing in 2 different documents was still indistinguishable from a word appearing in only 1.
**BigFrames API:** No direct equivalent.
**Repo example (tested):** `data+ai/bq-ml/functions/text/text.ipynb` — real product-name tokens from `thelook_ecommerce.products`, the `frequency_threshold=5` gotcha proof above (tested directly for `ML.TF_IDF` itself, not just asserted by analogy to `ML.BAG_OF_WORDS`), and a concrete `ML.BAG_OF_WORDS`-vs-`ML.TF_IDF` contrast showing a term appearing in every document gets a *lower* TF-IDF weight than rarer terms, while BOW gives them identical raw counts.

---

## `ML.BAG_OF_WORDS`
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
**Limitations:** Empty `OVER ()` required; counts depend on the analytic window — apply over the full corpus. Index `0` reserved for unknown. Shares the same `frequency_threshold=5` default gotcha as `ML.TF_IDF` above — verified live (see that entry).
**BigFrames API:** No direct equivalent.
**Repo example (tested):** `data+ai/bq-ml/functions/text/text.ipynb` — real product-name tokens, the `frequency_threshold=5` gotcha proof, and `ML.BAG_OF_WORDS` embedded in a real `LOGISTIC_REG` `TRANSFORM` classifying product category from the product name alone (~0.95 accuracy).

---

**Status:** All three are **GA**. **Connection required:** No.

**Typical pipeline:** tokenize (GoogleSQL `TEXT_ANALYZE`/`SPLIT`) → optional `ML.NGRAMS` → `ML.BAG_OF_WORDS`
or `ML.TF_IDF` (in `TRANSFORM`) → train classifier. Note: `ML.TF_IDF`/`ML.BAG_OF_WORDS` are analytic
(`OVER ()`) and an analytic function cannot be an argument of another analytic function — chain via
subqueries/CTEs, not nesting (consistent with the repo's note for `ML.STANDARD_SCALER` etc.).


---

## `ML.DISTANCE`
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

**Repo example (tested):** `data+ai/bq-ml/functions/distance/distance.ipynb` — all three metrics standalone, the cosine distance-vs-similarity pattern (same one used in `data+ai/bq-ai-functions/functions/ai_embed/ai_embed.sql`, lines 67/136), and real embedding similarity: trains a scratch `PCA` model on `penguins` and computes `ML.DISTANCE` between two penguins' projections from different species.

---

## `ML.LP_NORM`
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
- Combine with `ML.DISTANCE` only when you need a metric not directly supported (e.g., Jaccard — verified live: derivable via a dot product for the intersection count and `ML.LP_NORM(v, 1.0)` for each vector's set size, `jaccard = intersection / (norm_a + norm_b - intersection)`).

**Limitations:**
- Operates on a single vector (a norm), not a pair — use `ML.DISTANCE` for pairwise distance.
- `degree` is required (no implicit default).
- Brute-force scalar computation; not an index.

**BigFrames API:** No direct equivalent.
**Repo example (tested):** `data+ai/bq-ml/functions/distance/distance.ipynb` — L0/L1/L2 norms; **verified live that `ML.NORMALIZER(v, p)` (see `functions/scalers/`) equals `v / ML.LP_NORM(v, p)` element-wise** — `ML.LP_NORM` computes exactly the denominator `ML.NORMALIZER` uses internally; also the Jaccard-derivation example above.

**Repo example (tested):** Not present in the bq-ml feature-engineering notebooks or elsewhere in this repo (no `ML.LP_NORM` occurrences found). Documentation example pattern: `SELECT ML.LP_NORM([1.0, 2.0, 3.0], 2.0)`.


---

## Image preprocessing functions: `ML.DECODE_IMAGE`, `ML.RESIZE_IMAGE`, `ML.CONVERT_IMAGE_TYPE`, `ML.CONVERT_COLOR_SPACE`

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

## `ML.DECODE_IMAGE`
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
**Repo example (tested):** None — this project's preprocessing coverage (`functions/scalers/`, `functions/bucketizing/`, `functions/encoding/`, `functions/feature_engineering/`, `functions/text/`) is tabular and text only; no example exercises the image preprocessing functions. Doc pattern: `ML.DECODE_IMAGE(data)` over an object table's `data` column.

---

## `ML.RESIZE_IMAGE`
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

## `ML.CONVERT_IMAGE_TYPE`
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

## `ML.CONVERT_COLOR_SPACE`
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


---

## Model-free time series decomposition: `ML.TREND`, `ML.SEASONALITY`, `ML.DETECT_CHANGE_POINTS`

- **Description:** Three **table-valued functions** that decompose a time series without training a model. `ML.TREND` returns the trend component, `ML.SEASONALITY` returns per-period seasonal components, and `ML.DETECT_CHANGE_POINTS` returns sustained structural shifts as time windows. No `CREATE MODEL`, no model object, no connection — the first argument is a relation (a `TABLE` reference or a parenthesized subquery) and the column names are passed as `STRING` named arguments.
- **Use cases:**
  - Get a series' underlying direction or seasonal shape without committing to a model artifact you then have to manage, version, and retrain.
  - Extract seasonal components that are **bit-identical** to an `ARIMA_PLUS` model's (measured below) at a fraction of the setup.
  - Detect sustained level shifts — the gap between row-level anomaly detection and dataset-level drift monitoring, which nothing else in this project covers.
  - Exploratory decomposition across many series at once via `id_cols`, before deciding whether a model is warranted at all.
- **documentation:** [ML.TREND](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-trend) · [ML.SEASONALITY](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-seasonality) · [ML.DETECT_CHANGE_POINTS](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-detect-change-points)
- **Type:** Table-valued (TVF).
- **Applies to models:** None — model-free. `ML.TREND`/`ML.SEASONALITY` run the `ARIMA_PLUS` decomposition without materializing a model.
- **Status:** **Preview** as of 2026-08-20. **Connection required:** No.

**Syntax** (as the server enumerates it when handed a bad argument):
```sql
ML.TREND(TABLE, timestamp_col => STRING, data_col => STRING,
         [id_cols => ARRAY<STRING>], [horizon => INT64],
         [smoothing_window_size => INT64], [adjust_step_changes => BOOL])

ML.SEASONALITY(TABLE, timestamp_col => STRING, data_col => STRING,
               [id_cols => ARRAY<STRING>], [SEASONALITIES => ARRAY<STRING>],
               [horizon => INT64])

ML.DETECT_CHANGE_POINTS(TABLE, timestamp_col => STRING, data_col => STRING,
                        [id_cols => ARRAY<STRING>])
```

**Inputs:**

| Parameter | Type | Required | Default | Applies to | Description |
|-----------|------|----------|---------|-----------|-------------|
| (first argument) | relation | Yes | — | all three | A `TABLE` reference or parenthesized subquery. Not a string. |
| `timestamp_col` | `STRING` | Yes | — | all three | Name of the time column. |
| `data_col` | `STRING` | Yes | — | all three | Name of the value column. |
| `id_cols` | `ARRAY<STRING>` | No | — | all three | Decompose each series independently in one pass, like `ARIMA_PLUS`'s `time_series_id_col`. Echoed in the output. |
| `horizon` | `INT64` | No | — | `TREND`, `SEASONALITY` | **Extends** the series into the future; not a row limit. See limitations. |
| `smoothing_window_size` | `INT64` | No | unspecified | `TREND` | Widens the trend smoothing window. |
| `adjust_step_changes` | `BOOL` | No | **`FALSE`** | `TREND` | Adjusts for step changes. **Differs from the `ARIMA_PLUS` default** — see limitations. |
| `SEASONALITIES` | `ARRAY<STRING>` | No | auto | `SEASONALITY` | Restricts fitted periods. Accepted: `DAILY`, `WEEKLY`, `MONTHLY`, `QUARTERLY`, `YEARLY` (values are case-insensitive). |

Argument **names** are case-insensitive and order-independent among named arguments.

**Outputs:**

| Function | Columns |
|---|---|
| `ML.TREND` | `<timestamp_col>`, `time_series_type`, `<data_col>`, `trend`, `status` |
| `ML.SEASONALITY` | `<timestamp_col>`, `time_series_type`, `<data_col>`, `yearly`, `quarterly`, `monthly`, `weekly`, `daily`, `status` |
| `ML.DETECT_CHANGE_POINTS` | `begin_timestamp`, `end_timestamp`, `metrics` `STRUCT<avg, count, max, min, stddev>`, `status` |

The timestamp and data columns keep their **original names** — output is not renamed to a generic `time_series_timestamp`/`time_series_data` the way `ML.FORECAST`'s is. The data column comes back `FLOAT64` regardless of input type, because the returned series is gap-filled/preprocessed rather than echoed.

**Measured against `ARIMA_PLUS` on an identical series** (Citi Bike daily trips, Pershing Square North, n = 1,341 history rows; `ML.TREND` called with `adjust_step_changes => TRUE` to match the model default):

| Component | vs. `ML.EXPLAIN_FORECAST` | Correlation |
|---|---|---|
| `weekly` vs `seasonal_period_weekly` | mean abs diff **0.0** | **1.0** |
| `yearly` vs `seasonal_period_yearly` | mean abs diff **0.0** | **1.0** |
| `trend` vs `trend` | mean abs diff 8.337 (median 5.755, p95 25.121, max 58.555) | 0.9955 |

`ML.SEASONALITY` reproduces the model's seasonal decomposition exactly. `ML.TREND` does not quite. Two option differences remain unseparated by that comparison, so no single cause is claimed: the trained model also reports `"cleanSpikesAndDips": true` (`ML.TREND` exposes no equivalent option) and `"trendSmoothingWindowSize": -1` (auto), while `ML.TREND`'s `smoothing_window_size` default is unspecified.

**Best practices:**
- Use `ML.SEASONALITY` as a drop-in for an `ARIMA_PLUS` model's seasonal components — same numbers, no model to manage. Treat `ML.TREND` as very close but not a substitute where a specific model's trend must be reproduced to the digit.
- Detect which periods were actually fitted with a `COUNTIF(<period> IS NULL)` pass. The schema is fixed and tells you nothing.
- Test `status` with `status = ''` or `LENGTH(status) = 0`.
- Range-join on `date BETWEEN begin_timestamp AND end_timestamp` to attribute rows to a change window.
- **Profile a series for data gaps before acting on any change point** — see limitations. On the tested data six of seven change points were gap edges, so the gap profile is not an optional refinement.
- Keep the valid `SEASONALITIES` list to hand rather than relying on the error message to supply it.
- Reach for these before `CREATE MODEL` when the question is descriptive ("what does this series look like?") rather than predictive.

**Limitations:**
- **`adjust_step_changes` defaults to `FALSE` here but `TRUE` in `ARIMA_PLUS`.** A naive `ML.TREND` call does not reproduce a model's trend. Verified by differencing all three variants: default vs `FALSE` summed to exactly `0.0`; default vs `TRUE` summed to 91,344.17 over 1,341 rows.
- **`horizon` extends the series, it does not window it.** Supplying it adds rows with `time_series_type = 'forecast'`. On those rows the **data column carries the forecast value, not `NULL`** — only `time_series_type` distinguishes an actual from a prediction, so an unfiltered aggregate silently mixes the two. `ML.DETECT_CHANGE_POINTS` has no `horizon`.
- **`ML.SEASONALITY`'s period columns are a fixed schema, not a result.** All five are always present; unfitted periods are `NULL` on every row. On a daily series only `weekly` and `yearly` populated — `daily`, `monthly` and `quarterly` were `NULL` across all 1,341 rows.
- **`ML.DETECT_CHANGE_POINTS` returns windows, not per-row flags.** No `is_change_point` boolean, no full-partition output. Two windows on a 1,341-day series.
- **Its `metrics` struct describes the gap-filled series, not your rows**, so it will not tie out against a `GROUP BY` over the same range. Measured on one window: raw `GROUP BY` gave n 3, avg 552.33, min 194; the function reported n 7, avg 346.98, min 192.33879781420765 — fractional, though the input is an integer `COUNT(*)`.
- **All three gap-fill to a regular frequency.** Each series is filled to *its own* span, not a common calendar: five Citi Bike stations with 1,153–1,582 raw rows returned 1,341–1,768 rows. Row counts out will exceed row counts in on any gapped series. This is the third of three different behaviors over the same gap: `ARIMA_PLUS` interpolates a real value across the entire span (measured on the Citi Bike outage: `194.0` -> a constant `~-0.415`/day decline -> `118.0`, day by day, for all ~183 missing days), `ARIMA_PLUS_XREG` returns `NULL` across it, and these TVFs gap-fill. Same data, same gap, three answers.
- **On a gapped series, the gap-filling manufactures the structural break `ML.DETECT_CHANGE_POINTS` then reports — this is the most consequential behavior here.** The Citi Bike table has a dataset-wide ingestion outage (all five stations resume 2017-04-01; four stop 2016-09-30, one 2016-08-22). Labelling each detected window by whether it contains the edge of a ≥3-day gap, **six of the seven windows across the five stations are gap edges**. Only one is not: `West St & Chambers St`, 2016-04-27 → 2016-05-07, all 11 days present, with a genuine level shift across it (averaging raw daily counts: 248.1 trips/day over the 30 days before the window, 210.9 inside it, 373.4 over the 30 days after). The function is not wrong — after interpolation the series really does step down into a flat stretch and back out — but the shift is an artifact of missing data, not of the process being measured. **The practical workflow is two queries: profile the gaps, then keep the change points that do not land on one.** Without that filter, six of seven findings here would be an ingestion story reported as a business story.
- `status` is the empty string on success, never `NULL`; `status IS NULL` matches nothing.
- Bad `SEASONALITIES` values enumerate the valid set for `HOURLY`, `NO_SEASONALITY` and `AUTO`, but return a bare `Invalid seasonality value 'X' in SEASONALITIES.` for anything else (`MINUTELY`, `PER_MINUTE`, `PER_HOUR`, `AUTO_FREQUENCY`, `ANNUAL`, `''`, ordinary typos). Recorded as observed message behavior, not an inferred parser rule.
- **Not a substitute for anomaly detection.** On the same series, `ML.DETECT_ANOMALIES` (`anomaly_prob_threshold` 0.95) flagged 79 rows and `ML.DETECT_CHANGE_POINTS` found 2 windows, with **zero overlap**. Orthogonal detectors, not two sensitivities of one. Note the separation is sharper here than it would generally be, for the reason above: those two windows bracket an interpolated stretch that is smooth by construction and so holds nothing for a row-level detector to flag. The zero shows the two functions answer different questions; it does not measure how far apart their answers usually fall.

**Related — three functions, three questions:**

| Question | Function | Granularity |
|---|---|---|
| Is *this row* an outlier? | [`ML.DETECT_ANOMALIES`](model-lifecycle-functions.md#mldetect_anomalies) | Row |
| Did the series *shift* here? | `ML.DETECT_CHANGE_POINTS` | Window |
| Has the *whole dataset* moved? | [`ML.VALIDATE_DATA_DRIFT`](model-management-monitoring.md#mlvalidate_data_drift) | Dataset |

For zero-shot (TimesFM) forecasting and anomaly detection with no model *and* no fitted decomposition, see [`AI.FORECAST` / `AI.DETECT_ANOMALIES`](../../bq-ai-functions/RESOURCES.md) in the sibling project.

**BigFrames API:** No equivalent. `bigframes.ml.forecasting.ARIMAPlus` covers the *model* path only; reach these TVFs via `bigframes.pandas.read_gbq` over the SQL.

**Repo example (tested):** `data+ai/bq-ml/functions/time_series/time_series.ipynb` and `time_series.sql` — all three functions on the Citi Bike series shared with `models/arima_plus/`, including the `ARIMA_PLUS` head-to-head, the change-points-vs-anomalies overlap test, and the gap-fill demonstration.
