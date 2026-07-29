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
| [Agent Skill](../../agent-skills/.agents/skills/bigquery-ml/SKILL.md) | Packaged, use-case-organized reference for AI coding agents — see below |

New to BigQuery ML? Start with the [**Logistic Regression**](models/logistic_regression/) model — it walks the entire lifecycle end to end and is the template every other model follows.

### Using this project with an AI coding agent

This project's Agent Skill content lives centrally in [`agent-skills/`](../../agent-skills/) at the repo root (alongside every other skill built from this repo), not inside this folder — see the [`bigquery-ml` skill](../../agent-skills/.agents/skills/bigquery-ml/SKILL.md), a use-case-organized (classification / regression / unsupervised / model management / preprocessing / workflows-and-pipelines), gotcha-rich distillation of `RESOURCES.md` built for coding agents, not just human readers.

- **Claude Code** — picked up automatically from `.claude/skills/bigquery-ml` (a repo-root symlink into `agent-skills/`) anywhere in this repo; no setup needed. It activates automatically when your request matches — training/evaluating/deploying a model, picking a preprocessing function, choosing an orchestration pipeline — or invoke it explicitly.
- **Google Antigravity, Codex, and other `.agents/skills/`-compatible tools** — discovered from the repo-root `.agents/skills/bigquery-ml/` symlink, using the same `SKILL.md` files.
- **Standalone / other repos** — the whole `agent-skills/.agents/skills/bigquery-ml/` folder is self-contained and can be copied into any other project.

Not sure whether BigQuery ML or [BigQuery AI Functions](../bq-ai-functions/) fits your task? The [`choosing-a-bigquery-ai-approach`](../../agent-skills/.agents/skills/choosing-a-bigquery-ai-approach/SKILL.md) skill triages between the two.

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
| [Transform-Only](models/transform_only/) | `TRANSFORM_ONLY` | ML.TRANSFORM | GA | A model with no estimator — packages preprocessing (`ML.IMPUTER` + scalers + `ML.ONE_HOT_ENCODER`) as a reusable, exportable pipeline; verified a downstream model with no embedded `TRANSFORM` silently mispredicts on raw data until `ML.TRANSFORM` is re-applied |
| [Imported](models/imported/) | `TENSORFLOW` / `TENSORFLOW_LITE` / `ONNX` / `XGBOOST` | ML.PREDICT | GA | Bring a model trained outside BigQuery (scikit-learn, XGBoost, Keras) in from GCS and run `ML.PREDICT` natively — no connection, no serving endpoint; verified BQML's `XGBOOST` importer caps at XGBoost ≤ 1.5.1 |
| [Export](models/export/) | `EXPORT MODEL` | — | GA | Write a trained model to GCS as a TensorFlow SavedModel or XGBoost Booster and prove it runs entirely outside BigQuery; also covers `model_registry='VERTEX_AI'` and the `bq extract --model` CLI equivalent |
| [Remote](models/remote/) | `REMOTE` (custom Vertex AI endpoint) | ML.PREDICT | GA | The full round trip: train → export → deploy to a Vertex AI Endpoint → call it back from BigQuery with `REMOTE WITH CONNECTION`. The one model type in this project with a live, billable Endpoint — kept to a few minutes and torn down immediately. Also documents a confirmed, currently-broken Google shortcut (`model_registry='VERTEX_AI'` deploy fails on an unconditional explanation spec) and proves `REMOTE` works with a model that never touched BigQuery ML at all (an externally-trained XGBoost model, registered but not deployed) |

## Functions

Model-free `ML.*` utilities that transform data directly (no model required).

