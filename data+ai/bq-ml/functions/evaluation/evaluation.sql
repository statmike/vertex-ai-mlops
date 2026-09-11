-- Evaluation Without A Model -- Progressive SQL Examples (BigQuery ML model-free functions)
-- =============================================================
-- ML.METRICS computes evaluation metrics from a relation that already holds an
-- actual column and a predicted column. There is no model argument. Nothing is
-- trained, nothing is loaded, and the predictions can come from anywhere --
-- BigQuery ML, Vertex AI batch prediction, a vendor scoring API, a CSV someone
-- emailed you. Preview as of 2026-09-10.
--
-- Signature:
--   ML.METRICS({TABLE t | (QUERY_STATEMENT)},
--              predicted_col => 'name',
--              actual_col    => 'name',
--              task_type     => 'regression' | 'classification')
--
-- Returns (regression):     mean_absolute_error, mean_squared_error,
--                           mean_squared_log_error, median_absolute_error,
--                           r2_score, explained_variance
-- Returns (classification): precision, recall, accuracy, f1_score
--
-- The predicted and actual columns must share a type. Rows where either is NULL
-- are dropped before anything is computed.
--
-- WHY THIS EXISTS: ML.EVALUATE needs the model object. ML.METRICS needs only the
-- numbers. Example 2 drops the model and shows ML.EVALUATE failing with
-- "Not found: Model ..." while ML.METRICS returns the identical six metrics from
-- the saved prediction table.
--
-- GOTCHA the column TYPE silently changes what precision/recall/f1_score mean.
-- BOOL actual/predicted is scored as binary -- the positive (TRUE) class only.
-- The STRING equivalents of the same values are scored as multiclass and
-- macro-averaged over both classes. Example 4 measures it on one table: the
-- identical 62 predictions score precision 0.5238 as BOOL and 0.7497 as STRING.
-- Neither number is wrong; they answer different questions. On balanced data the
-- two agree, which is how this hides until the day it matters.
--
-- GOTCHA the same convention holds in AI.EVALUATE's TabFM branch -- measured, not
-- assumed (Example 5). This is a BigQuery-wide evaluation convention, not an
-- ML.METRICS quirk.
--
-- GOTCHA the (QUERY_STATEMENT) form fails on some relations with internal error
-- 80038528 while the TABLE form of the very same data succeeds. Example 6
-- documents the boundary that was actually measured, and the workaround:
-- materialize, then pass TABLE.
--
-- Data: bigquery-public-data.ml_datasets.penguins, filtered and split
--       deterministically with FARM_FINGERPRINT, so the TRAIN/TEST membership is
--       identical on every run and in every project -- the same dataset used by
--       models/linear_regression/. The classification metrics below reproduce
--       exactly; the regression ones move in their last digit or two, because
--       CREATE MODEL is not bit-deterministic (see Example 2).
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   ML.METRICS:  https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-metrics
--   ML.EVALUATE: https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-evaluate


-- =============================================================================
-- Setup: a deterministically split table
-- =============================================================================
-- The split is a hash of the row's own values, not RAND() and not a row number,
-- so the TRAIN/TEST membership is identical on every run and in every project.
-- 271 TRAIN rows, 62 TEST rows.
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.evaluation_penguins` AS
SELECT
  species, island, culmen_length_mm, culmen_depth_mm, flipper_length_mm, sex, body_mass_g,
  IF(MOD(ABS(FARM_FINGERPRINT(FORMAT('%s|%s|%t|%t|%t|%s|%t',
       species, island, culmen_length_mm, culmen_depth_mm, flipper_length_mm, sex, body_mass_g))), 5) = 0,
     'TEST', 'TRAIN') AS splits
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE');


-- =============================================================================
-- Example 1: The ordinary path -- train, predict, ML.EVALUATE
-- =============================================================================
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.evaluation_scratch_reg`
OPTIONS(
  model_type = 'LINEAR_REG',
  input_label_cols = ['body_mass_g'],
  data_split_method = 'NO_SPLIT',
  category_encoding_method = 'DUMMY_ENCODING'
) AS
SELECT species, island, culmen_length_mm, culmen_depth_mm, flipper_length_mm, sex, body_mass_g
FROM `PROJECT_ID.DATASET.evaluation_penguins`
WHERE splits = 'TRAIN';

