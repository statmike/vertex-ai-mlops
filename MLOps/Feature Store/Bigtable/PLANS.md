# Bigtable Feature Store — Plans & Status

> Last updated: 2026-05-06

## What We Built

10 notebooks, a series readme, and a `pyproject.toml` for a folder-level uv environment. All notebooks share consistent config, pixel-tracking headers, prerequisite checks (NB1-9 → NB0), and the `bigtable-feature-store` kernel. 60+ verified Google Cloud documentation links across all files — zero 404s.

### Supporting Files

| File | Status | Notes |
|------|--------|-------|
| `readme.md` | **Built** | Series overview, Key Concepts, 10 notebook descriptions with "What you'll learn", comparison table, Documentation reference (20 Bigtable + 11 BigQuery links), cross-reference to Vertex AI series |
| `pyproject.toml` | **Built** | uv project config with all dependencies |
| `../readme.md` (hub) | **Updated** | Comparison table (Vertex AI vs Bigtable), expanded descriptions |
| `../vertex/readme.md` | **Updated** | Cross-reference callout to Bigtable series |

### Notebooks

| # | Notebook | Cells | Size | Status |
|---|----------|-------|------|--------|
| 0 | Environment | 42 (23 md, 19 code) | 52 KB | **Built** |
| 1 | Fundamentals | 48 (25 md, 23 code) | 49 KB | **Built + cbt/GoogleSQL/BQ reads** |
| 2 | Serialization | 58 (24 md, 34 code) | 78 KB | **Built** |
| 3 | Synchronization | 55 (26 md, 29 code) | 67 KB | **Built + executable streaming + validation** |
| 4 | History and Time Travel | 57 (33 md, 24 code) | 59 KB | **Built** |
| 5 | Streaming and Direct Writes | 70 (37 md, 33 code) | 75 KB | **Built + Pub/Sub demo** |
| 6 | Key Design and Organization | 63 (30 md, 33 code) | 69 KB | **Built** |
| 7 | Schema Evolution and Operations | 56 (28 md, 28 code) | 76 KB | **Built + drift monitoring + BQ ML validation** |
| 8 | Serving Integration | 46 (22 md, 24 code) | 42 KB | **Built** |
| 9 | Dynamic Features | 47 (23 md, 24 code) | 47 KB | **Built** |

---

## Testing & Verification Checklist

Run notebooks in this order. NB0 creates all shared resources; NB1 creates the first export and reservation; NB2-7 can run in any order after NB1 (each creates/cleans up its own resources).

### Pre-flight

- [ ] Ensure GCP project `statmike-mlops-349915` has billing enabled
- [ ] Ensure no leftover `feature-store` Bigtable instance from prior runs (or accept reuse)
- [ ] Ensure no leftover `bigtable_feature_store` BQ dataset (or accept reuse)
- [ ] Install kernel: `cd Bigtable && uv sync && uv run python -m ipykernel install --user --name bigtable-feature-store --display-name "Bigtable Feature Store"`

### NB0: Environment

- [ ] Restart & Run All completes without errors
- [ ] BQ dataset `bigtable_feature_store` created
- [ ] `dense_features` table: ~130,000 rows, 200+ columns, all BQ data types present
- [ ] `sparse_events` table: ~2.6M rows, 5 event types
- [ ] Data investigation plots render (entity group distribution, daily volume, histograms)
- [ ] Bigtable instance `feature-store` created (DEVELOPMENT, us-central1-a)
- [ ] Bigtable table `features` created with column families: `features`, `metadata`
- [ ] APIs enabled: bigquery, bigqueryreservation, bigquerydatatransfer, bigtable, bigtableadmin, pubsub, monitoring
- [ ] Review: Does the Bigtable architecture explanation (instances → clusters → nodes) read clearly?
- [ ] Review: Does "Ways to Access Bigtable" section cover enough interfaces?

### NB1: Fundamentals

- [ ] Prerequisite check passes (finds BQ dataset + Bigtable instance from NB0)
- [ ] BQ latency measurement works (SELECT on dense_features)
- [ ] Enterprise reservation created successfully
- [ ] App profile created via gcloud
- [ ] EXPORT DATA completes — verify rows in Bigtable
- [ ] `#schema` metadata row written and read back correctly
- [ ] `decode_features()` function works on single-row read
- [ ] Batch read returns DataFrame with correct values
- [ ] Latency shootout: BQ vs Bigtable chart renders, Bigtable significantly faster
- [ ] Native column mapping preview works
- [ ] Cleanup: reservation and assignment deleted

