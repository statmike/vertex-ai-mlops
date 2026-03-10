#!/usr/bin/env python3
"""Run all benchmark phases end-to-end (unattended overnight run).

Goal: Serve --target-rate msg/s (default 1000) at p99 < --target-p99-ms (default 750ms).
Selection: processing_throughput >= 90% of rate AND p99 < target. Tiebreaker: lowest p99.

Phase 1: Baseline capacity — default 12 threads, default batch (1–64)
         Rates: 25 50 75 100 125 150 msg/s, 1 worker, 100s per rate
         Vertex AI endpoint scaled to 1 replica for fair baseline
Phase 2: Thread count sweep — test multiple harness thread counts
         Threads: 1–12 (configurable)
         Pick best thread count per experiment (Local GPU vs Vertex AI)
Phase 3: max_batch_size sweep — threads fixed from Phase 2
         max_batch_size: 64..256 by 32
         Rates near saturation point
Phase 4: min_batch_size sweep — threads + max_batch fixed from Phase 2–3
         min_batch_size: 1, 4, 8, 16, 32, ...
         Tests whether forcing larger batches improves throughput
Phase 5: Machine type sweep
  5a: Dataflow worker machine sweep (standard-4 vs standard-8)
  5b: Vertex AI endpoint machine sweep (different GPU machine for replicas)
Phase 6: Re-tune on winning machines (FULL range sweeps)
  6a: Thread re-sweep (1..12, full range)
  6b: max_batch_size re-sweep (64..256, full range)
  6c: min_batch_size re-sweep (full range)
  6d: Capacity refinement (fine-grained rates near saturation)
Phase 7: Scale verification (worker × replica × endpoint machine grid)
  7a: Local GPU worker sweep (proportional rates)
  7b+c: Vertex AI grid — proportional rates per replica count
  (delegated to run_phase7_sweep.py)
Phase 8: Cost analysis and recommendations
  Reads Phase 7 results, filters to goal-meeting configs, computes $/hour

Output layout (each run gets its own directory):
  data/runs/<run_name>/
    phase1_capacity/              rate sweep with default settings
    phase2_threads/               thread count sweep
      threads_1/ threads_2/ ...   per-thread-count results
      analysis.json               best thread count per experiment
    phase3_max_batch/             max_batch_size sweep
      batch_64/ batch_96/ ...     per-batch results
      analysis.json
    phase4_min_batch/             min_batch_size sweep
      min_1/ min_4/ ...           per-min-batch results
      analysis.json
    phase5_machine/               5a: Dataflow worker machine comparison
      n1-standard-4/ n1-standard-8/
      analysis.json
    phase5_endpoint/              5b: Vertex AI endpoint machine sweep
      n1-standard-4/ n1-standard-8/  (or g2-standard-*)
      analysis.json
    phase6_retune/                re-tune on winning machines
      threads/ max_batch/ min_batch/ capacity/
      analysis.json
    phase7_scale/                 worker × replica × machine grid
      local_gpu_1w/ ... local_gpu_4w/
      vertex_ai_g2s4/ vertex_ai_g2s8/
      sweep_summary.json
    cost_analysis.json            Phase 8: cost ranking
    report_charts/
    full_report.md

Usage:
  uv run python scripts/run_all_phases.py                    # all phases
  uv run python scripts/run_all_phases.py --run-name nightly # named run
  uv run python scripts/run_all_phases.py --phases 1 2 3     # specific phases
  uv run python scripts/run_all_phases.py --dry-run          # show plan
  uv run python scripts/run_all_phases.py --target-rate 500 --target-p99-ms 500
"""

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime

# Default per-worker/per-replica capacity assumption (msg/s) used when
# prior phase data is unavailable.  Defined once to keep all fallback
# references consistent.
DEFAULT_CAPACITY = 100


def run_command(cmd, label, cwd=None):
    """Run a subprocess command, streaming output. Returns (success, elapsed_min)."""
    print(f"\n{'─' * 70}", flush=True)
    print(f"  {label}", flush=True)
    print(f"  $ {' '.join(cmd)}", flush=True)
    print(f"{'─' * 70}\n", flush=True)

    start = time.time()
    result = subprocess.run(cmd, cwd=cwd)
    elapsed = (time.time() - start) / 60

    success = result.returncode == 0
    status = "OK" if success else f"FAILED (exit {result.returncode})"
    print(f"\n  [{status}] {label} — {elapsed:.1f} min\n", flush=True)
    return success, elapsed


def scale_endpoint(replicas=None, env_file=".env", label=None, machine_type=None):
    """Scale Vertex AI endpoint replicas and/or change machine type."""
    cmd = ["uv", "run", "python", "scripts/scale_endpoint.py",
           "--env_file", env_file]
    parts = []
    if replicas is not None:
        cmd += ["--replicas", str(replicas)]
        parts.append(f"{replicas} replica(s)")
    if machine_type is not None:
        cmd += ["--machine-type", machine_type]
        parts.append(f"machine={machine_type}")

    if label is None:
        label = f"Scale Vertex AI endpoint: {', '.join(parts)}"
    success, _ = run_command(cmd, label)
    if not success:
        print(f"  WARNING: Failed to scale endpoint ({label})", flush=True)
    return success


def get_endpoint_spec(env_file=".env"):
    """Get current endpoint machine spec via scale_endpoint.py --show."""
    cmd = ["uv", "run", "python", "scripts/scale_endpoint.py",
           "--show", "--env_file", env_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  WARNING: Failed to get endpoint spec: {result.stderr}",
              flush=True)
        return {}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}


def derive_endpoint_machine_types(env_file=".env"):
    """Auto-derive endpoint machine type variants (base + 2x vCPUs).

    Reads the current endpoint machine spec and generates two variants:
    the current machine type and one with 2x vCPUs.
    """
    spec = get_endpoint_spec(env_file)
    machine_spec = spec.get("machine_spec", {})
    current_mt = machine_spec.get("machineType", "")
    if not current_mt:
        return []

    # Parse: family-standard-N → [family-standard-N, family-standard-2N]
    parts = current_mt.rsplit("-", 1)
    if len(parts) == 2:
        try:
            base_cpus = int(parts[1])
            bigger = f"{parts[0]}-{base_cpus * 2}"
            return [current_mt, bigger]
        except ValueError:
            return [current_mt]
    return [current_mt]


def _short_machine_name(machine_type):
    """Shorten machine type for directory names: g2-standard-4 → g2s4."""
    parts = machine_type.split("-")
    if len(parts) == 3 and parts[1] == "standard":
        return f"{parts[0]}s{parts[2]}"
    return machine_type.replace("-", "")


def ensure_endpoint_at_1(args, scaled_phases, current_phase):
    """Scale endpoint to 1 replica if no earlier phase already did it."""
    if not any(p in scaled_phases for p in range(1, current_phase)):
        print(f"\n{'=' * 70}")
        print(f"  PRE-PHASE {current_phase}: Scaling Vertex AI endpoint to 1 replica")
        print(f"{'=' * 70}\n")
        scale_endpoint(1, env_file=args.env_file)


def compute_min_batch_values(max_batch):
    """Generate min_batch sweep values: 1,4,8,16,32, then by 32 up to max_batch-1."""
    base = [v for v in [1, 4, 8, 16, 32] if v < max_batch]
    base += list(range(64, max_batch, 32))
    return base


def analyze_sweep(sweep_dir, param_prefix, param_name, target_p99_ms=750):
    """Generic sweep analysis: find best parameter value per experiment.

    Scans directories matching {param_prefix}_{value}/ under sweep_dir,
    reads benchmark_results.json from each, and picks the value that
    achieves the highest healthy rate (processing_throughput >= 90% of
    target AND p99 < target_p99_ms) with the lowest tail latency at that
    rate.

    Returns: {
        mode: {
            f"best_{param_name}": value,
            "best_rate": int,
            "per_worker_capacity": int,
            ... stats ...
        }
    }
    """
    if not os.path.exists(sweep_dir):
        return {}

    # Collect: mode -> param_value -> rate -> stats
    collected = {}
    for entry in sorted(os.listdir(sweep_dir)):
        if not entry.startswith(f"{param_prefix}_"):
            continue
        try:
            value_str = entry[len(param_prefix) + 1:]
            param_value = int(value_str)
        except (IndexError, ValueError):
            continue

        summary_file = os.path.join(sweep_dir, entry, "benchmark_results.json")
        if not os.path.exists(summary_file):
            continue

        with open(summary_file) as f:
            summary = json.load(f)

        for mode, rate_stats in summary.items():
            if mode not in collected:
                collected[mode] = {}
            if param_value not in collected[mode]:
                collected[mode][param_value] = {}
            for rate_str, stats in rate_stats.items():
                collected[mode][param_value][int(rate_str)] = stats

    # For each mode: find best parameter value by p99 latency
    best = {}
    for mode, param_data in collected.items():
        best_val = None
        best_rate = 0
        best_p99 = 99999

        for pval, rate_stats in param_data.items():
            for rate in sorted(rate_stats.keys()):
                stats = rate_stats[rate]
                tp = stats.get("processing_throughput", stats.get("throughput", 0))
                p99 = stats.get("latency_p99", 99999)
                if tp >= rate * 0.90 and p99 < target_p99_ms:
                    if rate > best_rate or (rate == best_rate and p99 < best_p99):
                        best_val = pval
                        best_rate = rate
                        best_p99 = p99

        if best_val is not None:
            stats_at_best = param_data[best_val][best_rate]
            best[mode] = {
                f"best_{param_name}": best_val,
                "best_rate": best_rate,
                "per_worker_capacity": best_rate,
                **stats_at_best,
            }

    return best


