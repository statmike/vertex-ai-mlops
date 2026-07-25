-- Airflow + Vertex AI Pipelines (KFP) — BigQuery ML Pipeline
-- =============================================================
-- The "meta-orchestration" pairing: an Airflow DAG on the same live Cloud
-- Composer 3 environment as pipelines/composer_airflow/, using
-- RunPipelineJobOperator to trigger pipelines/vertex_kfp/'s already-built
-- Vertex AI Pipeline as a single managed task -- the repo's original "DAG 3"
-- pattern (MLOps/Serving/Batch/Orchestrating Batch Inference With
-- Airflow.ipynb), now pointed at a BQML pipeline instead of Dataflow/Dataproc.
--
-- Workflow operationalized: ../../workflows/ga4_churn_prediction/ (via ../vertex_kfp/)
-- Data: bigquery-public-data.ga4_obfuscated_sample_ecommerce
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   RunPipelineJobOperator: https://airflow.apache.org/docs/apache-airflow-providers-google/stable/operators/cloud/vertex_ai.html
--   MLOps/Serving/Batch/Orchestrating Batch Inference With Airflow.ipynb -- original "DAG 3" precedent


-- =============================================================================
-- dag_airflow_with_kfp.py -- reproduced in full in the notebook
-- =============================================================================
-- One task: RunPipelineJobOperator(
--     task_id="run_ga4_churn_kfp_pipeline",
--     project_id=..., region=..., display_name=...,
--     template_path=GCS_PATH_TO_COMPILED_PIPELINE_JSON,
--     pipeline_root=..., enable_caching=False,
--     parameter_values={"project":..., "dataset":..., "location":..., "quality_threshold": 0.6},
-- )
-- All the actual BQML logic (train -> evaluate -> quality-gate -> conditionally
-- score) lives in the compiled pipeline from pipelines/vertex_kfp/ -- reproduced
-- inline here for a self-contained build, not duplicated logic maintained twice.


-- =============================================================================
-- GOTCHA #1 (verified live, a REAL bug caught during build): this notebook
-- must recreate its own feature table -- it cannot rely on
-- pipelines/composer_airflow/'s copy still existing
-- =============================================================================
-- First live run failed: BigqueryCreateModelJobOp errored with "Not found:
-- Table PROJECT:DATASET.ga4_churn_pipeline_features was not found in
-- location US". Root cause: pipelines/composer_airflow/'s own Cleanup drops
-- its feature table/model as soon as ITS run finishes -- even when the two
-- notebooks are built/run back-to-back in the same session, by the time
-- this notebook's pipeline actually needs the table, it's already gone.
-- FIX: this notebook has its own Step 1 that recreates the feature table
-- independently, the same self-contained pattern every other Phase 8
-- pipeline already uses -- don't assume a sibling notebook's artifacts
-- persist past its own Cleanup, even in the same working session.


-- =============================================================================
-- GOTCHA #2 (verified live): a manually-triggered run of a PAUSED DAG hangs
-- forever in "queued", with no error
-- =============================================================================
-- Mid-build, this DAG got paused (via the Airflow REST API, to stop an
-- unrelated retry storm from a crashed test run). A subsequent manual
-- trigger (POST .../dagRuns) returned 200 and created a dag_run -- but its
-- state stayed "queued" indefinitely, since the scheduler never runs a
-- paused DAG's tasks regardless of how the run was created. No error is
-- surfaced anywhere. FIX/lesson: if a dag_run seems permanently stuck at
-- queued, check GET /dags/{dag_id}'s is_paused field before assuming
-- anything else is wrong.


-- =============================================================================
-- GOTCHA #3 (verified live): deleting a Composer environment does NOT
-- delete its GCS bucket
-- =============================================================================
-- After composer_client.delete_environment(...).result() completed (the
-- Environment resource confirmed gone via a subsequent describe call
-- returning NOT_FOUND), the environment's own GCS bucket
-- (gs://REGION-ENV_NAME-HASH-bucket/, containing dags/logs/data/plugins)
-- was still present and listable. Small (under 1KB for this notebook's own
-- usage) but not free and not automatically cleaned up -- delete it
-- separately if desired (a commented-out cell is provided; not run
-- automatically, matching this project's practice of leaving genuinely
-- optional extra teardown steps opt-in).


-- =============================================================================
-- Verified live end-to-end execution result:
-- =============================================================================
-- run_ga4_churn_kfp_pipeline (RunPipelineJobOperator) -> SUCCESS. The
-- underlying Vertex PipelineJob it triggered ("airflow-triggered-ga4-churn-
-- pipeline") independently confirmed PIPELINE_STATE_SUCCEEDED via
-- aiplatform.PipelineJob.list()/.task_details -- bigquery-create-model-job
-- -> bigquery-evaluate-model-job -> check-quality-gate -> condition-1
-- TRIGGERED -> bigquery-predict-model-job, all SUCCEEDED. Confirmed
-- independently rather than trusting the Airflow task's own "success"
-- status alone -- the same live-verification standard as every other
-- Phase 8 pipeline.


-- =============================================================================
-- Cleanup
-- =============================================================================
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.ga4_churn_pipeline_model`;
-- DROP TABLE IF EXISTS `PROJECT_ID.DATASET.ga4_churn_pipeline_features`;
-- Delete both DAG files (this notebook's and pipelines/composer_airflow/'s)
-- from the shared environment's DAG bucket.
-- composer_client.delete_environment(...) -- the REAL shared-environment
-- teardown lives here (this is the second/last notebook run against it).
-- Optional: also delete the now-orphaned Composer GCS bucket (see gotcha #3).
-- Compiled pipeline spec under gs://BUCKET/bq_ml/airflow_with_kfp/ and Vertex
-- Pipeline run history are left in place, same as pipelines/vertex_kfp/.
