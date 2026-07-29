# Model-Free Preprocessing Functions in BigQuery ML

Contents: [Options by category](#options-by-category) (numerical scaling, bucketizing, encoding, feature engineering, text, distance, image) · [Gotchas verified in this repo](#gotchas-verified-in-this-repo) · [Canonical snippets](#canonical-snippets) · [Go deeper](#go-deeper)

## Options by category

### Numerical scaling

| Function | What it does | When to reach for it vs. siblings |
|---|---|---|
| `ML.STANDARD_SCALER` | Z-score: `(x - AVG(x)) / STDDEV_POP(x)` | Roughly-Gaussian features; unbounded output. Uses **population** stddev, not sample stddev. |
| `ML.MIN_MAX_SCALER` | `(x - MIN) / (MAX - MIN)` → `[0,1]` | Need a bounded range; sensitive to outliers (a single extreme value compresses everything else). |
| `ML.MAX_ABS_SCALER` | `x / MAX(ABS(x))` → `[-1,1]` | Sparse/sign-bearing data where you must not shift/center (no subtraction of a mean/median). |
| `ML.ROBUST_SCALER` | `(x - median) / (q_hi - q_lo)`, default IQR `[25,75]` | Data with outliers — median/IQR aren't dragged around by extreme values the way mean/stddev or min/max are. |
| `ML.NORMALIZER` | Row-wise: `x_i / ||vector||_p` | Not a column scaler at all — normalizes each row's `ARRAY` to unit p-norm (e.g., embedding-like vectors). Scalar, no `OVER()`. |

The first four are **analytic** (mandatory empty `OVER()`); `ML.NORMALIZER` is **scalar** (no `OVER()`, operates within one row's array).

### Bucketizing / discretizing

| Function | What it does | When to reach for it vs. siblings |
|---|---|---|
| `ML.BUCKETIZE` | Bins a numeric value using manually supplied split points | You have domain-knowledge cut points (e.g., age brackets) and want them fixed and explicit. Scalar. |
| `ML.QUANTILE_BUCKETIZE` | Bins into `num_buckets` of ~equal frequency, boundaries from data | You want balanced bin populations on skewed data instead of hand-picked cut points. Analytic — requires `OVER()`. |
| `ML.HASH_BUCKETIZE` | Hashes a **string** into `hash(x) mod hash_bucket_size` | For high-cardinality categorical/string features (the hashing trick), not numeric — different input type from the other two. Scalar. Returns INT64, not a STRING bin label. |

### Encoding categoricals

| Function | What it does | When to reach for it vs. siblings |
|---|---|---|
| `ML.ONE_HOT_ENCODER` | Scalar STRING → sparse one-hot (or dummy, via `drop`) vector | Nominal categorical fed to linear/logistic/tree models where no arbitrary ordering should be implied. |
| `ML.MULTI_HOT_ENCODER` | `ARRAY<STRING>` → sparse multi-hot vector | Genuine multi-value columns (tags, SKUs) — one row can carry many categories at once. |
| `ML.LABEL_ENCODER` | Scalar STRING → ordinal INT64 `[0, n]` | Only when an ordinal integer is acceptable (tree models tolerate the arbitrary alphabetical ordering; linear/logistic models generally shouldn't get this). |

All three are analytic window functions (mandatory `OVER()`), share `top_k`/`frequency_threshold` vocabulary-capping args, and route NULL/unseen/trimmed categories to the same overloaded index/code `0`.

### Feature engineering (imputation, crosses, polynomial expansion)

| Function | What it does | When to reach for it vs. siblings |
|---|---|---|
| `ML.IMPUTER` | Replaces NULLs with `mean`/`median` (numeric) or `most_frequent` (numeric or string) | The only one of this group that's exportable in `TRANSFORM` — use it whenever missing values must be filled consistently at train and serve time. |
| `ML.FEATURE_CROSS` | STRUCT of categorical columns → STRUCT of all crossed combinations, degree `[2,4]` | Capture categorical interactions (e.g. `region × device`) for models that don't learn interactions natively. NOT exportable. |
| `ML.POLYNOMIAL_EXPAND` | STRUCT of ≤10 numeric columns → STRUCT of polynomial terms, degree `[1,4]` | Add curvature (squared/cubic/interaction) terms for linear models. NOT exportable. |
| *(`ML.TRANSPOSE`)* | Does not exist | Use the `TRANSFORM` clause itself — this is a naming red herring, not a function. |

### Text preprocessing

| Function | What it does | When to reach for it vs. siblings |
|---|---|---|
| `ML.NGRAMS` | Merges an `ARRAY<STRING>` of tokens into n-grams over a size range | Upstream step — build bigrams/trigrams before bag-of-words/TF-IDF to capture local token order. Scalar, no `OVER()`. |
| `ML.BAG_OF_WORDS` | Per-document raw term counts | Want raw frequency counts as a baseline text feature; every occurrence weighted equally. Analytic, requires `OVER()`. |
| `ML.TF_IDF` | Per-document term relevance (frequent-in-doc, rare-in-corpus) | Want terms weighted by discriminative value rather than raw count — common terms across all docs get down-weighted vs. BOW. Analytic, requires `OVER()`. |

Both `ML.BAG_OF_WORDS`/`ML.TF_IDF` share the same `top_k`/`frequency_threshold` dictionary controls and index `0` = unknown-term convention as the categorical encoders above.

### Distance / similarity

| Function | What it does | When to reach for it vs. siblings |
|---|---|---|
| `ML.DISTANCE` | Distance between two equal-length vectors: `'EUCLIDEAN'` (default) / `'MANHATTAN'` / `'COSINE'` | Pairwise similarity/distance between two vectors (e.g. embeddings). Brute-force, not an index — use `VECTOR_SEARCH` at scale. |
| `ML.LP_NORM` | Magnitude (Lp norm) of a **single** vector for a given degree | Not pairwise — use to normalize a vector yourself, or to derive a metric `ML.DISTANCE` doesn't support (e.g., Jaccard via dot product ÷ L1 norms). |

### Image preprocessing

| Function | What it does | When to reach for it vs. siblings |
|---|---|---|
| `ML.DECODE_IMAGE` | Image bytes → decoded `STRUCT{shape, values}` | Always the required entry point; every other image function consumes its output. |
| `ML.RESIZE_IMAGE` | Resize decoded image to target height/width | Match the model's expected input resolution; optional `preserve_aspect_ratio`. |
| `ML.CONVERT_IMAGE_TYPE` | Float pixel values → integers `[0, 255)` | Model expects integer/`uint8` pixels (e.g. SSD MobileNet V2) instead of the float output of `ML.DECODE_IMAGE`. |
| `ML.CONVERT_COLOR_SPACE` | RGB → `HSV`/`YIQ`/`YUV`/`GRAYSCALE` | Model was trained on a non-RGB color space; input must already be RGB. |

All four are scalar/row-wise (no `OVER()`) and nest freely, e.g. `ML.CONVERT_COLOR_SPACE(ML.RESIZE_IMAGE(ML.DECODE_IMAGE(data), 224, 280, TRUE), 'YIQ')`.

---

## Gotchas verified in this repo

- **`ML.STANDARD_SCALER` uses `STDDEV_POP` (÷N), not `STDDEV`/`STDDEV_SAMP` (÷N-1).** A manual sanity check using plain `STDDEV(x)` will not match — verified live in `functions/scalers/`.
- **`ML.BUCKETIZE`'s `exclude_boundaries=TRUE` does not NULL out-of-range values.** It drops the outermost split points entirely, merging overflow into the nearest interior bin. With split points `[10, 20, 30]`, default gives 4 bins; `exclude_boundaries=TRUE` collapses this to just 2 bins around the single remaining boundary `20` — no value ever becomes NULL from this option.
- **`ML.ONE_HOT_ENCODER`/`ML.LABEL_ENCODER`/`ML.MULTI_HOT_ENCODER`/`ML.TF_IDF`/`ML.BAG_OF_WORDS` current default is `frequency_threshold = 5`, not the older `0` cited in some repo notebooks.** Verified live: a category/term with fewer than 5 occurrences silently collapses into bucket/index `0`, indistinguishable from NULL or an unseen value at predict time — any rare-but-meaningful category will silently disappear unless `frequency_threshold` is lowered explicitly.
- **`ML.TF_IDF` gives a term appearing in every document a *lower* weight than rarer terms**, while `ML.BAG_OF_WORDS` gives those same terms identical raw counts — verified side-by-side in `functions/text/text.ipynb`.
- **`ML.NGRAMS`'s `range` argument must always be `ARRAY<INT64>`**, even for a single n-gram size. The docs' claimed shorthand (a bare `INT64` meaning `[x, x]`) errors outright with `"Unable to coerce type INT64 to expected type ARRAY<INT64>"`. Use `[x, x]` explicitly.
- **`ML.FEATURE_CROSS` and `ML.POLYNOMIAL_EXPAND` train and predict fine inside a `TRANSFORM`, but are NOT exportable.** `EXPORT MODEL` (or Vertex AI Model Registry / remote deployment) fails with `"400 Model TRANSFORM contains unsupported function for exporting."` `ML.IMPUTER`, the scalers, encoders, bucketizers, text functions, and image functions are all exportable — only these two crossing/expansion functions are the exception.
- **`ML.IMPUTER` correctly re-applies its training-time statistic at predict time**, even when the predict-time input is artificially forced to NULL — verified live in `functions/feature_engineering/feature_engineering.ipynb`.
- **`ML.TRANSFORM` (the table-valued function) passes through any input column not referenced anywhere in the model's `TRANSFORM` clause, unmodified, appended after the transform outputs** — useful for carrying an id/label through, but easy to mistake for the pipeline re-emitting a raw feature.
- **A downstream model trained on `ML.TRANSFORM` output, with no embedded `TRANSFORM` of its own, does not error when given raw (untransformed) data at `ML.PREDICT` time** — it silently predicts on wrong-scale values. Reproduced live: every row predicted the same class until raw input was re-wrapped in `ML.TRANSFORM` first (`models/transform_only/transform_only.ipynb`).
- **`ML.NORMALIZER(v, p)` is verified to equal `v / ML.LP_NORM(v, p)` element-wise** — `ML.LP_NORM` computes exactly the denominator `ML.NORMALIZER` uses internally (`functions/distance/distance.ipynb`).
- **`ML.ROBUST_SCALER`'s outlier robustness was verified directly against `ML.STANDARD_SCALER`** on an injected outlier — the standard scaler's mean/stddev shift substantially, the robust scaler's median/IQR barely move (`functions/scalers/scalers.ipynb`).
- **`ML.MIN_MAX_SCALER` caps prediction-time inputs to `[0, 1]`** when a serving value falls outside the training min/max — verified live via `CREATE MODEL` + `ML.TRANSFORM`.
- **Analytic functions cannot nest inside other analytic functions** (all the `OVER()`-requiring functions above), but scalar results (`ML.NORMALIZER`, `ML.IMPUTER` output, etc.) can be nested as arguments to other scalar functions — e.g. `ML.POLYNOMIAL_EXPAND(STRUCT(ML.IMPUTER(x, 'mean') OVER() AS x_imputed))` works because `ML.POLYNOMIAL_EXPAND` is scalar even though its argument came from an analytic call.
- **There is no `ML.TRANSPOSE` function** — a repo notebook of that name refers to using the `TRANSFORM` clause technique itself, not a callable function.
- **Image `STRUCT` outputs (`ML.DECODE_IMAGE` and downstream) can be large (up to 60 MB) and can fail to render in the BigQuery editor** — write results to a table rather than `SELECT`ing them directly for inspection.

## Canonical snippets

**1. Scaler used standalone:**
```sql
SELECT
  x,
  ML.STANDARD_SCALER(x) OVER() AS x_standard,
  ML.ROBUST_SCALER(x)   OVER() AS x_robust
FROM UNNEST([1.0, 2.0, 3.0, 4.0, 5.0, 100.0]) AS x;
```

**2. Encoder used standalone:**
```sql
SELECT
  category,
  ML.ONE_HOT_ENCODER(category, 'none', 10, 0) OVER() AS category_onehot,
  ML.LABEL_ENCODER(category, 10, 0)           OVER() AS category_label
FROM UNNEST(['a', 'a', 'b', 'c', 'c', 'c']) AS category;
```
(`frequency_threshold` set to `0` here to avoid the bucket-`0` collapse gotcha above on such a tiny example.)

**3. Functions inside a `CREATE MODEL ... TRANSFORM(...)` clause — usable both standalone and embedded:**
```sql
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.MODEL_NAME`
TRANSFORM (
  label_col,
  ML.IMPUTER(numeric_col, 'median') OVER() AS numeric_imputed,
  ML.STANDARD_SCALER(numeric_col)   OVER() AS numeric_scaled,
  ML.ONE_HOT_ENCODER(category_col)  OVER() AS category_encoded
)
OPTIONS (
  model_type = 'LOGISTIC_REG',
  input_label_cols = ['label_col']
) AS
SELECT * FROM `PROJECT_ID.DATASET.training_table`;
```
The scaler statistics and encoder vocabulary computed here are stored with the model and reapplied automatically by `ML.PREDICT`/`ML.EVALUATE` — no need to repeat the preprocessing at inference time.

## Go deeper

These functions are documented in full (option tables, syntax, defaults, BigFrames equivalents) directly in `RESOURCES.md` under **"Model-Free Functions"** — there is no dedicated per-function repo folder structure for these the way there is for model types. Full extracted notebook walkthroughs live in this skill's `narrative/` folder:

- [`narrative/scalers.md`](../narrative/scalers.md) (source: `functions/scalers/`) — all five scalers side by side on penguins, including the STDDEV_POP and MIN_MAX_SCALER capping proofs, ending in an embedded LOGISTIC_REG TRANSFORM
- [`narrative/bucketizing.md`](../narrative/bucketizing.md) (source: `functions/bucketizing/`) — ML.BUCKETIZE/ML.QUANTILE_BUCKETIZE/ML.HASH_BUCKETIZE together, including the exclude_boundaries proof
- [`narrative/encoding.md`](../narrative/encoding.md) (source: `functions/encoding/`) — all three encoders on penguins, including the frequency_threshold=5 default proof
- [`narrative/feature_engineering.md`](../narrative/feature_engineering.md) (source: `functions/feature_engineering/`) — ML.IMPUTER, ML.FEATURE_CROSS, ML.POLYNOMIAL_EXPAND on penguins, including the export-failure proof for the latter two
- [`narrative/text.md`](../narrative/text.md) (source: `functions/text/`) — ML.NGRAMS, ML.TF_IDF, ML.BAG_OF_WORDS on real thelook_ecommerce.products name tokens
- [`narrative/distance.md`](../narrative/distance.md) (source: `functions/distance/`) — ML.DISTANCE and ML.LP_NORM together, including the Jaccard-derivation and ML.NORMALIZER-equivalence proofs
- [`narrative/transform_only.md`](../narrative/transform_only.md) (source: `models/transform_only/`) — the fullest cross-function combination: ML.IMPUTER + scalers + ML.ONE_HOT_ENCODER feeding a downstream LOGISTIC_REG

There is no repo notebook exercising the image-preprocessing family (`ML.DECODE_IMAGE`/`ML.RESIZE_IMAGE`/`ML.CONVERT_IMAGE_TYPE`/`ML.CONVERT_COLOR_SPACE`) — those entries in RESOURCES.md are documentation-pattern only, unverified live in this repo.