def analyze_machine_sweep(sweep_dir, target_p99_ms=750):
    """Analyze machine size sweep — same logic as analyze_sweep but with string keys."""
    if not os.path.exists(sweep_dir):
        return {}

    collected = {}
    for entry in sorted(os.listdir(sweep_dir)):
        summary_file = os.path.join(sweep_dir, entry, "benchmark_results.json")
        if not os.path.exists(summary_file):
            continue

        machine_type = entry  # e.g. "n1-standard-4"

        with open(summary_file) as f:
            summary = json.load(f)

        for mode, rate_stats in summary.items():
            if mode not in collected:
                collected[mode] = {}
            if machine_type not in collected[mode]:
                collected[mode][machine_type] = {}
            for rate_str, stats in rate_stats.items():
                collected[mode][machine_type][int(rate_str)] = stats

    best = {}
    for mode, machine_data in collected.items():
        best_machine = None
        best_rate = 0
        best_p99 = 99999

        for mt, rate_stats in machine_data.items():
            for rate in sorted(rate_stats.keys()):
                stats = rate_stats[rate]
                tp = stats.get("processing_throughput", stats.get("throughput", 0))
                p99 = stats.get("latency_p99", 99999)
                if tp >= rate * 0.90 and p99 < target_p99_ms:
                    if rate > best_rate or (rate == best_rate and p99 < best_p99):
                        best_machine = mt
                        best_rate = rate
                        best_p99 = p99

        if best_machine is not None:
            stats_at_best = machine_data[best_machine][best_rate]
            best[mode] = {
                "best_machine_type": best_machine,
                "best_rate": best_rate,
                "per_worker_capacity": best_rate,
                **stats_at_best,
            }

    return best


def print_analysis(analysis, param_name, label):
    """Print sweep analysis results."""
    if not analysis:
        print(f"  WARNING: No {label} data found.", flush=True)
        return
    for mode, info in sorted(analysis.items()):
        print(f"  {mode}:")
        print(f"    Best {param_name}:      {info.get(f'best_{param_name}', '?')}")
        print(f"    Per-worker capacity:  {info.get('per_worker_capacity', '?')} msg/s")
        print(f"    Latency p50:          {info.get('latency_p50', '?')} ms")
        print(f"    Latency p99:          {info.get('latency_p99', '?')} ms")
        tp = info.get('processing_throughput', info.get('throughput', '?'))
        print(f"    Processing throughput: {tp} msg/s")
        print()


