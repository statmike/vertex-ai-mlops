-- Propensity Score Matching — BigQuery ML Workflow
-- =============================================================
-- Causal inference from observational data: does maternal smoking during
-- pregnancy affect birth weight, when mothers were never randomly assigned
-- to smoke? LOGISTIC_REG trains the propensity model (P(treatment |
-- covariates)); everything else -- matching, weighting, balance checks,
-- effect estimation -- is plain SQL.
--
-- Data: bigquery-public-data.samples.natality, year 2005 (real, non-synthetic
--       US birth-certificate data; already used elsewhere in this project for
--       models/automl_regressor/).
--
-- GOTCHA: two earlier dataset candidates were tried and rejected after live
-- verification. thelook_ecommerce/ga4_obfuscated_sample_ecommerce (a
-- marketing-channel "treatment") showed essentially flat covariates/outcomes
-- across channels -- no real confounding baked into that synthetic data.
-- bigquery-public-data.cms_synthetic_patient_data_omop (metformin vs.
-- glyburide, the textbook pharmacoepi PSM example) looked ideal on paper,
-- but live queries showed the *synthetic* OMOP data doesn't encode the
-- real-world "confounding by indication" story either: covariates were
-- nearly identical between drug groups, mortality was far too rare to use
-- (5 deaths per ~135K-person group), and even new-onset hypoglycemia (the
-- actual textbook sulfonylurea-vs-metformin safety difference) showed no
-- real difference. Natality is real administrative data, and both the
-- confounding and the effect are genuinely present and verifiable in it.
--
-- GOTCHA: the sample seed for the cohort query originally hashed on this
-- table's `day` column. `day` is NULL for every single row in 2005 (a real
-- de-identification/privacy suppression in the source data) -- CONCAT's
-- NULL-propagation silently zeroed out the entire cohort. Fixed by hashing
-- only on columns confirmed non-null first.
--
-- GOTCHA: BigQuery rejects a correlated subquery referencing a table inside
-- a JOIN ... ON predicate ("Unsupported subquery with table in join
-- predicate") -- computing the caliper as (SELECT caliper FROM
-- caliper_value) directly inside the join below fails outright. Fixed by
-- computing the caliper as its own query first and substituting the
-- literal value into the join (shown below as a hardcoded example value;
-- the notebook computes and substitutes it live).
--
-- GOTCHA: a direct inequality self-join for nearest-neighbor matching
-- (JOIN ... ON ABS(a.propensity_score - b.propensity_score) <= caliper) at
-- full population scale (hundreds of thousands x millions of rows) blew
-- through BigQuery on-demand's CPU-to-bytes-billed ratio limit ("Query
-- exceeded resource limits") even though the output was tiny. Fixed with
-- sample-size discipline, not a query trick: Step 1's cohort is sized so
-- this self-join is cheap and direct. At larger scale, bucket the
-- propensity score into caliper-width bins and join on bucket equality (a
-- cheap equi-join) before refining to the true nearest neighbor.
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   CREATE MODEL (GLM): https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-glm
--   ML.PREDICT:         https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-predict


-- =============================================================================
-- Step 1: Build the cohort -- treatment, covariates, outcome, deterministic sample
-- =============================================================================
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.psm_cohort` AS
SELECT
  ROW_NUMBER() OVER() AS row_id,
  treatment, mother_age, mother_married, mother_race, weight_gain_pounds, weight_pounds, low_birth_weight
FROM (
  SELECT
    IF(cigarette_use, 1, 0) AS treatment,
    mother_age,
    IF(mother_married, 1, 0) AS mother_married,
    CAST(mother_race AS STRING) AS mother_race,  -- cast: integer-coded categorical, not ordinal
    weight_gain_pounds,
    weight_pounds,
    IF(weight_pounds < 5.5, 1, 0) AS low_birth_weight
  FROM `bigquery-public-data.samples.natality`
  WHERE year = 2005
    AND cigarette_use IS NOT NULL
    AND weight_pounds IS NOT NULL
    AND mother_age IS NOT NULL
    AND weight_gain_pounds IS NOT NULL
    AND mother_race IS NOT NULL
    AND MOD(ABS(FARM_FINGERPRINT(CONCAT(
          CAST(source_year AS STRING), '-', CAST(month AS STRING), '-', CAST(wday AS STRING), '-',
          CAST(mother_age AS STRING), '-', CAST(weight_pounds AS STRING), '-', CAST(weight_gain_pounds AS STRING)
        ))), 1000) < 15
);
-- Verified: 3,604 treated (smokers) / 30,428 control (non-smokers).


-- =============================================================================
-- Step 2: Naive comparison -- show the confounding before any correction
-- =============================================================================
SELECT
  treatment,
  COUNT(*) AS n,
  ROUND(AVG(mother_age), 2) AS avg_mother_age,
  ROUND(AVG(mother_married), 3) AS married_rate,
  ROUND(AVG(weight_gain_pounds), 2) AS avg_weight_gain,
  ROUND(AVG(weight_pounds), 4) AS avg_birth_weight,
  ROUND(AVG(low_birth_weight), 4) AS low_birth_weight_rate
FROM `PROJECT_ID.DATASET.psm_cohort`
GROUP BY 1
ORDER BY 1;
-- Verified: smokers are younger (~25.3 vs ~27.8 avg age) and far less often
-- married (~36% vs ~66%) -- real imbalance. Naive birth-weight effect: ~-0.40 lbs.


-- =============================================================================
-- Step 3: Propensity model (LOGISTIC_REG predicts TREATMENT, not outcome) + score
-- =============================================================================
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.psm_propensity_model`
OPTIONS(
  model_type = 'LOGISTIC_REG',
  input_label_cols = ['treatment'],
  data_split_method = 'AUTO_SPLIT'
) AS
SELECT mother_age, mother_married, mother_race, weight_gain_pounds, treatment
FROM `PROJECT_ID.DATASET.psm_cohort`;

