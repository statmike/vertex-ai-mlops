# Regression Models in BigQuery ML

## Options

| model_type | Use this when | Key differentiator vs. the others in this bucket |
|---|---|---|
| `LINEAR_REG` | You want a fast, interpretable baseline for a continuous target, or need lagged-feature-based forecasting. | Only type with linear coefficients (`ML.WEIGHTS`/`ML.ADVANCED_WEIGHTS`); trains in seconds via `NORMAL_EQUATION` on small/unregularized problems. |
| `BOOSTED_TREE_REGRESSOR` | Tabular data with nonlinear relationships and you want the strongest accuracy while keeping training fast and in-BigQuery. | Sequential boosting on residuals — verified strongest accuracy in this repo's head-to-head (`r2_score` 0.968 vs. linear regression's 0.875 on identical data); exports a real XGBoost artifact. |
| `RANDOM_FOREST_REGRESSOR` | You want a low-tuning bagged ensemble that resists overfitting, especially on data where boosting risks overfitting. | Single-iteration bagging ensemble (`num_parallel_tree` trees, no sequential boosting) — verified to *underperform* both boosting and even plain linear regression on small data (see gotchas). |
| `DNN_REGRESSOR` | You specifically want a neural net (e.g. for TensorFlow SavedModel export/serving) or need Integrated-Gradients attributions on relationships trees underfit. | Only feed-forward neural net here; needs careful `learn_rate` tuning on small data or it silently fails to converge — reach for it after trees/AutoML, not as a default. |
| `DNN_LINEAR_COMBINED_REGRESSOR` (wide-and-deep) | Large, sparse, high-cardinality categorical features where you need both memorization and generalization on a numeric target. | Wide linear + deep components jointly trained; `learn_rate`/`optimizer` are fixed literals only — NOT hyperparameter-tunable, unlike plain `DNN_REGRESSOR`, and converges to a lower `r2_score` than `DNN_REGRESSOR` on the same fix (~0.79 vs ~0.86 before HP tuning closes most of the gap). |
| `AUTOML_REGRESSOR` | You want the strongest possible tabular regression baseline without choosing/tuning an algorithm, and can afford hours of training time and real $ cost. | Automatic architecture search + internal tuning (`budget_hours` is the only lever); opaque (no `ML.EXPLAIN_PREDICT`/`ML.WEIGHTS`); requires ≥1,000 training rows. |

## Choosing among them

1. **Do you need coefficient-level interpretability, or is the relationship genuinely close to linear?** → `LINEAR_REG`. It's also the workhorse for regression-based (lagged-feature) forecasting.
2. **Is the label driven by nonlinear feature interactions on structured/tabular data, and do you want fast in-BigQuery iteration?** → `BOOSTED_TREE_REGRESSOR` first. In this repo's own apples-to-apples comparison on identical data it beat both `LINEAR_REG` and `RANDOM_FOREST_REGRESSOR` by a wide margin (`r2_score` 0.968 vs. 0.875 vs. 0.74).
3. **Worried a single boosted model is overfitting, or want a low-tuning bagged ensemble?** → `RANDOM_FOREST_REGRESSOR` — but verify it actually helps on your data; on `penguins` (333 rows) it was the weakest of the three techniques tested, not the strongest.
4. **Do you have large, sparse, high-cardinality categorical features where memorization and generalization both matter?** → `DNN_LINEAR_COMBINED_REGRESSOR` (wide-and-deep).
5. **Do you specifically want a neural net** (TensorFlow export, or nonlinearity trees underfit) **without the wide-and-deep sparse-feature case?** → `DNN_REGRESSOR`, only after ruling out boosted trees/AutoML as better defaults.
6. **Want zero algorithm/HP choice, can afford 1–72 hours + real dollar cost, and have ≥1,000 rows?** → `AUTOML_REGRESSOR`. Not for fast, iterative retraining loops.

## Gotchas verified in this repo

