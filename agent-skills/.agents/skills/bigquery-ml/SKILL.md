---
name: bigquery-ml
description: Use when training, evaluating, deploying, or monitoring a machine learning model directly in BigQuery with SQL (CREATE MODEL and ML.* functions) — picking a model type, debugging CREATE MODEL options, choosing a preprocessing function, or operationalizing a model with a scheduled retrain pipeline. Covers classification, regression, clustering/dimensionality-reduction, forecasting, recommendations, driver analysis, model import/export/deployment, model-free preprocessing functions, and 8 production orchestration approaches.
---

# BigQuery ML

BigQuery ML trains and serves models with SQL: `CREATE MODEL` picks an algorithm via `model_type`, then `ML.*` functions evaluate/predict/explain/monitor it — no data leaves BigQuery, no separate training infrastructure.

This skill packages a verified, field-tested reference distilled from a project that built and live-tested every model type, model-free function, workflow, and pipeline approach listed below — not general BigQuery ML knowledge, but specific, evidence-backed gotchas (exact error messages, exact metric swings across retrains, exact option interactions) found by actually running this in BigQuery.

## Decision tree

1. **Do you have a labeled target to predict?**
   - Categorical label → see `reference/classification.md`
   - Continuous numeric label → see `reference/regression.md`
   - No label at all (clustering, dimensionality reduction, embeddings, recommendations, time-series forecasting, or "why did this metric change") → see `reference/unsupervised-and-specialized.md`
2. **Are you managing, deploying, or monitoring an existing model** (importing one trained elsewhere, calling a Vertex AI endpoint from SQL, exporting a BQML model out, or checking training/serving skew and drift) → see `reference/model-management.md`
3. **Are you doing feature engineering / preprocessing independent of any model type** (scaling, bucketizing, encoding, imputation, text/image prep) → see `reference/preprocessing-functions.md`
4. **Are you composing a real end-to-end task, or operationalizing one on a schedule** (drift-check → conditional retrain → score) → see `reference/workflows-and-pipelines.md`

If the ask is ambiguous between BigQuery ML (trained models) and BigQuery's generative AI functions (`AI.GENERATE`, `AI.FORECAST`, `AI.CLASSIFY`, etc. — the sibling `bigquery-ai-functions` skill), and you have access to it, consult the `choosing-a-bigquery-ai-approach` skill first — it triages between the two and encodes the specific head-to-head comparisons (e.g. `ARIMA_PLUS` vs. `AI.FORECAST`) already worked out in this project. If that skill isn't available, ask the user directly: do they need training-time control (custom holidays/regressors, hierarchical reconciliation, interpretable coefficients, scheduled retraining) or a fast, zero-setup answer?

## Cross-cutting gotchas (apply across model types)

- **Query-cache staleness after `CREATE OR REPLACE MODEL`**: re-running the same `ML.EVALUATE`-style query as a separate job right after a retrain can return a stale, cached result. The fix (`useQueryCache: false`) is not one value everywhere — it's per-library. A real Python/JSON `False` works in the `google-cloud-bigquery` client, Cloud Workflows YAML, and `BigQueryInsertJobOperator` (Airflow). The `google_cloud_pipeline_components` prebuilt KFP ops silently **drop** a Python `False` (their own JSON-cleanup logic strips falsy values) — pass the **string** `'false'` there instead. Verify via `INFORMATION_SCHEMA.JOBS_BY_PROJECT` rather than assuming either behavior for a library you haven't tested.
- **Non-determinism is real and model-type-specific, not paranoia**: `KMEANS` and `RANDOM_FOREST_*` retrain differently every time (no exposed seed / no deterministic init guarantee) even on identical data and options — don't treat a single before/after comparison as evidence of a feature's effect. `BOOSTED_TREE_*`, `PCA`, and `DNN_*` (same model name) reproduce far more consistently. When you need a stable narrative, key it to observed characteristics (metric ranges, cluster profiles), never to a specific non-deterministic cluster/component ID.
- **`ONE_HOT_ENCODING` (the GLM default) makes per-category `ML.WEIGHTS` unstable across retrains** due to collinearity with the intercept — use `category_encoding_method = 'DUMMY_ENCODING'` whenever you plan to read `ML.WEIGHTS`/`ML.ADVANCED_WEIGHTS`.
- **Encoders and text functions default to `frequency_threshold = 5`** (`ML.ONE_HOT_ENCODER`, `ML.LABEL_ENCODER`, `ML.MULTI_HOT_ENCODER`, `ML.TF_IDF`, `ML.BAG_OF_WORDS`) — any category/term appearing fewer than 5 times silently collapses into the unknown bucket. Lower it explicitly if rare-but-meaningful categories matter.
- **`MATRIX_FACTORIZATION` is the one model type that cannot train under on-demand pricing** — it needs an `ENTERPRISE`+ edition reservation. Always use an autoscale reservation (pay-per-second), never a flat capacity commitment, and tear it down after training.
- **Joining separate models' `ML.PREDICT` outputs on raw feature columns (instead of a synthetic row ID) can silently fan out rows** when different source rows share identical feature values — add a `ROW_NUMBER()` id before training and join on that.
- **Validate live before writing to a notebook**: option interactions in BigQuery ML frequently don't match official docs (see the model-specific gotcha files for exact error strings) — run the actual `CREATE MODEL`/`ML.*` call against real BigQuery before documenting expected behavior.
- **Real paid infrastructure (reservations, Composer environments, endpoints) should always be torn down for real**, not left as a reader's exercise — see `reference/workflows-and-pipelines.md` for the specific cleanup gotchas (e.g. deleting a Composer environment does not delete its GCS bucket).

## Reference files

- `reference/classification.md` — LOGISTIC_REG, BOOSTED_TREE_CLASSIFIER, RANDOM_FOREST_CLASSIFIER, DNN_CLASSIFIER, DNN_LINEAR_COMBINED_CLASSIFIER, AUTOML_CLASSIFIER
- `reference/regression.md` — LINEAR_REG, BOOSTED_TREE_REGRESSOR, RANDOM_FOREST_REGRESSOR, DNN_REGRESSOR, DNN_LINEAR_COMBINED_REGRESSOR, AUTOML_REGRESSOR
- `reference/unsupervised-and-specialized.md` — KMEANS, PCA, AUTOENCODER, MATRIX_FACTORIZATION, CONTRIBUTION_ANALYSIS, ARIMA_PLUS, ARIMA_PLUS_XREG
- `reference/model-management.md` — TRANSFORM_ONLY, imported models (TF/TFLite/ONNX/XGBoost), REMOTE models, EXPORT MODEL, data validation/drift functions
- `reference/preprocessing-functions.md` — scalers, bucketizers, encoders, feature engineering, text, distance, image preprocessing
- `reference/workflows-and-pipelines.md` — composing a workflow, then choosing among 8 orchestration approaches to operationalize it

## Go deeper (only resolves inside this repo)

If you're working inside the `vertex-ai-mlops` repo, every reference file's "Go deeper" pointers resolve to real, tested notebooks/`.sql` files under `models/`, `functions/`, `workflows/`, and `pipelines/`, plus the full syntax/options tables in `RESOURCES.md`. This skill is self-contained without that repo — the reference files above already carry the distilled decision guidance and verified gotchas — but the repo is where the full progressive lifecycle and raw evidence live.
