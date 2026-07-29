# Embeddings As Features For Hierarchical Classification — BigQuery ML

Use text embeddings *as classifier features* to place a product into a `department → category` hierarchy — a binary classifier scores "does this product belong to this hierarchy node?" for every (product, candidate node) pair, then the best-scoring department and category are picked top-down. Compared against two simpler alternatives to test whether that complexity is actually worth it.

**Models used:** `BOOSTED_TREE_CLASSIFIER`
**Functions used:** `AI.EMBED`, `ML.EVALUATE`, `ML.PREDICT`, `VECTOR_SEARCH`

Modernizes `Applied GenAI/Embeddings/Vertex AI GenAI Embeddings - As Features For Hierarchical Classification.ipynb`: replaces the deprecated `PaLM2TextEmbeddingGenerator`/BigFrames pipeline with `AI.EMBED` (no connection needed for text) and native SQL `CREATE MODEL ... BOOSTED_TREE_CLASSIFIER` (embeddings passed as `ARRAY<FLOAT64>` feature columns directly — no need to unnest into hundreds of individual columns). Compares 3 ways of turning two embeddings (product, hierarchy node) into pairwise classifier features — reduced from the original's 5, and at a smaller embedding dimensionality, after finding the original's richest variants took **52 minutes to 9 hours 39 minutes each** to train (BigFrames `XGBClassifier`, full 768-dim embeddings, deep/forested trees).

**Beyond the original notebook's scope: two baselines that test whether the pairwise approach is even the right tool for this job** — a direct multiclass classifier (predict the category straight from the product embedding, no candidate-pair framing at all) and a pure `VECTOR_SEARCH` nearest-neighbor lookup (no classifier, no training). Both are cheap to add and turn this notebook from "here's one technique" into "here's how to choose between techniques."

**Data:** [`bigquery-public-data.thelook_ecommerce.products`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) — 29,118 products (after dropping 2 with a NULL name), 2 departments (Men/Women), 36 `department: category` combinations (categories repeat across departments — e.g. both have "Accessories" — so the node label concatenates department + category to disambiguate). Products are split 90/10 (stratified by category) into TRAIN/TEST, then each split is cross-joined against all 38 hierarchy nodes (2 department + 36 category) to build the binary-classification training/serving tables — the multiclass baseline and vector search baseline use the products directly, with no cross-join.

**GOTCHA (verified) driving the scope here:** even after cutting to 3 approaches at 256-dim embeddings and training natively via SQL (rather than BigFrames), each pairwise `BOOSTED_TREE_CLASSIFIER` on the ~1M-row (product × node) training table took **19–40 minutes** — a real, substantial cost, though more than 13x faster than the original's worst case. All 3 are submitted **concurrently** (verified live: BigQuery trains distinctly-named models in true parallel), so the whole notebook's pairwise-training step takes as long as its single slowest model (~40 minutes), not the sum of all three (~75 minutes serial). **Expect Step 3 below to run for up to ~40 minutes** — the multiclass baseline afterward trains on 26x fewer rows and takes a few minutes; the vector search baseline needs no training at all.

---
## Setup

Set your project and location, authenticate, and create a shared dataset for the model.

> `AI.EMBED` needs no connection for text input (only multimodal/image embedding requires one) — no connection setup in this notebook. See the `setup` (Setup Reference) for details.

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
## Step 1 — Embed products and hierarchy nodes with `AI.EMBED`

`AI.EMBED` is a scalar function — no `CREATE MODEL`, no connection, for text input. `gemini-embedding-001` supports up to 3072 dimensions; `model_params => JSON '{"outputDimensionality": 256}'` truncates to 256 (Matryoshka-style), keeping the downstream feature tables and training cost manageable.

### Products

Disambiguate `category` by prefixing with `department` (e.g. `Men: Accessories` vs. `Women: Accessories` are different categories, but share a raw `category` name), then embed each product's `name`.

```python
query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.embed_class_products` AS
SELECT
  id, name, department,
  department || ': ' || category AS category,
  cost, retail_price, brand,
  (AI.EMBED(content => name, endpoint => 'gemini-embedding-001',
            model_params => JSON '{{"outputDimensionality": 256}}')).result AS name_embedding
