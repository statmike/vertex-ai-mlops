![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Fdata%2Bai%2Fbq-ml&file=README.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/data%2Bai/bq-ml/README.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ml/README.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ml/README.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ml/README.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ml/README.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-ml/README.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-ml/README.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
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
| [Linear Regression](models/linear_regression/) | `LINEAR_REG` | ML.PREDICT | GA | Continuous-value regression with interpretable coefficients (`ML.WEIGHTS`) and hyperparameter tuning |
| [Boosted Tree Classifier](models/boosted_tree_classifier/) | `BOOSTED_TREE_CLASSIFIER` | ML.PREDICT | GA | XGBoost binary classification with split-based feature importance (`ML.FEATURE_IMPORTANCE`); same data as Logistic Regression for direct comparison |
| [Boosted Tree Regressor](models/boosted_tree_regressor/) | `BOOSTED_TREE_REGRESSOR` | ML.PREDICT | GA | XGBoost regression with tree visualization (`EXPORT MODEL` + `xgboost.plot_tree`); same data as Linear Regression for direct comparison |
| [Random Forest Classifier](models/random_forest_classifier/) | `RANDOM_FOREST_CLASSIFIER` | ML.PREDICT | GA | Bagged tree ensemble, single-pass training; same data as Logistic/Boosted Tree Classifier for a three-way comparison |
| [Random Forest Regressor](models/random_forest_regressor/) | `RANDOM_FOREST_REGRESSOR` | ML.PREDICT | GA | Bagged tree ensemble; same data as Linear/Boosted Tree Regressor — genuinely underperforms boosting on this small dataset, discussed honestly |
| [DNN Classifier](models/dnn_classifier/) | `DNN_CLASSIFIER` | ML.PREDICT | GA | Feed-forward neural network classification; same data as the other classifiers — training is verified much slower than tree models |
| [DNN Regressor](models/dnn_regressor/) | `DNN_REGRESSOR` | ML.PREDICT | GA | Feed-forward neural network regression; same data as the other regressors — an honest debugging story from a badly broken baseline to a working fix |
| [Wide & Deep Classifier](models/wide_and_deep_classifier/) | `DNN_LINEAR_COMBINED_CLASSIFIER` | ML.PREDICT | GA | Joint wide (linear) + deep (DNN) classification; same data as the other classifiers |
| [Wide & Deep Regressor](models/wide_and_deep_regressor/) | `DNN_LINEAR_COMBINED_REGRESSOR` | ML.PREDICT | GA | Joint wide (linear) + deep (DNN) regression; same data as the other regressors — `learn_rate`/`optimizer` are verified not tunable for this type, unlike plain DNN |
| [K-Means](models/kmeans/) | `KMEANS` | ML.PREDICT | GA | Unsupervised clustering — no label; verified genuinely non-deterministic across retrains (even with `KMEANS++`), so a single before/after comparison isn't reliable evidence of a feature's effect |
| [PCA](models/pca/) | `PCA` | ML.PREDICT | GA | Unsupervised dimensionality reduction — no label; verified fully deterministic (closed-form eigendecomposition, unlike K-Means), plus `ML.GENERATE_EMBEDDING` and reconstruction-based `ML.DETECT_ANOMALIES` |
| [Autoencoder](models/autoencoder/) | `AUTOENCODER` | ML.PREDICT | GA | Unsupervised nonlinear dimensionality reduction — no label; the default RELU activation genuinely collapses to dead latent units on a small network, fixed by switching to TANH; embeddings pair with `VECTOR_SEARCH` for similarity |
| [Matrix Factorization](models/matrix_factorization/) | `MATRIX_FACTORIZATION` | ML.RECOMMEND | GA | Collaborative-filtering recommender — the only model type here that can't train on-demand; the notebook sets up and tears down a temporary BigQuery Editions reservation to enable it |
| [Contribution Analysis](models/contribution_analysis/) | `CONTRIBUTION_ANALYSIS` | ML.GET_INSIGHTS | GA | Key-driver / segment analysis — cross-links to `bq-ai-functions`' `AI.KEY_DRIVERS`; verified `ML.GET_INSIGHTS` has three different output schemas depending on the metric type (summable/ratio/category) |
| [AutoML Classifier](models/automl_classifier/) | `AUTOML_CLASSIFIER` | ML.PREDICT | GA | Vertex AI AutoML Tables binary classification via `CREATE MODEL`; same data as the other classifiers. The first model type in this project with real, substantial dollar cost (~$21–32/run) and multi-hour wall-clock time |
| [AutoML Regressor](models/automl_regressor/) | `AUTOML_REGRESSOR` | ML.PREDICT | GA | Vertex AI AutoML Tables regression via `CREATE MODEL`; uses `bigquery-public-data.samples.natality` (not `penguins`, which fails — AutoML requires 1,000+ training rows) |
| [ARIMA_PLUS](models/arima_plus/) | `ARIMA_PLUS` | ML.FORECAST | GA | Univariate time series forecasting — 5 real Citi Bike stations, single-series then multi-series via `time_series_id_col`; folds in granularity/missing-data handling as a verified GOTCHA (a real gap day interpolates to exactly the neighbor average) |
| [ARIMA_PLUS_XREG](models/arima_plus_xreg/) | `ARIMA_PLUS_XREG` | ML.FORECAST | GA | Multivariate forecasting with external regressors — same stations/TEST window as ARIMA_PLUS for direct comparison; verified several real option-compatibility differences from plain ARIMA_PLUS (forecast bounds rejected outright, no `mean_absolute_scaled_error`, strict 3-argument `ML.FORECAST`) |

*More model types are planned — see the backlog in [PLANS.md](PLANS.md) (imported / remote / exported model categories) — comprehensive coverage, not optional stretch goals.*

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
| [Regression-Based Forecasting](workflows/regression_based_forecasting/) | `LINEAR_REG`, `BOOSTED_TREE_REGRESSOR` · `ML.EVALUATE`, `ML.PREDICT` | Forecasts Citi Bike demand via time/lag/lead feature engineering instead of a native time-series model — time features only, + lags (leaked/truncated/recursive evaluation), and direct multi-step (one model per horizon day). Compares accuracy against `models/arima_plus/` on the identical station/TEST window. |
| [Hierarchical Forecasting](workflows/hierarchical_forecasting/) | `ARIMA_PLUS` · `ML.FORECAST`, `ML.EVALUATE` | Compares BQML's built-in bottom-up hierarchical reconciliation (`hierarchical_time_series_cols`) against a from-scratch top-down disaggregation (forecast proportions) on a real `State → County → City → Store` hierarchy (Iowa liquor sales). Includes a generalized Python function that automates the top-down cascade for any hierarchy depth. |
| [Embeddings As Features For Hierarchical Classification](workflows/embeddings_classification/) | `BOOSTED_TREE_CLASSIFIER` · `AI.EMBED`, `ML.EVALUATE`, `ML.PREDICT`, `VECTOR_SEARCH` | Places retail products into a `department → category` hierarchy 3 ways: a pairwise "does this belong here?" classifier (3 feature constructions, resolved top-down via `ML.PREDICT` + `UNNEST`/`QUALIFY`), a direct multiclass classifier, and a zero-training `VECTOR_SEARCH` lookup. The two simpler baselines both beat the pairwise approach on accuracy *and* cost — a real lesson in not reaching for the more complex technique by default. |
| *(planned)* | — | See [PLANS.md](PLANS.md) Phase 7 (segmentation, recommendation) |

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
