# Classification Models in BigQuery ML

## Options

| model_type | Use this when | Key differentiator vs. the others in this bucket |
|---|---|---|
| `LOGISTIC_REG` | You want a fast, interpretable baseline with calibrated class probabilities and (optionally) statistical inference (p-values, standard errors). | Only type with linear coefficients (`ML.WEIGHTS`/`ML.ADVANCED_WEIGHTS`) and true p-value inference; trains in seconds; assumes mostly-linear feature/label relationships. |
| `BOOSTED_TREE_CLASSIFIER` | Tabular data, nonlinear feature interactions, and you want the strongest accuracy while keeping training in-BigQuery and fast to iterate. | Sequential boosting (each tree fits prior residuals) — typically the best accuracy/cost tradeoff of the tree types; exports a real XGBoost `.bst` artifact. |
| `RANDOM_FOREST_CLASSIFIER` | You want a bagging ensemble that resists overfitting with minimal tuning, or a variance-reduction alternative when boosting overfits. | Trains a single iteration of `num_parallel_tree` independently-bagged trees (no sequential boosting); `max_iterations` isn't even a valid option — verified to hard-error if set. |
| `DNN_CLASSIFIER` | You specifically want a neural net (e.g. for TensorFlow export/serving) or need Integrated-Gradients attributions on nonlinear relationships trees don't capture. | Only feed-forward neural net in this bucket; needs deliberate `learn_rate` tuning on small data (see gotchas) — reach for it after trees/AutoML, not before. |
| `DNN_LINEAR_COMBINED_CLASSIFIER` (wide-and-deep) | Large, sparse, high-cardinality categorical features (ranking/recommendation-style problems) where you need both memorization of specific combinations and generalization. | Jointly trains a wide linear component + deep component; `learn_rate`/`optimizer` are fixed literals only — verified NOT hyperparameter-tunable, unlike plain `DNN_CLASSIFIER`. |
| `AUTOML_CLASSIFIER` | You want the strongest possible tabular baseline without choosing/tuning an algorithm yourself, and can afford hours of training time and $ cost. | Only type with automatic architecture search + internal HP tuning (`budget_hours` is the only lever); opaque — no `ML.EXPLAIN_PREDICT`/`ML.WEIGHTS`, only model-level `ML.GLOBAL_EXPLAIN`; requires ≥1,000 training rows. |

## Choosing among them

1. **Do you need coefficient-level interpretability or formal statistical inference (p-values)?** → `LOGISTIC_REG`. Nothing else in this bucket exposes linear weights or p-values.
2. **Is the label prediction dominated by nonlinear feature interactions on structured/tabular data, and do you want fast in-BigQuery iteration?** → `BOOSTED_TREE_CLASSIFIER` first. It's the workhorse: strong accuracy, exportable, built-in local+global explainability.
3. **Is your dataset small/noisy and you're worried about a single boosted model overfitting, or do you want a low-tuning bagged ensemble?** → `RANDOM_FOREST_CLASSIFIER`. But don't assume it beats boosting — on small data it has measurably underperformed boosted trees in this repo (see gotchas).
4. **Do you have large, sparse, high-cardinality categorical features** (many distinct IDs, ranking/recommendation-shaped data) **where you need both memorization and generalization?** → `DNN_LINEAR_COMBINED_CLASSIFIER` (wide-and-deep).
5. **Do you specifically want a neural net** (e.g. because you need a TensorFlow SavedModel artifact, or nonlinear relationships trees underfit) **but don't have the wide-and-deep sparse-feature case?** → `DNN_CLASSIFIER`. Otherwise prefer boosted trees or AutoML first — this doc's own guidance is "reach for DNN when you specifically want a neural net," not as a default.
6. **Do you want zero algorithm/hyperparameter choice, are OK trading 1–72 hours of training time and real dollar cost for the strongest possible result, and have ≥1,000 training rows?** → `AUTOML_CLASSIFIER`. If you need fast, iterative, in-BigQuery retraining, none of the AutoML properties apply — go back to boosted trees/DNN/logistic regression instead.

## Gotchas verified in this repo

