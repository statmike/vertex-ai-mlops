# Propensity Score Matching — BigQuery ML

**Causal inference from observational data.** Every other workflow in this project predicts an outcome. This one asks a different kind of question: *did X actually cause Y* — when you can't run a randomized experiment and have to work with data where people weren't randomly assigned to a "treatment."

**Models used:** `LOGISTIC_REG`
**Functions used:** `ML.EVALUATE`, `ML.PREDICT`

**Data:** [`bigquery-public-data.samples.natality`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) — real (not synthetic) US birth-certificate records, year 2005. Already used elsewhere in this project for `models/automl_regressor` (`models/automl_regressor/`).

**References:** `RESOURCES.md` (Full reference) | [CREATE MODEL (GLM) docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-glm) | `setup` (Setup guide)

---

## The problem: you can't always randomize

Most of BigQuery ML is about *prediction* — given these features, what's the likely outcome? Propensity Score Matching (PSM) is about something different: *causal effect estimation* — did a specific intervention (a drug, a policy, a marketing campaign, a training program) actually change the outcome, or does it just *look* that way because of who ended up receiving it?

In a randomized controlled trial (RCT), you'd flip a coin to decide who gets the treatment, which guarantees the treated and untreated groups are comparable on average — any outcome difference must be caused by the treatment. Most real-world data isn't like this. People **self-select** or get **selected by others** into "treatment": doctors prescribe based on how sick a patient is, marketers target based on who looks like a good customer, students choose which school to attend. This creates **confounding** — the treatment group differs from the control group in ways that also affect the outcome, independent of the treatment itself — and a naive before/after or treated/untreated comparison will be biased.

**Propensity Score Matching** addresses this by:
1. Modeling the *propensity* to receive treatment — `P(treatment | covariates)` — using exactly the tool BigQuery ML already gives you for binary outcomes: `LOGISTIC_REG`.
2. Using that single number to find comparable treated/untreated pairs (or weights), so the compared groups look statistically similar on the covariates that predicted treatment — approximating what a randomized experiment would have looked like.
3. Comparing outcomes *within* that matched/weighted population, not the raw population.

It corrects for **measured** confounders only — a real, important limitation covered honestly in this notebook's finding section.

### Where this shows up across industries

PSM isn't a niche academic technique — it's used wherever a real experiment isn't possible or ethical:

| Industry | Example | Why an RCT wasn't used |
|---|---|---|
| **Healthcare / critical care** | Connors et al. (1996, *JAMA*) studied right-heart catheterization in ICU patients | Sicker patients were preferentially catheterized — comparing raw outcomes would unfairly blame the procedure for how sick its recipients already were |
| **Labor economics / public policy** | The LaLonde National Supported Work job-training study; Dehejia & Wahba (1999) showed PSM on observational comparison groups could approximate the original randomized-experiment effect | Building a full comparison RCT for every policy question is expensive/slow — PSM lets you validate against observational data instead |
| **Marketing / pharma sales** | Rubin & Waterman's propensity-score analysis of pharmaceutical sales-force effectiveness | Sales reps aren't randomly assigned to accounts — higher-potential accounts get more attention, confounding a naive comparison |
| **Education policy** | Catholic-school achievement studies (Morgan 2001; Reardon, Cheadle & Robinson 2009) | Families self-select into private schooling; those families often differ in motivation/resources independent of the school itself |
| **Legal / public policy** | Propensity-score methods used in tobacco litigation to estimate smoking's mortality effect from observational data | You cannot ethically randomize who smokes — the causal question has to be answered from the data people actually generated |

This notebook's own example — **does maternal smoking during pregnancy affect birth weight** — is one of the most widely taught illustrations of exactly this problem: nobody randomly assigns smoking, so the treated (smoking) and untreated (non-smoking) groups differ in real, measurable ways before you even look at the outcome.

---
## Setup

Set your project and location, authenticate, and create a shared dataset. No connection needed — this workflow only uses `LOGISTIC_REG` and plain SQL.

```python
PROJECT_ID = 'statmike-mlops-349915'  # <-- Replace with your project ID
LOCATION = 'US'  # BigQuery dataset location
DATASET_ID = 'bq_ml'  # Shared dataset across all bq-ml notebooks
```

### Environment

