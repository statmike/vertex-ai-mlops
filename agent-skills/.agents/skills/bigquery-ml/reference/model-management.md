# Model Management, Deployment & Monitoring in BigQuery ML

## Options

| Capability | What it's for | Use this when |
|---|---|---|
| `TRANSFORM_ONLY` | Saves a reusable preprocessing pipeline (scalers, encoders, imputers) as a model object with no estimator | You want a feature-store-style, reusable transform decoupled from any one model, applied via `ML.TRANSFORM` |
| Imported models (`TENSORFLOW`, `TENSORFLOW_LITE`, `ONNX`, `XGBOOST`) | Brings a model trained outside BigQuery into BigQuery's own Inference Engine for native `ML.PREDICT` | You already have a trained artifact (SavedModel, `.tflite`, `.onnx`, XGBoost Booster) under the size limit and want SQL-native serving with no external endpoint |
| `REMOTE` model (custom Vertex AI endpoint) | Registers an external Vertex AI prediction endpoint so `ML.PREDICT` can call it from SQL | The model is too large to import, needs GPU/custom-container serving, or is already deployed and you want one SQL inference surface |
| `EXPORT MODEL` | Copies a BQML-trained model out to a GCS folder (TF SavedModel or XGBoost Booster) for serving elsewhere | You trained in BQML and need the artifact outside BigQuery (container, edge, Vertex AI endpoint, handoff to another team) |
| Data validation/drift functions (`ML.DESCRIBE_DATA`, `ML.VALIDATE_DATA_SKEW`, `ML.VALIDATE_DATA_DRIFT`, `ML.TFDV_DESCRIBE`, `ML.TFDV_VALIDATE`) | Profiles data and detects training/serving skew or drift between datasets | You need to monitor a model or pipeline in production for distribution shift, or sanity-check a dataset before/after training |

## Choosing among them

**"I already have a model trained outside BigQuery"** → Imported model. Pick the sub-type by source framework:
- Trained in **TensorFlow/Keras** → `TENSORFLOW` (SavedModel). Gives you `ML.EXPLAIN_PREDICT` per the docs, but this repo verified live that it's actually rejected (`"TENSORFLOW model is unsupported in ml.explain_predict."`) on a small Keras classifier — don't rely on that capability without testing your own model first.
- Need an **edge/quantized** TF artifact, or a TF Text preprocessing graph → `TENSORFLOW_LITE`. `ML.PREDICT` only, no `ML.EXPLAIN_PREDICT`.
- Trained in **scikit-learn, PyTorch, or anything convertible to ONNX** → `ONNX`. Best fit for numeric/tabular or pre-tokenized ARRAY inputs; framework-agnostic interchange format.
- Trained in **XGBoost** natively → `XGBOOST`. The only imported type with a feature-attribution function (`ML.FEATURE_IMPORTANCE`), and the only one with an explicit `INPUT`/`OUTPUT` schema clause.

**"I need to call an existing Vertex AI endpoint from SQL"** → `REMOTE` model with `REMOTE WITH CONNECTION`. This is the only path when the model is too big to import (imported types cap at 250–450 MB) or needs GPU/custom-container serving. It's also framework-agnostic on the far end — any model registered to Vertex AI Model Registry can back it, regardless of how it was trained.

**"I trained in BQML and need the artifact elsewhere"** → `EXPORT MODEL`. Produces a TF SavedModel or XGBoost Booster in GCS, with baked-in preprocessing (no manual re-transform needed at inference). Not available for remote models, ARIMA_PLUS/time-series models, or ONNX/TFLite-imported models.

**"I just want a saved, reusable preprocessing pipeline, no model"** → `TRANSFORM_ONLY`. No estimator, no `ML.PREDICT`; consumed via `ML.TRANSFORM`. Guarantees frozen training-time statistics so training/serving skew on the *transform* itself can't happen — but the transform must be explicitly reapplied before scoring a downstream model, since it isn't embedded.