-- Save the predictions. This table is the only thing ML.METRICS will need later.
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.evaluation_predictions` AS
SELECT
  body_mass_g AS actual_mass,
  predicted_body_mass_g AS predicted_mass
FROM ML.PREDICT(
  MODEL `PROJECT_ID.DATASET.evaluation_scratch_reg`,
  (SELECT * FROM `PROJECT_ID.DATASET.evaluation_penguins` WHERE splits = 'TEST'));

-- The familiar, model-bound way to score:
SELECT * FROM ML.EVALUATE(
  MODEL `PROJECT_ID.DATASET.evaluation_scratch_reg`,
  (SELECT * FROM `PROJECT_ID.DATASET.evaluation_penguins` WHERE splits = 'TEST'));
-- mean_absolute_error       254.33286710645913
-- mean_squared_error        100255.15083462212
-- mean_squared_log_error    0.0064085793751867091
-- median_absolute_error     192.29450220322906
-- r2_score                  0.85808135142145281
-- explained_variance        0.85913462037336985
--
-- These are one run's values, printed at full precision on purpose. Retraining
-- moves the last digit or two -- CREATE MODEL is not bit-deterministic -- so
-- compare yours to ~13 significant digits, not to the last one.


-- =============================================================================
-- Example 2: Delete the model. ML.EVALUATE dies; ML.METRICS does not.
-- =============================================================================
DROP MODEL `PROJECT_ID.DATASET.evaluation_scratch_reg`;

-- This now fails: "Not found: Model PROJECT_ID:DATASET.evaluation_scratch_reg"
SELECT * FROM ML.EVALUATE(
  MODEL `PROJECT_ID.DATASET.evaluation_scratch_reg`,
  (SELECT * FROM `PROJECT_ID.DATASET.evaluation_penguins` WHERE splits = 'TEST'));

-- This still works. Same six metrics, from the saved numbers alone.
SELECT * FROM ML.METRICS(
  TABLE `PROJECT_ID.DATASET.evaluation_predictions`,
  predicted_col => 'predicted_mass',
  actual_col    => 'actual_mass',
  task_type     => 'regression');
-- mean_absolute_error       254.33286710645919   <- ML.EVALUATE gave ...913
-- mean_squared_error        100255.15083462212
-- mean_squared_log_error    0.00640857937518671
-- median_absolute_error     192.29450220322906
-- r2_score                  0.85808135142145303  <- ML.EVALUATE gave ...281
-- explained_variance        0.85913462037336996  <- ML.EVALUATE gave ...985
--
-- Every metric agrees with ML.EVALUATE to at least 13 significant digits;
-- the relative gaps are around 1e-16. That is floating-point summation order
-- over a different physical plan, not a difference in definition.
--
-- Do not read anything into WHICH ones come back exactly equal -- it varies
-- between runs. The two functions sum the same numbers in different orders, and
-- CREATE MODEL is not bit-deterministic either, so the predictions themselves
-- move in their last digit. A 1e-16 gap here is noise; a 1e-3 gap would not be.


-- =============================================================================
-- Example 3: Regression metrics on predictions BigQuery never made
-- =============================================================================
-- The point of the function: nothing here mentions a model, a connection, or a
-- training run. Any two same-typed columns will do -- a Vertex AI batch
-- prediction output, a vendor scoring API's results loaded to a table, last
-- quarter's forecast archived next to what actually happened.
SELECT * FROM ML.METRICS(
  TABLE `PROJECT_ID.DATASET.evaluation_predictions`,
  predicted_col => 'predicted_mass',
  actual_col    => 'actual_mass',
  task_type     => 'regression');

-- Reproducible: three isolated runs with the query cache off returned
-- bit-identical values. ML.METRICS reads a table and does arithmetic; there is
-- no sampling and no model, so there is nothing to vary between runs.


-- =============================================================================
-- Example 4: Classification -- and the BOOL/STRING trap
-- =============================================================================
-- A deliberately imbalanced problem: is this penguin a Chinstrap? 12 of the 62
-- TEST rows are.
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.evaluation_scratch_clf`
OPTIONS(
  model_type = 'LOGISTIC_REG',
  input_label_cols = ['is_chinstrap'],
  data_split_method = 'NO_SPLIT',
  category_encoding_method = 'DUMMY_ENCODING'
) AS
SELECT island, culmen_depth_mm, body_mass_g,
       species = 'Chinstrap penguin (Pygoscelis antarctica)' AS is_chinstrap
