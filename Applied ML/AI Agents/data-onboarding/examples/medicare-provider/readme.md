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

This example shows the **recommended production workflow** — onboard locally, query via deployed Agent Engine:

```
Local (batch)                              Agent Engine (conversational)
─────────────                              ────────────────────────────
uv run adk web                             Python SDK / REST API
  → agent_orchestrator                       → agent_chat (deployed)
  → crawl CMS, download parquet,            → fast questions over the
    infer schemas, create BQ tables            onboarded data
```

1. **Onboard** — Run `agent_orchestrator` locally to crawl the CMS page, download parquet files, and create BigQuery tables
2. **Query** — Ask questions through the **deployed** `agent_chat` on Vertex AI Agent Engine
3. **Evaluate** — Run all 30 questions programmatically and collect results with timing

Unlike the [CBOE example](../cboe/cboe.md) (which runs questions locally), this example queries the **deployed agent** via the Vertex AI Python SDK — demonstrating Agent Engine in production.

### Why this split?

The orchestrator agent runs a long batch pipeline — crawling hundreds of pages, downloading files, inferring schemas, creating tables — that can take 20–60 minutes. Agent Engine is optimized for conversational agents with fast request-response cycles: long-running tool calls exceed its streaming timeout, and in-memory tool state is lost when the connection reconnects to a fresh container. The chat agent responds in seconds — a perfect Agent Engine workload.

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

## Step 2: Query with the Deployed Chat Agent

Make sure the chat agent is deployed:

```bash
uv run python deploy/deploy.py chat --info
```

Then ask questions interactively via `adk web` (connecting to Agent Engine sessions):

```bash
uv run adk web --session_service_uri="agentengine://RESOURCE_ID"
```

Or query programmatically — see [Step 3](#step-3-run-all-questions).

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

Run all 30 questions against the deployed chat agent and collect results:

```bash
# From the data-onboarding project root:

# Run all 30 questions (sequential, 5s delay between)
uv run python examples/medicare-provider/run_medicare_questions.py

# Run one persona at a time
uv run python examples/medicare-provider/run_medicare_questions.py --persona "Data Analyst"
uv run python examples/medicare-provider/run_medicare_questions.py --persona "Data Engineer"
uv run python examples/medicare-provider/run_medicare_questions.py --persona "Catalog Explorer"

# Run a single question
uv run python examples/medicare-provider/run_medicare_questions.py --id data-analyst-q3

# Resume (skip already-completed questions)
uv run python examples/medicare-provider/run_medicare_questions.py --resume

# Adjust delay between questions (default: 5s)
uv run python examples/medicare-provider/run_medicare_questions.py --delay 10
```

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
| **Question runner** | Local `InMemoryRunner` | **Deployed Agent Engine** (Python SDK) |
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
  run_medicare_questions.py         # Runs questions against deployed agent
  build_medicare_results.py         # Generates Results markdown from JSON
  results/
    medicare_results.json           # Collected answers + timing (after running)
```

---

## Results

*Results will appear here after running `build_medicare_results.py --write`.*
