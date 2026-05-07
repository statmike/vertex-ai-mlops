# Bigtable Feature Store — Plans & Status

> Last updated: 2026-05-07

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
| 0 | Environment | 42 (23 md, 19 code) | 52 KB | **Built + tested** — label column with learnable signal, ~5% NULLs on 5 columns, `list_clusters()` fix |
| 1 | Fundamentals | 48 (25 md, 23 code) | 49 KB | **Built + cbt/GoogleSQL/BQ reads** |
| 2 | Serialization | 58 (24 md, 34 code) | 78 KB | **Built** |
| 3 | Synchronization | 55 (26 md, 29 code) | 67 KB | **Built + executable streaming + validation** |
| 4 | History and Time Travel | 60 (35 md, 25 code) | 59 KB | **Built** — TTL/freshness section added |
| 5 | Streaming and Direct Writes | 70 (37 md, 33 code) | 75 KB | **Built + Pub/Sub demo** |
| 6 | Key Design and Organization | 63 (30 md, 33 code) | 69 KB | **Built** |
| 7 | Schema Evolution and Operations | 60 (32 md, 28 code) | 76 KB | **Built + drift monitoring + BQ ML validation + NB8 cross-ref + Security/IAM + autoscaling** |
| 8 | Serving Integration | 53 (26 md, 27 code) | 42 KB | **Built + tested** — real label, 5 read methods, FastAPI, schema evolution Section 6 |
| 9 | Dynamic Features | 47 (23 md, 24 code) | 47 KB | **Built + tested** — 3 patterns, Pub/Sub streaming, combined serving |

---

## Testing & Verification Checklist

Run notebooks in this order. NB0 creates all shared resources; NB1 creates the first export and reservation; NB2-7 can run in any order after NB1 (each creates/cleans up its own resources).

### Pre-flight

- [ ] Ensure GCP project `statmike-mlops-349915` has billing enabled
- [ ] Ensure no leftover `feature-store` Bigtable instance from prior runs (or accept reuse)
- [ ] Ensure no leftover `bigtable_feature_store` BQ dataset (or accept reuse)
- [ ] Install kernel: `cd Bigtable && uv sync && uv run python -m ipykernel install --user --name bigtable-feature-store --display-name "Bigtable Feature Store"`

### NB0: Environment ✅

- [x] Restart & Run All completes without errors
- [x] BQ dataset `bigtable_feature_store` created
- [x] `dense_features` table: 130,000 rows, 224 columns (19 distinct data types)
- [x] `sparse_events` table: 2,600,000 rows, 5 event types (each ~20%)
- [x] Data investigation plots render (entity group distribution, daily volume, histograms)
- [x] Bigtable instance `feature-store` created (DEVELOPMENT, us-central1-a)
- [x] Bigtable table `features` created with column families: `features`, `metadata`
- [x] APIs enabled: bigquery, bigqueryreservation, bigquerydatatransfer, bigtable, bigtableadmin, pubsub, monitoring
- [x] `label` column: 30.5% positive / 69.5% negative — derived from `feature_int_1`, `feature_float_1`, `feature_float_3`, `feature_bool_1` with noise
- [x] NULL rates: ~5% on `feature_float_3`, `feature_float_4`, `feature_string_2`, `feature_date_2`, `feature_numeric_2`
- [x] Review: Bigtable architecture explanation reads clearly
- [x] Review: "Ways to Access Bigtable" section covers client libraries, SQL interfaces, CLI tools
- [x] Fix: `list_clusters()` returns tuple `(clusters, failed_locations)` — unpacked correctly

### NB1: Fundamentals ✅

- [x] Prerequisite check passes (finds BQ dataset + Bigtable instance from NB0)
- [x] BQ latency measurement works (SELECT on dense_features)
- [x] Enterprise reservation created successfully
- [x] App profile created via gcloud
- [x] EXPORT DATA completes — verify rows in Bigtable
- [x] `#schema` metadata row written and read back correctly
- [x] `decode_features()` function works on single-row read
- [x] Batch read returns DataFrame with correct values
- [x] Latency shootout: BQ vs Bigtable chart renders, Bigtable significantly faster
- [x] Native column mapping preview works
- [x] Cleanup: reservation and assignment deleted
- [x] Fix: cbt CLI and GoogleSQL read examples added
- [x] Fix: BigQuery external table (federated query) example added

### NB2: Serialization ✅

