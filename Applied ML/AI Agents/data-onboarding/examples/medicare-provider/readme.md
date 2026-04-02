![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FApplied+ML%2FAI+Agents%2Fdata-onboarding%2Fexamples%2Fmedicare-provider&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20ML/AI%20Agents/data-onboarding/examples/medicare-provider/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/data-onboarding/examples/medicare-provider/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/data-onboarding/examples/medicare-provider/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/data-onboarding/examples/medicare-provider/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/data-onboarding/examples/medicare-provider/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/Applied%20ML/AI%20Agents/data-onboarding/examples/medicare-provider/readme.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/Applied%20ML/AI%20Agents/data-onboarding/examples/medicare-provider/readme.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# Medicare Provider Data — Example Data Source

Source: [https://www.cms.gov/medicare/payment/prospective-payment-systems/provider-specific-data-public-use-sas-format](https://www.cms.gov/medicare/payment/prospective-payment-systems/provider-specific-data-public-use-sas-format)

CMS publishes Provider Specific Files (PSF) containing payment rates, cost report data, and facility characteristics for Medicare-certified providers. The source page offers both SAS and Parquet formats — the onboarding agent discovers both, skips the unsupported SAS files, and onboards the **Parquet** files into BigQuery.

The data covers multiple provider types across quarterly releases:

| Abbreviation | Provider Type |
|-------------|--------------|
| **FULL** | All provider types combined |
| **HHA** | Home Health Agencies |
| **HHA_LRO** | Home Health Agencies — Low Utilization Rate Override |
| **HOSPICE** | Hospice providers |
| **IRF** | Inpatient Rehabilitation Facilities |
| **LTCH** | Long-Term Care Hospitals |
| **PSYCH** | Psychiatric facilities |
| **SNF** | Skilled Nursing Facilities |

---

## What This Example Demonstrates

This example shows the full cycle with a second data source — including how to use `CHAT_SCOPE` to focus the chat agent on the right tables when multiple sources are onboarded:

1. **Onboard** — Run `agent_orchestrator` locally to crawl the CMS page, download parquet files, and create BigQuery tables
2. **Scope** — Set `CHAT_SCOPE` to point the chat agent at the CMS dataset
3. **Evaluate** — Run all 30 questions locally and collect results with timing

### Why `CHAT_SCOPE`?

When multiple sources are onboarded (e.g., both Cboe and CMS), the chat agent's reranker sees all ~112 tables in a flat list. Generic terms like "providers" or "states" appear in both financial and healthcare datasets, causing the reranker to pick the wrong source's tables. `CHAT_SCOPE` restricts the chat agent — the reranker, context cache, and catalog search — to tables from a single source, eliminating cross-source confusion.

---

## Step 1: Onboard the Data

From the data-onboarding project root, run the orchestrator locally:

```bash
uv run adk web
```

Select **`agent_orchestrator`** from the dropdown and send:

```
Onboard data from: https://www.cms.gov/medicare/payment/prospective-payment-systems/provider-specific-data-public-use-sas-format
```

The agent will:
- Crawl the CMS page and follow links (332 pages, depth 1)
- Discover ~200 downloadable files (SAS + Parquet + PDFs)
- Download and stage to GCS (parquet files extracted from ZIP archives)
- Skip unsupported formats (`.sas7bdat`, `.sas`)
- Read parquet schemas, cross-reference with CMS documentation
- Design and create BigQuery tables with enriched column descriptions
- Validate the loaded data

**Result:** 54 BigQuery tables created in `data_onboarding_cms_gov_bronze` — 15 IPSF tables (one per provider type), 3 OPSF tables, plus ICD-10 coding tables, ambulance data, and more. The CMS crawl at depth 1 discovers far more than just the provider-specific files. Key IPSF tables:

| Table | Rows | Description |
|-------|------|-------------|
| `ipsf_full` | 4,895,679 | All provider types combined |
| `ipsf_inp` | 1,966,882 | Inpatient hospitals |
| `ipsf_snf` | 1,681,117 | Skilled Nursing Facilities |
| `ipsf_hha` | 1,077,752 | Home Health Agencies |
| `ipsf_ipf` | 480,220 | Inpatient Psychiatric Facilities |
| `ipsf_irf` | 448,365 | Inpatient Rehabilitation Facilities |
| `ipsf_hos` | 240,051 | Hospice |
| `ipsf_ltch` | 136,774 | Long-Term Care Hospitals |

Total pipeline time: ~2.5 hours (crawling 332 pages, downloading 384 files, analyzing 127 data files against 607 context documents).

---

## Step 2: Set Chat Scope

Point the chat agent at the CMS Medicare data by setting `CHAT_SCOPE`. You can either update `.env` or override it at runtime:

```bash
# Option A: override at runtime (doesn't change .env)
CHAT_SCOPE=data_onboarding_cms_gov_bronze uv run adk web

# Option B: set in .env permanently
# CHAT_SCOPE=data_onboarding_cms_gov_bronze
```

This scopes the reranker, context cache, and catalog search to CMS tables only. Without this, the chat agent would see both Cboe and CMS tables and frequently pick the wrong source.

Select **`agent_chat`** from the dropdown and ask questions, or run all 30 programmatically — see [Step 3](#step-3-run-all-questions).

> **Switching sources:** Use a different `CHAT_SCOPE` value — e.g., `data_onboarding_datashop_cboe_com_bronze` for Cboe.

> **Deploying to Agent Engine:** Set `CHAT_SCOPE` in `.env` before deploying — it's passed as an environment variable to the deployed instance. To switch sources on a deployed agent, update `.env` and run `uv run python deploy/deploy.py chat --update`. See [deploy/readme.md](../../deploy/readme.md) for details.

### Example Questions

| Persona | Question | What it tests |
|---------|----------|--------------|
| **Data Analyst** | "How many unique providers are in the most recent full IPSF dataset?" | Basic aggregation over provider data |
| **Data Analyst** | "Compare the number of providers across HHA, Hospice, IRF, LTCH, SNF, Psych" | Cross-table comparison |
| **Data Analyst** | "What are the top 10 states by number of providers?" | Geographic analysis |
| **Data Engineer** | "What files were downloaded from CMS?" | Provenance — acquisition metadata |
| **Data Engineer** | "How many tables were created and what are their row counts?" | Pipeline results |
| **Catalog Explorer** | "What does PRVDR_NUM mean?" | Semantic search over column descriptions |
| **Catalog Explorer** | "How are the different IPSF tables related to each other?" | Cross-table relationships |

See [medicare_questions.json](medicare_questions.json) for all 30 questions (10 per persona).

---

## Step 3: Run All Questions

Run all 30 questions locally and collect results. Override `CHAT_SCOPE` at runtime without changing `.env`:

```bash
# From the data-onboarding project root:

# Run all 30 questions (sequential, 5s delay between)
CHAT_SCOPE=data_onboarding_cms_gov_bronze \
  uv run python examples/medicare-provider/run_medicare_questions.py

# Run one persona at a time
CHAT_SCOPE=data_onboarding_cms_gov_bronze \
  uv run python examples/medicare-provider/run_medicare_questions.py --persona "Data Analyst"
CHAT_SCOPE=data_onboarding_cms_gov_bronze \
  uv run python examples/medicare-provider/run_medicare_questions.py --persona "Data Engineer"
CHAT_SCOPE=data_onboarding_cms_gov_bronze \
  uv run python examples/medicare-provider/run_medicare_questions.py --persona "Catalog Explorer"

# Run a single question
CHAT_SCOPE=data_onboarding_cms_gov_bronze \
  uv run python examples/medicare-provider/run_medicare_questions.py --id data-analyst-q3

# Resume (skip already-completed questions)
CHAT_SCOPE=data_onboarding_cms_gov_bronze \
  uv run python examples/medicare-provider/run_medicare_questions.py --resume

# Adjust delay between questions (default: 5s)
CHAT_SCOPE=data_onboarding_cms_gov_bronze \
  uv run python examples/medicare-provider/run_medicare_questions.py --delay 10
```

> **Tip:** The `CHAT_SCOPE` env var prefix overrides the `.env` file value at runtime, so your `.env` can stay pointed at Cboe (or whatever your default source is).

Results are saved incrementally to `results/medicare_results.json`.

### Build the Results Section

After running, generate the Results section of this document:

```bash
# Preview results markdown to stdout
uv run python examples/medicare-provider/build_medicare_results.py

# Write results into this file (replaces everything after "## Results")
uv run python examples/medicare-provider/build_medicare_results.py --write
```

---

## Key Differences from the CBOE Example

| Aspect | CBOE Example | Medicare Example |
|--------|-------------|-----------------|
| **Question runner** | Local `InMemoryRunner` | Local `InMemoryRunner` |
| **Key concept** | Basic end-to-end walkthrough | **`CHAT_SCOPE`** for multi-source disambiguation |
| **Data format** | CSV, Excel, ZIP | Parquet (from ZIP archives) |
| **Unsupported files** | None | SAS format files (skipped) |
| **Data domain** | Financial markets (options, volatility, FX) | Healthcare (Medicare provider payment data) |
| **Source** | Cboe DataShop (datashop.cboe.com) | CMS.gov (government open data) |
| **Tables created** | 58 | 54 |
| **Onboarding time** | ~15 min | ~2.5 hours |
| **Pages crawled** | ~20 | 332 |

---

## File Structure

```
examples/medicare-provider/
  readme.md                        # This file
  medicare_questions.json           # 30 questions (10 per persona)
  run_medicare_questions.py         # Runs questions locally via InMemoryRunner
  build_medicare_results.py         # Generates Results markdown from JSON
  results/
    medicare_results.json           # Collected answers + timing (after running)
```

---

## Results

### Data Analyst

<a id="data-analyst-q1"></a>
#### Q1: How many unique providers are in the most recent full IPSF dataset?

**Flow:** `agent_chat` → `agent_context` (callback: rerank) → `agent_convo` (conversational_chat)

| Step | Agent | Action | Time |
|------|-------|--------|------|
| 1 | agent_chat | `transfer_to_agent` | 2.3s |
| 2 | agent_context | `transfer_to_agent` | 60.3s |
| 3 | agent_convo | `conversational_chat` | 62.5s |
| | | **Total** | **81.3s** |

**Answer:**

In the most recent IPSF (Inpatient Prospective Payment System) dataset, there are a total of **69,745** unique Medicare providers. This count is based on the latest available data export dated January 2, 2026.

Here is the data retrieved:

| unique_provider_count | export_date |
|-----------------------|-------------|
| 69745.0               | 2026-01-02  |

The dataset provides a snapshot of a wide range of providers across the United States. With nearly 70,000 unique providers identified by their CMS Certification Number (CCN), this indicates a comprehensive coverage of the Medicare provider landscape for inpatient services at the time of the export.

Would you like to know:
*   What is the breakdown of these providers by provider\_type\_code?
*   Which state has the highest number of unique providers in this dataset?
*   How many providers have a waiver\_indicator set to 'Y'?
*   What is the average bed\_size for hospitals in this dataset?

<a id="data-analyst-q10"></a>
#### Q10: What are the largest SNF providers by bed size?

**Flow:** `agent_chat` → `agent_context` (callback: rerank) → `agent_convo` (conversational_chat)

| Step | Agent | Action | Time |
|------|-------|--------|------|
| 1 | agent_chat | `transfer_to_agent` | 2.4s |
| 2 | agent_context | `transfer_to_agent` | 79.9s |
| 3 | agent_convo | `conversational_chat` | 82.3s |
| | | **Total** | **126.1s** |

**Answer:**

### Summary
I have identified the largest Skilled Nursing Facility (SNF) providers by bed size based on the data in the `ipsf_snf` table. This table contains provider-specific records used for Medicare payment calculations.

The analysis shows the top 10 providers ranked by their maximum reported bed size. Please note that one provider (CCN 345516) shows a significantly higher bed count (over 93,000) than the others, which is likely a data entry error in the source system, as SNFs typically have hundreds, not tens of thousands, of beds.

## Data retrieved

| provider_ccn | max_bed_size |
|:-------------|:-------------|
| 345516       | 93002.0      |
| 0951V3       | 1979.0       |
| 105559       | 1414.0       |
| 5152V1       | 1148.0       |
| 555095       | 1021.0       |
| 335023       | 889.0        |
| 395780B      | 874.0        |
| 335462       | 816.0        |
| 555727       | 782.0        |
| 335063       | 775.0        |

### Insights
*   **Outlier Detection:** The facility with CCN **345516** reports a bed size of 93,002. This value is several orders of magnitude higher than other large facilities, which cluster around 800–2,000 beds. This is likely an error and should be treated with caution during further analysis.
*   **Scale of Large Providers:** Excluding the outlier, the largest SNF providers generally have between **800 and 2,000 beds**.
*   **Identification:** The facilities are identified by their **CMS Certification Number (CCN)**, which is the primary identifier for Medicare providers.

What is the average bed size for SNF providers by state?
List the SNF providers with the highest Medicaid ratios.
Can we see the bed size distribution for all SNFs (excluding the large outlier)?
Which SNF providers have been terminated from the Medicare program?


<a id="data-analyst-q2"></a>
#### Q2: What are the top 10 states by number of providers in the full IPSF data?

**Flow:** `agent_chat` → `agent_context` (callback: rerank) → `agent_convo` (conversational_chat)

| Step | Agent | Action | Time |
|------|-------|--------|------|
| 1 | agent_chat | `transfer_to_agent` | 2.4s |
| 2 | agent_context | `transfer_to_agent` | 55.8s |
| 3 | agent_convo | `conversational_chat` | 58.4s |
| | | **Total** | **104.9s** |

**Answer:**

### Summary
Based on the full IPPS PSF data, the state with the highest number of Medicare providers is state code **45** with **8,753** providers, followed by state code **05** with **8,036**. The following table and chart show the top 10 states by provider count.

## Data retrieved

state_code  provider_count
        45          8753.0
        05          8036.0
        10          4157.0
        36          3461.0
        14          2846.0
        39          2802.0
        23          2220.0
        33          1984.0
        15          1776.0
        26          1749.0

### Insights
- **Significant Concentration**: The top two states (45 and 05) account for a significantly higher number of providers compared to the rest of the top 10 list.
- **Top 10 Rankings**: The counts for the states ranked 3rd through 10th range from 4,157 down to 1,749 providers.
- **Provider Distribution**: This data helps in identifying where Medicare providers are most concentrated geographically.

What is the distribution of provider types in the top state (code 45)?
Which states have the highest average case-mix index among providers?
Compare the average bed size of providers in the top 5 states.
Identify the top 10 Metropolitan Statistical Areas (MSAs) with the most providers.


<a id="data-analyst-q3"></a>
#### Q3: Compare the number of providers across the different provider types (HHA, Hospice, IRF, LTCH, SNF, Psych).

**Flow:** `agent_chat` → `agent_context` (callback: rerank) → `agent_convo` (conversational_chat)

| Step | Agent | Action | Time |
|------|-------|--------|------|
| 1 | agent_chat | `transfer_to_agent` | 2.3s |
| 2 | agent_context | `transfer_to_agent` | 82.7s |
| 3 | agent_convo | `conversational_chat` | 85.7s |
| | | **Total** | **119.3s** |

**Answer:**

### Summary
This analysis compares the number of unique providers across different provider types: Home Health Agencies (HHA), Skilled Nursing Facilities (SNF), Hospice, Inpatient Rehabilitation Facilities (IRF), Inpatient Psychiatric Facilities (Psych), and Long-Term Care Hospitals (LTCH).

## Data retrieved

| provider_type | provider_count |
|---------------|----------------|
| HHA           | 22389.0        |
| SNF           | 22256.0        |
| Hospice       | 7881.0         |
| IRF           | 4613.0         |
| Psych         | 3034.0         |
| LTCH          | 872.0          |

The data reveals a clear hierarchy in the number of providers across these categories. Home Health Agencies (HHA) and Skilled Nursing Facilities (SNF) are the most prevalent, with 22,389 and 22,256 providers respectively. Together, they represent a significant majority of the provider population in this dataset. Hospice providers follow with 7,881, while Inpatient Rehabilitation Facilities (IRF) and Inpatient Psychiatric Facilities (Psych) have smaller but still substantial counts. Long-Term Care Hospitals (LTCH) represent the smallest category with 872 providers.

### Insights
- **HHA and SNF Dominance:** The number of HHA and SNF providers is nearly identical and significantly higher than all other provider types, suggesting a large-scale infrastructure for home health and skilled nursing care.
- **Concentration of Care:** The top two categories (HHA and SNF) account for approximately 73% of the total provider count across these six types.
- **Specialized Facilities:** Types like LTCH and IRF are much more specialized and fewer in number, which is typical for facilities providing highly specific intensive care.

What is the average bed size for SNF and IRF providers?
Which states have the highest number of HHA providers?
Compare the Medicaid ratio across these provider types.
How many providers are currently active versus terminated in each category?


<a id="data-analyst-q4"></a>
#### Q4: What is the average case mix index across all providers in the full IPSF?

**Flow:** `agent_chat` → `agent_context` (callback: rerank) → `agent_convo` (conversational_chat)

| Step | Agent | Action | Time |
|------|-------|--------|------|
| 1 | agent_chat | `transfer_to_agent` | 2.6s |
| 2 | agent_context | `transfer_to_agent` | 64.2s |
| 3 | agent_convo | `conversational_chat` | 66.7s |
| | | **Total** | **81.2s** |

**Answer:**

The average Case Mix Index (CMI) across all providers in the full Inpatient Provider Specific File (IPSF) is approximately **1.026**.

The Case Mix Index is a relative value assigned to a diagnosis-related group of patients in a medical care environment and is used in determining the allocation of resources to care for and/or treat the patients in the group. An average CMI of 1.026 suggests that, on average, the complexity and resource intensity of the patients treated by these providers are slightly above the national average (which is typically set at a baseline of 1.0).

What is the average case mix index by state?
Which provider types have the highest average case mix index?
Is there a correlation between bed size and case mix index?
Forecast the average case mix index for the next fiscal year.


<a id="data-analyst-q5"></a>
#### Q5: Which providers have the highest number of beds?

**Flow:** `agent_chat` → `agent_context` (callback: rerank) → `agent_convo` (conversational_chat)

| Step | Agent | Action | Time |
|------|-------|--------|------|
| 1 | agent_chat | `transfer_to_agent` | 2.3s |
| 2 | agent_context | `transfer_to_agent` | 75.3s |
| 3 | agent_convo | `conversational_chat` | 77.7s |
| | | **Total** | **130.0s** |

**Answer:**

Based on the January 2025 Inpatient Prospective Payment System (IPPS) full data snapshot, I've identified the providers with the highest reported bed counts.

The data initially showed many facilities reporting exactly 99,999 beds. This value is commonly used as a placeholder or data-entry code in healthcare datasets. To provide a clearer picture of real-world capacity, I've filtered the list to show the top 10 unique providers with bed counts below this threshold.

## Data retrieved

| provider_ccn | npi | max_bed_size |
|:-------------|:----|:-------------|
| 345516       | 3290 \002\021 | 93002.0      |
| 345516       | 1891722187 | 93002.0      |
| 345516       |             | 93002.0      |
| 140172       | 1588771919 | 20344.0      |
| 393007       |             | 20000.0      |
| 050080       |             | 10599.0      |
| 170091       |             | 9999.0       |
| 26S021       |             | 4510.0       |
| 260180A      |             | 4460.0       |
| 220897       |             | 3410.0       |

### Insights
- **Data Code 99,999**: Numerous facilities (including CCNs 150910, 150909, and others) reported 99,999 beds, which likely indicates missing or non-reported data.
- **Largest Reported Facilities**: Among facilities with reported counts, Provider **345516** (NPI 1891722187) reports the highest capacity at 93,002 beds.
- **Significant Capacity Variances**: The top 10 facilities range from over 90,000 beds down to approximately 3,400 beds, highlighting extreme differences in reported scale between different types of healthcare facilities.

What is the average bed size for providers in each state?
Can we identify providers with a high case mix index compared to their bed size?
Forecast the total number of beds across all providers for the next year.
Detect anomalies in bed size reporting based on historical data.

<a id="data-analyst-q6"></a>
#### Q6: How has the total number of providers changed across quarterly releases?

**Flow:** `agent_chat` → `agent_context` (callback: rerank) → `agent_convo` (conversational_chat)

| Step | Agent | Action | Time |
|------|-------|--------|------|
| 1 | agent_chat | `transfer_to_agent` | 2.5s |
| 2 | agent_context | `transfer_to_agent` | 71.7s |
| 3 | agent_convo | `conversational_chat` | 74.0s |
| | | **Total** | **100.6s** |

**Answer:**

### Summary
The total number of healthcare providers, calculated by combining the Inpatient Prospective Payment System (IPPS) and Outpatient Prospective Payment System (OPPS) provider files, has fluctuated over the recent quarterly releases. The data reveals a significant decrease in early 2025, followed by a slight recovery toward the beginning of 2026.

## Data retrieved

release_quarter | provider_count
--- | ---
2025-01-01 | 84060.0
2025-04-01 | 78032.0
2025-07-01 | 69246.0
2025-10-01 | 69514.0
2026-01-01 | 69745.0

### Insights
*   **Major Decline:** There was a sharp decrease in the total number of providers between the first and third quarters of 2025, dropping from 84,060 to 69,246.
*   **Stabilization and Growth:** After reaching a low in Q3 2025, the provider count has shown a gradual upward trend, reaching 69,745 by the first quarter of 2026.
*   **Release Gaps:** The data points correspond to snapshots from the quarterly release cycles, indicating the total active provider footprint at each point in time.

What is the breakdown of providers by state for the latest release?
Which provider types have seen the most significant changes in count over the last year?
Forecast the total provider count for the next four quarters.
Are there any anomalies in the provider count trends for specific census divisions?


<a id="data-analyst-q7"></a>
#### Q7: What is the distribution of fiscal year end dates across providers?

**Flow:** `agent_chat` → `agent_context` (callback: rerank) → `agent_convo` (conversational_chat)

| Step | Agent | Action | Time |
|------|-------|--------|------|
| 1 | agent_chat | `transfer_to_agent` | 2.3s |
| 2 | agent_context | `transfer_to_agent` | 81.9s |
| 3 | agent_convo | `conversational_chat` | 84.1s |
| | | **Total** | **166.8s** |

**Answer:**

### Summary
The fiscal year end dates across providers show a strong concentration on specific year-end cycles, particularly the calendar year end (December 31st). While the data spans over a century, the majority of the recorded provider activity occurs in the most recent three decades.

### Yearly Distribution
The yearly distribution of fiscal year end dates shows that the volume of records in the dataset increases significantly starting in the early 1980s, reflecting the comprehensive nature of the modern provider specific files.

### Fiscal Cycle Distribution
Analyzing the month and day of the fiscal year end reveals the most common reporting cycles. The majority of providers (nearly 47,404) align their fiscal year end with the calendar year end on **December 31st**. The federal government's fiscal year end on **September 30th** and the mid-year point of **June 30th** are also highly prevalent among providers.

## Data retrieved

| month_day | provider_count |
|:----------|---------------:|
| 12-31     |        47404.0 |
| 09-30     |        16242.0 |
| 06-30     |        13473.0 |
| 11-30     |         2594.0 |
| 11-29     |         2223.0 |
| 08-31     |         1939.0 |
| 03-31     |         1859.0 |
| 05-31     |         1754.0 |
| 04-30     |         1020.0 |
| 07-31     |          832.0 |
| 10-31     |          807.0 |
| 02-28     |          532.0 |
| 01-31     |          509.0 |
| 02-29     |          283.0 |
| 05-30     |          161.0 |
| 12-30     |          139.0 |
| 01-01     |          110.0 |
| 12-29     |           82.0 |
| 12-01     |           69.0 |
| 10-01     |           66.0 |

### Insights
*   **Dominant Cycles:** The most common fiscal year ends are December 31st, September 30th, and June 30th. These three dates account for the vast majority of all provider fiscal cycles.
*   **Data Density:** The dataset contains historical records dating back to 1900, but the density of records increases sharply after 1983, with the highest concentration of providers appearing between 2018 and 2021.
*   **Variability:** Beyond the primary cycles, there are many providers with non-standard fiscal year ends (e.g., November 30th or August 31st), reflecting various organizational or state-specific reporting requirements.

<a id="data-analyst-q8"></a>
#### Q8: Compare HHA providers across states — which states have the most home health agencies?

**Flow:** `agent_chat` → `agent_context` (callback: rerank) → `agent_convo` (conversational_chat)

| Step | Agent | Action | Time |
|------|-------|--------|------|
| 1 | agent_chat | `transfer_to_agent` | 2.1s |
| 2 | agent_context | `transfer_to_agent` | 59.2s |
| 3 | agent_convo | `conversational_chat` | 61.6s |
| | | **Total** | **92.2s** |

**Answer:**

### Summary
Based on the analysis of active Home Health Agencies (HHA), this report compares provider counts across different states (identified by their CMS state codes). The data highlights which states have the highest concentration of these agencies.

### Home Health Agency Distribution by State
The following table and chart show the count of unique, active HHA providers per state code, ranked from highest to lowest.

## Data retrieved

state_code hha_count
        05    3798.0
        45    2260.0
        10    1417.0
        36     976.0
        23     924.0
        39     745.0
        14     666.0
        49     429.0
        22     425.0
        24     404.0
        06     392.0
        26     320.0
        52     315.0
        33     291.0
        29     289.0
        37     272.0
        03     271.0
        16     261.0
        15     257.0
        17     253.0
        19     219.0
        34     186.0
        04     178.0
        46     163.0
        44     160.0
        01     132.0
        28     130.0
        07     119.0
        11     117.0
        18     104.0
        51      99.0
        32      97.0
        50      86.0
        42      82.0
        38      76.0
        13      75.0
        21      72.0
        31      69.0
        53      67.0
        40      67.0
        27      64.0
        43      61.0
        09      52.0
        25      47.0
        30      46.0
        35      45.0
        08      42.0
        20      37.0
        41      29.0
        12      28.0
        02      20.0
        47      13.0
        48       9.0
        55       5.0
        65       4.0
        66       3.0
        59       2.0
        75       2.0
      None       2.0

### Insights
- **Top States:** State code **05** has the highest number of home health agencies with **3,798** providers, significantly leading all other states. State code **45** follows with **2,260**, and state code **10** is third with **1,417**.
- **Concentration:** The top three states account for a substantial portion of the total HHA providers nationwide, suggesting a high concentration of services in these regions.
- **Active Status:** These counts reflect only currently active providers (those without a recorded termination date).

What is the average bed size for home health agencies across these states?
How many HHA providers were terminated in each state in the last 5 years?
Detect anomalies in the count of HHA providers per state to identify unusual concentrations.
Forecast the number of new home health agencies expected in state code 05 over the next 12 months.


<a id="data-analyst-q9"></a>
#### Q9: What are the wage index values for providers in California?

**Flow:** `agent_chat` → `agent_context` (callback: rerank) → `agent_convo` (conversational_chat)

| Step | Agent | Action | Time |
|------|-------|--------|------|
| 1 | agent_chat | `transfer_to_agent` | 2.2s |
| 2 | agent_context | `transfer_to_agent` | 66.9s |
| 3 | agent_convo | `conversational_chat` | 69.6s |
| | | **Total** | **124.3s** |

**Answer:**

### Summary
The following data provides the wage index values for Medicare providers located in California (State Code: 06). The list includes both inpatient and outpatient facilities, highlighting their special and supplemental wage indices, as well as geographic location codes for wage index calculations.

### Data Result
Showing a snapshot of 100 provider records in California, ordered by their most recent effective date.

## Data retrieved

provider_ccn state_code special_wage_index supplemental_wage_index msa_wage_index_location_code cbsa_wage_index_location effective_date facility_type
      060013         06               None                   1.0083                                                  None     2026-01-12     Inpatient
      060049         06               None                   1.0083                         0000                     None     2026-01-12     Inpatient
      064003         06               None                   0.9756                                                  None     2026-01-12     Inpatient
      060003         06               None                   1.0083                                                  None     2026-01-07     Inpatient
      060004         06               None                   1.0083                         0000                     None     2026-01-07     Inpatient
      060009         06               None                   1.0083                                                 14500     2026-01-07     Inpatient
      060054         06               None                   1.0083                                                  None     2026-01-07     Inpatient
      060064         06               None                   1.0083                         2080                     None     2026-01-07     Inpatient
      063030         06               None                   0.9782                         1720                     None     2026-01-06     Inpatient
      06T006         06               None                   1.0278                           06                     None     2026-01-02     Inpatient
      061642         06               None                      NaN                                                  None     2026-01-01     Inpatient
      062009         06               None                      NaN                                                  None     2026-01-01     Inpatient
      063030         06               None                   0.9782                         1720                     None     2026-01-01     Inpatient
      067002         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067004         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067015         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067026         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067044         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067051         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067054         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067056         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067063         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067080         06               None                      NaN                                                  None     2026-01-01     Inpatient
     067084A         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067098         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067112         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067115         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067117         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067129         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067133         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067136         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067147         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067161         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067169         06               None                      NaN                                                  None     2026-01-01     Inpatient
     067181A         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067191         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067192         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067193         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067195         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067196         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067198         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067201         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067204         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067208         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067215         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067219         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067224         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067253         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067254         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067272         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067274         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067275         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067277         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067280         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067295         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067325         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067337         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067338         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067339         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067402         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067407         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067408         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067413         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067415         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067416         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067417         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067418         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067420         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067421         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067437         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067441         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067443         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067445         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067449         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067450         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067451         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067452         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067453         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067456         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067457         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067460         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067462         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067463         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067464         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067466         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067468         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067469         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067470         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067471         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067474         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067475         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067476         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067477         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067478         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067479         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067481         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067486         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067487         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067489         06               None                      NaN                                                  None     2026-01-01     Inpatient
      067490         06               None                      NaN                                                  None     2026-01-01     Inpatient

### Insights
- **Wage Index Consistency:** Many providers in California share similar supplemental wage index values, such as **1.0083**, which often corresponds to specific metropolitan areas or standardized adjustments.
- **Geographic Reclassification:** Columns like `msa_wage_index_location_code` and `cbsa_wage_index_location` indicate if a provider's wage index is based on a Core-Based Statistical Area (CBSA) or Metropolitan Statistical Area (MSA) that differs from its actual geographic location.
- **Data Coverage:** The dataset includes various provider types, ranging from general hospitals (Inpatient) to specialized clinics (Outpatient), with records updated as recently as early 2026.

What is the average supplemental wage index for providers in California?
Which provider in California has the highest supplemental wage index?
Compare the wage indices between California and Texas providers.
Forecast the supplemental wage index for California providers for the next 24 months.


### Data Engineer

<a id="data-engineer-q1"></a>
#### Q1: Show me the processing log for this source.

**Flow:** `agent_chat` → `agent_engineer` (meta_chat)

| Step | Agent | Action | Time |
|------|-------|--------|------|
| 1 | agent_chat | `transfer_to_agent` | 2.3s |
| 2 | agent_engineer | `meta_chat` | 4.7s |
| | | **Total** | **39.8s** |

**Answer:**

I have retrieved the processing log for the most recently onboarded source, which is associated with the dataset **data_onboarding_cms_gov_bronze** (Source ID: `7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce`). The log details the sequence of actions taken across various phases of the onboarding pipeline, from initial acquisition to final validation.

## Data retrieved

                  dataset_name                               log_id                            source_id     phase                  action    status          started_at completed_at
data_onboarding_cms_gov_bronze f561fea7-f26d-4e56-b0c5-04c57edee2a7 7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce   acquire               crawl_url completed 2026-03-31 13:39:38         None
data_onboarding_cms_gov_bronze ce509ab1-41c1-4ac8-878a-fd8730aaa545 7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce   acquire          download_files completed 2026-03-31 13:57:57         None
data_onboarding_cms_gov_bronze cc2ec77f-a166-4ee0-bfb9-d9b7974543fa 7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce  discover          detect_changes completed 2026-03-31 13:58:16         None
data_onboarding_cms_gov_bronze bcfb7404-274d-40ed-9d2e-ab5fd28a5b27 7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce    design        record_decisions completed 2026-03-31 14:55:51         None
data_onboarding_cms_gov_bronze fd6eec30-8b91-45a7-8986-b3cb5946fcb8 7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce implement         column_recovery completed 2026-03-31 14:56:22         None
data_onboarding_cms_gov_bronze 65959eef-87b8-4ca9-bcd6-871145c18f39 7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce implement         column_recovery completed 2026-03-31 14:58:21         None
data_onboarding_cms_gov_bronze 2c84bf9b-fd15-467c-8ddd-adac0ce3cde8 7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce implement         column_recovery completed 2026-03-31 14:59:10         None
data_onboarding_cms_gov_bronze e312ab70-0cb8-418a-8b5f-ee9f9f080705 7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce implement         column_recovery completed 2026-03-31 14:59:50         None
data_onboarding_cms_gov_bronze a6750de2-180a-44eb-89d3-7b93720d591a 7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce implement         column_recovery completed 2026-03-31 14:59:59         None
data_onboarding_cms_gov_bronze 95e02457-99de-4305-b3d5-3aade96cbc33 7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce implement         column_recovery completed 2026-03-31 15:00:32         None
data_onboarding_cms_gov_bronze 3ab7da6c-93d4-432d-9728-b6a458d0687b 7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce implement         column_recovery completed 2026-03-31 15:02:24         None
data_onboarding_cms_gov_bronze bd712180-931e-4d9e-b4cb-3ca0ffa1b099 7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce implement  create_external_tables completed 2026-03-31 15:07:29         None
data_onboarding_cms_gov_bronze 829fed4c-ca5c-4ea3-9e9c-037a711a8938 7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce implement             execute_sql completed 2026-03-31 15:57:33         None
data_onboarding_cms_gov_bronze 74332917-348d-4086-a2d3-fa5709e1d552 7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce implement         publish_lineage completed 2026-03-31 15:58:09         None
data_onboarding_cms_gov_bronze c4d295a2-0a4f-46c5-80a5-b4d97272e013 7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce implement populate_context_chunks completed 2026-03-31 15:58:52         None
data_onboarding_cms_gov_bronze 6d8d512e-2f0a-4b96-95f1-702b13f5bece 7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce  validate        validate_lineage completed 2026-03-31 16:08:20         None

### Insights
*   **Pipeline Completion**: The onboarding process for this source successfully progressed through all major phases: **Acquire**, **Discover**, **Design**, **Implement**, and **Validate**.
*   **Activity Breakdown**: The most intensive phase was **Implement**, which involved multiple `column_recovery` actions, the creation of external tables, and the publishing of data lineage.
*   **Status**: All recorded actions are marked as `completed`, indicating a successful run of the pipeline for this specific source.
*   **Timeline**: The processing occurred on March 31, 2026, starting with the URL crawl at 1:39 PM and concluding with lineage validation at 4:08 PM.

What are the details of the schema decisions made for this source?
Can you show me the data lineage for the tables created in the cms_gov dataset?
How many files were downloaded during the acquire phase for this source?
Show me the processing logs for a different source, like the datashop_cboe_com domain.


<a id="data-engineer-q10"></a>
#### Q10: Which tables are partitioned and on what columns?

**Flow:** `agent_chat` → `agent_engineer` (meta_chat)

| Step | Agent | Action | Time |
|------|-------|--------|------|
| 1 | agent_chat | `transfer_to_agent` | 2.2s |
| 2 | agent_engineer | `meta_chat` | 4.6s |
| | | **Total** | **33.2s** |

**Answer:**

The following tables are partitioned by daily granularity:

*   **source_manifest**: Partitioned on the `discovered_at` column.
*   **processing_log**: Partitioned on the `started_at` column.
*   **table_lineage**: Partitioned on the `created_at` column.
*   **schema_decisions**: Partitioned on the `created_at` column.
*   **web_provenance**: Partitioned on the `crawled_at` column.

The **data_catalog** table is not partitioned, but it is clustered by `dataset_name`.

Partitioning by daily timestamps helps to optimize query performance and cost, especially for queries that filter by time ranges.

Would you like to know about the clustering columns for these tables, or perhaps look into the daily file discovery count?

<a id="data-engineer-q2"></a>
#### Q2: What files were downloaded from CMS?

**Flow:** `agent_chat` → `agent_engineer` (meta_chat)

| Step | Agent | Action | Time |
|------|-------|--------|------|
| 1 | agent_chat | `transfer_to_agent` | 2.4s |
| 2 | agent_engineer | `meta_chat` | 4.9s |
| | | **Total** | **283.3s** |

**Answer:**

A total of **1,257** files were downloaded from the CMS domain (`cms_gov`). These files include a variety of data archives, context documentation, and specific data formats such as Parquet, PDF, and Excel.

The following list shows a partial selection of the downloaded files (truncated to the first 1,000 results):

## Data retrieved

```
                                                                                                                                                                             file_path file_type  file_size_bytes classification  domain
                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/2016-2024-congressional-district-reports.zip       zip       10218874.0        unknown cms_gov
                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/2025-congressional-district-report-508.zip       zip        3615821.0        unknown cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/CMSAmbdata_Y2sample_post.zip       zip         156147.0        unknown cms_gov
                                                                   applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/CMSAmbdata_Y3sample_post_rev.zip       zip         156772.0        unknown cms_gov
                                                                   applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/CMSAmbdata_Y4sample_post_rev.zip       zip         156649.0        unknown cms_gov
                                   applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/ICD-10-CM-Conversion-Table-FY2025-Effective-10-01-2024-FINAL.zip       zip         152304.0        unknown cms_gov
                                                                             applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/POAexemptCodesFY25.zip       zip        1659705.0        unknown cms_gov
                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/Past Rate Announcements and Call Letters.zip       zip       10019439.0        unknown cms_gov
                                                   applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/Vehicles_MainTemplates_and_Instructions_v2_0.zip       zip          30406.0        unknown cms_gov
                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/Zip File 1 2025 Version Update Summary.zip       zip         106380.0        unknown cms_gov
                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/Zip File 3 2025 ICD-10-PCS Codes File.zip       zip         662579.0        unknown cms_gov
                            applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/Zip File 4 2025 ICD-10-PCS Order File (Long and Abbreviated Titles).zip       zip        1318110.0        unknown cms_gov
                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/Zip File 6 2025 ICD-PCS Conversion Table.zip       zip        1078256.0        unknown cms_gov
                                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/addendum.zip       zip         275967.0        unknown cms_gov
                                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/april-1-2026-addendum.zip       zip         294423.0        unknown cms_gov
                                                applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/april-1-2026-code-descriptions-in-tabular-order.zip       zip        2242530.0        unknown cms_gov
                                                     applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/april-1-2026-code-tables-tabular-and-index.zip       zip       22755010.0        unknown cms_gov
                                                                     applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/clm104c21_English_Exhibits.zip       zip        2854837.0        unknown cms_gov
                                                                     applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/clm104c21_Spanish_Exhibits.zip       zip        1569295.0        unknown cms_gov
                                                            applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/cmsambdata_y1sample_forposting20feb.zip       zip         135129.0        unknown cms_gov
                                                                              applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/code-descriptions.zip       zip        2194944.0        unknown cms_gov
                                                                  applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/cy2006-cy2025_landscape_files.zip       zip      190768604.0        unknown cms_gov
                                        applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/cy2026-medicare-advantage-and-part-d-contract-templates.zip       zip        3772167.0        unknown cms_gov
                                                                        applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/cy2026_landscape_202603.zip       zip       13529509.0        unknown cms_gov
                                                 applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/icd-10-cm-conversion-table-fy2026-april-1-2026.zip       zip         169772.0        unknown cms_gov
                                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/icd10OrderFiles2025_0.zip       zip        2317827.0        unknown cms_gov
                                                                      applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/icd10cm_drug_addenda_2026.zip       zip         894553.0        unknown cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/icd10cm_tabular_2025.zip       zip       22809189.0        unknown cms_gov
                                                                   applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/icd10cm_tabular_addenda_2025.zip       zip         743893.0        unknown cms_gov
                                                                                applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/icd10orderfiles.zip       zip        2204985.0        unknown cms_gov
                                                              applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/icd_10_cm_conversion_table_fy2026.zip       zip         167768.0        unknown cms_gov
                                              applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/past-medicare-part-d-retail-pharmacy-access-files.zip       zip        4674178.0        unknown cms_gov
                                                                             applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/poaexemptcodesfy26.zip       zip        1228270.0        unknown cms_gov
                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/psf-parquet-april-2025.zip       zip       23755139.0        unknown cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/psf-parquet-january-2025.zip       zip       32643200.0        unknown cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/psf-parquet-january-2026.zip       zip       28325532.0        unknown cms_gov
                                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/psf-parquet-july-2025.zip       zip       34632958.0        unknown cms_gov
                                                 applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/psf-parquet-october-2025-updated-december-2025.zip       zip       39863584.0        unknown cms_gov
                                                                             applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/psf-sas-april-2025.zip       zip       32901097.0        unknown cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/psf-sas-january-2025.zip       zip       51189229.0        unknown cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/psf-sas-january-2026.zip       zip       64169558.0        unknown cms_gov
                                                                              applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/psf-sas-july-2025.zip       zip       51965673.0        unknown cms_gov
                                                   applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/psf-sas-october-2025-updated-december-2025_1.zip       zip       64056701.0        unknown cms_gov
                                                                                applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/table-and-index.zip       zip       21881066.0        unknown cms_gov
                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/zip-file-1-2026-version-update-summary.zip       zip         211846.0        unknown cms_gov
                                                             applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/zip-file-1-pcs_update_summary_2026.zip       zip         105047.0        unknown cms_gov
                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/zip-file-2-2026-code-tables-and-index.zip       zip        7978738.0        unknown cms_gov
                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/zip-file-3-2026-icd-10-pcs-codes-file.zip       zip         663322.0        unknown cms_gov
                              applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/zip-file-4-2026-icd-10-pcs-order-file-long-and-abbreviated-titles.zip       zip        1319592.0        unknown cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/zip-file-5-2026-addendum.zip       zip         437254.0        unknown cms_gov
                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/archives/zip-file-6-2026-icd-pcs-conversion-table.zip       zip        1097410.0        unknown cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_000.md        md           1825.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_001.md        md           3045.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_002.md        md           1225.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_003.md        md            904.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_004.md        md            989.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_005.md        md          23038.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_006.md        md           2751.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_007.md        md           3802.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_008.md        md           5143.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_009.md        md           3593.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_100.md        md           1254.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_101.md        md           2370.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_102.md        md           6426.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_103.md        md           4361.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_104.md        md           4842.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_105.md        md           6915.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_106.md        md           5136.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_107.md        md          33885.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_108.md        md           3673.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_109.md        md           3660.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_110.md        md           5056.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_111.md        md           7438.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_112.md        md           3638.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_113.md        md           1888.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_114.md        md           2351.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_115.md        md           4399.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_116.md        md           6568.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_117.md        md           5009.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_118.md        md           2622.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_119.md        md           3910.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_120.md        md           2605.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_121.md        md           4469.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_122.md        md           2454.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_123.md        md           6132.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_124.md        md           1678.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_125.md        md           3781.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_126.md        md          25920.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_127.md        md           1671.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_128.md        md           1248.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_129.md        md           2829.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_130.md        md            573.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_131.md        md            757.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_132.md        md            943.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_133.md        md          17675.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_134.md        md           8324.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_135.md        md            777.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_136.md        md            940.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_137.md        md           9595.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_138.md        md           1363.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_139.md        md           2963.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_140.md        md           3055.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_141.md        md            797.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_142.md        md           1080.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_143.md        md           2768.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_144.md        md            972.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_145.md        md           4394.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_146.md        md           4771.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_147.md        md           1518.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_148.md        md            434.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_149.md        md           4458.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_150.md        md           3355.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_151.md        md           8195.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_152.md        md           8427.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_153.md        md           3723.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_154.md        md           5434.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_155.md        md           3563.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_156.md        md           1949.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_157.md        md            912.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_158.md        md           5237.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_159.md        md           2214.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_160.md        md           7386.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_161.md        md           4176.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_162.md        md           2931.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_163.md        md           2491.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_164.md        md           1102.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_165.md        md           3437.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_166.md        md           1825.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_167.md        md           1404.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_168.md        md            586.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_169.md        md           2202.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_170.md        md           3612.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_171.md        md           9429.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_172.md        md           1012.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_173.md        md           1229.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_174.md        md           3990.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_175.md        md           2794.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_176.md        md           1971.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_177.md        md           4249.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_178.md        md            891.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_179.md        md           5595.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_180.md        md           2454.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_181.md        md            589.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_182.md        md          12930.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_183.md        md            773.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_184.md        md          13821.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_185.md        md           3893.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_186.md        md            384.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_187.md        md           2048.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_188.md        md           1620.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_189.md        md           1258.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_190.md        md           3100.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_191.md        md            855.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_192.md        md           2665.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_193.md        md           4717.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_194.md        md           1112.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_195.md        md          11466.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_196.md        md          12462.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_197.md        md           1707.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_198.md        md           2506.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_199.md        md           3656.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_10.md        md           4287.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_11.md        md           3975.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_12.md        md          54249.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_13.md        md            965.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_14.md        md            968.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_15.md        md           1005.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_16.md        md           1021.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_17.md        md           1896.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_18.md        md          10749.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_19.md        md            872.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_200.md        md           3509.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_201.md        md           1203.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_202.md        md          53809.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_203.md        md           4641.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_204.md        md           4744.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_205.md        md           2969.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_206.md        md           6588.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_207.md        md           9311.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_208.md        md           6726.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_209.md        md            639.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_20.md        md            544.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_210.md        md            813.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_211.md        md            833.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_212.md        md           2535.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_213.md        md           3707.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_214.md        md            697.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_215.md        md           1086.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_216.md        md          17967.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_217.md        md         130099.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_218.md        md          12977.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_219.md        md           4222.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_21.md        md          17578.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_220.md        md           3143.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_221.md        md           4420.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_222.md        md           2364.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_223.md        md           1365.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_224.md        md           5661.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_225.md        md           2124.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_226.md        md           5678.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_227.md        md            999.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_228.md        md           4102.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_229.md        md            770.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_22.md        md           2485.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_230.md        md           1389.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_231.md        md           2458.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_232.md        md           2565.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_233.md        md           5495.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_234.md        md            697.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_235.md        md           1083.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_236.md        md           1803.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_237.md        md            777.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_238.md        md           1188.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_239.md        md            709.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_23.md        md           4013.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_240.md        md            551.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_241.md        md           3137.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_242.md        md           1392.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_243.md        md           1689.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_244.md        md            219.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_245.md        md            225.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_246.md        md           9089.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_247.md        md           2344.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_248.md        md           2638.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_249.md        md           2677.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_24.md        md           1681.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_250.md        md           5147.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_251.md        md           3895.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_252.md        md           6511.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_253.md        md           3440.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_254.md        md           2251.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_255.md        md            353.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_256.md        md           3491.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_257.md        md           4236.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_258.md        md           3251.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_259.md        md           5534.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_25.md        md           6034.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_260.md        md           1796.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_261.md        md           3152.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_262.md        md           1271.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_263.md        md            795.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_264.md        md          10114.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_265.md        md          11908.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_266.md        md            925.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_267.md        md           3162.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_268.md        md           1303.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_269.md        md           1791.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_26.md        md            161.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_270.md        md           3498.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_271.md        md           2238.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_272.md        md           1885.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_273.md        md           1979.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_274.md        md           2241.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_275.md        md           2000.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_276.md        md           2198.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_277.md        md           2372.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_278.md        md            731.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_279.md        md            290.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_27.md        md           3467.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_280.md        md            148.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_281.md        md           4758.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_282.md        md            652.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_283.md        md            954.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_284.md        md            267.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_285.md        md            324.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_286.md        md            460.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_287.md        md           1995.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_288.md        md            640.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_289.md        md           5817.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_28.md        md           1378.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_290.md        md            500.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_291.md        md            553.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_292.md        md           1681.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_293.md        md            737.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_294.md        md            345.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_295.md        md           2136.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_296.md        md           2072.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_297.md        md            604.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_298.md        md           7422.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_299.md        md           6190.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_29.md        md           1562.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_300.md        md           1229.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_301.md        md           2595.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_302.md        md           3982.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_303.md        md           1425.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_304.md        md          10833.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_305.md        md            938.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_306.md        md           7635.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_307.md        md           3207.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_308.md        md           7471.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_309.md        md           2197.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_30.md        md           1785.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_310.md        md           4988.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_311.md        md           4433.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_312.md        md           1891.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_313.md        md           6711.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_314.md        md           2729.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_315.md        md          19193.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_316.md        md           6052.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_317.md        md            914.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_318.md        md           4544.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_319.md        md           1207.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_31.md        md           1827.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_320.md        md           1680.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_321.md        md           1135.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_322.md        md           1466.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_323.md        md           4165.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_324.md        md          26453.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_325.md        md           8802.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_326.md        md           7794.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_327.md        md           4082.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_328.md        md           1253.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_329.md        md            845.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_32.md        md           3145.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_330.md        md          32747.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_331.md        md          32760.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_33.md        md           3610.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_34.md        md           4046.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_35.md        md           1936.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_36.md        md           1434.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_37.md        md           1293.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_38.md        md           2722.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_39.md        md          10487.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_40.md        md           4394.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_41.md        md           1458.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_42.md        md          14211.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_43.md        md           5231.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_44.md        md           7612.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_45.md        md          11598.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_46.md        md          10732.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_47.md        md            849.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_48.md        md            181.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_49.md        md           1185.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_50.md        md           3178.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_51.md        md           4943.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_52.md        md           9162.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_53.md        md           2101.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_54.md        md           4801.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_55.md        md           1710.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_56.md        md          15048.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_57.md        md           1757.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_58.md        md           1909.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_59.md        md           1937.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_60.md        md           1463.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_61.md        md           2412.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_62.md        md           3165.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_63.md        md           1343.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_64.md        md           2415.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_65.md        md           5743.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_66.md        md           3524.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_67.md        md           6435.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_68.md        md           1147.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_69.md        md           4520.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_70.md        md           4003.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_71.md        md           4671.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_72.md        md           2765.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_73.md        md           2206.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_74.md        md            855.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_75.md        md           5895.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_76.md        md           1138.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_77.md        md           1073.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_78.md        md           8899.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_79.md        md           2876.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_80.md        md           2459.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_81.md        md           1635.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_82.md        md            143.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_83.md        md           1708.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_84.md        md           4351.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_85.md        md           8668.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_86.md        md           1672.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_87.md        md           2585.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_88.md        md           5019.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_89.md        md           3291.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_90.md        md           2399.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_91.md        md           3111.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_92.md        md           2674.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_93.md        md           5432.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_94.md        md           1380.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_95.md        md            877.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_96.md        md          17352.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_97.md        md          10120.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_98.md        md           2165.0        context cms_gov
                                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/context/page_99.md        md           2313.0        context cms_gov
                                                                        applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/1.1_PartA_Inpatient_120907.pdf       pdf         382501.0        context cms_gov
                                                                        applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/1.1_PartA_Inpatient_120907.pdf       pdf         382501.0                cms_gov
                                                                                   applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/1.2_BofA_120907.pdf       pdf         362715.0        context cms_gov
                                                                                   applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/1.2_BofA_120907.pdf       pdf         362715.0                cms_gov
                                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/1.3_PartA_Hospice_120921.pdf       pdf         355943.0        context cms_gov
                                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/1.3_PartA_Hospice_120921.pdf       pdf         355943.0                cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/1.4_PartA_HomeHealth_120921.pdf       pdf         357355.0                cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/1.4_PartA_HomeHealth_120921.pdf       pdf         357355.0        context cms_gov
                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/1.6_PartB_Assigned_120907.pdf       pdf         369436.0        context cms_gov
                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/1.6_PartB_Assigned_120907.pdf       pdf         369436.0                cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/1.7_PartB_Unassigned_120907.pdf       pdf         334559.0        context cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/1.7_PartB_Unassigned_120907.pdf       pdf         334559.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/1.8_DME_Assigned_120907.pdf       pdf         340908.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/1.8_DME_Assigned_120907.pdf       pdf         340908.0        context cms_gov
                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/1.9_DME_Unassigned_120907.pdf       pdf         324319.0                cms_gov
                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/1.9_DME_Unassigned_120907.pdf       pdf         324319.0        context cms_gov
                                                               applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/11-20-25-complete-msn-message-list.xlsx      xlsx         134474.0                cms_gov
                                                               applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/11-20-25-complete-msn-message-list.xlsx      xlsx         134474.0           data cms_gov
                                                                                   applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/146514_bp102c15.pdf       pdf        1199911.0                cms_gov
                                                                                   applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/146514_bp102c15.pdf       pdf        1199911.0        context cms_gov
                                                                                     applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/182378_MM8921.pdf       pdf          76451.0                cms_gov
                                                                                     applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/182378_MM8921.pdf       pdf          76451.0        context cms_gov
                                                                    applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2.10_Breaking_LongNotes_120409.pdf       pdf         261272.0                cms_gov
                                                                    applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2.10_Breaking_LongNotes_120409.pdf       pdf         261272.0        context cms_gov
                                                                            applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2.11_Combined_A_121015.pdf       pdf         687221.0                cms_gov
                                                                            applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2.11_Combined_A_121015.pdf       pdf         687221.0        context cms_gov
                                                                        applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2.12_Combined_PartB_120907.pdf       pdf         336950.0        context cms_gov
                                                                        applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2.12_Combined_PartB_120907.pdf       pdf         336950.0                cms_gov
                                                                                   applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2.13_Pay_120907.pdf       pdf         329718.0                cms_gov
                                                                                   applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2.13_Pay_120907.pdf       pdf         329718.0        context cms_gov
                                                                             applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2.14_Envelopes_120409.pdf       pdf         179088.0                cms_gov
                                                                             applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2.14_Envelopes_120409.pdf       pdf         179088.0        context cms_gov
                                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2.15_Envelope_pay_120409.pdf       pdf         543502.0                cms_gov
                                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2.15_Envelope_pay_120409.pdf       pdf         543502.0        context cms_gov
                                                                              applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2.1_Duplicate_120907.pdf       pdf         247755.0                cms_gov
                                                                              applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2.1_Duplicate_120907.pdf       pdf         247755.0        context cms_gov
                                                                            applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2.26.26_telehealth_faq.pdf       pdf          50985.0                cms_gov
                                                                            applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2.26.26_telehealth_faq.pdf       pdf          50985.0        context cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2.2_Deductible_PartB_120907.pdf       pdf         278418.0                cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2.2_Deductible_PartB_120907.pdf       pdf         278418.0        context cms_gov
                                                                     applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2.3_Deductible_Benefit_120907.pdf       pdf         379643.0                cms_gov
                                                                     applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2.3_Deductible_Benefit_120907.pdf       pdf         379643.0        context cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2.4_ProviderList_120907.pdf       pdf         246306.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2.4_ProviderList_120907.pdf       pdf         246306.0        context cms_gov
                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2.5_ProviderHeader_120622.pdf       pdf         203655.0                cms_gov
                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2.5_ProviderHeader_120622.pdf       pdf         203655.0        context cms_gov
                                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2.6_Multipledates_120511.pdf       pdf         259441.0                cms_gov
                                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2.6_Multipledates_120511.pdf       pdf         259441.0        context cms_gov
                                                                             applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2.7_NoneRemain_120409.pdf       pdf         222084.0                cms_gov
                                                                             applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2.7_NoneRemain_120409.pdf       pdf         222084.0        context cms_gov
                                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2.8_AdjustedClaim_120925.pdf       pdf         219475.0        context cms_gov
                                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2.8_AdjustedClaim_120925.pdf       pdf         219475.0                cms_gov
                                                                        applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2.9_ContinuedClaims_120409.pdf       pdf         249591.0        context cms_gov
                                                                        applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2.9_ContinuedClaims_120409.pdf       pdf         249591.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2024.03 - SNF FINAL 508.pdf       pdf        1297877.0        context cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2024.03 - SNF FINAL 508.pdf       pdf        1297877.0                cms_gov
                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2025 Congressional District Report-508.html      html          82030.0        context cms_gov
                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2025 Congressional District Report-508.html      html          82030.0                cms_gov
                                                            applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2025 Congressional District Report-508.pdf       pdf        4453779.0        context cms_gov
                                                            applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2025 Congressional District Report-508.pdf       pdf        4453779.0                cms_gov
                                                               applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2025 Congressional District Report.xlsx      xlsx         126981.0           data cms_gov
                                                               applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2025 Congressional District Report.xlsx      xlsx         126981.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2026 1833 Cost Contract.pdf       pdf         170092.0        context cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2026 1833 Cost Contract.pdf       pdf         170092.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2026 1876 Cost Contract.pdf       pdf         225047.0        context cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2026 1876 Cost Contract.pdf       pdf         225047.0                cms_gov
                                                                applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2026 800 Series Only PFFS Contract.pdf       pdf         269906.0        context cms_gov
                                                                applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2026 800 Series Only PFFS Contract.pdf       pdf         269906.0                cms_gov
                                                                 applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2026 800 Series Only-PDP Contract.pdf       pdf         228490.0        context cms_gov
                                                                 applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2026 800 Series Only-PDP Contract.pdf       pdf         228490.0                cms_gov
                                                               applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2026 800 Series Only_MA-PD Addendum.pdf       pdf         224864.0        context cms_gov
                                                               applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2026 800 Series Only_MA-PD Addendum.pdf       pdf         224864.0                cms_gov
                                                                                 applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2026 CCP Contract.pdf       pdf         244400.0                cms_gov
                                                                                 applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2026 CCP Contract.pdf       pdf         244400.0        context cms_gov
                                                                              applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2026 ED PDP Contract.pdf       pdf         225031.0        context cms_gov
                                                                              applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2026 ED PDP Contract.pdf       pdf         225031.0                cms_gov
                                                               applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2026 EGWP Cost Part D Only Addendum.pdf       pdf         190243.0        context cms_gov
                                                               applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2026 EGWP Cost Part D Only Addendum.pdf       pdf         190243.0                cms_gov
                                                                        applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2026 EGWP MA-Only Addendum.pdf       pdf         172269.0                cms_gov
                                                                        applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2026 EGWP MA-Only Addendum.pdf       pdf         172269.0        context cms_gov
                                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2026 EGWP MA-PD Addendum.pdf       pdf         203692.0                cms_gov
                                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2026 EGWP MA-PD Addendum.pdf       pdf         203692.0        context cms_gov
                                                                            applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2026 EGWP MSA Addendum.pdf       pdf         164842.0        context cms_gov
                                                                            applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2026 EGWP MSA Addendum.pdf       pdf         164842.0                cms_gov
                                                                            applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2026 EGWP PDP Addendum.pdf       pdf         190661.0                cms_gov
                                                                            applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2026 EGWP PDP Addendum.pdf       pdf         190661.0        context cms_gov
                                                                               applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2026 MA-PD Addendum.pdf       pdf         204141.0                cms_gov
                                                                               applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2026 MA-PD Addendum.pdf       pdf         204141.0        context cms_gov
                                                                 applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2026 MSA 800 Series-Only Contract.pdf       pdf         251081.0                cms_gov
                                                                 applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2026 MSA 800 Series-Only Contract.pdf       pdf         251081.0        context cms_gov
                                                                                 applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2026 MSA Contract.pdf       pdf         241503.0                cms_gov
                                                                                 applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2026 MSA Contract.pdf       pdf         241503.0        context cms_gov
                                                                                 applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2026 PDP Contract.pdf       pdf         215164.0        context cms_gov
                                                                                 applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2026 PDP Contract.pdf       pdf         215164.0                cms_gov
                                                                                applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2026 PFFS Contract.pdf       pdf         247683.0        context cms_gov
                                                                                applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2026 PFFS Contract.pdf       pdf         247683.0                cms_gov
                                                                        applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2026 Signature Attestation.pdf       pdf          66260.0        context cms_gov
                                                                        applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/2026 Signature Attestation.pdf       pdf          66260.0                cms_gov
                                                              applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/231921_AmbulanceReport_Rule_31July-e.pdf       pdf        4357312.0                cms_gov
                                                              applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/231921_AmbulanceReport_Rule_31July-e.pdf       pdf        4357312.0        context cms_gov
                                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/3.10_SP_Duplicate_120907.pdf       pdf         261577.0                cms_gov
                                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/3.10_SP_Duplicate_120907.pdf       pdf         261577.0        context cms_gov
                                                                   applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/3.11_SP_Deductible_PartB_120907.pdf       pdf         304780.0                cms_gov
                                                                   applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/3.11_SP_Deductible_PartB_120907.pdf       pdf         304780.0        context cms_gov
                                                                 applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/3.12_SP_Deductible_Benefit_120907.pdf       pdf         396224.0                cms_gov
                                                                 applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/3.12_SP_Deductible_Benefit_120907.pdf       pdf         396224.0        context cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/3.13_SP_Providerlist_120907.pdf       pdf         264868.0                cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/3.13_SP_Providerlist_120907.pdf       pdf         264868.0        context cms_gov
                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/3.14_SP_NoneRemain_120622.pdf       pdf         273614.0        context cms_gov
                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/3.14_SP_NoneRemain_120622.pdf       pdf         273614.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/3.15_SP_Adjusted_120409.pdf       pdf         263076.0        context cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/3.15_SP_Adjusted_120409.pdf       pdf         263076.0                cms_gov
                                                                                applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/3.16_SP_Pay_120907.pdf       pdf         323351.0        context cms_gov
                                                                                applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/3.16_SP_Pay_120907.pdf       pdf         323351.0                cms_gov
                                                                             applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/3.17_SP_NoSHIP_120409.pdf       pdf         380062.0        context cms_gov
                                                                             applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/3.17_SP_NoSHIP_120409.pdf       pdf         380062.0                cms_gov
                                                                               applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/3.1_SP_PartA_120907.pdf       pdf         393943.0        context cms_gov
                                                                               applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/3.1_SP_PartA_120907.pdf       pdf         393943.0                cms_gov
                                                                                applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/3.2_SP_BofA_121016.pdf       pdf         366180.0                cms_gov
                                                                                applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/3.2_SP_BofA_121016.pdf       pdf         366180.0        context cms_gov
                                                                             applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/3.3_SP_Hospice_121016.pdf       pdf         347214.0                cms_gov
                                                                             applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/3.3_SP_Hospice_121016.pdf       pdf         347214.0        context cms_gov
                                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/3.4_SP_HomeHealth_120907.pdf       pdf         343866.0                cms_gov
                                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/3.4_SP_HomeHealth_120907.pdf       pdf         343866.0        context cms_gov
                                                                      applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/3.6_SP_PartB_Assigned_121016.pdf       pdf         373832.0        context cms_gov
                                                                      applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/3.6_SP_PartB_Assigned_121016.pdf       pdf         373832.0                cms_gov
                                                                    applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/3.7_SP_PartB_Unassigned_120907.pdf       pdf         328990.0                cms_gov
                                                                    applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/3.7_SP_PartB_Unassigned_120907.pdf       pdf         328990.0        context cms_gov
                                                                        applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/3.8_SP_DME_Assigned_120907.pdf       pdf         331254.0        context cms_gov
                                                                        applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/3.8_SP_DME_Assigned_120907.pdf       pdf         331254.0                cms_gov
                                                                      applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/3.9_SP_DME_Unassigned_120907.pdf       pdf         312406.0        context cms_gov
                                                                      applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/3.9_SP_DME_Unassigned_120907.pdf       pdf         312406.0                cms_gov
                                        applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/508-Version-ICD-10-CM-CONVERSION-TABLE-FY2026-April 1 2026.csv       csv         138437.0           data cms_gov
                                        applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/508-Version-ICD-10-CM-CONVERSION-TABLE-FY2026-April 1 2026.csv       csv         138437.0                cms_gov
                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/508-compliant-version-ICD_10_CM_CONVERSION_TABLE_FY2026.txt       txt         138455.0        context cms_gov
                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/508-compliant-version-ICD_10_CM_CONVERSION_TABLE_FY2026.txt       txt         138455.0                cms_gov
                                                                  applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/508-compliant-version-of-Example.txt       txt           1148.0        context cms_gov
                                                                  applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/508-compliant-version-of-Example.txt       txt           1148.0                cms_gov
                                                applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/508-compliant-version-of-Ground Ambulance Vehicles.txt       txt            256.0        context cms_gov
                                                applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/508-compliant-version-of-Ground Ambulance Vehicles.txt       txt            256.0                cms_gov
                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/508-compliant-version-of-Other Vehicles.txt       txt            400.0        context cms_gov
                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/508-compliant-version-of-Other Vehicles.txt       txt            400.0                cms_gov
                                                                   applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/508-compliant-version-of-Readme.txt       txt          12163.0                cms_gov
                                                                   applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/508-compliant-version-of-Readme.txt       txt          12163.0        context cms_gov
                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/508_Compliant_Version_of_ICD-10-CM-Conversion-Table-FY25.csv       csv         127424.0                cms_gov
                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/508_Compliant_Version_of_ICD-10-CM-Conversion-Table-FY25.csv       csv         127424.0           data cms_gov
                                                              applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/508_Compliant_Version_of_SampledNPIs.csv       csv         126589.0           data cms_gov
                                                              applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/508_Compliant_Version_of_SampledNPIs.csv       csv         126589.0                cms_gov
                                                                             applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/508compliantversionY2.csv       csv         125587.0           data cms_gov
                                                                             applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/508compliantversionY2.csv       csv         125587.0                cms_gov
                                                                      applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/837i_form_cms_1450_mln006926.pdf       pdf         853296.0        context cms_gov
                                                                      applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/837i_form_cms_1450_mln006926.pdf       pdf         853296.0                cms_gov
                                                                                                applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/8a.pdf       pdf          14626.0        context cms_gov
                                                                                                applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/8a.pdf       pdf          14626.0                cms_gov
                                                                                        applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/About-CMS.html      html         243537.0                cms_gov
                                                                                        applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/About-CMS.html      html         243537.0        context cms_gov
                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/Agent-Broker-Help-Desks Updates_051024_0.pdf       pdf         305542.0        context cms_gov
                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/Agent-Broker-Help-Desks Updates_051024_0.pdf       pdf         305542.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/Allocation_508compliant.pdf       pdf         339224.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/Allocation_508compliant.pdf       pdf         339224.0        context cms_gov
                                                                             applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMS BUCKET 1 FULL.pd_.pdf       pdf         343522.0                cms_gov
                                                                             applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMS BUCKET 1 FULL.pd_.pdf       pdf         343522.0        context cms_gov
                                                                                 applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMS BUCKET 2 FULL.pdf       pdf         315805.0                cms_gov
                                                                                 applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMS BUCKET 2 FULL.pdf       pdf         315805.0        context cms_gov
                                                                                 applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMS BUCKET 3 FULL.pdf       pdf         374651.0                cms_gov
                                                                                 applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMS BUCKET 3 FULL.pdf       pdf         374651.0        context cms_gov
                                                                                 applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMS BUCKET 4 FULL.pdf       pdf         213023.0        context cms_gov
                                                                                 applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMS BUCKET 4 FULL.pdf       pdf         213023.0                cms_gov
                                                                                 applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMS BUCKET 5 FULL.pdf       pdf         129889.0        context cms_gov
                                                                                 applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMS BUCKET 5 FULL.pdf       pdf         129889.0                cms_gov
                                                                             applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMS BUCKET 6 FULL.pd_.pdf       pdf         329082.0        context cms_gov
                                                                             applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMS BUCKET 6 FULL.pd_.pdf       pdf         329082.0                cms_gov
                                                                             applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMS BUCKET 7 FULL.pd_.pdf       pdf         420178.0                cms_gov
                                                                             applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMS BUCKET 7 FULL.pd_.pdf       pdf         420178.0        context cms_gov
                                                                             applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMS BUCKET 8 FULL.pd_.pdf       pdf         306223.0                cms_gov
                                                                             applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMS BUCKET 8 FULL.pd_.pdf       pdf         306223.0        context cms_gov
                                                                                 applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMS BUCKET 9 FULL.pdf       pdf         390452.0                cms_gov
                                                                                 applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMS BUCKET 9 FULL.pdf       pdf         390452.0        context cms_gov
                                                                                     applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMS Form 18F5.pdf       pdf         175443.0                cms_gov
                                                                                     applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMS Form 18F5.pdf       pdf         175443.0        context cms_gov
                                                                                     applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMS Form L564.pdf       pdf          90157.0                cms_gov
                                                                                     applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMS Form L564.pdf       pdf          90157.0        context cms_gov
                                                                        applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMS Mark License Agreement.pdf       pdf         192608.0                cms_gov
                                                                        applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMS Mark License Agreement.pdf       pdf         192608.0        context cms_gov
                                                                             applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMS-40B (508)July2023.pdf       pdf          96875.0                cms_gov
                                                                             applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMS-40B (508)July2023.pdf       pdf          96875.0        context cms_gov
                                                                               applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMS-855B - 04052021.pdf       pdf         863590.0        context cms_gov
                                                                               applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMS-855B - 04052021.pdf       pdf         863590.0                cms_gov
                                                                                     applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMS-855I-508C.pdf       pdf         497728.0                cms_gov
                                                                                     applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMS-855I-508C.pdf       pdf         497728.0        context cms_gov
                                                                                 applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMS-Form 4040-508.pdf       pdf          82369.0                cms_gov
                                                                                 applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMS-Form 4040-508.pdf       pdf          82369.0        context cms_gov
                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMSAmbdata_Y2sample_post.xlsx      xlsx         119646.0                cms_gov
                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMSAmbdata_Y2sample_post.xlsx      xlsx         119646.0           data cms_gov
                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMSAmbdata_Y3sample_post.xlsx      xlsx         121169.0                cms_gov
                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMSAmbdata_Y3sample_post.xlsx      xlsx         121169.0           data cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMSAmbdata_Y3sample_post508.csv       csv         124302.0           data cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMSAmbdata_Y3sample_post508.csv       csv         124302.0                cms_gov
                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMSAmbdata_Y4sample_post.xlsx      xlsx         120847.0           data cms_gov
                                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMSAmbdata_Y4sample_post.xlsx      xlsx         120847.0                cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMSAmbdata_Y4sample_post508.csv       csv         124148.0           data cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMSAmbdata_Y4sample_post508.csv       csv         124148.0                cms_gov
                                 applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/COVID-19 Updated Guidance for MA and Part D Plan Sponsors 5.22.20.pdf       pdf         190580.0                cms_gov
                                 applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/COVID-19 Updated Guidance for MA and Part D Plan Sponsors 5.22.20.pdf       pdf         190580.0        context cms_gov
                                                  applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CY 2024 MA Enrollment and Disenrollment Guidance.pdf       pdf        2822615.0                cms_gov
                                                  applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CY 2024 MA Enrollment and Disenrollment Guidance.pdf       pdf        2822615.0        context cms_gov
                                                                applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CY 2025 MA appendices and exhibits.pdf       pdf        1209299.0                cms_gov
                                                                applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CY 2025 MA appendices and exhibits.pdf       pdf        1209299.0        context cms_gov
                                                               applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CY 2025 PDP appendices and exhibits.pdf       pdf         891196.0                cms_gov
                                                               applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CY 2025 PDP appendices and exhibits.pdf       pdf         891196.0        context cms_gov
                                                                              applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CY2026 DUA AGREEMENT.pdf       pdf          44806.0                cms_gov
                                                                              applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CY2026 DUA AGREEMENT.pdf       pdf          44806.0        context cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CY2026_Landscape_202603.csv       csv       79215802.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CY2026_Landscape_202603.csv       csv       79215802.0           data cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CY2026_Landscape_ReadMe.txt       txt          11609.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CY2026_Landscape_ReadMe.txt       txt          11609.0        context cms_gov
                                                                 applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/Contracted_services_508_compliant.pdf       pdf         268782.0                cms_gov
                                                                 applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/Contracted_services_508_compliant.pdf       pdf         268782.0        context cms_gov
                                                                                        applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/Crown-Memo.pdf       pdf         110141.0                cms_gov
                                                                                        applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/Crown-Memo.pdf       pdf         110141.0        context cms_gov
                                                                                               applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/DRA.pdf       pdf         527638.0                cms_gov
                                                                                               applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/DRA.pdf       pdf         527638.0        context cms_gov
                                                                        applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/Document_Type_Descriptions.pdf       pdf         200693.0        context cms_gov
                                                                        applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/Document_Type_Descriptions.pdf       pdf         200693.0                cms_gov
                                                             applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/E-Signature How To Guide_Update_final.pdf       pdf        2503416.0                cms_gov
                                                             applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/E-Signature How To Guide_Update_final.pdf       pdf        2503416.0        context cms_gov
                                                                              applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/ESRDReportToCongress.pdf       pdf         984758.0        context cms_gov
                                                                              applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/ESRDReportToCongress.pdf       pdf         984758.0                cms_gov
                                                                                 applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/ESRDfinalrule0415.pdf       pdf         888550.0                cms_gov
                                                                                 applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/ESRDfinalrule0415.pdf       pdf         888550.0        context cms_gov
                                                                 applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/EnrollmentTips - Updated 11-28-16.pdf       pdf          59215.0        context cms_gov
                                                                 applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/EnrollmentTips - Updated 11-28-16.pdf       pdf          59215.0                cms_gov
                                                                        applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/FAQsESRDRolloutFINAL082808.pdf       pdf          62917.0        context cms_gov
                                                                        applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/FAQsESRDRolloutFINAL082808.pdf       pdf          62917.0                cms_gov
                                                                                        applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/FR04271999.pdf       pdf         528283.0                cms_gov
                                                                                        applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/FR04271999.pdf       pdf         528283.0        context cms_gov
                                                                                        applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/FR08072013.pdf       pdf         209778.0                cms_gov
                                                                                        applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/FR08072013.pdf       pdf         209778.0        context cms_gov
                                                                                        applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/FR08222002.pdf       pdf         444100.0                cms_gov
                                                                                        applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/FR08222002.pdf       pdf         444100.0        context cms_gov
                                                                                        applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/FR09262003.pdf       pdf         674385.0                cms_gov
                                                                                        applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/FR09262003.pdf       pdf         674385.0        context cms_gov
                                                                                        applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/FR11072003.pdf       pdf         528960.0        context cms_gov
                                                                                        applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/FR11072003.pdf       pdf         528960.0                cms_gov
                                                                              applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/FactSheet_june2023_0.pdf       pdf         178681.0                cms_gov
                                                                              applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/FactSheet_june2023_0.pdf       pdf         178681.0        context cms_gov
                                                   applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/Five_Top_GADCS_Tips_Year_1_and_2_508compliant_0.pdf       pdf          80848.0                cms_gov
                                                   applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/Five_Top_GADCS_Tips_Year_1_and_2_508compliant_0.pdf       pdf          80848.0        context cms_gov
                                                applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/Five_Top_GADCS_Tips_Year_3_and_Year_4_508compliant.pdf       pdf          65899.0        context cms_gov
                                                applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/Five_Top_GADCS_Tips_Year_3_and_Year_4_508compliant.pdf       pdf          65899.0                cms_gov
                                                                     applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/GADCS-User-Guide-02022024-508.pdf       pdf       12547244.0        context cms_gov
                                                                     applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/GADCS-User-Guide-02022024-508.pdf       pdf       12547244.0                cms_gov
                                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/Government_508_compliant.pdf       pdf         171768.0        context cms_gov
                                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/Government_508_compliant.pdf       pdf         171768.0                cms_gov
                                                                               applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/HE_Form_110722final.pdf       pdf         145656.0        context cms_gov
                                                                               applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/HE_Form_110722final.pdf       pdf         145656.0                cms_gov
                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/HPMS Memo - COVID-19 Vaccine Significant Cost Determination.pdf       pdf         129264.0        context cms_gov
                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/HPMS Memo - COVID-19 Vaccine Significant Cost Determination.pdf       pdf         129264.0                cms_gov
applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/HPMS Memo - Diagnostic Testing of Nursing Home Residents and Patients for Coronavirus Disease 2019.pdf       pdf          98215.0                cms_gov
applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/HPMS Memo - Diagnostic Testing of Nursing Home Residents and Patients for Coronavirus Disease 2019.pdf       pdf          98215.0        context cms_gov
                  applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/HPMS Memo - Waiver of Premiums related to COVID-19 Permissive Actions 10-15-2020.pdf       pdf          77365.0        context cms_gov
                  applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/HPMS Memo - Waiver of Premiums related to COVID-19 Permissive Actions 10-15-2020.pdf       pdf          77365.0                cms_gov
                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/ICD-10-CM FY25 Guidelines October 1, 2024.pdf       pdf         835361.0        context cms_gov
                                                         applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/ICD-10-CM FY25 Guidelines October 1, 2024.pdf       pdf         835361.0                cms_gov
                                                   applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/ICD-10-CM-CONVERSION-TABLE-FY2026-April 1 2026.xlsx      xlsx         164738.0           data cms_gov
                                                   applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/ICD-10-CM-CONVERSION-TABLE-FY2026-April 1 2026.xlsx      xlsx         164738.0                cms_gov
                                     applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/ICD-10-CM-Conversion-Table-FY2025-Effective-10-01-2024-FINAL.xlsx      xlsx         152230.0                cms_gov
                                     applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/ICD-10-CM-Conversion-Table-FY2025-Effective-10-01-2024-FINAL.xlsx      xlsx         152230.0           data cms_gov
                                                                applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/ICD_10_CM_CONVERSION_TABLE_FY2026.xlsx      xlsx         164524.0                cms_gov
                                                                applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/ICD_10_CM_CONVERSION_TABLE_FY2026.xlsx      xlsx         164524.0           data cms_gov
                                                             applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IDE Study Criteria Crosswalk Sep 2014.pdf       pdf          91450.0        context cms_gov
                                                             applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IDE Study Criteria Crosswalk Sep 2014.pdf       pdf          91450.0                cms_gov
                                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_FULL_2025-01-01.parquet   parquet       14487239.0                cms_gov
                                                                          applied-ml/ai-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_FULL_2025-01-01.parquet   parquet       14487239.0           data cms_gov
                                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_FULL_2025-04-01.parquet   parquet        3487863.0                cms_gov
                                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_FULL_2025-04-01.parquet   parquet        3487863.0           data cms_gov
                                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_Full_2025-07-01.parquet   parquet       14865211.0                cms_gov
                                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_Full_2025-07-01.parquet   parquet       14865211.0           data cms_gov
                                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_Full_2025-10-01.parquet   parquet       15356754.0           data cms_gov
                                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_Full_2025-10-01.parquet   parquet       15356754.0                cms_gov
                                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_Full_2026-01-02.parquet   parquet       15583235.0                cms_gov
                                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_Full_2026-01-02.parquet   parquet       15583235.0           data cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_HHA_2025-01-01.parquet   parquet        1683778.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_HHA_2025-01-01.parquet   parquet        1683778.0           data cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_HHA_2025-04-01.parquet   parquet        1739053.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_HHA_2025-04-01.parquet   parquet        1739053.0           data cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_HHA_2025-07-01.parquet   parquet        1752542.0           data cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_HHA_2025-07-01.parquet   parquet        1752542.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_HHA_2025-10-01.parquet   parquet        1775817.0           data cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_HHA_2025-10-01.parquet   parquet        1775817.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_HHA_2026-01-02.parquet   parquet        1810247.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_HHA_2026-01-02.parquet   parquet        1810247.0           data cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_HHA_LRO_2025-01-01.parquet   parquet         589692.0                cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_HHA_LRO_2025-01-01.parquet   parquet         589692.0           data cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_HHA_LRO_2025-04-01.parquet   parquet         618746.0                cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_HHA_LRO_2025-04-01.parquet   parquet         618746.0           data cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_HHA_LRO_2025-07-01.parquet   parquet         626401.0                cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_HHA_LRO_2025-07-01.parquet   parquet         626401.0           data cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_HHA_LRO_2025-10-01.parquet   parquet         642466.0           data cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_HHA_LRO_2025-10-01.parquet   parquet         642466.0                cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_HHA_LRO_2026-01-02.parquet   parquet         652533.0           data cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_HHA_LRO_2026-01-02.parquet   parquet         652533.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_HOS_2025-01-01.parquet   parquet         520036.0           data cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_HOS_2025-01-01.parquet   parquet         520036.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_HOS_2025-04-01.parquet   parquet         525257.0           data cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_HOS_2025-04-01.parquet   parquet         525257.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_HOS_2025-07-01.parquet   parquet         531798.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_HOS_2025-07-01.parquet   parquet         531798.0           data cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_HOS_2025-10-01.parquet   parquet         550244.0           data cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_HOS_2025-10-01.parquet   parquet         550244.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_HOS_2026-01-02.parquet   parquet         552426.0           data cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_HOS_2026-01-02.parquet   parquet         552426.0                cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_HOS_LRO_2025-01-01.parquet   parquet         259334.0           data cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_HOS_LRO_2025-01-01.parquet   parquet         259334.0                cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_HOS_LRO_2025-04-01.parquet   parquet         261762.0           data cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_HOS_LRO_2025-04-01.parquet   parquet         261762.0                cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_HOS_LRO_2025-07-01.parquet   parquet         263359.0           data cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_HOS_LRO_2025-07-01.parquet   parquet         263359.0                cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_HOS_LRO_2025-10-01.parquet   parquet         268914.0                cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_HOS_LRO_2025-10-01.parquet   parquet         268914.0           data cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_HOS_LRO_2026-01-02.parquet   parquet         270877.0                cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_HOS_LRO_2026-01-02.parquet   parquet         270877.0           data cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_INP_2025-01-01.parquet   parquet        6431301.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_INP_2025-01-01.parquet   parquet        6431301.0           data cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_INP_2025-04-01.parquet   parquet        6464315.0           data cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_INP_2025-04-01.parquet   parquet        6464315.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_INP_2025-07-01.parquet   parquet        6576285.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_INP_2025-07-01.parquet   parquet        6576285.0           data cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_INP_2025-10-01.parquet   parquet        6659387.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_INP_2025-10-01.parquet   parquet        6659387.0           data cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_INP_2025-12-05.parquet   parquet        6753939.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_INP_2025-12-05.parquet   parquet        6753939.0           data cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_INP_2026-01-02.parquet   parquet        6736147.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_INP_2026-01-02.parquet   parquet        6736147.0           data cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_INP_LRO_2025-01-01.parquet   parquet         681319.0                cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_INP_LRO_2025-01-01.parquet   parquet         681319.0           data cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_INP_LRO_2025-04-01.parquet   parquet         682197.0                cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_INP_LRO_2025-04-01.parquet   parquet         682197.0           data cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_INP_LRO_2025-07-01.parquet   parquet         684819.0           data cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_INP_LRO_2025-07-01.parquet   parquet         684819.0                cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_INP_LRO_2025-10-01.parquet   parquet         184253.0           data cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_INP_LRO_2025-10-01.parquet   parquet         184253.0                cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_INP_LRO_2025-12-05.parquet   parquet         680238.0           data cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_INP_LRO_2025-12-05.parquet   parquet         680238.0                cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_INP_LRO_2026-01-02.parquet   parquet         687307.0           data cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_INP_LRO_2026-01-02.parquet   parquet         687307.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IPF_2025-01-01.parquet   parquet         939464.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IPF_2025-01-01.parquet   parquet         939464.0           data cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IPF_2025-04-01.parquet   parquet         949465.0           data cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IPF_2025-04-01.parquet   parquet         949465.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IPF_2025-07-01.parquet   parquet         956686.0           data cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IPF_2025-07-01.parquet   parquet         956686.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IPF_2025-07-29.parquet   parquet         960735.0           data cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IPF_2025-07-29.parquet   parquet         960735.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IPF_2025-10-01.parquet   parquet         968898.0           data cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IPF_2025-10-01.parquet   parquet         968898.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IPF_2026-01-02.parquet   parquet         978135.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IPF_2026-01-02.parquet   parquet         978135.0           data cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IPF_LRO_2025-01-01.parquet   parquet         180831.0                cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IPF_LRO_2025-01-01.parquet   parquet         180831.0           data cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IPF_LRO_2025-04-01.parquet   parquet         182120.0                cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IPF_LRO_2025-04-01.parquet   parquet         182120.0           data cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IPF_LRO_2025-07-01.parquet   parquet         684819.0                cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IPF_LRO_2025-07-01.parquet   parquet         684819.0           data cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IPF_LRO_2025-07-29.parquet   parquet         183083.0                cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IPF_LRO_2025-07-29.parquet   parquet         183083.0           data cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IPF_LRO_2025-10-01.parquet   parquet         184253.0                cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IPF_LRO_2025-10-01.parquet   parquet         184253.0           data cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IPF_LRO_2026-01-02.parquet   parquet         183629.0                cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IPF_LRO_2026-01-02.parquet   parquet         183629.0           data cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IRF_2025-01-01.parquet   parquet        1189923.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IRF_2025-01-01.parquet   parquet        1189923.0           data cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IRF_2025-04-01.parquet   parquet        1202580.0           data cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IRF_2025-04-01.parquet   parquet        1202580.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IRF_2025-07-01.parquet   parquet        1220601.0           data cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IRF_2025-07-01.parquet   parquet        1220601.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IRF_2025-10-01.parquet   parquet        1233617.0           data cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IRF_2025-10-01.parquet   parquet        1233617.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IRF_2026-01-02.parquet   parquet        1248887.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IRF_2026-01-02.parquet   parquet        1248887.0           data cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IRF_LRO_2025-01-01.parquet   parquet         235172.0           data cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IRF_LRO_2025-01-01.parquet   parquet         235172.0                cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IRF_LRO_2025-04-01.parquet   parquet         235926.0           data cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IRF_LRO_2025-04-01.parquet   parquet         235926.0                cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IRF_LRO_2025-07-01.parquet   parquet         236421.0           data cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IRF_LRO_2025-07-01.parquet   parquet         236421.0                cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IRF_LRO_2025-10-01.parquet   parquet         237017.0           data cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IRF_LRO_2025-10-01.parquet   parquet         237017.0                cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IRF_LRO_2026-01-02.parquet   parquet         238081.0                cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_IRF_LRO_2026-01-02.parquet   parquet         238081.0           data cms_gov
                                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_LTCH_2025-01-01.parquet   parquet         359136.0                cms_gov
                                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_LTCH_2025-01-01.parquet   parquet         359136.0           data cms_gov
                                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_LTCH_2025-04-01.parquet   parquet         366667.0                cms_gov
                                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_LTCH_2025-04-01.parquet   parquet         366667.0           data cms_gov
                                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_LTCH_2025-07-01.parquet   parquet         372736.0           data cms_gov
                                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_LTCH_2025-07-01.parquet   parquet         372736.0                cms_gov
                                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_LTCH_2025-10-01.parquet   parquet         371793.0           data cms_gov
                                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_LTCH_2025-10-01.parquet   parquet         371793.0                cms_gov
                                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_LTCH_2026-01-02.parquet   parquet         379725.0           data cms_gov
                                                                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_LTCH_2026-01-02.parquet   parquet         379725.0                cms_gov
                                                                      applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_LTCH_LRO_2025-01-01.parquet   parquet          86873.0                cms_gov
                                                                      applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_LTCH_LRO_2025-01-01.parquet   parquet          86873.0           data cms_gov
                                                                      applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_LTCH_LRO_2025-04-01.parquet   parquet          86705.0           data cms_gov
                                                                      applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_LTCH_LRO_2025-04-01.parquet   parquet          86705.0                cms_gov
                                                                      applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_LTCH_LRO_2025-07-01.parquet   parquet          87171.0                cms_gov
                                                                      applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_LTCH_LRO_2025-07-01.parquet   parquet          87171.0           data cms_gov
                                                                      applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_LTCH_LRO_2025-10-01.parquet   parquet          86611.0                cms_gov
                                                                      applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_LTCH_LRO_2025-10-01.parquet   parquet          86611.0           data cms_gov
                                                                      applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_LTCH_LRO_2026-01-02.parquet   parquet          87255.0           data cms_gov
                                                                      applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_LTCH_LRO_2026-01-02.parquet   parquet          87255.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_SNF_2025-01-01.parquet   parquet        3515822.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_SNF_2025-01-01.parquet   parquet        3515822.0           data cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_SNF_2025-04-01.parquet   parquet        3487863.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_SNF_2025-04-01.parquet   parquet        3487863.0           data cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_SNF_2025-07-01.parquet   parquet        3498918.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_SNF_2025-07-01.parquet   parquet        3498918.0           data cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_SNF_2025-10-01.parquet   parquet        3651931.0           data cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_SNF_2025-10-01.parquet   parquet        3651931.0                cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_SNF_2026-01-02.parquet   parquet        3711642.0           data cms_gov
                                                                           applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_SNF_2026-01-02.parquet   parquet        3711642.0                cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_SNF_LRO_2025-01-01.parquet   parquet         843709.0                cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_SNF_LRO_2025-01-01.parquet   parquet         843709.0           data cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_SNF_LRO_2025-04-01.parquet   parquet         847963.0           data cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_SNF_LRO_2025-04-01.parquet   parquet         847963.0                cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_SNF_LRO_2025-07-01.parquet   parquet         850209.0           data cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_SNF_LRO_2025-07-01.parquet   parquet         850209.0                cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_SNF_LRO_2025-10-01.parquet   parquet         908940.0           data cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_SNF_LRO_2025-10-01.parquet   parquet         908940.0                cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_SNF_LRO_2026-01-02.parquet   parquet         933700.0           data cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_SNF_LRO_2026-01-02.parquet   parquet         933700.0                cms_gov
                                                                applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/MA_Step_Therapy_HPMS_Memo_8_7_2018.pdf       pdf          57614.0        context cms_gov
                                                                applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/MA_Step_Therapy_HPMS_Memo_8_7_2018.pdf       pdf          57614.0                cms_gov
                    applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/MLN Enrollment Webcast Presentation Multi_Factor Authentication for I&A System.pdf       pdf        1214232.0        context cms_gov
                    applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/MLN Enrollment Webcast Presentation Multi_Factor Authentication for I&A System.pdf       pdf        1214232.0                cms_gov
                      applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/MLN Enrollment Webcast Transcript Multi-Factor Authentication for I&A System.pdf       pdf         296515.0        context cms_gov
                      applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/MLN Enrollment Webcast Transcript Multi-Factor Authentication for I&A System.pdf       pdf         296515.0                cms_gov
                                                                                     applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/MMAProvisions.pdf       pdf         234297.0        context cms_gov
                                                                                     applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/MMAProvisions.pdf       pdf         234297.0                cms_gov
                                                                        applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/MPS-QuickReferenceChart-1.html      html          43618.0        context cms_gov
                                                                        applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/MPS-QuickReferenceChart-1.html      html          43618.0                cms_gov
                                                                     applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/MSN Message Character Limits.xlsx      xlsx          22278.0           data cms_gov
                                                                     applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/MSN Message Character Limits.xlsx      xlsx          22278.0                cms_gov
                                                   applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/Mandatory-Clinical-Trial-Identifier-Number-QsAs.pdf       pdf          94198.0                cms_gov
                                                   applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/Mandatory-Clinical-Trial-Identifier-Number-QsAs.pdf       pdf          94198.0        context cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/Med-Prov-Enroll-MLN9658742.html      html         116865.0                cms_gov
                                                                       applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/Med-Prov-Enroll-MLN9658742.html      html         116865.0        context cms_gov
                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/Medicare_Ground_Ambulance_Data_Collection_System_Instrument_Nov_2023_508.pdf       pdf         710062.0        context cms_gov
                          applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/Medicare_Ground_Ambulance_Data_Collection_System_Instrument_Nov_2023_508.pdf       pdf         710062.0                cms_gov
                                 applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/Medicare_Provider-Supplier_Enrollment_National_Education_Products.pdf       pdf         145363.0                cms_gov
                                 applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/Medicare_Provider-Supplier_Enrollment_National_Education_Products.pdf       pdf         145363.0        context cms_

<a id="data-engineer-q3"></a>
#### Q3: Which files came from ZIP archives versus direct downloads?

**Flow:** `agent_chat` → `agent_engineer` (meta_chat)

| Step | Agent | Action | Time |
|------|-------|--------|------|
| 1 | agent_chat | `transfer_to_agent` | 2.8s |
| 2 | agent_engineer | `meta_chat` | 5.3s |
| | | **Total** | **95.5s** |

**Answer:**

Based on the analysis of the onboarding metadata, files can be distinguished by their origin: **Direct Downloads** are identified by the presence of an original source URL, while **Files from ZIP archives** (and other processing) are typically recorded without an original URL as they were extracted from archives or generated during the pipeline's processing phases.

### File Origin Breakdown
The following table summarizes the files by their origin and type. "Extracted from ZIP" specifically refers to data files (CSV, Parquet, XLSX, XML) that were uncovered from archives, whereas "Direct Downloads" include the initial files acquired from the web.

```
                       file_origin file_type  file_count
                   Direct Download       pdf       292.0
                   Direct Download   parquet        87.0
                   Direct Download       csv        65.0
                   Direct Download       txt        62.0
                   Direct Download       xml        26.0
                   Direct Download      xlsx        23.0
                   Direct Download      html         5.0
                   Direct Download        gz         2.0
                   Direct Download                   1.0
         Extracted from ZIP (Data)   parquet        87.0
         Extracted from ZIP (Data)       csv        65.0
         Extracted from ZIP (Data)      xlsx        21.0
         Extracted from ZIP (Data)       xml        13.0
                    Other/Internal      json         2.0
                    Other/Internal        gz         2.0
                    Other/Internal                   1.0
Processed Context (from PDF/other)        md       352.0
Processed Context (from PDF/other)       pdf       254.0
Processed Context (from PDF/other)       txt        42.0
Processed Context (from PDF/other)      html         5.0
```

### Key Insights

*   **Direct Downloads**: A total of **563 files** were downloaded directly. The most common directly downloaded file types are **PDFs (292)**, followed by **Parquet (87)** and **CSV (65)**.
*   **Extracted from ZIP Archives**: There are **186 data files** (Parquet, CSV, XLSX, and XML) that were extracted from the **94 ZIP archives** identified in the inventory. These files do not have direct source URLs because they reside within the downloaded archives.
*   **Processed Context**: Additionally, **653 context files** (mostly **Markdown (352)** and **PDF (254)**) were generated or extracted (e.g., page-level extraction from larger documents) during the onboarding process to provide additional metadata for the datasets.
*   **Archive Folder**: ZIP archives themselves are stored in the `archives/` directory, while their extracted contents are placed in the `files/` directory for further processing.

<a id="data-engineer-q4"></a>
#### Q4: What schema decisions were made for the provider tables?

**Flow:** `agent_chat` → `agent_engineer` (meta_chat)

| Step | Agent | Action | Time |
|------|-------|--------|------|
| 1 | agent_chat | `transfer_to_agent` | 2.2s |
| 2 | agent_engineer | `meta_chat` | 4.4s |
| | | **Total** | **74.8s** |

**Answer:**

### Summary
Based on the metadata, several schema decisions were made for tables related to healthcare providers, specifically ground ambulance providers and facilities under the Inpatient Prospective Payment System (IPPS). These decisions involve specific partitioning, clustering, and data enrichment strategies to support Medicare payment analysis and provider tracking.

## Data retrieved

| decision_id | table_name | reasoning | status | proposal | created_at |
|:---|:---|:---|:---|:---|:---|
| 159a3627-73a0-4191-9f66-3411fd76111e | _508_compliant_version_of_sampled_npis | A list of ground ambulance providers and suppliers selected to submit data in Year 1 of the Medicare Ground Ambulance Data Collection System (GADCS). It includes organization names and state-level address information from the National Plan and Provider Enumeration System (NPPES). | proposed | {"cluster_by":[],"columns":[{"category":"text","dtype":"object","name":"medicare_ground_ambulance_data_collection","source_name":"Medicare Ground Ambulance Data Collection"},{"category":"text","dtype":"object","name":"unnamed_1","source_name":"Unnamed: 1"},{"category":"text","dtype":"object","name":"unnamed_2","source_name":"Unnamed: 2"},{"category":"text","dtype":"object","name":"unnamed_3","source_name":"Unnamed: 3"}],"description":"A list of ground ambulance providers and suppliers selected to submit data in Year 1 of the Medicare Ground Ambulance Data Collection System (GADCS). It includes organization names and state-level address information from the National Plan and Provider Enumeration System (NPPES).","enriched_columns":[{"attributed_to":["page_025.md","page_330.md"],"bq_type":"STRING","description":"Implicitly contains the National Provider Identifier (NPI) of the selected ground ambulance organization.","mode":"NULLABLE","name":"npi","notes":"This column contains descriptive text and should be processed to extract relevant information or used as file-level metadata.","source_name":"Medicare Ground Ambulance Data Collection"},{"attributed_to":["page_025.md","page_330.md"],"bq_type":"STRING","description":"The legal business name of the ground ambulance organization as registered in NPPES.","mode":"NULLABLE","name":"nppes_organization_name","notes":"Header 'NPPES Organization Name' is in the first data row.","source_name":"Unnamed: 1"},{"attributed_to":["page_025.md","page_330.md"],"bq_type":"STRING","description":"The state abbreviation for the organization's practice address as registered in NPPES.","mode":"NULLABLE","name":"nppes_practice_address_state","notes":"Header 'NPPES Practice Address State' is in the first data row.","source_name":"Unnamed: 2"},{"attributed_to":["page_025.md","page_330.md"],"bq_type":"STRING","description":"The state abbreviation for the organization's mailing address as registered in NPPES.","mode":"NULLABLE","name":"nppes_mailing_address_state","notes":"Header 'NPPES Mailing Address State' is in the first data row.","source_name":"Unnamed: 3"}],"full_table_id":"statmike-mlops-349915.data_onboarding_cms_gov_bronze._508_compliant_version_of_sampled_npis","partition_by":null,"related_tables":{},"row_count":500,"source_file":"508_Compliant_Version_of_SampledNPIs.csv","source_files":["508_Compliant_Version_of_SampledNPIs.csv"],"source_path":"applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/508_Compliant_Version_of_SampledNPIs.csv","source_paths":["applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/508_Compliant_Version_of_SampledNPIs.csv"],"table_name":"_508_compliant_version_of_sampled_npis"} | 2026-03-31 14:55:49 |
| 86d13749-549c-4cd6-bd5b-d5cdea5940fb | _508compliantversion_y2 | A list of ground ambulance providers and suppliers selected to submit data in Year 2 of the Medicare Ground Ambulance Data Collection System (GADCS). It includes organization names and state-level address information from the National Plan and Provider Enumeration System (NPPES). | proposed | {"cluster_by":[],"columns":[{"category":"text","dtype":"object","name":"medicare_ground_ambulance_data_collection","source_name":"Medicare Ground Ambulance Data Collection"},{"category":"text","dtype":"object","name":"unnamed_1","source_name":"Unnamed: 1"},{"category":"text","dtype":"object","name":"unnamed_2","source_name":"Unnamed: 2"},{"category":"text","dtype":"object","name":"unnamed_3","source_name":"Unnamed: 3"}],"description":"A list of ground ambulance providers and suppliers selected to submit data in Year 2 of the Medicare Ground Ambulance Data Collection System (GADCS). It includes organization names and state-level address information from the National Plan and Provider Enumeration System (NPPES).","enriched_columns":[{"attributed_to":["page_025.md","page_330.md"],"bq_type":"STRING","description":"Implicitly contains the National Provider Identifier (NPI) of the selected ground ambulance organization.","mode":"NULLABLE","name":"npi","notes":"This column contains descriptive text and should be processed to extract relevant information or used as file-level metadata.","source_name":"Medicare Ground Ambulance Data Collection"},{"attributed_to":["page_025.md","page_330.md"],"bq_type":"STRING","description":"The legal business name of the ground ambulance organization as registered in NPPES.","mode":"NULLABLE","name":"nppes_organization_name","notes":"Header 'NPPES Organization Name' is in the first data row.","source_name":"Unnamed: 1"},{"attributed_to":["page_025.md","page_330.md"],"bq_type":"STRING","description":"The state abbreviation for the organization's practice address as registered in NPPES.","mode":"NULLABLE","name":"nppes_practice_address_state","notes":"Header 'NPPES Practice Address State' is in the first data row.","source_name":"Unnamed: 2"},{"attributed_to":["page_025.md","page_330.md"],"bq_type":"STRING","description":"The state abbreviation for the organization's mailing address as registered in NPPES.","mode":"NULLABLE","name":"nppes_mailing_address_state","notes":"Header 'NPPES Mailing Address State' is in the first data row.","source_name":"Unnamed: 3"}],"full_table_id":"statmike-mlops-349915.data_onboarding_cms_gov_bronze._508compliantversion_y2","partition_by":null,"related_tables":{},"row_count":500,"source_file":"508compliantversionY2.csv","source_files":["508compliantversionY2.csv"],"source_path":"applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/508compliantversionY2.csv","source_paths":["applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/508compliantversionY2.csv"],"table_name":"_508compliantversion_y2"} | 2026-03-31 14:55:49 |
| 76335ee9-ffc8-44b9-95ad-77d7082a4a85 | cmsambdata_y2sample_post | A list of ground ambulance providers and suppliers selected to submit data in Year 2 of the Medicare Ground Ambulance Data Collection System (GADCS). This file appears to be a duplicate of '508compliantversionY2.csv'. | proposed | {"cluster_by":[],"columns":[{"category":"text","dtype":"object","name":"medicare_ground_ambulance_data_collection","source_name":"Medicare Ground Ambulance Data Collection"},{"category":"text","dtype":"object","name":"unnamed_1","source_name":"Unnamed: 1"},{"category":"text","dtype":"object","name":"unnamed_2","source_name":"Unnamed: 2"},{"category":"text","dtype":"object","name":"unnamed_3","source_name":"Unnamed: 3"}],"description":"A list of ground ambulance providers and suppliers selected to submit data in Year 2 of the Medicare Ground Ambulance Data Collection System (GADCS). This file appears to be a duplicate of '508compliantversionY2.csv'.","enriched_columns":[{"attributed_to":["page_025.md","page_330.md"],"bq_type":"STRING","description":"Implicitly contains the National Provider Identifier (NPI) of the selected ground ambulance organization.","mode":"NULLABLE","name":"npi","notes":"This column contains descriptive text and should be processed to extract relevant information or used as file-level metadata.","source_name":"Medicare Ground Ambulance Data Collection"},{"attributed_to":["page_025.md","page_330.md"],"bq_type":"STRING","description":"The legal business name of the ground ambulance organization as registered in NPPES.","mode":"NULLABLE","name":"nppes_organization_name","notes":"Header 'NPPES Organization Name' is in the first data row.","source_name":"Unnamed: 1"},{"attributed_to":["page_025.md","page_330.md"],"bq_type":"STRING","description":"The state abbreviation for the organization's practice address as registered in NPPES.","mode":"NULLABLE","name":"nppes_practice_address_state","notes":"Header 'NPPES Practice Address State' is in the first data row.","source_name":"Unnamed: 2"},{"attributed_to":["page_025.md","page_330.md"],"bq_type":"STRING","description":"The state abbreviation for the organization's mailing address as registered in NPPES.","mode":"NULLABLE","name":"nppes_mailing_address_state","notes":"Header 'NPPES Mailing Address State' is in the first data row.","source_name":"Unnamed: 3"}],"full_table_id":"statmike-mlops-349915.data_onboarding_cms_gov_bronze.cmsambdata_y2sample_post","partition_by":null,"related_tables":{},"row_count":500,"source_file":"CMSAmbdata_Y2sample_post.xlsx","source_files":["CMSAmbdata_Y2sample_post.xlsx"],"source_path":"applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMSAmbdata_Y2sample_post.xlsx","source_paths":["applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMSAmbdata_Y2sample_post.xlsx"],"table_name":"cmsambdata_y2sample_post"} | 2026-03-31 14:55:49 |
| 6fa4a65a-d4a9-42e5-852c-4b52305343db | cmsambdata_y3sample_post | A list of ground ambulance providers and suppliers selected to submit data in Year 3 of the Medicare Ground Ambulance Data Collection System (GADCS). This file appears to be a duplicate of 'CMSAmbdata_Y3sample_post508.csv'. | proposed | {"cluster_by":[],"columns":[{"category":"text","dtype":"object","name":"medicare_ground_ambulance_data_collection","source_name":"Medicare Ground Ambulance Data Collection"},{"category":"text","dtype":"object","name":"unnamed_1","source_name":"Unnamed: 1"},{"category":"text","dtype":"object","name":"unnamed_2","source_name":"Unnamed: 2"},{"category":"text","dtype":"object","name":"unnamed_3","source_name":"Unnamed: 3"}],"description":"A list of ground ambulance providers and suppliers selected to submit data in Year 3 of the Medicare Ground Ambulance Data Collection System (GADCS). This file appears to be a duplicate of 'CMSAmbdata_Y3sample_post508.csv'.","enriched_columns":[{"attributed_to":["page_025.md","page_330.md"],"bq_type":"STRING","description":"Implicitly contains the National Provider Identifier (NPI) of the selected ground ambulance organization.","mode":"NULLABLE","name":"npi","notes":"This column contains descriptive text and should be processed to extract relevant information or used as file-level metadata.","source_name":"Medicare Ground Ambulance Data Collection"},{"attributed_to":["page_025.md","page_330.md"],"bq_type":"STRING","description":"The legal business name of the ground ambulance organization as registered in NPPES.","mode":"NULLABLE","name":"nppes_organization_name","notes":"Header 'NPPES Organization Name' is in the first data row.","source_name":"Unnamed: 1"},{"attributed_to":["page_025.md","page_330.md"],"bq_type":"STRING","description":"The state abbreviation for the organization's practice address as registered in NPPES.","mode":"NULLABLE","name":"nppes_practice_address_state","notes":"Header 'NPPES Practice Address State' is in the first data row.","source_name":"Unnamed: 2"},{"attributed_to":["page_025.md","page_330.md"],"bq_type":"STRING","description":"The state abbreviation for the organization's mailing address as registered in NPPES.","mode":"NULLABLE","name":"nppes_mailing_address_state","notes":"Header 'NPPES Mailing Address State' is in the first data row.","source_name":"Unnamed: 3"}],"full_table_id":"statmike-mlops-349915.data_onboarding_cms_gov_bronze.cmsambdata_y3sample_post","partition_by":null,"related_tables":{},"row_count":500,"source_file":"CMSAmbdata_Y3sample_post.xlsx","source_files":["CMSAmbdata_Y3sample_post.xlsx"],"source_path":"applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMSAmbdata_Y3sample_post.xlsx","source_paths":["applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMSAmbdata_Y3sample_post.xlsx"],"table_name":"cmsambdata_y3sample_post"} | 2026-03-31 14:55:49 |
| 8e390930-ad1d-436f-96e7-6a685d4f5670 | cmsambdata_y3sample_post508 | A list of ground ambulance providers and suppliers selected to submit data in Year 3 of the Medicare Ground Ambulance Data Collection System (GADCS). This file appears to be a duplicate of 'CMSAmbdata_Y3sample_post.xlsx'. | proposed | {"cluster_by":[],"columns":[{"category":"text","dtype":"object","name":"medicare_ground_ambulance_data_collection","source_name":"Medicare Ground Ambulance Data Collection"},{"category":"text","dtype":"object","name":"unnamed_1","source_name":"Unnamed: 1"},{"category":"text","dtype":"object","name":"unnamed_2","source_name":"Unnamed: 2"},{"category":"text","dtype":"object","name":"unnamed_3","source_name":"Unnamed: 3"}],"description":"A list of ground ambulance providers and suppliers selected to submit data in Year 3 of the Medicare Ground Ambulance Data Collection System (GADCS). This file appears to be a duplicate of 'CMSAmbdata_Y3sample_post.xlsx'.","enriched_columns":[{"attributed_to":["page_025.md","page_330.md"],"bq_type":"STRING","description":"Implicitly contains the National Provider Identifier (NPI) of the selected ground ambulance organization.","mode":"NULLABLE","name":"npi","notes":"This column contains descriptive text and should be processed to extract relevant information or used as file-level metadata.","source_name":"Medicare Ground Ambulance Data Collection"},{"attributed_to":["page_025.md","page_330.md"],"bq_type":"STRING","description":"The legal business name of the ground ambulance organization as registered in NPPES.","mode":"NULLABLE","name":"nppes_organization_name","notes":"Header 'NPPES Organization Name' is in the first data row.","source_name":"Unnamed: 1"},{"attributed_to":["page_025.md","page_330.md"],"bq_type":"STRING","description":"The state abbreviation for the organization's practice address as registered in NPPES.","mode":"NULLABLE","name":"nppes_practice_address_state","notes":"Header 'NPPES Practice Address State' is in the first data row.","source_name":"Unnamed: 2"},{"attributed_to":["page_025.md","page_330.md"],"bq_type":"STRING","description":"The state abbreviation for the organization's mailing address as registered in NPPES.","mode":"NULLABLE","name":"nppes_mailing_address_state","notes":"Header 'NPPES Mailing Address State' is in the first data row.","source_name":"Unnamed: 3"}],"full_table_id":"statmike-mlops-349915.data_onboarding_cms_gov_bronze.cmsambdata_y3sample_post508","partition_by":null,"related_tables":{},"row_count":500,"source_file":"CMSAmbdata_Y3sample_post508.csv","source_files":["CMSAmbdata_Y3sample_post508.csv"],"source_path":"applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMSAmbdata_Y3sample_post508.csv","source_paths":["applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMSAmbdata_Y3sample_post508.csv"],"table_name":"cmsambdata_y3sample_post508"} | 2026-03-31 14:55:49 |
| 4a981078-cd47-4681-90fe-aae828785d34 | cmsambdata_y4sample_post | A list of ground ambulance providers and suppliers selected to submit data in Year 4 of the Medicare Ground Ambulance Data Collection System (GADCS). This file appears to be a duplicate of 'CMSAmbdata_Y4sample_post508.csv'. | proposed | {"cluster_by":[],"columns":[{"category":"text","dtype":"object","name":"medicare_ground_ambulance_data_collection","source_name":"Medicare Ground Ambulance Data Collection"},{"category":"text","dtype":"object","name":"unnamed_1","source_name":"Unnamed: 1"},{"category":"text","dtype":"object","name":"unnamed_2","source_name":"Unnamed: 2"},{"category":"text","dtype":"object","name":"unnamed_3","source_name":"Unnamed: 3"}],"description":"A list of ground ambulance providers and suppliers selected to submit data in Year 4 of the Medicare Ground Ambulance Data Collection System (GADCS). This file appears to be a duplicate of 'CMSAmbdata_Y4sample_post508.csv'.","enriched_columns":[{"attributed_to":["page_025.md","page_330.md"],"bq_type":"STRING","description":"Implicitly contains the National Provider Identifier (NPI) of the selected ground ambulance organization.","mode":"NULLABLE","name":"npi","notes":"This column contains descriptive text and should be processed to extract relevant information or used as file-level metadata.","source_name":"Medicare Ground Ambulance Data Collection"},{"attributed_to":["page_025.md","page_330.md"],"bq_type":"STRING","description":"The legal business name of the ground ambulance organization as registered in NPPES.","mode":"NULLABLE","name":"nppes_organization_name","notes":"Header 'NPPES Organization Name' is in the first data row.","source_name":"Unnamed: 1"},{"attributed_to":["page_025.md","page_330.md"],"bq_type":"STRING","description":"The state abbreviation for the organization's practice address as registered in NPPES.","mode":"NULLABLE","name":"nppes_practice_address_state","notes":"Header 'NPPES Practice Address State' is in the first data row.","source_name":"Unnamed: 2"},{"attributed_to":["page_025.md","page_330.md"],"bq_type":"STRING","description":"The state abbreviation for the organization's mailing address as registered in NPPES.","mode":"NULLABLE","name":"nppes_mailing_address_state","notes":"Header 'NPPES Mailing Address State' is in the first data row.","source_name":"Unnamed: 3"}],"full_table_id":"statmike-mlops-349915.data_onboarding_cms_gov_bronze.cmsambdata_y4sample_post","partition_by":null,"related_tables":{},"row_count":500,"source_file":"CMSAmbdata_Y4sample_post.xlsx","source_files":["CMSAmbdata_Y4sample_post.xlsx"],"source_path":"applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMSAmbdata_Y4sample_post.xlsx","source_paths":["applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMSAmbdata_Y4sample_post.xlsx"],"table_name":"cmsambdata_y4sample_post"} | 2026-03-31 14:55:49 |
| 934ec4f4-811d-4aca-a2f4-353b7728d4ab | cmsambdata_y4sample_post508 | A list of ground ambulance providers and suppliers selected to submit data in Year 4 of the Medicare Ground Ambulance Data Collection System (GADCS). This file appears to be a duplicate of 'CMSAmbdata_Y4sample_post.xlsx'. | proposed | {"cluster_by":[],"columns":[{"category":"text","dtype":"object","name":"medicare_ground_ambulance_data_collection","source_name":"Medicare Ground Ambulance Data Collection"},{"category":"text","dtype":"object","name":"unnamed_1","source_name":"Unnamed: 1"},{"category":"text","dtype":"object","name":"unnamed_2","source_name":"Unnamed: 2"},{"category":"text","dtype":"object","name":"unnamed_3","source_name":"Unnamed: 3"}],"description":"A list of ground ambulance providers and suppliers selected to submit data in Year 4 of the Medicare Ground Ambulance Data Collection System (GADCS). This file appears to be a duplicate of 'CMSAmbdata_Y4sample_post.xlsx'.","enriched_columns":[{"attributed_to":["page_025.md","page_330.md"],"bq_type":"STRING","description":"Implicitly contains the National Provider Identifier (NPI) of the selected ground ambulance organization.","mode":"NULLABLE","name":"npi","notes":"This column contains descriptive text and should be processed to extract relevant information or used as file-level metadata.","source_name":"Medicare Ground Ambulance Data Collection"},{"attributed_to":["page_025.md","page_330.md"],"bq_type":"STRING","description":"The legal business name of the ground ambulance organization as registered in NPPES.","mode":"NULLABLE","name":"nppes_organization_name","notes":"Header 'NPPES Organization Name' is in the first data row.","source_name":"Unnamed: 1"},{"attributed_to":["page_025.md","page_330.md"],"bq_type":"STRING","description":"The state abbreviation for the organization's practice address as registered in NPPES.","mode":"NULLABLE","name":"nppes_practice_address_state","notes":"Header 'NPPES Practice Address State' is in the first data row.","source_name":"Unnamed: 2"},{"attributed_to":["page_025.md","page_330.md"],"bq_type":"STRING","description":"The state abbreviation for the organization's mailing address as registered in NPPES.","mode":"NULLABLE","name":"nppes_mailing_address_state","notes":"Header 'NPPES Mailing Address State' is in the first data row.","source_name":"Unnamed: 3"}],"full_table_id":"statmike-mlops-349915.data_onboarding_cms_gov_bronze.cmsambdata_y4sample_post508","partition_by":null,"related_tables":{},"row_count":500,"source_file":"CMSAmbdata_Y4sample_post508.csv","source_files":["CMSAmbdata_Y4sample_post508.csv"],"source_path":"applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMSAmbdata_Y4sample_post508.csv","source_paths":["applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/CMSAmbdata_Y4sample_post508.csv"],"table_name":"cmsambdata_y4sample_post508"} | 2026-03-31 14:55:49 |
| 2f2f3b99-d216-4967-ad2d-a6f2c471abf8 | ipsf_full | Provider Specific File (PSF) for Inpatient Prospective Payment System (IPPS) facilities, containing provider-specific data used for Medicare payment calculations. This is a snapshot from January 1, 2025. It includes financial rates, geographic and provider-specific adjustments, and provider characteristics. | proposed | {"cluster_by":["provider_type_code","provider_ccn","npi","waiver_indicator"],"columns":[{"category":"categorical","dtype":"string","name":"provider_ccn","source_name":"providerCcn"},{"category":"datetime_candidate","dtype":"object","name":"effective_date","source_name":"effectiveDate"},{"category":"datetime_candidate","dtype":"object","name":"fiscal_year_begin_date","source_name":"fiscalYearBeginDate"},{"category":"datetime_candidate","dtype":"object","name":"export_date","source_name":"exportDate"},{"category":"datetime_candidate","dtype":"object","name":"termination_date","source_name":"terminationDate"},{"category":"categorical","dtype":"string","name":"waiver_indicator","source_name":"waiverIndicator"},{"category":"categorical","dtype":"string","name":"intermediary_number","source_name":"intermediaryNumber"},{"category":"categorical","dtype":"string","name":"provider_type","source_name":"providerType"},{"category":"categorical","dtype":"string","name":"census_division","source_name":"censusDivision"},{"category":"categorical","dtype":"string","name":"msa_actual_geographic_location","source_name":"msaActualGeographicLocation"},{"category":"categorical","dtype":"string","name":"msa_wage_index_location","source_name":"msaWageIndexLocation"},{"category":"categorical","dtype":"string","name":"msa_standardized_amount_location","source_name":"msaStandardizedAmountLocation"},{"category":"datetime_candidate","dtype":"string","name":"sole_community_or_medicare_dependent_hospital_base_year","source_name":"soleCommunityOrMedicareDependentHospitalBaseYear"},{"category":"datetime_candidate","dtype":"string","name":"change_code_for_lugar_reclassification","source_name":"changeCodeForLugarReclassification"},{"category":"datetime_candidate","dtype":"string","name":"temporary_relief_indicator","source_name":"temporaryReliefIndicator"},{"category":"datetime_candidate","dtype":"string","name":"federal_pps_blend","source_name":"federalPpsBlend"},{"category":"categorical","dtype":"string","name":"state_code","source_name":"stateCode"},{"category":"Float64","dtype":"Float64","name":"case_mix_adjusted_cost_per_discharge_pps_facility_specific_rate","source_name":"caseMixAdjustedCostPerDischarge_PpsFacilitySpecificRate"},{"category":"Float64","dtype":"Float64","name":"cost_of_living_adjustment","source_name":"costOfLivingAdjustment"},{"category":"Float64","dtype":"Float64","name":"interns_to_beds_ratio","source_name":"internsToBedsRatio"},{"category":"Int64","dtype":"Int64","name":"bed_size","source_name":"bedSize"},{"category":"Float64","dtype":"Float64","name":"operating_cost_to_charge_ratio","source_name":"operatingCostToChargeRatio"},{"category":"Float64","dtype":"Float64","name":"case_mix_index","source_name":"caseMixIndex"},{"category":"Float64","dtype":"Float64","name":"supplemental_security_income_ratio","source_name":"supplementalSecurityIncomeRatio"},{"category":"Float64","dtype":"Float64","name":"medicaid_ratio","source_name":"medicaidRatio"},{"category":"Float64","dtype":"Float64","name":"special_provider_update_factor","source_name":"specialProviderUpdateFactor"},{"category":"Float64","dtype":"Float64","name":"operating_dsh","source_name":"operatingDsh"},{"category":"datetime_candidate","dtype":"object","name":"fiscal_year_end_date","source_name":"fiscalYearEndDate"},{"category":"categorical","dtype":"string","name":"special_payment_indicator","source_name":"specialPaymentIndicator"},{"category":"categorical","dtype":"string","name":"hospital_quality_indicator","source_name":"hospitalQualityIndicator"},{"category":"categorical","dtype":"string","name":"cbsa_actual_geographic_location","source_name":"cbsaActualGeographicLocation"},{"category":"categorical","dtype":"string","name":"cbsa_wage_index_location","source_name":"cbsaWageIndexLocation"},{"category":"datetime_candidate","dtype":"string","name":"cbsa_standardized_amount_location","source_name":"cbsaStandardizedAmountLocation"},{"category":"Float64","dtype":"Float64","name":"special_wage_index","source_name":"specialWageIndex"},{"category":"Float64","dtype":"Float64","name":"pass_through_amount_for_capital","source_name":"passThroughAmountForCapital"},{"category":"Float64","dtype":"Float64","name":"pass_through_amount_for_direct_medical_education","source_name":"passThroughAmountForDirectMedicalEducation"},{"category":"Float64","dtype":"Float64","name":"pass_through_amount_for_organ_acquisition","source_name":"passThroughAmountForOrganAcquisition"},{"category":"Float64","dtype":"Float64","name":"pass_through_total_amount","source_name":"passThroughTotalAmount"},{"category":"categorical","dtype":"string","name":"capital_pps_payment_code","source_name":"capitalPpsPaymentCode"},{"category":"Float64","dtype":"Float64","name":"hospital_specific_capital_rate","source_name":"hospitalSpecificCapitalRate"},{"category":"Float64","dtype":"Float64","name":"old_capital_hold_harmless_rate","source_name":"oldCapitalHoldHarmlessRate"},{"category":"Float64","dtype":"Float64","name":"new_capital_hold_harmless_rate","source_name":"newCapitalHoldHarmlessRate"},{"category":"Float64","dtype":"Float64","name":"capital_cost_to_charge_ratio","source_name":"capitalCostToChargeRatio"},{"category":"datetime_candidate","dtype":"string","name":"new_hospital","source_name":"newHospital"},{"category":"Float64","dtype":"Float64","name":"capital_indirect_medical_education_ratio","source_name":"capitalIndirectMedicalEducationRatio"},{"category":"Float64","dtype":"Float64","name":"capital_exception_payment_rate","source_name":"capitalExceptionPaymentRate"},{"category":"categorical","dtype":"string","name":"vbp_participant_indicator","source_name":"vbpParticipantIndicator"},{"category":"Float64","dtype":"Float64","name":"vbp_adjustment","source_name":"vbpAdjustment"},{"category":"Int64","dtype":"Int64","name":"hrr_participant_indicator","source_name":"hrrParticipantIndicator"},{"category":"Float64","dtype":"Float64","name":"hrr_adjustment","source_name":"hrrAdjustment"},{"category":"Float64","dtype":"Float64","name":"bundle_model1_discount","source_name":"bundleModel1Discount"},{"category":"categorical","dtype":"string","name":"hac_reduction_participant_indicator","source_name":"hacReductionParticipantIndicator"},{"category":"Float64","dtype":"Float64","name":"uncompensated_care_amount","source_name":"uncompensatedCareAmount"},{"category":"datetime_candidate","dtype":"string","name":"ehr_reduction_indicator","source_name":"ehrReductionIndicator"},{"category":"Float64","dtype":"Float64","name":"low_volume_adjustment_factor","source_name":"lowVolumeAdjustmentFactor"},{"category":"datetime_candidate","dtype":"string","name":"county_code","source_name":"countyCode"},{"category":"Float64","dtype":"Float64","name":"medicare_performance_adjustment","source_name":"medicarePerformanceAdjustment"},{"category":"datetime_candidate","dtype":"string","name":"ltch_dpp_indicator","source_name":"ltchDppIndicator"},{"category":"Float64","dtype":"Float64","name":"supplemental_wage_index","source_name":"supplementalWageIndex"},{"category":"datetime_candidate","dtype":"string","name":"supplemental_wage_index_indicator","source_name":"supplementalWageIndexIndicator"},{"category":"categorical","dtype":"string","name":"change_code_wage_index_reclassification","source_name":"changeCodeWageIndexReclassification"},{"category":"categorical","dtype":"string","name":"national_provider_identifier","source_name":"nationalProviderIdentifier"},{"category":"Float64","dtype":"Float64","name":"pass_through_amount_for_allogenic_stem_cell_acquisition","source_name":"passThroughAmountForAllogenicStemCellAcquisition"},{"category":"datetime_candidate","dtype":"string","name":"pps_blend_year_indicator","source_name":"ppsBlendYearIndicator"},{"category":"datetime_candidate","dtype":"object","name":"last_updated","source_name":"lastUpdated"},{"category":"Float64","dtype":"Float64","name":"pass_through_amount_for_direct_graduate_medical_education","source_name":"passThroughAmountForDirectMedicalEducation"},{"category":"Float64","dtype":"Float64","name":"pass_through_amount_for_kidney_acquisition","source_name":"passThroughAmountForKidneyAcquisition"},{"category":"Float64","dtype":"Float64","name":"pass_through_amount_for_supply_chain","source_name":"passThroughAmountForSupplyChain"}],"description":"Provider Specific File (PSF) for Inpatient Prospective Payment System (IPPS) facilities, containing provider-specific data used for Medicare payment calculations. This is a snapshot from January 1, 2025. It includes financial rates, geographic and provider-specific adjustments, and provider characteristics.","enriched_columns":[{"attributed_to":["page_000.md","page_301.md"],"bq_type":"STRING","description":"The 6-digit CMS Certification Number (CCN), a unique identifier for the Medicare provider.","mode":"NULLABLE","name":"provider_ccn","notes":"This is a primary key for joining with other provider-level data.","source_name":"providerCcn"},{"attributed_to":["page_000.md"],"bq_type":"DATE","description":"The date on which the specific rate, factor, or data element in this record became effective.","mode":"NULLABLE","name":"effective_date","notes":"Data is stored as an object/string and needs to be parsed to a DATE type.","source_name":"effectiveDate"},{"attributed_to":["page_000.md"],"bq_type":"DATE","description":"The start date of the provider's fiscal year.","mode":"NULLABLE","name":"fiscal_year_begin_date","notes":"Data is stored as an object/string and needs to be parsed to a DATE type.","source_name":"fiscalYearBeginDate"},{"attributed_to":["page_000.md"],"bq_type":"DATE","description":"The date the data was exported from the source system, indicating the snapshot date of the file.","mode":"NULLABLE","name":"export_date","notes":"This value is the same for all rows in the file and should ideally be stored as table-level metadata or in a separate column added during ingestion.","source_name":"exportDate"},{"attributed_to":["page_107.md"],"bq_type":"DATE","description":"The date the provider's participation in the Medicare program was terminated, if applicable.","mode":"NULLABLE","name":"termination_date","notes":"Very high null percentage (99.2%) is expected as most providers are active. Data is stored as an object/string.","source_name":"terminationDate"},{"bq_type":"STRING","description":"An indicator for any special waivers the provider may have.","mode":"NULLABLE","name":"waiver_indicator","notes":null,"source_name":"waiverIndicator"},{"attributed_to":["page_315.md"],"bq_type":"STRING","description":"Identifier for the Medicare Administrative Contractor (MAC) or Fiscal Intermediary responsible for processing the provider's claims.","mode":"NULLABLE","name":"intermediary_number","notes":"This can be used to link to MAC-specific information.","source_name":"intermediaryNumber"},{"attributed_to":["page_000.md","page_102.md"],"bq_type":"STRING","description":"A code indicating the type of provider (e.g., '00' for hospital).","mode":"NULLABLE","name":"provider_type_code","notes":"The meaning of these codes would need to be looked up in a separate data dictionary. For this file group, provider type can be inferred from the filename.","source_name":"providerType"},{"bq_type":"STRING","description":"A code representing the U.S. Census Division where the provider is located.","mode":"NULLABLE","name":"census_division_code","notes":null,"source_name":"censusDivision"},{"bq_type":"STRING","description":"A code for the Metropolitan Statistical Area (MSA) of the provider's actual geographic location.","mode":"NULLABLE","name":"msa_actual_geographic_location_code","notes":null,"source_name":"msaActualGeographicLocation"},{"attributed_to":["page_302.md"],"bq_type":"STRING","description":"A code for the Metropolitan Statistical Area (MSA) used for the provider's wage index calculation, which may differ from the actual location due to reclassification.","mode":"NULLABLE","name":"msa_wage_index_location_code","notes":null,"source_name":"msaWageIndexLocation"},{"bq_type":"STRING","description":"","mode":"NULLABLE","name":"msa_standardized_amount_location","notes":"","source_name":"msaStandardizedAmountLocation"},{"bq_type":"TIMESTAMP","description":"","mode":"NULLABLE","name":"sole_community_or_medicare_dependent_hospital_base_year","notes":"","source_name":"soleCommunityOrMedicareDependentHospitalBaseYear"},{"bq_type":"TIMESTAMP","description":"","mode":"NULLABLE","name":"change_code_for_lugar_reclassification","notes":"","source_name":"changeCodeForLugarReclassification"},{"bq_type":"TIMESTAMP","description":"","mode":"NULLABLE","name":"temporary_relief_indicator","notes":"","source_name":"temporaryReliefIndicator"},{"bq_type":"TIMESTAMP","description":"","mode":"NULLABLE","name":"federal_pps_blend","notes":"","source_name":"federalPpsBlend"},{"bq_type":"STRING","description":"","mode":"NULLABLE","name":"state_code","notes":"","source_name":"stateCode"},{"bq_type":"FLOAT64","description":"","mode":"NULLABLE","name":"case_mix_adjusted_cost_per_discharge_pps_facility_specific_rate","notes":"","source_name":"caseMixAdjustedCostPerDischarge_PpsFacilitySpecificRate"},{"bq_type":"FLOAT64","description":"","mode":"NULLABLE","name":"cost_of_living_adjustment","notes":"","source_name":"costOfLivingAdjustment"},{"bq_type":"FLOAT64","description":"","mode":"NULLABLE","name":"interns_to_beds_ratio","notes":"","source_name":"internsToBedsRatio"},{"bq_type":"INT64","description":"","mode":"NULLABLE","name":"bed_size","notes":"","source_name":"bedSize"},{"bq_type":"FLOAT64","description":"","mode":"NULLABLE","name":"operating_cost_to_charge_ratio","notes":"","source_name":"operatingCostToChargeRatio"},{"bq_type":"FLOAT64","description":"","mode":"NULLABLE","name":"case_mix_index","notes":"","source_name":"caseMixIndex"},{"bq_type":"FLOAT64","description":"","mode":"NULLABLE","name":"supplemental_security_income_ratio","notes":"","source_name":"supplementalSecurityIncomeRatio"},{"bq_type":"FLOAT64","description":"","mode":"NULLABLE","name":"medicaid_ratio","notes":"","source_name":"medicaidRatio"},{"bq_type":"FLOAT64","description":"","mode":"NULLABLE","name":"special_provider_update_factor","notes":"","source_name":"specialProviderUpdateFactor"},{"bq_type":"FLOAT64","description":"","mode":"NULLABLE","name":"operating_dsh","notes":"","source_name":"operatingDsh"},{"bq_type":"TIMESTAMP","description":"","mode":"NULLABLE","name":"fiscal_year_end_date","notes":"","source_name":"fiscalYearEndDate"},{"bq_type":"STRING","description":"","mode":"NULLABLE","name":"special_payment_indicator","notes":"","source_name":"specialPaymentIndicator"},{"bq_type":"STRING","description":"","mode":"NULLABLE","name":"hospital_quality_indicator","notes":"","source_name":"hospitalQualityIndicator"},{"bq_type":"STRING","description":"","mode":"NULLABLE","name":"cbsa_actual_geographic_location","notes":"","source_name":"cbsaActualGeographicLocation"},{"bq_type":"STRING","description":"","mode":"NULLABLE","name":"cbsa_wage_index_location","notes":"","source_name":"cbsaWageIndexLocation"},{"bq_type":"TIMESTAMP","description":"","mode":"NULLABLE","name":"cbsa_standardized_amount_location","notes":"","source_name":"cbsaStandardizedAmountLocation"},{"bq_type":"FLOAT64","description":"","mode":"NULLABLE","name":"special_wage_index","notes":"","source_name":"specialWageIndex"},{"bq_type":"FLOAT64","description":"","mode":"NULLABLE","name":"pass_through_amount_for_capital","notes":"","source_name":"passThroughAmountForCapital"},{"bq_type":"FLOAT64","description":"","mode":"NULLABLE","name":"pass_through_amount_for_direct_medical_education","notes":"","source_name":"passThroughAmountForDirectMedicalEducation"},{"bq_type":"FLOAT64","description":"","mode":"NULLABLE","name":"pass_through_amount_for_organ_acquisition","notes":"","source_name":"passThroughAmountForOrganAcquisition"},{"bq_type":"FLOAT64","description":"","mode":"NULLABLE","name":"pass_through_total_amount","notes":"","source_name":"passThroughTotalAmount"},{"bq_type":"STRING","description":"","mode":"NULLABLE","name":"capital_pps_payment_code","notes":"","source_name":"capitalPpsPaymentCode"},{"bq_type":"FLOAT64","description":"","mode":"NULLABLE","name":"hospital_specific_capital_rate","notes":"","source_name":"hospitalSpecificCapitalRate"},{"bq_type":"FLOAT64","description":"","mode":"NULLABLE","name":"old_capital_hold_harmless_rate","notes":"","source_name":"oldCapitalHoldHarmlessRate"},{"bq_type":"FLOAT64","description":"","mode":"NULLABLE","name":"new_capital_hold_harmless_rate","notes":"","source_name":"newCapitalHoldHarmlessRate"},{"bq_type":"FLOAT64","description":"","mode":"NULLABLE","name":"capital_cost_to_charge_ratio","notes":"","source_name":"capitalCostToChargeRatio"},{"bq_type":"TIMESTAMP","description":"","mode":"NULLABLE","name":"new_hospital","notes":"","source_name":"newHospital"},{"bq_type":"FLOAT64","description":"","mode":"NULLABLE","name":"capital_indirect_medical_education_ratio","notes":"","source_name":"capitalIndirectMedicalEducationRatio"},{"bq_type":"FLOAT64","description":"","mode":"NULLABLE","name":"capital_exception_payment_rate","notes":"","source_name":"capitalExceptionPaymentRate"},{"bq_type":"STRING","description":"","mode":"NULLABLE","name":"vbp_participant_indicator","notes":"","source_name":"vbpParticipantIndicator"},{"bq_type":"FLOAT64","description":"","mode":"NULLABLE","name":"vbp_adjustment","notes":"","source_name":"vbpAdjustment"},{"bq_type":"INT64","description":"","mode":"NULLABLE","name":"hrr_participant_indicator","notes":"","source_name":"hrrParticipantIndicator"},{"bq_type":"FLOAT64","description":"","mode":"NULLABLE","name":"hrr_adjustment","notes":"","source_name":"hrrAdjustment"},{"bq_type":"FLOAT64","description":"","mode":"NULLABLE","name":"bundle_model1_discount","notes":"","source_name":"bundleModel1Discount"},{"bq_type":"STRING","description":"","mode":"NULLABLE","name":"hac_reduction_participant_indicator","notes":"","source_name":"hacReductionParticipantIndicator"},{"bq_type":"FLOAT64","description":"","mode":"NULLABLE","name":"uncompensated_care_amount","notes":"","source_name":"uncompensatedCareAmount"},{"bq_type":"TIMESTAMP","description":"","mode":"NULLABLE","name":"ehr_reduction_indicator","notes":"","source_name":"ehrReductionIndicator"},{"bq_type":"FLOAT64","description":"","mode":"NULLABLE","name":"low_volume_adjustment_factor","notes":"","source_name":"lowVolumeAdjustmentFactor"},{"bq_type":"TIMESTAMP","description":"","mode":"NULLABLE","name":"county_code","notes":"","source_name":"countyCode"},{"bq_type":"FLOAT64","description":"","mode":"NULLABLE","name":"medicare_performance_adjustment","notes":"","source_name":"medicarePerformanceAdjustment"},{"bq_type":"TIMESTAMP","description":"","mode":"NULLABLE","name":"ltch_dpp_indicator","notes":"","source_name":"ltchDppIndicator"},{"bq_type":"FLOAT64","description":"","mode":"NULLABLE","name":"supplemental_wage_index","notes":"","source_name":"supplementalWageIndex"},{"bq_type":"TIMESTAMP","description":"","mode":"NULLABLE","name":"supplemental_wage_index_indicator","notes":"","source_name":"supplementalWageIndexIndicator"},{"bq_type":"STRING","description":"","mode":"NULLABLE","name":"change_code_wage_index_reclassification","notes":"","source_name":"changeCodeWageIndexReclassification"},{"attributed_to":["page_007.md","page_330.md"],"bq_type":"STRING","description":"The National Provider Identifier (NPI), a unique 10-digit identification number for the health care provider.","mode":"NULLABLE","name":"npi","notes":"This is a key identifier for joining with other datasets. Empty strings likely represent missing NPIs and should be treated as NULLs.","source_name":"nationalProviderIdentifier"},{"bq_type":"FLOAT64","description":"","mode":"NULLABLE","name":"pass_through_amount_for_allogenic_stem_cell_acquisition","notes":"","source_name":"passThroughAmountForAllogenicStemCellAcquisition"},{"bq_type":"TIMESTAMP","description":"","mode":"NULLABLE","name":"pps_blend_year_indicator","notes":"","source_name":"ppsBlendYearIndicator"},{"bq_type":"DATE","description":"The date the record was last updated in the source system.","mode":"NULLABLE","name":"last_updated_date","notes":"Data is stored as an object/string and needs to be parsed to a DATE type.","source_name":"lastUpdated"},{"bq_type":"FLOAT64","description":"","mode":"NULLABLE","name":"pass_through_amount_for_direct_graduate_medical_education","notes":"","source_name":"passThroughAmountForDirectMedicalEducation"},{"bq_type":"FLOAT64","description":"","mode":"NULLABLE","name":"pass_through_amount_for_kidney_acquisition","notes":"","source_name":"passThroughAmountForKidneyAcquisition"},{"bq_type":"FLOAT64","description":"","mode":"NULLABLE","name":"pass_through_amount_for_supply_chain","notes":"","source_name":"passThroughAmountForSupplyChain"}],"full_table_id":"statmike-mlops-349915.data_onboarding_cms_gov_bronze.ipsf_full","partition_by":{"column":"effective_date","type":"MONTH"},"related_tables":{"contains":["ipsf_hha","ipsf_hos","ipsf_inp","ipsf_ipf","ipsf_irf","ipsf_ltch","ipsf_snf"]},"row_count":4895679,"source_file":"IPSF_FULL_2025-01-01.parquet","source_files":["IPSF_FULL_2025-01-01.parquet","IPSF_FULL_2025-04-01.parquet","IPSF_Full_2025-07-01.parquet","IPSF_Full_2025-10-01.parquet","IPSF_Full_2026-01-02.parquet"],"source_path":"applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_FULL_2025-01-01.parquet","source_paths":["applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_FULL_2025-01-01.parquet","applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_FULL_2025-04-01.parquet","applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_Full_2025-07-01.parquet","applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_Full_2025-10-01.parquet","applied-ml/ai-agents/data-onboarding/7a9bbbaf-2a6b-5237-99c5-fc2e59d4d9ce/files/IPSF_Full_2026-01-02.parquet"],"table_name":"ipsf_full"} | 2026-03-31 14:55:49 |

### Key Schema Decisions

#### 1. Inpatient Prospective Payment System (IPPS) Provider Data
For the `ipsf_full` table, which contains provider-specific files for Medicare payment calculations:
*   **Partitioning:** The table is partitioned by **month** based on the `effective_date` to optimize time-based queries.
*   **Clustering:** It is clustered by `provider_type_code`, `provider_ccn`, `npi`, and `waiver_indicator` to improve the performance of searches for specific provider identifiers and characteristics.
*   **Enrichment:** Data was enriched with specific column mappings for unique identifiers like the **National Provider Identifier (NPI)** and **CMS Certification Number (CCN)**, which are critical for joining this dataset with other healthcare tables.

#### 2. Ground Ambulance Data Collection System (GADCS) Tables
Multiple tables (e.g., `_508_compliant_version_of_sampled_npis`, `cmsambdata_y3sample_post`) were created to track ambulance providers selected for data submission across different years (Year 1 through Year 4):
*   **Purpose:** These tables identify ground ambulance providers and suppliers from the National Plan and Provider Enumeration System (NPPES).
*   **Data Extraction:** The schema designs focused on extracting and mapping the **NPI**, legal organization names, and state-level address information (practice and mailing) to provide a clean list of participants for the Medicare Ground Ambulance Data Collection System.
*   **Duplicate Management:** The pipeline identified several files as duplicates of earlier versions (e.g., `cmsambdata_y2sample_post` being a duplicate of the 508-compliant version), allowing for better data governance.

### Insights
*   **Identifier-Centric Design:** Significant emphasis was placed on ensuring the `npi` and `provider_ccn` columns were correctly mapped and used for clustering, highlighting their importance as primary keys for the entire data onboarding ecosystem.
*   **Temporal Tracking:** The use of partitioning on `effective_date` and the ingestion of multiple snapshot files (like the quarterly IPPS files) indicate a design that prioritizes tracking changes in provider status and financial rates over time.
*   **Data Quality:** Identifying duplicates during the onboarding phase helps prevent data redundancy in the bronze layer, ensuring that downstream analysis remains efficient.

<a id="data-engineer-q5"></a>
#### Q5: How many tables were created and what are their row counts?

**Flow:** `agent_chat` → `agent_engineer` (meta_chat)

| Step | Agent | Action | Time |
|------|-------|--------|------|
| 1 | agent_chat | `transfer_to_agent` | 2.1s |
| 2 | agent_engineer | `meta_chat` | 4.2s |
| | | **Total** | **90.6s** |

**Answer:**

A total of **112 tables** were created during the data onboarding process across two main bronze datasets. The row counts for these tables were recorded in the processing logs during the pipeline's execution.

### Created Tables by Dataset
The tables are distributed between the Cboe and CMS datasets as follows:

                                                       dataset  table_count
statmike-mlops-349915.data_onboarding_datashop_cboe_com_bronze         58.0
          statmike-mlops-349915.data_onboarding_cms_gov_bronze         54.0

### Top Tables by Row Count
The row counts were extracted from the processing logs. Below are the top tables from each source, sorted by row count:

**CMS Bronze Dataset (Total 54 Tables):**
- `ipsf_full`: 4,895,679 rows
- `ipsf_inp`: 1,966,882 rows
- `ipsf_snf`: 1,681,117 rows
- `opsf`: 1,418,399 rows
- `opsf_full`: 1,406,663 rows
- `ipsf_hha`: 1,077,752 rows
- `ipsf_ipf`: 480,220 rows
- `ipsf_irf`: 448,365 rows
- `opsf_lro`: 266,721 rows
- `ipsf_hos`: 240,051 rows

**Cboe Bronze Dataset (Total 58 Tables):**
- `eod_theos_cboe_prop_20251215_1600`: 99,047 rows
- `cboe_cfe_trades_rth`: 48,599 rows
- `cboe_equity_short_sales_edgx`: 36,206 rows
- `underlying_options_eodcalcs_2023_08_25_cgi_or_historical`: 32,672 rows
- `underlying_options_eodcalcs_2023_08_25_no_cgi_subscription`: 32,672 rows
- `ftref_fit_parameters`: 26,772 rows
- `ftref_early_exercise_strike_by_option_class`: 26,676 rows
- `ftref_traded_vega_ratio`: 26,518 rows
- `cboe_equity_svr_edgx`: 9,222 rows
- `cboe_equity_svr_bzx`: 8,588 rows

### Insights
- **Data Skew**: The CMS dataset contains significantly larger tables, with `ipsf_full` exceeding 4.8 million rows, whereas the largest Cboe table is around 99,000 rows.
- **Categorization**: Most large tables in the CMS dataset are related to "IPSF" (Inpatient) and "OPSF" (Outpatient) files, while Cboe's largest data involves theoretical end-of-day calculations and futures trades.
- **Metadata Accessibility**: While table row counts are not stored in the primary `table_lineage` metadata, they are systematically recorded in the `processing_log` during the validation and execution phases.

<a id="data-engineer-q6"></a>
#### Q6: Were any columns coerced or dropped during loading?

**Flow:** `agent_chat` → `agent_engineer` (meta_chat)

| Step | Agent | Action | Time |
|------|-------|--------|------|
| 1 | agent_chat | `transfer_to_agent` | 2.1s |
| 2 | agent_engineer | `meta_chat` | 4.6s |
| | | **Total** | **46.6s** |

**Answer:**

Based on the processing logs:

**No columns were dropped** during the loading process.

However, several columns were **coerced to strings** to resolve data type conversion errors. This happened because the pipeline encountered issues converting "object" type Pandas columns to appropriate pyarrow data types (such as Array, ListArray, or StructArray).

Here are some examples of tables and the columns that were coerced to strings:

*   **vehicles_main_templates_and_instructions_v2**: `Unnamed: 5`, `Unnamed: 7`, `Unnamed: 8`, `Unnamed: 9`, `Unnamed: 10`
*   **msn_message_character_limits**: `page`
*   **icd_10_cm_conversion_table_fy2025_effective_10_01_2024_final**: `nppes_organization_name`
*   **icd_10_cm_conversion_table_fy2026_april_1_2026**: `nppes_organization_name`
*   **cmsambdata_y4sample_post**: `npi`
*   **cmsambdata_y3sample_post**: `npi`
*   **_11_20_25_complete_msn_message_list**: `message_number`, `character_count_english`, `character_count_spanish`, `message_implementation_date`, `message_expiration_date`, `associated_cr_tdl`
*   **livevol_trade_condition_ids**: `CTA Code`, `UTP Code`

<a id="data-engineer-q7"></a>
#### Q7: What context documents were found and how were they used?

**Flow:** `agent_chat` → `agent_engineer` (meta_chat)

| Step | Agent | Action | Time |
|------|-------|--------|------|
| 1 | agent_chat | `transfer_to_agent` | 3.5s |
| 2 | agent_engineer | `meta_chat` | 5.9s |
| | | **Total** | **28.2s** |

**Answer:**

Analyzing context. I've retrieved context for 6 tables.

I'm now formulating a query to extract context documents from `source_manifest`, focusing on those classified as 'context'. Then, I plan to cross-reference these with the `data_catalog`, specifically its `context_documents` field, and the descriptive content for each dataset. Finally, I intend to integrate the findings with relevant schema decisions, scrutinizing their reasoning.

<a id="data-engineer-q8"></a>
#### Q8: Show the web provenance — what pages were crawled?

**Flow:** `agent_chat` → `agent_engineer` (meta_chat)

| Step | Agent | Action | Time |
|------|-------|--------|------|
| 1 | agent_chat | `transfer_to_agent` | 2.3s |
| 2 | agent_engineer | `meta_chat` | 4.9s |
| | | **Total** | **30.3s** |

**Answer:**

The web provenance shows that a total of **625 pages and files** were crawled across two primary domains: **cms.gov** and **datashop.cboe.com**. The crawled content includes informational web pages, technical specifications (PDFs), data archives (ZIPs), and reference files (XLSX, CSV).

The most recent crawls were from `cms.gov` on 2026-03-31 and `datashop.cboe.com` on 2026-03-26.

Here are some of the most recently crawled URLs:

| url                                                                                                                                                                                        | parent_url                                                                                                          | page_title | status_code | crawled_at          |
|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:--------------------------------------------------------------------------------------------------------------------|:-----------|:------------|:--------------------|
| https://www.cms.gov/files/zip/2025-icd-10-pcs-conversion-table.zip                                                                                                                     | https://www.cms.gov/medicare/coding-billing/icd-10-codes                                                            | None       | nan         | 2026-03-31 13:39:34 |
| https://www.cms.gov/files/zip/2025-version-update-summary.zip                                                                                                                          | https://www.cms.gov/medicare/coding-billing/icd-10-codes                                                            | None       | nan         | 2026-03-31 13:39:34 |
| https://www.cms.gov/marketplace/resources/letters                                                                                                                                      | https://www.cms.gov/medicare/payment/prospective-payment-systems/provider-specific-data-public-use-sas-format       | None       | 200.0       | 2026-03-31 13:39:34 |
| https://www.cms.gov/marketplace-private-insurance/resources/marketplace-coverage-transitions                                                                                             | https://www.cms.gov/medicare/payment/prospective-payment-systems/provider-specific-data-public-use-sas-format       | None       | 200.0       | 2026-03-31 13:39:34 |
| https://www.cms.gov/medicare/payment/prospective-payment-systems/provider-specific-data-public-use-sas-format                                                                            | None                                                                                                                | None       | 200.0       | 2026-03-31 13:39:34 |
| https://www.cms.gov/priorities/key-initiatives/burden-reduction                                                                                                                        | https://www.cms.gov/medicare/payment/prospective-payment-systems/provider-specific-data-public-use-sas-format       | None       | 200.0       | 2026-03-31 13:39:34 |
| https://www.cms.gov/about-cms/contact/newsroom                                                                                                                                         | https://www.cms.gov/medicare/payment/prospective-payment-systems/provider-specific-data-public-use-sas-format       | None       | 200.0       | 2026-03-31 13:39:34 |
| https://www.cms.gov/fraud                                                                                                                                                              | https://www.cms.gov/medicare/payment/prospective-payment-systems/provider-specific-data-public-use-sas-format       | None       | 200.0       | 2026-03-31 13:39:34 |
| https://www.cms.gov/data-research                                                                                                                                                      | https://www.cms.gov/medicare/payment/prospective-payment-systems/provider-specific-data-public-use-sas-format       | None       | 200.0       | 2026-03-31 13:39:34 |
| https://www.cms.gov/priorities/key-initiatives/e-health                                                                                                                                | https://www.cms.gov/medicare/payment/prospective-payment-systems/provider-specific-data-public-use-sas-format       | None       | 200.0       | 2026-03-31 13:39:34 |

Insights from the crawled data:
*   **Domain Focus:** The pipeline successfully traversed deep into the CMS (Centers for Medicare & Medicaid Services) and Cboe Datashop sites, capturing both high-level landing pages and direct links to data assets.
*   **Data Asset Discovery:** Many of the crawled URLs are direct links to data files (e.g., `.zip` for ICD-10 codes, `.pdf` for specifications, and `.xlsx` for message lists), indicating a thorough discovery of structured data sources.
*   **Health and Finance Context:** The provenance confirms a focus on healthcare billing/coding (CMS) and financial market data (Cboe), matching the intended onboarding scope.
*   **Recursive Crawling:** The `parent_url` field demonstrates how the crawler moves from main product pages to specific document and sample data links.

Would you like to know how many files of each type (pdf, csv, zip) were discovered, or which parent URLs yielded the most discovered links? I can also check for any failed crawls.

<a id="data-engineer-q9"></a>
#### Q9: What table relationships were detected across datasets?

**Flow:** `agent_chat` → `agent_engineer` (meta_chat)

| Step | Agent | Action | Time |
|------|-------|--------|------|
| 1 | agent_chat | `transfer_to_agent` | 2.6s |
| 2 | agent_engineer | `meta_chat` | 5.0s |
| | | **Total** | **25.2s** |

**Answer:**

Table relationships were primarily detected for the `data_onboarding_cms_gov_bronze` dataset. There were no specific relationships recorded for the `data_onboarding_datashop_cboe_com_bronze` dataset.

For the `data_onboarding_cms_gov_bronze` dataset, the relationships include:

**Containment Hierarchies**:
*   `ipsf_full` acts as a parent table and contains:
    *   `ipsf_hha` (Home Health)
    *   `ipsf_hos` (Hospice)
    *   `ipsf_inp` (Inpatient)
    *   `ipsf_ipf` (Inpatient Psychiatric)
    *   `ipsf_irf` (Inpatient Rehabilitation)
    *   `ipsf_ltch` (Long-Term Care Hospital)
    *   `ipsf_snf` (Skilled Nursing Facility)
*   `opsf_full` contains the `opsf` table.

**Snapshotting**:
Most major tables (e.g., `ipsf_hha`, `ipsf_inp`, `opsf`) have corresponding **LRO (Latest Record Only)** snapshot tables (e.g., `ipsf_hha_lro`).

**Shared Keys**:
These tables share a consistent set of primary and descriptive keys, such as `provider_ccn`, `effective_date`, `npi`, and `fiscal_year_begin_date`, which facilitates cross-table analysis and data integrity.

For example, the `ipsf_hha` table's relationships are detailed as:
*   `contained_by`: `ipsf_full`
*   `has_snapshot`: `ipsf_hha_lro`
*   `shared_keys`: A long list of common keys including `provider_ccn`, `effective_date`, `fiscal_year_begin_date`, `export_date`, etc.

The same pattern applies to `ipsf_hos`, `ipsf_inp`, `ipsf_ipf`, `ipsf_irf`, `ipsf_ltch`, `ipsf_snf`, and `opsf` and their respective `_lro` snapshots.

Would you like to know more about the column mappings for the `ipsf_full` table, or perhaps see the processing logs for the `cms_gov` dataset?

### Catalog Explorer

<a id="catalog-explorer-q1"></a>
#### Q1: What does PRVDR_NUM mean?

**Flow:** `agent_chat` → `agent_catalog` (search_context / get_table_columns)

| Step | Agent | Action | Time |
|------|-------|--------|------|
| 1 | agent_chat | `transfer_to_agent` | 2.5s |
| 2 | agent_catalog | `search_context` | 4.7s |
| | | **Total** | **10.8s** |

**Answer:**

I couldn't find a direct definition for `PRVDR_NUM` in the available documentation. The search returned results for other columns like `carrier_code`, `message_number`, `vbp_participant_indicator`, and `hrr_participant_indicator`, but nothing specific to `PRVDR_NUM`.

<a id="catalog-explorer-q10"></a>
#### Q10: What Medicare payment data is available and how are the tables organized?

**Flow:** `agent_chat` → `agent_catalog` (search_context / get_table_columns)

| Step | Agent | Action | Time |
|------|-------|--------|------|
| 1 | agent_chat | `transfer_to_agent` | 2.1s |
| 2 | agent_catalog | `search_context` | 4.6s |
| 3 | agent_catalog | `search_context` | 10.4s |
| 4 | agent_catalog | `list_all_tables` | 15.3s |
| | | **Total** | **25.1s** |

**Answer:**

There is a variety of Medicare payment data available, primarily categorized into provider-specific payment calculations and Medicare plan information.

**Available Medicare Payment Data:**

1.  **Provider-Specific Payment Calculation Data**: These tables, found in the `data_onboarding_cms_gov_bronze` dataset, contain detailed information used for calculating Medicare payments to various healthcare providers.
    *   **`ipsf_full`**: This table contains "Provider Specific File (PSF) for Inpatient Prospective Payment System (IPPS) facilities, containing provider-specific data used for Medicare payment calculations. This is a snapshot from January 1, 2025. It includes financial rates, geographic and provider-specific adjustments, and provider characteristics."
    *   Similar tables exist for specific facility types under IPPS, such as:
        *   `ipsf_hha` (Home Health Agency)
        *   `ipsf_hos` (Hospice)
        *   `ipsf_inp` (Inpatient)
        *   `ipsf_ipf` (Inpatient Psychiatric Facility)
        *   `ipsf_irf` (Inpatient Rehabilitation Facility)
        *   `ipsf_ltch` (Long-Term Care Hospital)
        *   `ipsf_snf` (Skilled Nursing Facility)
    *   **`opsf_full` and `opsf`**: These tables contain data related to the Outpatient Prospective Payment System, likely mirroring the `ipsf` tables for outpatient services.
    *   Many of these provider-specific tables also have `_lro` versions (e.g., `ipsf_hha_lro`), which may represent limited reimbursement options or specific subsets of the data.

2.  **Medicare Plan Information**:
    *   **`cy2026_landscape_202603`**: This table provides a list of "all approved Medicare Advantage (MA) Plans, Cost Plans, Special Needs Plans (SNP), and stand-alone Prescription Drug Plans (PDP) for contract year 2026. It includes detailed information about plan characteristics, service areas, premiums, cost-sharing, and star ratings."

**How the Tables are Organized:**

1.  **By Prospective Payment System (PPS) and Facility Type**: The `ipsf_` and `opsf_` tables are organized by the type of Prospective Payment System (Inpatient or Outpatient) and then further by the specific facility or provider type (e.g., hospital, skilled nursing facility, home health agency). These tables contain financial rates, geographic and provider-specific adjustments, and provider characteristics relevant to Medicare payment calculations.
2.  **By Contract Year for Plan Data**: The `cy2026_landscape_202603` table is organized by contract year and provides comprehensive details about Medicare Advantage and Prescription Drug Plans offered within that year, including premiums and cost-sharing.

In addition to these direct payment-related tables, there are also numerous supporting tables in the `data_onboarding_cms_gov_bronze` dataset related to ICD-10 codes (for diagnoses and procedures), ground ambulance provider data (e.g., `_508_compliant_version_of_sampled_npis`), and Medicare Summary Notice (MSN) messages, which indirectly contribute to the understanding of Medicare healthcare and payment processes.

<a id="catalog-explorer-q2"></a>
#### Q2: Describe the columns in the IPSF full table.

**Flow:** `agent_chat` → `agent_catalog` (search_context / get_table_columns)

| Step | Agent | Action | Time |
|------|-------|--------|------|
| 1 | agent_chat | `transfer_to_agent` | 2.0s |
| 2 | agent_catalog | `get_table_columns` | 4.0s |
| | | **Total** | **7.9s** |

**Answer:**

The `ipsf_full` table (statmike-mlops-349915.data_onboarding_cms_gov_bronze.ipsf_full) contains 68 columns providing provider-specific data for Inpatient Prospective Payment System (IPPS) facilities. This data is used for Medicare payment calculations and includes financial rates, geographic and provider-specific adjustments, and provider characteristics.

Here are some key columns and their descriptions:

*   **provider_ccn**: The 6-digit CMS Certification Number (CCN), a unique identifier for the Medicare provider.
*   **effective_date**: The date on which the specific rate, factor, or data element in this record became effective.
*   **fiscal_year_begin_date**: The start date of the provider's fiscal year.
*   **export_date**: The date the data was exported from the source system, indicating the snapshot date of the file.
*   **termination_date**: The date the provider's participation in the Medicare program was terminated, if applicable.
*   **npi**: The National Provider Identifier (NPI), a unique 10-digit identification number for the health care provider.
*   **provider_type_code**: A code indicating the type of provider (e.g., '00' for hospital).
*   **census_division_code**: A code representing the U.S. Census Division where the provider is located.
*   **msa_actual_geographic_location_code**: A code for the Metropolitan Statistical Area (MSA) of the provider's actual geographic location.
*   **bed_size**: The number of beds in the facility.
*   **case_mix_adjusted_cost_per_discharge_pps_facility_specific_rate**: Case mix adjusted cost per discharge PPS facility specific rate.
*   **cost_of_living_adjustment**: Cost of living adjustment.
*   **operating_dsh**: Operating disproportionate share hospital (DSH) adjustment.
*   **vbp_adjustment**: Value-Based Purchasing (VBP) adjustment.
*   **uncompensated_care_amount**: Amount for uncompensated care.
*   **last_updated_date**: The date the record was last updated in the source system.

For a complete list and more detailed documentation, you can query `data_onboarding_cms_gov_bronze.table_documentation` where `table_name = 'ipsf_full'`.

<a id="catalog-explorer-q3"></a>
#### Q3: How are the different IPSF tables related to each other?

**Flow:** `agent_chat` → `agent_catalog` (search_context / get_table_columns)

| Step | Agent | Action | Time |
|------|-------|--------|------|
| 1 | agent_chat | `transfer_to_agent` | 2.4s |
| 2 | agent_catalog | `search_context` | 4.5s |
| | | **Total** | **9.8s** |

**Answer:**

The `data_onboarding_cms_gov_bronze.ipsf_full` table contains the following IPSF tables:
*   `ipsf_hha`
*   `ipsf_hos`
*   `ipsf_inp`
*   `ipsf_ipf`
*   `ipsf_irf`
*   `ipsf_ltch`
*   `ipsf_snf`

<a id="catalog-explorer-q4"></a>
#### Q4: What columns are shared between the HHA and SNF tables?

**Flow:** `agent_chat` → `agent_catalog` (search_context / get_table_columns)

| Step | Agent | Action | Time |
|------|-------|--------|------|
| 1 | agent_chat | `transfer_to_agent` | 2.3s |
| 2 | agent_catalog | `list_all_tables` | 5.4s |
| | | **Total** | **16.3s** |

**Answer:**

The `ipsf_hha` and `ipsf_snf` tables share all of their 68 columns. These common columns are:

*   `provider_ccn`
*   `effective_date`
*   `fiscal_year_begin_date`
*   `export_date`
*   `termination_date`
*   `waiver_indicator`
*   `intermediary_number`
*   `provider_type_code`
*   `census_division_code`
*   `msa_actual_geographic_location_code`
*   `msa_wage_index_location_code`
*   `msa_standardized_amount_location`
*   `sole_community_or_medicare_dependent_hospital_base_year`
*   `change_code_for_lugar_reclassification`
*   `temporary_relief_indicator`
*   `federal_pps_blend`
*   `state_code`
*   `case_mix_adjusted_cost_per_discharge_pps_facility_specific_rate`
*   `cost_of_living_adjustment`
*   `interns_to_beds_ratio`
*   `bed_size`
*   `operating_cost_to_charge_ratio`
*   `case_mix_index`
*   `supplemental_security_income_ratio`
*   `medicaid_ratio`
*   `special_provider_update_factor`
*   `operating_dsh`
*   `fiscal_year_end_date`
*   `special_payment_indicator`
*   `hospital_quality_indicator`
*   `cbsa_actual_geographic_location`
*   `cbsa_wage_index_location`
*   `cbsa_standardized_amount_location`
*   `special_wage_index`
*   `pass_through_amount_for_capital`
*   `pass_through_amount_for_direct_medical_education`
*   `pass_through_amount_for_organ_acquisition`
*   `pass_through_total_amount`
*   `capital_pps_payment_code`
*   `hospital_specific_capital_rate`
*   `old_capital_hold_harmless_rate`
*   `new_capital_hold_harmless_rate`
*   `capital_cost_to_charge_ratio`
*   `new_hospital`
*   `capital_indirect_medical_education_ratio`
*   `capital_exception_payment_rate`
*   `vbp_participant_indicator`
*   `vbp_adjustment`
*   `hrr_participant_indicator`
*   `hrr_adjustment`
*   `bundle_model1_discount`
*   `hac_reduction_participant_indicator`
*   `uncompensated_care_amount`
*   `ehr_reduction_indicator`
*   `low_volume_adjustment_factor`
*   `county_code`
*   `medicare_performance_adjustment`
*   `ltch_dpp_indicator`
*   `supplemental_wage_index`
*   `supplemental_wage_index_indicator`
*   `change_code_wage_index_reclassification`
*   `npi`
*   `pass_through_amount_for_allogenic_stem_cell_acquisition`
*   `pps_blend_year_indicator`
*   `last_updated_date`
*   `pass_through_amount_for_direct_graduate_medical_education`
*   `pass_through_amount_for_kidney_acquisition`
*   `pass_through_amount_for_supply_chain`

<a id="catalog-explorer-q5"></a>
#### Q5: What does the wage index represent in this data?

**Flow:** `agent_chat` → `agent_catalog` (search_context / get_table_columns)

| Step | Agent | Action | Time |
|------|-------|--------|------|
| 1 | agent_chat | `transfer_to_agent` | 2.3s |
| 2 | agent_catalog | `search_context` | 4.4s |
| | | **Total** | **11.0s** |

**Answer:**

The documentation does not provide a specific definition for "wage index" or what it represents. However, the search results indicate that there are several columns related to `cbsa_wage_index_location` and `supplemental_wage_index_indicator` in various tables, such as:

*   `data_onboarding_cms_gov_bronze.ipsf_ipf.cbsa_wage_index_location`
*   `data_onboarding_cms_gov_bronze.ipsf_ltch.cbsa_wage_index_location`
*   `data_onboarding_cms_gov_bronze.ipsf_irf.cbsa_wage_index_location`
*   `data_onboarding_cms_gov_bronze.ipsf_ltch_lro.cbsa_wage_index_location`
*   `data_onboarding_cms_gov_bronze.ipsf_ipf_lro.cbsa_wage_index_location`
*   `data_onboarding_cms_gov_bronze.ipsf_irf_lro.cbsa_wage_index_location`
*   `data_onboarding_cms_gov_bronze.ipsf_snf.cbsa_wage_index_location`
*   `data_onboarding_cms_gov_bronze.ipsf_full.supplemental_wage_index_indicator`
*   `data_onboarding_cms_gov_bronze.ipsf_snf_lro.cbsa_wage_index_location`
*   `data_onboarding_cms_gov_bronze.ipsf_ipf.supplemental_wage_index_indicator`

<a id="catalog-explorer-q6"></a>
#### Q6: Explain the difference between the IPSF full file and the provider-type-specific files.

**Flow:** `agent_chat` → `agent_catalog` (search_context / get_table_columns)

| Step | Agent | Action | Time |
|------|-------|--------|------|
| 1 | agent_chat | `transfer_to_agent` | 2.1s |
| 2 | agent_catalog | `search_context` | 4.5s |
| | | **Total** | **11.2s** |

**Answer:**

The `data_onboarding_cms_gov_bronze.ipsf_full` file is a comprehensive dataset that **contains** data from various provider-type-specific files.

The provider-type-specific files, such as `data_onboarding_cms_gov_bronze.ipsf_hha`, `data_onboarding_cms_gov_bronze.ipsf_hos`, `data_onboarding_cms_gov_bronze.ipsf_inp`, `data_onboarding_cms_gov_bronze.ipsf_ipf`, `data_onboarding_cms_gov_bronze.ipsf_irf`, `data_onboarding_cms_gov_bronze.ipsf_ltch`, and `data_onboarding_cms_gov_bronze.ipsf_snf`, represent subsets of the full file, each focused on a particular type of provider.

<a id="catalog-explorer-q7"></a>
#### Q7: What reference or lookup data is available?

**Flow:** `agent_chat` → `agent_catalog` (search_context / get_table_columns)

| Step | Agent | Action | Time |
|------|-------|--------|------|
| 1 | agent_chat | `transfer_to_agent` | 2.3s |
| 2 | agent_catalog | `list_all_tables` | 4.5s |
| | | **Total** | **21.4s** |

**Answer:**

Based on the available table descriptions, here are some tables that appear to be reference or lookup data:

*   **_11_20_25_complete_msn_message_list** (`statmike-mlops-349915.data_onboarding_cms_gov_bronze._11_20_25_complete_msn_message_list`): A master list of standardized messages that appear on the Medicare Summary Notice (MSN).
*   **_508_compliant_version_of_icd_10_cm_conversion_table_fy25** (`statmike-mlops-349915.data_onboarding_cms_gov_bronze._508_compliant_version_of_icd_10_cm_conversion_table_fy25`): A conversion table for ICD-10-CM codes for Fiscal Year 2025.
*   **_508_version_icd_10_cm_conversion_table_fy2026_april_1_2026** (`statmike-mlops-349915.data_onboarding_cms_gov_bronze._508_version_icd_10_cm_conversion_table_fy2026_april_1_2026`): A conversion table for ICD-10-CM codes for Fiscal Year 2026.
*   **cy2026_landscape_202603** (`statmike-mlops-349915.data_onboarding_cms_gov_bronze.cy2026_landscape_202603`): Contains a list of all approved Medicare Advantage (MA) Plans, Cost Plans, Special Needs Plans (SNP), and stand-alone Prescription Drug Plans (PDP) for contract year 2026.
*   **icd10cm_drug_2025** (`statmike-mlops-349915.data_onboarding_cms_gov_bronze.icd10cm_drug_2025`): Contains data related to ICD10-CM drug codes for 2025.
*   **icd10cm_drug_2026** (`statmike-mlops-349915.data_onboarding_cms_gov_bronze.icd10cm_drug_2026`): Contains data related to ICD10-CM drug codes for 2026.
*   **icd10cm_eindex_2025** (`statmike-mlops-349915.data_onboarding_cms_gov_bronze.icd10cm_eindex_2025`): Contains data related to ICD10-CM e-index for 2025.
*   **icd10cm_eindex_2026** (`statmike-mlops-349915.data_onboarding_cms_gov_bronze.icd10cm_eindex_2026`): Contains data related to ICD10-CM e-index for 2026.
*   **icd10cm_index_2025** (`statmike-mlops-349915.data_onboarding_cms_gov_bronze.icd10cm_index_2025`): Contains data related to ICD10-CM index for 2025.
*   **icd10cm_index_2026** (`statmike-mlops-349915.data_onboarding_cms_gov_bronze.icd10cm_index_2026`): Contains data related to ICD10-CM index for 2026.
*   **icd10cm_neoplasm_2025** (`statmike-mlops-349915.data_onboarding_cms_gov_bronze.icd10cm_neoplasm_2025`): Contains data related to ICD10-CM neoplasm codes for 2025.
*   **icd10cm_neoplasm_2026** (`statmike-mlops-349915.data_onboarding_cms_gov_bronze.icd10cm_neoplasm_2026`): Contains data related to ICD10-CM neoplasm codes for 2026.
*   **icd10pcs_conversion_table** (`statmike-mlops-349915.data_onboarding_cms_gov_bronze.icd10pcs_conversion_table`): A conversion table for ICD10-PCS codes.
*   **icd10pcs_definitions_2026** (`statmike-mlops-349915.data_onboarding_cms_gov_bronze.icd10pcs_definitions_2026`): Contains definitions for ICD10-PCS codes for 2026.
*   **icd10pcs_index_2026** (`statmike-mlops-349915.data_onboarding_cms_gov_bronze.icd10pcs_index_2026`): Contains index data for ICD10-PCS codes for 2026.
*   **icd10pcs_tables_2026** (`statmike-mlops-349915.data_onboarding_cms_gov_bronze.icd10pcs_tables_2026`): Contains table data for ICD10-PCS codes for 2026.
*   **msn_message_character_limits** (`statmike-mlops-349915.data_onboarding_cms_gov_bronze.msn_message_character_limits`): Provides character limits for MSN messages.
*   **poaexempt_add_codes_fy25** (`statmike-mlops-349915.data_onboarding_cms_gov_bronze.poaexempt_add_codes_fy25`): A list of new ICD-10-CM diagnosis codes added to the Present on Admission (POA) exempt list for Fiscal Year 2025.
*   **poaexempt_add_codes_fy26** (`statmike-mlops-349915.data_onboarding_cms_gov_bronze.poaexempt_add_codes_fy26`): A list of new ICD-10-CM diagnosis codes added to the Present on Admission (POA) exempt list for Fiscal Year 2026.
*   **poaexempt_codes_fy25** (`statmike-mlops-349915.data_onboarding_cms_gov_bronze.poaexempt_codes_fy25`): Contains POA exempt codes for Fiscal Year 2025.
*   **poaexempt_codes_fy26** (`statmike-mlops-349915.data_onboarding_cms_gov_bronze.poaexempt_codes_fy26`): Contains POA exempt codes for Fiscal Year 2026.
*   **poaexempt_delete_codes_fy25** (`statmike-mlops-349915.data_onboarding_cms_gov_bronze.poaexempt_delete_codes_fy25`): Contains POA exempt codes to be deleted for Fiscal Year 2025.
*   **poaexempt_delete_codes_fy26** (`statmike-mlops-349915.data_onboarding_cms_gov_bronze.poaexempt_delete_codes_fy26`): Contains POA exempt codes to be deleted for Fiscal Year 2026.
*   **poaexempt_revise_codes_fy25** (`statmike-mlops-349915.data_onboarding_cms_gov_bronze.poaexempt_revise_codes_fy25`): Contains POA exempt codes to be revised for Fiscal Year 2025.
*   **poaexempt_revise_codes_fy26** (`statmike-mlops-349915.data_onboarding_cms_gov_bronze.poaexempt_revise_codes_fy26`): Contains POA exempt codes to be revised for Fiscal Year 2026.

Additionally, the following tables relate to sampled NPIs for ground ambulance providers, which can serve as reference lists for those specific samples:

*   **_508_compliant_version_of_sampled_npis** (`statmike-mlops-349915.data_onboarding_cms_gov_bronze._508_compliant_version_of_sampled_npis`)
*   **_508compliantversion_y2** (`statmike-mlops-349915.data_onboarding_cms_gov_bronze._508compliantversion_y2`)
*   **cmsambdata_y1sample_forposting20feb** (`statmike-mlops-349915.data_onboarding_cms_gov_bronze.cmsambdata_y1sample_forposting20feb`)
*   **cmsambdata_y2sample_post** (`statmike-mlops-349915.data_onboarding_cms_gov_bronze.cmsambdata_y2sample_post`)
*   **cmsambdata_y3sample_post** (`statmike-mlops-349915.data_onboarding_cms_gov_bronze.cmsambdata_y3sample_post`)
*   **cmsambdata_y3sample_post508** (`statmike-mlops-349915.data_onboarding_cms_gov_bronze.cmsambdata_y3sample_post508`)
*   **cmsambdata_y4sample_post** (`statmike-mlops-349915.data_onboarding_cms_gov_bronze.cmsambdata_y4sample_post`)
*   **cmsambdata_y4sample_post508** (`statmike-mlops-349915.data_onboarding_cms_gov_bronze.cmsambdata_y4sample_post508`)

<a id="catalog-explorer-q8"></a>
#### Q8: What does the case mix index measure?

**Flow:** `agent_chat` → `agent_catalog` (search_context / get_table_columns)

| Step | Agent | Action | Time |
|------|-------|--------|------|
| 1 | agent_chat | `transfer_to_agent` | 2.1s |
| 2 | agent_catalog | `search_context` | 4.7s |
| | | **Total** | **10.5s** |

**Answer:**

The documentation does not provide a definition for "case mix index". It appears as a column in several tables within the `data_onboarding_cms_gov_bronze` dataset, including:

*   `data_onboarding_cms_gov_bronze.ipsf_hos.case_mix_index`
*   `data_onboarding_cms_gov_bronze.ipsf_hos_lro.case_mix_index`
*   `data_onboarding_cms_gov_bronze.ipsf_full.case_mix_index`
*   `data_onboarding_cms_gov_bronze.ipsf_hha.case_mix_index`
*   `data_onboarding_cms_gov_bronze.ipsf_ltch.case_mix_index`
*   `data_onboarding_cms_gov_bronze.ipsf_inp.case_mix_index`
*   `data_onboarding_cms_gov_bronze.ipsf_hha_lro.case_mix_index`
*   `data_onboarding_cms_gov_bronze.ipsf_irf.case_mix_index`
*   `data_onboarding_cms_gov_bronze.ipsf_snf.case_mix_index`
*   `data_onboarding_cms_gov_bronze.ipsf_inp_lro.case_mix_index`

However, the specific meaning or what it measures is not detailed in the available documentation.

<a id="catalog-explorer-q9"></a>
#### Q9: Which tables contain hospice-related data?

**Flow:** `agent_chat` → `agent_catalog` (search_context / get_table_columns)

| Step | Agent | Action | Time |
|------|-------|--------|------|
| 1 | agent_chat | `transfer_to_agent` | 2.3s |
| 2 | agent_catalog | `search_context` | 4.6s |
| | | **Total** | **14.2s** |

**Answer:**

I could not find any tables explicitly containing "hospice-related data" based on my initial search. The results pointed to columns within tables like `data_onboarding_cms_gov_bronze.ipsf_hha`, `data_onboarding_cms_gov_bronze.ipsf_hha_lro`, `data_onboarding_cms_gov_bronze.ipsf_hos`, `data_onboarding_cms_gov_bronze.ipsf_hos_lro`, and `data_onboarding_cms_gov_bronze.ipsf_irf`, but these columns are general indicators and the tables themselves do not explicitly mention hospice in their descriptions.

It's possible that hospice data is integrated into broader healthcare datasets without being explicitly named "hospice" in the table or column descriptions.

Would you like me to try searching for a broader term like "patient care" or "end-of-life care" to see if any relevant tables appear?