FROM `PROJECT_ID.DATASET.evaluation_penguins`
WHERE splits = 'TRAIN';

-- One table, one set of predictions, stored twice: once as BOOL, once as the
-- STRING rendering of the very same values.
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.evaluation_classifications` AS
SELECT
  is_chinstrap                            AS actual_bool,
  predicted_is_chinstrap                  AS predicted_bool,
  CAST(is_chinstrap AS STRING)            AS actual_string,
  CAST(predicted_is_chinstrap AS STRING)  AS predicted_string
FROM ML.PREDICT(
  MODEL `PROJECT_ID.DATASET.evaluation_scratch_clf`,
  (SELECT island, culmen_depth_mm, body_mass_g,
          species = 'Chinstrap penguin (Pygoscelis antarctica)' AS is_chinstrap
   FROM `PROJECT_ID.DATASET.evaluation_penguins` WHERE splits = 'TEST'));

SELECT 'BOOL' AS label_type, * FROM ML.METRICS(
  TABLE `PROJECT_ID.DATASET.evaluation_classifications`,
  predicted_col => 'predicted_bool', actual_col => 'actual_bool',
  task_type => 'classification')
UNION ALL
SELECT 'STRING', * FROM ML.METRICS(
  TABLE `PROJECT_ID.DATASET.evaluation_classifications`,
  predicted_col => 'predicted_string', actual_col => 'actual_string',
  task_type => 'classification');
-- label_type  precision           recall              accuracy            f1_score
-- BOOL        0.5238095238095238  0.9166666666666666  0.8225806451612904  0.6666666666666666
-- STRING      0.7497096399535423  0.8583333333333334  0.8225806451612904  0.7728937728937728
--
-- Same rows. Same predictions. Precision reads 0.52 or 0.75 depending only on
-- whether the column is BOOL or STRING. accuracy is identical either way,
-- because accuracy has no per-class definition to average.

-- The confusion matrix behind both rows:
SELECT actual_bool, predicted_bool, COUNT(*) AS n
FROM `PROJECT_ID.DATASET.evaluation_classifications`
GROUP BY 1, 2 ORDER BY 1, 2;
-- false false 40 | false true 10 | true false 1 | true true 11
--
-- BOOL   -> the TRUE class alone:   precision 11/21 = 0.5238, recall 11/12 = 0.9167
-- STRING -> mean of the two classes:
--            "true":  precision 11/21 = 0.5238, recall 11/12 = 0.9167, F1 0.6667
--            "false": precision 40/41 = 0.9756, recall 40/50 = 0.8000, F1 0.8791
--            macro precision (0.5238 + 0.9756)/2 = 0.7497  <- matches exactly
--            macro F1        (0.6667 + 0.8791)/2 = 0.7729  <- mean of the F1s,
--                                                   not the F1 of the mean P/R
--
-- Which to use: BOOL when one class is the event you care about and the other is
-- background (fraud, churn, defect). STRING when the classes are peers and you
-- want a rare class to count as much as a common one. Choose deliberately --
-- do not let a CAST decide it.


-- =============================================================================
-- Example 5: The same convention in AI.EVALUATE -- measured, not assumed
-- =============================================================================
-- AI.EVALUATE's TabFM branch returns the same four classification metric names.
-- It takes data rather than predictions and trains internally, so its numbers
-- are its own -- but the BOOL/STRING convention is the question, and it is the
-- same convention. Four isolated runs of each returned identical values:
--
--   label column type   precision           recall  f1_score            accuracy
--   BOOL                0.5217391304347826  1.0     0.6857142857142857  0.8225806451612904
--   STRING              0.7608695652173914  0.89    0.7810593900481542  0.8225806451612904
--
-- TabFM's confusion matrix here is TP 12, FP 11, FN 0, TN 39 -- so BOOL reports
-- 12/23 and 12/12, the positive class alone, and STRING reports the two-class
-- mean of (0.5217, 1.0000) and (1.0000, 0.7800). Identical rule to ML.METRICS.
--
-- Do NOT put both label encodings in the relations you pass: each is a perfect
-- predictor of the other, and leaving the unused one in leaks the label.
SELECT * FROM AI.EVALUATE(
  (SELECT island, culmen_depth_mm, body_mass_g,
          species = 'Chinstrap penguin (Pygoscelis antarctica)' AS is_chinstrap
   FROM `PROJECT_ID.DATASET.evaluation_penguins` WHERE splits = 'TRAIN'),
  (SELECT island, culmen_depth_mm, body_mass_g,
          species = 'Chinstrap penguin (Pygoscelis antarctica)' AS is_chinstrap
   FROM `PROJECT_ID.DATASET.evaluation_penguins` WHERE splits = 'TEST'),
  label_col => 'is_chinstrap');


-- =============================================================================
-- Example 6: GOTCHA -- internal error 80038528 on the (QUERY_STATEMENT) form
-- =============================================================================
-- A natural thing to want: how much better is the model than predicting a
-- constant? Compute the baseline inline and score it.
SELECT * FROM ML.METRICS(
  (SELECT body_mass_g AS actual_mass, 4207.0 AS predicted_mass
   FROM `PROJECT_ID.DATASET.evaluation_penguins` WHERE splits = 'TEST'),
  predicted_col => 'predicted_mass', actual_col => 'actual_mass',
  task_type => 'regression');
-- An internal error occurred and the request could not be completed. ...
-- Error: 80038528
--
-- The message says "transient" and suggests retrying. It is not transient here:
-- the same statement fails the same way on every run.
--
-- The client libraries take the message at face value. internalError is on
-- google-cloud-bigquery's default retryable list, so a plain
-- client.query(sql).result() resubmits the job until its 600-second deadline --
-- 12 job attempts over 604 seconds, measured -- before raising. Pass
-- retry=None to client.query() and retry=None, job_retry=None to .result()
-- so the failure surfaces in seconds instead of minutes.

-- The workaround, reliable in every case tested: materialize, then pass TABLE.
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.evaluation_baseline` AS
SELECT body_mass_g AS actual_mass, 4207.0 AS predicted_mass
FROM `PROJECT_ID.DATASET.evaluation_penguins` WHERE splits = 'TEST';