> **Already set up the project environment?** The cell below is a no-op — packages are already in your kernel. See the `setup` (Setup Reference) for details.
>
> **Running standalone** (Colab, Colab Enterprise, Vertex AI Workbench)? The cell below installs required packages into your current kernel.

```python
from google.cloud import bigquery
import pandas as pd

client = bigquery.Client(project=PROJECT_ID)
pd.set_option('display.max_colwidth', None)

# Create the shared dataset (idempotent)
dataset_ref = bigquery.DatasetReference(PROJECT_ID, DATASET_ID)
dataset = bigquery.Dataset(dataset_ref)
dataset.location = LOCATION
client.create_dataset(dataset, exists_ok=True)
print(f'Dataset {PROJECT_ID}.{DATASET_ID} ready')

# Register %%bigquery cell magic (auto-loaded in Colab, needed elsewhere)
%load_ext bigquery_magics
```

---
## Step 1 — Build the cohort: real patients, a real "treatment"

**Treatment:** `cigarette_use` — did the mother smoke during pregnancy? **Outcome:** `weight_pounds` — the baby's birth weight (plus a secondary binary `low_birth_weight` flag, <5.5 lbs). **Covariates:** `mother_age`, `mother_married`, `mother_race`, `weight_gain_pounds` during pregnancy — factors that plausibly affect *both* whether a mother smokes *and* the baby's birth weight.

Restricted to `year = 2005` (this dataset's cigarette-use reporting is well-populated in the mid-2000s) and a deterministic ~1.5% sample via `FARM_FINGERPRINT` — this keeps the propensity model, the matching self-join, and IPTW all fast and cheap on a full BigQuery on-demand project, while preserving the exact same confounding and outcome signal as the full ~2.3M-row population (verified separately; not shown here to keep this notebook self-contained). **Gotcha found live:** an earlier version of this cohort query hashed on the table's `day` column for the sample seed — `day` is `NULL` for every single 2005 row in this public dataset (a real de-identification/privacy suppression in the source data, not a bug), which silently zeroed out the entire cohort via `CONCAT`'s NULL-propagation. Fixed by hashing on columns confirmed non-null first.

```python
query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.psm_cohort` AS
SELECT
  ROW_NUMBER() OVER() AS row_id,
  treatment, mother_age, mother_married, mother_race, weight_gain_pounds, weight_pounds, low_birth_weight
FROM (
  SELECT
    IF(cigarette_use, 1, 0) AS treatment,
    mother_age,
    IF(mother_married, 1, 0) AS mother_married,
    CAST(mother_race AS STRING) AS mother_race,
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
    -- deterministic ~1.5% sample, hashed on columns verified non-null for this year
    AND MOD(ABS(FARM_FINGERPRINT(CONCAT(
          CAST(source_year AS STRING), '-', CAST(month AS STRING), '-', CAST(wday AS STRING), '-',
          CAST(mother_age AS STRING), '-', CAST(weight_pounds AS STRING), '-', CAST(weight_gain_pounds AS STRING)
        ))), 1000) < 15
)
"""
client.query(query).result()

query = f"""
SELECT treatment, COUNT(*) AS n
FROM `{PROJECT_ID}.{DATASET_ID}.psm_cohort`
GROUP BY 1
"""
client.query(query).to_dataframe()
```

---
## Step 2 — Show the confounding: why a naive comparison is biased

Compare the two groups' covariates *before* any correction. If `mother_age`/`mother_married` were similar between smokers and non-smokers, there'd be nothing for PSM to fix. They aren't.

```python
query = f"""
SELECT
  treatment,
  COUNT(*) AS n,
  ROUND(AVG(mother_age), 2) AS avg_mother_age,
  ROUND(AVG(mother_married), 3) AS married_rate,
  ROUND(AVG(weight_gain_pounds), 2) AS avg_weight_gain,
  ROUND(AVG(weight_pounds), 4) AS avg_birth_weight,
  ROUND(AVG(low_birth_weight), 4) AS low_birth_weight_rate
FROM `{PROJECT_ID}.{DATASET_ID}.psm_cohort`
GROUP BY 1
ORDER BY 1
"""
naive = client.query(query).to_dataframe()
naive
```

**Verified finding:** smokers (`treatment=1`) are meaningfully younger (avg. ~25.3 vs. ~27.8) and far less likely to be married (~36% vs. ~66%) than non-smokers — real, measurable imbalance between the groups *before* considering smoking's own effect. A naive birth-weight comparison mixes the true effect of smoking with these demographic differences.

**Naive effect estimate:** the raw difference in average birth weight between smokers and non-smokers (computed below) is the number every subsequent step tries to correct.

```python
naive_effect = naive.loc[naive.treatment == 1, 'avg_birth_weight'].values[0] - naive.loc[naive.treatment == 0, 'avg_birth_weight'].values[0]
print(f'Naive (unadjusted) effect estimate: {naive_effect:.4f} lbs')
```

---
## Step 3 — The propensity model: `LOGISTIC_REG` predicting *treatment*, not outcome

This is the one place BigQuery ML itself does any work in this workflow — a `LOGISTIC_REG` model, but instead of predicting the birth outcome, it predicts **the probability of being a smoker given the covariates**. That predicted probability is the "propensity score."

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.psm_propensity_model`
OPTIONS(
  model_type = 'LOGISTIC_REG',
  input_label_cols = ['treatment'],
  data_split_method = 'AUTO_SPLIT'
) AS
SELECT mother_age, mother_married, mother_race, weight_gain_pounds, treatment
FROM `{PROJECT_ID}.{DATASET_ID}.psm_cohort`
"""
client.query(query).result()
print('Model psm_propensity_model created')
```

```python
query = f"SELECT * FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.psm_propensity_model`)"
client.query(query).to_dataframe()
```

**Verified finding:** `roc_auc` lands well above 0.5 (real predictive signal — the covariates genuinely distinguish smokers from non-smokers, consistent with Step 2's imbalance) but `precision`/`recall`/`f1_score` show as `0.0`. That's not a broken model — it's the expected artifact of `ML.EVALUATE`'s default 0.5 classification threshold combined with class imbalance (only ~10-11% of this cohort are smokers), so the model's default *binary decision* rarely predicts "smoker." **For propensity scoring, the threshold and classification metrics don't matter at all — only the raw predicted probability does**, which is what gets used next.

Score every row in the cohort to get its propensity score, and keep the covariates/outcome alongside for the next steps.

```python
query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.psm_scored` AS
SELECT
  row_id, treatment, mother_age, mother_married, mother_race, weight_gain_pounds, weight_pounds, low_birth_weight,
  (SELECT prob FROM UNNEST(predicted_treatment_probs) WHERE label = 1) AS propensity_score
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.psm_propensity_model`,
  TABLE `{PROJECT_ID}.{DATASET_ID}.psm_cohort`
)
"""
client.query(query).result()

query = f"""
SELECT treatment, COUNT(*) AS n, ROUND(AVG(propensity_score), 4) AS avg_propensity,
       ROUND(MIN(propensity_score), 4) AS min_propensity, ROUND(MAX(propensity_score), 4) AS max_propensity