**"I need to detect training/serving skew or drift over time"** → the monitoring functions, distinguished by what they compare:
- `ML.VALIDATE_DATA_SKEW` — compares new/serving data against **statistics stored inside a trained model** (no original training data needed). Use to catch serving inputs diverging from what a specific model was trained on.
- `ML.VALIDATE_DATA_DRIFT` — compares **two arbitrary datasets** (e.g., last week vs. this week of serving data); the `MODEL` argument is optional and only adds a Vertex AI visualization link. Use for drift monitoring independent of any one model, or as a manual skew check without stored training stats.
- `ML.TFDV_DESCRIBE` / `ML.TFDV_VALIDATE` — the TFDV-compatible, proto-based variants of the same two ideas (describe → stats proto; validate → anomalies proto), for teams already integrated with `tensorflow-data-validation`/TFX. Functionally equivalent numbers to the basic tier, just packaged as protos instead of tabular rows.
- `ML.DESCRIBE_DATA` — plain descriptive statistics (no comparison), typically the first step before running skew/drift checks.

## Gotchas verified in this repo

- **Imported models need no connection for `ML.PREDICT`** — BigQuery reads the GCS model file using the calling user's own credentials. A Cloud Resource connection is only required if you later serve the imported model against an **object table**, and that path is reservation/capacity pricing only (no on-demand).
- **`REMOTE` models always need a `CLOUD_RESOURCE` connection**, and its auto-provisioned service account needs `roles/aiplatform.user`. IAM propagation is unreliable — verified live to take **over two minutes** in one case despite the grant itself reporting success immediately. Retry `CREATE MODEL` in a loop (several attempts, ~20s apart) rather than sleeping once.
- **`REMOTE` connection must be co-located with the dataset** (e.g., `US` dataset needs a `US` connection); one connection can be reused across multiple remote models.
- **`REMOTE` only supports shared public Vertex AI endpoints** — dedicated public, Private Service Connect, and private endpoints are not supported. Only `ML.PREDICT` works; no `ML.EVALUATE`/weights/explainability lifecycle functions apply since nothing is trained in BigQuery.
- **`model_registry='VERTEX_AI'` is not a safe shortcut to a working `REMOTE` endpoint**, at least for `LOGISTIC_REG`: it bakes in an unconditional Sampled-Shapley `explanationSpec`, and deploying that model to an endpoint fails with an `InvalidArgument` explanation-preprocessing error (confirmed open, "not planned" upstream — vertex-ai-samples#2723). The manual `EXPORT MODEL` → `aiplatform.Model.upload()` → deploy path is the reliable one.
- **XGBoost import/export version mismatch runs in both directions**: the importer only accepts Booster files saved by **XGBoost ≤ 1.5.1** (a modern 2.x/3.x-saved booster fails with `"XGBoost model version newer than 1.5.1 is not supported."`); conversely, `EXPORT MODEL` on `BOOSTED_TREE_*`/`RANDOM_FOREST_*` emits **XGBoost 0.82's legacy binary format**, which modern `xgboost` (2.0+) cannot load (`Check failed: str[0] == '{'`) — pin `xgboost==1.7.6` to load/visualize an exported booster locally, and `xgboost==1.5.1` (with `numpy<2`) to train a booster BigQuery will accept on import.
- **`EXPORT MODEL` strips feature names** — the loaded booster's `feature_names` comes back `None` (generic `f0`, `f1`, ...); reassign manually from the training query's non-label column order (verified 1:1, `num_features()` matches raw column count with no categorical expansion).
- **ONNX opset/IR version must match ONNX Runtime 1.12.0** exactly, not just "be recent" — a default `skl2onnx` conversion emits IR version 10 / opset 22, both too new; this repo pins `target_opset=13` and sets `ir_version=8` explicitly. Also, sklearn classifiers need `zipmap=False` at conversion time or import fails with `unsupported ONNX type: ONNX_TYPE_SEQUENCE`.
- **`ML.PREDICT` on a downstream model does not validate that inputs went through the matching `TRANSFORM_ONLY` pipeline** — feeding raw (untransformed) data to a model trained on `ML.TRANSFORM` output does not error, it silently mispredicts (every row predicted the same class in a live test until inputs were re-wrapped in `ML.TRANSFORM`).
- **Sampling method matters as much as the skew/drift function call**: `SELECT ... LIMIT N` without `ORDER BY` on a non-randomly-ordered table can manufacture a false skew alarm — a `LIMIT 5000` grab from the model's own training table flagged `education_num` as anomalous (Jensen-Shannon ~0.65 vs. 0.3 threshold); switching to `WHERE RAND() < p` for a true random sample dropped divergence to near-zero. None of the five monitoring functions require a Cloud resource connection; the optional `MODEL` argument only adds a Vertex AI visualization link and requires Vertex AI Model Registry registration — a plain `CREATE MODEL`-trained model does not qualify, which is why this repo's drift-check pipelines use the 3-argument form of `ML.VALIDATE_DATA_DRIFT` with no `MODEL`.
- **`categorical_metric_type` choice changes which columns get flagged**, not just the score: `L_INFTY` vs. `JENSEN_SHANNON_DIVERGENCE` at the same threshold flagged genuinely different columns in a live comparison (`race`/`sex` dropped out under JS while `L_INFTY` flagged all three).

## Canonical snippet

```sql
-- 1. One-time: Cloud Resource connection + IAM grant (outside SQL, then verify before proceeding)
--    bq mk --connection --connection_type=CLOUD_RESOURCE --location=US my_conn
--    gcloud projects add-iam-policy-binding PROJECT_ID \
--      --member="serviceAccount:<connection_service_account>" --role="roles/aiplatform.user"

-- 2. Register the Vertex AI endpoint as a REMOTE model
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.MODEL_NAME`
INPUT  (feature_a FLOAT64, feature_b STRING)
OUTPUT (predicted_label STRING, predicted_score FLOAT64)
REMOTE WITH CONNECTION `PROJECT_ID.US.my_conn`
OPTIONS(
  ENDPOINT = 'https://us-central1-aiplatform.googleapis.com/v1/projects/PROJECT_ID/locations/us-central1/endpoints/ENDPOINT_ID'
);

-- 3. Score with ML.PREDICT (remote_model_status reports per-row call errors)
SELECT *
FROM ML.PREDICT(
  MODEL `PROJECT_ID.DATASET.MODEL_NAME`,
  (SELECT feature_a, feature_b FROM `PROJECT_ID.DATASET.SERVING_TABLE`)
);
```

## Go deeper

Full extracted notebook walkthroughs live in this skill's `narrative/` folder — no need to be inside the source repo:

- [`narrative/transform_only.md`](../narrative/transform_only.md) (source: `models/transform_only/`) — chained ML.IMPUTER/scalers/ML.ONE_HOT_ENCODER feeding a downstream LOGISTIC_REG with no embedded TRANSFORM
- [`narrative/imported.md`](../narrative/imported.md) (source: `models/imported/`) — all four imported types (TENSORFLOW, TENSORFLOW_LITE, ONNX, XGBOOST) built and scored
- [`narrative/remote.md`](../narrative/remote.md) (source: `models/remote/`) — full round trip: LOGISTIC_REG → EXPORT MODEL → Vertex AI deploy → CLOUD_RESOURCE connection → REMOTE model → ML.PREDICT
- [`narrative/export.md`](../narrative/export.md) (source: `models/export/`) — EXPORT MODEL covering both TF SavedModel and XGBoost Booster formats, run locally outside BigQuery
- [`narrative/data_quality.md`](../narrative/data_quality.md) (source: `functions/data_quality/`) — all five data validation/drift functions on census_adult_income; also used as the conditional-retrain trigger in pipelines/

Full RESOURCES.md documentation for the data validation functions is under the "Model Management & Monitoring" section (`bq-ml/RESOURCES.md`).