- [x] Prerequisite check passes
- [x] Reservation created (conditional 180s wait — skips if already exists)
- [x] 5 Bigtable tables created (features-native, features-json, features-concat, features-proto, features-hybrid)
- [x] Data type challenge: INFORMATION_SCHEMA query works, type classification table renders (203 BT-native, 21 complex)
- [x] Method 1 (Native): EXPORT DATA with individual columns, read-back works — all 222 features
- [x] Method 2 (JSON): TO_JSON_STRING export, read-back works — all 222 features
- [x] Method 3 (Concat): CONCAT export, delimiter trap discussion present — all 222 features
- [x] Method 4 (Protobuf): Dynamic protobuf schema generation, binary write, read-back with FileDescriptorSet — all 222 features
- [x] Method 5 (Hybrid): Native hot features + protobuf blob — all 222 features
- [x] Tax Analysis: storage size comparison, latency benchmark chart renders
- [x] Cleanup: reservation deleted, demo tables retained for later notebooks
- [x] Fix: compound row key (`entity_group#entity_id`) — original used single column causing collisions
- [x] Fix: `cast_sql()` helper — GEOGRAPHY uses `ST_ASTEXT()`, ARRAY/STRUCT/RANGE/JSON use `TO_JSON_STRING()`
- [x] Fix: CONCAT NULL propagation — `COALESCE(cast, '')` prevents NULL poisoning entire row
- [x] Fix: protobuf v6.x — `message_factory.GetMessageClass()` replaces removed `GetPrototype()`
- [x] Fix: TYPE_BYTES protobuf fields — `.encode('utf-8')` for string values
- [x] Fix: `_is_null()` helper — `pd.notna()` fails on list values from ARRAY columns
- [x] Fix: all 5 methods now serialize all 222 features (was 201 for non-JSON methods)

### NB3: Synchronization ✅

- [x] Prerequisite check passes
- [x] Reservation + app profile created (conditional 180s wait)
- [x] One-time EXPORT DATA completes, 130K rows verified in Bigtable
- [x] `overwrite = true` vs `overwrite = false` comparison — corrected (no upsert mode)
- [x] Scheduled query pattern (Data Transfer Service) — API call shown (not executed)
- [x] Orchestration alternatives section (Airflow/Composer, Cloud Scheduler, Workflows) present
- [x] Continuous query SQL with `APPENDS()` — shown as reference pattern, upsert semantics noted
- [x] Streaming pipeline: executable Pub/Sub → Bigtable demo (20 events published, pulled, written, verified, cleaned up)
- [x] Post-export validation: row count, sample check (10/10), schema row — all PASS
- [x] Propagation Race: test row inserted, EXPORT DATA in 1.6s, row verified in Bigtable
- [x] Cleanup: reservation and assignment deleted, no ongoing charges
- [x] Fix: `BT_COLUMN_FAMILY.encode()` → `BT_COLUMN_FAMILY` (string key, not bytes) in validation
- [x] Fix: `b'_values'` → `b'_schema'` for schema row column qualifier
- [x] Fix: `overwrite = false` → `overwrite = true` in propagation race (no upsert mode for EXPORT DATA)
- [x] Fix: corrected markdown framing — `overwrite = false` requires empty table, not upsert
- [x] Fix: continuous query SQL uses upsert semantics natively (no overwrite option)

### NB4: History and Time Travel ✅

- [x] Prerequisite check passes
- [x] Creates `features-history-key` table (key-based history design)
- [x] Creates `features-history-cell` table (cell versioning design)
- [x] Writes sample entities with timestamps to both tables
- [x] Key-based: prefix range scan works, `read_features_at_time_key_design()` works
- [x] Cell versioning: `CellsColumnLimitFilter(1)` returns latest, `TimestampRangeFilter` returns PIT
- [x] Point-in-time joins implemented for both designs
- [x] `ML.FEATURES_AT_TIME` and `ML.ENTITY_FEATURES_AT_TIME` BQ queries work
- [x] GC policy demo tables created and GC behavior demonstrated
- [x] Trade-off summary table present and clear
- [x] Cleanup: demo tables deleted

### NB5: Streaming and Direct Writes ✅

- [x] Prerequisite check passes
- [x] Creates `features-writes` table with `MaxVersionsGCRule(3)`
- [x] Single-row write + read-back works
- [x] Batch write (1,000 rows) completes, throughput measured
- [x] Atomic increment (`increment_cell_value`) works, concurrent test passes
- [x] Conditional write (`CheckAndMutateRow`) state transition works
- [x] Change streams section present (reference pattern — may not execute if not enabled)
- [x] Dual-write architecture diagrams present
- [x] Idempotency patterns documented
- [x] Cleanup: experiment table deleted

