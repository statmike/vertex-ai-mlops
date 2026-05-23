![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Fdata%2Bai%2Fbq-solutions%2Fbq-continuous-queries&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/data%2Bai/bq-solutions/bq-continuous-queries/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-solutions/bq-continuous-queries/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-solutions/bq-continuous-queries/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-solutions/bq-continuous-queries/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-solutions/bq-continuous-queries/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Connect With Author On: </b> 
    <a href="https://www.linkedin.com/in/statmike"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a>
    <a href="https://www.github.com/statmike"><img src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub Logo" width="20px"></a> 
    <a href="https://www.youtube.com/@statmike-channel"><img src="https://upload.wikimedia.org/wikipedia/commons/f/fd/YouTube_full-color_icon_%282024%29.svg" alt="YouTube Logo" width="20px"></a>
    <a href="https://bsky.app/profile/statmike.bsky.social"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://x.com/statmike"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-solutions/bq-continuous-queries/readme.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-solutions/bq-continuous-queries/readme.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# BigQuery Continuous Queries with GA4 Data

[BigQuery Continuous Queries](https://cloud.google.com/bigquery/docs/continuous-queries-introduction) let you run SQL that processes data continuously as it arrives — no Dataflow, no Spark, just SQL. This project demonstrates that capability using [Google Analytics 4 (GA4)](https://developers.google.com/analytics) e-commerce event data streamed into BigQuery.

**The story:** GA4 properties can [export event data directly to BigQuery](https://support.google.com/analytics/answer/9358801) in near-real-time. Once that data lands, continuous queries can detect patterns as they happen — funnel drop-offs, traffic anomalies, conversion shifts — and write results to destination tables automatically.

**The demo:** Since the [public GA4 sample dataset](https://developers.google.com/analytics/bigquery/web-ecommerce-demo-dataset) is a static snapshot, we simulate GA4's streaming export by replaying real events into our own table using BigQuery [load jobs](https://cloud.google.com/bigquery/docs/loading-data). Four continuous queries run against this table — two produce results instantly (row-by-row), two produce results when 1-minute windows close (windowed). A live dashboard shows both patterns updating in real time, including traffic anomaly detection with injected bursts. The notebook also documents how to connect a real GA4 property for production use.

## Environment Setup

From this directory (`bq-continuous-queries/`):

**uv** (recommended)
```bash
uv sync
uv run python -m ipykernel install --user --name bq-continuous-queries --display-name "BQ Continuous Queries"
```

**pip**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m ipykernel install --user --name bq-continuous-queries --display-name "BQ Continuous Queries"
```

Then select the **BQ Continuous Queries** kernel in your notebook.

## Key Concepts

- **[GA4 BigQuery Export](https://support.google.com/analytics/answer/9358801)** — GA4 can export raw event data to BigQuery in two modes: daily batch export and streaming (intraday) export. Streaming export creates `events_intraday_YYYYMMDD` tables with near-real-time data. This is the foundation for real-time analytics.

- **[Continuous Queries](https://cloud.google.com/bigquery/docs/continuous-queries-introduction)** — A BigQuery feature that runs a SQL query continuously against new data as it arrives. Unlike scheduled queries (which run at intervals), continuous queries process each row once and emit results immediately. Results can be written to a [BigQuery table](https://cloud.google.com/bigquery/docs/continuous-queries-introduction), exported to [Pub/Sub](https://cloud.google.com/pubsub/docs/overview), or sent to [Bigtable](https://cloud.google.com/bigtable/docs/overview) or [Spanner](https://cloud.google.com/spanner/docs/overview).

- **[Load Jobs](https://cloud.google.com/bigquery/docs/loading-data)** — BigQuery's batch loading mechanism that writes directly to managed storage. We use `load_table_from_json()` to simulate GA4's streaming export — load jobs make data immediately visible to continuous queries with no propagation delay. Continuous queries can process data from [any write method](https://cloud.google.com/bigquery/docs/continuous-queries-introduction) — Storage Write API, `tabledata.insertAll`, load jobs, DML, Pub/Sub subscriptions, Dataflow, and Datastream.

- **[GA4 Event Schema](https://support.google.com/analytics/answer/7029846)** — GA4 records all user interactions as events. Each event has a name (e.g., `page_view`, `purchase`), a timestamp, a user identifier, traffic source information, and a nested `event_params` array of key-value pairs. Understanding this schema is essential for writing analytics queries.

- **[Enterprise Reservations](https://cloud.google.com/bigquery/docs/reservations-intro)** — Continuous queries require BigQuery Enterprise edition, enabled through reservations — pools of compute capacity (slots) allocated to your project. A CONTINUOUS assignment type is needed (separate from QUERY). Slots are billed per-second while the reservation exists.

## Notebook

A single notebook covers the full end-to-end flow:

**[BigQuery Continuous Queries](./bq-ga4-continuous-queries.ipynb)** — explores the GA4 schema, creates the demo infrastructure (dataset, tables, Enterprise reservation), creates four continuous queries (2 row-by-row + 2 windowed), runs a live dashboard that streams events and visualizes CQ output in real time, and cleans up all resources.

| Section | Topic |
|---------|-------|
| 1. Explore GA4 Data | Schema, event types, unnesting event parameters, traffic sources |
| 2. E-Commerce Funnel | Funnel analysis: page_view → purchase conversion |
| 3. Real GA4 Setup | How to connect a real GA4 property (documentation + links) |
| 4. Create Demo Dataset | BigQuery dataset, streaming table, 4 destination tables |
| 5. Enterprise Reservation | Slots, assignments, CONTINUOUS job type |
| 6. Stream Events | Read GA4 events, start background load jobs with anomaly bursts |
| 7. Continuous Queries | 4 CQs: row-by-row (`APPENDS`) + windowed (`TUMBLE`) patterns |
| 8. Live Dashboard | Monitor CQ output with live-updating multi-panel charts |
| 9. Extended Streaming | Run 2 — warm CQs process data immediately, no initialization delay |
| 10. Cleanup | Cancel queries, delete reservation, delete dataset |

## Prerequisites

- A GCP project with billing enabled
- APIs enabled: BigQuery, BigQuery Storage, BigQuery Reservation (notebook handles enablement)
- Python >= 3.13
- `gcloud` CLI authenticated (`gcloud auth application-default login`)

## Documentation

| Topic | Link |
|-------|------|
| GA4 BigQuery Export | [Setup guide](https://support.google.com/analytics/answer/9358801) |
| GA4 Event Schema | [Reference](https://support.google.com/analytics/answer/7029846) |
| GA4 Public Dataset | [Demo dataset](https://developers.google.com/analytics/bigquery/web-ecommerce-demo-dataset) |
| BigQuery Continuous Queries | [Introduction](https://cloud.google.com/bigquery/docs/continuous-queries-introduction) |
| CREATE CONTINUOUS QUERY | [DDL reference](https://cloud.google.com/bigquery/docs/reference/standard-sql/data-definition-language#create_continuous_query) |
| BigQuery Load Jobs | [Guide](https://cloud.google.com/bigquery/docs/loading-data) |
| BigQuery Reservations | [Overview](https://cloud.google.com/bigquery/docs/reservations-intro) |
| BigQuery Editions | [Comparison](https://cloud.google.com/bigquery/docs/editions-intro) |
| APPENDS() function | [Reference](https://cloud.google.com/bigquery/docs/reference/standard-sql/table-functions#appends) |
| TUMBLE() function | [Reference](https://cloud.google.com/bigquery/docs/reference/standard-sql/time-series-functions#tumble) |
| Pub/Sub | [Overview](https://cloud.google.com/pubsub/docs/overview) |
| Bigtable | [Overview](https://cloud.google.com/bigtable/docs/overview) |
| Spanner | [Overview](https://cloud.google.com/spanner/docs/overview) |
