# Causal Effect — BigQuery ML

**Sometimes there is no control group.** `workflows/difference_in_differences` (`difference_in_differences`) needs a comparison state; `workflows/synthetic_control` (`synthetic_control`) needs a whole donor pool. When you have neither — one series, one intervention date — the remaining option is to forecast what the series *would* have done and measure the gap. That is the [CausalImpact](https://google.github.io/CausalImpact/) idea (Brodersen et al., 2015), and `AI.CAUSAL_EFFECT` is BigQuery's one-call version of it — with `ARIMA_PLUS` standing in for the Bayesian structural time series model the original uses, and a closed form standing in for its posterior sampling. Step 5 verifies the first substitution and Step 7 reconstructs the second.

**Functions used:** `AI.CAUSAL_EFFECT` (Preview), `ML.FORECAST`, `ML.ARIMA_EVALUATE`, `ML.EXPLAIN_FORECAST`
**Models used:** `ARIMA_PLUS` — built here *to reproduce* what the function does internally, not because the function needs it
**Data:** [`bigquery-public-data.covid19_open_data.covid19_open_data`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) — the **same** Texas weekly per-100k case-rate series used by `workflows/difference_in_differences` (`difference_in_differences`) and `workflows/synthetic_control` (`synthetic_control`), so all three estimators are measured on identical numbers in identical units.
**References:** `RESOURCES.md` (Full reference) | [`AI.CAUSAL_EFFECT` docs](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-causal-effect) | [`ARIMA_PLUS` docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-time-series) | `setup` (Setup guide)

---

## Read this first: what this function is, and where it sits

`AI.CAUSAL_EFFECT` is a table-valued function that takes **one series and one intervention timestamp** and returns an effect estimate with a p-value. It accepts no control series and no covariates — the documentation gives the reason, avoiding bias from experiment spillover effects, though it also means the method has no way to see a shock that hit everyone.

Two things are worth knowing before you read the results:

**It creates no model artifact.** Verified by counting models in the dataset before and after the call (identical) and by reading `INFORMATION_SCHEMA.JOBS`: one `SELECT` job, `parent_job_id` null, no child jobs. That is why it lives here in `workflows/` alongside the other causal-inference methods rather than in `models/` — there is nothing to manage, evaluate or re-serve.

**Its counterfactual is `ARIMA_PLUS`, and this notebook proves it bit-for-bit.** Step 5 trains a plain `ARIMA_PLUS` on the pre-intervention window with default options and gets forecasts and prediction intervals identical to the function's, to the last digit. So the counterfactual is not the thing you are paying for. The p-value is — and Step 7 shows that is the one piece that does *not* reproduce from documented BigQuery parts.

**Where it sits in this project's causal family.** Every method here answers the same question with a different identifying assumption, and this one has the weakest:

| Workflow | Identifies the counterfactual off |
|---|---|
| `workflows/propensity_score_matching` (`propensity_score_matching`) | covariates — matched comparable units |
| `workflows/difference_in_differences` (`difference_in_differences`) | a control group with parallel pre-trends |
| `workflows/synthetic_control` (`synthetic_control`) | a weighted donor pool of control units |
| `workflows/uplift_cate` (`uplift_cate`) | randomized assignment plus covariates |
| `workflows/price_elasticity_dml` (`price_elasticity_dml`) | covariates, via double machine learning |
| **this notebook** | **the treated unit's own pre-intervention history** |

Step 8 runs three of them on this one dataset and they do **not** agree on magnitude. That disagreement is the most useful thing in the notebook.

---
## Setup

Set your project and location, authenticate, and create a shared dataset.

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
import numpy as np
import matplotlib.pyplot as plt

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
## Step 1 — The panel: the same series the sibling workflows use

Texas plus the 13-state donor pool from `workflows/synthetic_control` (`synthetic_control`), weekly new confirmed cases per 100k population, 2020-05-04 through 2020-08-09. Texas raised its `facial_coverings` policy level from 2 to 3 on **2020-07-03** — a real statewide mask mandate — giving 9 pre-intervention weeks and 5 post.

Only Texas is needed for `AI.CAUSAL_EFFECT` itself. The donor states are loaded now so Step 8 can re-derive the other two estimators from the identical numbers instead of quoting them.

The `n_days = 7` filter matters: `DATE_TRUNC` at the edge of a `BETWEEN` range silently truncates the boundary weeks to fewer than 7 days, which would depress those weeks' sums.

```python
donor_pool = ['CO', 'GA', 'ID', 'IL', 'ME', 'MN', 'ND', 'NE', 'NH', 'SD', 'VA', 'WV', 'WY']
all_states = ['TX'] + donor_pool
INTERVENTION = '2020-07-03'

query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.causal_effect_panel` AS
WITH pop AS (
  SELECT subregion1_code, ANY_VALUE(population) AS population
  FROM `bigquery-public-data.covid19_open_data.covid19_open_data`
  WHERE country_code = 'US' AND aggregation_level = 1 AND subregion1_code IN UNNEST(@states)
  GROUP BY subregion1_code
),
base AS (
  SELECT subregion1_code, DATE_TRUNC(date, WEEK(MONDAY)) AS wk, SUM(new_confirmed) AS wk_cases, COUNT(*) AS n_days
  FROM `bigquery-public-data.covid19_open_data.covid19_open_data`
  WHERE country_code = 'US' AND aggregation_level = 1 AND subregion1_code IN UNNEST(@states)
    AND date BETWEEN '2020-05-04' AND '2020-08-09'
  GROUP BY subregion1_code, wk
)
SELECT b.subregion1_code, b.wk, b.wk_cases / p.population * 100000 AS rate
FROM base b JOIN pop p USING (subregion1_code)
WHERE b.n_days = 7
"""
job_config = bigquery.QueryJobConfig(query_parameters=[bigquery.ArrayQueryParameter('states', 'STRING', all_states)])
client.query(query, job_config=job_config).result()

panel_df = client.query(
    f'SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.causal_effect_panel` ORDER BY subregion1_code, wk'
).to_dataframe()
panel_df['wk'] = pd.to_datetime(panel_df['wk'])
pivot = panel_df.pivot(index='wk', columns='subregion1_code', values='rate').sort_index()

tx = pivot['TX']
print(f'{len(pivot)} weeks, {len(all_states)} states')
print(f'Pre-intervention:  {(pivot.index < INTERVENTION).sum()} weeks')
print(f'Post-intervention: {(pivot.index >= INTERVENTION).sum()} weeks\n')
tx.to_frame('TX rate per 100k')
```

---
## Step 2 — The whole analysis in one call

Three required arguments. The series goes in as a subquery.

```python
TX_SERIES = f"""(SELECT TIMESTAMP(wk) AS wk_ts, rate
                 FROM `{PROJECT_ID}.{DATASET_ID}.causal_effect_panel`
                 WHERE subregion1_code = 'TX')"""

query = f"""
SELECT * FROM AI.CAUSAL_EFFECT(
  {TX_SERIES},
  timestamp_col          => 'wk_ts',
  data_col               => 'rate',
  intervention_timestamp => TIMESTAMP '{INTERVENTION}'
)
"""
summary = client.query(query).to_dataframe()
summary.T
```

**Reading the output.** `absolute_effect` is the *cumulative* gap over the whole post-intervention window, not a per-period rate — divide by the 5 post weeks to compare it against the sibling workflows' per-week estimates. `relative_effect` expresses that same cumulative gap as a fraction of the cumulative counterfactual. `prob_causal_effect` is exactly `1 - p_value`, carrying no information the p-value does not. `status` is empty on success and carries the error string otherwise.

The p-value here does not clear conventional significance. Keep that in view through the rest of the notebook — the point estimate is the number that will be quoted, and it is the number the p-value says not to lean on.

---
## Step 3 — The pointwise view

`output_time_series => TRUE` adds `is_post_intervention`, `predicted_<data_col>`, `lower_bound` and `upper_bound` per row. The four summary columns repeat unchanged on every row.

```python
query = f"""
SELECT wk_ts, is_post_intervention, rate, predicted_rate, lower_bound, upper_bound
FROM AI.CAUSAL_EFFECT(
  {TX_SERIES},
  timestamp_col          => 'wk_ts',
  data_col               => 'rate',
  intervention_timestamp => TIMESTAMP '{INTERVENTION}',
  output_time_series     => TRUE
)
ORDER BY wk_ts
"""
ts = client.query(query).to_dataframe()
ts
```

```python
post = ts[ts['is_post_intervention']].reset_index(drop=True)

print('Week-over-week change in the counterfactual:')
print(np.diff(post['predicted_rate'].values), '\n')

centered = post['predicted_rate'] - (post['lower_bound'] + post['upper_bound']) / 2
print(f'Max asymmetry of the intervals about the forecast: {centered.abs().max():.2e}')
print(f'Interval half-width, week 1: {(post["upper_bound"][0] - post["lower_bound"][0]) / 2:8.2f}')
print(f'Interval half-width, week 5: {(post["upper_bound"][4] - post["lower_bound"][4]) / 2:8.2f}')
```

```python
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(ts['wk_ts'], ts['rate'], marker='o', color='black', linewidth=2, label='Texas (actual)')
ax.plot(post['wk_ts'], post['predicted_rate'], marker='o', linestyle='--', color='darkorange',
        label='Counterfactual (AI.CAUSAL_EFFECT)')
ax.fill_between(post['wk_ts'], post['lower_bound'], post['upper_bound'],
                color='darkorange', alpha=0.15, label='95% prediction interval')
ax.axvline(pd.Timestamp(INTERVENTION), color='gray', linestyle='--', linewidth=1,
           label=f'TX mandate ({INTERVENTION})')
ax.set_xlabel('Week')
ax.set_ylabel('New confirmed cases per 100k')
ax.set_title('Texas vs. the counterfactual AI.CAUSAL_EFFECT extrapolates from its own history')
ax.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
```

**Verified finding — the counterfactual is a perfect straight line.** Every week-over-week change in `predicted_rate` is the same value to 8 decimals. With 9 pre-period points on a steeply accelerating epidemic curve, `auto_arima` had no room to find seasonality or mean reversion, so the counterfactual asserts Texas would have kept adding the same increment every week indefinitely. That extrapolation is the null hypothesis the p-value tests against, and it is worth seeing plainly before trusting anything downstream of it.

The prediction intervals are exactly symmetric about the forecast and widen sharply with horizon — from roughly ±27 in week 1 to ±200 in week 5. By the end of a five-week window the interval spans more than the entire observed range of the series, which is the honest statement of how much a 9-point pre-period can support.

---
## Step 4 — Reproduce both effect columns by hand

Neither aggregate involves inference. They are sums over the post-intervention rows.

```python
manual_absolute = (post['rate'] - post['predicted_rate']).sum()
manual_relative = manual_absolute / post['predicted_rate'].sum()

pd.DataFrame({
    'reported': [summary['absolute_effect'][0], summary['relative_effect'][0]],
    'manual':   [manual_absolute, manual_relative],
    'match':    [np.isclose(manual_absolute, summary['absolute_effect'][0], rtol=0, atol=1e-9),
                 np.isclose(manual_relative, summary['relative_effect'][0], rtol=0, atol=1e-12)],
}, index=['absolute_effect', 'relative_effect'])
```

**Verified finding:** `absolute_effect = SUM(actual - expected)` and `relative_effect = SUM(actual - expected) / SUM(expected)`, both reproduced exactly. Everything interesting the function does is therefore concentrated in two places: the counterfactual (Step 5) and the p-value (Step 7).

```python
no_cache = bigquery.QueryJobConfig(use_query_cache=False)

def tx_effects(expr):
    """Run the same call on a transformed copy of the Texas series."""
    return client.query(f"""
    SELECT absolute_effect, relative_effect, p_value
    FROM AI.CAUSAL_EFFECT(
      (SELECT TIMESTAMP(wk) AS wk_ts, {expr} AS rate
       FROM `{PROJECT_ID}.{DATASET_ID}.causal_effect_panel`
       WHERE subregion1_code = 'TX'),
      timestamp_col => 'wk_ts', data_col => 'rate',
      intervention_timestamp => TIMESTAMP '{INTERVENTION}')
    """, job_config=no_cache).to_dataframe().iloc[0]

pd.DataFrame({
    'rate (as published)': tx_effects('rate'),
    'rate * 10':           tx_effects('rate * 10'),
    'rate + 100':          tx_effects('rate + 100'),
    '-rate':               tx_effects('-rate'),
}).T
```

**Verified finding — `relative_effect` is not a unit-free summary, and the sign does not mean what it looks like.**

`absolute_effect` behaves exactly as a sum of differences must: multiply the series by 10 and it multiplies by 10; add a constant to every point and it does not move, because the constant lands in the counterfactual too.

`relative_effect` is invariant to *scale* but **not to the origin**. Shifting the series by a constant changes it from `-0.2205` to `-0.1586` — the numerator is unchanged and the denominator, `SUM(expected)`, absorbed the shift. So `relative_effect` only means "a 22% reduction" when the metric sits on a ratio scale with a true zero. On an index, a temperature, a mean-centred residual, or anything with an arbitrary offset, the percentage is an artifact of where zero happens to be, and the number to quote is `absolute_effect`.

Negating the series is the sharper trap. `absolute_effect` flips sign, as expected — and `relative_effect` **does not**, because the numerator and the denominator negate together. On a metric where down is good, `relative_effect`'s sign describes the deviation relative to the counterfactual's own sign, not the direction of improvement. Read it against `absolute_effect`, never alone.

The p-value is invariant to all three transformations, which is the expected behaviour of a standardized statistic and a useful check on the reconstruction attempted in Step 7.

---
## Step 5 — Reproduce the counterfactual: plain `ARIMA_PLUS`, default options

Train on the pre-intervention window only, change no options, forecast 5 weeks.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.causal_effect_arima`
OPTIONS(
  model_type                = 'ARIMA_PLUS',
  time_series_timestamp_col = 'wk_ts',
  time_series_data_col      = 'rate'
) AS
SELECT TIMESTAMP(wk) AS wk_ts, rate
FROM `{PROJECT_ID}.{DATASET_ID}.causal_effect_panel`
WHERE subregion1_code = 'TX' AND wk < '{INTERVENTION}'
"""
client.query(query).result()

query = f"""
SELECT forecast_timestamp, forecast_value,
       prediction_interval_lower_bound, prediction_interval_upper_bound
FROM ML.FORECAST(MODEL `{PROJECT_ID}.{DATASET_ID}.causal_effect_arima`,
                 STRUCT(5 AS horizon, 0.95 AS confidence_level))
ORDER BY forecast_timestamp
"""
fc = client.query(query).to_dataframe()

compare = pd.DataFrame({
    'week':                post['wk_ts'].dt.date.values,
    'AI.CAUSAL_EFFECT':    post['predicted_rate'].values,
    'ARIMA_PLUS':          fc['forecast_value'].values,
    'identical':           post['predicted_rate'].values == fc['forecast_value'].values,
    'lower identical':     post['lower_bound'].values == fc['prediction_interval_lower_bound'].values,
    'upper identical':     post['upper_bound'].values == fc['prediction_interval_upper_bound'].values,
})
compare
```

**Verified finding — bit-for-bit identical.** Not "close," not "within tolerance": all fifteen values (5 forecasts and 10 interval bounds) compare equal under exact float equality.

So `AI.CAUSAL_EFFECT`'s counterfactual **is** `ARIMA_PLUS` + `ML.FORECAST` on default options. Nothing proprietary, nothing tuned, no TimesFM. The convenience is real — one call instead of two, no model to name, drop or grant access to — but the counterfactual is not a capability you were missing.

Two consequences worth stating. First, everything documented about `ARIMA_PLUS` applies to this function's counterfactual: its handling of gaps, its holiday options, its `auto_arima` search. Second, if the defaults are wrong for your series, `AI.CAUSAL_EFFECT` gives you no way to change them — there is no argument to pass `holiday_region`, `data_frequency`, or a custom `(p,d,q)` through.

---
## Step 6 — What the model artifact buys you that the function does not

Having built the model, the whole `ARIMA_PLUS` lifecycle is available against the exact counterfactual the function used.

```python
arima_eval = client.query(
    f'SELECT * FROM ML.ARIMA_EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.causal_effect_arima`)'
).to_dataframe()
arima_eval.T
```

```python
explain = client.query(f"""
SELECT time_series_timestamp, time_series_data, time_series_adjusted_data, trend
FROM ML.EXPLAIN_FORECAST(MODEL `{PROJECT_ID}.{DATASET_ID}.causal_effect_arima`,
                         STRUCT(5 AS horizon, 0.95 AS confidence_level))
ORDER BY time_series_timestamp
""").to_dataframe()
explain
```

**Verified finding — the selected order explains the shape seen in Step 3.** `ML.ARIMA_EVALUATE` returns the candidate models `auto_arima` compared, best first. The winner is **(0, 2, 0)** — no AR terms, no MA terms, **twice differenced** — with `has_drift = False`, `seasonal_periods = [NO_SEASONALITY]`, and no holiday, spike or step-change component. Every candidate in the list shares `non_seasonal_d = 2`.

That single fact accounts for everything odd about the counterfactual. A twice-differenced random walk forecasts a perfectly straight line, which is why the week-over-week increment never varies; and its forecast variance accumulates as the cumulative sum of squared horizons, which Step 7 confirms directly against the interval widths. The straight line is not a drift term the model estimated — `has_drift` is `False` — it is the double differencing carrying the last observed slope forward unchanged.

`ML.EXPLAIN_FORECAST` shows the same thing from the other side: the whole series decomposes into `trend` alone, with no seasonal or holiday component to separate out.

This is the real cost of the one-call convenience. For a *causal* claim you are being asked to trust a counterfactual you cannot inspect: `AI.CAUSAL_EFFECT` returns no model, so without rebuilding it there is no way to learn that the null hypothesis you are testing against is "the last nine weeks' acceleration continues forever." When the answer matters, build the model.

---
## Step 7 — The p-value: rebuilding it from two ingredients

`absolute_effect` and `relative_effect` are sums (Step 4) and the counterfactual is `ARIMA_PLUS` (Step 5). That leaves the p-value as the only genuinely new quantity the function computes — so it is worth rebuilding.

Step 5 pays off here. `AI.CAUSAL_EFFECT` renders interval bounds and nothing else, but the model behind them is one this notebook has already reproduced, and `ML.FORECAST` reports the pointwise standard error as a column. Take the exact standard errors from there, check what the rendered bounds do with them, recover the moving-average (`psi`) weights the errors encode, then test seven plausible constructions of a cumulative-effect test statistic against the value the function actually returned.

It takes two ingredients, and neither is the one a textbook reaches for first. The interval multiplier gives away the second before the p-value needs it.

```python
from scipy import stats

# AI.CAUSAL_EFFECT publishes interval bounds but no standard error. Step 5 established that its
# counterfactual is the ARIMA_PLUS model bit for bit, and ML.FORECAST does publish one - so the
# exact quantity is available without reconstructing it from the rendered bounds.
fc_se = client.query(f"""
SELECT standard_error,
       prediction_interval_upper_bound - prediction_interval_lower_bound AS width
FROM ML.FORECAST(MODEL `{PROJECT_ID}.{DATASET_ID}.causal_effect_arima`,
                 STRUCT(5 AS horizon, 0.95 AS confidence_level))
ORDER BY forecast_timestamp
""").to_dataframe()

se   = fc_se['standard_error'].values
z95  = stats.norm.ppf(0.975)
print('Standard errors reported by ML.FORECAST:       ', np.round(se, 3))
print('Backed out of the intervals with z = 1.959964: ', np.round(
    (post['upper_bound'].values - post['lower_bound'].values) / (2 * z95), 3))
print('Multiplier the rendered intervals actually use:', np.round(fc_se['width'].values / (2 * se), 7))
print(f'Normal 97.5th percentile:                       {z95:.7f}')
print('How far the rendered bounds fall short:         '
      f'{(fc_se["width"].values / (2 * se))[0] / z95 - 1:+.2%}')

gap = (post['rate'] - post['predicted_rate']).values
cum, H = gap.sum(), len(gap)

print('\nRatio to the one-step se:      ', np.round(se / se[0], 3))
print('sqrt(cumulative sum of j^2):   ', np.round(np.sqrt(np.cumsum(np.arange(1, H + 1) ** 2)), 3))

# The se sequence encodes the model's psi weights: se_h^2 = sigma^2 * sum(psi_0..psi_{h-1})^2,
# so each weight can be read straight back out of it. psi_0 is 1 by construction.
psi = np.concatenate([[1.0], np.sqrt(np.diff(se ** 2) / se[0] ** 2)])
print('\nPsi weights recovered from the se: ', np.round(psi, 9))
```

```python
# Is the multiplier a different distribution, or an approximation to the normal quantile?
from scipy.optimize import brentq

def as_cdf(x):
    """Normal CDF via Abramowitz & Stegun 26.2.18 (the Hastings quartic). |error| < 2.5e-4."""
    x = np.abs(x)
    poly = 1 + 0.196854 * x + 0.115194 * x ** 2 + 0.000344 * x ** 3 + 0.019527 * x ** 4
    return 1 - 0.5 * poly ** -4

def as_ppf(p):
    """The quantile of that same approximation, by bisection."""
    return brentq(lambda x: as_cdf(x) - p, 0.0, 8.0)

rows = []
for cl in [0.80, 0.90, 0.95, 0.98, 0.99]:
    q_used = client.query(f"""
    SELECT AVG((prediction_interval_upper_bound - prediction_interval_lower_bound)
               / (2 * standard_error)) AS q
    FROM ML.FORECAST(MODEL `{PROJECT_ID}.{DATASET_ID}.causal_effect_arima`,
                     STRUCT(5 AS horizon, {cl} AS confidence_level))
    """).to_dataframe()['q'][0]
    rows.append({'confidence_level':    cl,
                 'multiplier used':     q_used,
                 'A&S 26.2.18 inverse': as_ppf(0.5 + cl / 2),
                 'A&S error':           as_ppf(0.5 + cl / 2) - q_used,
                 'normal quantile':     stats.norm.ppf(0.5 + cl / 2),
                 'normal error':        stats.norm.ppf(0.5 + cl / 2) - q_used,
                 'Student t, df = 7':   stats.t.ppf(0.5 + cl / 2, df=H + 2)})
pd.DataFrame(rows).set_index('confidence_level')
```

**Verified finding — `ML.FORECAST`'s prediction interval is `forecast ± q · standard_error` where `q` inverts a *quartic approximation* to the normal CDF, not the CDF itself.** At `confidence_level => 0.95` the rendered bounds are exactly `1.9564581 × standard_error` wide on each side, identical to seven decimal places at all five horizons. The normal 97.5th percentile is `1.9599640`, so the bounds are 0.18% narrower than the textbook interval.

The sweep identifies the multiplier rather than merely bounding it. Inverting **Abramowitz & Stegun 26.2.18** — the Hastings quartic, `P(x) = 1 - ½(1 + 0.196854x + 0.115194x² + 0.000344x³ + 0.019527x⁴)⁻⁴`, a four-term rational approximation with `|error| < 2.5e-4` — reproduces every multiplier in the table to about a millionth, which is the precision at which they are printed. The exact normal quantile misses by up to `0.0119`, four orders of magnitude worse.

Two competitors die on the same table. A Student *t* quantile is ruled out by direction alone — *t* is always **wider** than normal, at every level here and by a wide margin at 7 degrees of freedom. A constant scale factor is ruled out because the `normal error` column **changes sign** across the five levels. Non-monotone error that grows in the tail is what a fixed-degree polynomial approximation does; it is not what a different distribution does.

This does not establish what BigQuery's source code contains. It establishes that the rendered multipliers are numerically indistinguishable from this specific published approximation, at every level tested — which is enough to predict them, and, in the next cells, enough to predict the p-value too.

The practical consequence is narrow and worth knowing: **do not back a standard error out of the rendered bounds.** Dividing a 95% interval width by `2 × 1.959964` returns a number 0.18% too small — invisible on a chart, and large enough to swamp the comparison the rest of this step is about. The `standard_error` column is the quantity itself, and everything below uses it.

```python
def two_sided(sd):
    z = cum / sd
    return sd, z, 2 * stats.norm.cdf(-abs(z))

constructions = {
    'independent — sqrt(sum of variances)':        two_sided(np.sqrt((se ** 2).sum())),
    'random-walk cumulation of the one-step se':   two_sided(se[0] * np.sqrt(H * (H + 1) * (2 * H + 1) / 6)),
    "the last step's se alone":                    two_sided(se[-1]),
    'H x the last step\'s se':                     two_sided(H * se[-1]),
    'sum of the se (perfectly correlated errors)': two_sided(se.sum()),
    'cumulative ARIMA forecast error (psi weights)': two_sided(se[0] * np.sqrt((np.cumsum(psi) ** 2).sum())),
}
tbl = pd.DataFrame(constructions, index=['implied sd', 'z', 'p']).T

# a t-test on the 5 pointwise gaps, which is not a z construction
t_stat = gap.mean() / (gap.std(ddof=1) / np.sqrt(H))
tbl.loc['t-test on the H pointwise gaps'] = [np.nan, t_stat, 2 * stats.t.cdf(-abs(t_stat), df=H - 1)]

reported_p = summary['p_value'][0]
tbl['abs error vs reported'] = (tbl['p'] - reported_p).abs()
print(f'Reported p_value: {reported_p!r}\n')
tbl.sort_values('abs error vs reported')
```

```python
required_sd = abs(cum) / abs(stats.norm.ppf(reported_p / 2))
print(f'Standard deviation implied by the reported p_value: {required_sd:.3f}')
print(f'Closest construction (sum of the se):               {se.sum():.3f}')
print(f'Gap:                                                {abs(required_sd - se.sum()) / required_sd:.2%}')

# Alternatively, keep sd = sum(se) and ask what degrees of freedom would close the gap
implied_df = brentq(lambda df: 2 * stats.t.cdf(-abs(cum / se.sum()), df=df) - reported_p, 2, 1e6)
print(f'\nDegrees of freedom that would close it instead:     {implied_df:.0f}')
print(f'Pre-intervention points available:                  {(~ts["is_post_intervention"]).sum()}')
```

```python
# Two ingredients, both measured above: the ceiling variance from the table of constructions,
# and the CDF approximation the interval multiplier gave away - used forward now, not inverted.
sd_psi  = se[0] * np.sqrt((np.cumsum(psi) ** 2).sum())
z_stat  = cum / se.sum()
p_as    = 2 * (1 - as_cdf(z_stat))
p_exact = 2 * stats.norm.cdf(-abs(z_stat))
p_psi   = 2 * stats.norm.cdf(-abs(cum / sd_psi))

print(f'Z = absolute_effect / sum(se) = {cum:.6f} / {se.sum():.6f} = {z_stat:.9f}\n')
print(f'{"":<38}{"p":>13}{"vs reported":>15}')
for label, p in [('reported by AI.CAUSAL_EFFECT',       reported_p),
                 ('2 x (1 - A&S 26.2.18 CDF(|Z|))',     p_as),
                 ('2 x (1 - exact normal CDF(|Z|))',    p_exact),
                 ('exact normal on the psi cumulation', p_psi)]:
    print(f'{label:<38}{p:>13.9f}{p - reported_p:>15.2e}')

print('\nWhat separates the textbook answer from the reported one:')
print(f'  conservative variance choice (psi -> sum of se): {p_exact - p_psi:.6f}'
      f'   (sd inflated {se.sum() / sd_psi - 1:+.2%})')
print(f'  CDF approximation (exact normal -> A&S):         {p_as - p_exact:.6f}')
print(f'  the modelling choice is larger by:               {(p_exact - p_psi) / (p_as - p_exact):.0f}x')
```

**Verified finding — the p-value is `2 · (1 − CDF(|Z|))` with `Z = absolute_effect ÷ Σ standard_error`, and the `CDF` is the approximation the interval multiplier gave away two cells above.** No fitted constant, no free parameter: both ingredients were measured before the comparison, and the reconstruction lands on the reported value exactly — the two `FLOAT64`s are equal bit for bit.

The seven candidates split into three groups, and the split is the informative part. The **`psi`-weight cumulation is the right answer to the textbook question** — given an `ARIMA(0, 2, 0)` counterfactual, `266.695866` *is* the standard deviation of the sum of its five forecast errors, built from weights recovered from the model's own reported standard errors rather than assumed. It is not the one the function uses. The **sum of the pointwise standard errors** is, at `275.139104` — the variance you get only if the five forecast errors are *perfectly* correlated, the ceiling of the family rather than a member of it.

**That is a deliberate choice, and it is the conservative one.** Perfect positive correlation gives the largest variance any correlation structure among these errors can produce, hence the widest interval and the largest p-value. The function is built not to overstate significance. It is not free — the cell above prints what it costs, and it is the bigger of the two effects in play by a wide margin. The CDF approximation, by comparison, is a rounding convention.

The two cells before this one measured the residual as `0.09%` in standard-deviation units, or a *t* distribution with 543 degrees of freedom — a number with no counterpart in a 9-point pre-period. Neither describes a mechanism, because neither is one: the exact normal evaluated on the same `Z` already gives `0.304355`, and the approximation supplies the rest.

A wording caution worth carrying: what is established is that these numbers are indistinguishable from **Abramowitz & Stegun 26.2.18** at the precision available. That is a claim about arithmetic, not about BigQuery's source code.

Three measured constraints confirm the reconstruction below — the horizon sweep, then `confidence_level` and determinism.

```python
# num_post_intervention_points shortens the post window without changing the pre window,
# so the counterfactual is untouched and only the number of points being summed moves.
rows = []
for h in [2, 3, H]:
    r = client.query(f"""
    SELECT absolute_effect, p_value FROM AI.CAUSAL_EFFECT(
      {TX_SERIES},
      timestamp_col => 'wk_ts', data_col => 'rate',
      intervention_timestamp => TIMESTAMP '{INTERVENTION}',
      num_post_intervention_points => {h})
    """, job_config=no_cache).to_dataframe().iloc[0]
    z_h     = r['absolute_effect'] / se[:h].sum()
    implied = abs(r['absolute_effect']) / abs(stats.norm.ppf(r['p_value'] / 2))
    rows.append({
        'post points':          h,
        'same counterfactual':  np.isclose(r['absolute_effect'], gap[:h].sum(), rtol=0, atol=1e-9),
        'p_value':              r['p_value'],
        'Z = effect / sum(se)': z_h,
        'p from A&S(|Z|)':      2 * (1 - as_cdf(z_h)),
        'A&S error':            2 * (1 - as_cdf(z_h)) - r['p_value'],
        'p from exact normal':  2 * stats.norm.cdf(-abs(z_h)),
        'implied / ceiling':    implied / se[:h].sum(),
    })
pd.DataFrame(rows).set_index('post points')
```

**Verified finding — the reconstruction holds at three horizons, and the sign change in the residual is the approximation's own oscillation, not a constraint on the variance.** Shortening the post window with `num_post_intervention_points` leaves the pre window and therefore the counterfactual untouched (the `same counterfactual` column confirms the reported effect is still the sum of the same pointwise gaps), which turns one comparison into three. At all three, `2 · (1 − A&S(|Z|))` matches the reported p-value to the last digits a `FLOAT64` carries — zero difference at two horizons and one unit in the last place at the third. Note `Z` is *positive* at two post weeks: Texas ran above its counterfactual before it ran below, so the cumulative gap changes sign as the window lengthens, and the reconstruction tracks it through the turn.

The `implied / ceiling` column is that same residual measured the other way, by inverting the *exact* normal: `0.999418`, `0.999073`, `1.000946` — below the ceiling twice, above it once. Read as evidence about the variance, that straddle looks like it eliminates whole families of explanation at once, since a constant correction or a fixed-*df* distribution would leave a consistent sign. It is not evidence about the variance. The variance is exactly the ceiling at every horizon. The straddle is the quartic's error against the function it approximates, which changes sign as `|Z|` moves — the same oscillation the `normal error` column showed for the interval multiplier, seen through a second lens.

**The general shape of the mistake is worth naming, because it is cheap to make: when a reproduction misses by a margin far smaller than the quantity being reproduced, suspect the *evaluation* of the formula before concluding the formula is wrong.** A `0.09%` residual on a standard deviation is the size of a rounding convention, not the size of a missing variance component.

That the comparison could be made at all depends on these being the model's *reported* standard errors. Had it used errors reconstructed from the rendered bounds, the 0.18% narrowing measured above would have pushed all three ratios to the same side and hidden the oscillation completely.

```python
rows = []
for cl in [0.80, 0.95, 0.99]:
    q = f"""
    SELECT p_value, absolute_effect, MIN(lower_bound) OVER () AS min_lower, MAX(upper_bound) OVER () AS max_upper
    FROM AI.CAUSAL_EFFECT(
      {TX_SERIES},
      timestamp_col => 'wk_ts', data_col => 'rate',
      intervention_timestamp => TIMESTAMP '{INTERVENTION}',
      confidence_level => {cl}, output_time_series => TRUE)
    LIMIT 1
    """
    r = client.query(q).to_dataframe().iloc[0]
    rows.append({'confidence_level': cl, 'p_value': r['p_value'],
                 'widest interval': r['max_upper'] - r['min_lower']})
pd.DataFrame(rows)
```

```python
q = f"""
SELECT absolute_effect, relative_effect, p_value FROM AI.CAUSAL_EFFECT(
  {TX_SERIES},
  timestamp_col => 'wk_ts', data_col => 'rate',
  intervention_timestamp => TIMESTAMP '{INTERVENTION}')
"""
repeats = pd.concat([client.query(q, job_config=no_cache).to_dataframe() for _ in range(3)],
                    ignore_index=True)
print(repeats.to_string(index=False))
print(f'\nDistinct p_value across 3 cache-disabled runs: {repeats["p_value"].nunique()}')
```

**Verified finding — the p-value is invariant to `confidence_level` and deterministic across runs.**

The interval width changes as expected when `confidence_level` moves, and the p-value does not move at all. So it is computed from the model’s internal variance, not from the rendered bounds — which is why the reconstruction above uses the `standard_error` column and not a number read back off an interval.

Determinism is worth stating because it is not the norm here: the TimesFM-backed `AI.*` functions are not reproducible even with the model version pinned, and separate cache-disabled calls are the only way to establish it, since the query cache will happily return the same row four times. A closed form, not a posterior sample — which is a genuine difference from the R `CausalImpact` package, whose tail area comes from MCMC.

Which settles what this function actually buys you. The counterfactual is plain `ARIMA_PLUS` (Step 5), the two effect columns are plain sums (Step 4), and the p-value is two measured quantities combined in a single line. The value on offer is the packaging and one defensible modelling decision — the conservative variance — not a capability that was otherwise out of reach.

**One thing the function does not return: an interval on the effect itself.** The summary row carries a point estimate and a p-value; `lower_bound` and `upper_bound` are pointwise bounds on the *counterfactual*, not on the cumulative gap. With both ingredients in hand the missing interval can be built — and built on the function's own terms, so it agrees with the p-value printed beside it.

```python
# The interval AI.CAUSAL_EFFECT does not return, assembled from the two ingredients that
# produce its p-value so that the two agree by construction.
rows = []
for cl in [0.80, 0.95, 0.99]:
    hw_as    = as_ppf(0.5 + cl / 2) * se.sum()
    hw_exact = stats.norm.ppf(0.5 + cl / 2) * se.sum()
    rows.append({'confidence_level':        cl,
                 "on the function's terms": f'[{cum - hw_as:9.3f}, {cum + hw_as:8.3f}]',
                 'textbook normal':         f'[{cum - hw_exact:9.3f}, {cum + hw_exact:8.3f}]',
                 'half-width difference':   hw_as - hw_exact,
                 'straddles zero':          (cum - hw_as) < 0 < (cum + hw_as)})
pd.DataFrame(rows).set_index('confidence_level')
```

```python
# If a threshold is going to be used anyway, this is where the approximation could move a
# verdict: near the boundary, where a few ten-thousandths decide the sentence.
print(f'{"threshold":>11}{"a true p at it reports as":>28}{"a reported p at it is truly":>30}')
for t in [0.10, 0.05, 0.01]:
    z_exact = stats.norm.ppf(1 - t / 2)
    z_as    = brentq(lambda x: 2 * (1 - as_cdf(x)) - t, 0.01, 8.0)
    print(f'{t:>11.2f}{2 * (1 - as_cdf(z_exact)):>28.6f}{2 * stats.norm.cdf(-z_as):>30.6f}')
```

**The threshold is a convention; the interval is the finding.** `p_value` is the whole of what this function says about uncertainty, and quoted alone it collapses into a verdict: above `0.05`, therefore "not significant," therefore — in far too many readings — "no effect." The 95% interval says something a threshold cannot. The cumulative effect over five weeks is estimated at `-282.6` cases per 100k, and the data are consistent with anything from roughly `-821` to `+256`. That range contains a large reduction, no change at all, and a moderate increase. It is not a failure to detect an effect; it is a direct statement of how little a 9-week pre-period can pin down.

The interval is also strictly more informative than the threshold, not merely friendlier. The p-value is recoverable from it — the interval straddles zero exactly when `p > 1 - confidence_level`, which the `straddles zero` column shows at all three levels — and the interval is not recoverable from the p-value. When the question is "should we act," a threshold is a defensible way to stop arguing. When the question is "what did this do," report the interval and the point estimate together and let the reader see the range.

**At the boundary, the approximation is worth naming.** The cell above prices it: a result whose true two-sided p-value is exactly `0.05` is reported as `0.049591`, and a reported `0.05` corresponds to a true `0.050411`. Either way it is four ten-thousandths, which matters to nobody who reads an interval and to anybody who reads `< 0.05` as a verdict. That is an argument about thresholds, not about the approximation.

**Build it on the function's terms, not the textbook's.** Both columns above use the ceiling variance, because that is what the reported p-value uses; a `psi`-based interval would be narrower and would quietly contradict the p-value sitting next to it. What remains between the two columns is the CDF approximation — under one case per 100k at `0.80` and `0.95`, a few cases at `0.99`. Small enough to ignore when reporting, large enough to be worth knowing which convention produced which number.

---
## Step 8 — Three estimators, one dataset, identical units

The Texas mask mandate, measured three structurally different ways on the same weekly per-100k series. The other two are re-derived here rather than quoted, so the comparison is arithmetic rather than assertion.

```python
pre_p  = pivot[pivot.index < INTERVENTION]
post_p = pivot[pivot.index >= INTERVENTION]

# Difference-in-differences: the 2x2 means, equal to the balanced-panel interaction coefficient
did = (post_p['TX'].mean() - pre_p['TX'].mean()) - (post_p['GA'].mean() - pre_p['GA'].mean())

# Synthetic control: weights non-negative and summing to 1, fit on the pre-period
from scipy.optimize import minimize
D, t = pre_p[donor_pool].values, pre_p['TX'].values
res = minimize(lambda w: np.sum((t - D @ w) ** 2), np.ones(len(donor_pool)) / len(donor_pool),
               method='SLSQP', bounds=[(0, 1)] * len(donor_pool),
               constraints=({'type': 'eq', 'fun': lambda w: w.sum() - 1}))
synth = (post_p['TX'].values - post_p[donor_pool].values @ res.x).mean()

ce_weekly = summary['absolute_effect'][0] / H

pd.DataFrame({
    'per-week effect': [did, synth, ce_weekly],
    'counterfactual built from': ['Georgia', 
                                  ' + '.join(f'{w:.0%} {d}' for d, w in zip(donor_pool, res.x) if w > 0.01),
                                  "Texas's own 9 pre-period weeks"],
}, index=['difference-in-differences', 'synthetic control', 'AI.CAUSAL_EFFECT'])
```

```python
synth_full = pivot[donor_pool].values @ res.x
ce_full = np.concatenate([np.full((pivot.index < INTERVENTION).sum(), np.nan), post['predicted_rate'].values])

# DiD's counterfactual is Georgia's *path* anchored to Texas's own pre-period level,
# not Georgia's raw series — the level difference is exactly what DiD differences away.
did_full = pivot['GA'] + (pre_p['TX'].mean() - pre_p['GA'].mean())
print(f"DiD from the plotted counterfactual: {(post_p['TX'] - did_full[post_p.index]).mean():.6f}")

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(pivot.index, pivot['TX'], marker='o', color='black', linewidth=2, label='Texas (actual)')
ax.plot(pivot.index, synth_full, marker='o', linestyle='--', color='steelblue',
        label='Counterfactual: synthetic control')
ax.plot(pivot.index, did_full, marker='o', linestyle=':', color='gray',
        label='Counterfactual: Georgia, level-shifted (DiD)')
ax.plot(pivot.index, ce_full, marker='o', linestyle='--', color='darkorange',
        label='Counterfactual: AI.CAUSAL_EFFECT')
ax.axvline(pd.Timestamp(INTERVENTION), color='gray', linestyle='--', linewidth=1)
ax.set_xlabel('Week')
ax.set_ylabel('New confirmed cases per 100k')
ax.set_title('Three counterfactuals for the same intervention')
ax.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
```

**Verified finding — all three agree on sign, and disagree on magnitude by roughly 3x.** The two control-unit methods land within a rounding error of each other; the univariate counterfactual is far larger.

The plot shows why, and it is not a defect in any of the three. Georgia and the donor pool lived through the same nationwide summer-2020 surge Texas did: both control-based counterfactuals climb through early July and then **level off**, because the states they are built from levelled off. Using them as the comparison removes that common shock. The univariate counterfactual cannot level off — a twice-differenced model carries June's slope forward forever, and nothing inside it can know that a national wave crested. `AI.CAUSAL_EFFECT` therefore attributes the *entire* deviation from Texas's prior trajectory to the mandate, including the part every state experienced.

**That is the identifying assumption, stated plainly:** absent the intervention, the series would have continued its own pre-intervention pattern. When no common shock hits the post-period, that is reasonable and the method is a genuine gift — it needs no control group at all. When one does, the estimate absorbs it, and there is no diagnostic inside the function that will tell you so.

**The trade runs both ways, though, and this data makes only one direction visible.** A control unit removes the common shock, but it also imports whatever else is happening in the control. Two failure modes are ordinary. If the control is itself affected by the intervention — a neighbouring state whose residents change behaviour because Texas did, a holdout market reached by the same campaign — the spillover lands in the counterfactual and biases the estimate toward zero. And if the control's own trajectory diverges for reasons unrelated to the intervention, that divergence is charged to the treatment. A univariate counterfactual cannot be contaminated in either of those ways, because there is no other unit in it. Here the common shock is large and the spillover plausibly small, so the control-based estimates are the better ones; reverse those two magnitudes and the ranking reverses with them. The choice is which bias you would rather carry, not which method is correct.

**And the significance test is doing its job.** The p-value on this data does not clear 0.05. Read together, the honest summary is not "the mandate cut cases by 56 per 100k per week"; it is that a 9-week pre-period and a 5-week post-period cannot separate a mandate effect from a cresting epidemic wave, and the function says as much if you read past the point estimate.

---
## Step 9 — `id_cols`: many series in one call

The signature accepts `id_cols`, and the obvious question is what the function does with several series at once: fit them jointly, borrow strength across them, or simply fan out. Run three states through one call and the same three states through three calls, then compare.

```python
THREE = ['TX', 'CO', 'GA']

many = client.query(f"""
SELECT subregion1_code, absolute_effect, relative_effect, p_value
FROM AI.CAUSAL_EFFECT(
  (SELECT subregion1_code, TIMESTAMP(wk) AS wk_ts, rate
   FROM `{PROJECT_ID}.{DATASET_ID}.causal_effect_panel`
   WHERE subregion1_code IN UNNEST({THREE})),
  timestamp_col          => 'wk_ts',
  data_col               => 'rate',
  intervention_timestamp => TIMESTAMP '{INTERVENTION}',
  id_cols                => ['subregion1_code'])
ORDER BY subregion1_code
""", job_config=no_cache).to_dataframe()

alone = pd.concat([
    client.query(f"""
    SELECT '{s}' AS subregion1_code, absolute_effect, relative_effect, p_value
    FROM AI.CAUSAL_EFFECT(
      (SELECT TIMESTAMP(wk) AS wk_ts, rate
       FROM `{PROJECT_ID}.{DATASET_ID}.causal_effect_panel`
       WHERE subregion1_code = '{s}'),
      timestamp_col => 'wk_ts', data_col => 'rate',
      intervention_timestamp => TIMESTAMP '{INTERVENTION}')
    """, job_config=no_cache).to_dataframe()
    for s in sorted(THREE)
], ignore_index=True)

cols = ['absolute_effect', 'relative_effect', 'p_value']
print('One call with id_cols:')
print(many.to_string(index=False))
print(f'\nLargest disagreement against three separate calls: '
      f'{(many[cols].values - alone[cols].values).__abs__().max()!r}')
```

**Verified finding — `id_cols` fans out, it does not pool.** Every value from the three-series call is *bit-identical* to the value from a call on that state alone: the largest disagreement across all nine numbers is exactly zero. Nothing is shared between series — no common trend, no pooled variance, no hierarchical shrinkage. Each `id_cols` combination gets its own `ARIMA_PLUS` fit, its own counterfactual, and its own significance test, and the only thing they have in common is the intervention timestamp.

That is worth knowing in both directions. It makes `id_cols` safe — a badly-behaved series cannot contaminate its neighbours, and one row's `status` can carry an error while the rest succeed. It also means `id_cols` buys convenience and one job's worth of overhead rather than any statistical benefit, so there is no reason to prefer it over separate calls except operational tidiness, and no reason to avoid it either.

Note the three states disagree sharply on the same date: Colorado's effect is positive, Georgia's is nearly twice Texas's in magnitude, and none of the three clears `p_value < 0.05`. Three independent univariate counterfactuals through one nationwide summer wave is precisely the situation Step 8 warns about.

---
## Step 10 — Arguments, limits, and gotchas

**The full signature**, verified live:

| Argument | Type | Notes |
|---|---|---|
| *(first, positional)* | table or subquery | the input series |
| `timestamp_col` | `STRING`, required | column holding the `TIMESTAMP` |
| `data_col` | `STRING`, required | the metric |
| `intervention_timestamp` | `TIMESTAMP` **literal**, required | splits pre from post |
| `id_cols` | `ARRAY<STRING>`, optional | `STRING`/`INT64` columns identifying separate series; each combination is analyzed independently and returns its own row — demonstrated in Step 9 |
| `num_post_intervention_points` | `INT64`, optional | cap on post-intervention points; defaults to everything through the end of the series |
| `confidence_level` | `FLOAT64` in `[0, 1)`, default `0.95` | affects the pointwise `lower_bound`/`upper_bound` only — **not** `p_value`, as Step 7 measured |
| `output_time_series` | `BOOL`, default `FALSE` | `TRUE` adds the pointwise columns |

**Gotchas**

- **`intervention_timestamp` must be a literal.** `TIMESTAMP '2020-07-03'` works; `TIMESTAMP("2020-07-03")` fails with *"expects the intervention_timestamp argument to be a TIMESTAMP literal, but TIMESTAMP was provided."* That rules out passing the date as a query parameter or computing it in the query, so parameterizing this call means string-substituting the SQL, as this notebook does.
- **There is no `model` argument.** `AI.FORECAST` accepts `model => 'TimesFM 2.5'`; passing it here fails with *"Named argument model not found in signature for call to function AI.CAUSAL_EFFECT."* The `ARIMA_PLUS` engine is fixed. So despite the `AI.` prefix and the time-series subject matter, this function shares no engine with `AI.FORECAST`.
- **No `ARIMA_PLUS` options are reachable** — no `holiday_region`, no `data_frequency`, no manual order. Defaults or nothing.
- **The three-point minimum is a floor, not a recommendation.** `status` returns *"The time series data is too short"* below three points. This notebook's 9 pre-period points already yield a counterfactual with no seasonal structure and week-5 intervals of ±200.
- **`absolute_effect` is cumulative, not per-period** — the single easiest number here to misquote by a factor of the horizon length.
- **No interval is returned on the effect.** `lower_bound` and `upper_bound` bound the *counterfactual* at each timestamp, not the cumulative gap, so the summary row offers a threshold verdict and no range. Step 7 builds the missing interval from the same two quantities the p-value uses.
- **No model artifact is produced.** The function fits its counterfactual and discards it: there is nothing to inspect, re-use, grant access to, or apply to later data, and `ML.EXPLAIN_FORECAST` has nothing to point at. Step 5's rebuild is the only way to get one.
- **A univariate counterfactual cannot see a common shock**, which is Step 8's whole finding and the reason to reach for `workflows/difference_in_differences` (`difference_in_differences`) or `workflows/synthetic_control` (`synthetic_control`) whenever a credible control unit exists.

**Preview status.** `AI.CAUSAL_EFFECT` is in Preview; arguments and output columns can change. The behaviors measured here were verified on 2026-09-11.

---
## Related content

- `workflows/difference_in_differences` (`workflows/difference_in_differences/`) and `workflows/synthetic_control` (`workflows/synthetic_control/`) — the two control-unit estimators re-derived in Step 8; both build on the same Texas panel.
- `workflows/propensity_score_matching` (`workflows/propensity_score_matching/`), `workflows/uplift_cate` (`workflows/uplift_cate/`), `workflows/price_elasticity_dml` (`workflows/price_elasticity_dml/`) — the rest of this project's causal-inference family.
- `models/arima_plus` (`models/arima_plus/`) — `ARIMA_PLUS` as a first-class model, which is what Step 5 rebuilds.
- `bq-ai-functions` (`data+ai/bq-ai-functions/`) — the sibling project covering the rest of the `AI.*` function surface, including `AI.FORECAST` and `AI.KEY_DRIVERS`. `AI.CAUSAL_EFFECT` is documented there too, pointing here.

---
## Examples — `%%bigquery` Magics

The same summary call using IPython magic commands.

```sql
%%bigquery --project {PROJECT_ID}

SELECT absolute_effect, relative_effect, p_value, prob_causal_effect
FROM AI.CAUSAL_EFFECT(
  (SELECT TIMESTAMP(wk) AS wk_ts, rate
   FROM `statmike-mlops-349915.bq_ml.causal_effect_panel`
   WHERE subregion1_code = 'TX'),
  timestamp_col          => 'wk_ts',
  data_col               => 'rate',
  intervention_timestamp => TIMESTAMP '2020-07-03'
)
```

---
## Examples — BigFrames

BigFrames has no wrapper for `AI.CAUSAL_EFFECT` — the `bigframes.bigquery` module exposes several `AI.*` functions but not this one. Run it with `bigframes.pandas.read_gbq(sql)` against the SQL above, or use the BigQuery client directly as this notebook does. `bigframes.ml.forecasting.ARIMAPlus` *is* a drop-in for Step 5's model (the same pattern shown in `models/arima_plus` (`models/arima_plus/`)), so the reproduction half of this notebook has a BigFrames path even though the function itself does not.
