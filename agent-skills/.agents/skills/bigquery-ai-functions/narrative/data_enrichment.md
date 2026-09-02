# Data Enrichment — BigQuery AI Functions

A practical workflow for data quality improvement: given a table of business records with missing or incorrect fields, fill the gaps two different ways. `AI.GENERATE` with **Google Search grounding** and `output_schema` looks up real-world facts the table never contained. `AI.PREDICT` infers a missing structured attribute from the rows you already have.

**What this demonstrates:**
- Using `AI.GENERATE` with Google Search grounding to retrieve real-world data
- Structured output with `output_schema` for type-safe results
- Data quality improvement: fixing misspellings, filling missing fields, correcting errors
- Using `AI.PREDICT` (TabFM) to fill a missing categorical column from the table's own structure, with a per-class probability array as the confidence signal generative enrichment does not give you
- Scoring both routes against a human answer key in code, and reading what a low tabular score says about the features rather than about the function

**Functions used:** `functions/ai_generate` (`AI.GENERATE`) with `output_schema` and Google Search grounding | `functions/ai_predict` (`AI.PREDICT`)

**Runtime and cost before you Run All:** the seed table holds **24** business records. Step 3 issues **two `AI.GENERATE` calls per record — 48 calls** — and is by far the longest-running cell in this notebook; budget several minutes for it. Step 5 adds exactly one `AI.PREDICT` call. Both scale directly with the seed row count, so trimming the `UNNEST` list in Step 1 is the way to make a cheaper run.

**Prerequisites:** `setup` (Setup guide) | `RESOURCES.md` (Function reference)

---
## Setup

Set your project and location, authenticate, and create a shared dataset.

> `AI.GENERATE` with Google Search grounding doesn't require a connection or model — it uses end-user credentials and defaults to `gemini-2.5-flash`. `AI.PREDICT` likewise needs no connection, no model object, and no `CREATE MODEL` step: it runs the pre-trained TabFM tabular foundation model on end-user credentials. See the `setup` (Setup Reference) for details.

```python
PROJECT_ID = 'statmike-mlops-349915'  # <-- Replace with your project ID
LOCATION = 'US'  # BigQuery dataset location
DATASET_ID = 'bq_ai_functions'  # Shared dataset across all notebooks
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

```python
from pydantic import BaseModel, Field
from typing import get_origin, get_args

# Python type → BigQuery type
_BQ_TYPES = {str: 'STRING', int: 'INT64', float: 'FLOAT64', bool: 'BOOL'}

def _bq_type(annotation) -> str:
    """Map a Python type annotation to a BigQuery type string."""
    if get_origin(annotation) is list:
        inner = _BQ_TYPES[get_args(annotation)[0]]
        return f'ARRAY<{inner}>'
    return _BQ_TYPES[annotation]

def bq_schema(model: type[BaseModel]) -> str:
    """Convert a Pydantic model to a BigQuery output_schema string.

    Supports str, int, float, bool, and list[T].
    Field descriptions become OPTIONS(description = '...').
    """
    fields = []
    for name, info in model.model_fields.items():
        field_str = f'{name} {_bq_type(info.annotation)}'
        if info.description:
            field_str += f" OPTIONS(description = '{info.description}')"
        fields.append(field_str)
    return ', '.join(fields)
