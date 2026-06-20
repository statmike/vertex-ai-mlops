<!--
Landing-page map for the bq-ml project. Tables of models/functions/workflows/pipelines,
a "how it fits together" diagram, and the project structure tree. Keep tables in sync
with the content folders and with RESOURCES.md / PLANS.md (see the audit procedure in PLANS.md).
-->

# BigQuery ML

Train and run machine learning models entirely in SQL with BigQuery ML — `CREATE MODEL` plus the `ML.*` functions. No data movement, no separate training infrastructure: the model lives in your dataset and you evaluate, predict, and explain it with SQL.

This is the sibling project to [**BigQuery AI Functions**](../bq-ai-functions/) (Gemini-in-SQL). Where that project is organized per function, BigQuery ML is organized around the **model lifecycle**, so the unit of content is the **model type**.

## Start Here

| Resource | What it is |
|----------|------------|
| [Interactive Overview](overview.ipynb) | A short runnable tour — one example per category |
| [Setup Reference](setup/) | Datasets, connections (for remote/imported/export), IAM, the CREATE MODEL deep dive, quotas, BigFrames |
| [Detailed Reference](RESOURCES.md) | Syntax, options, outputs, and limitations for CREATE MODEL and every `ML.*` function |
| [Project Plan](PLANS.md) | The operating manual: conventions, templates, backlog, and audit procedure |

New to BigQuery ML? Start with the [**Logistic Regression**](models/logistic_regression/) model — it walks the entire lifecycle end to end and is the template every other model follows.

## Models

Per-model-type deep dives covering the full lifecycle (create → evaluate → predict → explain → tune).

| Model | Type | Lifecycle entry | Status | What it does |
|-------|------|-----------------|--------|--------------|
| [Logistic Regression](models/logistic_regression/) | `LOGISTIC_REG` | ML.PREDICT | GA | Binary classification with feature attributions and hyperparameter tuning |

*More model types are planned — see the backlog in [PLANS.md](PLANS.md) (linear regression, boosted trees, random forest, DNN, K-means, PCA, matrix factorization, ARIMA_PLUS, autoencoder, plus imported / remote / exported model categories).*

## Functions

Model-free `ML.*` utilities that transform data directly (no model required).

| Function | Category | Status | What it does |
|----------|----------|--------|--------------|
| *(planned)* | Preprocessing / transforms / distance / text | — | See [PLANS.md](PLANS.md) Phase 6 (ML.STANDARD_SCALER, ML.BUCKETIZE, ML.FEATURE_CROSS, ML.DISTANCE, ML.NGRAMS, ML.TF_IDF, …) |

`ML.STANDARD_SCALER` is demonstrated inline in the [Logistic Regression](models/logistic_regression/) notebook (the `TRANSFORM` clause).

## Workflows

End-to-end SQL logic composing preprocessing + a model lifecycle into a real task.

| Workflow | Models / Functions used | What it does |
|----------|-------------------------|--------------|
| *(planned)* | — | See [PLANS.md](PLANS.md) Phase 7 (classification, segmentation, forecasting, recommendation) |

## Pipelines

Operationalizing the workflows — MLOps on BigQuery. Same logic, scheduled and orchestrated.

| Pipeline | Approach | What it shows |
|----------|----------|---------------|
| *(planned)* | SQL scripting · scheduled queries · Composer/Airflow · Vertex KFP · Airflow+KFP | See [PLANS.md](PLANS.md) Phase 8 |

---

## How BigQuery ML Fits Together

```
   DATA (a BigQuery table / query)
     │
     │   model-free ML.* functions can preprocess features
     │   (ML.STANDARD_SCALER, ML.BUCKETIZE, ML.FEATURE_CROSS, ...)
     │   — standalone, or inside a TRANSFORM clause
     ▼
┌──────────────────────────────┐
│        CREATE MODEL          │   model_type = LOGISTIC_REG | LINEAR_REG |
│   (trains + stores a model)  │   KMEANS | BOOSTED_TREE_* | ARIMA_PLUS | ...
│   + optional TRANSFORM       │   + optional NUM_TRIALS (hyperparameter tuning)
└──────────────┬───────────────┘
               │
   ┌───────────┼───────────────┬─────────────────┬──────────────────┐
   ▼           ▼               ▼                 ▼                  ▼
ML.EVALUATE  ML.PREDICT    ML.EXPLAIN_PREDICT  ML.GLOBAL_EXPLAIN   ML.TRIAL_INFO
(metrics)    ML.FORECAST   (per-row            (global feature     (tuning trials)
ML.CONFUSION ML.RECOMMEND   attributions)       importance)
ML.ROC_CURVE                                   ML.FEATURE_INFO / ML.TRAINING_INFO

   Model management: EXPORT MODEL (→ GCS) · imported models (TF/ONNX/XGBoost)
                     · remote models (REMOTE WITH CONNECTION → Vertex AI)

   Pipelines wrap all of the above for scheduled retrain + scoring
   (SQL scripting · scheduled queries · Composer/Airflow · Vertex KFP)
```

**Key distinctions:**
- **`CREATE MODEL`** trains a model object stored in your dataset; `model_type` picks the algorithm.
- **Lifecycle `ML.*` functions** are table-valued — use them in `FROM`, passing `MODEL \`...\`` and (optionally) input data.
- **Model-free `ML.*` functions** transform data with no model — use standalone or inside `TRANSFORM`.
- **Most model types need no connection.** Only remote (Vertex endpoints), imported (GCS artifacts), and `EXPORT MODEL` require one. See [Setup](setup/).
- **`enable_global_explain = TRUE`** must be set at training time to use `ML.GLOBAL_EXPLAIN` later.

---

## Project Structure

```
bq-ml/
├── README.md               ◄ You are here
├── RESOURCES.md            ◄ Detailed CREATE MODEL + ML.* reference
├── PLANS.md                ◄ Operating manual: conventions, templates, backlog, audit
├── overview.ipynb          ◄ Interactive overview notebook
├── setup/                  ◄ Datasets, connections, IAM, CREATE MODEL deep dive, quotas
├── models/                 ◄ Per-model-type lifecycle deep dives (SQL + notebook)
│   └── logistic_regression/
├── functions/              ◄ Model-free ML.* utilities (SQL + notebook)
├── workflows/              ◄ End-to-end composed SQL logic
└── pipelines/              ◄ Orchestration / MLOps (scheduled queries, Composer, Vertex KFP)
```