### NB2: Serialization

- [ ] Prerequisite check passes
- [ ] Reservation created
- [ ] 5 Bigtable tables created (features-native, features-json, features-concat, features-proto, features-hybrid)
- [ ] Data type challenge: INFORMATION_SCHEMA query works, type classification table renders
- [ ] Method 1 (Native): EXPORT DATA with individual columns, read-back works
- [ ] Method 2 (JSON): TO_JSON_STRING export, read-back works
- [ ] Method 3 (Concat): CONCAT export, delimiter trap discussion present
- [ ] Method 4 (Protobuf): Dynamic protobuf schema generation, binary write, read-back with FileDescriptorSet
- [ ] Method 5 (Hybrid): Native hot features + protobuf blob
- [ ] Tax Analysis: storage size comparison, latency benchmark chart renders
- [ ] Cleanup: reservation deleted, demo tables deleted

### NB3: Synchronization

- [ ] Prerequisite check passes
- [ ] Reservation + app profile created
- [ ] One-time EXPORT DATA completes, row count verified
- [ ] `overwrite = true` vs `overwrite = false` comparison cell reads clearly
- [ ] Scheduled query pattern (Data Transfer Service) — API call shown (not executed is OK)
- [ ] Orchestration alternatives section (Airflow/Composer, Cloud Scheduler, Workflows) present
- [ ] Continuous query SQL with `APPENDS()` — shown as reference pattern
- [ ] Streaming pipeline architecture diagram present
- [ ] Propagation Race: test row inserted, EXPORT DATA timed, propagation measured
- [ ] Cleanup: reservation resources deleted

### NB4: History and Time Travel

- [ ] Prerequisite check passes
- [ ] Creates `features-history-key` table (key-based history design)
- [ ] Creates `features-history-cell` table (cell versioning design)
- [ ] Writes sample entities with timestamps to both tables
- [ ] Key-based: prefix range scan works, `read_features_at_time_key_design()` works
- [ ] Cell versioning: `CellsColumnLimitFilter(1)` returns latest, `TimestampRangeFilter` returns PIT
- [ ] Point-in-time joins implemented for both designs
- [ ] `ML.FEATURES_AT_TIME` and `ML.ENTITY_FEATURES_AT_TIME` BQ queries work
- [ ] GC policy demo tables created and GC behavior demonstrated
- [ ] Trade-off summary table present and clear
- [ ] Cleanup: demo tables deleted

### NB5: Streaming and Direct Writes

- [ ] Prerequisite check passes
- [ ] Creates `features-writes` table with `MaxVersionsGCRule(3)`
- [ ] Single-row write + read-back works
- [ ] Batch write (1,000 rows) completes, throughput measured
- [ ] Atomic increment (`increment_cell_value`) works, concurrent test passes
- [ ] Conditional write (`CheckAndMutateRow`) state transition works
- [ ] Change streams section present (reference pattern — may not execute if not enabled)
- [ ] Dual-write architecture diagrams present
- [ ] Idempotency patterns documented
- [ ] Cleanup: experiment table deleted

### NB6: Key Design and Organization

- [ ] Prerequisite check passes
- [ ] Row key anatomy explanation with compound key format
- [ ] Key distribution visualization renders (bar chart, pie chart)
- [ ] Hotspot anti-patterns demonstrated with visualizations
- [ ] 4 key design patterns compared with distribution plots
- [ ] Creates `features-key-design` table, writes 300 rows from BQ
- [ ] Point reads, prefix scans, filtered scans, multi-row reads all work
- [ ] Creates `features-multi-cf` table with 3 column families
- [ ] Selective reads per family demonstrated
- [ ] Single table vs multi-table decision matrix present
- [ ] Key Visualizer section (console URLs, simulated heatmaps)
- [ ] Cleanup: demo tables deleted

### NB7: Schema Evolution and Operations

- [ ] Prerequisite check passes
- [ ] Versioned schema rows (`#schema#v1`, `#schema#v2`, `#schema#current`) written and read
- [ ] Schema upgrade and rollback demonstrated
- [ ] Adding features: v1 → v2 with backward-compatible decoder
- [ ] Removing features: deprecated metadata, decoder skips deprecated columns
- [ ] Backfill: reads existing rows, batch-appends new features
- [ ] Cloud Monitoring queries execute (may return no data if instance is new)
- [ ] App profiles: created via gcloud, priority levels explained
- [ ] Cost estimation table present
- [ ] Production readiness checklist (20+ items)
- [ ] Cleanup: demo rows, schema versions, and app profiles deleted