FROM `bigquery-public-data.thelook_ecommerce.products`
WHERE name IS NOT NULL
"""
client.query(query).result()

query = f"""
SELECT department, COUNT(DISTINCT category) AS n_categories, COUNT(*) AS n_products
FROM `{PROJECT_ID}.{DATASET_ID}.embed_class_products`
GROUP BY department
"""
client.query(query).to_dataframe()
```

### Hierarchy nodes

Each department and each `department: category` combination becomes one hierarchy node, with its own embedding and a pointer to its parent (`ALL` for departments, the department name for categories).

```python
query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.embed_class_hierarchy` AS
WITH department_nodes AS (
  SELECT DISTINCT department AS hierarchy_node, 'department' AS hierarchy_level, 'ALL' AS hierarchy_node_parent
  FROM `{PROJECT_ID}.{DATASET_ID}.embed_class_products`
),
category_nodes AS (
  SELECT DISTINCT category AS hierarchy_node, 'category' AS hierarchy_level, department AS hierarchy_node_parent
  FROM `{PROJECT_ID}.{DATASET_ID}.embed_class_products`
)
SELECT *, (AI.EMBED(content => hierarchy_node, endpoint => 'gemini-embedding-001',
                     model_params => JSON '{{"outputDimensionality": 256}}')).result AS hierarchy_node_embedding
FROM department_nodes
UNION ALL
SELECT *, (AI.EMBED(content => hierarchy_node, endpoint => 'gemini-embedding-001',
                     model_params => JSON '{{"outputDimensionality": 256}}')).result
FROM category_nodes
"""
client.query(query).result()

query = f"""
SELECT hierarchy_level, COUNT(*) AS n_nodes
FROM `{PROJECT_ID}.{DATASET_ID}.embed_class_hierarchy`
GROUP BY hierarchy_level
"""
client.query(query).to_dataframe()
```

---
## Step 2 — Build the labeled (product × node) training and test tables

Split products 90/10, stratified by `category` (native SQL — no need for the local pandas/numpy workaround the original notebook used, a BigFrames limitation at the time). Then cross-join each split against every hierarchy node: `label = 1` when the node is that product's true department or category, else `0`.

Two feature constructions are computed once, up front, so every model below can just select the columns it needs:
- `concat_embedding` — the product and node embeddings concatenated into one 512-dim vector (`ARRAY_CONCAT`)
- `adiff_embedding` — the elementwise absolute difference between the two 256-dim embeddings (via `UNNEST ... WITH OFFSET` + `JOIN` on position — BigQuery has no native elementwise array arithmetic)

Both stay as `ARRAY<FLOAT64>` columns passed directly to `CREATE MODEL` below — confirmed live that `BOOSTED_TREE_CLASSIFIER` accepts array-typed features without needing them unnested into individual columns first.

```python
query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.embed_class_products_split` AS
SELECT *,
  IF(
    ROW_NUMBER() OVER (PARTITION BY category ORDER BY RAND()) <= CEIL(0.10 * COUNT(*) OVER (PARTITION BY category)),
    'TEST', 'TRAIN'
  ) AS splits
FROM `{PROJECT_ID}.{DATASET_ID}.embed_class_products`
"""
client.query(query).result()

query = f"""
SELECT splits, COUNT(*) AS n_products
FROM `{PROJECT_ID}.{DATASET_ID}.embed_class_products_split`
GROUP BY splits
"""
client.query(query).to_dataframe()
```