| Function | Category | Status | What it does |
|----------|----------|--------|--------------|
| [Scalers](functions/scalers/) | `ML.STANDARD_SCALER` / `ML.MIN_MAX_SCALER` / `ML.MAX_ABS_SCALER` / `ML.ROBUST_SCALER` / `ML.NORMALIZER` | GA | Rescale numerical inputs; verified `ML.STANDARD_SCALER` uses population (not sample) stddev, `ML.MIN_MAX_SCALER` caps out-of-range predictions to `[0,1]`, and `ML.ROBUST_SCALER` is provably immune to an injected outlier that distorts `ML.STANDARD_SCALER` |
| [Feature Engineering](functions/feature_engineering/) | `ML.IMPUTER` / `ML.FEATURE_CROSS` / `ML.POLYNOMIAL_EXPAND` | GA | Fill `NULL`s and build interaction/power terms; verified live that `ML.FEATURE_CROSS`/`ML.POLYNOMIAL_EXPAND` train and predict fine inside a `TRANSFORM` but the model can't be exported (exact error captured) |
| [Encoding](functions/encoding/) | `ML.ONE_HOT_ENCODER` / `ML.LABEL_ENCODER` / `ML.MULTI_HOT_ENCODER` | GA | Categorical encoding; verified live that the current default `frequency_threshold=5` silently drops any category with fewer than 5 occurrences into the unknown bucket — a real behavior change from older `frequency_threshold=0` documentation |
| [Bucketizing](functions/bucketizing/) | `ML.BUCKETIZE` / `ML.QUANTILE_BUCKETIZE` / `ML.HASH_BUCKETIZE` | GA | Discretize continuous/string values; clarifies live what `exclude_boundaries=TRUE` actually does (merges outer bins, doesn't null out-of-range values) |
| [Distance / Vectors](functions/distance/) | `ML.DISTANCE` / `ML.LP_NORM` | GA | Pairwise vector distance and vector magnitude — no prior repo example; verified `ML.NORMALIZER` equals `v / ML.LP_NORM(v, p)`, plus a real embedding-similarity worked example using a scratch PCA model |
| [Text](functions/text/) | `ML.NGRAMS` / `ML.TF_IDF` / `ML.BAG_OF_WORDS` | GA | Turn tokenized text into features; `ML.TF_IDF`/`ML.BAG_OF_WORDS` had no prior repo example — verified they share the same `frequency_threshold=5` default gotcha as the encoders |
| [Data Quality](functions/data_quality/) | `ML.DESCRIBE_DATA` / `ML.VALIDATE_DATA_SKEW` / `ML.VALIDATE_DATA_DRIFT` / `ML.TFDV_DESCRIBE` / `ML.TFDV_VALIDATE` | GA | Dataset-level distribution monitoring (distinct from row-level `ML.DETECT_ANOMALIES`); verified live that naive `LIMIT`-based sampling (no `ORDER BY`) triggers a false-positive skew alarm on a non-randomly-ordered public table — fixed with `WHERE RAND() < p` |

`ML.STANDARD_SCALER` is also demonstrated inline in the [Logistic Regression](models/logistic_regression/) notebook (the `TRANSFORM` clause), and `ML.IMPUTER`/scalers/`ML.ONE_HOT_ENCODER` are composed together in [Transform-Only](models/transform_only/).

## Workflows

End-to-end SQL logic composing preprocessing + a model lifecycle into a real task.

| Workflow | Models / Functions used | What it does |
|----------|-------------------------|--------------|
| [Regression-Based Forecasting](workflows/regression_based_forecasting/) | `LINEAR_REG`, `BOOSTED_TREE_REGRESSOR` · `ML.EVALUATE`, `ML.PREDICT` | Forecasts Citi Bike demand via time/lag/lead feature engineering instead of a native time-series model — time features only, + lags (leaked/truncated/recursive evaluation), and direct multi-step (one model per horizon day). Compares accuracy against `models/arima_plus/` on the identical station/TEST window. |
| [Hierarchical Forecasting](workflows/hierarchical_forecasting/) | `ARIMA_PLUS` · `ML.FORECAST`, `ML.EVALUATE` | Compares BQML's built-in bottom-up hierarchical reconciliation (`hierarchical_time_series_cols`) against a from-scratch top-down disaggregation (forecast proportions) on a real `State → County → City → Store` hierarchy (Iowa liquor sales). Includes a generalized Python function that automates the top-down cascade for any hierarchy depth. |
| [Embeddings As Features For Hierarchical Classification](workflows/embeddings_classification/) | `BOOSTED_TREE_CLASSIFIER` · `AI.EMBED`, `ML.EVALUATE`, `ML.PREDICT`, `VECTOR_SEARCH` | Places retail products into a `department → category` hierarchy 3 ways: a pairwise "does this belong here?" classifier (3 feature constructions, resolved top-down via `ML.PREDICT` + `UNNEST`/`QUALIFY`), a direct multiclass classifier, and a zero-training `VECTOR_SEARCH` lookup. The two simpler baselines both beat the pairwise approach on accuracy *and* cost — a real lesson in not reaching for the more complex technique by default. |
| [Customer Segmentation](workflows/customer_segmentation/) | `KMEANS` · `ML.STANDARD_SCALER`, `ML.EVALUATE`, `ML.CENTROIDS`, `ML.PREDICT` | RFM (Recency/Frequency/Monetary) feature engineering from raw `thelook_ecommerce` order history, then `KMEANS` into 4 interpretable business segments (champions, loyal regulars, one-time low-value, lapsed). The real content is the feature engineering — `KMEANS` mechanics are covered in `models/kmeans/`. |
| [Churn / Retention](workflows/churn_retention/) | `BOOSTED_TREE_CLASSIFIER` · `ML.EVALUATE`, `ML.CONFUSION_MATRIX`, `ML.GLOBAL_EXPLAIN`, `ML.EXPLAIN_PREDICT` | Defines churn from real order-history gaps (a genuine backtest, not a synthetic label), then an honest metric-literacy lesson: richer features improve accuracy/recall/F1 substantially but barely move `roc_auc` — a real finding about this dataset's weak individual-level churn signal, not glossed over. |
| [GA4 Churn Prediction](workflows/ga4_churn_prediction/) | `BOOSTED_TREE_CLASSIFIER` · `ML.EVALUATE`, `ML.CONFUSION_MATRIX`, `ML.GLOBAL_EXPLAIN`, `ML.FEATURE_IMPORTANCE`, `ML.EXPLAIN_PREDICT` | Engagement-based churn from a real GA4 event export (Google Merchandise Store) — a genuine complement to `churn_retention`'s order-lapse definition. First-week behavioral features give a much stronger signal (`roc_auc` 0.74-0.77 vs. 0.53) than order-history RFM alone, and richer features move `roc_auc` *up* while fixed-threshold metrics move slightly down — the mirror image of `churn_retention`'s finding. This workflow is operationalized across all of Phase 8's [Pipelines](#pipelines). |
| [Recommendation](workflows/recommendation/) | `MATRIX_FACTORIZATION` · `ML.EVALUATE`, `ML.RECOMMEND` | Extends `models/matrix_factorization/` into a full workflow: a popularity baseline (personalized top-10 shares 0/10 items with it — real evidence personalization works), batch top-N generation for many users at once, and an empirical cold-start deep dive (absent users get an identical, non-personalized fallback ranking that itself closely approximates the popularity baseline). |
| [Anomaly / Fraud Detection](workflows/anomaly_fraud_detection/) | `PCA`, `AUTOENCODER`, `BOOSTED_TREE_CLASSIFIER` · `ML.DETECT_ANOMALIES`, `ML.EVALUATE` | The real ground-truth validation the 5 existing `ML.DETECT_ANOMALIES` demos lack — real labeled fraud (`ulb_fraud_detection`, 492 cases), unsupervised precision/recall vs. a supervised classifier (recall triples with labels). Along the way, found and documented a genuine PCA reproducibility gotcha: `pca_explained_variance_ratio` can produce wildly different anomaly-detection results across identical retrainings even though `ML.EVALUATE`'s own metric stays stable. |
| [Cross-Validation](workflows/cross_validation/) | `LOGISTIC_REG` · `ML.EVALUATE` | BigQuery ML has no native k-fold cross-validation — hand-rolls 5-fold CV via deterministic hash-based fold assignment on `ulb_fraud_detection` (reused from `anomaly_fraud_detection`, motivated by that workflow's ~15-fraud-case eval split). Real fold-to-fold metric variance (roc_auc 0.968-0.985) is compared against a same-model-type single holdout, which lands within — but on the low end of — the fold distribution. |
| [Ensembling](workflows/ensembling/) | `LOGISTIC_REG`, `BOOSTED_TREE_CLASSIFIER`, `RANDOM_FOREST_CLASSIFIER` · `ML.PREDICT`, `ML.EVALUATE` | Self-contained stacked ensemble (3 base model types, own retrains — no cross-notebook dependency) on `census_adult_income`, with a stricter 3-way TRAIN/VALIDATE/TEST split than the legacy notebook it modernizes to avoid stacking leakage. Honest, metric-dependent finding: the stacker wins on `roc_auc`, a free simple-average ensemble wins on F1 — neither dramatically. |
| [Propensity Score Matching](workflows/propensity_score_matching/) | `LOGISTIC_REG` · `ML.EVALUATE`, `ML.PREDICT` | This project's first causal-inference (not prediction) workflow — does maternal smoking during pregnancy affect birth weight, estimated from real (non-synthetic) `bigquery-public-data.samples.natality` records where treatment was never randomized. `LOGISTIC_REG` trains the propensity model; nearest-neighbor matching and inverse-probability-of-treatment weighting (IPTW) are hand-rolled SQL. Two dataset candidates (`thelook_ecommerce`/GA4 marketing channels, then `cms_synthetic_patient_data_omop` metformin vs. glyburide — the textbook pharmacoepi PSM example) were tried and rejected live because their synthetic data didn't actually encode the real-world confounding/effect relationships. Honest finding: naive, matched, and IPTW effect estimates all land in a narrow band (roughly -0.40 to -0.43 lbs, exact values shift run to run since `LOGISTIC_REG`'s `AUTO_SPLIT` re-randomizes the train/eval split on every retrain) — the measured confounders are real and imbalanced but aren't the dominant driver of the naive gap. |
| [Survival Analysis](workflows/survival_analysis/) | `LOGISTIC_REG` (+ `lifelines.CoxPHFitter` outside BigQuery) · `ML.EVALUATE`, `ML.PREDICT`, `ML.WEIGHTS` | States upfront that Cox Proportional Hazards — the standard survival model — is not possible natively in BigQuery ML (its partial-likelihood, risk-set estimation doesn't map onto any BQML model type) and names real external options (`lifelines`, `scikit-survival`, `statsmodels.PHReg`), then builds what genuinely is possible: Kaplan-Meier curves in pure SQL and a discrete-time hazard model (person-period reshape + `LOGISTIC_REG`). Also fits real Cox PH via `lifelines` to prove the escape hatch works, hitting and fixing two genuine convergence errors along the way (collinearity, then an unstandardized skewed covariate). Reuses `ga4_churn_prediction`'s real GA4 cohort (time-to-first-purchase instead of 30-day churn) after `thelook_ecommerce` again showed no real covariate-hazard signal live. Honest finding: all three techniques agree first-week activity strongly accelerates time-to-purchase (KM curves separate ~30 points by week 5, discrete-hazard `roc_auc` ~0.90, Cox hazard ratio ~4.3) — real converging evidence, with Cox's BigQuery-exit tradeoff and the discrete model's weekly-granularity coarsening both disclosed plainly. |
| [Price Elasticity via Double ML](workflows/price_elasticity_dml/) | `LINEAR_REG`, `BOOSTED_TREE_REGRESSOR` · `ML.WEIGHTS`, `ML.PREDICT` | Naive price/quantity regression is confounded by real factors (distribution breadth, category, vendor) — Double Machine Learning (Chernozhukov et al. 2018, the current industry standard) fixes this natively: two `BOOSTED_TREE_REGRESSOR` models strip out what confounders explain via 5-fold cross-fitting (reusing `cross_validation`'s fold pattern), then a final regression on the residuals isolates price's own effect. Cross-sectional design across 1,130 real Iowa liquor SKUs (`iowa_liquor_sales`'s retail price is state-fixed over time, ruling out a time-series design, but genuinely varies across brands/products). Honest finding: naive elasticity (~-1.4) overstates the true effect by roughly 2x once confounding is removed (DML ~-0.7) — distribution breadth alone explained much of the apparent price sensitivity. |
| [Uplift Modeling / CATE (T-Learner)](workflows/uplift_cate/) | `BOOSTED_TREE_CLASSIFIER` · `ML.PREDICT` | A single average treatment effect (`propensity_score_matching`'s territory) can hide the only number a real targeting decision needs: which segments actually respond. A T-learner — two independent `BOOSTED_TREE_CLASSIFIER` models, one per treatment arm (paid marketing vs. organic search, on the real GA360 Merchandise Store export) — estimates a per-session Conditional Average Treatment Effect, fully native to BigQuery ML. Verified real heterogeneity (desktop uplift ~10x tablet's, new-visitor uplift ~3x returning-visitor's) and a real, front-loaded Qini curve confirming the model's ranking beats random targeting where it matters most. Honest finding: a T-learner is more bias-prone than X-learner/R-learner meta-learners (`causalml`, `EconML`) under this workflow's real ~12:1 treatment/control imbalance — not needed here since the point is demonstrating real, capturable heterogeneity exists. |
| [Difference-in-Differences](workflows/difference_in_differences/) | `LINEAR_REG` | States that naive two-way-fixed-effects DiD (the textbook "just add more units" extension) is now known (Goodman-Bacon 2021, Callaway-Sant'Anna 2021) to be unreliable under staggered treatment timing — sometimes attenuating the estimate, sometimes flipping its sign — then proves both failure modes with real data. A clean single-date design (Texas's 2020 mask mandate vs. Georgia, a real untreated comparison) is fully native and reliable once checked across multiple post-period horizons (`LINEAR_REG` with an interaction term). **Found and fixed a major, previously-undocumented BQML gotcha**: `LINEAR_REG`'s default `optimize_strategy='AUTO_STRATEGY'` chose gradient descent that stopped before converging on this small, collinear design, silently returning a coefficient 68% too small — `optimize_strategy='NORMAL_EQUATION'` fixes it. A real staggered-adoption panel (9 states, different real mandate dates) shows naive TWFE substantially understating the true effect in this run (and, per an earlier live check of the identical query against the same revised-over-time public dataset, flipping its sign entirely) — corrected via the real, installable `differences` package's Callaway-Sant'Anna estimator. |
| [Synthetic Control](workflows/synthetic_control/) | `LINEAR_REG` (native, unconstrained approximation) | Extends `difference_in_differences`'s single, somewhat-arbitrary comparison state (Georgia) into a weighted combination of several real, verified never-mandated states — the same method behind the classic California tobacco-tax study, still used today for geo marketing-lift experiments. States upfront that the real constrained optimization (weights non-negative, summing to 1 — a literal blend of real states) is a quadratic program `CREATE MODEL` can't express, and proves it concretely: the unconstrained `LINEAR_REG` fit gives negative weights and a sum far from 1, further destabilized by a genuinely underdetermined system (9 pre-period weeks vs. 13 donors). The real constrained fit (`scipy.optimize`, matching `pysyncon`'s approach) settles on 82.4% Georgia + 17.6% Idaho, improving pre-period fit ~24% over Georgia alone, and its post-period estimate (-19.28) closely corroborates the simple 2-state DiD (-19.29) — two independently-built counterfactuals agreeing. |

## Pipelines

Operationalizing the workflows — MLOps on BigQuery. Same logic, scheduled and orchestrated.

| Pipeline | Approach | What it shows |
|----------|----------|---------------|
| [SQL Scripting](pipelines/sql_scripting/) | `DECLARE`/`SET`/`IF`/`BEGIN...END` · `ML.VALIDATE_DATA_DRIFT`, `ML.EVALUATE` | No external orchestrator: one multi-statement BigQuery script checks data drift between the model's original training cohort and everyone who arrived since, conditionally retrains, and reports via `SELECT ERROR()` (the report becomes the job's error message — a real alerting idiom). Live, explainable result: a genuine Black-Friday-driven population shift triggers a retrain that improves `roc_auc`. Modernizes `MLOps/Model Monitoring/model_monitoring_job.sql`. |
| [Scheduled Queries](pipelines/scheduled_queries/) | `google.cloud.bigquery_datatransfer` · `TransferConfig`, `ScheduleOptions`, `EmailPreferences` | Takes `sql_scripting`'s exact script, unmodified, and schedules it via the BigQuery Data Transfer API (the same mechanism behind BigQuery Studio's "Scheduled queries" UI). Triggers a real manual backfill run and confirms `FAILED` is the correct terminal state (the `SELECT ERROR()` report becomes the failure-alert email payload). Modernizes `MLOps/Model Monitoring/bqml-model-monitoring-tutorial.ipynb`'s scheduling section. |
| [Dataform](pipelines/dataform/) | `google.cloud.dataform_v1` · `CREATE MODEL` as `operations`/`hasOutput`, `ML.EVALUATE` as an `assertion` | Version-controlled SQL pipeline — a real 5-action dependency graph (feature table → model → two quality assertions → scoring table) compiled and run via the Dataform API. `dependOnDependencyAssertions: true` makes the scoring table depend on the model's assertions, not just the model itself — verified live that a deliberately-failing strict assertion genuinely blocks the scoring table from ever being created, while a passing assertion lets the pipeline continue. One of Google's own three officially-documented BQML pipeline paths, and the engine behind BigQuery Studio's native "Pipelines" UI. |
| [Cloud Workflows](pipelines/cloud_workflows/) | Cloud Workflows YAML · `googleapis.bigquery.v2.jobs.*` connector | The same `sql_scripting` drift-check/retrain logic re-expressed as external declarative orchestration — one BigQuery job per step (`jobs.insert` + poll `jobs.get`), branching on the result in YAML instead of BigQuery's own scripting language. A serverless, near-free alternative to Airflow for simple pipelines. **Found and fixed a major, previously-undocumented BQML gotcha while building this**: BigQuery's query result cache can silently serve a stale `ML.EVALUATE` result after `CREATE OR REPLACE MODEL` when the before/after checks are separate query jobs (exactly what any external orchestrator does) — fixed with `useQueryCache: false`, now documented in [RESOURCES.md](RESOURCES.md). |
| [dbt](pipelines/dbt/) | `dbt-core`/`dbt-bigquery` via `dbtRunner` · custom `bqml_model` materialization, dbt tests | Works end-to-end: a real BQML model trained under dbt, a passing and a deliberately-failing quality-gate test, and a downstream table dbt correctly refuses to build when a gate fails. dbt has no *built-in* `CREATE MODEL` materialization (unlike Dataform's officially-supported one) — closed with a small, one-time custom materialization macro, not a per-model workaround. `dbt build` (not separate `run`+`test`) natively skips a downstream model when an upstream test fails, a genuinely comparable capability to Dataform's `dependOnDependencyAssertions` — corrected live from an initial wrong assumption that dbt tests were report-only. Also notes dbt's newer, more "native" ML path (Python models via BigFrames) as a further option, not a replacement for what's demonstrated here. |
| [Vertex AI Pipelines (KFP)](pipelines/vertex_kfp/) | `google_cloud_pipeline_components.v1.bigquery` · `BigqueryCreateModelJobOp`/`EvaluateModelJobOp`/`PredictModelJobOp` | Train → evaluate → quality-gate → conditionally score, using the official prebuilt BQML components (auto-tracked lineage in Vertex ML Metadata) instead of hand-rolled BigQuery client calls — a real upgrade over this repo's own legacy custom-`@dsl.component` pattern. One small custom component reads back the quality metric and gates `BigqueryPredictModelJobOp` via `dsl.If`, verified live both ways: a passing threshold triggers scoring, an unattainable one genuinely blocks it (the prediction job never even gets created). **Found two real gotchas building this**: the `evaluation_metrics` artifact stores raw BigQuery REST-style `schema`/`rows` data, not a flat metric dict; and the prebuilt components' own JSON-cleanup logic silently drops `useQueryCache: False` (a Python bool) before it ever reaches the API — passing the *string* `'false'` is the actual fix. Both now documented in [RESOURCES.md](RESOURCES.md). |
| [Cloud Composer / Airflow](pipelines/composer_airflow/) | Cloud Composer 3 · `BigQueryInsertJobOperator`, `BranchPythonOperator`, XCom | The same `sql_scripting` drift-check/retrain logic on a real, live Cloud Composer 3 environment — `BigQueryInsertJobOperator` for every BigQuery job, `BranchPythonOperator` + XCom for the conditional retrain, a join task with `trigger_rule=NONE_FAILED_MIN_ONE_SUCCESS`. First use of Composer 3 in this repo (cheaper than Composer 2 via explicit per-component `workloads_config` sizing, billed in DCU-hours). **Verified live that `useQueryCache: False` (a real Python bool) works correctly here**, unlike the KFP-components bug found in `vertex_kfp` — confirmed via `INFORMATION_SCHEMA.JOBS_BY_PROJECT`. Also found and worked around a minimal-webserver restart cycle (~every 10-15 min) requiring genuine retry-with-backoff, not just a fixed short retry budget. |
| [Airflow + Vertex AI Pipelines (KFP)](pipelines/airflow_with_kfp/) | `RunPipelineJobOperator` · shares the Composer 3 environment above | The "meta-orchestration" pairing: one Airflow task (`RunPipelineJobOperator`) triggers `pipelines/vertex_kfp/`'s already-built Vertex Pipeline — the repo's original "DAG 3" pattern, now pointed at a real BQML pipeline instead of Dataflow/Dataproc. Verified live end-to-end, including independently confirming the triggered `PipelineJob` itself succeeded (not just the Airflow task). **A real bug caught building this**: this notebook must recreate its own feature table rather than assume `composer_airflow`'s copy still exists, since that notebook's own Cleanup drops it as soon as its run finishes, even in the same session. Also found that deleting a Composer environment does **not** delete its GCS bucket — orphaned and billed separately until removed by hand. Performs the real shared-environment teardown. |

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

   Model management: EXPORT MODEL (→ GCS) · imported models (TF/TFLite/ONNX/XGBoost)
                     · remote models (REMOTE WITH CONNECTION → Vertex AI)
                     · TRANSFORM_ONLY (preprocessing pipeline, no estimator)

   Pipelines wrap all of the above for scheduled retrain + scoring
   (SQL scripting · scheduled queries · Composer/Airflow · Vertex KFP)
```

**Key distinctions:**
- **`CREATE MODEL`** trains a model object stored in your dataset; `model_type` picks the algorithm.
- **Lifecycle `ML.*` functions** are table-valued — use them in `FROM`, passing `MODEL \`...\`` and (optionally) input data.
- **Model-free `ML.*` functions** transform data with no model — use standalone or inside `TRANSFORM`.
- **Most model types need no connection — including imported models and `EXPORT MODEL`.** Verified live: only `REMOTE WITH CONNECTION` (Vertex endpoints) genuinely requires one; imported/export just need ordinary GCS IAM on your own credentials. See [Setup](setup/).
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