### Post-run

- [ ] Bigtable instance `feature-store` still exists and is healthy
- [ ] BQ dataset `bigtable_feature_store` with `dense_features` and `sparse_events` intact
- [ ] No orphaned reservations (check: `bq ls --reservation --project_id=statmike-mlops-349915 --location=us-central1`)
- [ ] All notebook outputs saved (Restart & Run All leaves outputs in place)

---

## MYPLANS.md Coverage Review

Cross-reference of MYPLANS.md modules against what we built:

| MYPLANS Module | Our Notebook | Coverage | Notes |
|----------------|-------------|----------|-------|
| **Prerequisites (Step 0)**: Dense + sparse tables, impedance mismatch | NB0: Environment | **Full** | 130K entities, 200+ features, all BQ types, compound key |
| **Module 1**: First serving layer, EXPORT DATA, Key Visualizer, latency baseline | NB1: Fundamentals | **Full** | End-to-end export + reads + latency shootout |
| **Module 2**: Serialization methods, self-describing schemas, tax analysis | NB2: Serialization | **Full** | All 5 methods + benchmarks + delimiter trap |
| **Module 3**: Sync patterns, propagation race | NB3: Synchronization | **Full** | One-time + scheduled + continuous + streaming + Airflow |
| **Module 4**: History in key vs cell versioning, PIT joins | NB4: History and Time Travel | **Full** | Both designs + GC policies + training data extraction |
| **Module 5**: Direct writes, dual-write, idempotency | NB5: Streaming and Direct Writes | **Full** | Direct + batch + atomic + conditional + change streams |
| **Module 6**: Single table, key namespacing, ordering problem | NB6: Key Design and Organization | **Full** | Compound keys + hotspots + prefix scans + column families |
| **Module 7**: Schema evolution, versioned protobufs, backfilling | NB7: Schema Evolution and Operations | **Full** | Versioned schemas + backfill + monitoring + operations |
| **Module 8**: Monitoring, Key Visualizer, cost optimization | NB7: Schema Evolution and Operations | **Full** | Cloud Monitoring + cost estimation + production checklist |
| **Final Project**: Real-time recommendation engine | — | **Not built** | See "What's Missing" below |

All 8 original MYPLANS.md modules are fully covered. We also added content beyond the original plan: Bigtable architecture explanation, client library catalog, orchestration alternatives, overwrite mode comparison, documentation reference tables, and cross-references to the Vertex AI series.

---

## What's Missing — Planned Additions

### Priority 1: Serving Integration Notebook (NB8)

**Gap:** We teach writing features to Bigtable and reading them back — in notebooks. But we never show the payoff: a serving application that reads features from Bigtable before making a prediction. The Vertex AI series has a CatBoost example (`CatBoost Prediction With Vertex AI Feature Store`). The Bigtable series needs its equivalent.

**Proposed: `Bigtable Feature Store - Serving Integration.ipynb`**

Sections:
- Simple model trained on features from `dense_features` (sklearn or similar — lightweight)
- Cloud Run service: receives prediction request → reads features from Bigtable → runs inference → returns prediction
- End-to-end latency measurement (request → feature read → predict → response)
- Multiple read methods demonstrated side-by-side:
  - Python client (`google-cloud-bigtable`)
  - `cbt` CLI
  - GoogleSQL (Bigtable Studio)
  - BigQuery external table (federated query)
  - REST/gRPC (curl examples)
- Connection pooling and client reuse patterns for production
- Comparison: feature read latency vs model inference latency vs total request latency

**Why it matters:** This is the "so what" notebook. Every prior notebook is infrastructure — this one shows the application. A startup engineer finishes this and has a deployable serving stack. An enterprise architect sees how the pieces compose.

### Priority 2: Serving with Dynamic Feature Computation (NB9)

**Gap:** At serving time, a new event arrives (e.g., a user clicks something) and the model needs features that depend on that event combined with pre-computed features already in Bigtable. Examples: "clicks in the last 30 seconds" requires the new click + the running count; "average transaction amount" requires the new transaction + the stored running average. The client shouldn't have to compute this — the serving layer should handle it with minimal latency.

**Proposed: `Bigtable Feature Store - Dynamic Features.ipynb`**

