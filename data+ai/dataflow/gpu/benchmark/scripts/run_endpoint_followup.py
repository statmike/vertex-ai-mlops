#!/usr/bin/env python3
"""Option A follow-up: Re-tune Vertex AI for -standard-8 endpoint machines.

The main benchmark run (run_all_phases.py) failed to test -standard-8 endpoint
machines because mutateDeployedModel doesn't support machine type changes.
That bug is now fixed (undeploy+redeploy in scale_endpoint.py).

This script fills the gap:
  1. Scale endpoint to -standard-8
  2. Run Phase 6a-d to re-tune Vertex AI settings for the -standard-8 endpoint
     (one sweep per worker machine type)
  3. Run Phase 7b+c Vertex AI grid with the newly optimized settings
  4. Re-run Phase 8 cost analysis

The existing run directory is reused — new results are written alongside the
original data so Phase 8 can compare all configurations.

Usage:
  # Full follow-up for T4
  uv run python scripts/run_endpoint_followup.py --env-file .env.t4 \
      --run-name t4_full --topic-prefix bench-t4

  # Full follow-up for L4
  uv run python scripts/run_endpoint_followup.py --env-file .env.l4 \
      --run-name l4_full --topic-prefix bench-l4

  # Phase 5b quick test only (stop if no improvement)
  uv run python scripts/run_endpoint_followup.py --env-file .env.t4 \
      --run-name t4_full --topic-prefix bench-t4 --phase5b-only
"""

import argparse
import json
import math
import os
import subprocess
import sys
import time
from datetime import datetime


# ---------------------------------------------------------------------------
# Helpers (mirrored from run_all_phases.py)
# ---------------------------------------------------------------------------

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


def scale_endpoint(replicas=None, env_file=".env", machine_type=None):
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

    label = f"Scale endpoint: {', '.join(parts)}"
    success, _ = run_command(cmd, label)
    if not success:
        print(f"  ERROR: Failed to scale endpoint ({label})", flush=True)
    return success


def _short_machine_name(machine_type):
    """Shorten machine type: g2-standard-4 → g2s4."""
    parts = machine_type.split("-")
    if len(parts) == 3 and parts[1] == "standard":
        return f"{parts[0]}s{parts[2]}"
    return machine_type.replace("-", "")


def compute_min_batch_values(max_batch):
    """Generate min_batch sweep values: 1,4,8,16,32, then by 32 up to max_batch-1."""
    base = [v for v in [1, 4, 8, 16, 32] if v < max_batch]
    base += list(range(64, max_batch, 32))
    return base


def analyze_sweep(sweep_dir, param_prefix, param_name, target_p99_ms=750):
    """Analyze a parameter sweep — find best value per experiment.

    Reuses the analyze_sweep function from run_all_phases.py by importing it.
    Falls back to a simpler inline version if import fails.
    """
    # Import the full analyzer from the orchestrator
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        from run_all_phases import analyze_sweep as _analyze
        return _analyze(sweep_dir, param_prefix, param_name,
                        target_p99_ms=target_p99_ms)
    finally:
        sys.path.pop(0)