- **Query-cache staleness after retrain (applies to any model type, hits classification pipelines hardest):** re-running the identical `ML.EVALUATE`-reading query as a separate job before/after `CREATE OR REPLACE MODEL` can return a cached, stale result (`cacheHit: true`) with bit-for-bit identical numbers even though the model changed — confirmed directly (`roc_auc` stuck at `0.7688881118881119` until `useQueryCache: false` was set, then correctly returned `0.729021978021978`). The `google_cloud_pipeline_components` prebuilt `Bigquery*JobOp` components silently **drop** `useQueryCache: False` if passed as a Python bool (falsy values get stripped by the library's own JSON cleanup) — pass the **string** `'false'`, not the Python bool, to actually disable caching in those components.
- **`RANDOM_FOREST_*` training is genuinely non-deterministic run-to-run** (default `subsample`/`colsample_bynode` = 0.8, no exposed seed) — two identical retrains produced visibly different tree structures, predictions, and `ML.GLOBAL_EXPLAIN` rankings, though `r2_score` stayed in a similar range. `BOOSTED_TREE_*`, by contrast, reproduced bit-for-bit across separate runs in testing (no default subsampling).
- **`RANDOM_FOREST_*` underperformed boosting and even a GLM on small data** — verified on `penguins` (333 rows, regression side, same dynamic applies to the classifier): random forest reached only `r2_score ≈ 0.74–0.76` vs. boosted trees' `≈ 0.97`. Don't assume bagging is the stronger ensemble by default; it needs enough data to pay off.
- **`max_iterations` is a hard-invalid option for `RANDOM_FOREST_CLASSIFIER`** — `CREATE MODEL` errors immediately (`Option(s) MAX_ITERATIONS are not supported for RANDOM_FOREST_* model training`), confirming it's a true single-pass API guarantee, not just convention.
- **`RANDOM_FOREST_*` default trees are too dense to visualize** — a default `num_parallel_tree=50`/`max_tree_depth=6` tree had 2,435 dump lines / depth 15; `xgboost.plot_tree()` fails even as SVG. Train a small dedicated illustrative forest (e.g. `num_parallel_tree=10`, `max_tree_depth=3`) for diagrams only.
- **`BOOSTED_TREE_*` has a large fixed training-time floor** (~2.5–4.5 minutes even on <1,000-row tables, vs. ~15s for `LINEAR_REG`/`LOGISTIC_REG` on the same data) that does not shrink with fewer iterations or a slots reservation — but it's a floor, not a ceiling: on a ~1M-row, 771-feature table (including two `ARRAY<FLOAT64>` embedding columns), training took 19–40 minutes per model. Submitting multiple distinctly-named `CREATE MODEL` jobs concurrently finishes in roughly the slowest single model's time, not the sum — use this to parallelize many small classifier trainings.
- **`ARRAY<FLOAT64>` embedding columns can be passed directly as `BOOSTED_TREE_CLASSIFIER` features** — no need to unnest into `col_0, col_1, ...`; verified at 256/512 dimensions, and `ML.FEATURE_INFO` reports a `dimension` value for them.
- **`DNN_CLASSIFIER`/`DNN_LINEAR_COMBINED_CLASSIFIER` can silently fail to converge on small datasets with default `learn_rate=0.001` + default `early_stop=TRUE`**, stopping after only 1-2 iterations with no error — on the regression analogue this produced `r2_score≈-27.5` (far worse than predicting the mean); feature scaling alone did **not** fix it, but raising `learn_rate` ~50x did. Always check `ML.TRAINING_INFO`'s iteration count on small data before trusting the metrics.
- **`DNN_LINEAR_COMBINED_CLASSIFIER`'s `learn_rate` and `optimizer` are NOT hyperparameter-tunable** — `CREATE MODEL` errors immediately (`"Unsupported hyperparameter learn_rate for model_type DNN_LINEAR_COMBINED_CLASSIFIER"`) if you pass `HPARAM_RANGE`/`HPARAM_CANDIDATES`, unlike plain `DNN_CLASSIFIER` where both are tunable. If the default doesn't converge, you must set a fixed literal — you can't search for a better value.
- **`AUTOML_CLASSIFIER` requires ≥1,000 training rows** — `CREATE MODEL` fails immediately below that threshold regardless of `budget_hours`; not called out in the official reference. Small demo datasets (e.g. `penguins`, ~333 rows) can't train AutoML at all.
- **`AUTOML_CLASSIFIER`'s zero-argument `ML.CONFUSION_MATRIX` fails consistently** with a generic, seemingly-transient error (`Error: 21631273`) that is actually NOT transient — reproduced on 100+ attempts, and the client library's retry logic makes calls appear to hang. `ML.EVALUATE`/`ML.ROC_CURVE`'s zero-argument forms work fine on the same model. Always pass explicit input data to `ML.CONFUSION_MATRIX` for AutoML models.
- **`AUTOML_CLASSIFIER`'s zero-argument `ML.EVALUATE` returns an `accuracy` that doesn't reconcile with the model's own confusion matrix** (`accuracy=0.5` returned while the model's own threshold=0.5 confusion-matrix row showed `accuracy=0.844`) — pass explicit data (`ML.EVALUATE(MODEL ..., (SELECT ...))`) for trustworthy metrics, or prefer threshold-independent `roc_auc`/`log_loss`.
- **AutoML wall-clock time badly exceeds `budget_hours`** — this repo's own from-scratch build with `budget_hours=1.0` took 2.63 hours; budget 2-3x the nominal budget for planning purposes.
- **Joining multiple models' `ML.PREDICT` outputs back together (e.g. for ensembling/stacking classifiers) can silently fan out rows if joined on raw feature columns instead of a stable ID** — a 6,587-row split fanned out to 11,027 rows because different source rows shared identical feature values. Add a synthetic `ROW_NUMBER()` row ID before training any model and join on that; sanity-check joined row counts.

## Canonical snippet

```sql
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.MODEL_NAME`
OPTIONS(
  model_type = 'LOGISTIC_REG',
  input_label_cols = ['label_col'],
  auto_class_weights = TRUE,
  category_encoding_method = 'DUMMY_ENCODING',
  enable_global_explain = TRUE,
  data_split_method = 'AUTO_SPLIT'
) AS
SELECT feature1, feature2, ..., label_col
FROM `PROJECT_ID.DATASET.training_table`;
```

## Go deeper

Full extracted notebook walkthroughs live in this skill's `narrative/` folder — no need to be inside the source repo:

- [`narrative/logistic_regression.md`](../narrative/logistic_regression.md) (source: `models/logistic_regression/`)
- [`narrative/boosted_tree_classifier.md`](../narrative/boosted_tree_classifier.md) (source: `models/boosted_tree_classifier/`)
- [`narrative/random_forest_classifier.md`](../narrative/random_forest_classifier.md) (source: `models/random_forest_classifier/`)
- [`narrative/dnn_classifier.md`](../narrative/dnn_classifier.md) (source: `models/dnn_classifier/`)
- [`narrative/wide_and_deep_classifier.md`](../narrative/wide_and_deep_classifier.md) (source: `models/wide_and_deep_classifier/`)
- [`narrative/automl_classifier.md`](../narrative/automl_classifier.md) (source: `models/automl_classifier/`)

Full syntax/options tables: see RESOURCES.md in the source repo (`bq-ml/RESOURCES.md`).