### NB6: Key Design and Organization ✅

- [x] Prerequisite check passes
- [x] Row key anatomy explanation with compound key format
- [x] Key distribution visualization renders (bar chart, pie chart)
- [x] Hotspot anti-patterns demonstrated with visualizations (timestamp, skewed, hash-only)
- [x] 4 key design patterns compared with distribution plots
- [x] Creates `features-key-design` table, writes 300 rows from BQ (100 per group: A, B, C)
- [x] Point reads, prefix scans, filtered scans, multi-row reads all work (4/4 keys found)
- [x] Latency comparison table: point read, prefix scan, filtered scan, multi-row read
- [x] Creates `features-multi-cf` table with 3 column families (features, metadata, streaming)
- [x] Selective reads per family demonstrated (features-only, metadata-only, full row)
- [x] GC policy demo: 7 versions written, 8 retained (GC not yet compacted), max 5 policy
- [x] Single table vs multi-table decision matrix present
- [x] Key Visualizer section (console URLs, simulated heatmaps for 3 patterns)
- [x] Cleanup: demo tables deleted
- [x] Fix: `BQ_SOURCE_TABLE_A` corrected from `'entity_features_dense'` to `'dense_features'`
- [x] Fix: `entity_id` format — already a zero-padded string, removed `:06d` int format spec
- [x] Fix: balanced per-group query using `ROW_NUMBER()` window function (was `LIMIT 300` returning only group A)

### NB7: Schema Evolution and Operations ✅

- [x] Prerequisite check passes
- [x] Versioned schema rows (`#schema#v1`, `#schema#v2`, `#schema#current`) written and read
- [x] Schema upgrade and rollback demonstrated
- [x] Adding features: v1 → v2 with backward-compatible decoder
- [x] Removing features: deprecated metadata, decoder skips deprecated columns
- [x] Backfill: reads existing rows, batch-appends new features (using isolated `backfill_*` demo rows)
- [x] Cloud Monitoring queries execute (248 requests: 223 ReadRows, 25 MutateRows, CPU 1.4-1.9%)
- [x] App profiles: created via gcloud, priority levels explained
- [x] Cost estimation: conceptual breakdown (storage footprint, node-hour scenarios), no dollar amounts
- [x] Production readiness checklist (20+ items)
- [x] Cleanup: 214 demo rows (`backfill_*`) + 2 app profiles deleted
- [x] Data validation: ML.DESCRIBE_DATA works, ML.VALIDATE_DATA_DRIFT clean (JSD < 0.001)
- [x] Drift detection: all 5 features OK (shift < 0.06σ)
- [x] NB8 cross-reference cell added (points to NB8 Section 6)
- Pre-test fixes applied:
  - Fix: schema V1/V2/V3 column order reordered to match NB1 EXPORT DATA order (5 INT64 then 5 FLOAT64)
  - Fix: demo row value generation reordered to match schema column order
  - Fix: backfill redesigned to use dedicated `backfill_*` rows — zero side effects on shared serving data
  - Fix: cleanup deletes `backfill_*` rows via batched `mutate_rows()`
  - Fix: ML.DESCRIBE_DATA — removed invalid `categorical_default_threshold` param
  - Fix: ML.VALIDATE_DATA_SKEW — changed to reference pattern (requires trained BQML model)
  - Fix: cost analysis — removed specific dollar amounts, restructured to conceptual tables with pricing page link
  - Design: production schema evolution during live serving deferred to NB8 (see NB7↔NB8 cross-reference in Priority 1)

### NB9: Dynamic Features ✅

- [x] Prerequisite check passes (Bigtable instance from NB0)
- [x] Creates `features-dynamic` table with 3 column families (counters, aggregates, metadata)
- [x] 10 entities seeded with baseline features
- [x] Pattern 1 — Read-Modify-Write: atomic increment 100→101, 100 rapid increments at 6.6ms mean
- [x] Counter decay: windowed reads with TimestampRangeFilter, 3 events in 30-min window (correct)
- [x] Pattern 2 — Read+Compute: 5.6ms mean, amount_vs_avg ratio computed at serve time
- [x] Pattern 3 — Streaming Aggregation: 50 events published to Pub/Sub, 50 pulled and processed, all 10 entities updated
- [x] Latency comparison charts render (event-time vs serve-time)
- [x] Combined serving: single read → counter + aggregate + derived features, 9.2ms total
- [x] Cleanup: table, subscription, topic all deleted
- Fixes applied:
  - Fix: windowed event spacing changed from 10min to 12min — avoids inclusive boundary at exactly 30min
  - Fix: Pub/Sub pull retry loop — pulls up to 5 times with 3s waits to collect all messages