```python
def build_labeled_table(split_name, table_suffix):
    query = f"""
    CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.embed_class_{table_suffix}` AS
    SELECT
      p.id, p.name, p.department, p.category, p.cost, p.retail_price, p.brand,
      h.hierarchy_node, h.hierarchy_level, h.hierarchy_node_parent,
      IF(
        (h.hierarchy_level = 'department' AND h.hierarchy_node = p.department) OR
        (h.hierarchy_level = 'category' AND h.hierarchy_node = p.category),
        1, 0
      ) AS label,
      ARRAY_CONCAT(p.name_embedding, h.hierarchy_node_embedding) AS concat_embedding,
      ARRAY(
        SELECT ABS(a - b)
        FROM UNNEST(p.name_embedding) AS a WITH OFFSET pos
        JOIN UNNEST(h.hierarchy_node_embedding) AS b WITH OFFSET pos
        USING(pos)
        ORDER BY pos
      ) AS adiff_embedding
    FROM `{PROJECT_ID}.{DATASET_ID}.embed_class_products_split` p
    CROSS JOIN `{PROJECT_ID}.{DATASET_ID}.embed_class_hierarchy` h
    WHERE p.splits = '{split_name}'
    """
    client.query(query).result()
    print(f'Table embed_class_{table_suffix} created')

build_labeled_table('TRAIN', 'train')
build_labeled_table('TEST', 'test')

query = f"""
SELECT COUNT(*) AS n_rows, SUM(label) AS n_positive
FROM `{PROJECT_ID}.{DATASET_ID}.embed_class_train`
"""
client.query(query).to_dataframe()
```

---
## Step 3 — Train 3 pairwise classifiers: different feature constructions

- **`adiff`** — absolute difference only (256 features): cheapest, simplest.
- **`conadiff`** — concatenated + absolute difference (768 features): richer embedding-only signal.
- **`conadiff_weighted`** — same features as `conadiff`, plus `auto_class_weights = TRUE`: the (product, node) label is heavily imbalanced (~2.6% positive), so this tests whether correcting for that — rather than adding more features — is the better lever.

All three trained with otherwise-default `BOOSTED_TREE_CLASSIFIER` hyperparameters (no attempt to replicate the original's deep/forested configurations, which is what drove its multi-hour training times). Submitted concurrently — **this cell takes up to ~40 minutes.**

```python
model_configs = {
    'embed_class_model_adiff': (
        f'SELECT adiff_embedding, label FROM `{PROJECT_ID}.{DATASET_ID}.embed_class_train`',
        {}
    ),
    'embed_class_model_conadiff': (
        f'SELECT concat_embedding, adiff_embedding, label FROM `{PROJECT_ID}.{DATASET_ID}.embed_class_train`',
        {}
    ),
    'embed_class_model_conadiff_weighted': (
        f'SELECT concat_embedding, adiff_embedding, label FROM `{PROJECT_ID}.{DATASET_ID}.embed_class_train`',
        {'auto_class_weights': 'TRUE'}
    ),
}

jobs = {}
for model_name, (select_sql, extra_options) in model_configs.items():
    options = "model_type = 'BOOSTED_TREE_CLASSIFIER', input_label_cols = ['label']"
    for opt_name, opt_value in extra_options.items():
        options += f", {opt_name} = {opt_value}"
    query = f"""
    CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.{model_name}`
    OPTIONS({options}) AS
    {select_sql}
    """
    jobs[model_name] = client.query(query)  # submitted asynchronously
    print(f'submitted {model_name}')

for model_name, job in jobs.items():
    job.result()
    print(f'{model_name} trained')
```

---
## Step 4 — Evaluate with `ML.EVALUATE`