```

---
## Step 1 — Create source data with quality issues

Imagine you have a CRM table of 24 business contacts with typical data quality problems: misspelled names, missing cities, blank ZIP codes, and no phone numbers at all.

Two kinds of gap live in this table, and the difference between them is the whole reason Step 5 works:

- **The text fields encode "missing" as an empty string.** `city`, `zip_code`, and `phone` use `''`, the way a great many CRM exports do. Step 3 fills those from the web.
- **`sector` encodes "missing" as a real `NULL`.** Six of the 24 records have no sector. Step 5 splits training rows from prediction rows with `WHERE sector IS NOT NULL` / `WHERE sector IS NULL`, and that split only does anything on true `NULL`s. An empty string is a value: it would put all 24 rows in the training set and leave nothing to predict.

Two structured columns come along for the ride — `founded_year` and `employees_thousands` — because a tabular model needs something to reason over other than unique per-row identifiers.

```python
query = f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_enrichment_businesses` AS
SELECT * FROM UNNEST([
  -- Technology
  STRUCT('Googl' AS name, '1600 Amphitheatre Parkway' AS address, '' AS city, 'CA' AS state, '94042' AS zip_code, '' AS phone, 1998 AS founded_year, 183 AS employees_thousands, CAST(NULL AS STRING) AS sector),
  STRUCT('Microsft', 'One Microsoft Way', 'Redmond', 'WA', '98052', '', 1975, 228, 'Technology'),
  STRUCT('Apple Inc', 'One Apple Park Way', '', 'CA', '95014', '', 1976, 164, 'Technology'),
  STRUCT('Nvidia Corp', '2788 San Tomas Expressway', 'Santa Clara', 'CA', '', '', 1993, 30, 'Technology'),
  -- Retail
  STRUCT('Amazn', '410 Terry Ave North', 'Seattle', 'WA', '', '', 1994, 1556, 'Retail'),
  STRUCT('Starbucks', '2401 Utah Avenue South', 'Seattle', 'WA', '98101', '', 1971, 381, 'Retail'),
  STRUCT('Walmart', '702 SW 8th Street', 'Bentonville', 'AR', '72716', '', 1962, 2100, 'Retail'),
  STRUCT('Costco Wholsale', '999 Lake Drive', 'Issaquah', 'WA', '98027', '', 1983, 333, CAST(NULL AS STRING)),
  -- Automotive
  STRUCT('Tesla Motors', '1 Tesla Road', '', 'TX', '78701', '', 2003, 141, 'Automotive'),
  STRUCT('Ford Motor Company', 'One American Road', 'Dearborn', 'MI', '48126', '', 1903, 177, 'Automotive'),
  STRUCT('General Motrs', '300 Renaissance Center', 'Detroit', 'MI', '', '', 1908, 163, 'Automotive'),
  STRUCT('Rivian', '14600 Myford Road', '', 'CA', '92606', '', 2009, 15, CAST(NULL AS STRING)),
  -- Finance
  STRUCT('JPMorgan Chase', '383 Madison Avenue', 'New York', 'NY', '10179', '', 1799, 309, 'Finance'),
  STRUCT('Goldman Sachs', '200 West Street', 'New York', 'NY', '10282', '', 1869, 46, 'Finance'),
  STRUCT('Amercan Express', '200 Vesey Street', '', 'NY', '10285', '', 1850, 74, 'Finance'),
  STRUCT('Charles Schwab', '3000 Schwab Way', 'Westlake', 'TX', '76262', '', 1971, 32, CAST(NULL AS STRING)),
  -- Healthcare
  STRUCT('UnitedHealth Group', '9900 Bren Road East', 'Minnetonka', 'MN', '55343', '', 1977, 400, 'Healthcare'),
  STRUCT('CVS Health', '1 CVS Drive', 'Woonsocket', 'RI', '02895', '', 1963, 300, 'Healthcare'),
  STRUCT('Pfizer Inc', '66 Hudson Boulevard East', 'New York', 'NY', '', '', 1849, 88, 'Healthcare'),
  STRUCT('Eli Lily', '893 Delaware Street', 'Indianapolis', 'IN', '46225', '', 1876, 43, CAST(NULL AS STRING)),
  -- Logistics
  STRUCT('FedEx Corporation', '942 South Shady Grove Road', 'Memphis', 'TN', '38120', '', 1971, 500, 'Logistics'),
  STRUCT('United Parcel Servce', '55 Glenlake Parkway NE', 'Atlanta', 'GA', '30328', '', 1907, 490, 'Logistics'),
  STRUCT('Union Pacific Railroad', '1400 Douglas Street', 'Omaha', 'NE', '68179', '', 1862, 32, 'Logistics'),
  STRUCT('J.B. Hunt Transport', '615 J.B. Hunt Corporate Drive', 'Lowell', 'AR', '', '', 1961, 34, CAST(NULL AS STRING))
])
'''
client.query(query).result()

# Display the messy source data
source = client.query(
    f'SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.workflow_enrichment_businesses`'
).to_dataframe()
print(f'{len(source)} records, {source["sector"].notna().sum()} with a known sector, '
      f'{source["sector"].isna().sum()} awaiting one')