### NB8: Serving Integration ✅

- [x] Prerequisite check passes (BQ dataset + Bigtable data from NB0/NB1)
- [x] Model trained on real `label` column from `dense_features` (70/30 split, 81.2% accuracy)
- [x] Single-entity read+predict: 7.6ms read, 14.4ms total, proper two-class probabilities
- [x] Batch predictions: 50 entities, mean read 7.5ms, mean total 13.6ms
- [x] Latency charts render (stacked bar + histogram)
- [x] 5 read methods demonstrated: Python client, cbt CLI, GoogleSQL, BQ external table, REST/gRPC
- [x] BQ external table: created and queried via UNNEST(features.column)
- [x] FastAPI serving endpoint: /predict and /health, runs on background thread
- [x] 10 prediction requests with realistic probability mix (0s and 1s)
- [x] 100 concurrent requests: wall p50=145ms, server-side read p50=6.9ms
- [x] Schema evolution during live serving (Section 6): 60 requests, 0 errors across 3 phases
- [x] Latency flat during migration: baseline 11.0ms → migration 11.1ms → post-switch 11.3ms
- [x] Cleanup: 50 backfilled rows restored, versioned schema rows deleted, external table dropped
- Fixes applied:
  - Fix: synthetic label `feature_float_1 + feature_float_2 > 1.0` always true — switched to real `label` column from NB0
  - Fix: `CAST(label AS INT64)` fails on string "positive" — use `CASE WHEN label = 'positive' THEN 1 ELSE 0 END`
  - Fix: `predict_proba` single-class IndexError — robust probability display with `join()`
  - Fix: BQ external table query — `features._values` doesn't exist, use `UNNEST(features.column) AS col WHERE col.name = '_values'`

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

> **Status:** Priorities 1–5 are complete (built in Phase 2). Priority 6 (TTL) is complete (built in Phase 4).

### ~~Priority 1: Serving Integration Notebook (NB8)~~ ✅ COMPLETE

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

**NB7↔NB8 Cross-Reference: Production Schema Evolution During Live Serving**

NB7 teaches schema evolution mechanics (versioned schemas, backward-compatible decoders, backfill) using isolated demo rows (`backfill_*` prefix) so it has zero side effects on shared serving data. But this design intentionally skips the hardest production problem: coordinating schema changes with data changes while a serving layer is actively reading features. The timing gap — when the schema says "v2" but some rows still have v1 data — is where production incidents happen.

NB8 should include a section that demonstrates this coordination:
- A running serving endpoint reads features from Bigtable
- Schema evolves (v1 → v2) while the endpoint is live
- Backfill runs against real serving data (not isolated demo rows)
- Show what happens when the decoder encounters mixed v1/v2 rows during the transition
- Demonstrate the backward-compatible decoder's resilience (trailing fields ignored)
- Measure: does serving latency or accuracy degrade during the migration window?

NB7 should cross-reference NB8 for this topic: "For production schema migration during live serving, see NB8 Section X." NB8 should cross-reference NB7 for the mechanics: "For schema versioning fundamentals, see NB7 Sections 2-4."

### ~~Priority 2: Serving with Dynamic Feature Computation (NB9)~~ ✅ COMPLETE

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

### ~~Priority 3: Executable Streaming Pipeline (fix NB3 + NB5)~~ ✅ COMPLETE

**Gap:** NB3 (Synchronization) shows Pub/Sub → Dataflow → Bigtable as pseudocode. This needs to be real, executable code — not reference patterns.

**Plan:**
- NB3: Replace the pseudocode Beam pipeline with an executable pattern. Options:
  - Pub/Sub topic + subscription → Python subscriber that writes to Bigtable (simplest, runs in the notebook)
  - Pub/Sub → Cloud Function → Bigtable (serverless, deployable from notebook)
  - Pub/Sub → Dataflow (full production pattern — requires Dataflow job submission)
