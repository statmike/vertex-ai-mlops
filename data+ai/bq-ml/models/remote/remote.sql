-- REMOTE (Custom Vertex AI Endpoint) — Progressive SQL Examples (BigQuery ML)
-- =============================================================
-- A remote model registers an external prediction service -- here, a
-- custom model deployed to a Vertex AI Endpoint -- as a BigQuery ML model,
-- so it can be queried in-warehouse with ML.PREDICT. Unlike models/imported/,
-- the model runs on the ENDPOINT's infrastructure, not inside BigQuery --
-- any framework, any size, GPUs if needed. This is the full round trip:
-- train in BQML -> EXPORT MODEL -> deploy to a Vertex AI Endpoint -> call
-- it back from BigQuery with REMOTE WITH CONNECTION.
--
-- REAL, SMALL DOLLAR COST while the Endpoint is deployed (verified ~a few
-- minutes on the smallest general-purpose machine type for this example --
-- undeploy/delete the Endpoint promptly once done, see Cleanup).
--
-- Data: bigquery-public-data.ml_datasets.census_adult_income (same
--       feature/label set as models/logistic_regression/ and
--       models/export/) -- a small LOGISTIC_REG, exported and deployed.
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   CREATE MODEL (remote, custom endpoint): https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-remote-model-https
--   Cloud Resource Connection:              https://cloud.google.com/bigquery/docs/create-cloud-resource-connection
--   ML.PREDICT:                             https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-predict


-- =============================================================================
-- Example 1: Train + EXPORT MODEL (see models/export/ for the deep dive)
-- =============================================================================
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.remote_source_logistic_regression`
OPTIONS(
  model_type = 'LOGISTIC_REG',
  input_label_cols = ['income_bracket'],
  auto_class_weights = TRUE
) AS
SELECT
  age, workclass, education, education_num, marital_status, occupation,
  relationship, race, sex, hours_per_week, native_country, income_bracket
FROM `bigquery-public-data.ml_datasets.census_adult_income`;

EXPORT MODEL `PROJECT_ID.DATASET.remote_source_logistic_regression`
OPTIONS (URI = 'gs://BUCKET/bq_ml/remote/tf_export/1');

-- Deploy the export to a Vertex AI Endpoint with a pre-built TF-serving
-- container (aiplatform.Model.upload + .deploy() -- Python, not SQL; see
-- the notebook's Step 2). Note this is the ONLY step in this file that
-- costs real money and needs teardown.


-- =============================================================================
-- Example 2 (attempted, does NOT currently work): the native shortcut
-- =============================================================================
-- CREATE MODEL ... model_registry='VERTEX_AI' registers a model directly to
-- Vertex AI Model Registry -- no EXPORT MODEL, no manual container. Google's
-- docs say this needs "no serving container" -- looks like it should replace
-- Example 1's manual export+upload entirely.
--
-- VERIFIED LIVE: it doesn't currently work for LOGISTIC_REG. BQML bakes a
-- full Sampled-Shapley explanationSpec into every model registered this way
-- (confirmed via `gcloud ai models describe` -- present unconditionally).
-- Deploying it fails with a GraphDef version mismatch in Vertex's automatic
-- explanation preprocessing:
--   InvalidArgument: 400 Error occurred in Explanation preprocessing. ValueError:
--   NodeDef mentions attr 'debug_name' not in Op<name=VarHandleOp...>
-- This is a confirmed, currently-open Google issue -- github.com/GoogleCloudPlatform/
-- vertex-ai-samples/issues/2723 -- closed "not planned." A manually-uploaded
-- model (Example 1) has no baked-in explanation spec, so it never hits this --
-- which is why this file uses the manual route as primary.
--
-- CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.remote_native_shortcut_demo`
-- OPTIONS(
--   model_type = 'LOGISTIC_REG',
--   input_label_cols = ['income_bracket'],
--   model_registry = 'VERTEX_AI',
--   vertex_ai_model_id = 'bq_ml_remote_native_shortcut_demo'
-- ) AS
-- SELECT
--   age, workclass, education, education_num, marital_status, occupation,
--   relationship, race, sex, hours_per_week, native_country, income_bracket
-- FROM `bigquery-public-data.ml_datasets.census_adult_income`;
-- (then aiplatform.Model(...).deploy(endpoint=scratch_endpoint, ...) -- fails;
-- pass an explicit endpoint= so the empty scratch Endpoint the SDK would
-- otherwise auto-create can be deleted immediately in a finally block --
-- verified live: omitting endpoint= leaves an orphaned Endpoint behind)


-- =============================================================================
-- Example 3: REMOTE isn't limited to BQML models
-- =============================================================================
-- REMOTE WITH CONNECTION doesn't care where the model came from -- it just
-- calls whatever's running on the endpoint. An XGBoost model trained
-- entirely OUTSIDE BigQuery (Python, no BQML import) registers to Vertex AI
-- Model Registry the same way, with a different pre-built container
-- (xgboost-cpu instead of tf2-cpu):
--   aiplatform.Model.upload(
--       artifact_uri='gs://BUCKET/bq_ml/remote/xgboost_external/',
--       serving_container_image_uri='us-docker.pkg.dev/vertex-ai/prediction/xgboost-cpu.2-1:latest',
--   )
-- Deploying it follows the identical Example 1/aiplatform.Model.deploy()
-- pattern -- not done here to avoid a second live billable endpoint; see
-- MLOps/Serving/SQL Inference/BQML Remote Model on Vertex AI Endpoint.ipynb
-- for that exact idea fully executed (there with a HuggingFace container).