Sections:
- The problem: pre-computed features are stale the moment a new event arrives
- Pattern 1: Read-modify-write — atomic increment/append on arrival, read updated value at serving time
- Pattern 2: Read + compute — read pre-computed features from Bigtable, combine with the new event value at the serving layer (lightweight aggregation)
- Pattern 3: Streaming aggregation — Pub/Sub → processing → Bigtable direct write updates running aggregates continuously
- Latency analysis: which pattern minimizes total serving latency?
- Client burden analysis: which pattern keeps the client simplest?
- End-to-end demo: simulate events arriving, features updating, and a serving request reading the freshest values

**Why it matters:** This is the pattern that separates a demo feature store from a production one. Most real ML systems need both pre-computed features (batch) and real-time features (streaming/dynamic). Showing how to combine them at serving time with minimal client complexity is the advanced story.

### Priority 3: Executable Streaming Pipeline (fix NB3 + NB5)

**Gap:** NB3 (Synchronization) shows Pub/Sub → Dataflow → Bigtable as pseudocode. This needs to be real, executable code — not reference patterns.

**Plan:**
- NB3: Replace the pseudocode Beam pipeline with an executable pattern. Options:
  - Pub/Sub topic + subscription → Python subscriber that writes to Bigtable (simplest, runs in the notebook)
  - Pub/Sub → Cloud Function → Bigtable (serverless, deployable from notebook)
  - Pub/Sub → Dataflow (full production pattern — requires Dataflow job submission)
- NB5: The streaming section should also use real Pub/Sub messages, not simulated data. Create a topic, publish events, consume and write to Bigtable — all executable.
- Both notebooks should show the full loop: publish event → consume → write to Bigtable → read back → measure end-to-end latency

### Priority 4: Feature Validation & Data Quality

**Gap:** No notebook covers how to verify features were exported correctly or detect feature drift.

**Options:**
- A. Add validation sections to NB3 (post-export row count + sample verification) and NB7 (drift detection with Cloud Monitoring)
- B. Create a dedicated notebook

**Recommendation:** Option A — add validation cells to existing notebooks rather than creating a new one. Post-export verification is a natural fit for NB3. Feature drift monitoring fits NB7.

### Priority 5: Multi-Language Read Examples

**Gap:** All notebooks use Python. Teams with Go/Java/Node.js serving stacks can't directly use our patterns.

**Options:**
- A. Add `cbt` and GoogleSQL examples to NB1 (Fundamentals) alongside the Python reads
- B. Include language-specific read examples in the Serving Integration notebook (NB8)

**Recommendation:** Both. Quick `cbt`/GoogleSQL demos in NB1 show breadth. Deeper multi-language examples in NB8 serve production teams.

### Lower Priority (Nice to Have)

| Item | Where | Notes |
|------|-------|-------|
| Terraform/IaC for Bigtable provisioning | NB7 or dedicated section | Show `google_bigtable_instance` resource block |
| CI/CD testing patterns | NB7 | How to integration-test feature store pipelines |
| Bigtable emulator for local dev | NB0 or NB8 | `gcloud beta emulators bigtable start` |
| BigQuery external table reading from Bigtable | NB8 | Federated query: BQ → Bigtable |
| Materialized views in Bigtable | Future NB | GoogleSQL continuous materialized views |
| Feature store for embeddings / vector features | Future NB | Store and retrieve embedding vectors, compare with Vertex AI Feature Store's vector search |

---

## Execution Order

### Phase 1: Test & Verify (current)
1. Run NB0 → verify all resources created
2. Run NB1 → verify end-to-end flow
3. Run NB2-NB7 in any order → verify each independently
4. Fix any issues found during testing
5. Final review of markdown quality, flow, and readability

### Phase 2: Fill Gaps (COMPLETE)
1. ~~Build NB8 (Serving Integration) — the "so what" notebook~~ **DONE** (46 cells)
2. ~~Build NB9 (Dynamic Features) — real-time feature computation at serving time~~ **DONE** (47 cells)
3. ~~Fix NB3: replace pseudocode streaming pipeline with executable code~~ **DONE** (48→55 cells)
4. ~~Fix NB5: add real Pub/Sub event publishing + consumption (not simulated)~~ **DONE** (63→70 cells)
5. ~~Add `cbt`/GoogleSQL read examples to NB1~~ **DONE** (41→48 cells)
6. ~~Add post-export validation cells to NB3~~ **DONE** (included in #3)
7. ~~Add feature drift monitoring cells to NB7~~ **DONE** (50→56 cells, includes BQ ML validation functions)
8. ~~Update readme.md with NB8 and NB9 entries~~ **DONE**

### Phase 3: Polish
1. Run full series end-to-end one more time
2. Review all markdown for clarity, scannability, and consistency
3. Ensure every concept links to documentation
4. Final commit