def print_analysis(analysis, param_name, label):
    """Print analysis results."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        from run_all_phases import print_analysis as _print
        _print(analysis, param_name, label)
    finally:
        sys.path.pop(0)


def load_analysis(path):
    """Load analysis JSON file."""
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def save_analysis(analysis, output_path):
    """Save analysis to JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(analysis, f, indent=2)
    print(f"  Analysis saved: {output_path}", flush=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Option A follow-up: re-tune Vertex AI for -standard-8 "
                    "endpoint machines"
    )
    parser.add_argument(
        "--env-file", required=True,
        help="Path to .env file (.env.t4 or .env.l4)",
    )
    parser.add_argument(
        "--run-name", required=True,
        help="Existing run name to append results to (e.g., t4_full)",
    )
    parser.add_argument(
        "--topic-prefix", required=True,
        help="Pub/Sub topic prefix (e.g., bench-t4)",
    )
    parser.add_argument(
        "--endpoint-machine", default=None,
        help="Endpoint machine type to test (default: auto-derive -standard-8 "
             "from current endpoint)",
    )
    parser.add_argument(
        "--phase5b-only", action="store_true",
        help="Only run Phase 5b quick test. If no improvement, stop.",
    )
    parser.add_argument(
        "--skip-phase5b", action="store_true",
        help="Skip Phase 5b test (assume improvement, go straight to Phase 6).",
    )
    parser.add_argument(
        "--duration", type=int, default=100,
        help="Duration in seconds per rate phase (default: 100)",
    )
    parser.add_argument(
        "--target-p99-ms", type=int, default=750,
        help="Target p99 latency in ms (default: 750)",
    )
    parser.add_argument(
        "--target-rate", type=int, default=1000,
        help="Target total throughput in msg/s (default: 1000)",
    )
    parser.add_argument(
        "--vertex-ai-workers", type=int, nargs="+",
        default=[1, 2, 4, 8, 11],
        help="Worker counts for Vertex AI Phase 7 sweep (default: 1 2 4 8 11)",
    )
    parser.add_argument(
        "--vertex-ai-replicas", type=int, nargs="+",
        default=[1, 2, 5, 10],
        help="Replica counts for Phase 7 sweep (default: 1 2 5 10)",
    )
    args = parser.parse_args()

    run_dir = os.path.join("data", "runs", args.run_name)
    if not os.path.exists(run_dir):
        print(f"ERROR: Run directory {run_dir} does not exist.", file=sys.stderr)
        sys.exit(1)

    # Set up logging
    log_path = os.path.join(run_dir, "endpoint_followup.log")

    class _Tee:
        def __init__(self, stream, log_path):
            self.stream = stream
            self.log = open(log_path, "a")

        def write(self, data):
            self.stream.write(data)
            self.log.write(data)

        def flush(self):
            self.stream.flush()
            self.log.flush()

    sys.stdout = _Tee(sys.stdout, log_path)
    sys.stderr = _Tee(sys.stderr, log_path)

    total_start = time.time()
    phase_results = {}

    print(f"\n{'=' * 70}")
    print("  OPTION A FOLLOW-UP: Vertex AI -standard-8 Endpoint Re-tune")
    print(f"  Run directory: {run_dir}")
    print(f"  Env file:      {args.env_file}")
    print(f"  Topic prefix:  {args.topic_prefix}")
    print(f"  Started:       {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 70}\n")

    # ── Load existing Phase 6 analysis ──
    phase6_analysis_path = os.path.join(run_dir, "phase6_retune", "analysis.json")
    prior = load_analysis(phase6_analysis_path)
    if not prior.get("per_machine"):
        print("ERROR: No Phase 6 per_machine data found in "
              f"{phase6_analysis_path}", file=sys.stderr)
        sys.exit(1)

    prior_best = prior["best_settings"]
    prior_per_machine = prior["per_machine"]
    worker_machines = sorted(prior_per_machine.keys())

    print(f"  Loaded Phase 6 analysis: {len(worker_machines)} worker machines")
    for mt in worker_machines:
        s = prior_per_machine[mt]
        print(f"    {mt}: vertex_capacity={s.get('vertex_capacity', '?')} msg/s "
              f"(endpoint was -standard-4)")
    print()

    # ── Determine endpoint machine type ──
    if args.endpoint_machine:
        new_endpoint_mt = args.endpoint_machine
    else:
        # Auto-derive: take current endpoint machine and double vCPUs
        current_endpoint = prior_best.get("endpoint_machine_type", "")
        if not current_endpoint:
            # Fall back to first worker machine family
            current_endpoint = worker_machines[0]
        parts = current_endpoint.rsplit("-", 1)
        if len(parts) == 2:
            try:
                base_cpus = int(parts[1])
                new_endpoint_mt = f"{parts[0]}-{base_cpus * 2}"
            except ValueError:
                print("ERROR: Cannot derive -standard-8 from "
                      f"{current_endpoint}", file=sys.stderr)
                sys.exit(1)
        else:
            print(f"ERROR: Cannot parse endpoint machine: {current_endpoint}",
                  file=sys.stderr)
            sys.exit(1)

    new_endpoint_short = _short_machine_name(new_endpoint_mt)
    current_endpoint_mt = prior_best.get("endpoint_machine_type",
                                          worker_machines[0])

    print(f"  Current endpoint machine: {current_endpoint_mt}")
    print(f"  New endpoint machine:     {new_endpoint_mt}")
    print()

    # Common flags for run_benchmark.py
    common_flags = [
        "--env_file", args.env_file,
        "--topic_prefix", args.topic_prefix,
    ]

    # Batch sweep rates (same as run_all_phases defaults)
    batch_sweep_rates = [75, 100, 125]
    batch_rates_str = [str(r) for r in batch_sweep_rates]

    # Capacity sweep rates (same as run_all_phases defaults)
    capacity_sweep_rates = list(range(50, 326, 25))

    # Thread sweep (same as run_all_phases defaults)
    thread_sweep = list(range(1, 13))

    # Batch sizes (same as run_all_phases defaults)
    batch_sizes = list(range(64, 257, 32))

    # ── Step 1: Scale endpoint to -standard-8 ──
    print(f"\n{'=' * 70}")
    print(f"  STEP 1: Scale endpoint to {new_endpoint_mt}")
    print(f"{'=' * 70}\n")

    if not scale_endpoint(replicas=1, env_file=args.env_file,
                          machine_type=new_endpoint_mt):
        print("ERROR: Failed to scale endpoint. Aborting.", file=sys.stderr)
        sys.exit(1)

    # ── Step 2: Phase 5b quick capacity test ──
    if not args.skip_phase5b:
        print(f"\n{'=' * 70}")
        print(f"  STEP 2: Phase 5b — Quick capacity test on {new_endpoint_mt}")
        print(f"{'=' * 70}\n")

        phase5b_dir = os.path.join(run_dir, "phase5b_endpoint_followup",
                                   new_endpoint_short)

        # Use the first worker machine's settings for a quick test
        test_mt = worker_machines[0]
        test_settings = prior_per_machine[test_mt]

        test_flags = [
            "--machine_type", test_mt,
            "--experiments", "vertex_ai",
            "--num_workers", "1",
        ]
        if test_settings.get("threads_vertex_ai"):
            test_flags += ["--harness_threads", str(test_settings["threads_vertex_ai"])]
        if test_settings.get("max_batch_vertex_ai"):
            test_flags += ["--max_batch_size", str(test_settings["max_batch_vertex_ai"])]
        if test_settings.get("min_batch_vertex_ai"):
            test_flags += ["--min_batch_size", str(test_settings["min_batch_vertex_ai"])]

        success, elapsed = run_command(
            ["uv", "run", "python", "scripts/run_benchmark.py",
             "--duration", str(args.duration),
             "--rates", "50", "75", "100", "125", "150",
             "--output_dir", phase5b_dir]
            + test_flags + common_flags,
            f"Phase 5b [{new_endpoint_short}]: Quick capacity test",
        )
        phase_results["5b"] = (f"Quick capacity test on {new_endpoint_mt}",
                               success, elapsed)

        # Analyze result
        if success:
            results_path = os.path.join(phase5b_dir, "benchmark_results.json")
            if os.path.exists(results_path):
                with open(results_path) as f:
                    results = json.load(f)

                # Find highest rate where p99 < target
                vertex_data = results.get("vertex_ai", {})
                current_vertex_cap = test_settings.get("vertex_capacity",
                                                        DEFAULT_CAPACITY)
                best_rate = 0
                best_p99 = 0

                for rate_str, stats in sorted(vertex_data.items(),
                                               key=lambda x: int(x[0])):
                    rate = int(rate_str)
                    tp = stats.get("processing_throughput", 0)
                    p99 = stats.get("latency_p99", 99999)
                    if tp >= rate * 0.9 and p99 < args.target_p99_ms:
                        best_rate = rate
                        best_p99 = p99

                print(f"\n  Phase 5b results on {new_endpoint_mt} endpoint:")
                print(f"    Best healthy rate: {best_rate} msg/s "
                      f"(p99={best_p99:.0f}ms)")
                print(f"    Current -standard-4 capacity: "
                      f"{current_vertex_cap} msg/s")

                if best_rate <= current_vertex_cap:
                    print(f"\n  VERDICT: No improvement from {new_endpoint_mt} "
                          f"endpoint.")
                    print(f"  Current data is the final answer. Stopping.\n")

                    # Scale back to -standard-4
                    scale_endpoint(replicas=1, env_file=args.env_file,
                                   machine_type=current_endpoint_mt)
                    _print_summary(phase_results, total_start)
                    return
                else:
                    print(f"\n  VERDICT: {new_endpoint_mt} endpoint shows "
                          f"improvement ({best_rate} vs {current_vertex_cap} "
                          f"msg/s).")
                    print(f"  Proceeding to Phase 6 re-tune.\n")

        if args.phase5b_only:
            print("\n  --phase5b-only specified. Stopping after Phase 5b.\n")
            _print_summary(phase_results, total_start)
            return

    # ── Step 3: Phase 6 Vertex AI re-tune for -standard-8 endpoint ──
    print(f"\n{'=' * 70}")
    print(f"  STEP 3: Phase 6 — Re-tune Vertex AI for {new_endpoint_mt} endpoint")
    print(f"  Worker machines: {worker_machines}")
    print(f"{'=' * 70}\n")

    retune_dir = os.path.join(run_dir, f"phase6_endpoint_{new_endpoint_short}")
    phase6_start = time.time()
    phase6_ok = True

    # Per-machine best settings for the new endpoint
    endpoint_per_machine = {}

    for mt in worker_machines:
        mt_short = _short_machine_name(mt)
        mt_retune_dir = os.path.join(retune_dir, mt_short)

        # Start from the prior Phase 6 settings for this worker machine
        # (these were tuned for -standard-4 endpoint, we'll re-tune for -standard-8)
        mt_best = dict(prior_per_machine[mt])

        print(f"\n{'=' * 70}")
        print(f"  PHASE 6 — Worker: {mt} ({mt_short}), "
              f"Endpoint: {new_endpoint_mt}")
        print(f"  Starting from: threads_va={mt_best.get('threads_vertex_ai')}, "
              f"max_batch_va={mt_best.get('max_batch_vertex_ai')}, "
              f"min_batch_va={mt_best.get('min_batch_vertex_ai')}")
        print(f"{'=' * 70}\n")

        # ── 6a: Thread re-sweep (Vertex AI only) ──
        print(f"\n{'=' * 70}")
        print(f"  PHASE 6a [{mt_short}]: Thread Re-sweep — "
              f"{len(thread_sweep)} values (1..12)")
        print(f"{'=' * 70}\n")

        retune_base_flags = [
            "--machine_type", mt,
            "--experiments", "vertex_ai",
        ]
        if mt_best.get("max_batch_vertex_ai"):
            retune_base_flags += ["--max_batch_size",
                                  str(mt_best["max_batch_vertex_ai"])]
        if mt_best.get("min_batch_vertex_ai"):
            retune_base_flags += ["--min_batch_size",
                                  str(mt_best["min_batch_vertex_ai"])]

        thread_dir = os.path.join(mt_retune_dir, "threads")
        for tc in thread_sweep:
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
            if "vertex_ai" in thread_analysis:
                mt_best["threads_vertex_ai"] = \
                    thread_analysis["vertex_ai"]["best_threads"]

        # ── 6b: max_batch_size re-sweep ──
        print(f"\n{'=' * 70}")
        print(f"  PHASE 6b [{mt_short}]: max_batch_size Re-sweep — "
              f"{len(batch_sizes)} sizes (64..256)")
        print(f"  Using 6a threads: VA={mt_best.get('threads_vertex_ai')}")
        print(f"{'=' * 70}\n")

        batch_retune_flags = [
            "--machine_type", mt,
            "--experiments", "vertex_ai",
        ]
        if mt_best.get("threads_vertex_ai"):
            batch_retune_flags += ["--harness_threads",
                                   str(mt_best["threads_vertex_ai"])]
        if mt_best.get("min_batch_vertex_ai"):
            batch_retune_flags += ["--min_batch_size",
                                   str(mt_best["min_batch_vertex_ai"])]

        batch_dir = os.path.join(mt_retune_dir, "max_batch")
        for bs in batch_sizes:
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
            if "vertex_ai" in batch_analysis:
                mt_best["max_batch_vertex_ai"] = \
                    batch_analysis["vertex_ai"]["best_max_batch_size"]

        # ── 6c: min_batch_size re-sweep ──
        retune_max = mt_best.get("max_batch_vertex_ai", 64)
        retune_min_values = compute_min_batch_values(retune_max)
        if not retune_min_values:
            retune_min_values = [1]

        print(f"\n{'=' * 70}")
        print(f"  PHASE 6c [{mt_short}]: min_batch_size Re-sweep — "
              f"{len(retune_min_values)} values "
              f"({retune_min_values[0]}..{retune_min_values[-1]})")
        print(f"  Using 6a threads + 6b batch")
        print(f"{'=' * 70}\n")

        min_retune_flags = [
            "--machine_type", mt,
            "--experiments", "vertex_ai",
        ]
        if mt_best.get("threads_vertex_ai"):
            min_retune_flags += ["--harness_threads",
                                 str(mt_best["threads_vertex_ai"])]
        if mt_best.get("max_batch_vertex_ai"):
            min_retune_flags += ["--max_batch_size",
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
            if "vertex_ai" in min_analysis:
                mt_best["min_batch_vertex_ai"] = \
                    min_analysis["vertex_ai"]["best_min_batch_size"]

        # Preliminary capacity from 6c
        if min_analysis and "vertex_ai" in min_analysis:
            mt_best["vertex_capacity"] = min_analysis["vertex_ai"].get(
                "per_worker_capacity",
                mt_best.get("vertex_capacity", DEFAULT_CAPACITY))
        elif batch_analysis and "vertex_ai" in batch_analysis:
            mt_best["vertex_capacity"] = batch_analysis["vertex_ai"].get(
                "per_worker_capacity",
                mt_best.get("vertex_capacity", DEFAULT_CAPACITY))

        # ── 6d: Capacity refinement ──
        capacity_dir = os.path.join(mt_retune_dir, "capacity")

        capacity_flags = [
            "--machine_type", mt,
            "--experiments", "vertex_ai",
        ]
        if mt_best.get("threads_vertex_ai"):
            capacity_flags += ["--harness_threads",
                               str(mt_best["threads_vertex_ai"])]
        if mt_best.get("max_batch_vertex_ai"):
            capacity_flags += ["--max_batch_size",
                               str(mt_best["max_batch_vertex_ai"])]
        if mt_best.get("min_batch_vertex_ai"):
            capacity_flags += ["--min_batch_size",
                               str(mt_best["min_batch_vertex_ai"])]

        print(f"\n{'=' * 70}")
        print(f"  PHASE 6d [{mt_short}]: Capacity Refinement — "
              f"{len(capacity_sweep_rates)} rates")
        print(f"  Rates: {capacity_sweep_rates}")
        print(f"  Using all best settings from 6a/6b/6c")
        print(f"{'=' * 70}\n")

        for cr in capacity_sweep_rates:
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

        # Analyze 6d
        cap_analysis = analyze_sweep(capacity_dir, "rate", "capacity",
                                     target_p99_ms=args.target_p99_ms)
        if cap_analysis:
            print_analysis(cap_analysis, "capacity",
                           f"Phase 6d [{mt_short}] capacity refinement")
            if "vertex_ai" in cap_analysis:
                mt_best["vertex_capacity"] = cap_analysis["vertex_ai"].get(
                    "per_worker_capacity",
                    mt_best.get("vertex_capacity", DEFAULT_CAPACITY))

        # Save per-machine analysis
        mt_analysis = {
            "machine_type": mt,
            "endpoint_machine_type": new_endpoint_mt,
            "best_settings": {k: v for k, v in mt_best.items()
                              if v is not None},
            "thread_analysis": thread_analysis if thread_analysis else {},
            "batch_analysis": batch_analysis if batch_analysis else {},
            "min_batch_analysis": min_analysis if min_analysis else {},
            "capacity_analysis": cap_analysis if cap_analysis else {},
        }
        save_analysis(mt_analysis,
                      os.path.join(mt_retune_dir, "analysis.json"))

        endpoint_per_machine[mt] = mt_best

        print(f"\n  {mt} ({mt_short}) with {new_endpoint_mt} endpoint:")
        print(f"    Vertex AI capacity: {mt_best.get('vertex_capacity', '?')} msg/s")
        print(f"    threads: {mt_best.get('threads_vertex_ai')}")
        print(f"    max_batch: {mt_best.get('max_batch_vertex_ai')}")
        print(f"    min_batch: {mt_best.get('min_batch_vertex_ai')}")
        print()

    phase6_elapsed = (time.time() - phase6_start) / 60
    phase_results["6"] = (
        f"Re-tune Vertex AI for {new_endpoint_mt} endpoint",
        phase6_ok, phase6_elapsed)

    # Save combined endpoint follow-up analysis
    combined = {
        "endpoint_machine_type": new_endpoint_mt,
        "per_machine": {mt: {k: v for k, v in s.items() if v is not None}
                        for mt, s in endpoint_per_machine.items()},
    }
    save_analysis(combined, os.path.join(retune_dir, "analysis.json"))

    # ── Step 4: Phase 7b+c — Vertex AI grid with new endpoint ──
    print(f"\n{'=' * 70}")
    print(f"  STEP 4: Phase 7b+c — Vertex AI scale verification on "
          f"{new_endpoint_mt}")
    print(f"  Workers: {args.vertex_ai_workers}")
    print(f"  Replicas: {args.vertex_ai_replicas}")
    print(f"  Worker machines: {worker_machines}")
    print(f"{'=' * 70}\n")

    vertex_workers_str = [str(w) for w in args.vertex_ai_workers]
    vertex_replicas_str = [str(r) for r in args.vertex_ai_replicas]

    # Use the highest vertex capacity across worker machines for rate calculation
    best_vertex_capacity = max(
        s.get("vertex_capacity", DEFAULT_CAPACITY)
        for s in endpoint_per_machine.values()
    )

    # Pick the worker machine with the best vertex capacity for Phase 7 settings
    best_vertex_mt = max(endpoint_per_machine,
                         key=lambda m: endpoint_per_machine[m].get(
                             "vertex_capacity", 0))
    vertex_settings = endpoint_per_machine[best_vertex_mt]

    phase7v_flags = [
        "--env-file", args.env_file,
        "--topic-prefix", args.topic_prefix,
        "--experiments", "vertex_ai",
    ]
    if vertex_settings.get("threads_vertex_ai"):
        phase7v_flags += ["--harness-threads-vertex-ai",
                          str(vertex_settings["threads_vertex_ai"])]
    if vertex_settings.get("max_batch_vertex_ai"):
        phase7v_flags += ["--max-batch-vertex-ai",
                          str(vertex_settings["max_batch_vertex_ai"])]
    if vertex_settings.get("min_batch_vertex_ai"):
        phase7v_flags += ["--min-batch-vertex-ai",
                          str(vertex_settings["min_batch_vertex_ai"])]

    # Use the best worker machine type
    phase7v_flags += ["--machine-type", best_vertex_mt]

    cmd = [
        "uv", "run", "python", "scripts/run_phase7_sweep.py",
        "--output-base", os.path.join(run_dir, "phase7_scale"),
        "--duration", str(args.duration),
        "--vertex-ai-workers"] + vertex_workers_str + [
        "--vertex-ai-replicas"] + vertex_replicas_str + [
        "--vertex-ai-rate", str(args.target_rate),
        "--vertex-ai-rate-per-replica", str(best_vertex_capacity),
        "--vertex-ai-endpoint-machines", new_endpoint_mt,
    ] + phase7v_flags

    desc = (f"Vertex AI {new_endpoint_mt} endpoint, "
            f"workers {args.vertex_ai_workers} × "
            f"replicas {args.vertex_ai_replicas}")
    success, elapsed = run_command(cmd, f"Phase 7b+c: {desc}")
    phase_results["7b"] = (desc, success, elapsed)

    # ── Step 5: Phase 8 — Cost analysis ──
    print(f"\n{'=' * 70}")
    print("  STEP 5: Phase 8 — Cost Analysis (all data)")
    print(f"{'=' * 70}\n")

    cost_cmd = [
        "uv", "run", "python", "scripts/cost_analysis.py",
        "--data-dir", run_dir,
        "--target-rate", str(args.target_rate),
        "--target-p99-ms", str(args.target_p99_ms),
        "--env-file", args.env_file,
    ]
    success, elapsed = run_command(cost_cmd, "Phase 8: Cost analysis")
    phase_results["8"] = ("Cost analysis", success, elapsed)

    # ── Scale endpoint back to -standard-4, 1 replica ──
    print(f"\n  Scaling endpoint back to {current_endpoint_mt}...", flush=True)
    scale_endpoint(replicas=1, env_file=args.env_file,
                   machine_type=current_endpoint_mt)

    _print_summary(phase_results, total_start)


def _print_summary(phase_results, total_start):
    """Print final summary."""
    total_elapsed = (time.time() - total_start) / 60

    print(f"\n{'=' * 70}")
    print("  ENDPOINT FOLLOW-UP COMPLETE")
    print(f"{'=' * 70}")
    print(f"  Total time: {total_elapsed:.0f} min ({total_elapsed / 60:.1f} hrs)")
    print()
    for label in sorted(phase_results.keys()):
        desc, success, elapsed = phase_results[label]
        status = "PASS" if success else "FAIL"
        print(f"  Step {label}: [{status}] {desc} ({elapsed:.0f} min)")
    print(f"\n{'=' * 70}\n")

    if not all(success for _, success, _ in phase_results.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