source
```

---
## Step 2 — Define the enrichment schema

Define the output structure using a Pydantic model. Each field has a description that guides the model on what information to return. The `bq_schema()` helper converts this to BigQuery's `output_schema` format.

```python
class BusinessInfo(BaseModel):
    name: str = Field(description='Corrected official business name')
    address: str = Field(description='Street address of headquarters')
    city: str = Field(description='City of headquarters')
    state: str = Field(description='US state two-letter abbreviation')
    zip_code: str = Field(description='5-digit ZIP code')
    phone: str = Field(description='Main phone number with area code')
    website: str = Field(description='Official website URL')
    business_type: str = Field(description='Industry or business type, e.g. Technology, Retail')

print(bq_schema(BusinessInfo))
```

---
## Step 3 — Enrich with grounded AI.GENERATE

Google Search grounding and `output_schema` are used in two steps because grounding produces text with citations that can't be directly parsed into a typed schema:

1. **Grounded lookup** (CTE): `AI.GENERATE` with Google Search looks up real information for each business and returns it as text
2. **Structured extraction** (outer query): a second `AI.GENERATE` with `output_schema` parses the grounded text into typed fields

```python
output_schema = bq_schema(BusinessInfo)

query = f'''
WITH grounded AS (
  SELECT
    source.name AS original_name,
    (AI.GENERATE(
      CONCAT(
        'Look up this business and provide its correct headquarters information: ',
        'official name, street address, city, state, ZIP code, phone number, website URL, and type of business. ',
        'Business name: ', source.name,
        ', Address: ', source.address,
        ', City: ', source.city,
        ', State: ', source.state,
        ', ZIP: ', source.zip_code
      ),
      model_params => JSON '{{"tools": [{{"googleSearch": {{}}}}]}}'
    )).result AS lookup_text
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_enrichment_businesses` AS source
)
SELECT
  g.original_name,
  result.name,
  result.address,
  result.city,
  result.state,
  result.zip_code,
  result.phone,
  result.website,
  result.business_type
FROM grounded AS g,
UNNEST([
  AI.GENERATE(
    CONCAT(
      'Extract the business information from this text into the structured fields. ',
      'If any value is not found, return an empty string — never return the word null. ',
      'Text: ', g.lookup_text
    ),
    output_schema => """{output_schema}"""
  )
]) AS result
'''
enriched = client.query(query).to_dataframe()
enriched
```

---
## Step 4 — Compare original vs enriched

Compare the messy input with the AI-corrected results. Look for:
- **Names fixed**: "Googl" → "Google", "Amazn" → "Amazon", "Microsft" → "Microsoft", "Costco Wholsale" → "Costco Wholesale", "Eli Lily" → "Eli Lilly"
- **Missing cities filled**: Google, Apple, Tesla, American Express, and Rivian now have correct cities
- **ZIP codes corrected**: wrong and blank ZIP codes fixed to match actual headquarters
- **Phone numbers added**: the source table has none at all; the cell below counts how many come back filled
- **New fields**: website and business_type, neither of which exists in the source table

Not every field comes back populated. The extraction prompt in Step 3 says "If any value is not found, return an empty string — never return the word null", and the cell below still names any record that ends up without a phone. When one appears, the value is a true `NULL`, not the empty string the prompt asked for. A prompt instruction shapes what an `output_schema` field contains; it does not guarantee the field is populated, so downstream code has to handle both the empty string and the `NULL`.

`business_type` deserves a second look before moving on. It is free text the model retrieved from the web: it is not constrained to any fixed vocabulary, two records describing the same industry can word it differently, and it arrives with no indication of how confident the model is. Step 5 fills the same kind of attribute a completely different way.

```python
from IPython.display import display