- NB5: The streaming section should also use real Pub/Sub messages, not simulated data. Create a topic, publish events, consume and write to Bigtable — all executable.
- Both notebooks should show the full loop: publish event → consume → write to Bigtable → read back → measure end-to-end latency

### ~~Priority 4: Feature Validation & Data Quality~~ ✅ COMPLETE

**Gap:** No notebook covers how to verify features were exported correctly or detect feature drift.

**Options:**
- A. Add validation sections to NB3 (post-export row count + sample verification) and NB7 (drift detection with Cloud Monitoring)
- B. Create a dedicated notebook

**Recommendation:** Option A — add validation cells to existing notebooks rather than creating a new one. Post-export verification is a natural fit for NB3. Feature drift monitoring fits NB7.

### ~~Priority 5: Multi-Language Read Examples~~ ✅ COMPLETE

**Gap:** All notebooks use Python. Teams with Go/Java/Node.js serving stacks can't directly use our patterns.

**Options:**
- A. Add `cbt` and GoogleSQL examples to NB1 (Fundamentals) alongside the Python reads
- B. Include language-specific read examples in the Serving Integration notebook (NB8)

**Recommendation:** Both. Quick `cbt`/GoogleSQL demos in NB1 show breadth. Deeper multi-language examples in NB8 serve production teams.

### ~~Priority 6: TTL for Feature Values~~ ✅ COMPLETE

Implemented in Phase 4 (Option B — integrate throughout):
- **NB4**: TTL & Feature Freshness section after GC policies — `MaxAgeGCRule` vs application-level `_last_updated`, freshness demo code, patterns table
- **NB8**: Feature Freshness subsection in Production Patterns — `predict_with_freshness()` reference pattern
- Cross-references between NB4 and NB8 in both directions

### Lower Priority (Nice to Have)

| Item | Where | Status | Notes |
|------|-------|--------|-------|
| Terraform/IaC for Bigtable provisioning | NB7 or dedicated section | Pending | Show `google_bigtable_instance` resource block |
| CI/CD testing patterns | NB7 | Pending | How to integration-test feature store pipelines |
| Bigtable emulator for local dev | NB0 or NB8 | Phase 5 | `gcloud beta emulators bigtable start` |
| ~~BigQuery external table reading from Bigtable~~ | NB8 | **Done** | Federated query: BQ → Bigtable (Section 3d) |
| Materialized views in Bigtable | Future NB | Pending | GoogleSQL continuous materialized views |
| Feature store for embeddings / vector features | Future NB | Phase 5 | Store and retrieve embedding vectors, compare with Vertex AI Feature Store's vector search |

---

## Execution Order

### Phase 1: Test & Verify (COMPLETE)
1. ~~Run NB0 → verify all resources created~~ **DONE** — label + NULLs added, `list_clusters` fix
2. ~~Run NB1 → verify end-to-end flow~~ **DONE** — cbt/GoogleSQL/BQ federated reads added
3. ~~Run NB2 → verify all 5 serialization methods~~ **DONE** — compound row key, cast_sql, NULL handling, protobuf v6 fixes, all 222 features across all methods
4. ~~Run NB3 → verify synchronization patterns~~ **DONE** — overwrite semantics corrected, validation cell fixed, Pub/Sub demo working
5. ~~Run NB4 → verify history and time travel~~ **DONE** — metric_1/2/3→feature_1/2/3 alias, TimestampRangeFilter API fix
6. ~~Run NB5 → verify streaming and direct writes~~ **DONE** — ConditionalRow API fix (set_cell with state= param, not set_cell_on_true/false)
7. ~~Run NB6 → verify key design and organization~~ **DONE** — table name fix (entity_features_dense→dense_features), entity_id format fix (already zero-padded string, not int), balanced per-group query for multi-group demos
8. ~~Run NB7 → verify schema evolution and operations~~ **DONE** — ML.DESCRIBE_DATA fix, cost analysis conceptual restructure, NB8 cross-ref added
7. ~~Run NB8 → verify serving integration~~ **DONE** — label fix (use real label column), BQ external table UNNEST fix, predict_proba robustness
8. ~~Run NB9 → verify dynamic features~~ **DONE** — windowed event spacing fix, Pub/Sub pull retry loop
9. ~~Fix any issues found during testing~~ **DONE** — all fixes applied during testing
10. Final review of markdown quality, flow, and readability