def save_analysis(analysis, output_path):
    """Save analysis JSON."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(analysis, f, indent=2)
    print(f"  Analysis saved: {output_path}", flush=True)


def load_analysis(path):
    """Load analysis JSON if it exists."""
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def main():
    parser = argparse.ArgumentParser(
        description="Run all benchmark phases end-to-end"
    )
    parser.add_argument(
        "--run-name",
        help="Name for this benchmark run (default: run_YYYYMMDD_HHMMSS). "
             "Results are saved to data/runs/<run-name>/.",
    )
    parser.add_argument(
        "--phases", type=int, nargs="+", default=[1, 2, 3, 4, 5, 6, 7, 8],
        help="Which phases to run (default: 1 2 3 4 5 6 7 8)",
    )
    parser.add_argument(
        "--target-rate", type=int, default=1000,
        help="Target throughput in msg/s (default: 1000). Used for cost calculations.",
    )
    parser.add_argument(
        "--target-p99-ms", type=int, default=750,
        help="Target p99 latency in ms (default: 750). Used as health criterion.",
    )
    parser.add_argument(
        "--duration", type=int, default=100,
        help="Duration in seconds per rate phase (default: 100)",
    )
    parser.add_argument(
        "--rates", type=int, nargs="+",
        default=[25, 50, 75, 100, 125, 150],
        help="Rates (msg/s) for Phase 1 & 2 capacity sweep (default: 25 50 75 100 125 150). "
             "Increase for faster GPUs like L4.",
    )
    parser.add_argument(
        "--batch-sweep-rates", type=int, nargs="+",
        default=[75, 100, 125],
        help="Rates (msg/s) for Phase 3/4 batch sweeps (default: 75 100 125). "
             "Should cover the per-worker capacity range found in Phase 1.",
    )
    parser.add_argument(
        "--batch-sizes", type=int, nargs="+",
        default=list(range(64, 257, 32)),
        help="max_batch_size values for Phase 3 (default: 64 96 128 160 192 224 256)",
    )
    parser.add_argument(
        "--thread-sweep", type=int, nargs="+",
        default=list(range(1, 13)),
        help="Thread counts for Phase 2 sweep (default: 1-12). "
             "Phase 1 uses the Dataflow default (12) as baseline.",
    )
    parser.add_argument(
        "--min-batch-sizes", type=int, nargs="+",
        default=None,
        help="min_batch_size values for Phase 4. "
             "Default: auto from Phase 3 max_batch (1..64 by 1, then by 32 up to max_batch-1).",
    )
    parser.add_argument(
        "--machine-types", type=str, nargs="+",
        default=None,
        help="Machine types for Phase 5 (default: auto from .env, e.g. n1-standard-4 n1-standard-8). "
             "Must be compatible with the GPU type in .env.",
    )
    parser.add_argument(
        "--local-gpu-workers", type=int, nargs="+",
        default=[1, 2, 3, 4],
        help="Worker counts for Local GPU sweep in Phase 7 (default: 1 2 3 4)",
    )
    parser.add_argument(
        "--vertex-ai-workers", type=int, nargs="+",
        default=[1, 2, 4, 8, 11],
        help="Worker counts for Vertex AI sweep in Phase 7 (default: 1 2 4 8 11)",
    )
    parser.add_argument(
        "--endpoint-machine-types", type=str, nargs="+", default=None,
        help="Machine types for Vertex AI endpoint sweep in Phase 5b. "
             "Default: auto-derive from current endpoint (base and 2x vCPUs).",
    )
    parser.add_argument(
        "--vertex-ai-replicas", type=int, nargs="+",
        default=[1, 2, 5, 10],
        help="Replica counts for Vertex AI grid search in Phase 7 (default: 1 2 5 10)",
    )
    parser.add_argument(
        "--vertex-ai-rate", type=int, default=1000,
        help="Fixed rate for Vertex AI scale testing in Phase 7 (default: 1000)",
    )
    parser.add_argument(
        "--capacity-sweep-rates", type=int, nargs="+",
        default=list(range(50, 326, 25)),
        help="Rates (msg/s) for Phase 6d capacity refinement "
             "(default: 50 75 100 ... 300 325). "
             "Wide range discovers true per-worker saturation beyond batch-sweep-rates max.",
    )
    parser.add_argument(
        "--clean", action="store_true",
        help="Remove existing run directory before starting",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print the plan without running anything",
    )
    parser.add_argument(
        "--topic-prefix", default="benchmark",
        help="Prefix for Pub/Sub topic names (default: benchmark). "
             "Use different prefixes for parallel runs.",
    )
    parser.add_argument(
        "--env-file", default=".env",
        help="Path to .env file (default: .env). Use .env.t4 or .env.l4 for GPU-specific configs.",
    )
    parser.add_argument(
        "--raw-predict", action="store_true", default=True,
        help="Use :rawPredict instead of :predict for Vertex AI endpoint calls (default: True)",
    )
    parser.add_argument(
        "--no-raw-predict", action="store_true",
        help="Use :predict instead of :rawPredict for Vertex AI endpoint calls",
    )
    args = parser.parse_args()

    # --no-raw-predict overrides --raw-predict default
    if args.no_raw_predict:
        args.raw_predict = False

    # Work from the benchmark project root
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(base_dir)

    # Load .env to derive machine type defaults for Phase 5
    env = {}
    env_path = args.env_file
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()

    # Auto-derive machine types for Phase 5 if not specified
    if args.machine_types is None:
        base_machine = env.get("MACHINE_TYPE", "n1-standard-4")
        # Parse: family-standard-N → [family-standard-N, family-standard-2N]
        parts = base_machine.rsplit("-", 1)
        if len(parts) == 2:
            try:
                base_cpus = int(parts[1])
                bigger = f"{parts[0]}-{base_cpus * 2}"
                args.machine_types = [base_machine, bigger]
            except ValueError:
                args.machine_types = [base_machine]
        else:
            args.machine_types = [base_machine]

    # Determine run directory
    run_name = args.run_name or datetime.now().strftime("run_%Y%m%d_%H%M%S")
    run_dir = os.path.join("data", "runs", run_name)

    # ── Plan ──
    print(f"\n{'=' * 70}")
    print("  BENCHMARK PLAN")
    print(f"{'=' * 70}")
    print(f"  Goal:         {args.target_rate} msg/s at p99 < {args.target_p99_ms}ms")
    print(f"  Run name:     {run_name}")
    print(f"  Output dir:   {run_dir}")
    print(f"  Phases:       {args.phases}")
    print(f"  Duration:     {args.duration}s per rate")
    print(f"  Env file:     {args.env_file}")
    print(f"  Topic prefix: {args.topic_prefix}")
    print(f"  Predict mode: {'rawPredict' if args.raw_predict else 'predict'}")
    if 1 in args.phases or 2 in args.phases:
        print(f"  Rates:        {args.rates} msg/s")
    if 2 in args.phases:
        print(f"  Thread sweep: {args.thread_sweep}")
    if 3 in args.phases or 4 in args.phases:
        print(f"  Batch rates:  {args.batch_sweep_rates} msg/s")
    if 3 in args.phases:
        print(f"  Batch sizes:  {args.batch_sizes}")
    if 4 in args.phases:
        if args.min_batch_sizes:
            print(f"  Min batches:  {args.min_batch_sizes}")
        else:
            print(f"  Min batches:  (auto from Phase 3: 1,4,8,16,32 then by 32 up to max_batch-1)")
    if 5 in args.phases:
        print(f"  Machines:     {args.machine_types} (5a: Dataflow workers)")
        endpoint_mt = args.endpoint_machine_types or "(auto-derive)"
        print(f"  Endpoint MT:  {endpoint_mt} (5b: Vertex AI endpoint)")
    if 6 in args.phases:
        print(f"  Re-tune:      per-machine loop over {args.machine_types}")
        print(f"  Re-tune 6a:   threads (1..12, full range)")
        print(f"  Re-tune 6b:   max_batch ({args.batch_sizes[0]}..{args.batch_sizes[-1]}, full range)")
        print(f"  Re-tune 6c:   min_batch (full range)")
        csr = args.capacity_sweep_rates
        print(f"  Re-tune 6d:   capacity refinement ({csr[0]}..{csr[-1]} by {csr[1]-csr[0]} msg/s, "
              f"{len(csr)} rates)")
    if 7 in args.phases:
        print(f"  Local GPU:    workers {args.local_gpu_workers}")
        print(f"  Vertex AI:    workers {args.vertex_ai_workers}, "
              f"replicas {args.vertex_ai_replicas}")
        print(f"  Vertex rate:  {args.vertex_ai_rate} msg/s (proportional per replica)")
    if 8 in args.phases:
        print(f"  Phase 8:      Cost analysis and recommendations")

    # Estimate runtime
    est_min = 0
    num_rates = len(args.rates)
    num_batch_rates = len(args.batch_sweep_rates)
    phase_time = args.duration / 60 + 0.5  # per rate: duration + overhead
    if 1 in args.phases:
        est_min += 12 + num_rates * phase_time
    if 2 in args.phases:
        est_min += len(args.thread_sweep) * (12 + num_rates * phase_time)
    if 3 in args.phases:
        est_min += len(args.batch_sizes) * (12 + num_batch_rates * phase_time)
    if 4 in args.phases:
        n_min = len(args.min_batch_sizes) if args.min_batch_sizes else 10  # ~5 base + a few 32-step
        est_min += n_min * (12 + num_batch_rates * phase_time)
    if 5 in args.phases:
        # 5a: worker machines, 5b: endpoint machines (~15 min scaling + benchmark each)
        est_min += len(args.machine_types) * (12 + num_rates * phase_time)
        n_emt = len(args.endpoint_machine_types) if args.endpoint_machine_types else 2
        est_min += n_emt * (15 + 12 + num_batch_rates * phase_time)
    if 6 in args.phases:
        # Per-machine: (6a: 12 threads, 6b: ~7 batch sizes, 6c: ~10 min_batch,
        # 6d: capacity sweep) × number of machine types
        n_machines = len(args.machine_types)
        n_cap_rates = len(args.capacity_sweep_rates)
        est_min += n_machines * (
            (12 + 7 + 10) * (12 + num_batch_rates * phase_time)
            + n_cap_rates * (12 + phase_time)  # 6d capacity sweep
        )
    if 7 in args.phases:
        est_min += len(args.local_gpu_workers) * 12
        n_emt = len(args.endpoint_machine_types) if args.endpoint_machine_types else 2
        n_grid = n_emt * len(args.vertex_ai_replicas) * len(args.vertex_ai_workers)
        est_min += n_grid * 8 + n_emt * 15 + len(args.vertex_ai_replicas) * 3
    if 8 in args.phases:
        est_min += 1  # cost analysis is computation-only
    print(f"  Estimated:    ~{est_min:.0f} min ({est_min / 60:.1f} hrs)")
    print(f"{'=' * 70}\n")

    if args.dry_run:
        print("  (dry run — exiting)")
        return

    # ── Clean ──
    if args.clean and os.path.exists(run_dir):
        shutil.rmtree(run_dir)
        print(f"  Cleaned: {run_dir}")

    os.makedirs(run_dir, exist_ok=True)

    # Tee stdout/stderr to orchestrator.log inside the run directory
    import io

    class _Tee(io.TextIOBase):
        """Write to both a file and the original stream."""
        def __init__(self, stream, log_path):
            self._stream = stream
            self._log = open(log_path, "a")

        def write(self, data):
            self._stream.write(data)
            self._log.write(data)
            self._log.flush()
            return len(data)

        def flush(self):
            self._stream.flush()
            self._log.flush()

    log_path = os.path.join(run_dir, "orchestrator.log")
    sys.stdout = _Tee(sys.stdout, log_path)
    sys.stderr = _Tee(sys.stderr, log_path)

    phase_results = {}  # phase_label -> (description, success, elapsed_min)
    total_start = time.time()

    # Common flags passed to every run_benchmark.py invocation
    common_flags = [
        "--env_file", args.env_file,
        "--topic_prefix", args.topic_prefix,
    ]
    if not args.raw_predict:
        common_flags += ["--no_raw_predict"]

    # Track which phases have already scaled the endpoint to 1
    scaled_phases = set()

    # Accumulated best settings (updated after each analysis phase)
    best = {
        "threads_local_gpu": None,    # None = Dataflow default (12)
        "threads_vertex_ai": None,
        "max_batch_local_gpu": None,  # None = handler default (64)
        "max_batch_vertex_ai": None,
        "min_batch_local_gpu": None,  # None = 1
        "min_batch_vertex_ai": None,
        "machine_type": None,         # None = from .env
        "endpoint_machine_type": None,  # None = current endpoint machine
        "local_capacity": DEFAULT_CAPACITY,
        "vertex_capacity": DEFAULT_CAPACITY,
    }
    best_per_machine = {}  # machine_type -> per-machine optimal settings

    # ── Phase 1: Baseline Capacity Sweep ──
    if 1 in args.phases:
        print(f"\n{'=' * 70}")
        print("  PRE-PHASE 1: Scaling Vertex AI endpoint to 1 replica")
        print(f"{'=' * 70}\n")
        scale_endpoint(1, env_file=args.env_file)
        scaled_phases.add(1)

        rates_str = [str(r) for r in args.rates]
        desc = f"Baseline capacity (12 threads, default batch, rates {args.rates})"
        success, elapsed = run_command(
            ["uv", "run", "python", "scripts/run_benchmark.py",
             "--duration", str(args.duration),
             "--rates"] + rates_str + [
             "--num_workers", "1",
             "--output_dir", os.path.join(run_dir, "phase1_capacity")]
            + common_flags,
            f"Phase 1: {desc}",
        )
        phase_results["1"] = (desc, success, elapsed)

    # ── Phase 2: Thread Count Sweep ──
    if 2 in args.phases:
        ensure_endpoint_at_1(args, scaled_phases, 2)
        scaled_phases.add(2)

        rates_str = [str(r) for r in args.rates]
        thread_dir = os.path.join(run_dir, "phase2_threads")

        print(f"\n{'=' * 70}")
        print(f"  PHASE 2: Thread Count Sweep — {len(args.thread_sweep)} values "
              f"({args.thread_sweep})")
        print(f"{'=' * 70}\n")

        phase2_start = time.time()
        phase2_ok = True

        for tc in args.thread_sweep:
            desc = f"Thread sweep: {tc} threads"
            success, elapsed = run_command(
                ["uv", "run", "python", "scripts/run_benchmark.py",
                 "--duration", str(args.duration),
                 "--rates"] + rates_str + [
                 "--num_workers", "1",
                 "--harness_threads", str(tc),
                 "--output_dir", os.path.join(thread_dir, f"threads_{tc}")]
                + common_flags,
                f"Phase 2 [{tc}t]: {desc}",
            )
            if not success:
                phase2_ok = False
                print(f"  WARNING: threads={tc} failed, continuing...", flush=True)

        phase2_elapsed = (time.time() - phase2_start) / 60
        phase_results["2"] = (f"Thread sweep ({args.thread_sweep})", phase2_ok, phase2_elapsed)

        # Analyze Phase 2
        print(f"\n{'=' * 70}")
        print("  PHASE 2 ANALYSIS: Optimal Thread Count")
        print(f"{'=' * 70}\n")

        thread_analysis = analyze_sweep(thread_dir, "threads", "threads",
                                        target_p99_ms=args.target_p99_ms)
        print_analysis(thread_analysis, "threads", "thread sweep")
        save_analysis(thread_analysis, os.path.join(thread_dir, "analysis.json"))

        # Update best settings
        if "local_gpu" in thread_analysis:
            best["threads_local_gpu"] = thread_analysis["local_gpu"]["best_threads"]
        if "vertex_ai" in thread_analysis:
            best["threads_vertex_ai"] = thread_analysis["vertex_ai"]["best_threads"]

    # Load Phase 2 analysis if we skipped Phase 2 but have prior results
    if 2 not in args.phases:
        prior = load_analysis(os.path.join(run_dir, "phase2_threads", "analysis.json"))
        if "local_gpu" in prior:
            best["threads_local_gpu"] = prior["local_gpu"].get("best_threads")
        if "vertex_ai" in prior:
            best["threads_vertex_ai"] = prior["vertex_ai"].get("best_threads")

    # ── Phase 3: max_batch_size Sweep ──
    if 3 in args.phases:
        ensure_endpoint_at_1(args, scaled_phases, 3)
        scaled_phases.add(3)

        batch_rates_str = [str(r) for r in args.batch_sweep_rates]
        batch_dir = os.path.join(run_dir, "phase3_max_batch")

        print(f"\n{'=' * 70}")
        print(f"  PHASE 3: max_batch_size Sweep — {len(args.batch_sizes)} sizes × "
              f"{len(args.batch_sweep_rates)} rates ({args.batch_sweep_rates})")
        if best["threads_local_gpu"]:
            print(f"  Using Local GPU threads: {best['threads_local_gpu']} (from Phase 2)")
        if best["threads_vertex_ai"]:
            print(f"  Using Vertex AI threads: {best['threads_vertex_ai']} (from Phase 2)")
        print(f"{'=' * 70}\n")

        phase3_start = time.time()
        phase3_ok = True

        # Build per-experiment thread flags from Phase 2 results
        thread_flags = []
        if best["threads_local_gpu"]:
            thread_flags += ["--harness_threads_local_gpu", str(best["threads_local_gpu"])]
        if best["threads_vertex_ai"]:
            thread_flags += ["--harness_threads_vertex_ai", str(best["threads_vertex_ai"])]

        for bs in args.batch_sizes:
            desc = f"Batch sweep: max_batch_size={bs}"
            success, elapsed = run_command(
                ["uv", "run", "python", "scripts/run_benchmark.py",
                 "--duration", str(args.duration),
                 "--rates"] + batch_rates_str + [
                 "--num_workers", "1",
                 "--max_batch_size", str(bs),
                 "--output_dir", os.path.join(batch_dir, f"batch_{bs}")]
                + thread_flags + common_flags,
                f"Phase 3 [{bs}]: {desc}",
            )
            if not success:
                phase3_ok = False
                print(f"  WARNING: max_batch_size={bs} failed, continuing...", flush=True)

        phase3_elapsed = (time.time() - phase3_start) / 60
        phase_results["3"] = (f"max_batch sweep ({args.batch_sweep_rates} msg/s)", phase3_ok, phase3_elapsed)

        # Analyze Phase 3
        print(f"\n{'=' * 70}")
        print("  PHASE 3 ANALYSIS: Optimal max_batch_size")
        print(f"{'=' * 70}\n")

        batch_analysis = analyze_sweep(batch_dir, "batch", "max_batch_size",
                                       target_p99_ms=args.target_p99_ms)
        print_analysis(batch_analysis, "max_batch_size", "max_batch sweep")
        save_analysis(batch_analysis, os.path.join(batch_dir, "analysis.json"))

        if "local_gpu" in batch_analysis:
            best["max_batch_local_gpu"] = batch_analysis["local_gpu"]["best_max_batch_size"]
        if "vertex_ai" in batch_analysis:
            best["max_batch_vertex_ai"] = batch_analysis["vertex_ai"]["best_max_batch_size"]

    # Load Phase 3 analysis if skipped
    if 3 not in args.phases:
        prior = load_analysis(os.path.join(run_dir, "phase3_max_batch", "analysis.json"))
        if "local_gpu" in prior:
            best["max_batch_local_gpu"] = prior["local_gpu"].get("best_max_batch_size")
        if "vertex_ai" in prior:
            best["max_batch_vertex_ai"] = prior["vertex_ai"].get("best_max_batch_size")

    # ── Phase 4: min_batch_size Sweep ──
    if 4 in args.phases:
        ensure_endpoint_at_1(args, scaled_phases, 4)
        scaled_phases.add(4)

        batch_rates_str = [str(r) for r in args.batch_sweep_rates]
        min_batch_dir = os.path.join(run_dir, "phase4_min_batch")

        # Auto-compute min_batch values from Phase 3 max_batch if not explicitly provided
        if args.min_batch_sizes is not None:
            min_batch_values = args.min_batch_sizes
        else:
            max_batch = max(
                best["max_batch_local_gpu"] or 64,
                best["max_batch_vertex_ai"] or 64,
            )
            min_batch_values = compute_min_batch_values(max_batch)

        print(f"\n{'=' * 70}")
        print(f"  PHASE 4: min_batch_size Sweep — {len(min_batch_values)} values × "
              f"{len(args.batch_sweep_rates)} rates ({args.batch_sweep_rates})")
        print(f"  Values: {min_batch_values} "
              f"(1,4,8,16,32 then by 32)")
        print(f"  Using threads: LG={best['threads_local_gpu'] or 'default(12)'}, "
              f"VA={best['threads_vertex_ai'] or 'default(12)'}")
        print(f"  Using max_batch: LG={best['max_batch_local_gpu'] or 'default(64)'}, "
              f"VA={best['max_batch_vertex_ai'] or 'default(64)'}")
        print(f"{'=' * 70}\n")

        phase4_start = time.time()
        phase4_ok = True

        # Build accumulated flags from Phases 2–3
        tuning_flags = []
        if best["threads_local_gpu"]:
            tuning_flags += ["--harness_threads_local_gpu", str(best["threads_local_gpu"])]
        if best["threads_vertex_ai"]:
            tuning_flags += ["--harness_threads_vertex_ai", str(best["threads_vertex_ai"])]
        if best["max_batch_local_gpu"]:
            tuning_flags += ["--max_batch_size_local_gpu", str(best["max_batch_local_gpu"])]
        if best["max_batch_vertex_ai"]:
            tuning_flags += ["--max_batch_size_vertex_ai", str(best["max_batch_vertex_ai"])]

        for mbs in min_batch_values:
            desc = f"min_batch sweep: min_batch_size={mbs}"
            success, elapsed = run_command(
                ["uv", "run", "python", "scripts/run_benchmark.py",
                 "--duration", str(args.duration),
                 "--rates"] + batch_rates_str + [
                 "--num_workers", "1",
                 "--min_batch_size", str(mbs),
                 "--output_dir", os.path.join(min_batch_dir, f"min_{mbs}")]
                + tuning_flags + common_flags,
                f"Phase 4 [min={mbs}]: {desc}",
            )
            if not success:
                phase4_ok = False
                print(f"  WARNING: min_batch_size={mbs} failed, continuing...", flush=True)

        phase4_elapsed = (time.time() - phase4_start) / 60
        phase_results["4"] = (f"min_batch sweep ({len(min_batch_values)} values)", phase4_ok, phase4_elapsed)

        # Analyze Phase 4
        print(f"\n{'=' * 70}")
        print("  PHASE 4 ANALYSIS: Optimal min_batch_size")
        print(f"{'=' * 70}\n")

        min_analysis = analyze_sweep(min_batch_dir, "min", "min_batch_size",
                                      target_p99_ms=args.target_p99_ms)
        print_analysis(min_analysis, "min_batch_size", "min_batch sweep")
        save_analysis(min_analysis, os.path.join(min_batch_dir, "analysis.json"))

        if "local_gpu" in min_analysis:
            best["min_batch_local_gpu"] = min_analysis["local_gpu"]["best_min_batch_size"]
        if "vertex_ai" in min_analysis:
            best["min_batch_vertex_ai"] = min_analysis["vertex_ai"]["best_min_batch_size"]

    # Load Phase 4 analysis if skipped
    if 4 not in args.phases:
        prior = load_analysis(os.path.join(run_dir, "phase4_min_batch", "analysis.json"))
        if "local_gpu" in prior:
            best["min_batch_local_gpu"] = prior["local_gpu"].get("best_min_batch_size")
        if "vertex_ai" in prior:
            best["min_batch_vertex_ai"] = prior["vertex_ai"].get("best_min_batch_size")

    # ── Phase 5a: Dataflow Worker Machine Sweep ──
    if 5 in args.phases:
        ensure_endpoint_at_1(args, scaled_phases, 5)
        scaled_phases.add(5)

        rates_str = [str(r) for r in args.rates]
        machine_dir = os.path.join(run_dir, "phase5_machine")

        print(f"\n{'=' * 70}")
        print(f"  PHASE 5a: Dataflow Worker Machine Sweep — "
              f"{len(args.machine_types)} types ({args.machine_types})")
        print(f"  Using optimal threads + batch from Phases 2–4")
        print(f"{'=' * 70}\n")

        phase5a_start = time.time()
        phase5a_ok = True

        # Build all accumulated tuning flags
        tuning_flags = []
        if best["threads_local_gpu"]:
            tuning_flags += ["--harness_threads_local_gpu", str(best["threads_local_gpu"])]
        if best["threads_vertex_ai"]:
            tuning_flags += ["--harness_threads_vertex_ai", str(best["threads_vertex_ai"])]
        if best["max_batch_local_gpu"]:
            tuning_flags += ["--max_batch_size_local_gpu", str(best["max_batch_local_gpu"])]
        if best["max_batch_vertex_ai"]:
            tuning_flags += ["--max_batch_size_vertex_ai", str(best["max_batch_vertex_ai"])]
        if best["min_batch_local_gpu"]:
            tuning_flags += ["--min_batch_size_local_gpu", str(best["min_batch_local_gpu"])]
        if best["min_batch_vertex_ai"]:
            tuning_flags += ["--min_batch_size_vertex_ai", str(best["min_batch_vertex_ai"])]

        for mt in args.machine_types:
            desc = f"Worker machine: {mt}"
            success, elapsed = run_command(
                ["uv", "run", "python", "scripts/run_benchmark.py",
                 "--duration", str(args.duration),
                 "--rates"] + rates_str + [
                 "--num_workers", "1",
                 "--machine_type", mt,
                 "--output_dir", os.path.join(machine_dir, mt)]
                + tuning_flags + common_flags,
                f"Phase 5a [{mt}]: {desc}",
            )
            if not success:
                phase5a_ok = False
                print(f"  WARNING: {mt} failed, continuing...", flush=True)

        phase5a_elapsed = (time.time() - phase5a_start) / 60
        phase_results["5a"] = (f"Worker machine sweep ({args.machine_types})",
                               phase5a_ok, phase5a_elapsed)

        # Analyze Phase 5a
        print(f"\n{'=' * 70}")
        print("  PHASE 5a ANALYSIS: Optimal Worker Machine Type")
        print(f"{'=' * 70}\n")

        machine_analysis = analyze_machine_sweep(machine_dir,
                                                 target_p99_ms=args.target_p99_ms)
        print_analysis(machine_analysis, "machine_type", "worker machine sweep")
        save_analysis(machine_analysis, os.path.join(machine_dir, "analysis.json"))

        if "local_gpu" in machine_analysis:
            best["machine_type"] = machine_analysis["local_gpu"]["best_machine_type"]

    # Load Phase 5a analysis if skipped
    if 5 not in args.phases:
        prior = load_analysis(os.path.join(run_dir, "phase5_machine", "analysis.json"))
        if "local_gpu" in prior:
            best["machine_type"] = prior["local_gpu"].get("best_machine_type")

    # ── Phase 5b: Vertex AI Endpoint Machine Sweep ──
    if 5 in args.phases:
        # Determine endpoint machine types to test
        endpoint_machine_types = args.endpoint_machine_types
        if endpoint_machine_types is None:
            endpoint_machine_types = derive_endpoint_machine_types(args.env_file)
            if not endpoint_machine_types:
                print("  WARNING: Could not auto-derive endpoint machine types. "
                      "Skipping Phase 5b.", flush=True)

        if endpoint_machine_types:
            batch_rates_str = [str(r) for r in args.batch_sweep_rates]
            endpoint_dir = os.path.join(run_dir, "phase5_endpoint")

            print(f"\n{'=' * 70}")
            print(f"  PHASE 5b: Vertex AI Endpoint Machine Sweep — "
                  f"{len(endpoint_machine_types)} types ({endpoint_machine_types})")
            print(f"  Testing Vertex AI only (endpoint machine change)")
            print(f"{'=' * 70}\n")

            phase5b_start = time.time()
            phase5b_ok = True

            # Build tuning flags for vertex_ai only
            vertex_flags = []
            if best["threads_vertex_ai"]:
                vertex_flags += ["--harness_threads_vertex_ai",
                                 str(best["threads_vertex_ai"])]
            if best["max_batch_vertex_ai"]:
                vertex_flags += ["--max_batch_size_vertex_ai",
                                 str(best["max_batch_vertex_ai"])]
            if best["min_batch_vertex_ai"]:
                vertex_flags += ["--min_batch_size_vertex_ai",
                                 str(best["min_batch_vertex_ai"])]

            for emt in endpoint_machine_types:
                desc = f"Endpoint machine: {emt}"

                # Scale endpoint to 1 replica with this machine type
                print(f"\n  Scaling endpoint to machine={emt}, replicas=1...",
                      flush=True)
                if not scale_endpoint(replicas=1, machine_type=emt,
                                      env_file=args.env_file):
                    print(f"  WARNING: Failed to set endpoint to {emt}. "
                          f"Skipping.", flush=True)
                    phase5b_ok = False
                    continue

                success, elapsed = run_command(
                    ["uv", "run", "python", "scripts/run_benchmark.py",
                     "--duration", str(args.duration),
                     "--rates"] + batch_rates_str + [
                     "--num_workers", "1",
                     "--experiments", "vertex_ai",
                     "--output_dir", os.path.join(endpoint_dir, emt)]
                    + vertex_flags + common_flags,
                    f"Phase 5b [{emt}]: {desc}",
                )
                if not success:
                    phase5b_ok = False
                    print(f"  WARNING: endpoint {emt} failed, continuing...",
                          flush=True)

            phase5b_elapsed = (time.time() - phase5b_start) / 60
            phase_results["5b"] = (
                f"Endpoint machine sweep ({endpoint_machine_types})",
                phase5b_ok, phase5b_elapsed)

            # Analyze Phase 5b
            print(f"\n{'=' * 70}")
            print("  PHASE 5b ANALYSIS: Optimal Endpoint Machine Type")
            print(f"{'=' * 70}\n")

            endpoint_analysis = analyze_machine_sweep(
                endpoint_dir, target_p99_ms=args.target_p99_ms)
            print_analysis(endpoint_analysis, "machine_type",
                           "endpoint machine sweep")
            save_analysis(endpoint_analysis,
                          os.path.join(endpoint_dir, "analysis.json"))

            if "vertex_ai" in endpoint_analysis:
                best["endpoint_machine_type"] = (
                    endpoint_analysis["vertex_ai"]["best_machine_type"])

    # Load Phase 5b analysis if skipped
    if 5 not in args.phases:
        prior = load_analysis(
            os.path.join(run_dir, "phase5_endpoint", "analysis.json"))
        if "vertex_ai" in prior:
            best["endpoint_machine_type"] = prior["vertex_ai"].get(
                "best_machine_type")

    # ── Phase 6: Re-tune on All Machine Types ──
    if 6 in args.phases:
        scaled_phases.add(6)

        batch_rates_str = [str(r) for r in args.batch_sweep_rates]
        retune_dir = os.path.join(run_dir, "phase6_retune")

        # Re-tune each machine type independently for per-machine cost comparison
        all_worker_machines = args.machine_types or [env.get("MACHINE_TYPE", "n1-standard-4")]

        # Scale endpoint to best endpoint machine (stays fixed across worker machines)
        if best["endpoint_machine_type"]:
            print(f"\n{'=' * 70}")
            print(f"  PRE-PHASE 6: Setting endpoint to best machine "
                  f"({best['endpoint_machine_type']})")
            print(f"{'=' * 70}\n")
            scale_endpoint(replicas=1, machine_type=best["endpoint_machine_type"],
                           env_file=args.env_file)
        else:
            ensure_endpoint_at_1(args, scaled_phases, 6)

        print(f"\n{'=' * 70}")
        print("  PHASE 6: Re-tune on All Machine Types")
        print(f"  Worker machines: {all_worker_machines}")
        print(f"  Endpoint machine: {best['endpoint_machine_type'] or 'current'}")
        print(f"{'=' * 70}\n")

        phase6_start = time.time()
        phase6_ok = True

        for mt in all_worker_machines:
            mt_short = _short_machine_name(mt)
            mt_retune_dir = os.path.join(retune_dir, mt_short)

            # Per-machine best settings, starting from Phase 2-4 results
            mt_best = {
                "threads_local_gpu": best["threads_local_gpu"],
                "threads_vertex_ai": best["threads_vertex_ai"],
                "max_batch_local_gpu": best["max_batch_local_gpu"],
                "max_batch_vertex_ai": best["max_batch_vertex_ai"],
                "min_batch_local_gpu": best["min_batch_local_gpu"],
                "min_batch_vertex_ai": best["min_batch_vertex_ai"],
                "local_capacity": best["local_capacity"],
                "vertex_capacity": best["vertex_capacity"],
            }

            print(f"\n{'=' * 70}")
            print(f"  PHASE 6 — Machine: {mt} ({mt_short})")
            print(f"{'=' * 70}\n")

            # ── 6a: Thread re-sweep (full range) ──
            retune_threads = list(args.thread_sweep)

            print(f"\n{'=' * 70}")
            print(f"  PHASE 6a [{mt_short}]: Thread Re-sweep — "
                  f"{len(retune_threads)} values "
                  f"({retune_threads[0]}..{retune_threads[-1]} by 1)")
            print(f"{'=' * 70}\n")

            # Build flags with this machine + Phase 3-4 batch settings
            retune_base_flags = ["--machine_type", mt]
            if mt_best["max_batch_local_gpu"]:
                retune_base_flags += ["--max_batch_size_local_gpu",
                                      str(mt_best["max_batch_local_gpu"])]
            if mt_best["max_batch_vertex_ai"]:
                retune_base_flags += ["--max_batch_size_vertex_ai",
                                      str(mt_best["max_batch_vertex_ai"])]
            if mt_best["min_batch_local_gpu"]:
                retune_base_flags += ["--min_batch_size_local_gpu",
                                      str(mt_best["min_batch_local_gpu"])]
            if mt_best["min_batch_vertex_ai"]:
                retune_base_flags += ["--min_batch_size_vertex_ai",
                                      str(mt_best["min_batch_vertex_ai"])]

            thread_dir = os.path.join(mt_retune_dir, "threads")
            for tc in retune_threads:
                desc = f"Re-tune threads: {tc}"
                success, elapsed = run_command(
                    ["uv", "run", "python", "scripts/run_benchmark.py",
                     "--duration", str(args.duration),
                     "--rates"] + batch_rates_str + [
                     "--num_workers", "1",
                     "--harness_threads", str(tc),
                     "--output_dir", os.path.join(thread_dir, f"threads_{tc}")]
                    + retune_base_flags + common_flags,
                    f"Phase 6a [{mt_short}:{tc}t]: {desc}",
                )
                if not success:
                    phase6_ok = False

            # Analyze 6a
            thread_analysis = analyze_sweep(thread_dir, "threads", "threads",
                                            target_p99_ms=args.target_p99_ms)
            if thread_analysis:
                print_analysis(thread_analysis, "threads",
                               f"Phase 6a [{mt_short}] thread re-sweep")
                if "local_gpu" in thread_analysis:
                    mt_best["threads_local_gpu"] = thread_analysis["local_gpu"]["best_threads"]
                if "vertex_ai" in thread_analysis:
                    mt_best["threads_vertex_ai"] = thread_analysis["vertex_ai"]["best_threads"]

            # ── 6b: max_batch_size re-sweep (full range) ──
            retune_batch_sizes = list(args.batch_sizes)

            print(f"\n{'=' * 70}")
            print(f"  PHASE 6b [{mt_short}]: max_batch_size Re-sweep — "
                  f"{len(retune_batch_sizes)} sizes "
                  f"({retune_batch_sizes[0]}..{retune_batch_sizes[-1]} by 32)")
            print(f"  Using 6a threads: LG={mt_best['threads_local_gpu'] or 'default'}, "
                  f"VA={mt_best['threads_vertex_ai'] or 'default'}")
            print(f"{'=' * 70}\n")

            # Build flags with 6a threads + this machine + Phase 4 min_batch
            batch_retune_flags = ["--machine_type", mt]
            if mt_best["threads_local_gpu"]:
                batch_retune_flags += ["--harness_threads_local_gpu",
                                       str(mt_best["threads_local_gpu"])]
            if mt_best["threads_vertex_ai"]:
                batch_retune_flags += ["--harness_threads_vertex_ai",
                                       str(mt_best["threads_vertex_ai"])]
            if mt_best["min_batch_local_gpu"]:
                batch_retune_flags += ["--min_batch_size_local_gpu",
                                       str(mt_best["min_batch_local_gpu"])]
            if mt_best["min_batch_vertex_ai"]:
                batch_retune_flags += ["--min_batch_size_vertex_ai",
                                       str(mt_best["min_batch_vertex_ai"])]

            batch_dir = os.path.join(mt_retune_dir, "max_batch")
            for bs in retune_batch_sizes:
                desc = f"Re-tune max_batch: {bs}"
                success, elapsed = run_command(
                    ["uv", "run", "python", "scripts/run_benchmark.py",
                     "--duration", str(args.duration),
                     "--rates"] + batch_rates_str + [
                     "--num_workers", "1",
                     "--max_batch_size", str(bs),
                     "--output_dir", os.path.join(batch_dir, f"batch_{bs}")]
                    + batch_retune_flags + common_flags,
                    f"Phase 6b [{mt_short}:{bs}]: {desc}",
                )
                if not success:
                    phase6_ok = False

            # Analyze 6b
            batch_analysis = analyze_sweep(batch_dir, "batch", "max_batch_size",
                                           target_p99_ms=args.target_p99_ms)
            if batch_analysis:
                print_analysis(batch_analysis, "max_batch_size",
                               f"Phase 6b [{mt_short}] max_batch re-sweep")
                if "local_gpu" in batch_analysis:
                    mt_best["max_batch_local_gpu"] = batch_analysis["local_gpu"]["best_max_batch_size"]
                if "vertex_ai" in batch_analysis:
                    mt_best["max_batch_vertex_ai"] = batch_analysis["vertex_ai"]["best_max_batch_size"]

            # ── 6c: min_batch_size re-sweep (full range) ──
            retune_max = max(
                mt_best["max_batch_local_gpu"] or 64,
                mt_best["max_batch_vertex_ai"] or 64,
            )
            retune_min_values = compute_min_batch_values(retune_max)
            if not retune_min_values:
                retune_min_values = [1]

            print(f"\n{'=' * 70}")
            print(f"  PHASE 6c [{mt_short}]: min_batch_size Re-sweep — "
                  f"{len(retune_min_values)} values "
                  f"({retune_min_values[0]}..{retune_min_values[-1]})")
            print(f"  Using 6a threads + 6b batch")
            print(f"{'=' * 70}\n")

            # Build flags with 6a threads + 6b max_batch + this machine
            min_retune_flags = ["--machine_type", mt]
            if mt_best["threads_local_gpu"]:
                min_retune_flags += ["--harness_threads_local_gpu",
                                     str(mt_best["threads_local_gpu"])]
            if mt_best["threads_vertex_ai"]:
                min_retune_flags += ["--harness_threads_vertex_ai",
                                     str(mt_best["threads_vertex_ai"])]
            if mt_best["max_batch_local_gpu"]:
                min_retune_flags += ["--max_batch_size_local_gpu",
                                     str(mt_best["max_batch_local_gpu"])]
            if mt_best["max_batch_vertex_ai"]:
                min_retune_flags += ["--max_batch_size_vertex_ai",
                                     str(mt_best["max_batch_vertex_ai"])]

            min_batch_dir = os.path.join(mt_retune_dir, "min_batch")
            for mbs in retune_min_values:
                desc = f"Re-tune min_batch: {mbs}"
                success, elapsed = run_command(
                    ["uv", "run", "python", "scripts/run_benchmark.py",
                     "--duration", str(args.duration),
                     "--rates"] + batch_rates_str + [
                     "--num_workers", "1",
                     "--min_batch_size", str(mbs),
                     "--output_dir", os.path.join(min_batch_dir, f"min_{mbs}")]
                    + min_retune_flags + common_flags,
                    f"Phase 6c [{mt_short}:min={mbs}]: {desc}",
                )
                if not success:
                    phase6_ok = False

            # Analyze 6c
            min_analysis = analyze_sweep(min_batch_dir, "min", "min_batch_size",
                                         target_p99_ms=args.target_p99_ms)
            if min_analysis:
                print_analysis(min_analysis, "min_batch_size",
                               f"Phase 6c [{mt_short}] min_batch re-sweep")
                if "local_gpu" in min_analysis:
                    mt_best["min_batch_local_gpu"] = min_analysis["local_gpu"]["best_min_batch_size"]
                if "vertex_ai" in min_analysis:
                    mt_best["min_batch_vertex_ai"] = min_analysis["vertex_ai"]["best_min_batch_size"]

            # Preliminary capacity from 6c results
            if min_analysis and "local_gpu" in min_analysis:
                mt_best["local_capacity"] = min_analysis["local_gpu"].get(
                    "per_worker_capacity", mt_best["local_capacity"])
            elif batch_analysis and "local_gpu" in batch_analysis:
                mt_best["local_capacity"] = batch_analysis["local_gpu"].get(
                    "per_worker_capacity", mt_best["local_capacity"])
            elif thread_analysis and "local_gpu" in thread_analysis:
                mt_best["local_capacity"] = thread_analysis["local_gpu"].get(
                    "per_worker_capacity", mt_best["local_capacity"])

            if min_analysis and "vertex_ai" in min_analysis:
                mt_best["vertex_capacity"] = min_analysis["vertex_ai"].get(
                    "per_worker_capacity",
                    mt_best.get("vertex_capacity", DEFAULT_CAPACITY))
            elif batch_analysis and "vertex_ai" in batch_analysis:
                mt_best["vertex_capacity"] = batch_analysis["vertex_ai"].get(
                    "per_worker_capacity",
                    mt_best.get("vertex_capacity", DEFAULT_CAPACITY))

            # ── 6d: Capacity refinement — wide rate sweep ──
            capacity_dir = os.path.join(mt_retune_dir, "capacity")

            # Build all accumulated tuning flags for capacity sweep
            capacity_flags = ["--machine_type", mt]
            if mt_best["threads_local_gpu"]:
                capacity_flags += ["--harness_threads_local_gpu",
                                   str(mt_best["threads_local_gpu"])]
            if mt_best["threads_vertex_ai"]:
                capacity_flags += ["--harness_threads_vertex_ai",
                                   str(mt_best["threads_vertex_ai"])]
            if mt_best["max_batch_local_gpu"]:
                capacity_flags += ["--max_batch_size_local_gpu",
                                   str(mt_best["max_batch_local_gpu"])]
            if mt_best["max_batch_vertex_ai"]:
                capacity_flags += ["--max_batch_size_vertex_ai",
                                   str(mt_best["max_batch_vertex_ai"])]
            if mt_best["min_batch_local_gpu"]:
                capacity_flags += ["--min_batch_size_local_gpu",
                                   str(mt_best["min_batch_local_gpu"])]
            if mt_best["min_batch_vertex_ai"]:
                capacity_flags += ["--min_batch_size_vertex_ai",
                                   str(mt_best["min_batch_vertex_ai"])]

            # Wide capacity rates to discover true per-worker saturation
            capacity_rates = list(args.capacity_sweep_rates)

            print(f"\n{'=' * 70}")
            print(f"  PHASE 6d [{mt_short}]: Capacity Refinement — "
                  f"{len(capacity_rates)} rates")
            print(f"  Rates: {capacity_rates}")
            print(f"  Using all best settings from 6a/6b/6c")
            print(f"{'=' * 70}\n")

            for cr in capacity_rates:
                desc = f"Capacity refinement: {cr} msg/s"
                success, elapsed = run_command(
                    ["uv", "run", "python", "scripts/run_benchmark.py",
                     "--duration", str(args.duration),
                     "--rates", str(cr),
                     "--num_workers", "1",
                     "--output_dir", os.path.join(capacity_dir, f"rate_{cr}")]
                    + capacity_flags + common_flags,
                    f"Phase 6d [{mt_short}:{cr}]: {desc}",
                )
                if not success:
                    phase6_ok = False

            # Analyze 6d: find highest healthy rate
            cap_analysis = analyze_sweep(capacity_dir, "rate", "capacity",
                                         target_p99_ms=args.target_p99_ms)
            if cap_analysis:
                print_analysis(cap_analysis, "capacity",
                               f"Phase 6d [{mt_short}] capacity refinement")
                if "local_gpu" in cap_analysis:
                    mt_best["local_capacity"] = cap_analysis["local_gpu"].get(
                        "per_worker_capacity", mt_best["local_capacity"])
                if "vertex_ai" in cap_analysis:
                    mt_best["vertex_capacity"] = cap_analysis["vertex_ai"].get(
                        "per_worker_capacity",
                        mt_best.get("vertex_capacity", DEFAULT_CAPACITY))

            # Save per-machine analysis
            mt_analysis = {
                "machine_type": mt,
                "best_settings": {k: v for k, v in mt_best.items()
                                  if v is not None},
                "thread_analysis": thread_analysis if thread_analysis else {},
                "batch_analysis": batch_analysis if batch_analysis else {},
                "min_batch_analysis": min_analysis if min_analysis else {},
                "capacity_analysis": cap_analysis if cap_analysis else {},
            }
            save_analysis(mt_analysis,
                          os.path.join(mt_retune_dir, "analysis.json"))

            best_per_machine[mt] = mt_best

            print(f"\n  {mt} ({mt_short}) complete:")
            print(f"    Local GPU capacity:  {mt_best['local_capacity']} msg/s")
            print(f"    Vertex AI capacity:  {mt_best['vertex_capacity']} msg/s")
            print()

        phase6_elapsed = (time.time() - phase6_start) / 60
        phase_results["6"] = (
            f"Re-tune on {len(all_worker_machines)} machines "
            f"({[_short_machine_name(m) for m in all_worker_machines]})",
            phase6_ok, phase6_elapsed)

        # Update overall best from the machine with highest local_gpu capacity
        winner_mt = max(best_per_machine,
                        key=lambda m: best_per_machine[m]["local_capacity"])
        winner = best_per_machine[winner_mt]
        best["machine_type"] = winner_mt
        for key in ["threads_local_gpu", "threads_vertex_ai",
                     "max_batch_local_gpu", "max_batch_vertex_ai",
                     "min_batch_local_gpu", "min_batch_vertex_ai",
                     "local_capacity", "vertex_capacity"]:
            if winner.get(key) is not None:
                best[key] = winner[key]

        # Save combined Phase 6 analysis
        combined_analysis = {
            "best_settings": {k: v for k, v in best.items()
                              if v is not None},
            "per_machine": {mt: {k: v for k, v in settings.items()
                                 if v is not None}
                            for mt, settings in best_per_machine.items()},
            "winner_machine": winner_mt,
        }
        save_analysis(combined_analysis,
                      os.path.join(retune_dir, "analysis.json"))

    # Load Phase 6 analysis if skipped
    if 6 not in args.phases:
        prior = load_analysis(
            os.path.join(run_dir, "phase6_retune", "analysis.json"))
        if prior.get("best_settings"):
            bs = prior["best_settings"]
            for key in ["threads_local_gpu", "threads_vertex_ai",
                        "max_batch_local_gpu", "max_batch_vertex_ai",
                        "min_batch_local_gpu", "min_batch_vertex_ai",
                        "local_capacity", "vertex_capacity",
                        "endpoint_machine_type", "machine_type"]:
                if key in bs and bs[key] is not None:
                    best[key] = bs[key]
        # Load per-machine data
        if prior.get("per_machine"):
            for mt, settings in prior["per_machine"].items():
                best_per_machine[mt] = settings

    # ── Print Scale Calculation ──
    print(f"\n{'=' * 70}")
    print("  SCALE CALCULATION")
    print(f"{'=' * 70}")
    print(f"  Goal: {args.target_rate} msg/s at p99 < {args.target_p99_ms}ms")
    if best_per_machine:
        for mt in sorted(best_per_machine):
            settings = best_per_machine[mt]
            mt_short = _short_machine_name(mt)
            local_cap = settings.get("local_capacity", DEFAULT_CAPACITY)
            vertex_cap = settings.get("vertex_capacity", DEFAULT_CAPACITY)
            workers_needed = math.ceil(args.target_rate / local_cap)
            print(f"  {mt} ({mt_short}):")
            print(f"    Local GPU capacity:  {local_cap} msg/s → "
                  f"{workers_needed} workers for {args.target_rate} msg/s")
            print(f"    Vertex AI capacity:  {vertex_cap} msg/s/replica")
    else:
        local_capacity = best["local_capacity"]
        print(f"  Per-worker capacity (Local GPU): {local_capacity} msg/s")
        local_workers_needed = math.ceil(args.target_rate / local_capacity)
        print(f"  Workers for {args.target_rate} msg/s: {local_workers_needed}")
        if best.get("vertex_capacity"):
            print(f"  Per-replica capacity (Vertex AI): "
                  f"{best['vertex_capacity']} msg/s")
    print(f"  Overall best: {json.dumps({k: v for k, v in best.items() if v is not None}, indent=4)}")
    print(f"{'=' * 70}\n")

    # ── Phase 7: Scale Verification ──
    if 7 in args.phases:
        print(f"\n{'=' * 70}")
        print("  PHASE 7: Scale Verification (via run_phase7_sweep.py)")
        print(f"{'=' * 70}\n")

        # Clear stale sweep_summary.json from prior runs so each Phase 7
        # invocation merges only with results from this run
        stale_summary = os.path.join(run_dir, "phase7_scale", "sweep_summary.json")
        if os.path.exists(stale_summary):
            os.remove(stale_summary)
            print(f"  Cleared stale {stale_summary}", flush=True)

        local_workers_str = [str(w) for w in args.local_gpu_workers]
        vertex_workers_str = [str(w) for w in args.vertex_ai_workers]
        vertex_replicas_str = [str(r) for r in args.vertex_ai_replicas]

        # Determine endpoint machine types for Phase 7 grid
        endpoint_machines = args.endpoint_machine_types
        if endpoint_machines is None:
            endpoint_machines = derive_endpoint_machine_types(args.env_file)
        if not endpoint_machines and best.get("endpoint_machine_type"):
            endpoint_machines = [best["endpoint_machine_type"]]

        # Phase 7a: Local GPU — one sweep per worker machine type
        machines_to_sweep = (sorted(best_per_machine.keys())
                             if best_per_machine
                             else [best.get("machine_type")])
        machines_to_sweep = [m for m in machines_to_sweep if m]

        for mt in machines_to_sweep:
            mt_short = _short_machine_name(mt)
            mt_settings = best_per_machine.get(mt, best)
            local_capacity_mt = mt_settings.get("local_capacity",
                                                 best["local_capacity"])

            desc = (f"Local GPU {mt} ({mt_short}), "
                    f"workers {args.local_gpu_workers}")

            phase7a_flags = [
                "--env-file", args.env_file,
                "--topic-prefix", args.topic_prefix,
                "--experiments", "local_gpu",
                "--machine-type", mt,
            ]
            if not args.raw_predict:
                phase7a_flags += ["--no-raw-predict"]

            # Forward per-machine optimal settings
            if mt_settings.get("threads_local_gpu"):
                phase7a_flags += ["--harness-threads-local-gpu",
                                  str(mt_settings["threads_local_gpu"])]
            if mt_settings.get("max_batch_local_gpu"):
                phase7a_flags += ["--max-batch-local-gpu",
                                  str(mt_settings["max_batch_local_gpu"])]
            if mt_settings.get("min_batch_local_gpu"):
                phase7a_flags += ["--min-batch-local-gpu",
                                  str(mt_settings["min_batch_local_gpu"])]

            cmd = [
                "uv", "run", "python", "scripts/run_phase7_sweep.py",
                "--output-base", os.path.join(run_dir, "phase7_scale"),
                "--duration", str(args.duration),
                "--local-gpu-workers"] + local_workers_str + [
                "--local-gpu-rate-per-worker", str(local_capacity_mt),
            ] + phase7a_flags

            success, elapsed = run_command(
                cmd, f"Phase 7a [{mt_short}]: {desc}")
            phase_results[f"7a_{mt_short}"] = (desc, success, elapsed)

        # Phase 7b+c: Vertex AI grid (uses overall best vertex settings)
        vertex_capacity = best.get("vertex_capacity", DEFAULT_CAPACITY)

        desc = (f"Vertex AI, workers {args.vertex_ai_workers} × "
                f"replicas {args.vertex_ai_replicas}")
        if endpoint_machines:
            desc += f" × machines {endpoint_machines}"

        phase7v_flags = [
            "--env-file", args.env_file,
            "--topic-prefix", args.topic_prefix,
            "--experiments", "vertex_ai",
        ]
        if not args.raw_predict:
            phase7v_flags += ["--no-raw-predict"]
        if best["threads_vertex_ai"]:
            phase7v_flags += ["--harness-threads-vertex-ai",
                              str(best["threads_vertex_ai"])]
        if best["max_batch_vertex_ai"]:
            phase7v_flags += ["--max-batch-vertex-ai",
                              str(best["max_batch_vertex_ai"])]
        if best["min_batch_vertex_ai"]:
            phase7v_flags += ["--min-batch-vertex-ai",
                              str(best["min_batch_vertex_ai"])]
        if best["machine_type"]:
            phase7v_flags += ["--machine-type", best["machine_type"]]

        cmd = [
            "uv", "run", "python", "scripts/run_phase7_sweep.py",
            "--output-base", os.path.join(run_dir, "phase7_scale"),
            "--duration", str(args.duration),
            "--vertex-ai-workers"] + vertex_workers_str + [
            "--vertex-ai-replicas"] + vertex_replicas_str + [
            "--vertex-ai-rate", str(args.vertex_ai_rate),
            "--vertex-ai-rate-per-replica", str(vertex_capacity),
        ] + phase7v_flags

        if endpoint_machines:
            cmd += ["--vertex-ai-endpoint-machines"] + endpoint_machines

        success, elapsed = run_command(cmd, f"Phase 7b+c: {desc}")
        phase_results["7b"] = (desc, success, elapsed)

    # ── Phase 8: Cost Analysis ──
    if 8 in args.phases:
        print(f"\n{'=' * 70}")
        print("  PHASE 8: Cost Analysis and Recommendations")
        print(f"{'=' * 70}\n")

        cost_cmd = [
            "uv", "run", "python", "scripts/cost_analysis.py",
            "--data-dir", run_dir,
            "--target-rate", str(args.target_rate),
            "--target-p99-ms", str(args.target_p99_ms),
            "--env-file", args.env_file,
        ]
        if best.get("machine_type"):
            cost_cmd += ["--worker-machine", best["machine_type"]]

        success, elapsed = run_command(cost_cmd, "Phase 8: Cost analysis")
        phase_results["8"] = ("Cost analysis", success, elapsed)

    # ── Charts ──
    print(f"\n{'=' * 70}")
    print("  Generating report charts...")
    print(f"{'=' * 70}\n")

    run_command(
        ["uv", "run", "python", "scripts/generate_report_charts.py",
         "--data-dir", run_dir],
        "Generate report charts",
    )

    # ── Final Summary ──
    total_elapsed = (time.time() - total_start) / 60

    print(f"\n{'=' * 70}")
    print("  FULL BENCHMARK COMPLETE")
    print(f"{'=' * 70}")
    print(f"  Run name:   {run_name}")
    print(f"  Output dir: {run_dir}")
    print(f"  Total time: {total_elapsed:.0f} min ({total_elapsed / 60:.1f} hrs)")
    print()
    for phase_label in sorted(phase_results.keys()):
        desc, success, elapsed = phase_results[phase_label]
        status = "PASS" if success else "FAIL"
        print(f"  Phase {phase_label}: [{status}] {desc} ({elapsed:.0f} min)")
    print(f"\n  Overall best settings:")
    for k, v in best.items():
        if v is not None:
            print(f"    {k}: {v}")
    if best_per_machine:
        print(f"\n  Per-machine settings:")
        for mt in sorted(best_per_machine):
            mt_short = _short_machine_name(mt)
            settings = best_per_machine[mt]
            local_cap = settings.get("local_capacity", "?")
            vertex_cap = settings.get("vertex_capacity", "?")
            print(f"    {mt} ({mt_short}): "
                  f"local_capacity={local_cap}, "
                  f"vertex_capacity={vertex_cap}")
    print(f"\n{'=' * 70}\n")

    # Exit with failure if any phase failed
    if not all(success for _, success, _ in phase_results.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