# Reload original for side-by-side comparison
original = client.query(
    f'SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.workflow_enrichment_businesses`'
).to_dataframe()

# Sort both by original name so rows align
original_sorted = original.sort_values('name').reset_index(drop=True)
enriched_sorted = enriched.sort_values('original_name').reset_index(drop=True)

print("ORIGINAL (messy input):\n")
display(original_sorted)

print("\nENRICHED (corrected via AI.GENERATE + Google Search):\n")
display(enriched_sorted[['original_name', 'name', 'address', 'city', 'state', 'zip_code', 'phone', 'website', 'business_type']])

# Count what the enrichment actually filled, rather than asserting it
def filled(series):
    """A field counts as filled only if it is non-NULL and not blank."""
    return series.notna() & (series.astype(str).str.strip() != '')

print('\nFIELD FILL AFTER ENRICHMENT:\n')
for col in ['city', 'state', 'zip_code', 'phone', 'website', 'business_type']:
    print(f'  {col:>14}: {int(filled(enriched_sorted[col]).sum())} of {len(enriched_sorted)} populated')

no_phone = enriched_sorted.loc[~filled(enriched_sorted['phone']), 'original_name'].tolist()
print('\nRecords with no phone after enrichment:', no_phone or 'none')
```

---
## Step 5 — Fill a missing structured attribute with AI.PREDICT

Step 3 answered a question this table could not: it went out to the web and brought back facts that were never in the data. `AI.PREDICT` answers a different kind of question — one the data can already answer, if you read all the rows at once.

`sector` is `NULL` on six records. The other 18 carry a sector alongside a state, a founding year, and a headcount. That is a labeled training set, which makes the following a testable hypothesis: automakers cluster in Michigan and are a century old, banks cluster in New York and are older still, technology firms are young and Californian — so a classifier reading those three columns should recover the pattern and label the six unlabeled rows. Whether 18 rows of three weak features actually carry that signal is an empirical question, and the scoring cell after the prediction answers it.

`AI.PREDICT` runs the pre-trained **TabFM** tabular foundation model. There is no `CREATE MODEL` step, no training job, no connection, and no artifact left behind. You hand it a training query and a prediction query in a single call:

```
AI.PREDICT(
  { TABLE training_table | (training_query) },
  { TABLE prediction_table | (prediction_query) }
  [, label_col => 'LABEL_COL' ]
)
```

Because the label column is a `STRING`, this is a classification task, and the output carries two prediction columns: `predicted_sector`, and `predicted_sector_probs` — an `ARRAY<STRUCT<label STRING, prob FLOAT64>>` holding a probability for every class seen in training.

**Feature selection matters.** The training query deliberately passes only `state`, `founded_year`, and `employees_thousands`. Every column left out — `name`, `address`, `city`, `zip_code`, `phone` — is a unique-per-row identifier with no signal that transfers to a new row. The prediction query adds `name` back purely as a passthrough so the results are readable; `AI.PREDICT` allows the prediction side to carry extra columns beyond the feature set.

Two documented limits shape the design: at most **20 feature columns** and at most **10 classes**. This example uses 3 features and 6 sectors.

Here is what someone who knows these companies would write in. The cell after the prediction scores both routes against this key instead of leaving you to eyeball them:

| Record | Sector a human would assign |
|---|---|
| Googl | Technology |
| Costco Wholsale | Retail |
| Rivian | Automotive |
| Charles Schwab | Finance |
| Eli Lily | Healthcare |
| J.B. Hunt Transport | Logistics |

> `AI.PREDICT` is in Preview. One call takes roughly 30–95 seconds no matter how small the input is, so expect this cell to run for about a minute.

```python
query = f'''
WITH predictions AS (
  SELECT *
  FROM AI.PREDICT(
    -- Training data: the 18 records whose sector is already known
    (SELECT state, founded_year, employees_thousands, sector
     FROM `{PROJECT_ID}.{DATASET_ID}.workflow_enrichment_businesses`
     WHERE sector IS NOT NULL),
    -- Prediction data: the 6 records whose sector is NULL
    (SELECT name, state, founded_year, employees_thousands
     FROM `{PROJECT_ID}.{DATASET_ID}.workflow_enrichment_businesses`
     WHERE sector IS NULL),
    label_col => 'sector')
)
SELECT
  name,
  state,
  founded_year,
  employees_thousands,
  predicted_sector,
  ROUND((SELECT p.prob FROM UNNEST(predicted_sector_probs) AS p WHERE p.label = predicted_sector), 4) AS confidence,
  ARRAY(
    SELECT AS STRUCT p.label, ROUND(p.prob, 4) AS prob
    FROM UNNEST(predicted_sector_probs) AS p
    ORDER BY p.prob DESC
    LIMIT 3
  ) AS top_3_sectors
FROM predictions
ORDER BY confidence DESC
'''
predicted = client.query(query).to_dataframe()
predicted
```

```python
# Score both routes against the answer key in the markdown above
answer_key = {
    'Googl': 'Technology',
    'Costco Wholsale': 'Retail',
    'Rivian': 'Automotive',
    'Charles Schwab': 'Finance',
    'Eli Lily': 'Healthcare',
    'J.B. Hunt Transport': 'Logistics',
}