SELECT * FROM ML.METRICS(
  TABLE `PROJECT_ID.DATASET.evaluation_baseline`,
  predicted_col => 'predicted_mass', actual_col => 'actual_mass',
  task_type => 'regression');

-- WHAT WAS ACTUALLY MEASURED, and what was ruled out.
-- The TABLE form succeeded on every relation tried (7 of 7), including every one
-- whose (QUERY_STATEMENT) form failed. The query form is the fragile one, and no
-- clean rule for when it breaks emerged. Ruled out by direct test:
--   * cross-project references -- bigquery-public-data.usa_names works in query
--     form; a copy of penguins inside the caller's own project still fails
--   * JOINs -- a join across two of the caller's own tables works
--   * NULLs in either column -- filtering both to NOT NULL does not help
--   * REQUIRED (NOT NULL) schema modes -- the failing copy has none
--   * row count -- a 62-row table works, a 150-row table fails, a 32,561-row
--     table works
--   * WHERE, LIMIT, and computed expressions -- present in both working and
--     failing cases
-- Observed failing: ml_datasets.penguins, ml_datasets.iris, a copy of penguins
-- in the caller's project, and evaluation_penguins above.
-- Observed working: ml_datasets.census_adult_income, usa_names.usa_1910_2013,
-- evaluation_predictions, and penguins wrapped in a GROUP BY.
-- No mechanism is claimed. The practical advice is the point: if the query form
-- errors, do not spend time reshaping the subquery -- materialize and use TABLE.


-- =============================================================================
-- Cleanup
-- =============================================================================
DROP MODEL IF EXISTS `PROJECT_ID.DATASET.evaluation_scratch_clf`;
DROP TABLE IF EXISTS `PROJECT_ID.DATASET.evaluation_baseline`;
DROP TABLE IF EXISTS `PROJECT_ID.DATASET.evaluation_classifications`;
DROP TABLE IF EXISTS `PROJECT_ID.DATASET.evaluation_predictions`;
DROP TABLE IF EXISTS `PROJECT_ID.DATASET.evaluation_penguins`;
-- evaluation_scratch_reg was already dropped in Example 2.