SELECT * FROM ML.EVALUATE(MODEL `PROJECT_ID.DATASET.psm_propensity_model`);
-- Verified: roc_auc ~0.70 (real signal). precision/recall/f1 show as 0.0 --
-- expected artifact of the default 0.5 threshold under class imbalance
-- (~10-11% treated), irrelevant for propensity scoring (only the raw
-- predicted probability is used downstream).

CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.psm_scored` AS
SELECT
  row_id, treatment, mother_age, mother_married, mother_race, weight_gain_pounds, weight_pounds, low_birth_weight,
  (SELECT prob FROM UNNEST(predicted_treatment_probs) WHERE label = 1) AS propensity_score
FROM ML.PREDICT(
  MODEL `PROJECT_ID.DATASET.psm_propensity_model`,
  TABLE `PROJECT_ID.DATASET.psm_cohort`
);


-- =============================================================================
-- Step 4: Nearest-neighbor matching with replacement, within a caliper
-- =============================================================================
-- Step 4a: compute the caliper as its own query first (0.1 x SD of the propensity score)
SELECT STDDEV(propensity_score) * 0.1 AS caliper
FROM `PROJECT_ID.DATASET.psm_scored`;
-- Verified: ~0.007370. Substitute the literal value into the join below --
-- a correlated subquery-in-JOIN-predicate is not supported (see gotcha above).

-- Step 4b: nearest-neighbor match within the caliper, using the literal from 4a
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.psm_matched` AS
WITH treated AS (
  SELECT row_id, propensity_score, mother_age, mother_married, weight_pounds
  FROM `PROJECT_ID.DATASET.psm_scored` WHERE treatment = 1
),
control AS (
  SELECT row_id, propensity_score, mother_age, mother_married, weight_pounds
  FROM `PROJECT_ID.DATASET.psm_scored` WHERE treatment = 0
),
candidates AS (
  SELECT
    t.row_id AS treated_row_id,
    c.row_id AS control_row_id,
    ABS(t.propensity_score - c.propensity_score) AS prop_diff,
    t.weight_pounds AS treated_outcome, c.weight_pounds AS control_outcome,
    t.mother_age AS t_age, c.mother_age AS c_age,
    t.mother_married AS t_married, c.mother_married AS c_married
  FROM treated t
  JOIN control c ON ABS(t.propensity_score - c.propensity_score) <= 0.007370  -- literal from Step 4a
)
SELECT *
FROM candidates
QUALIFY ROW_NUMBER() OVER (PARTITION BY treated_row_id ORDER BY prop_diff) = 1;

SELECT
  COUNT(*) AS n_matched_pairs,
  COUNT(DISTINCT control_row_id) AS n_distinct_controls_reused,
  ROUND(AVG(t_age), 2) AS matched_treated_age, ROUND(AVG(c_age), 2) AS matched_control_age,
  ROUND(AVG(t_married), 3) AS matched_treated_married, ROUND(AVG(c_married), 3) AS matched_control_married,
  ROUND(AVG(treated_outcome), 4) AS matched_treated_bw, ROUND(AVG(control_outcome), 4) AS matched_control_bw
FROM `PROJECT_ID.DATASET.psm_matched`;
-- Verified: all 3,604 treated units matched (full caliper coverage). Age gap
-- shrinks from ~2.5 to ~0.14; married-rate gap shrinks from ~0.30 to ~0.004
-- (both robust across reruns). Matched effect: ~-0.40 lbs, but LOGISTIC_REG's
-- AUTO_SPLIT randomizes the train/eval split on every retrain, so the exact
-- value (and even whether it lands closer to or further from naive) shifts
-- run to run -- don't treat this as a fixed constant.


-- =============================================================================
-- Step 5: Inverse Probability of Treatment Weighting (IPTW) -- a second method
-- =============================================================================
WITH weighted AS (
  SELECT
    treatment, weight_pounds,
    IF(treatment = 1, 1 / propensity_score, 1 / (1 - propensity_score)) AS iptw_weight
  FROM `PROJECT_ID.DATASET.psm_scored`
)
SELECT
  treatment,
  COUNT(*) AS n,
  ROUND(MAX(iptw_weight), 2) AS max_weight,
  ROUND(SUM(weight_pounds * iptw_weight) / SUM(iptw_weight), 4) AS iptw_weighted_birth_weight
FROM weighted
GROUP BY 1
ORDER BY 1;
-- Verified: IPTW effect ~-0.43 lbs (also subject to the same AUTO_SPLIT
-- non-determinism noted above). Max weight in the treated group is ~66 --
-- a known IPTW instability (a low-propensity smoker dominates the weighted
-- average) worth flagging alongside the estimate, not hiding.


-- =============================================================================
-- Honest finding: naive / matched / IPTW effect estimates all land in a
-- narrow band (roughly -0.40 to -0.43 lbs, exact values shift run to run
-- due to LOGISTIC_REG's AUTO_SPLIT randomization -- see gotchas above). The
-- measured confounders here are real and imbalanced but are not the
-- dominant driver of the naive birth-weight gap -- the smoking effect looks
-- robust to adjusting for them. PSM only corrects for MEASURED confounders;
-- unmeasured ones (e.g. detailed socioeconomic status, prenatal care
-- access) could still bias every estimate above.
-- =============================================================================
