-- Dataform — BigQuery ML Pipeline
-- =============================================================
-- Version-controlled SQL pipeline: CREATE MODEL as an `operations`-type
-- .sqlx file, ML.EVALUATE as an assertion that halts a dependent downstream
-- action when it fails. One of Google's own three officially-documented
-- BQML pipeline paths (alongside plain SQL scripting and Vertex AI
-- Pipelines) -- and the engine behind BigQuery Studio's newer native
-- "Pipelines" UI feature.
--
-- Workflow operationalized: ../../workflows/ga4_churn_prediction/
-- Data: bigquery-public-data.ga4_obfuscated_sample_ecommerce
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   Dataform overview: https://cloud.google.com/dataform/docs/overview
--   Create operations (hasOutput/self()): https://cloud.google.com/dataform/docs/custom-sql
--   Assertions: https://cloud.google.com/dataform/docs/assertions


-- =============================================================================
-- workflow_settings.yaml (project config -- modern replacement for the
-- legacy dataform.json + package.json pair; verified live that dataform.json
-- alone fails with "Can't find package.json")
-- =============================================================================
-- defaultProject: PROJECT_ID
-- defaultDataset: DATASET_ID
-- defaultLocation: US
-- defaultAssertionDataset: DATASET_ID_assertions
-- dataformCoreVersion: 3.0.0


-- =============================================================================
-- definitions/ga4_churn_pipeline_features.sqlx  (type: "table")
-- =============================================================================
-- config { type: "table" }
--
-- (same cohort/feature/label SELECT body as workflows/ga4_churn_prediction/
-- -- Dataform wraps it in CREATE OR REPLACE TABLE ${self()} AS (...)
-- automatically for type "table", so no CREATE statement is written here)


-- =============================================================================
-- definitions/ga4_churn_pipeline_model.sqlx  (type: "operations", hasOutput: true)
-- =============================================================================
-- config { type: "operations", hasOutput: true }
--
-- CREATE OR REPLACE MODEL ${self()}
-- OPTIONS(
--   model_type = 'BOOSTED_TREE_CLASSIFIER',
--   input_label_cols = ['churned'],
--   auto_class_weights = TRUE,
--   data_split_method = 'AUTO_SPLIT',
--   enable_global_explain = TRUE
-- ) AS
-- SELECT n_events, n_active_days, n_page_view, n_view_item, n_add_to_cart,
--        n_begin_checkout, n_sessions, did_purchase, device_category, country,
--        traffic_medium, total_engagement_time_msec, churned
-- FROM ${ref("ga4_churn_pipeline_features")}
-- WHERE first_date <= '2020-11-20'
-- -- hasOutput: true + ${self()} declares this operation's output (the MODEL)
-- -- as referenceable by other actions via ${ref("ga4_churn_pipeline_model")}.
-- -- ${ref(...)} establishes the real dependency edge in Dataform's DAG.


-- =============================================================================
-- definitions/ga4_churn_pipeline_quality_reasonable.sqlx  (type: "assertion")
-- =============================================================================
-- config { type: "assertion" }
--
-- SELECT * FROM ML.EVALUATE(MODEL ${ref("ga4_churn_pipeline_model")})
-- WHERE roc_auc < 0.6
-- -- Dataform assertions are just SELECT queries: returning ANY rows means
-- -- the assertion FAILED. Verified live: PASSED (0 rows) -- actual roc_auc
-- -- ~0.72-0.77 comfortably clears a 0.6 bar.


-- =============================================================================
-- definitions/ga4_churn_pipeline_quality_strict.sqlx  (type: "assertion")
-- =============================================================================
-- config { type: "assertion" }
--
-- SELECT * FROM ML.EVALUATE(MODEL ${ref("ga4_churn_pipeline_model")})
-- WHERE roc_auc < 0.99
-- -- Deliberately unrealistic bar to demonstrate a genuine, non-contrived
-- -- assertion FAILURE live (no model here gets anywhere near 0.99).
-- -- Verified live: FAILED -- "Query error: Assertion failed, expected zero
-- -- rows."