### Phase 2: Fill Gaps (COMPLETE)
1. ~~Build NB8 (Serving Integration) — the "so what" notebook~~ **DONE** (46 cells)
2. ~~Build NB9 (Dynamic Features) — real-time feature computation at serving time~~ **DONE** (47 cells)
3. ~~Fix NB3: replace pseudocode streaming pipeline with executable code~~ **DONE** (48→55 cells)
4. ~~Fix NB5: add real Pub/Sub event publishing + consumption (not simulated)~~ **DONE** (63→70 cells)
5. ~~Add `cbt`/GoogleSQL read examples to NB1~~ **DONE** (41→48 cells)
6. ~~Add post-export validation cells to NB3~~ **DONE** (included in #3)
7. ~~Add feature drift monitoring cells to NB7~~ **DONE** (50→56 cells, includes BQ ML validation functions)
8. ~~Update readme.md with NB8 and NB9 entries~~ **DONE**

### Phase 3: Polish (IN PROGRESS)
1. Run full series end-to-end one more time
2. Review all markdown for clarity, scannability, and consistency
3. ~~Fix broken cross-reference links in NB1~~ **DONE** — 4 links corrected
4. ~~Add cross-references between related notebooks~~ **DONE** — NB3↔NB5, NB4→NB7, NB5→NB9, NB6→NB2, NB9→NB1/NB5/NB8
5. ~~Add missing documentation links~~ **DONE** — autoscaling, IAM, connection pooling, retry/timeout, row key best practices
6. Final commit

### Phase 4: Short-term Content Additions ✅ COMPLETE
Enterprise-grade gaps identified during testing. Added as sections within existing notebooks.

1. ~~**TTL / Feature Freshness** (NB4 + NB8)~~ ✅
   - NB4: Added TTL & Feature Freshness section after GC policies — `MaxAgeGCRule` vs application-level `_last_updated`, freshness demo code, patterns table
   - NB8: Added Feature Freshness subsection to Production Patterns — `predict_with_freshness()` reference pattern, cross-reference to NB4
   - NB4↔NB8 cross-references in both directions

2. ~~**Security & IAM** (NB7)~~ ✅
   - Added Section 8: Security and IAM — IAM roles table (`reader`/`user`/`admin`), read-only `get-iam-policy` cell, reference gcloud commands, network security (VPC SC, CMEK)
   - Production Readiness Checklist renumbered to Section 9 with dedicated Security subsection

3. ~~**Autoscaling & Capacity Planning** (NB7)~~ ✅
   - Expanded autoscaling subsection in Section 7 — capacity planning table, QPS estimation formula, dev instance note, storage-target parameter
   - Link to autoscaling documentation

4. ~~**Topic-to-Notebook Map** (readme.md)~~ ✅
   - Added Topic Map section with 16 topics mapped to relevant notebooks
   - Updated Notebook Comparison table entries for NB4, NB7, NB8

### Phase 5: Longer-term Content
These require new notebooks or significant additions. Lower urgency — the 10-notebook series is complete without them.

1. **Final Project: Real-time Recommendation Engine**
   - New notebook that ties the entire series together: a mini-recommendation system using all patterns
   - User features in Bigtable (batch-synced from BQ), item features (direct writes), interaction counts (atomic increments)
   - Serving endpoint that reads user features + item features + real-time signals → produces ranked recommendations
   - End-to-end latency measurement: feature read + model inference + response
   - Uses: NB0 data, NB1 export, NB2 serialization, NB5 streaming writes, NB6 key design, NB8 serving, NB9 dynamic features

2. **Embeddings & Vector Features**
   - New notebook covering embedding storage and retrieval in Bigtable
   - Store embedding vectors as serialized payloads (protobuf, binary, base64)
   - Nearest-neighbor search patterns: brute-force scan vs pre-computed ANN indices
   - Comparison with Vertex AI Feature Store's built-in vector search capabilities
   - Use case: product embeddings for similarity-based recommendations

3. **Bigtable Emulator for Local Development**
   - Add section to NB0 (Environment): `gcloud beta emulators bigtable start` for local testing
   - Show how to run notebook cells against the emulator vs production
   - Useful for CI/CD pipelines that can't connect to a live Bigtable instance

4. **Multi-Region Replication**
   - Expand NB7 with replication topology patterns (single-cluster, multi-cluster, cross-region)
   - Consistency models: eventual vs strong consistency with single-cluster routing
   - Failover testing: simulate cluster failure, verify reads still work via multi-cluster routing