# The grounded route returns open free text, so comparing it to the key at all needs a
# hand-written normalizer into the closed vocabulary. Most-specific first, because one
# description can name several industries. Needing this step is itself part of the result.
VOCABULARY = [
    (('automotive', 'vehicle', 'automaker'), 'Automotive'),
    (('pharmaceutical', 'health', 'biotech', 'medical'), 'Healthcare'),
    (('logistics', 'transportation', 'freight', 'railroad', 'delivery', 'courier'), 'Logistics'),
    (('financial', 'finance', 'bank', 'brokerage', 'investment'), 'Finance'),
    (('retail', 'wholesale', 'grocery'), 'Retail'),
    (('technology', 'software', 'semiconductor', 'electronics'), 'Technology'),
]

def to_vocabulary(text):
    """Map a free-text business_type onto one of the six training sectors, or None."""
    lowered = (text or '').lower()
    for words, sector in VOCABULARY:
        if any(word in lowered for word in words):
            return sector
    return None

grounded_type = dict(zip(enriched['original_name'], enriched['business_type']))

scorecard = pd.DataFrame([
    {
        'name': row['name'],
        'answer_key': answer_key.get(row['name']),
        'tabfm_predicted': row['predicted_sector'],
        'confidence': row['confidence'],
        'grounded_business_type': grounded_type.get(row['name']),
        'grounded_mapped': to_vocabulary(grounded_type.get(row['name'])),
    }
    for _, row in predicted.iterrows()
])
scorecard['tabfm_match'] = scorecard['tabfm_predicted'] == scorecard['answer_key']
scorecard['grounded_match'] = scorecard['grounded_mapped'] == scorecard['answer_key']

display(scorecard[['name', 'answer_key', 'tabfm_predicted', 'confidence', 'tabfm_match',
                   'grounded_mapped', 'grounded_match', 'grounded_business_type']])

n = len(scorecard)
print(f'AI.PREDICT / TabFM (Step 5) matches the key : {int(scorecard.tabfm_match.sum())} of {n}')
print(f'Grounded business_type (Step 3), normalized : {int(scorecard.grounded_match.sum())} of {n}')
print('\nRows AI.PREDICT got wrong:', scorecard.loc[~scorecard.tabfm_match, 'name'].tolist() or 'none')
print('Free-text descriptions the normalizer could not place:',
      scorecard.loc[scorecard.grounded_mapped.isna(), 'name'].tolist() or 'none')

