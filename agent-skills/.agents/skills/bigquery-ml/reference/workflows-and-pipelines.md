# Composing Workflows and Operationalizing Them With Pipelines

A single `CREATE MODEL` is rarely the whole task. Two layers build on the model types:

- **Workflows** compose model-free preprocessing + a model lifecycle into a real business question.
- **Pipelines** take a workflow's SQL and operationalize it: scheduled drift detection, conditional retraining, and scoring, through a real orchestrator.

## Workflows: what's already built

| Workflow | Models used | Real finding worth knowing before you copy the pattern |
|---|---|---|
| `regression_based_forecasting` | `LINEAR_REG`, `BOOSTED_TREE_REGRESSOR` | Forecast via lag/lead feature engineering instead of a native time-series model — a legitimate alternative to `ARIMA_PLUS` when you want a single model shared across many series or need arbitrary exogenous features. |
| `hierarchical_forecasting` | `ARIMA_PLUS` | Compares `ARIMA_PLUS`'s native bottom-up reconciliation against a hand-rolled top-down disaggregation on a real 4-level hierarchy. |
| `embeddings_classification` | `BOOSTED_TREE_CLASSIFIER` + `AI.EMBED`/`VECTOR_SEARCH` | The two *simpler* baselines (direct multiclass classifier; zero-training `VECTOR_SEARCH` lookup) beat the more elaborate pairwise classifier on both accuracy and cost — don't reach for the fancier technique by default. |
| `customer_segmentation` | `KMEANS` | The real content is RFM feature engineering, not `KMEANS` mechanics (see `unsupervised-and-specialized.md`). |
| `churn_retention` | `BOOSTED_TREE_CLASSIFIER` | Order-history-lapse churn definition. Richer features move accuracy/recall/F1 a lot but barely move `roc_auc` — a real lesson that headline metrics can hide weak individual-level signal. |
| `ga4_churn_prediction` | `BOOSTED_TREE_CLASSIFIER` | Engagement-based churn from a real GA4 export — first-week behavioral features give `roc_auc` 0.74-0.77 vs. 0.53 from order-history RFM alone. This is the workflow operationalized across all 8 pipelines below. |
| `recommendation` | `MATRIX_FACTORIZATION` | Personalized top-10 shares 0/10 items with a popularity baseline (real evidence personalization works); absent users fall back to a ranking that closely approximates the popularity baseline (cold start). |
| `anomaly_fraud_detection` | `PCA`, `AUTOENCODER`, `BOOSTED_TREE_CLASSIFIER` | Ground-truth validation against real labeled fraud — unsupervised recall roughly triples once you add labels and go supervised. Also found `pca_explained_variance_ratio` can shift materially across identical retrainings even though `ML.EVALUATE`'s own metric stays stable. |
| `cross_validation` | `LOGISTIC_REG` | BigQuery ML has no native k-fold CV — hand-roll it with deterministic hash-based fold assignment; a single holdout split can land on the low end of the real fold-to-fold variance. |
| `ensembling` | `LOGISTIC_REG`, `BOOSTED_TREE_CLASSIFIER`, `RANDOM_FOREST_CLASSIFIER` | A stacked ensemble wins on `roc_auc`; a free simple-average ensemble wins on F1 — pick the ensemble strategy by the metric you actually care about, not by complexity.
| `propensity_score_matching` | `LOGISTIC_REG` (as a propensity model, not a predictor) | This project's only **causal-inference** workflow — everything else above predicts an outcome, this one estimates a treatment effect from observational data. Naive, propensity-matched, and IPTW effect estimates all landed in a narrow band despite real, verified confounding — a genuine "the correction didn't change much" finding, not a failure of the method. See `unsupervised-and-specialized.md`'s sibling note on `CONTRIBUTION_ANALYSIS` for a related but distinct "why did this metric move" question. |

Go deeper: `workflows/<name>/`.

## Pipelines: choosing an orchestrator

All 8 pipelines operationalize the *same* workflow (`ga4_churn_prediction`) so they're a genuine apples-to-apples comparison. Use this to pick one:

| If you... | Reach for | Why |
|---|---|---|
| Have no orchestrator at all and want the simplest possible thing | `sql_scripting` | Pure `DECLARE`/`SET`/`IF`/`BEGIN...END` — one BigQuery script, no external system. Reports failures via `SELECT ERROR()` (becomes the job's error message). |
| Just want that script to run on a schedule | `scheduled_queries` | Wraps the exact same script in BigQuery Data Transfer API scheduling — the same mechanism behind BigQuery Studio's "Scheduled queries" UI. `FAILED` is a legitimate terminal state, not a bug. |
| Want version-controlled SQL with a dependency graph and built-in data-quality gates | `dataform` | One of Google's own officially-documented BQML pipeline paths (also powers BigQuery Studio's native "Pipelines" UI). `dependOnDependencyAssertions: true` makes a downstream table depend on a model's quality assertions, not just the model — a failing assertion genuinely blocks the downstream table. |
| Want serverless, near-free declarative orchestration without adopting Airflow | `cloud_workflows` | YAML-based; one BigQuery job per step (`jobs.insert` + poll `jobs.get`), branching in YAML. This is where the query-cache-staleness bug was originally found (see below). |
| Already run dbt for your other transformations | `dbt` | No *built-in* `CREATE MODEL` materialization (unlike Dataform) — closed with a one-time custom materialization macro. `dbt build` natively skips a downstream model when an upstream test fails, comparable to Dataform's assertion-gating. |
| Want managed ML orchestration with automatic lineage tracking | `vertex_kfp` | Official prebuilt `google_cloud_pipeline_components.v1.bigquery` ops (`BigqueryCreateModelJobOp`/`EvaluateModelJobOp`/`PredictModelJobOp`), auto-tracked in Vertex ML Metadata. Gate retraining with `dsl.If` on a custom metric-reading component. |
| Run an enterprise Airflow footprint and want BQML jobs as native Airflow tasks | `composer_airflow` | `BigQueryInsertJobOperator` + `BranchPythonOperator` + XCom for the conditional retrain, on Cloud Composer 3. |
| Have both an existing Airflow footprint *and* a KFP pipeline you don't want to rebuild | `airflow_with_kfp` | `RunPipelineJobOperator` triggers the already-built `vertex_kfp` pipeline as a single managed Airflow task — you don't have to choose one or the other. |

## Gotchas verified in this repo

- **Query-cache staleness after `CREATE OR REPLACE MODEL`**: any external orchestrator that runs the "before" and "after" `ML.EVALUATE` checks as *separate* query jobs can silently get served a stale cached result. Found in `cloud_workflows`; fixed everywhere by explicitly disabling the query cache on the check queries.
- **The disable-cache fix is not one value everywhere** — it's per-library, not per-BigQuery:
  - `google-cloud-bigquery` client / `cloud_workflows` YAML / `BigQueryInsertJobOperator` (`composer_airflow`): a real Python/JSON `False` works correctly.
  - `google_cloud_pipeline_components` prebuilt KFP ops (`vertex_kfp`): the components' own JSON-cleanup logic silently **drops** a Python `False` before it reaches the API — you must pass the **string** `'false'` instead. Verify whichever library you're using via `INFORMATION_SCHEMA.JOBS_BY_PROJECT` rather than assuming either behavior.