-- =============================================================================
-- Example 4: Create the Cloud Resource Connection (required -- unlike
-- imported models or EXPORT MODEL, remote models NEED a connection)
-- =============================================================================
-- bq mk --connection --location=US --connection_type=CLOUD_RESOURCE \
--   --project_id=PROJECT_ID bq_ml_remote_demo
--
-- Grant the connection's auto-provisioned service account roles/aiplatform.user
-- (its serviceAccountId comes back from `bq show --connection`):
-- gcloud projects add-iam-policy-binding PROJECT_ID \
--   --member=serviceAccount:SERVICE_ACCOUNT --role=roles/aiplatform.user
--
-- GOTCHAS, both verified live: (1) `bq mk --connection` on an existing ID
-- fails with "Already Exists: Connection ..." (capitalized) -- check for
-- this case-insensitively, don't treat it as a hard failure. (2) IAM
-- propagation can take well over a minute even after the grant succeeds --
-- retry CREATE MODEL (Example 5) on a permission error rather than a single
-- fixed wait.


-- =============================================================================
-- Example 5: CREATE MODEL ... REMOTE WITH CONNECTION
-- =============================================================================
-- INPUT/OUTPUT is required for a custom endpoint (unlike the LLM/foundation
-- remote-model variants documented in ../bq-ai-functions/). Field NAMES
-- must match the endpoint's request/response field names exactly --
-- BigQuery wraps INPUT columns into the `instances` payload and unpacks
-- `predictions` back into OUTPUT columns.
--
-- Verified: the TF-serving container's response for this LOGISTIC_REG
-- export uses the same three field names the SavedModel signature itself
-- exposes (see models/export/ Step 2): income_bracket_probs (ARRAY<FLOAT64>),
-- income_bracket_values (ARRAY<STRING>), predicted_income_bracket (ARRAY<STRING>).
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.remote_logistic_regression`
INPUT(
  age FLOAT64, workclass STRING, education STRING, education_num FLOAT64,
  marital_status STRING, occupation STRING, relationship STRING, race STRING,
  sex STRING, hours_per_week FLOAT64, native_country STRING
)
OUTPUT(
  income_bracket_probs ARRAY<FLOAT64>,
  income_bracket_values ARRAY<STRING>,
  predicted_income_bracket ARRAY<STRING>
)
REMOTE WITH CONNECTION `PROJECT_ID.US.bq_ml_remote_demo`
OPTIONS(
  endpoint = 'https://us-central1-aiplatform.googleapis.com/v1/projects/PROJECT_ID/locations/us-central1/endpoints/ENDPOINT_ID'
);


-- =============================================================================
-- Example 6: ML.PREDICT — single/multi-row and batch table scoring
-- =============================================================================
-- ML.PREDICT is the ONLY supported lifecycle function for a remote model --
-- no ML.EVALUATE, no ML.EXPLAIN_PREDICT, no ML.FEATURE_INFO (the model
-- wasn't trained in BigQuery). remote_model_status reports per-row call
-- status -- NULL means success.
SELECT income_bracket, predicted_income_bracket, income_bracket_probs, remote_model_status
FROM ML.PREDICT(
  MODEL `PROJECT_ID.DATASET.remote_logistic_regression`,
  (SELECT income_bracket, age, workclass, education, education_num, marital_status,
          occupation, relationship, race, sex, hours_per_week, native_country
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   LIMIT 5)
);

-- Batch table scoring -- verified 0 remote_model_status errors across 200 rows.
SELECT COUNT(*) AS n, COUNTIF(remote_model_status IS NOT NULL) AS errors
FROM ML.PREDICT(
  MODEL `PROJECT_ID.DATASET.remote_logistic_regression`,
  (SELECT age, workclass, education, education_num, marital_status,
          occupation, relationship, race, sex, hours_per_week, native_country
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   LIMIT 200)
);


-- =============================================================================
-- Cleanup
-- =============================================================================
-- Undeploy + delete the Vertex AI Endpoint and Model FIRST (Python/aiplatform
-- SDK -- see the notebook), THEN:
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.remote_logistic_regression`;
-- DROP MODEL IF EXISTS `PROJECT_ID.DATASET.remote_source_logistic_regression`;
-- bq rm --connection --project_id=PROJECT_ID --location=US bq_ml_remote_demo
-- (delete the GCS export blobs, including the Example 3 XGBoost-external
-- artifact -- it lives under the same gs://BUCKET/bq_ml/remote/ prefix --
-- and delete its Vertex AI Model Registry entry via aiplatform.Model.delete(),
-- since it was registered but never deployed)