- **Query-cache staleness after retrain (applies to any model type):** re-running the identical `ML.EVALUATE`-style query as a separate job before/after `CREATE OR REPLACE MODEL` can silently return a stale `cacheHit: true` result — confirmed directly with identical roc_auc values pre/post retrain until `useQueryCache: false` was explicitly set. The `google_cloud_pipeline_components` `Bigquery*JobOp` components silently **drop** `useQueryCache: False` when passed as a Python bool — pass the **string** `'false'` instead.
- **`ONE_HOT_ENCODING` (the `LINEAR_REG` default) makes per-category `ML.WEIGHTS` unstable across retrains** because the design matrix becomes collinear with the intercept — verified by training the identical `LINEAR_REG` model twice on `penguins`/`body_mass_g`: one categorical weight swung from **+305/+353/+340 in one run to −39/−4/+8.6 in another** (different scale and sign), even though `ML.PREDICT`/`ML.EVALUATE` stayed effectively unchanged. Use `category_encoding_method = 'DUMMY_ENCODING'` whenever you plan to read `ML.WEIGHTS` — it pins one baseline category per feature to `weight: 0.0` and makes the rest stable, well-defined deltas.
- **`NORMAL_EQUATION` (auto-selected for small/unregularized `LINEAR_REG` problems) trains in a single pass** — `ML.TRAINING_INFO` returns exactly one row with `eval_loss = NULL`, i.e. no per-iteration eval curve like gradient descent produces.
- **`RANDOM_FOREST_REGRESSOR` genuinely underperformed on small data** — `r2_score ≈ 0.74` (≈0.76 best-tuned) on `penguins`/`body_mass_g` (333 rows) vs. `BOOSTED_TREE_REGRESSOR`'s ≈0.97 and `LINEAR_REG`'s ≈0.88 on identical data. Bagging's variance reduction needs enough data to pay off — don't assume it's the stronger ensemble by default.
- **`RANDOM_FOREST_*` retraining is genuinely non-deterministic** (default `subsample`/`colsample_bynode`=0.8, no exposed seed) — two identical retrains of the same regressor config produced visibly different tree structures, predictions, and `ML.GLOBAL_EXPLAIN` rankings, though `r2_score` stayed in a similar ~0.74–0.75 range. `BOOSTED_TREE_*` reproduced bit-for-bit in testing by contrast (no default subsampling).
- **`max_iterations` is a hard-invalid option for `RANDOM_FOREST_REGRESSOR`** — errors immediately if set (`Option(s) MAX_ITERATIONS are not supported for RANDOM_FOREST_* model training`); `ML.TRAINING_INFO` always shows exactly one iteration.
- **With default column subsampling (`colsample_bynode=0.8`) over a small feature set, some features can get *zero* `ML.FEATURE_IMPORTANCE`/`ML.GLOBAL_EXPLAIN`** — verified on the 6-feature `penguins` regressor (`island`, `culmen_length_mm` both zero, reproduced across two independent runs). A real bagging-variance effect, not a bug.
- **`BOOSTED_TREE_REGRESSOR` has a large fixed training-time floor** (~2.5–4.5 min even under 1,000 rows, vs. ~15s for `LINEAR_REG` on the same data) that doesn't shrink with fewer iterations or a slots reservation — but scales up substantially on real large data (19–40 min/model at ~1M rows / 771 features). Submitting multiple distinctly-named `CREATE MODEL` jobs concurrently finishes in roughly one model's training time, not the sum — this repo's `regression_based_forecasting` workflow trains 28 `BOOSTED_TREE_REGRESSOR` models (one per forecast horizon) this way.
- **`DNN_REGRESSOR`/`DNN_LINEAR_COMBINED_REGRESSOR` can silently fail to converge on small datasets** — on a 333-row set, default `learn_rate=0.001` + default `early_stop=TRUE` stopped training after only 2 iterations, producing `r2_score≈-27.5` (worse than predicting the mean) with no error. Feature scaling alone did **not** fix it (`r2_score` still ≈-27.4); raising `learn_rate` ~50x did (`r2_score≈0.86`). Always check `ML.TRAINING_INFO`'s iteration count on small data.
- **DNN training reproduces bit-for-bit across separate retrains of an identically-named model** (verified across three full runs) — but a *different* model name with the identical config can explore a completely different, worse trajectory. Don't expect a result to transfer across a rename/duplicate of the `CREATE MODEL` statement.
- **`DNN_LINEAR_COMBINED_REGRESSOR`'s `learn_rate`/`optimizer` are NOT hyperparameter-tunable** (`CREATE MODEL` errors immediately if given `HPARAM_RANGE`/`HPARAM_CANDIDATES`) — a real gap vs. plain `DNN_REGRESSOR`. If the default doesn't converge, you must set a fixed literal and can't search for a better one; HP tuning of the tunable options (e.g. `hidden_units`) can still close most of the resulting accuracy gap.
- **`AUTOML_REGRESSOR` requires ≥1,000 training rows** — fails immediately below that regardless of `budget_hours`; forced this project to switch off `penguins` (333 rows) to `bigquery-public-data.samples.natality`.
- **`AUTOML_REGRESSOR`'s zero-argument `ML.EVALUATE` returned `median_absolute_error` and `explained_variance` as exactly `0.0`** while `mean_absolute_error`/`mean_squared_error`/`r2_score` were genuine and self-consistent (`mean_squared_error` matched `ML.TRAINING_INFO`'s `eval_loss`). Pass explicit input data, and prefer `mean_squared_error`/`r2_score` over the zero-argument `median_absolute_error`/`explained_variance` fields for this model type.
- **AutoML wall-clock time badly exceeds `budget_hours`** — this project's own `budget_hours=1.0` regressor build took 2.25 hours; budget 2-3x the nominal figure.
- **Joining multiple models' `ML.PREDICT` outputs on raw feature columns instead of a stable row ID can silently fan out rows** (a 6,587-row split fanned out to 11,027) — add a synthetic `ROW_NUMBER()` ID before training and join on that; sanity-check row counts after any join.

## Canonical snippet

```sql
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.MODEL_NAME`
OPTIONS(
  model_type = 'LINEAR_REG',
  input_label_cols = ['label_col'],
  category_encoding_method = 'DUMMY_ENCODING',
  enable_global_explain = TRUE,
  data_split_method = 'AUTO_SPLIT'
) AS
SELECT feature1, feature2, ..., label_col
FROM `PROJECT_ID.DATASET.training_table`;
```

## Go deeper

Full extracted notebook walkthroughs live in this skill's `narrative/` folder — no need to be inside the source repo:

- [`narrative/linear_regression.md`](../narrative/linear_regression.md) (source: `models/linear_regression/`)
- [`narrative/boosted_tree_regressor.md`](../narrative/boosted_tree_regressor.md) (source: `models/boosted_tree_regressor/`)
- [`narrative/random_forest_regressor.md`](../narrative/random_forest_regressor.md) (source: `models/random_forest_regressor/`)
- [`narrative/dnn_regressor.md`](../narrative/dnn_regressor.md) (source: `models/dnn_regressor/`)
- [`narrative/wide_and_deep_regressor.md`](../narrative/wide_and_deep_regressor.md) (source: `models/wide_and_deep_regressor/`)
- [`narrative/automl_regressor.md`](../narrative/automl_regressor.md) (source: `models/automl_regressor/`)

Full syntax/options tables: see RESOURCES.md in the source repo (`bq-ml/RESOURCES.md`).
