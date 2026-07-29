# Data Enrichment with Search-Grounded AI.GENERATE — BigQuery AI Functions

A practical workflow for data quality improvement: given a table of business records with missing or incorrect fields, use `AI.GENERATE` with **Google Search grounding** and `output_schema` to look up real information and return corrected, complete records.

**What this demonstrates:**
- Using `AI.GENERATE` with Google Search grounding to retrieve real-world data
- Structured output with `output_schema` for type-safe results
- Data quality improvement: fixing misspellings, filling missing fields, correcting errors

**Functions used:** `functions/ai_generate` (`AI.GENERATE`) with `output_schema` and Google Search grounding

**Prerequisites:** `setup` (Setup guide) | `functions/ai_generate` (AI.GENERATE reference)

---
## Setup

Set your project and location, authenticate, and create a shared dataset.

> `AI.GENERATE` with Google Search grounding doesn't require a connection or model — it uses end-user credentials and defaults to `gemini-2.5-flash`. See the `setup` (Setup Reference) for details.

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

Imagine you have a CRM table of business contacts with typical data quality problems: misspelled names, missing cities, wrong ZIP codes, and no phone numbers. We create this scenario with a handful of well-known companies.

```python
query = f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_enrichment_businesses` AS
SELECT * FROM UNNEST([
  STRUCT('Googl' AS name, '1600 Amphitheatre Parkway' AS address, '' AS city, 'CA' AS state, '94042' AS zip_code, '' AS phone),
  STRUCT('Starbucks', '2401 Utah Avenue South', 'Seattle', 'WA', '98101', ''),
  STRUCT('Amazn', '410 Terry Ave North', 'Seattle', 'WA', '', ''),
  STRUCT('Apple Inc', 'One Apple Park Way', '', 'CA', '95014', ''),
  STRUCT('Microsft', 'One Microsoft Way', 'Redmond', 'WA', '98052', ''),
  STRUCT('Tesla Motors', '1 Tesla Road', '', 'TX', '78701', '')
])
'''
client.query(query).result()

# Display the messy source data
source = client.query(
    f'SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.workflow_enrichment_businesses`'
).to_dataframe()
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
- **Names fixed**: "Googl" → "Google", "Amazn" → "Amazon", "Microsft" → "Microsoft"
- **Missing cities filled**: Google, Apple, Tesla now have correct cities
- **ZIP codes corrected**: wrong ZIP codes fixed to match actual headquarters
- **Phone numbers added**: all businesses now have phone numbers
- **New fields**: website and business_type added for every record

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
```
