# Feature Engineering — BigQuery ML Model-Free Functions

Three functions that build new features rather than just rescaling existing ones: `ML.IMPUTER` (fill `NULL`s with a train-time statistic), `ML.FEATURE_CROSS` (categorical interaction terms), and `ML.POLYNOMIAL_EXPAND` (numeric interaction/power terms). All three are **scalar or analytic**, usable standalone or inside a `CREATE MODEL ... TRANSFORM(...)` clause — but not all of them survive being exported afterward.

**When to use these:**
- `ML.IMPUTER` — fill missing values with `mean`/`median` (numeric) or `most_frequent` (numeric or string), reusing the exact training-time statistic at predict time.
- `ML.FEATURE_CROSS` — give a linear/logistic model access to interactions between categorical columns it can't learn on its own (e.g. `region` × `device`).
- `ML.POLYNOMIAL_EXPAND` — add squared/cubic/interaction terms so a linear model can fit curvature, without writing `col1*col2` by hand.

**Data:** [`bigquery-public-data.ml_datasets.penguins`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) — same dataset as `functions/scalers` (`functions/scalers/`) and `models/transform_only` (Transform-Only).

**Featured in:** `models/transform_only` (`models/transform_only/`) (`ML.IMPUTER` chained with scalers into a reusable pipeline).

**References:** `RESOURCES.md` (Full reference) | [`ML.IMPUTER` docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-imputer) | [`ML.FEATURE_CROSS` docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-feature-cross) | [`ML.POLYNOMIAL_EXPAND` docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-polynomial-expand) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a shared dataset. No connection needed.

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
## Step 1 — `ML.IMPUTER`: fill `NULL`s with a train-time statistic

Analytic function — requires `OVER()` because it needs to compute a statistic (mean/median/mode) across every row first, then broadcast that single value back to each row that had a `NULL`. `strategy` is required — `'mean'`/`'median'` (numeric only) or `'most_frequent'` (works on **either** numeric or string columns, unlike `mean`/`median`).

```python
query = """
SELECT
  body_mass_g,
  ML.IMPUTER(body_mass_g, 'mean') OVER() AS imputed_mean,
  ML.IMPUTER(body_mass_g, 'median') OVER() AS imputed_median,
  ML.IMPUTER(body_mass_g, 'most_frequent') OVER() AS imputed_mode,
  ML.IMPUTER(sex, 'most_frequent') OVER() AS sex_imputed_mode
FROM `bigquery-public-data.ml_datasets.penguins`
ORDER BY body_mass_g IS NULL DESC
LIMIT 3
"""
client.query(query).to_dataframe()
```

---
## Step 2 — `ML.IMPUTER` embedded in `TRANSFORM`: exportable, auto-applies at `ML.PREDICT`

Unlike the two functions in the rest of this notebook, `ML.IMPUTER` **is** exportable when embedded in a `TRANSFORM` clause — it plugs into a real model with no restrictions.

```python
query = """
CREATE OR REPLACE MODEL `{project}.{dataset}.feature_engineering_imputer_downstream`
TRANSFORM(
  species,
  ML.IMPUTER(body_mass_g, 'mean') OVER() AS body_mass_imputed,
  culmen_length_mm, culmen_depth_mm, flipper_length_mm
)
OPTIONS(model_type = 'LOGISTIC_REG', input_label_cols = ['species']) AS
SELECT species, body_mass_g, culmen_length_mm, culmen_depth_mm, flipper_length_mm
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE culmen_length_mm IS NOT NULL AND culmen_depth_mm IS NOT NULL AND flipper_length_mm IS NOT NULL
""".format(project=PROJECT_ID, dataset=DATASET_ID)
client.query(query).result()
print('Model feature_engineering_imputer_downstream created')
```

**Verified:** predicting with a `NULL` `body_mass_g` at predict time still works correctly — the model auto-imputes using the **training** mean, no error, no special handling needed by the caller.

```python
query = f"""
SELECT species, body_mass_g, predicted_species
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.feature_engineering_imputer_downstream`,
  (SELECT species, CAST(NULL AS FLOAT64) AS body_mass_g, culmen_length_mm, culmen_depth_mm, flipper_length_mm
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE culmen_length_mm IS NOT NULL AND culmen_depth_mm IS NOT NULL AND flipper_length_mm IS NOT NULL
   LIMIT 3)
)
"""
client.query(query).to_dataframe()
```

---
## Step 3 — `ML.FEATURE_CROSS`: categorical interaction terms

Scalar function (no `OVER()`). Given a `STRUCT` of categorical columns, returns a `STRUCT` of all pairwise (or higher-degree) combinations, each concatenated as `<col_a>_<col_b>`.

```python
query = """
SELECT island, sex,
  ML.FEATURE_CROSS(STRUCT(island, sex)) AS crossed
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE sex IS NOT NULL
LIMIT 3
"""
client.query(query).to_dataframe()
```

`degree` (default `2`, range `[2,4]`) controls how many columns get crossed together at once — a 3-column `STRUCT` with `degree=3` adds the full triple-cross on top of every pairwise cross:

```python
query = """
SELECT island, sex, species,
  ML.FEATURE_CROSS(STRUCT(island, sex, species), 3) AS crossed_degree3
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE sex IS NOT NULL
LIMIT 2
"""
client.query(query).to_dataframe()
```

---
## Step 4 — `ML.FEATURE_CROSS` in a real `TRANSFORM`: trains and predicts fine, but isn't exportable

The legacy source material this notebook draws from only ever showed `ML.FEATURE_CROSS` standalone — never actually plugged into a live `CREATE MODEL`. It turns out it works completely normally for training and `ML.PREDICT`; the "not exportable" limitation only bites at `EXPORT MODEL` time, not before.

```python
query = """
CREATE OR REPLACE MODEL `{project}.{dataset}.scratch_featurecross_transform_demo`
TRANSFORM(
  species,
  ML.FEATURE_CROSS(STRUCT(island, sex)) AS island_sex_cross
)
OPTIONS(model_type = 'LOGISTIC_REG', input_label_cols = ['species']) AS
SELECT species, island, sex
FROM `bigquery-public-data.ml_datasets.penguins`
""".format(project=PROJECT_ID, dataset=DATASET_ID)
client.query(query).result()
print('Trains fine -- TRANSFORM with ML.FEATURE_CROSS is not rejected at CREATE MODEL time')

query = f"""
SELECT species, predicted_species
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.scratch_featurecross_transform_demo`,
  (SELECT species, island, sex FROM `bigquery-public-data.ml_datasets.penguins` LIMIT 3)
)
"""
print('ML.PREDICT also works fine:')
display(client.query(query).to_dataframe())
```