top = scorecard.sort_values('confidence', ascending=False).iloc[0]
print(f"\nHighest-confidence prediction: {top['name']} -> {top['tabfm_predicted']} "
      f"(p={top['confidence']:.4f}); matches the key: {bool(top['tabfm_match'])}")
```

### Reading the score

The two counts above are the point of this notebook. The tabular route is reading three columns that barely distinguish these rows, and that is visible in the training table rather than in the function:

- **`state` is nearly an identifier.** The 18 labeled rows span 11 distinct states. Of the six rows to be predicted, `CA` appears in training only as Technology, `AR` only as Retail, `TX` only as Automotive, and `IN` does not appear at all — so for Eli Lilly the state column carries no information whatsoever.
- **`founded_year` is worse.** 18 rows hold 17 distinct years, so the column is almost a row id; only 1971 repeats, and it repeats across two different sectors.
- **`employees_thousands` cannot separate the sectors that matter here.** The nearest labeled row to Eli Lilly's 43 thousand employees is Goldman Sachs at 46 thousand — a bank. A 43k pharmaceutical company and a 46k bank are neighbors in the only continuous feature available, which is the kind of neighborhood that produces a confident wrong answer rather than an uncertain one.
- **The real signal is in the column that was correctly excluded.** A human fills in that answer key by reading the company names. `name` is a unique-per-row identifier, so it must stay out of the feature set — and it is exactly what Step 3 sent to Google Search. The sector is public knowledge attached to the name, not a pattern in state, year, and headcount.

So the scoring cell is not a verdict on `AI.PREDICT`; it is a verdict on the features. TabFM ran zero-shot on 18 rows, returned a well-formed probability vector for every row, and never signalled that its inputs could not support the question. That is the risk of zero-shot tabular inference on a small, weak-feature table: it always answers.

Two practical consequences. First, check the highest-confidence line the cell prints. The probability is the model's split of mass over six classes, not a measured accuracy — on this data the most confident row can easily be a wrong one, so a routing threshold has to be validated against a labeled holdout before it is trusted. Second, `AI.PREDICT` output is not bit-stable: an identical call can return slightly different probabilities on a later run, which is why the score is computed in the notebook rather than written into this paragraph.

### Generative enrichment vs tabular prediction

Both steps filled a blank. They are not interchangeable.

| | `AI.GENERATE` + Google Search (Step 3) | `AI.PREDICT` / TabFM (Step 5) |
|---|---|---|
| Where the answer comes from | The public web | The other rows in your own table |
| Fact is not derivable from your data | Works — that is the point | Cannot help |
| Fact is private to your data | Cannot help | Works |
| Output vocabulary | Open — free text, whatever the model writes | Closed — only classes present in the training rows |
| Confidence signal | None | `predicted_sector_probs`, one probability per class — a split of mass, not a measured accuracy |
| Runs without live web content | No | Yes |
| Cost shape | Per row, per call | One call for the whole batch |

The `confidence` column is the practical difference. A grounded lookup hands back `business_type` as a bare string with nothing to threshold on, so a wrong answer looks exactly like a right one. `predicted_sector_probs` is what a routing rule can be built on: send low-probability rows to a human, auto-apply the rest. The scoring cell shows why that rule needs a labeled holdout before it is switched on — a probability is the model's split of mass across the six training classes, not a measured accuracy rate, so "most confident" and "most likely correct" are not the same column. On this table, with three features and 18 training rows, the honest read of the score is to auto-apply none of it.

The rule of thumb: reach for grounded generation when the missing value lives in the world, and for `AI.PREDICT` when the missing value lives in the pattern of the rows you already have. In this notebook `business_type` and `sector` describe the same idea from the two different directions in the table above — open free text with no confidence attached, versus a closed vocabulary with a probability vector — and the scoring cell shows which direction this particular question belonged to. A company's sector is public knowledge encoded in its name, so it was a grounding problem all along; the tabular route only ever saw the columns that survived feature selection, and the name was not one of them. Pick the route by where the answer lives, not by which function is more convenient.
