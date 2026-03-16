![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Fdata%2Bai%2Fdataflow%2Fgpu%2Fbenchmark&file=README.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/data%2Bai/dataflow/gpu/benchmark/README.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/dataflow/gpu/benchmark/README.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/dataflow/gpu/benchmark/README.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/dataflow/gpu/benchmark/README.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/dataflow/gpu/benchmark/README.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
</table><br/><br/>

---
# GPU Inference Benchmark: Local GPU vs Vertex AI Endpoint

> **Goal:** Determine the optimal infrastructure configuration to serve **1000 messages/second** with **< 750ms p99 latency** for BERT text classification, comparing Local GPU (Dataflow) vs Vertex AI endpoint approaches across T4 and L4 GPUs.

Fair comparison of two Dataflow streaming pipelines for BERT text classification:

- **Exp A (Local GPU)**: Model runs on the Dataflow worker's GPU via `LocalGPUHandler`
- **Exp B (Vertex AI)**: Model served via a Vertex AI endpoint (GPU) via `VertexAIHandler`

Both experiments use **identical pipeline code** — only the `ModelHandler` passed to `RunInference` differs.

**Results:** Each benchmark run produces a full report with charts and cost analysis. See the [Benchmark Report](reports/benchmark_report.md) for the complete results with drill-through analysis.

## Architecture

```
Pub/Sub (input) → Decode → RunInference(KeyedModelHandler(handler)) → FormatResult → Pub/Sub (output)
```

The handler is the only variable. Everything else — transforms, batching, message format, latency measurement — is the same. The pipeline is defined in [`benchmark/pipeline.py`](benchmark/pipeline.py).

### Fairness Guarantees

| Parameter | Exp A (Local GPU) | Exp B (Vertex AI) | Source |
|---|---|---|---|
| Pipeline code | Identical | Identical | [`benchmark/pipeline.py`](benchmark/pipeline.py) |
| RunInference | `KeyedModelHandler` | `KeyedModelHandler` | [`pipeline.py:86`](benchmark/pipeline.py#L86) |
| ModelHandler | `LocalGPUHandler` | `VertexAIHandler` | [`benchmark/handlers.py`](benchmark/handlers.py) |
| DF machine type | From `.env` (GPU-specific) | `n1-standard-4` (forced) | `.env`, [`run_benchmark.py`](scripts/run_benchmark.py) |
| GPU | Per `.env` (on worker) | Per `.env` (on Vertex endpoint) | `.env` |
| FP16 | Yes (`.half()`) | Yes (`.half()`) | [`handlers.py:47`](benchmark/handlers.py#L47), [`serve.py`](serve.py) |
| Custom container | Same image | Same image | `.env` |
| `latency_ms` | `processed_time - publish_time` | Same | [`pipeline.py:54`](benchmark/pipeline.py#L54) |
| `pure_inference_time_ms` | `time.perf_counter` in model forward | Same (returned in endpoint JSON) | [`model.py:38-44`](benchmark/model.py#L38) |

## Capacity Planning: Phased Approach

The benchmark uses an 8-phase approach to systematically determine the infrastructure needed for a target throughput (default: 1000 msg/s at p99 < 750ms). Each phase isolates one variable, building on the previous phase's findings. The orchestrator (`run_all_phases.py`) tracks the best settings discovered in each phase and carries them forward automatically.

### Selection Criteria

A configuration is considered "healthy" if it meets **both** criteria:
- **Processing throughput** >= 90% of the target rate
- **p99 latency** < 750ms (configurable via `--target-p99-ms`)

At equal healthy rates, the configuration with the lowest **p99** (tail latency) is preferred. This directly aligns with the stated goal — a config with p50=49ms but p99=2000ms would fail; a config with p50=100ms but p99=400ms would pass.

### Phase 1: Baseline Capacity Sweep

**Goal:** Find each approach's per-worker saturation point with default settings.

**Design:** Run both experiments on 1 Dataflow worker with default harness threads (12) and default batch settings. Sweep publish rates from well-below to well-above expected capacity. The rate where latency spikes marks the saturation point.

**What to look for:** A sudden latency inflection — typically 10–50x jump in p50 over a single rate step. This indicates the pipeline can no longer keep up with incoming messages.

| Setting | Value | Notes |
|---|---|---|
| Experiments | `local_gpu`, `vertex_ai` | Both run in parallel |
| Dataflow workers | 1 | Single worker baseline |
| Harness threads | 12 (Dataflow default) | Not yet tuned |
| max_batch_size | 64 (handler default) | Not yet tuned |
| min_batch_size | 1 (default) | Not yet tuned |
| Worker machine | from `.env` | e.g. `n1-standard-4` |
| Endpoint replicas | 1 | Fair single-replica baseline |
| **Swept: publish rate** | **25, 50, 75, 100, 125, 150 msg/s** | `--rates` |
| Duration per rate | 100s | `--duration` |

**Settings carried forward:** None — Phase 1 is observational only.

```bash
uv run python scripts/run_all_phases.py --phases 1
```

### Phase 2: Thread Count Sweep

**Goal:** Find the optimal [`--number_of_worker_harness_threads`](https://cloud.google.com/dataflow/docs/pipeline-options#streaming_engine_options) per experiment.

**Design:** Dataflow streaming defaults to 12 harness threads per worker. For Local GPU, all threads compete for a single GPU via [`_gpu_lock`](benchmark/handlers.py#L42) — fewer threads may reduce contention. For Vertex AI, each thread is an independent HTTP client — fewer threads may limit concurrency.

**Key insight:** The two experiments may need *different* thread counts. The orchestrator picks the best thread count independently for each experiment and carries it forward.

| Setting | Value | Notes |
|---|---|---|
| Experiments | `local_gpu`, `vertex_ai` | Both run per thread count |
| Dataflow workers | 1 | |
| max_batch_size | 64 (handler default) | Not yet tuned |
| min_batch_size | 1 (default) | Not yet tuned |
| Worker machine | from `.env` | |
| Endpoint replicas | 1 | |
| **Swept: harness threads** | **1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12** | `--thread-sweep` |
| Rates per sweep point | 25, 50, 75, 100, 125, 150 msg/s | Same as Phase 1 |
| Total runs | 12 (one per thread count) | |

**Settings carried forward:** `best["threads_local_gpu"]`, `best["threads_vertex_ai"]` — independently selected per experiment.

```bash
uv run python scripts/run_all_phases.py --phases 2
# Or with custom sweep:
uv run python scripts/run_all_phases.py --phases 2 --thread-sweep 1 2 3 4 6 8 12
```

### Phase 3: max_batch_size Sweep

**Goal:** Find optimal `max_batch_size` for each experiment with thread counts fixed from Phase 2.

**Design:** Apache Beam's `RunInference` batches elements before calling `run_inference()`. The [`batch_elements_kwargs`](benchmark/handlers.py#L91) method controls `min_batch_size` and `max_batch_size`. Since batch size is set at pipeline construction, each value requires a fresh pipeline launch. Too-small batches add per-batch GPU overhead; too-large batches add queuing delay while waiting to fill.

| Setting | Value | Notes |
|---|---|---|
| Experiments | `local_gpu`, `vertex_ai` | Both run per batch size |
| Dataflow workers | 1 | |
| Harness threads | from Phase 2 | Per-experiment best |
| min_batch_size | 1 (default) | Not yet tuned |
| Worker machine | from `.env` | |
| Endpoint replicas | 1 | |
| **Swept: max_batch_size** | **64, 96, 128, 160, 192, 224, 256** | `--batch-sizes` (32-step from 64) |
| Rates per sweep point | 75, 100, 125 msg/s | `--batch-sweep-rates` |
| Total runs | 7 (one per batch size) | |

**Settings carried forward:** `best["max_batch_local_gpu"]`, `best["max_batch_vertex_ai"]`.

```bash
uv run python scripts/run_all_phases.py --phases 3
```

### Phase 4: min_batch_size Sweep

**Goal:** Test whether forcing Beam to accumulate larger batches before inference improves throughput.

**Design:** With `min_batch_size=1` (default), Beam fires inference as soon as any element is ready, producing small batches under low load. Setting `min_batch_size=8` forces Beam to accumulate at least 8 elements, reducing GPU kernel launches but adding queuing delay.

| Setting | Value | Notes |
|---|---|---|
| Experiments | `local_gpu`, `vertex_ai` | Both run per min_batch |
| Dataflow workers | 1 | |
| Harness threads | from Phase 2 | Per-experiment best |
| max_batch_size | from Phase 3 | Per-experiment best |
| Worker machine | from `.env` | |
| Endpoint replicas | 1 | |
| **Swept: min_batch_size** | **1, 4, 8, 16, 32, 64, 96, ..., max_batch-1 (by 32 after 32)** | `--min-batch-sizes` (auto from Phase 3) |
| Rates per sweep point | 75, 100, 125 msg/s | `--batch-sweep-rates` |
| Total runs | ~10 (depends on Phase 3 max_batch) | e.g. max_batch=256 → 11 values |

**Settings carried forward:** `best["min_batch_local_gpu"]`, `best["min_batch_vertex_ai"]`.

```bash
uv run python scripts/run_all_phases.py --phases 4
```

### Phase 5: Machine Type Sweep

Two sub-phases isolating the **Dataflow worker machine** (5a) and the **Vertex AI endpoint machine** (5b).

#### Phase 5a: Dataflow Worker Machine Sweep

**Goal:** Test whether bigger worker machines (more CPU/memory) improve per-worker capacity.

**Design:** The pipeline's CPU-side work (tokenization, Pub/Sub I/O, Beam scheduling) may benefit from more CPU cores or memory bandwidth. Compare the default machine type from `.env` against a 2x variant (e.g., `n1-standard-4` vs `n1-standard-8`). All tuning from Phases 2–4 is applied. GPU-optimized families (G2, A2, A3) are automatically converted to the N1 equivalent preserving vCPU count for Vertex AI Dataflow workers (e.g., `g2-standard-8` → `n1-standard-8`) since they require `onHostMaintenance=TERMINATE`.

| Setting | Value | Notes |
|---|---|---|
| Experiments | `local_gpu`, `vertex_ai` | Both run per machine type |
| Dataflow workers | 1 | |
| Harness threads | from Phase 2 | Per-experiment best |
| max_batch_size | from Phase 3 | Per-experiment best |
| min_batch_size | from Phase 4 | Per-experiment best |
| Endpoint replicas | 1 | |
| **Swept: worker machine type** | **e.g. `n1-standard-4`, `n1-standard-8`** | `--machine-types` (auto: base + 2x vCPUs) |
| Rates per sweep point | 25, 50, 75, 100, 125, 150 msg/s | `--rates` |
| Total runs | 2 (one per machine type) | |

**Settings carried forward:** `best["machine_type"]` — best Dataflow worker machine.

```bash
uv run python scripts/run_all_phases.py --phases 5
# Or with explicit machine types:
uv run python scripts/run_all_phases.py --phases 5 --machine-types n1-standard-4 n1-standard-8
```

#### Phase 5b: Vertex AI Endpoint Machine Sweep

**Goal:** Test whether different endpoint replica machine types affect serving performance.

**Design:** While 5a tests the Dataflow *worker* machine, 5b tests the *endpoint* machine — the VM type running the model on Vertex AI replicas. For each machine type, the endpoint is scaled to 1 replica with that machine type via `scale_endpoint.py --machine-type`, then benchmarked at rates near capacity. The GPU accelerator (T4 or L4) stays the same; only the host machine (CPU/memory) changes.

| Setting | Value | Notes |
|---|---|---|
| Experiments | `vertex_ai` only | Endpoint machine only affects serving |
| Dataflow workers | 1 | |
| Harness threads | from Phase 2 | Vertex AI best |
| max_batch_size | from Phase 3 | Vertex AI best |
| min_batch_size | from Phase 4 | Vertex AI best |
| Endpoint replicas | 1 | Per machine type |
| **Swept: endpoint machine type** | **T4: `n1-standard-4`, `n1-standard-8`** | `--endpoint-machine-types` |
| | **L4: `g2-standard-4`, `g2-standard-8`** | (auto-derived from current endpoint) |
| Rates per sweep point | 75, 100, 125 msg/s | `--batch-sweep-rates` |
| Total runs | 2 (one per endpoint machine) | ~15 min scaling per change |

**Settings carried forward:** `best["endpoint_machine_type"]` — best endpoint machine.

```bash
uv run python scripts/run_all_phases.py --phases 5
# Or with explicit endpoint machine types:
uv run python scripts/run_all_phases.py --phases 5 --endpoint-machine-types n1-standard-4 n1-standard-8
```

### Phase 6: Re-tune on All Machine Types

**Goal:** Re-optimize thread count, max_batch_size, min_batch_size, and discover precise per-worker capacity **independently for each worker machine type** from Phase 5. This enables Phase 8 cost analysis to compare strategies like "10 × smaller machines" vs "5 × larger machines".

**Design:** Phase 6 loops over **all machine types** tested in Phase 5a (e.g., both `n1-standard-4` and `n1-standard-8`). For each machine type, four sequential sub-sweeps run in isolation, building on each other. If Phase 5b found a better endpoint machine, the endpoint is scaled to that machine before the loop begins. All sub-phases sweep the **full range** to avoid missing lower optima on any machine.

| Sub-phase | Swept setting | Levels | Fixed from prior | Output |
|---|---|---|---|---|
| **6a** | harness threads | 1..12 (full range) | Phase 5 machine + Phase 3 max_batch + Phase 4 min_batch | `phase6_retune/{mt}/threads/` |
| **6b** | max_batch_size | 64..256 by 32 (full range) | Phase 5 machine + **6a threads** + Phase 4 min_batch | `phase6_retune/{mt}/max_batch/` |
| **6c** | min_batch_size | 1..max_batch-1 (full range) | Phase 5 machine + **6a threads** + **6b max_batch** | `phase6_retune/{mt}/min_batch/` |
| **6d** | publish rate (capacity) | 50..325 by 25 msg/s (wide) | Phase 5 machine + **6a** + **6b** + **6c** | `phase6_retune/{mt}/capacity/` |

Phase 6d uses a **wide rate sweep** (default: 50–325 msg/s by 25) to discover the true per-worker saturation point, which may exceed the Phase 3/4 batch-sweep-rates max (125 msg/s). This produces a precise per-worker/per-replica capacity measurement that's used for proportional rate scaling in Phase 7.

| Setting | Value | Notes |
|---|---|---|
| Experiments | `local_gpu`, `vertex_ai` | Both run per sweep point |
| Dataflow workers | 1 | |
| Worker machines | **all from Phase 5a** | Loop: e.g., `n1-standard-4`, `n1-standard-8` |
| Endpoint machine | from Phase 5b | Scaled once before loop |
| Endpoint replicas | 1 | |
| Rates per sweep point | 75, 100, 125 msg/s (6a-6c); 50-325 (6d) | `--batch-sweep-rates`, `--capacity-sweep-rates` |
| Total runs | ~varies × num_machines | (6a: 12, 6b: ~7, 6c: ~10, 6d: ~12) × 2 machines |

**Settings carried forward:** Per-machine `threads_*`, `max_batch_*`, `min_batch_*`, `local_capacity`, and `vertex_capacity` in `best_per_machine` dict. Overall `best` updated from the highest-capacity machine.

```bash
uv run python scripts/run_all_phases.py --phases 6
# Custom capacity sweep range:
uv run python scripts/run_all_phases.py --phases 6 --capacity-sweep-rates 50 100 150 200 250 300
```

### Phase 7: Scale Verification

**Goal:** Verify the target throughput is achievable at calculated scale, with a full worker × replica × endpoint machine grid for Vertex AI.

**Design:** Three sub-phases, delegated to [`run_phase7_sweep.py`](scripts/run_phase7_sweep.py). All optimal settings (threads, batch sizes, worker machine) from Phases 2–6 are forwarded.

#### Phase 7a: Local GPU Worker Sweep (Per Machine Type)

Phase 7a runs **once per worker machine type** from Phase 6, using each machine's independently-tuned optimal settings and capacity.

| Setting | Value | Notes |
|---|---|---|
| Experiment | `local_gpu` only | |
| Harness threads | from Phase 6a | **Per-machine** best for local_gpu |
| max_batch_size | from Phase 6b | **Per-machine** best for local_gpu |
| min_batch_size | from Phase 6c | **Per-machine** best for local_gpu |
| **Worker machines** | **all from Phase 6** | e.g., both `n1-standard-4` and `n1-standard-8` |
| **Swept: worker count** | **T4: 1, 2, 3, 4** | `--local-gpu-workers` |
| | **L4: 1, 2, 4, 6, 8, 10** | |
| Rate per run | `local_capacity_per_machine × workers` msg/s | Proportional, per-machine capacity |
| Total runs | (T4: 4, L4: 6) × 2 machines | |

#### Phase 7b+c: Vertex AI Grid Search

Grouped by endpoint machine type (slow change, ~15 min), then by replica count (fast change, ~2-3 min), then by worker count (no endpoint change).

| Setting | Value | Notes |
|---|---|---|
| Experiment | `vertex_ai` only | |
| Harness threads | from Phase 6a | Best for vertex_ai |
| max_batch_size | from Phase 6b | Best for vertex_ai |
| min_batch_size | from Phase 6c | Best for vertex_ai |
| Worker machine | from Phase 5a | Dataflow worker machine |
| **Swept: endpoint machine** | **e.g. `n1-standard-4`, `n1-standard-8`** | `--endpoint-machine-types` |
| **Swept: endpoint replicas** | **1, 2, 5, 10** | `--vertex-ai-replicas` |
| **Swept: Dataflow workers** | **1, 2, 4, 8, 11** | `--vertex-ai-workers` |
| Rate per run | `vertex_capacity × replicas` (proportional, capped at `--vertex-ai-rate`) | `--vertex-ai-rate-per-replica` |
| Total runs | 2 machines × 4 replicas × 5 workers = **40** | |

**Output directories:** `phase7_scale/vertex_ai_{mt_short}/r{R}_w{W}/` — e.g. `vertex_ai_n1s4/r10_w8/`.

```bash
uv run python scripts/run_all_phases.py --phases 7
```

### Phase 8: Cost Analysis

**Goal:** Determine the cheapest infrastructure configuration that meets the target goal (1000 msg/s, p99 < 750ms).

**Design:** Reads all Phase 7 sweep results, filters to configurations that meet the throughput and latency criteria, computes $/hour using GCP pricing from `pricing.json`, and ranks by cost.

**Cost model:**
- **Local GPU:** `workers_needed × (worker_machine $/hr + GPU $/hr)`
- **Vertex AI:** `workers × worker_machine $/hr + replicas × (endpoint_machine $/hr + GPU $/hr)`

**Output:** `cost_analysis.json` with ranked configurations, and a comparison table printed to the console.

```bash
# Run cost analysis on existing Phase 7 results
uv run python scripts/cost_analysis.py --data-dir data/runs/my_run
# Customize target
uv run python scripts/cost_analysis.py --data-dir data/runs/my_run \
    --target-rate 1000 --target-p99-ms 750
```

Pricing is stored in [`pricing.json`](pricing.json) (us-central1, on-demand rates). Update this file before running to reflect current GCP pricing.

### Settings Carried Forward Summary

Each phase builds on prior results. The orchestrator loads saved `analysis.json` files when phases are skipped.

| Phase | Discovers | Carries forward |
|---|---|---|
| 1 | Saturation point | *(observational only)* |
| 2 | Best thread count | `threads_local_gpu`, `threads_vertex_ai` |
| 3 | Best max_batch | `max_batch_local_gpu`, `max_batch_vertex_ai` |
| 4 | Best min_batch | `min_batch_local_gpu`, `min_batch_vertex_ai` |
| 5a | Best worker machine | `machine_type` |
| 5b | Best endpoint machine | `endpoint_machine_type` |
| 6a | Re-tuned threads (per machine) | `best_per_machine[mt].threads_*` |
| 6b | Re-tuned max_batch (per machine) | `best_per_machine[mt].max_batch_*` |
| 6c | Re-tuned min_batch (per machine) | `best_per_machine[mt].min_batch_*` |
| 6d | Precise capacity (per machine) | `best_per_machine[mt].local_capacity`, `vertex_capacity` |
| 7 | Scale verification | *(final validation)* |
| 8 | Cost analysis | `cost_analysis.json` |

## Running the Benchmark

### Full Automated Run (All Phases)

A single command runs all 8 phases end-to-end. Each run gets its own timestamped directory under `data/runs/`, so previous results are never overwritten:

```bash
make benchmark-all
# Or directly:
uv run python scripts/run_all_phases.py
# Named run:
uv run python scripts/run_all_phases.py --run-name nightly_v2
# GPU-specific config:
uv run python scripts/run_all_phases.py --env-file .env.t4
# Dry run (print plan without executing):
uv run python scripts/run_all_phases.py --dry-run
```

The orchestrator automatically:
- Scales the Vertex AI endpoint to **1 replica** before Phases 1–6 (ensuring a fair single-replica baseline)
- Tracks the **best settings** from each phase and carries them forward (threads → batch sizes → machine type)
- Pins worker count (min=max) to prevent autoscaling during benchmarks
- Verifies all workers are active before starting each benchmark
- Uses **rawPredict** with dedicated endpoints by default (use `--no-raw-predict` to opt out)

### Individual Phases

```bash
# Run specific phases (orchestrator loads prior results for skipped phases)
uv run python scripts/run_all_phases.py --phases 1 2 3
uv run python scripts/run_all_phases.py --phases 4 5 6  # uses saved Phase 2-3 results

# Scale verification only
uv run python scripts/run_all_phases.py --phases 7
```

### Single Experiment Run

```bash
# Quick test
uv run python scripts/run_benchmark.py --count 1000 --rates 50

# Duration-based (100s per rate, preferred for consistent timing)
uv run python scripts/run_benchmark.py --duration 100 --rates 50 75 100

# Run only one experiment
uv run python scripts/run_benchmark.py --experiments local_gpu
uv run python scripts/run_benchmark.py --experiments vertex_ai

# Per-experiment tuning
uv run python scripts/run_benchmark.py \
    --duration 100 --rates 75 100 125 \
    --num_workers 1 \
    --harness_threads_local_gpu 2 \
    --max_batch_size_local_gpu 32 \
    --min_batch_size_local_gpu 8 \
    --machine_type n1-standard-8
```

### CLI Flags

**`run_all_phases.py`** (orchestrator):

| Flag | Description | Default |
|---|---|---|
| `--run-name` | Name for this run (directory under `data/runs/`) | `run_YYYYMMDD_HHMMSS` |
| `--phases` | Which phases to run | 1 2 3 4 5 6 7 8 |
| `--target-rate` | Target throughput in msg/s (for cost analysis) | 1000 |
| `--target-p99-ms` | Target p99 latency in ms (health criterion) | 750 |
| `--duration` | Seconds per rate phase | 100 |
| `--rates` | Rates for Phase 1/2 capacity sweep | 25 50 75 100 125 150 |
| `--thread-sweep` | Thread counts for Phase 2 | 1–12 (all integers) |
| `--batch-sizes` | max_batch_size values for Phase 3 | 64 96 128 160 192 224 256 |
| `--min-batch-sizes` | min_batch_size values for Phase 4 | auto (1..max_batch-1) |
| `--batch-sweep-rates` | Rates for Phase 3/4 sweeps | 75 100 125 |
| `--capacity-sweep-rates` | Rates for Phase 6d capacity refinement | 50 75 100 ... 300 325 |
| `--machine-types` | Worker machine types for Phase 5a | auto (from .env + 2x) |
| `--endpoint-machine-types` | Endpoint machine types for Phase 5b | auto (from endpoint + 2x) |
| `--local-gpu-workers` | Worker counts for Phase 7 Local GPU | 1 2 3 4 |
| `--vertex-ai-workers` | Worker counts for Phase 7 Vertex AI | 1 2 4 8 11 |
| `--vertex-ai-replicas` | Replica counts for Phase 7 Vertex AI grid | 1 2 5 10 |
| `--vertex-ai-rate` | Max rate for Phase 7 Vertex AI testing | 1000 |
| `--env-file` | Path to .env file | `.env` |
| `--raw-predict` / `--no-raw-predict` | Use `:rawPredict` for Vertex AI | True |
| `--clean` | Remove existing run directory first | false |
| `--dry-run` | Print plan without running | false |

**`run_benchmark.py`** (single run):

| Flag | Description | Default |
|---|---|---|
| `--duration` | Seconds per rate phase (count = rate × duration) | None (uses `--count`) |
| `--count` | Messages per rate phase (ignored if `--duration` set) | 100,000 |
| `--rates` | Publish rates in msg/s | 50 75 100 |
| `--num_workers` | Fixed worker count (disables autoscaling) | None (Dataflow default) |
| `--harness_threads` | Override thread count for all experiments | None (12 for streaming) |
| `--harness_threads_local_gpu` | Thread count for local_gpu only | None |
| `--harness_threads_vertex_ai` | Thread count for vertex_ai only | None |
| `--max_batch_size` | Max RunInference batch size for all | None (handler default: 64) |
| `--max_batch_size_local_gpu` | Max batch size for local_gpu only | None |
| `--max_batch_size_vertex_ai` | Max batch size for vertex_ai only | None |
| `--min_batch_size` | Min RunInference batch size for all | None (default: 1) |
| `--min_batch_size_local_gpu` | Min batch size for local_gpu only | None |
| `--min_batch_size_vertex_ai` | Min batch size for vertex_ai only | None |
| `--machine_type` | Override worker machine type | None (from `.env`) |
| `--raw_predict` / `--no_raw_predict` | Use `:rawPredict` for Vertex AI | True |
| `--experiments` | Which experiments to run | both |
| `--output_dir` | Results directory | `data` |
| `--timeout` | Collection timeout per rate (minutes) | 45 |

### Output Structure

Each `make benchmark-all` creates a self-contained run directory:

```
data/runs/
├── run_20260306_220000/        # auto-timestamped run
│   ├── phase1_capacity/        # Phase 1: baseline rate sweep
│   │   ├── results_{mode}_{rate}.json
│   │   ├── benchmark_results.json
│   │   ├── benchmark_report.md
│   │   └── charts/
│   ├── phase2_threads/         # Phase 2: thread count sweep
│   │   ├── threads_1/ ... threads_8/
│   │   └── analysis.json       # Best thread count per experiment
│   ├── phase3_max_batch/       # Phase 3: max_batch_size sweep
│   │   ├── batch_4/ ... batch_256/
│   │   └── analysis.json
│   ├── phase4_min_batch/       # Phase 4: min_batch_size sweep
│   │   ├── min_1/ ... min_32/
│   │   └── analysis.json
│   ├── phase5_machine/         # Phase 5a: worker machine comparison
│   │   ├── n1-standard-4/ n1-standard-8/
│   │   └── analysis.json
│   ├── phase5_endpoint/        # Phase 5b: endpoint machine sweep
│   │   ├── n1-standard-4/ n1-standard-8/  (or g2-standard-*)
│   │   └── analysis.json
│   ├── phase6_retune/          # Phase 6: per-machine re-tuning
│   │   ├── n1s4/              # Machine 1 (e.g., n1-standard-4)
│   │   │   ├── threads/       # 6a: thread re-sweep
│   │   │   ├── max_batch/     # 6b: max_batch re-sweep
│   │   │   ├── min_batch/     # 6c: min_batch re-sweep
│   │   │   ├── capacity/      # 6d: wide capacity sweep (50-325 msg/s)
│   │   │   │   └── rate_50/ rate_75/ ... rate_325/
│   │   │   └── analysis.json
│   │   ├── n1s8/              # Machine 2 (e.g., n1-standard-8)
│   │   │   └── (same structure)
│   │   └── analysis.json       # Combined analysis + per_machine dict
│   ├── phase7_scale/           # Phase 7: scale verification grid
│   │   ├── local_gpu_n1s4_1w/ ... local_gpu_n1s4_4w/   # Per-machine
│   │   ├── local_gpu_n1s8_1w/ ... local_gpu_n1s8_4w/
│   │   ├── vertex_ai_g2s4/    # Smaller endpoint machine
│   │   │   ├── r1_w1/ r1_w2/ ... r10_w11/
│   │   ├── vertex_ai_g2s8/    # Larger endpoint machine
│   │   │   ├── r1_w1/ r1_w2/ ... r10_w11/
│   │   └── sweep_summary.json
│   ├── cost_analysis.json      # Phase 8: cost ranking
│   ├── report_charts/          # Phase-specific visualizations
│   └── full_report.md          # Comprehensive cross-phase report
└── nightly_v2/                 # named run
    └── ...
```

## Prerequisites

1. A GCP project with billing enabled
2. APIs enabled: Dataflow, Pub/Sub, Vertex AI, Cloud Build, Cloud Storage
3. `gcloud` CLI authenticated
4. `uv` installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
5. Docker images built and pushed (see Setup below)
6. For Exp B: a Vertex AI endpoint deployed with the model

## Setup (One-Time)

```bash
# 1. Copy and configure environment
cp .env.template .env
# Edit .env with your project ID, bucket paths, etc.

# 2. Install dependencies
make init

# 3. Create Pub/Sub topics
make create-topics

# 4. Train model and generate test data
make train-model
make generate-data

# 5. Build container images
make build-worker    # Dataflow GPU worker (~15 min)
make build-serve     # Vertex AI serving (~10 min)

# 6. Deploy Vertex AI endpoint
make deploy-endpoint
# Follow the printed instructions, then update .env with
# VERTEX_ENDPOINT_ID and VERTEX_MODEL_ID
```

## Redeploying After Code Changes

Changes to `benchmark/handlers.py` or `benchmark/pipeline.py` are baked into the Docker container images. Vertex AI's model registry caches the container image, so a code change requires a full teardown and redeploy cycle:

```bash
# 1. Rebuild container images
make build-worker   # Dataflow GPU worker image
make build-serve    # Vertex AI serving image

# 2. Tear down and redeploy (per GPU config)
make redeploy       # Uses default .env
# Or for specific configs:
ENV_FILE=.env.t4 make redeploy
ENV_FILE=.env.l4 make redeploy

# 3. Follow the manual steps printed by `make redeploy`:
#    - Update .env with new VERTEX_ENDPOINT_ID and VERTEX_MODEL_ID
#    - Deploy model to endpoint
#    - Smoke test
```

The `make redeploy` target automates the teardown (undeploy model, delete endpoint, delete model) and re-upload (upload new model, create new endpoint), but the final deploy-model step requires manual execution to ensure correctness.

## Key Design Decisions

### Why a threading lock around GPU inference?

Dataflow streaming workers run multiple harness threads by default (12 for streaming). Without a lock, multiple threads call `model.forward()` concurrently, competing for the single T4 GPU. The lock in [`LocalGPUHandler._gpu_lock`](benchmark/handlers.py#L42) serializes GPU access while allowing CPU-side work (tokenization, result formatting) to remain parallel. See usage at [`handlers.py:72`](benchmark/handlers.py#L72).

This lock is the central reason why thread count matters so much: 12 threads contending for 1 lock creates catastrophic queuing, while 2 threads allow clean pipelining of CPU and GPU work. See the [Phase 2 thread tuning results](reports/benchmark_report.md) for the measured impact.

### Why duration-based testing?

Each rate phase runs for a fixed duration (default: 100 seconds) rather than a fixed message count. At 25 msg/s this means 2,500 messages; at 150 msg/s it means 15,000. This keeps wall-clock time consistent across rates and avoids extremely long runs at low rates (100k messages at 25 msg/s = 67 minutes).

### Why per-experiment Pub/Sub topics?

When running both experiments in parallel, each gets its own input/output topics (e.g., `benchmark-input-local-gpu`, `benchmark-input-vertex-ai`). If they shared topics, each experiment's subscription would receive *all* messages from both experiments, doubling throughput and corrupting latency measurements.

### Why `ReadFromPubSub(subscription=...)` instead of `topic=`?

`ReadFromPubSub(topic=...)` creates a temporary subscription that only receives messages published *after* the pipeline starts. Messages published before workers are ready are silently dropped. With `subscription=`, we create the subscription upfront and messages persist until consumed.

### Why warmup before benchmarking?

GPU workers take 5–15 minutes to become healthy (VM boot, container pull, NVIDIA driver install, model download from GCS, GPU warmup). The warmup phase sends messages and waits for output, confirming the full stack is ready before benchmark messages begin.

### Why pin worker count with `update-options`?

When `--num_workers` is set for benchmarking, the Beam SDK sets `--num_workers` (initial) and `--max_num_workers` (ceiling). But the Beam Python SDK has no `--min_num_workers` flag, so Streaming Engine's autoscaler defaults `minNumWorkers` to 1 — free to scale down from the initial count. We observed `minNumWorkers: 1, maxNumWorkers: 11` in a job where `--num_workers 11 --max_num_workers 11` were set, with only 4 workers active after the benchmark burst.

The fix uses `gcloud dataflow jobs update-options --min-num-workers=N --max-num-workers=N` immediately after the job enters RUNNING state to pin the count. After warmup, the benchmark verifies all workers are active by polling `CurrentVcpuCount` and `CurrentGpuCount` from `gcloud beta dataflow metrics list --source=service`. This ensures the benchmark doesn't start until the requested infrastructure is fully provisioned. See [`run_benchmark.py:449`](scripts/run_benchmark.py#L449).

### Why no retry/timeout on Vertex AI HTTP calls?

At scale, Vertex AI exhibits severe tail latency — some requests take 30–60 seconds when normal inference takes 5 ms. This is endpoint-side queuing: requests get stuck behind other requests on an overloaded replica. A natural fix is to set an HTTP timeout (e.g., 2 seconds) and retry on a different replica:

```python
# In VertexAIHandler.run_inference() — conceptual, not implemented
for attempt in range(max_retries + 1):
    try:
        resp = model.session.post(model.url, json=payload, timeout=2.0, ...)
        resp.raise_for_status()
        return parse_results(resp)
    except (requests.Timeout, requests.HTTPError):
        if attempt == max_retries:
            raise
```

We chose **not** to implement this because: (1) it changes the comparison — Local GPU has no retry mechanism, so adding one to Vertex AI would make the benchmark unfair; (2) retries increase total request volume to the endpoint, risking retry storms under sustained load; (3) the timeout threshold requires its own tuning. However, in a production deployment where Vertex AI tail latency is the primary concern, a **2-second timeout with max 2 retries** would likely cut p99 from 60s to under 5s. See the [Phase 7 scaling results](reports/benchmark_report.md) for the data motivating this option.

### Why rawPredict with dedicated endpoints by default?

Vertex AI offers two prediction methods: `:predict` (standard) and `:rawPredict` (bypasses pre/post-processing). For dedicated endpoints, `:rawPredict` sends requests directly to the endpoint's own DNS hostname, skipping the regional API proxy.

Phase 1 benchmarks on both T4 and L4 confirmed that dedicated endpoints with `:rawPredict` consistently outperform shared endpoints:
- Lower p50 latency at all rates (58ms vs 63ms at 50 msg/s)
- Higher saturation point (100+ msg/s vs ~75 msg/s per worker)
- More predictable tail latency under load

The benchmark defaults to `--raw_predict` (True). Use `--no_raw_predict` to fall back to the standard `:predict` path. Dedicated endpoint DNS is configured via `VERTEX_ENDPOINT_DNS` in `.env`.

### GPU-to-machine-family pairing

Each NVIDIA GPU is available only on a specific GCE machine family. You cannot mix GPUs across families:

| GPU | Machine Family | Example Type | CPU Architecture |
|---|---|---|---|
| T4 | N1 | `n1-standard-4` | Intel Skylake / Cascade Lake |
| L4 | G2 | `g2-standard-4` | Intel Sapphire Rapids |
| V100 | N1 | `n1-standard-8` | Intel Skylake / Cascade Lake |
| A100 | A2 | `a2-highgpu-1g` | Intel Cascade Lake |
| H100 | A3 | `a3-highgpu-1g` | Intel Sapphire Rapids |

This means **comparing two GPU types also changes the host CPU and memory subsystem**. For example, a T4 benchmark runs on N1 (Skylake) while an L4 benchmark runs on G2 (Sapphire Rapids). In practice the impact is minimal because GPU inference dominates wall-clock time (100–140 ms per batch vs single-digit ms for CPU-side tokenization), but readers should be aware that GPU results cannot be fully isolated from the host machine change.

For the **Vertex AI experiment**, the Dataflow workers don't use GPUs — they just send HTTP requests. The benchmark automatically converts GPU-optimized machine families (G2, A2, A3) to the N1 equivalent preserving the vCPU count (e.g., `g2-standard-8` → `n1-standard-8`). This is necessary because GPU-optimized families require `onHostMaintenance=TERMINATE`, which Dataflow only sets when a GPU accelerator is attached. Without GPU attachment, these machine families fail to schedule. This conversion is handled by `resolve_machine_type()` in [`run_benchmark.py`](scripts/run_benchmark.py). Since Vertex AI workers only perform HTTP calls (no tokenization, no inference), the CPU architecture difference has negligible impact on results.

The GPU-to-machine pairing is configured via separate `.env` files (`.env.t4`, `.env.l4`) that set both `MACHINE_TYPE` and `GPU_TYPE` together.

### Why the same custom container for both experiments?

The `benchmark` package imports `torch` and `transformers` at module level — even the `VertexAIHandler` path triggers these imports during Beam's deserialization. Using the same container ensures identical environments. Exp A gets a GPU attached via `--dataflow_service_option worker_accelerator=...`; Exp B uses the same container but without GPU attachment.

## Container Details

### Dataflow Worker (`Dockerfile.worker`)

Built from `nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04`:

1. Install Python 3.11 (must match submission environment)
2. Install PyTorch with CUDA support, Beam SDK, transformers
3. Copy the benchmark package
4. Copy the Beam boot launcher: `COPY --from=apache/beam_python3.11_sdk:2.71.0 /opt/apache/beam /opt/apache/beam`
5. Set entrypoint to `/opt/apache/beam/boot`

Required Dataflow flags:
- `--sdk_container_image <image> --sdk_location container`
- `--experiment use_runner_v2`
- `--experiment no_use_multiple_sdk_containers`
- `--dataflow_service_option "worker_accelerator=type:nvidia-tesla-t4;count:1;install-nvidia-driver"`

### Vertex AI Serving (`Dockerfile.serve`)

Flask app that loads the same `BertModelWrapper`, exposes `/predict` and `/health` endpoints. Returns `pure_inference_time_ms` per prediction using the same `time.perf_counter` measurement as local inference.

## Metrics

All metrics are computed from actual message attributes:

- **End-to-end latency** (`latency_ms`): `processed_time_ms - publish_time_ms`
- **Pure inference time** (`pure_inference_time_ms`): GPU kernel time from `BertModelWrapper.forward()` — same code path for both experiments
- **Throughput**: `message_count / (last_processed_time - first_publish_time)` — includes ramp-up
- **Processing throughput**: `message_count / (last_processed_time - first_processed_time)` — excludes ramp-up, better reflects sustained capacity
- **Queue wait** (`queue_wait_ms`): `inference_start_ms - publish_time_ms` — time in Pub/Sub + Beam queue before inference begins
- **Inference overhead** (`inference_overhead_ms`): `processed_time_ms - inference_start_ms` — tokenize + infer + format
- **Loss rate**: `1 - collected_count / published_count` — tracks silent message loss at saturation
- Percentiles: p50, p95, p99, mean

## Cost Comparison

| Factor | Local GPU (Exp A) | Vertex AI (Exp B) |
|---|---|---|
| Simpler architecture | Yes — single system | No — two systems |
| Lower cost (steady traffic) | Yes — no idle endpoint | No — endpoint always on |
| Model shared across services | No — coupled to pipeline | Yes — any client can call it |
| Independent scaling | No — GPU tied to worker | Yes — scale pipeline and model separately |
| Latency | Lower (no network hop) | Higher (HTTP round trip) |
| Tail latency at scale | Tight (see [Phase 7](reports/benchmark_report.md)) | Can be problematic |

Both approaches support model updates without pipeline restarts. Beam's `RunInference` supports [`WatchFilePattern`](https://beam.apache.org/documentation/ml/about-ml/#automatic-model-refresh) for hot-swapping model artifacts. Vertex AI achieves the same by deploying a new model version to the endpoint.

## Manual Runs

For debugging or running experiments individually:

```bash
# Terminal 1: Start pipeline
make run-exp-a   # or: make run-exp-b

# Terminal 2: Publish messages (start AFTER workers are healthy)
make publish

# After processing:
make cancel-job
make collect-a   # or: make collect-b
make compare
```

## Cleanup

```bash
make cleanup    # Deletes Pub/Sub topics/subs, Vertex AI endpoint + model
```

## File Structure

```
benchmark/
├── benchmark/                     # Python package (pipeline + handlers)
│   ├── __init__.py
│   ├── pipeline.py                # build_pipeline() with RunInference
│   ├── handlers.py                # LocalGPUHandler + VertexAIHandler
│   ├── model.py                   # BertModelWrapper + GCS download
│   └── run.py                     # Pipeline CLI entry point
├── scripts/
│   ├── run_all_phases.py          # Full multi-phase orchestrator
│   ├── run_benchmark.py           # Single-run benchmark orchestration
│   ├── run_phase7_sweep.py        # Phase 7 scale verification sweep
│   ├── cost_analysis.py           # Phase 8: cost analysis
│   ├── scale_endpoint.py          # Vertex AI replica scaling
│   ├── generate_report_charts.py  # Chart generation from results
│   ├── train_model.py             # Fine-tune DistilBERT
│   ├── generate_data.py           # Synthetic transactions
│   ├── publish.py                 # Manual Pub/Sub publisher
│   ├── collect.py                 # Manual result collector
│   └── cleanup.py                 # GCP resource teardown
├── data/
│   ├── test_transactions.txt      # Generated test data (100k lines)
│   └── runs/                      # Benchmark results (one dir per run)
│       ├── initial/               # Archived first run
│       └── run_YYYYMMDD_HHMMSS/   # Timestamped runs from benchmark-all
├── serve.py                       # Flask endpoint for Vertex AI
├── Dockerfile.worker              # Dataflow GPU worker (CUDA + Beam boot)
├── Dockerfile.serve               # Vertex AI serving
├── cloudbuild-worker.yaml         # Cloud Build config for worker image
├── cloudbuild-serve.yaml          # Cloud Build config for serve image
├── pricing.json                  # GCP pricing for cost analysis
├── Makefile
├── .env.template
├── setup.py
└── requirements.txt
```

---

**[View the Benchmark Report](reports/benchmark_report.md)** — Full results, cross-GPU comparison, cost analysis, and drill-through phase reports.
