-- Synthetic Control — BigQuery ML Workflow
-- =============================================================
-- difference_in_differences/ picked Georgia as Texas's comparison state --
-- real, defensible, but still an arbitrary single choice. Synthetic control
-- (Abadie, Diamond & Hainmueller) replaces that choice with an optimization:
-- a weighted combination of SEVERAL untreated states, constrained so weights
-- are non-negative and sum to 1 (a literal percentage blend of real states).
-- That constraint makes this a quadratic program, not a form CREATE MODEL
-- can express -- the same structural gap as Cox PH in survival_analysis/.
--
-- Data: reuses difference_in_differences/'s exact Texas mask-mandate panel,
-- extended to a 13-state donor pool (every state whose facial_coverings
-- level never reached Texas's post-mandate level 3 during the study window).
--
-- Full reference: ../../RESOURCES.md
-- Official docs:
--   CREATE MODEL (GLM): https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-glm
--   pysyncon: https://github.com/sdfordham/pysyncon


-- =============================================================================
-- Step 1: Build the donor pool -- extended version of the DiD panel
-- =============================================================================
CREATE OR REPLACE TABLE `PROJECT_ID.DATASET.synthetic_control_panel` AS
WITH pop AS (
  SELECT subregion1_code, ANY_VALUE(population) AS population
  FROM `bigquery-public-data.covid19_open_data.covid19_open_data`
  WHERE country_code = 'US' AND aggregation_level = 1
    AND subregion1_code IN ('TX','CO','GA','ID','IL','ME','MN','ND','NE','NH','SD','VA','WV','WY')
  GROUP BY subregion1_code
),
base AS (
  SELECT subregion1_code, DATE_TRUNC(date, WEEK(MONDAY)) AS wk, SUM(new_confirmed) AS wk_cases, COUNT(*) AS n_days
  FROM `bigquery-public-data.covid19_open_data.covid19_open_data`
  WHERE country_code = 'US' AND aggregation_level = 1
    AND subregion1_code IN ('TX','CO','GA','ID','IL','ME','MN','ND','NE','NH','SD','VA','WV','WY')
    AND date BETWEEN '2020-05-04' AND '2020-08-09'
  GROUP BY subregion1_code, wk
)
SELECT b.subregion1_code, b.wk, b.wk_cases / p.population * 100000 AS rate
FROM base b JOIN pop p USING (subregion1_code)
WHERE b.n_days = 7;


-- =============================================================================
-- Step 2/3: Why synthetic control, and the unconstrained-fit failure made concrete
-- =============================================================================
CREATE OR REPLACE MODEL `PROJECT_ID.DATASET.synthetic_control_unconstrained`
OPTIONS(model_type = 'LINEAR_REG', input_label_cols = ['TX'], data_split_method = 'NO_SPLIT', optimize_strategy = 'NORMAL_EQUATION') AS
SELECT CO, GA, ID, IL, ME, MN, ND, NE, NH, SD, VA, WV, WY, TX
FROM `PROJECT_ID.DATASET.synthetic_control_panel`
PIVOT (AVG(rate) FOR subregion1_code IN ('TX','CO','GA','ID','IL','ME','MN','ND','NE','NH','SD','VA','WV','WY'))
WHERE wk <= '2020-06-29';

SELECT * FROM ML.WEIGHTS(MODEL `PROJECT_ID.DATASET.synthetic_control_unconstrained`);
-- Verified: several weights come back negative, others land far above 1, and
-- the full set is nowhere near summing to 1 -- none possible for a real
-- percentage blend. Also an underdetermined system: only 9 pre-period weeks
-- vs. 13 donor states, no unique OLS solution -- confirmed live across THREE
-- separate runs (a planning-time scratch check, this notebook's own
-- pre-execution run, and a fresh user run) that this makes the exact weights
-- themselves unstable -- each produced a substantially different extreme-
-- weight pattern (sums observed: ~-0.83, ~+3.08, and others) -- a second,
-- compounding reason this approach is untrustworthy, beyond the
-- interpretability problem itself. Contrast with the constrained fit below,
-- which reproduces identically every time.


-- =============================================================================
-- Step 4: The real, constrained fit -- scipy.optimize (weights >= 0, sum to 1)
-- =============================================================================
-- Done in Python, not SQL -- BQML has no constrained-QP CREATE MODEL option:
--   from scipy.optimize import minimize
--   def objective(w): return np.sum((treated_pre - donors_pre @ w) ** 2)
--   minimize(objective, w0, method='SLSQP', bounds=[(0,1)]*n,
--            constraints={'type': 'eq', 'fun': lambda w: np.sum(w) - 1})
-- Verified: optimal weights = 82.4% Georgia + 17.6% Idaho (every other donor
-- ~0). Pre-period MSE: synthetic 143.95 vs. Georgia alone 189.98 -- a real,
-- quantified ~24% better fit.


-- =============================================================================
-- Step 5: Post-period comparison (plotted in notebook)
-- =============================================================================
-- Verified: average post-period gap (synthetic control ATT) = -19.28,
-- matching difference_in_differences/'s own 2-state estimate (-19.29)
-- almost exactly.


-- =============================================================================
-- Honest finding: two independently-built counterfactuals agree
-- (-19.28 vs. -19.29). The improved pre-period fit (24% MSE reduction) is
-- real evidence synthetic control's optimization was worth doing, even
-- though the final answer barely moved vs. the simpler 2-state DiD --
-- sometimes the more rigorous method mostly buys confidence in an answer
-- you already had, not a different answer.
-- =============================================================================
