-- Cloud Composer / Airflow — BigQuery ML Pipeline
-- =============================================================
-- The same drift-check -> conditional-retrain -> report logic as
-- pipelines/sql_scripting/, pipelines/scheduled_queries/, and
-- pipelines/cloud_workflows/, re-expressed as a real Apache Airflow DAG on a
-- live Cloud Composer 3 environment -- BigQueryInsertJobOperator for every
-- BigQuery job, BranchPythonOperator + XCom for the conditional retrain, and
-- a join task with trigger_rule=NONE_FAILED_MIN_ONE_SUCCESS so the DAG
-- completes cleanly regardless of which branch ran.
--
-- Workflow operationalized: ../../workflows/ga4_churn_prediction/
-- Data: bigquery-public-data.ga4_obfuscated_sample_ecommerce
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   Cloud Composer 3 overview: https://docs.cloud.google.com/composer/docs/composer-3/composer-overview
--   BigQueryInsertJobOperator: https://airflow.apache.org/docs/apache-airflow-providers-google/stable/operators/cloud/bigquery.html
--   MLOps/Serving/Batch/Orchestrating Batch Inference With Airflow.ipynb -- this repo's deeper Composer 2 precedent


-- =============================================================================
-- Cloud Composer 3 environment config -- the actual cost lever
-- =============================================================================
-- environments.Environment(
--   config=environments.EnvironmentConfig(
--     software_config=environments.SoftwareConfig(image_version='composer-3-airflow-2.11.1-build.11'),
--     node_config=environments.NodeConfig(service_account=COMPUTE_DEFAULT_SA),
--     environment_size=EnvironmentSize.ENVIRONMENT_SIZE_SMALL,
--     workloads_config=environments.WorkloadsConfig(
--       scheduler=SchedulerResource(cpu=0.5, memory_gb=2, storage_gb=1, count=1),
--       web_server=WebServerResource(cpu=0.5, memory_gb=2, storage_gb=1),
--       worker=WorkerResource(cpu=0.5, memory_gb=2, storage_gb=1, min_count=1, max_count=1),
--       triggerer=TriggererResource(cpu=0.5, memory_gb=1, count=1),
--       dag_processor=DagProcessorResource(cpu=0.5, memory_gb=2, storage_gb=1, count=1),
--     ),
--   ),
-- )
-- Composer 3 adds this explicit per-component workloads_config (vs. Composer
-- 2's single node_config) -- billed in DCU-hours (~$0.06/DCU-hour in
-- us-central1), the actual "cheaper than Composer 2" mechanism.


-- =============================================================================
-- dag_ga4_churn_pipeline.py -- reproduced in full in the notebook
-- =============================================================================
-- check_drift (BigQueryInsertJobOperator, ML.VALIDATE_DATA_DRIFT) ->
-- branch_on_drift (BranchPythonOperator, reads check_drift's job_id via
--   BigQueryHook + XCom) ->
--   [drift path] get_prior_metric -> retrain_model -> get_new_metric ->
--     report_drift_retrain (PythonOperator) -> pipeline_complete
--   [no-drift path] no_drift (EmptyOperator) -> pipeline_complete
-- pipeline_complete: EmptyOperator, trigger_rule=NONE_FAILED_MIN_ONE_SUCCESS
--
-- BigQueryInsertJobOperator.execute() returns the job's job_id as its XCom
-- value (not row data) -- reading actual query results back into Airflow
-- uses BigQueryHook().get_job(job_id=...).result() inside a PythonOperator.


-- =============================================================================
-- GOTCHA #1 (verified live): webserver readiness lags environment RUNNING,
-- and restarts periodically at floor resources
-- =============================================================================
-- Right after the Environment resource reports RUNNING, the Airflow
-- webserver itself is often still starting -- API calls may 502 for a few
-- extra minutes (DAG processor/scheduler are ready sooner, confirmed via
-- Cloud Logging: DAGs parsed with 0 errors while the webserver was still
-- printing "Starting the process, got command: webserver"). With web_server
-- floored at cpu=0.5/memory_gb=2 (no replica), the webserver process itself
-- restarted several times over a ~25 min session (~every 10-15 min,
-- confirmed via repeated "Starting gunicorn" log timestamps) -- each causes
-- a brief window of non-200s, while the scheduler and in-progress task
-- instances are completely unaffected. A first retry budget (6 retries x
-- 15s ~ 90s) genuinely wasn't enough -- a real run hit a restart window that
-- outlasted it and crashed on resp.json() when the retry loop returned a
-- non-200 response with an empty body. FIX: retry longer (12 x 20s ~ 4 min)
-- and check resp is not None and resp.status_code == 200 before parsing
-- JSON anywhere, not just at the first call site.


-- =============================================================================
-- GOTCHA #2 (verified live): the documented CLI path is much slower than
-- the direct REST API
-- =============================================================================
-- `gcloud composer environments run ENV --location REGION dags list` took
-- over 10 minutes to return anything useful in this session (it spins up
-- its own temporary execution context). Direct Airflow REST API calls via
-- google.auth.transport.requests.AuthorizedSession (once the webserver is
-- actually up) are far faster and more scriptable -- used throughout instead.


-- =============================================================================
-- Verified live end-to-end execution result:
-- =============================================================================
-- Drift detected in 5/12 features (total_engagement_time_msec strongest),
-- same Black-Friday-driven population shift as every other Phase 8 pipeline.
-- branch_on_drift routes to the retrain path; no_drift shows SKIPPED (real
-- proof BranchPythonOperator diverts execution, not just returns a value).
-- roc_auc before/after retrain: 0.7515 -> 0.7697. pipeline_complete succeeds
-- despite one skipped upstream branch, confirming trigger_rule works.
-- get_prior_metric/get_new_metric confirmed cache_hit: false via
-- INFORMATION_SCHEMA.JOBS_BY_PROJECT -- useQueryCache: False (a real Python
-- bool) works correctly here, unlike the KFP components' bug in
-- pipelines/vertex_kfp/ (BigQueryInsertJobOperator submits jobs through the
-- standard google-cloud-bigquery client's QueryJob.from_api_repr(), not the
-- custom JSON-cleanup logic that silently drops False in that other library).


-- =============================================================================
-- Cleanup
-- =============================================================================
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.ga4_churn_pipeline_model`;
-- DROP TABLE IF EXISTS `PROJECT_ID.DATASET.ga4_churn_pipeline_features`;
-- Delete this notebook's own DAG file from the shared environment's DAG bucket.
-- Leave the Composer environment running if pipelines/airflow_with_kfp/ runs
-- next in the same session -- that notebook performs the real environment
-- deletion in its own Cleanup section.