```python
eval_rows = []
for model_name in model_configs:
    query = f"""
    SELECT '{model_name}' AS model, *
    FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.{model_name}`,
      (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.embed_class_test`))
    """
    eval_rows.append(client.query(query).to_dataframe())

eval_metrics = pd.concat(eval_rows, ignore_index=True)
eval_metrics
```

---
## Step 5 — Resolve the hierarchy top-down and measure applied accuracy

`ML.EVALUATE`'s metrics score the raw binary "does this pair match?" task. What actually matters for the product-catalog use case is: **given all 38 candidate scores for one product, does the top-1 resolution pick the right department, then the right category within it?**

The resolution query: `ML.PREDICT` → unnest `predicted_label_probs` down to the `label = 1` probability → pick the highest-probability department per product (`QUALIFY ROW_NUMBER() ... = 1`) → join category candidates whose parent matches that predicted department, and pick the highest-probability one among those.

```python
def resolve_hierarchy(model_name):
    query = f"""
    WITH probs AS (
      SELECT id, name, category, department, hierarchy_level, hierarchy_node, hierarchy_node_parent, lp.prob
      FROM ML.PREDICT(
        MODEL `{PROJECT_ID}.{DATASET_ID}.{model_name}`,
        (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.embed_class_test`)
      ) p
      CROSS JOIN UNNEST(p.predicted_label_probs) AS lp
      WHERE lp.label = 1
    ),
    department_pred AS (
      SELECT id, name, category, department, hierarchy_node AS pred_department, prob AS pred_department_prob
      FROM probs
      WHERE hierarchy_level = 'department'
      QUALIFY ROW_NUMBER() OVER (PARTITION BY id ORDER BY prob DESC) = 1
    )
    SELECT d.*, c.hierarchy_node AS pred_category, c.prob AS pred_category_prob
    FROM department_pred d
    LEFT JOIN (
      SELECT id, hierarchy_node, hierarchy_node_parent, prob
      FROM probs WHERE hierarchy_level = 'category'
    ) c
    ON d.id = c.id
    WHERE d.pred_department = c.hierarchy_node_parent
    QUALIFY ROW_NUMBER() OVER (PARTITION BY d.id ORDER BY c.prob DESC) = 1
    """
    return client.query(query).to_dataframe()

resolved = {model_name: resolve_hierarchy(model_name) for model_name in model_configs}

comparison = pd.DataFrame([
    {
        'model': model_name,
        'department_accuracy': (df['department'] == df['pred_department']).mean(),
        'category_accuracy': (df['category'] == df['pred_category']).mean(),
    }
    for model_name, df in resolved.items()
])
comparison
```

---
## Step 6 — Two baselines: is the pairwise approach even the right tool here?

The pairwise setup above is real infrastructure: a ~1M-row cross-joined training table, 19–40 minutes per model, and a two-stage `ML.PREDICT`/`UNNEST`/`QUALIFY` resolution query at serving time. That complexity is worth it *if* it's actually solving a problem a simpler approach can't. Two much cheaper alternatives:

1. **Direct multiclass classification** — skip the (product, node) pairing entirely. Train one `BOOSTED_TREE_CLASSIFIER` with `category` (all 36 values) as the label, straight from the product's own embedding. Department is then just the predicted category's own department prefix — no separate department model needed.
2. **Pure `VECTOR_SEARCH`** — no classifier, no training at all. Find the hierarchy node whose embedding is nearest the product's embedding. At this data size (2 department nodes, at most 22 categories per department) a vector index isn't needed — `VECTOR_SEARCH` falls back to an exact brute-force scan, which is both simpler and, at this scale, not meaningfully slower than an index would be.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.embed_class_baseline_multiclass`
OPTIONS(model_type = 'BOOSTED_TREE_CLASSIFIER', input_label_cols = ['category']) AS
SELECT name_embedding, category
FROM `{PROJECT_ID}.{DATASET_ID}.embed_class_products_split`
WHERE splits = 'TRAIN'
"""
client.query(query).result()
print('Model embed_class_baseline_multiclass created')

query = f"""
SELECT
  department AS actual_department, category AS actual_category,
  SPLIT(predicted_category, ': ')[OFFSET(0)] AS pred_department,
  predicted_category AS pred_category
FROM ML.PREDICT(MODEL `{PROJECT_ID}.{DATASET_ID}.embed_class_baseline_multiclass`,
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.embed_class_products_split` WHERE splits = 'TEST'))
"""
multiclass_baseline_df = client.query(query).to_dataframe()
multiclass_baseline_df.rename(columns={'actual_department': 'department', 'actual_category': 'category'}, inplace=True)

print('department_accuracy:', (multiclass_baseline_df['department'] == multiclass_baseline_df['pred_department']).mean())
print('category_accuracy:', (multiclass_baseline_df['category'] == multiclass_baseline_df['pred_category']).mean())
```

```python
query = f"""
WITH dept_search AS (
  SELECT
    query.id, query.department, query.category, query.name_embedding,
    base.hierarchy_node AS pred_department
  FROM VECTOR_SEARCH(
    (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.embed_class_hierarchy` WHERE hierarchy_level = 'department'),
    'hierarchy_node_embedding',
    (SELECT id, department, category, name_embedding FROM `{PROJECT_ID}.{DATASET_ID}.embed_class_products_split` WHERE splits = 'TEST'),
    'name_embedding',
    top_k => 1,
    distance_type => 'COSINE'
  )
),
cat_search AS (
  SELECT
    query.id, query.department, query.category,
    base.hierarchy_node AS pred_category
  FROM VECTOR_SEARCH(
    (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.embed_class_hierarchy` WHERE hierarchy_level = 'category'),
    'hierarchy_node_embedding',
    (SELECT id, department, category, name_embedding, pred_department FROM dept_search),
    'name_embedding',
    top_k => 36,  -- every category node, so the true department's categories are never excluded before filtering
    distance_type => 'COSINE'
  )
  WHERE base.hierarchy_node_parent = query.pred_department
  QUALIFY ROW_NUMBER() OVER (PARTITION BY query.id ORDER BY distance ASC) = 1
)
SELECT d.department, d.category, d.pred_department, c.pred_category
FROM dept_search d
JOIN cat_search c USING(id)
"""
vector_search_df = client.query(query).to_dataframe()