FROM `{PROJECT_ID}.{DATASET_ID}.psm_scored`
GROUP BY 1
ORDER BY 1
"""
client.query(query).to_dataframe()
```

Smokers have a visibly higher average propensity score than non-smokers (as expected — the model learned their covariate profile), and the ranges overlap well between groups — the "common support" a matching step needs to actually find good pairs.

---
## Step 4 — Nearest-neighbor matching (with replacement), in plain SQL

For each smoker, find the non-smoker with the closest propensity score, within a **caliper** (a maximum allowed distance — matches farther than this are considered too poor to trust, and dropped rather than kept anyway). Caliper here is the standard rule of thumb: 0.1 × the standard deviation of the propensity score across the whole cohort.

**Two real gotchas found live, worth knowing before you try this at real scale:**
- BigQuery rejects a correlated subquery referencing a table inside a `JOIN ... ON` predicate (`"Unsupported subquery with table in join predicate"`) — computing the caliper as `(SELECT caliper FROM caliper_value)` directly inside the join below fails outright. Fixed by computing the caliper as its own query first and substituting the literal value into the join.
- A direct `JOIN ... ON ABS(a.propensity_score - b.propensity_score) <= caliper` is a genuine inequality self-join — BigQuery has to consider a large number of candidate pairs before filtering, and at full population scale (hundreds of thousands of treated rows × millions of control rows) this blew through the on-demand query engine's CPU-to-bytes-billed ratio limit (`"Query exceeded resource limits"`) even though the *output* was tiny. The fix used here isn't a query trick — it's sample-size discipline: Step 1's cohort is already sized so this self-join is cheap and fast directly, no bucketing or capping needed. If you outgrow this sample size, the standard scalable pattern is to bucket the propensity score into caliper-width bins first and join on bucket equality (a cheap equi-join) before refining to the true nearest neighbor.

```python
query = f"""
SELECT STDDEV(propensity_score) * 0.1 AS caliper
FROM `{PROJECT_ID}.{DATASET_ID}.psm_scored`
"""
caliper = client.query(query).to_dataframe()['caliper'][0]
print(f'Caliper: {caliper:.6f}')

query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.psm_matched` AS
WITH treated AS (
  SELECT row_id, propensity_score, mother_age, mother_married, weight_pounds
  FROM `{PROJECT_ID}.{DATASET_ID}.psm_scored` WHERE treatment = 1
),
control AS (
  SELECT row_id, propensity_score, mother_age, mother_married, weight_pounds
  FROM `{PROJECT_ID}.{DATASET_ID}.psm_scored` WHERE treatment = 0
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
  JOIN control c ON ABS(t.propensity_score - c.propensity_score) <= {caliper}
)
SELECT *
FROM candidates
QUALIFY ROW_NUMBER() OVER (PARTITION BY treated_row_id ORDER BY prop_diff) = 1
"""
client.query(query).result()

