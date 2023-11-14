![ga4](https://www.google-analytics.com/collect?v=2&tid=G-6VDTYWLKX6&cid=1&en=page_view&sid=1&dl=statmike%2Fvertex-ai-mlops%2FFeature+Store&dt=readme.md)

# vertex-ai-mlops/Feature Store/readme.md

A core part of MLOps for going from model to MODELS is feature management.  [Vertex AI Feature Store](https://cloud.google.com/vertex-ai/docs/featurestore/latest/overview) is an excellent way manage features and short-cut the process of deploying models into production systems.

**Versions**

Vertex AI Feature Store (pre-2023) is now named [Vertex Ai Feature Store (Legacy)](https://cloud.google.com/vertex-ai/docs/featurestore#vaifs_legacy).  The new feature store is [Vertex AI Feature Store](https://cloud.google.com/vertex-ai/docs/featurestore).  This readme will now focus on the latest feature store but for information regarding the legacy feature store see:
- Notebook based workflow: [Feature Store (Legacy)](./Feature%20Store%20(Legacy).ipynb)
- [Documentation](https://cloud.google.com/vertex-ai/docs/featurestore/overview)
- [Comparison to Vertex AI Feature Store](https://cloud.google.com/vertex-ai/docs/featurestore#comparison_between_and)

## Vertex AI Feature Store

[Documentation](https://cloud.google.com/vertex-ai/docs/featurestore/latest/overview)

---
**tl;dr**

<p align="center" width="100%"><center>
    <img src="../architectures/architectures/images/feature store/readme/overview.png">
</center></p>

The main layout for Feature Store is serving environment for **features** observed on **entities**:
- **entity** = a unique record, think row
- **feature** = observations, input for ML, think column

The **offline store** is made up of any BigQuery Table(s)/View(s), the **data source**, that you manage:
- (1) If a table/view has a single row per unique **entity** with columns that are non-changing values for **features** then the table can be directly used in an **online store's** **feature view** (see below).
- (2) For time bound **features** the table/view needs to have two additional columns: entity_id, feature_timestamp

The **feature registry**:
- Tables/Views of type (2) above are registered as **Feature Groups** - a feature group is sourced by a single table/view
- Columns from the **feature group** are then registered as **features**

The **online store** is has two types to choose from:
- Cloud Bigtable online serving - highly scalable
- Optimized online serving - ultra-low latencies and responsive to burst of requests

**Feature Views** are created in the **online store** from:
- One or more **feature groups**
- a table/view of type (1)
 
BigQuery as a **data soruce**:
- This means that managing time bound **features** is done in BigQuery but before the **feature store**.  You can create multiple rows per **entity** in tables and use the entity_id and feature_timestamp columns to indicate the time based values. To make this shape of source data useful for training data batches there are two new functions in BigQuery to help extract point-in-time value for **entity/feature** data:
    - [ML.FEATURES_AT_TIME](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-feature-time) - will take a table and timestamp as input and return the value for each feature on each entity as of the timestamp.  There are additional optional configurations also.  
    - [ML.ENTITY_FEATURES_AT_TIME](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-entity-feature-time) - will take a table and an additional table of entity+timestamp pairs and return the feature values for each entity+timestamp pair.  This allows both multiple points in time for single entities as well as different times for different entities.
- Time bound data, or column values that change for a row/entity, might not be the native way data scientist are working with data.  There are great features in BigQuery to help with handling data that changes with time.
    - Creating these tables/views with timestamp entity records may be benefited by [time-travel](https://cloud.google.com/bigquery/docs/time-travel#time_travel) (up to 7 days - configurable) and [snapshots](https://cloud.google.com/bigquery/docs/table-snapshots-intro) (user controlled points in time). You can also [query time-travel](https://cloud.google.com/bigquery/docs/access-historical-data) as well as [create snapshots from time-travel](https://cloud.google.com/bigquery/docs/table-snapshots-create#create_a_table_snapshot_using_time_travel).
---