```python
try:
    query = f"""
    EXPORT MODEL `{PROJECT_ID}.{DATASET_ID}.scratch_featurecross_transform_demo`
    OPTIONS (URI = 'gs://{PROJECT_ID}/bq_ml/feature_engineering/scratch_export/')
    """
    client.query(query).result()
    print('Export succeeded (!) -- Google may have changed this limitation since it was last verified')
except Exception as e:
    print(f'Export failed as expected: {type(e).__name__}: {str(e)[:400]}')

client.query(f"DROP MODEL IF EXISTS `{PROJECT_ID}.{DATASET_ID}.scratch_featurecross_transform_demo`").result()
print('Scratch model dropped')
```

Same limitation applies to `ML.POLYNOMIAL_EXPAND` below (per RESOURCES.md — not independently re-verified with its own `try/except` here, to avoid a redundant second live `EXPORT MODEL` failure demo). A model that needs portability/serving outside BigQuery (`EXPORT MODEL`, `model_registry='VERTEX_AI'`, `models/remote` (`models/remote/`)) must compute crosses/polynomial terms in the **input query** instead of inside `TRANSFORM`.

---
## Step 5 — `ML.POLYNOMIAL_EXPAND`: numeric interaction/power terms

Scalar function (no `OVER()`). Given a `STRUCT` of **named** numeric features (≤10, no duplicates), returns all polynomial combinations up to `degree` (default 2, range [1,4]), including the originals.

```python
query = """
SELECT
  culmen_length_mm, culmen_depth_mm,
  ML.POLYNOMIAL_EXPAND(STRUCT(culmen_length_mm AS length, culmen_depth_mm AS depth), 2) AS expanded
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE culmen_length_mm IS NOT NULL AND culmen_depth_mm IS NOT NULL
LIMIT 2
"""
client.query(query).to_dataframe()
```

`degree` (default `2`, range `[1,4]`) controls the highest power/interaction order. `degree=3` on a single feature adds the cube term on top of the square:

```python
query = """
SELECT culmen_length_mm,
  ML.POLYNOMIAL_EXPAND(STRUCT(culmen_length_mm AS length), 3) AS expanded_degree3
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE culmen_length_mm IS NOT NULL
LIMIT 2
"""
client.query(query).to_dataframe()
```

---
## Step 6 — Compounding: a scalar function CAN wrap an analytic function's result

**GOTCHA:** an analytic function cannot be an argument to *another* analytic function, but a **scalar** function (`ML.POLYNOMIAL_EXPAND`, `ML.FEATURE_CROSS`) *can* take an analytic function's result (`ML.IMPUTER`) as an argument. This lets you impute-then-expand in one expression.

```python
query = """
SELECT
  body_mass_g,
  ML.POLYNOMIAL_EXPAND(
    STRUCT(ML.IMPUTER(body_mass_g, 'mean') OVER() AS mass_imputed),
    2
  ) AS expanded
FROM `bigquery-public-data.ml_datasets.penguins`
ORDER BY body_mass_g IS NULL DESC
LIMIT 3
"""
client.query(query).to_dataframe()
```

---
## Examples — `%%bigquery` Magics

The same operations using IPython magic commands — write SQL directly in cells without Python string wrapping.

```sql
%%bigquery --project {PROJECT_ID}

SELECT island, sex,
  ML.FEATURE_CROSS(STRUCT(island, sex)) AS crossed
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE sex IS NOT NULL
LIMIT 3
```

---
## Examples — BigFrames

`bigframes.ml.impute.SimpleImputer` maps to `ML.IMPUTER`, and `bigframes.ml.preprocessing.PolynomialFeatures` maps to `ML.POLYNOMIAL_EXPAND`. There is **no** direct equivalent for `ML.FEATURE_CROSS` — build categorical crosses via ordinary DataFrame column operations instead.

```python
import bigframes.pandas as bpd
from bigframes.ml.impute import SimpleImputer
from bigframes.ml.preprocessing import PolynomialFeatures

bpd.close_session()  # Reset session to apply project/location settings
bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION

df = bpd.read_gbq("SELECT body_mass_g FROM `bigquery-public-data.ml_datasets.penguins`")
imputer = SimpleImputer(strategy='mean')
imputer.fit(df[['body_mass_g']])
imputer.transform(df[['body_mass_g']]).peek()
```

```python
df2 = bpd.read_gbq(
    "SELECT culmen_length_mm, culmen_depth_mm FROM `bigquery-public-data.ml_datasets.penguins` "
    "WHERE culmen_length_mm IS NOT NULL AND culmen_depth_mm IS NOT NULL"
)
poly = PolynomialFeatures(degree=2)
poly.fit(df2[['culmen_length_mm', 'culmen_depth_mm']])
poly.transform(df2[['culmen_length_mm', 'culmen_depth_mm']]).peek()
```