query = f"""
SELECT
  COUNT(*) AS n_matched_pairs,
  COUNT(DISTINCT control_row_id) AS n_distinct_controls_reused,
  ROUND(AVG(t_age), 2) AS matched_treated_age, ROUND(AVG(c_age), 2) AS matched_control_age,
  ROUND(AVG(t_married), 3) AS matched_treated_married, ROUND(AVG(c_married), 3) AS matched_control_married,
  ROUND(AVG(treated_outcome), 4) AS matched_treated_bw, ROUND(AVG(control_outcome), 4) AS matched_control_bw
FROM `{PROJECT_ID}.{DATASET_ID}.psm_matched`
"""
matched = client.query(query).to_dataframe()
matched
```

```python
matched_effect = matched['matched_treated_bw'][0] - matched['matched_control_bw'][0]
print(f'Matched effect estimate: {matched_effect:.4f} lbs')
print(f"Balance check — age gap: naive {naive.loc[naive.treatment==1,'avg_mother_age'].values[0] - naive.loc[naive.treatment==0,'avg_mother_age'].values[0]:.2f} -> matched {matched['matched_treated_age'][0] - matched['matched_control_age'][0]:.2f}")
print(f"Balance check — married-rate gap: naive {naive.loc[naive.treatment==1,'married_rate'].values[0] - naive.loc[naive.treatment==0,'married_rate'].values[0]:.3f} -> matched {matched['matched_treated_married'][0] - matched['matched_control_married'][0]:.3f}")
```

**Verified finding — matching worked as designed:** the age gap and married-rate gap both shrink dramatically after matching (compare the printed "naive" vs. "matched" numbers above) — direct evidence the matched comparison groups are far more alike on the confounders than the raw groups were. Every treated unit found a within-caliper match here (`n_matched_pairs` equals the full smoker count); at real-world scale with a tighter caliper or more covariates, some treated units may find no acceptable match and get dropped — that's a real, honest limitation of the method (a smaller but more comparable sample), not a bug to hide.

---
## Step 5 — Inverse Probability of Treatment Weighting (IPTW): a second correction method

Matching keeps a subset of pairs; **IPTW keeps every row** and instead re-weights it: a smoker's weight is `1 / propensity_score`, a non-smoker's weight is `1 / (1 - propensity_score)`. Rows the model considered "surprising" (a smoker who looked like a typical non-smoker, or vice versa) get up-weighted — they carry more information about the counterfactual. The weighted average outcome per group approximates what you'd see if treatment had been assigned independent of the covariates.

```python
query = f"""
WITH weighted AS (
  SELECT
    treatment, weight_pounds,
    IF(treatment = 1, 1 / propensity_score, 1 / (1 - propensity_score)) AS iptw_weight
  FROM `{PROJECT_ID}.{DATASET_ID}.psm_scored`
)
SELECT
  treatment,
  COUNT(*) AS n,
  ROUND(MAX(iptw_weight), 2) AS max_weight,
  ROUND(SUM(weight_pounds * iptw_weight) / SUM(iptw_weight), 4) AS iptw_weighted_birth_weight
FROM weighted
GROUP BY 1
ORDER BY 1
"""
iptw = client.query(query).to_dataframe()
iptw
```

```python
iptw_effect = iptw.loc[iptw.treatment==1, 'iptw_weighted_birth_weight'].values[0] - iptw.loc[iptw.treatment==0, 'iptw_weighted_birth_weight'].values[0]
print(f'IPTW effect estimate: {iptw_effect:.4f} lbs')
print(f"Max IPTW weight (treated group): {iptw.loc[iptw.treatment==1, 'max_weight'].values[0]}")
```

**Verified finding — a real IPTW limitation, not glossed over:** the maximum weight in the treated group is well over 60 (a smoker whose covariates gave them a very *low* predicted propensity to smoke gets weighted very heavily). This is a known instability of IPTW — a single unusual row can dominate the weighted average — and is exactly why some practitioners prefer matching (which simply drops non-comparable units) or a stabilized/trimmed-weight variant of IPTW over the plain version shown here. Reporting the max weight alongside the estimate, as done here, is the honest way to flag when an IPTW result might be less trustworthy.

---
## Step 6 — Honest finding: do the three estimates agree?

```python
summary = pd.DataFrame({
    'method': ['Naive (unadjusted)', 'Propensity-matched', 'IPTW'],
    'effect_estimate_lbs': [naive_effect, matched_effect, iptw_effect],
})
summary
```

**All three estimates land in a fairly narrow band** (naive -0.4001, matched -0.4095, IPTW -0.4274 lbs in this run) despite Step 2's demonstrably real confounding (the age and marital-status gaps). That's a genuinely interesting, honest result — not the dramatic "correction changes everything" story a teaching example might be tempted to manufacture: **the measured confounders here (age, marital status, race, weight gain) are real and imbalanced, but they aren't the dominant driver of the naive birth-weight gap.** The smoking effect looks robust to adjusting for them.

**Non-determinism note:** `LOGISTIC_REG`'s `AUTO_SPLIT` randomly assigns rows to train/eval on every retrain, which shifts the fitted propensity scores slightly run to run — so exactly *which* correction method (matching vs. IPTW) lands closer to vs. further from the naive estimate is not stable across reruns, only the overall "narrow band, confounders don't dominate" finding is. Treat the specific values above as illustrative of one run, not fixed constants — re-run this notebook and the exact numbers (and even which direction each correction moves) may differ, while the qualitative story should not.

**What this workflow cannot tell you, and no amount of PSM can fix:** this only corrects for confounders that were actually *measured and included* — `mother_age`, `mother_married`, `mother_race`, `weight_gain_pounds`. Any *unmeasured* confounder correlated with both smoking and birth weight (e.g., detailed socioeconomic status, access to prenatal care, other substance use) would still bias every estimate above, matched or weighted. This is PSM's central, well-known limitation — it's a real improvement over a naive comparison, not a substitute for a randomized experiment.

---
## Related content

- `models/logistic_regression` (`models/logistic_regression/`) — `LOGISTIC_REG` mechanics in depth (this workflow uses it for propensity scoring, not for its usual predictive role).
- `models/contribution_analysis` (`models/contribution_analysis/`) and `bq-ai-functions/functions/ai_key_drivers` (`bq-ai-functions`'s `AI.KEY_DRIVERS`) — a different flavor of "why did this metric move" analysis (driver/contribution attribution on an already-observed change), rather than estimating the causal effect of a specific, named treatment as PSM does here.

---
## Examples — `%%bigquery` Magics

The same core query using IPython magic commands — write SQL directly in cells without Python string wrapping.

```sql
%%bigquery --project {PROJECT_ID}

SELECT treatment, COUNT(*) AS n
FROM `statmike-mlops-349915.bq_ml.psm_cohort`
GROUP BY treatment
ORDER BY treatment
```

---
## Examples — BigFrames

No direct BigFrames equivalent for the matching/weighting steps — those are hand-rolled SQL here, same as this project's other multi-technique workflows (`workflows/ensembling` (`ensembling`), `workflows/cross_validation` (`cross_validation`)). `bigframes.ml.linear_model.LogisticRegression` is a valid drop-in for Step 3's propensity model itself (same pattern demonstrated in `models/logistic_regression` (`models/logistic_regression/`)) — the matching/weighting logic downstream would still be plain SQL or pandas either way.