-- =============================================================================
-- definitions/ga4_churn_pipeline_scoring.sqlx  (type: "table",
-- dependOnDependencyAssertions: true)
-- =============================================================================
-- config { type: "table", dependOnDependencyAssertions: true }
--
-- SELECT user_pseudo_id, predicted_churned, predicted_churned_probs
-- FROM ML.PREDICT(
--   MODEL ${ref("ga4_churn_pipeline_model")},
--   (SELECT * FROM ${ref("ga4_churn_pipeline_features")} WHERE first_date <= '2020-11-20' LIMIT 1000)
-- )
-- -- dependOnDependencyAssertions: true makes this action ALSO depend on
-- -- every assertion of its direct dependencies (both quality assertions
-- -- above, since both reference ga4_churn_pipeline_model) -- not just the
-- -- model itself. Verified live: this is what actually halts the pipeline
-- -- on a failed quality gate, not just an evaluation number sitting unread
-- -- in a table somewhere.


-- =============================================================================
-- Verified live end-to-end workflow invocation result:
-- =============================================================================
-- ga4_churn_pipeline_features            SUCCEEDED
-- ga4_churn_pipeline_model               SUCCEEDED  (roc_auc ~0.73, see gotcha #3)
-- ga4_churn_pipeline_quality_reasonable  SUCCEEDED  (assertion passed)
-- ga4_churn_pipeline_quality_strict      FAILED     (assertion failed, as designed)
-- ga4_churn_pipeline_scoring             SKIPPED    (blocked by the failed
--                                                    dependency assertion --
--                                                    the table was never
--                                                    created)
-- Overall workflow invocation state: FAILED -- a real, working "halt
-- downstream work on a failed quality gate" pipeline, not a hypothetical.
--
-- Three real gotchas hit live, none documented in the tutorials researched:
-- 1. A workspace cannot be named the same as the repository's default
--    branch ("main") -- FAILED_PRECONDITION. Use any other workspace name.
-- 2. Running a workflow invocation requires an explicit service_account in
--    invocation_config, AND that service account's own IAM policy must
--    grant roles/iam.serviceAccountTokenCreator to Dataform's per-project
--    service agent (service-PROJECT_NUMBER@gcp-sa-dataform.iam.gserviceaccount.com)
--    -- otherwise every action fails with a permission-denied error before
--    any BigQuery work starts. IAM changes can take ~1-2 minutes to
--    propagate; the notebook checks for and grants this automatically, with
--    a short wait/retry if the very first invocation attempt hits the
--    propagation window.
-- 3. The notebook's own added `SELECT roc_auc FROM ML.EVALUATE(MODEL ...)`
--    display query (added after the pipeline run, outside Dataform) is a
--    plain standalone query -- exactly the pattern documented in
--    pipelines/cloud_workflows/ and RESOURCES.md as vulnerable to serving a
--    STALE cached result after CREATE OR REPLACE MODEL. Caught live: this
--    exact query text had run against this exact model name in earlier
--    pipeline notebooks, and without use_query_cache=False it displayed a
--    stale value (cache_hit: true, confirmed via INFORMATION_SCHEMA.JOBS).
--    Fixed by disabling the cache on that one query. The Dataform
--    assertions themselves (quality_reasonable/quality_strict) were never
--    affected -- Dataform compiles each into a CREATE VIEW + ASSERT script,
--    the same script-scoped pattern that makes pipelines/sql_scripting/
--    immune to this bug.


-- =============================================================================
-- Cleanup
-- =============================================================================
-- Delete the workspace, then force-delete the repository (removes the
-- workspace's uncommitted files -- nothing was ever committed to Dataform's
-- own git history in this demo, so no separate history to clean up):
--   dataform_client.delete_workspace(name=workspace.name)
--   dataform_client.delete_repository(request=DeleteRepositoryRequest(name=repository.name, force=True))
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.ga4_churn_pipeline_model`;
-- DROP TABLE IF EXISTS `PROJECT_ID.DATASET.ga4_churn_pipeline_features`;
-- DROP TABLE IF EXISTS `PROJECT_ID.DATASET.ga4_churn_pipeline_scoring`; -- only exists if the strict assertion was loosened enough to let it run