- **Composer 3, not Composer 2, is the current default choice** for new Airflow work in this project — it's billed in DCU-hours with explicit per-component `workloads_config` sizing (scheduler/web_server/worker/triggerer/dag_processor), which is the actual cost lever. A minimal webserver restarts every ~10-15 minutes and briefly 502s — build real retry-with-backoff, not a fixed short retry budget.
- **Deleting a Composer environment does not delete its GCS bucket** — it's orphaned and billed separately until removed by hand.
- **`MATRIX_FACTORIZATION` needs a BigQuery Editions reservation to train** (the only model type in this project that can't train on-demand) — use an autoscale reservation and tear it down after, never a flat capacity commitment.
- Every pipeline in this project performs **real teardown of real paid infrastructure it stands up** (reservations, Composer environments, endpoints) rather than leaving cleanup as a reader exercise — follow that convention for any new pipeline.
- **A dataset that's schema-perfect for a causal-inference story doesn't guarantee the real-world relationship is actually baked into the data** — verified twice while building `propensity_score_matching`: `thelook_ecommerce`/GA4 marketing-channel data and `bigquery-public-data.cms_synthetic_patient_data_omop` (a real pharmacoepidemiology drug-comparison dataset) both looked ideal on paper but showed essentially flat covariates/outcomes when actually queried — synthetic data generation frequently doesn't preserve the real confounding/effect relationships its schema suggests it should. Always verify the actual relationship live before committing to a causal-inference dataset, the same standing-practice discipline as validating any other SQL before it goes in a notebook.
- **BigQuery rejects a correlated subquery referencing a table inside a `JOIN ... ON` predicate** (`"Unsupported subquery with table in join predicate"`) — compute any such value (e.g. a matching caliper) as its own query first and substitute the literal.
- **A direct inequality self-join (e.g. nearest-neighbor matching on a continuous score) can blow through the on-demand CPU-to-bytes-billed ratio limit** (`"Query exceeded resource limits"`) even when the output is tiny, once both sides reach real population scale. Fix with sample-size discipline (work on a consistent, deterministic sample sized for the self-join to stay cheap) or a bucketed equi-join (round the join key into bins matching your tolerance, join on bucket equality, then refine) rather than a naive full-range join.

## Go deeper

Full extracted notebook walkthroughs live in this skill's `narrative/` folder:

**Workflows:**
- [`narrative/regression_based_forecasting.md`](../narrative/regression_based_forecasting.md) (source: `workflows/regression_based_forecasting/`)
- [`narrative/hierarchical_forecasting.md`](../narrative/hierarchical_forecasting.md) (source: `workflows/hierarchical_forecasting/`)
- [`narrative/embeddings_classification.md`](../narrative/embeddings_classification.md) (source: `workflows/embeddings_classification/`)
- [`narrative/customer_segmentation.md`](../narrative/customer_segmentation.md) (source: `workflows/customer_segmentation/`)
- [`narrative/churn_retention.md`](../narrative/churn_retention.md) (source: `workflows/churn_retention/`)
- [`narrative/ga4_churn_prediction.md`](../narrative/ga4_churn_prediction.md) (source: `workflows/ga4_churn_prediction/`)
- [`narrative/recommendation.md`](../narrative/recommendation.md) (source: `workflows/recommendation/`)
- [`narrative/anomaly_fraud_detection.md`](../narrative/anomaly_fraud_detection.md) (source: `workflows/anomaly_fraud_detection/`)
- [`narrative/cross_validation.md`](../narrative/cross_validation.md) (source: `workflows/cross_validation/`)
- [`narrative/ensembling.md`](../narrative/ensembling.md) (source: `workflows/ensembling/`)
- [`narrative/propensity_score_matching.md`](../narrative/propensity_score_matching.md) (source: `workflows/propensity_score_matching/`)

**Pipelines** (each has its own notebook + supporting files — DAGs, workflow YAML, dbt project, KFP pipeline spec, etc. — not captured in the narrative extract, which covers the notebook's own markdown+code):
- [`narrative/sql_scripting.md`](../narrative/sql_scripting.md) (source: `pipelines/sql_scripting/`)
- [`narrative/scheduled_queries.md`](../narrative/scheduled_queries.md) (source: `pipelines/scheduled_queries/`)
- [`narrative/dataform.md`](../narrative/dataform.md) (source: `pipelines/dataform/`)
- [`narrative/cloud_workflows.md`](../narrative/cloud_workflows.md) (source: `pipelines/cloud_workflows/`)
- [`narrative/dbt.md`](../narrative/dbt.md) (source: `pipelines/dbt/`)
- [`narrative/vertex_kfp.md`](../narrative/vertex_kfp.md) (source: `pipelines/vertex_kfp/`)
- [`narrative/composer_airflow.md`](../narrative/composer_airflow.md) (source: `pipelines/composer_airflow/`)
- [`narrative/airflow_with_kfp.md`](../narrative/airflow_with_kfp.md) (source: `pipelines/airflow_with_kfp/`)

Full pipeline comparison table: see the README in the source repo (`bq-ml/README.md`).
