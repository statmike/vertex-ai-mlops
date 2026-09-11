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

---

## `AI.CAUSAL_EFFECT`

> **Why an `AI.*` function is documented here.** The dividing line between this project and [`bq-ai-functions`](../../bq-ai-functions/RESOURCES.md) is *"does the reader manage a model artifact,"* not *"does the name start with `AI.`"* — and by that test this function belongs with the model-free `ML.*` TVFs above. It creates nothing, and its subject is causal inference, the topic [`workflows/`](../README.md#workflows) already covers in five other places. The sibling project keeps a pointer so its `AI.*` list stays complete.

- **Description:** Table-valued function implementing [CausalImpact](https://google.github.io/CausalImpact/)-style intervention analysis. Given **one series and one intervention timestamp**, it fits a counterfactual on the pre-intervention window and reports the cumulative gap afterward, with a p-value. It accepts **no control series and no covariates** — the documentation's stated reason is avoiding bias from experiment spillover effects.
- **Use cases:**
  - Estimating the effect of a launch, price change, outage or policy when no control group exists and no experiment was run.
  - Screening many series at once via `id_cols` — each unit is analyzed independently and returns its own row.
  - A first pass before reaching for [`difference_in_differences`](../workflows/difference_in_differences/) or [`synthetic_control`](../workflows/synthetic_control/), which are stronger but need a control unit.
- **documentation:** [AI.CAUSAL_EFFECT](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-causal-effect)
- **Type:** Table-valued (TVF).
- **Applies to models:** None — model-free. Verified: model count in the dataset identical before and after, and `INFORMATION_SCHEMA.JOBS` shows a single `SELECT` job with `parent_job_id` null and no child jobs.
- **Status:** **Preview** as of 2026-09-11. **Connection required:** No.

**Syntax:**
```sql
AI.CAUSAL_EFFECT(TABLE, timestamp_col => STRING, data_col => STRING,
                 intervention_timestamp => TIMESTAMP literal,
                 [id_cols => ARRAY<STRING>], [num_post_intervention_points => INT64],
                 [confidence_level => FLOAT64], [output_time_series => BOOL])
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| (first argument) | relation | Yes | — | A `TABLE` reference or parenthesized subquery. |
| `timestamp_col` | `STRING` | Yes | — | Name of the `TIMESTAMP` column. |
| `data_col` | `STRING` | Yes | — | Name of the metric column. |
| `intervention_timestamp` | `TIMESTAMP` **literal** | Yes | — | Splits pre from post. Must be a literal — see limitations. |
| `id_cols` | `ARRAY<STRING>` | No | — | `STRING`/`INT64` columns identifying separate series; each combination returns its own row. |
| `num_post_intervention_points` | `INT64` | No | all | Caps how many post-intervention points are included. |
| `confidence_level` | `FLOAT64` in `[0, 1)` | No | `0.95` | Sets `lower_bound`/`upper_bound` only — **not** `p_value`. |
| `output_time_series` | `BOOL` | No | `FALSE` | `TRUE` adds the pointwise columns. |

**Outputs:**

| Mode | Columns |
|---|---|
| Default | `absolute_effect`, `relative_effect`, `p_value`, `prob_causal_effect`, `status` |
| `output_time_series => TRUE` | the above repeated on every row, plus `<timestamp_col>`, `is_post_intervention`, `<data_col>`, `predicted_<data_col>`, `lower_bound`, `upper_bound` |

`absolute_effect` is the **cumulative** gap over the post-intervention window, not a per-period rate. `prob_causal_effect` is exactly `1 - p_value`. Pre-intervention rows carry `NULL` for the predicted and bound columns.

**Measured behavior** (Texas weekly COVID case rate per 100k, 9 pre-intervention weeks and 5 post, verified 2026-09-11):

| Component | Finding |
|---|---|
| Counterfactual | **Bit-for-bit identical** to `ARIMA_PLUS` + `ML.FORECAST` on default options — all 5 forecasts and all 10 interval bounds compare equal under exact float equality. |
| `absolute_effect` | `SUM(actual - expected)` over the post rows. Reproduced by hand exactly. |
| `relative_effect` | `SUM(actual - expected) / SUM(expected)`. Reproduced by hand exactly. |
| `p_value` | **Does not reproduce.** Six constructions tested; the closest (sum of the pointwise standard errors, i.e. perfectly correlated forecast errors) gives 0.303489 against the reported 0.304812 — 0.27% off. |
| Determinism | Deterministic. Identical to the last digit across cache-disabled repeat calls, unlike the TimesFM-backed `AI.*` functions. |
| `confidence_level` | `p_value` is **invariant** to it while the interval widths move, so the p-value derives from the model's internal variance rather than the rendered bounds. |
| Engine | Fixed. `model => 'TimesFM 2.0'` fails with *"Named argument model not found in signature."* Despite the `AI.` prefix, it shares no engine with `AI.FORECAST`. |

**Best practices:**
- Divide `absolute_effect` by the number of post-intervention points before comparing against any per-period estimate.
- **Rebuild the counterfactual as an `ARIMA_PLUS` model when the answer matters.** Because the function returns no artifact, there is otherwise no `ML.ARIMA_EVALUATE` to tell you the selected order and no `ML.EXPLAIN_FORECAST` to show the decomposition. On the tested series `auto_arima` chose `(0, 2, 0)` with `has_drift = False` and `[NO_SEASONALITY]` — a twice-differenced random walk, which is exactly why the counterfactual is a perfect straight line.
- Read the p-value before quoting the point estimate. On a short pre-period the two often disagree about what the data supports.
- Test `status` with `status = ''`; it is the empty string on success.

**Limitations:**
- **`intervention_timestamp` must be a literal.** `TIMESTAMP '2020-07-03'` works; `TIMESTAMP("2020-07-03")` fails with *"expects the intervention_timestamp argument to be a TIMESTAMP literal, but TIMESTAMP was provided."* It cannot be a query parameter or a computed expression, so parameterizing the call means string-substituting the SQL.
- **No `ARIMA_PLUS` options are reachable** — no `holiday_region`, `data_frequency`, or manual `(p,d,q)`. Defaults or nothing.
- **A univariate counterfactual cannot see a common shock.** It attributes the *entire* deviation from the unit's own past trend to the intervention. Measured on one dataset against two control-based estimators: `AI.CAUSAL_EFFECT` **−56.52** per week versus difference-in-differences **−19.29** and synthetic control **−19.28** — same sign, ~2.9× the magnitude, because the control methods net out a nationwide surge the donor states also experienced and this function has no way to. There is no diagnostic inside the function that flags this.
- **Three points is a hard floor, not a sensible minimum.** Below three, `status` returns *"The time series data is too short."* Nine pre-period points already produced a counterfactual with no seasonal structure and week-5 intervals of ±200 on a series whose full observed range is ~203.
- Prediction intervals are exactly symmetric around the forecast and widen quickly with horizon.
- **Preview** — arguments and output columns can change.

**Related:** [`AI.KEY_DRIVERS`](../../bq-ai-functions/reference/augmented-analytics.md) is the other augmented-analytics `AI.*` function Google groups with this one; it answers "which dimensions explain a metric change," not "did this intervention cause one." For the control-based alternatives see [`workflows/difference_in_differences/`](../workflows/difference_in_differences/) and [`workflows/synthetic_control/`](../workflows/synthetic_control/).

**BigFrames API:** No equivalent — `bigframes.bigquery` exposes several `AI.*` functions but not this one. Reach it via `bigframes.pandas.read_gbq` over the SQL. `bigframes.ml.forecasting.ARIMAPlus` does cover the manual-reproduction path.

**Repo example (tested):** `data+ai/bq-ml/workflows/causal_effect/causal_effect.ipynb` and `causal_effect.sql` — the bit-for-bit `ARIMA_PLUS` reproduction, the six p-value constructions, the `confidence_level` and determinism probes, and the three-estimator comparison on one panel.

---

## `ML.METRICS`
- **Description:** Model-free table-valued function that computes evaluation metrics from a relation that already contains an **actual** column and a **predicted** column. There is no model argument — nothing is trained and nothing is loaded, so the predictions may come from BigQuery ML, Vertex AI batch prediction, a third-party scoring API, or a file someone loaded last quarter. **Preview.**
- **Use cases:**
  - Scoring predictions after the model that produced them has been deleted, deprecated, or moved out of reach.
  - Comparing a BQML model, an external model, and a naive baseline under one implementation of `r2_score` / `f1_score`, so the numbers are actually comparable.
  - Recomputing a metric on demand for a model card, a release gate, or an audit — the computation is reproducible where `AI.EVALUATE` is not.
  - Backfilling metrics over an archive of predictions and actuals.
- **documentation:** https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-metrics
- **Type:** Table-valued function. Returns exactly one row.
- **Applies to models:** None — model-free utility (operates on saved predictions, not a model).

**Syntax:**
```sql
ML.METRICS(
  { TABLE `project.dataset.table` | (QUERY_STATEMENT) },
  predicted_col => 'predicted_column_name',
  actual_col    => 'actual_column_name',
  task_type     => 'regression' | 'classification'
)
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| relation | `TABLE` reference or `(QUERY_STATEMENT)` | Yes | — | The rows to score. See the `80038528` limitation below before choosing the query form. |
| `predicted_col` | `STRING` | Yes | — | Name of the column holding predictions. |
| `actual_col` | `STRING` | Yes | — | Name of the column holding ground truth. Must share a type with `predicted_col`. |
| `task_type` | `STRING` | Yes | — | `'regression'` or `'classification'`. Determines which metric set is returned. |

**Outputs (`task_type => 'regression'`):**

| Column | Type | Description |
|--------|------|-------------|
| `mean_absolute_error` | `FLOAT64` | Mean of `ABS(actual - predicted)`. |
| `mean_squared_error` | `FLOAT64` | Mean of `(actual - predicted)^2`. |
| `mean_squared_log_error` | `FLOAT64` | Mean squared error of `LOG(1 + x)` values. |
| `median_absolute_error` | `FLOAT64` | Median of `ABS(actual - predicted)`. |
| `r2_score` | `FLOAT64` | Coefficient of determination. Negative when the predictions are worse than predicting the mean. |
| `explained_variance` | `FLOAT64` | Fraction of variance explained; differs from `r2_score` when the errors are biased. |

**Outputs (`task_type => 'classification'`):**

| Column | Type | Description |
|--------|------|-------------|
| `precision` | `FLOAT64` | See the BOOL/STRING note below — the definition depends on the column type. |
| `recall` | `FLOAT64` | Same. |
| `accuracy` | `FLOAT64` | Fraction of correct predictions. Type-independent. |
| `f1_score` | `FLOAT64` | Same type dependence as `precision`/`recall`. |

**Best practices:**
- **Materialize predictions you intend to score.** Once written down, a prediction table outlives the model, the endpoint, and the vendor contract — and `ML.METRICS` is what makes that table useful.
- **Prefer the `TABLE` form.** It succeeded on every relation tested; the `(QUERY_STATEMENT)` form did not (below).
- Choose the label column type deliberately rather than inheriting it from an upstream `CAST` — the type changes the metric definitions.
- Use it as the single scorer when comparing models from different systems, so "our MAE" and "their MAE" mean the same thing.

**Limitations:**
- **Preview.**
- `predicted_col` and `actual_col` must share a type. Rows where either is `NULL` are dropped before anything is computed.
- No `log_loss`, no `roc_auc`, and no confusion matrix — `ML.EVALUATE` on a trained classification model returns the first two. Probability-threshold tuning is not possible from these four numbers.
- **The column type silently redefines `precision`, `recall` and `f1_score`.** A `BOOL` pair is scored as **binary** — the positive (`TRUE`) class alone. The `STRING` rendering of the identical values is scored as **multiclass and macro-averaged**, even with exactly two classes. Measured on one 62-row table (12 positives; TP 11, FP 10, FN 1, TN 40): precision `0.5238095238095238` as `BOOL` versus `0.7497096399535423` as `STRING`, `f1_score` `0.6666666666666666` versus `0.7728937728937728`; `accuracy` was `0.8225806451612904` either way. On balanced data the two agree, which is how this stays hidden until the classes are lopsided. Note also that macro `f1_score` is the mean of the per-class F1s, not the F1 of the macro precision and recall. **This is a BigQuery-wide convention, not an `ML.METRICS` quirk** — [`AI.EVALUATE`](../../bq-ai-functions/RESOURCES.md)'s TabFM branch was measured to follow the identical rule.
- **Internal error `80038528` on the `(QUERY_STATEMENT)` form.** Some relations fail with a generic "An internal error occurred... usually caused by a transient issue" and `Error: 80038528`. It is not transient — the same statement fails identically on every run. The `TABLE` form of the very same data succeeded in every case tested (7 of 7), including every relation whose query form failed. No rule for *when* the query form breaks emerged; ruled out by direct test: cross-project references (a public table works in query form; a copy of the failing table inside the caller's own project still fails), `JOIN`s (a join across two of the caller's own tables works), `NULL`s in either column, `REQUIRED` schema modes, row count (62 works, 150 fails, 32,561 works), and the presence of `WHERE` / `LIMIT` / computed expressions. Observed failing: `ml_datasets.penguins`, `ml_datasets.iris`, a copy of `penguins` in the caller's project. Observed working: `ml_datasets.census_adult_income`, `usa_names.usa_1910_2013`, a 62-row prediction table, and `penguins` wrapped in a `GROUP BY`. No mechanism is claimed. **Workaround: materialize and pass `TABLE`.**
- **The client libraries retry that error.** `internalError` is on `google-cloud-bigquery`'s default retryable list, so `client.query(sql).result()` resubmits the job until its 600-second deadline — **12 job attempts over 604 seconds, measured** — before raising. Pass `retry=None` to `client.query()` and `retry=None, job_retry=None` to `.result()` to fail fast.

**Related — three ways to get evaluation metrics:**

| You have | Function | Notes |
|---|---|---|
| A trained model plus an eval set | [`ML.EVALUATE`](model-lifecycle-functions.md#mlevaluate) | Returns `log_loss` and `roc_auc` too; requires the model object to exist |
| Two columns, actual and predicted | `ML.METRICS` | No model. Measured against `ML.EVALUATE` on the same predictions, every regression metric agrees to at least 13 significant digits (relative gaps ~1e-16, floating-point summation order); which ones land bit-identical varies between runs |
| Raw data and no model at all | [`AI.EVALUATE`](../../bq-ai-functions/RESOURCES.md) | Trains TabFM/TimesFM internally; same metric names, but not reproducible run to run |

**BigFrames API:** No wrapper for `ML.METRICS`. `bigframes.ml.metrics` (`r2_score`, `accuracy_score`, `roc_auc_score`, …) computes metrics client-side over BigFrames Series — a different thing, useful when the predictions are already in a DataFrame. Reach the SQL function via `bigframes.pandas.read_gbq`.

**Repo example (tested):** `data+ai/bq-ml/functions/evaluation/evaluation.ipynb` and `evaluation.sql` — trains a `LINEAR_REG` on `penguins`, saves predictions, **drops the model**, and shows `ML.EVALUATE` failing with *Not found: Model* while `ML.METRICS` returns the same six metrics; scores a constant baseline the model can be compared against; measures the BOOL/STRING split on one table and reproduces both rows by hand from the confusion matrix; tests the same split in `AI.EVALUATE`; and reproduces `80038528` with the ruled-out mechanisms above.

---

## Exploratory data analysis: `ML.DESCRIBE_DATA`, `ML.CORRELATION`

The two questions asked of a dataset before anything is modeled: *what is in it* and *what moves with the target*. Both are table-valued functions, both are model-free, and neither needs a connection.

They are deliberately **not** filed with the data-quality functions. `ML.VALIDATE_DATA_SKEW` / `ML.VALIDATE_DATA_DRIFT` answer "has this dataset **changed**" — a comparison between two relations. These two answer "what **is** this dataset" from one relation. Profile here, monitor in [Model Management & Monitoring](model-management-monitoring.md#model-monitoring--data-validation).

**Repo example (tested):** [`functions/exploration/`](../functions/exploration/) — `exploration.ipynb` and `exploration.sql` cover both functions end to end.

---

## `ML.DESCRIBE_DATA`
- **Description:** Computes descriptive statistics for every column of a table or subquery in one pass — row/value/null/zero counts, min/max, mean, stddev, median, quantiles, distinct count, top values, and array-length statistics. One row per input column. **GA.**
- **Use cases:**
  - Profile a dataset before writing the first `CREATE MODEL` — types, ranges, cardinality, and missingness in a single query.
  - Find placeholder-encoded nulls (`' ?'`, `'N/A'`, `-1`, `9999`) that `num_nulls` cannot see.
  - Decide which columns are numeric enough to correlate and which need bucketizing or encoding first.
  - Snapshot a profile before/after a pipeline change, as an informal precursor to a formal skew/drift check.
- **documentation:** https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-describe-data
- **Type:** Table-valued function. One row per input column.
- **Applies to models:** None — model-free utility (operates on data, not a model).

**Syntax:**
```sql
ML.DESCRIBE_DATA(
  { TABLE `PROJECT_ID.DATASET.TABLE_NAME` | (QUERY_STATEMENT) }
  [, STRUCT(
       num_quantiles AS num_quantiles,
       num_array_length_quantiles AS num_array_length_quantiles,
       top_k AS top_k
     )]
)
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| input data | `TABLE` reference or `(QUERY_STATEMENT)` | Yes | — | Data to profile. |
| `num_quantiles` | `INT64` | No | **2** | Quantiles for numerical columns. Range \[2, 100000\]. The returned `quantiles` array has `num_quantiles + 1` entries (the boundaries), so the default returns min / median / max. |
| `num_array_length_quantiles` | `INT64` | No | 10 | Quantiles for `ARRAY` lengths. Range \[1, 100000\]. Same `+ 1` boundary convention. |
| `top_k` | `INT64` | No | 1 | Top values returned per categorical column. Range \[1, 10000\]. |

**Outputs:** one row per input column. Columns not applicable to a given input type come back `NULL` (or an empty array).

| Column | Type | Populated for | Description |
|--------|------|---------------|-------------|
| `name` | `STRING` | all | Input column name. |
| `num_rows` | `INT64` | all | Rows in the input. |
| `num_values` | `INT64` | all | Non-null values considered. Differs from `num_rows` for `ARRAY` columns, which are unnested first. |
| `num_nulls` | `INT64` | all | Null count. **Counts SQL `NULL` only** — see the limitation below. |
| `num_zeros` | `INT64` | numeric | Count of exact zeros. |
| `min` / `max` | `STRING` | all | MIN / MAX, rendered as strings regardless of input type. |
| `mean` / `stddev` / `median` | `FLOAT64` | numeric | The docs spell the middle one `stdev`; the actual output column is **`stddev`**. |
| `quantiles` | `ARRAY<FLOAT64>` | numeric | `APPROX_QUANTILES` boundaries, `num_quantiles + 1` of them. |
| `unique` | `INT64` | categorical | `APPROX_COUNT_DISTINCT`. |
| `avg_string_length` | `FLOAT64` | `STRING` | Mean length of the non-null values. |
| `top_values` | `ARRAY<STRUCT<value STRING, count INT64>>` | categorical | `top_k` entries. |
| `min_array_length` / `max_array_length` / `avg_array_length` / `total_array_length` | `INT64` / `FLOAT64` | `ARRAY` | Array-length statistics. |
| `array_length_quantiles` | `ARRAY<INT64>` | `ARRAY` | `num_array_length_quantiles + 1` boundaries. |
| `dimension` | `STRING` | — | Present in the output schema and `NULL` in every call tested; there is no setting that populates it (`dimension_cols` is rejected: *unsupported setting field*). |

**Best practices:**
- **Read `num_nulls` and `min`/`max` together.** A `num_nulls` of 0 next to a `min` of `' ?'` is the signature of string-encoded missingness. On `census_adult_income`, `workclass` reports `num_nulls = 0` while 1,836 rows hold the literal string `' ?'` — repair with `NULLIF(TRIM(col), '?')` before doing anything statistical.
- **Raise `top_k`.** The default of 1 gives you the mode and nothing else; 5–10 is what makes a categorical column legible.
- **Raise `num_quantiles`.** The default of 2 gives min / median / max. `4` or `10` is what shows you the shape.
- Run on a representative slice (filter by date) rather than the full table to control cost.
- Profile before correlating — [`ML.CORRELATION`](#mlcorrelation) requires numeric columns, and this tells you which ones are actually numeric and how much of each is missing.

**Limitations:**
- **`num_nulls` counts SQL `NULL` only.** Placeholder encodings are invisible to it, and every downstream statistic (`mean`, `stddev`, `unique`, `top_values`) silently treats the placeholder as a real value.
- The documented output column `stdev` does not exist — selecting it fails with *Unrecognized name: stdev; Did you mean stddev?*
- `min` / `max` are `STRING`, so ordering them in the output is lexicographic, not numeric.
- Quantiles are approximate (`APPROX_QUANTILES`), and `unique` is approximate (`APPROX_COUNT_DISTINCT`).
- `ARRAY` columns are unnested before statistics are computed; `ARRAY<STRUCT<INT64, numerical>>` is treated as a sparse `ARRAY<numerical>`.

**BigFrames API:** No wrapper. `bigframes.pandas.DataFrame.describe()` is a pandas-shaped equivalent compiled to BigQuery SQL — a different implementation with a different output shape (statistics as rows, columns as columns) and no `top_values` or array handling. Reach the SQL function via `bigframes.pandas.read_gbq`.

**Repo example (tested):** [`functions/exploration/`](../functions/exploration/) — profiles `census_adult_income` numerically and categorically, catches the `num_nulls = 0` / `min = ' ?'` contradiction, and demonstrates the `stdev` → `stddev` error live.

---

## `ML.CORRELATION`
- **Description:** Computes the correlation between one target column and one or more numeric correlation columns, optionally sliced by dimension columns. Three methods: `PEARSON`, `SPEARMAN`, `KENDALL`. With `dimension_cols`, the output is a full `GROUP BY CUBE` over those dimensions. **Preview.**
- **Use cases:**
  - Rank candidate features against a target before feature selection.
  - Detect **Simpson's-paradox-shaped** structure: the whole-table coefficient versus the same coefficient inside every segment, in one query.
  - Compare linear (`PEARSON`) against monotone (`SPEARMAN`) association to find non-linear-but-ordered relationships.
  - Produce a correlation matrix over a wide table without writing one `CORR()` per pair.
- **documentation:** https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-correlation
- **Type:** Table-valued function. One row per (correlation column × cube cell).
- **Applies to models:** None — model-free utility.

**Syntax:**
```sql
ML.CORRELATION(
  { TABLE `PROJECT_ID.DATASET.TABLE_NAME` | (QUERY_STATEMENT) },
  target_col              => 'target',
  target_correlation_cols => 'metric' | ['metric_1', 'metric_2', ...]
  [, dimension_cols       => 'dim'    | ['dim_1', 'dim_2', ...] ]
  [, method               => 'PEARSON' | 'SPEARMAN' | 'KENDALL' ]
)
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| input data | `TABLE` reference or `(QUERY_STATEMENT)` | Yes | — | Data to correlate. |
| `target_col` | `STRING` | Yes | — | Name of the numeric target column. |
| `target_correlation_cols` | `STRING` or `ARRAY<STRING>` | Yes | — | Numeric column(s) to correlate against the target. |
| `dimension_cols` | `STRING` or `ARRAY<STRING>` | No | none | Groupable column(s) to slice by. **Maximum 12.** |
| `method` | `STRING` | No | `'PEARSON'` | `'PEARSON'`, `'SPEARMAN'`, or `'KENDALL'`. |

**Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| `target_col` | `STRING` | Echo of the target column name. |
| `corr_col` | `STRING` | Which correlation column this row is for. |
| `correlation` | `FLOAT64` | The coefficient. `NULL` for degenerate segments (a single row) — those rows are **not** dropped. |
| `segment_size` | `INT64` | Rows in the segment. **Not** the pairwise *n* the coefficient used. |
| `segment_proportion` | `FLOAT64` | `segment_size` as a fraction of the whole input. |
| `segment` | `ARRAY<STRUCT<dimension_col STRING, dimension_value JSON>>` | Which dimensions this row is *not* rolled up over, and their values. Empty array on the global row. |
| one column per `dimension_cols` entry | source type | The dimension value, or `NULL` — for either of two reasons; see below. |

**Best practices:**
- **Round before comparing.** Never compare `correlation` across queries with `=`.
- **Use `segment` to disambiguate `NULL`.** A dimension column is `NULL` both when the row is a rollup over that dimension and when the segment *is* the genuine-`NULL` group. The rolled-up dimension is **absent** from `segment`; the genuine-`NULL` group is **present** in `segment` with `dimension_value` = JSON `null`. `NOT EXISTS (SELECT 1 FROM UNNEST(segment) s WHERE s.dimension_col = 'col')` is the rollup test.
- **Bucketize continuous columns before using them as dimensions** — see [`ML.QUANTILE_BUCKETIZE`](#mlquantile_bucketize) and [`functions/bucketizing/`](../functions/bucketizing/).
- **Filter by `segment_size`** to keep the cube readable, but treat it as an upper bound on evidence, not a sample size.
- Run [`ML.DESCRIBE_DATA`](#mldescribe_data) first — it tells you the `NULL` rates that make `segment_size` misleading, and catches placeholder-encoded nulls before they become a segment.

**Limitations:**
- **Preview.**
- **`SPEARMAN` is not the textbook Spearman.** BigQuery computes it as `CORR()` over SQL `RANK()` — **competition (min) ranks**, where every tied observation gets the smallest rank in its group. SciPy, R, and pandas' default use **mid-ranks** (the average of the ranks the tie spans). On tied data the two disagree in the second decimal place: on `census_adult_income`, `education_num` vs `hours_per_week` reads `0.172612` from `ML.CORRELATION` and `0.167215` from `scipy.stats.spearmanr`. Reproduce BigQuery's number with `pandas.Series.rank(method='min')` or a pure-SQL `CORR()` over `RANK()`; on tie-free data all conventions agree. Not documented.
- **`KENDALL` *is* tie-corrected — it is tau-b.** So within one function, Kendall corrects for ties and Spearman does not. Matched against `scipy.stats.kendalltau(variant='b')` to floating-point noise; `variant='c'` does not match.
- **`KENDALL` is O(n²) and the constant is not small.** Measured on a synthetic table with the cache off, every doubling of rows multiplies slot time several-fold and the fitted exponent lands near 2, while `PEARSON` and `SPEARMAN` show no size dependence at all across the same range and return a million rows in about a second. A `KENDALL` on 100,000 rows of that shape did not finish inside 12 minutes. Sample or segment before using it.
- **Projecting the `segment` column changes `correlation`** in its last three digits, reproducibly, with the query cache off. Column pruning changes the physical plan, which changes the float summation order. Every projection that includes `segment` returns one value; every projection that omits it returns another. The gap lands in the sixteenth decimal place.
- **`PEARSON` matches `CORR()` but is not bit-identical** — agreement to ~15 significant digits, residual ~4e-16, float summation order again.
- **`segment_size` is the segment's row count, not the pairwise *n*.** Correlation is computed pairwise: for each correlation column, rows where either that column or the target is `NULL` are dropped. Two `corr_col` rows in the same segment can rest on different sample sizes and nothing in the output says so. `WHERE segment_size >= 30` does not guarantee 30 usable pairs.
- **`dimension_cols` accepts any groupable type, including `INT64`.** Passing a continuous numeric column silently produces one segment per distinct value (73 distinct ages → 74 output rows, no error).
- **Maximum 12 `dimension_cols`** — a 13th fails with an explicit error. Output row count is the full CUBE cell count, including degenerate single-row cells, so it grows fast: three dimensions on `census_adult_income` produce 134 rows.

**Related — three ways to correlate in BigQuery:**

| You want | Use | Notes |
|---|---|---|
| One pair, Pearson | `CORR(x, y)` | Aggregate function; matches `ML.CORRELATION` `PEARSON` to ~15 digits |
| One target vs many columns, optionally sliced | `ML.CORRELATION` | Three methods, CUBE slicing, one query |
| Which features *drive* an outcome, not just co-move | [`AI.KEY_DRIVERS`](../../bq-ai-functions/reference/augmented-analytics.md) / [`AI.CAUSAL_EFFECT`](#aicausal_effect) | Correlation is symmetric and pairwise; these are neither |

**BigFrames API:** No wrapper. `bigframes.pandas.DataFrame.corr()` is a pandas-shaped equivalent compiled to BigQuery SQL — Pearson only, no dimension slicing, and a matrix rather than a target-vs-columns shape. Reach the SQL function via `bigframes.pandas.read_gbq`.

**Repo example (tested):** [`functions/exploration/`](../functions/exploration/) — establishes `PEARSON` == `CORR()`, reproduces the `SPEARMAN` min-rank convention three ways (pandas, pure SQL, and a tie-free control), confirms `KENDALL` is tau-b against SciPy, measures the Kendall cost curve, matches the `dimension_cols` output row count against `GROUP BY CUBE` exactly, separates the two kinds of dimension `NULL`, and shows `segment_size` overstating the pairwise *n*.

---

## Point-in-time feature retrieval: `ML.FEATURES_AT_TIME`, `ML.ENTITY_FEATURES_AT_TIME`

Two model-free table-valued functions that answer *"what did we know about this entity at this moment?"* — the question a feature store exists to answer. `ML.FEATURES_AT_TIME` retrieves every entity's vector as of **one shared timestamp** (the online-serving shape); `ML.ENTITY_FEATURES_AT_TIME` retrieves each entity's vector as of **its own timestamp** (the training-set shape, and what prevents label leakage). Neither trains a model, neither needs a connection, and neither creates an object to clean up. There is no feature store to provision — the feature table is an ordinary BigQuery table.

Both take the same **feature table contract**: a `STRING` column named `entity_id`, a `TIMESTAMP` column named `feature_timestamp`, and one column per feature (wide format). Column names are **case-insensitive** — verified live, `Entity_ID` and `Feature_TimeStamp` are accepted and the original casing is preserved in the output — but the *types* are not negotiable, and all three violations fail at planning time:

| Violation | Error |
|---|---|
| `entity_id` is `INT64` | `feature_table column 'entity_id' can only be String type but found INT64` |
| `feature_timestamp` is `DATE` | `feature_table column 'feature_timestamp' can only be Timestamp type but found DATE` |
| `feature_timestamp` absent | `feature_table must include a 'feature_timestamp' column` |

**The one thing to carry away:** `ignore_feature_nulls` is a statement about your table's **shape**, not a tuning knob. It is *required* on a sparse history and *harmful* on a dense one, with no error and no visibly wrong output either way.

| Feature table shape | One row is… | A `NULL` means… | `ignore_feature_nulls => TRUE` |
|---|---|---|---|
| **Sparse** (assembled from independent event streams) | one *update* touching a subset of features | this update had nothing to say about that feature | **Required** — reassembles the vector |
| **Dense** (one row per complete observation) | a complete observation | genuinely unknown or not applicable — a *fact* | **Harmful** — fabricates values |
| **EAV** (`entity_key, feature_timestamp, feature_name, feature_value STRUCT<…>`) | one *observation* of one feature | absent rather than `NULL` | Pivots to the sparse shape, so **required** |

Measured on `thelook_ecommerce` at a fixed 2024-01-01 cutoff over 26,979 customers: on the sparse table the flag repaired **17,440** entities whose `lifetime_orders` came back `NULL` only because their most recent row was a shipment or a delivery (down to **0**, with the genuine absences surviving). On the dense table the identical flag invented a delivery duration for **1,572** customers whose latest order was cancelled, processing, or shipped-but-not-arrived — a real measurement of a *different, earlier* order.

---

## `ML.FEATURES_AT_TIME`
- **Description:** Model-free table-valued function returning each entity's most recent feature row(s) as of a single shared point in time. Retrieval only — no model, no connection, no training. **GA.**
- **Use cases:**
  - Building the online serving vector for every entity at `CURRENT_TIMESTAMP()`, with the same feature definitions used for training.
  - Materializing a "state of the world as of date X" snapshot for backtesting or reporting.
  - Aggregating each entity's last N updates (`num_rows > 1`) into recency features.
- **documentation:** https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-feature-time
- **Type:** Table-valued function.
- **Applies to models:** None — model-free utility.

**Syntax:**
```sql
ML.FEATURES_AT_TIME(
  { TABLE `project.dataset.feature_table` | (QUERY_STATEMENT) }
  [, time => TIMESTAMP]
  [, num_rows => INT64]
  [, ignore_feature_nulls => BOOL])
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| feature relation | `TABLE` reference or `(QUERY_STATEMENT)` | Yes | — | Must satisfy the contract above. The query form is how you pivot an EAV table on the way in. |
| `time` | `TIMESTAMP` | No | `CURRENT_TIMESTAMP()` | The cutoff. Only rows with `feature_timestamp <= time` are considered. **A single timestamp — not a list.** |
| `num_rows` | `INT64` | No | `1` | Rows returned per entity, most recent first. |
| `ignore_feature_nulls` | `BOOL` | No | `FALSE` | Per feature column, walk back to the most recent row where *that* column is non-`NULL`, independently of the others. |

**Outputs:** `entity_id`, `feature_timestamp`, and every feature column of the input, **in the input's column order** (verified — see below). One row per entity, or `num_rows` per entity.

**Best practices:**
- **Decide `ignore_feature_nulls` from the table's shape, not from the output's appearance.** See the table above. This is the single highest-value decision in using either function.
- **Collapse simultaneous events on write.** Duplicate `(entity_id, feature_timestamp)` pairs make "the most recent row" ambiguous and the tie is broken arbitrarily — a small, silent source of run-to-run variation. A `GROUP BY entity_id, feature_timestamp` in the feature table's build fixes it structurally.
- **Carry a copy of the event time as an ordinary feature column** if you need provenance; see the limitation below.
- Prefer the function to a hand-written `QUALIFY` window even though they are provably equivalent — the hand-written form has a trap the function cannot have (below).

**Limitations:**
- **`time` takes one timestamp, not a list.** `time => [TIMESTAMP '2023-01-01', TIMESTAMP '2024-01-01']` fails with `Unable to coerce type ARRAY<TIMESTAMP> to expected type TIMESTAMP`. For many cutoffs, use `ML.ENTITY_FEATURES_AT_TIME` or `UNION ALL` the calls.
- **The output `feature_timestamp` is the time you asked for, not the time the source row was written.** Provenance is discarded on every row. With `ignore_feature_nulls => TRUE` the returned row is assembled from several source rows at different instants, so no single source time would even be correct — but you also cannot recover when any value was true.
- **`num_rows > 1` returns more history and erases which row is which.** All returned rows carry the same requested `feature_timestamp` and nothing else distinguishes them, so there is nothing to `ORDER BY`. It supports *aggregating* recent history; it cannot support *sequencing* it.
- **The `QUALIFY` equivalent has an alias-shadowing trap.** The default call is exactly `QUALIFY ROW_NUMBER() OVER (PARTITION BY entity_id ORDER BY feature_timestamp DESC) = 1` followed by overwriting the timestamp — verified with a two-way `EXCEPT DISTINCT` returning 0 and 0. But BigQuery resolves `QUALIFY` **after** the SELECT list, so writing `TIMESTAMP '2024-01-01' AS feature_timestamp` in that same SELECT makes the window's `ORDER BY feature_timestamp DESC` order by the **constant**. Every row ties, `ROW_NUMBER` picks arbitrarily, and roughly **46%** of 26,979 entities get a different — wrong — vector from a query that runs cleanly and reads correctly. The exact count *moves between runs*, which is the tell. The function has no select list to shadow anything with.
- **Not a gotcha, but easy to get backwards: output column order is preserved.** Several clients sort field names when rendering a row as JSON — including `bq --format=json` — which makes the output look alphabetized. Read the order off the schema, not off a serialized row.

**BigFrames API:** No wrapper. Reach the SQL function via `bigframes.pandas.read_gbq`.

**Repo example (tested):** [`functions/feature_store/`](../functions/feature_store/) — builds all three table shapes from `thelook_ecommerce` order/shipment/delivery events, captures the three contract errors, proves the `QUALIFY` equivalence and then breaks it with alias shadowing, measures `ignore_feature_nulls` in both directions (repairing 17,440 on sparse, fabricating 1,572 on dense), traces one entity's vector being assembled from three different source rows, and round-trips the EAV pivot to the sparse answer exactly. Used end to end in [`workflows/feature_store/`](../workflows/feature_store/).

---

## `ML.ENTITY_FEATURES_AT_TIME`
- **Description:** Model-free table-valued function returning each entity's most recent feature row(s) as of **its own** requested point in time, supplied by a second relation. This is the training-set builder: one row per labeled event, features as of that event's instant. **GA.**
- **Use cases:**
  - Assembling a leakage-free training set where every row's features predate its own label window.
  - Backfilling features for an arbitrary set of `(entity, moment)` pairs — an audit sample, a set of support tickets, a batch of decisions to review.
  - Reconstructing what a scoring system would have seen at each historical decision point.
- **documentation:** https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-entity-feature-time
- **Type:** Table-valued function.
- **Applies to models:** None — model-free utility.

**Syntax:**
```sql
ML.ENTITY_FEATURES_AT_TIME(
  { TABLE `project.dataset.feature_table`     | (FEATURE_QUERY_STATEMENT) },
  { TABLE `project.dataset.entity_time_table` | (ENTITY_TIME_QUERY_STATEMENT) }
  [, num_rows => INT64]
  [, ignore_feature_nulls => BOOL])
```

**Inputs:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| feature relation | `TABLE` reference or `(QUERY_STATEMENT)` | Yes | — | Same contract as `ML.FEATURES_AT_TIME`: `entity_id STRING`, `feature_timestamp TIMESTAMP`, wide. |
| entity time relation | `TABLE` reference or `(QUERY_STATEMENT)` | Yes | — | Needs `entity_id STRING` and a `TIMESTAMP` column named **`time`** — *not* `feature_timestamp`. Must be **no larger than 100 MB** (documented). |
| `num_rows` | `INT64` | No | `1` | Rows returned per row of the entity time table. |
| `ignore_feature_nulls` | `BOOL` | No | `FALSE` | Same per-column walk-back as `ML.FEATURES_AT_TIME`. |

**Outputs:** `entity_id`, `feature_timestamp` (**the requested instant**, i.e. the entity table's `time`), and the feature columns. Nothing else.

**Best practices:**
- **Join the label back on `(entity_id, feature_timestamp)`.** The requested instant comes back under the feature table's name for it, which makes the join natural once you expect it.
- **Assert the row count against the entity table before training.** One line, and it is the only thing standing between you and a silently truncated training set.
- **`LEFT JOIN` the entity table back on** if cold-start entities matter, and decide explicitly what a missing vector means (a `0`, a global default, or exclusion by choice rather than by accident).

**Limitations:**
- **There is no `time` argument** — the entity table *is* the time argument. The naming asymmetry (`time` here, `feature_timestamp` there) is the most common first mistake.
- **The entity table's extra columns are dropped.** Only `entity_id` and the requested time come back. Your label is exactly such a column.
- **It is an INNER join.** An entity with no feature row at or before its requested instant is **omitted**, not returned with `NULL` features. Verified: 26,979 requests placed one day before each customer's first event returned **0** rows. The dropped rows are not a random sample — they are precisely the cold-start cases (new customers, new products, the first weeks of any entity's life). Dropping them makes a training set look cleaner and a model look better while removing the population it will most often be asked about.
- **100 MB cap on the entity time relation.** Documented, and a real constraint for large training sets — `entity_id` plus `time` for tens of millions of rows will exceed it. Partition the build by time window or entity range and `UNION ALL` the results.
- The output `feature_timestamp` carries the same loss of provenance described under `ML.FEATURES_AT_TIME`.

**Related — choosing between the two:**

| You need | Function |
|---|---|
| One shared cutoff for every entity (serving *now*, or one snapshot date) | [`ML.FEATURES_AT_TIME`](#mlfeatures_at_time) |
| A different cutoff per entity (a training set, an audit sample) | `ML.ENTITY_FEATURES_AT_TIME` |
| Both, against one feature table | That is offline/online parity — see [`workflows/feature_store/`](../workflows/feature_store/) |

**BigFrames API:** No wrapper. Reach the SQL function via `bigframes.pandas.read_gbq`.

**Repo example (tested):** [`functions/feature_store/`](../functions/feature_store/) covers the mechanics — dropped columns, the inner-join cold-start check, and the `time`/`feature_timestamp` asymmetry. [`workflows/feature_store/`](../workflows/feature_store/) measures what it is worth: the same feature history queried with a naive `GROUP BY entity_id` versus point-in-time, on a shared hash split, reports `roc_auc` **0.9387** against **0.5194** — and the leaky model, fed the point-in-time features production can actually supply, collapses to **0.5299**, where the honest model already was.