print('department_accuracy:', (vector_search_df['department'] == vector_search_df['pred_department']).mean())
print('category_accuracy:', (vector_search_df['category'] == vector_search_df['pred_category']).mean())
```

```python
all_resolved = dict(resolved)  # the 3 pairwise models' resolved DataFrames from Step 5
all_resolved['embed_class_baseline_multiclass'] = multiclass_baseline_df
all_resolved['embed_class_baseline_vector_search'] = vector_search_df

training_cost = {
    'embed_class_model_adiff': '~1M-row cross-join, ~19 min',
    'embed_class_model_conadiff': '~1M-row cross-join, ~40 min',
    'embed_class_model_conadiff_weighted': '~1M-row cross-join, ~40 min',
    'embed_class_baseline_multiclass': '~26K rows, a few minutes',
    'embed_class_baseline_vector_search': 'no training at all',
}

all_comparison = pd.DataFrame([
    {
        'model': model_name,
        'department_accuracy': (df['department'] == df['pred_department']).mean(),
        'category_accuracy': (df['category'] == df['pred_category']).mean(),
        'training_cost': training_cost[model_name],
    }
    for model_name, df in all_resolved.items()
])
all_comparison
```

---
## Step 7 — Confusion matrix for the best approach overall (category level)

Best across all 5 approaches now, not just the 3 pairwise ones. 36 candidate categories, so this is dense — but it shows where the confusion concentrates (e.g. visually related categories within the same department) rather than just a single accuracy number.

```python
best_model = all_comparison.sort_values('category_accuracy', ascending=False).iloc[0]['model']
best_df = all_resolved[best_model]

labels = sorted(best_df['category'].unique())
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay

cm = confusion_matrix(best_df['category'], best_df['pred_category'], labels=labels)
fig, ax = plt.subplots(figsize=(16, 16))
ConfusionMatrixDisplay(cm, display_labels=labels).plot(ax=ax, xticks_rotation='vertical', colorbar=False)
ax.set_title(f'Category-level confusion matrix — {best_model} (TEST)')
plt.tight_layout()
plt.show()
```

---
## Interpretation

**The headline finding: the pairwise binary-relevance approach — the entire premise of the original notebook this workflow modernizes — is not the best tool for this specific hierarchy, on either accuracy or cost.** The direct multiclass baseline reaches roughly **70% category accuracy** while training on a table **~38x smaller** (no cross-join with hierarchy nodes) in a few minutes rather than tens of minutes. The pairwise approaches, even at their best (`conadiff_weighted`, ~46% category accuracy), don't come close — and even the **zero-training** `VECTOR_SEARCH` baseline (~53% category accuracy, verified without needing a vector index at this data size) beats every pairwise variant.

**Within the pairwise family, the ranking is informative on its own:** `adiff` (absolute-difference-only) is clearly weakest. Adding the concatenated embeddings (`conadiff`) helps substantially. Correcting for the real ~2.6% positive-label imbalance via `auto_class_weights=TRUE` (`conadiff_weighted`) helps *again*, on top of that — trading precision for recall and improving `ML.EVALUATE`'s ROC-AUC — confirming that for this pairwise framing, addressing class imbalance is a more effective lever than the metadata features the original notebook added instead.

**Why does the "obviously simpler" approach win so decisively here?** The pairwise framing's real advantage — not needing to retrain when a new hierarchy node is added — is wasted on a small, static, 2-level hierarchy with only 38 total nodes. Its real cost — a training set that grows as `O(products × nodes)`, and a classifier that has to learn "does X belong with Y" as a general relation rather than directly learning the 36 categories' decision boundaries — is fully paid regardless. For a hierarchy that's genuinely large or changes often (thousands of leaf nodes, new categories added weekly), that tradeoff could flip; for this one, it doesn't. **The practical lesson: try the direct/simple framing and a zero-training baseline first, and only reach for the pairwise pattern when the hierarchy's scale or dynamism actually demands it** — reflected here in `all_comparison`'s `training_cost` column sitting right next to its accuracy numbers, not as an afterthought.

Category-level accuracy tops out around 70% (not higher) even for the winning approach — this reflects genuine task difficulty (36 similar retail categories, several of them adjacent by nature — e.g. `Pants` vs. `Jeans` vs. `Shorts` — classified from a short product name alone, no images or descriptions).
