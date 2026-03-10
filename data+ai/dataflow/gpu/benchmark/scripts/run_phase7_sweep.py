#!/usr/bin/env python3
"""Phase 7: Scale verification with worker × replica × endpoint machine grid.

Local GPU:  1–N workers — demonstrate linear scaling at healthy rates.
            Each worker count is tested at (per_worker_capacity × num_workers)
            msg/s, proving that adding workers scales throughput linearly
            while maintaining healthy latency.

Vertex AI:  Grid search over endpoint machine types × replica counts ×
            Dataflow worker counts. Grouped by endpoint machine type (slow
            change, ~15 min) then by replica count (fast change, ~2-3 min),
            then worker count (no endpoint change needed).

Optimal settings (threads, batch sizes, worker machine type) are forwarded
from the orchestrator via CLI flags — no hardcoded settings.

Results are saved to <output_base>/<experiment>_<N>w/ for local GPU and
<output_base>/vertex_ai_<mt>/r<R>_w<W>/ for Vertex AI grid.
"""

import json
import os
import subprocess
import sys
import time


def run_command(cmd, label):
    """Run a subprocess, streaming output. Returns (success, elapsed_min)."""
    print(f"\n{'─' * 70}", flush=True)
    print(f"  {label}", flush=True)
    print(f"  $ {' '.join(cmd)}", flush=True)
    print(f"{'─' * 70}\n", flush=True)

    start = time.time()
    result = subprocess.run(cmd)
    elapsed = (time.time() - start) / 60

    success = result.returncode == 0
    status = "OK" if success else f"FAILED (exit {result.returncode})"
    print(f"\n  [{status}] {label} — {elapsed:.1f} min\n", flush=True)
    return success, elapsed


def scale_endpoint(replicas=None, machine_type=None, env_file=".env"):
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
    success, elapsed = run_command(cmd, label)
    if not success:
        print(f"  WARNING: Failed to scale endpoint ({label})", flush=True)
    return success


def run_benchmark(experiment, num_workers, rate, output_dir, duration=100,
                   extra_args=None):
    """Run a single benchmark: one experiment, one worker count, one rate."""
    cmd = [
        "uv", "run", "python", "scripts/run_benchmark.py",
        "--duration", str(duration),
        "--rates", str(rate),
        "--num_workers", str(num_workers),
        "--experiments", experiment,
        "--output_dir", output_dir,
    ]

    if extra_args:
        cmd += extra_args

    label = f"{experiment} ({num_workers}w) at {rate} msg/s"
    return run_command(cmd, label)


def _short_machine_name(machine_type):
    """Shorten machine type for directory names: g2-standard-4 → g2s4."""
    parts = machine_type.split("-")
    if len(parts) == 3 and parts[1] == "standard":
        return f"{parts[0]}s{parts[2]}"
    return machine_type.replace("-", "")


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Phase 7: Scale verification with grid search"
    )
    parser.add_argument(
        "--experiments", nargs="+",
        choices=["local_gpu", "vertex_ai"],
        default=["local_gpu", "vertex_ai"],
        help="Which experiments to run (default: both)",
    )
    parser.add_argument(
        "--local-gpu-workers", type=int, nargs="+",
        default=[1, 2, 3, 4],
        help="Worker counts for local_gpu sweep (default: 1 2 3 4)",
    )
    parser.add_argument(
        "--vertex-ai-workers", type=int, nargs="+",
        default=[1, 2, 4, 8, 11],
        help="Worker counts for vertex_ai sweep (default: 1 2 4 8 11)",
    )
    parser.add_argument(
        "--local-gpu-rate-per-worker", type=int, default=100,
        help="Per-worker rate for Local GPU (total rate = this × workers). "
             "Default: 100 msg/s",
    )
    parser.add_argument(
        "--vertex-ai-rate", type=int, default=1000,
        help="Maximum rate for Vertex AI sweep (default: 1000 msg/s). "
             "When --vertex-ai-rate-per-replica is set, actual rate = "
             "per_replica × replicas, capped at this value.",
    )
    parser.add_argument(
        "--vertex-ai-rate-per-replica", type=int, default=None,
        help="Per-replica rate for Vertex AI (rate = this × replicas, "
             "capped at --vertex-ai-rate). If not set, uses fixed "
             "--vertex-ai-rate for all runs.",
    )
    parser.add_argument(
        "--vertex-ai-replicas", type=int, nargs="+",
        default=[10],
        help="Replica counts for Vertex AI grid (default: 10). "
             "Scaled in sorted order within each endpoint machine type.",
    )
    parser.add_argument(
        "--vertex-ai-endpoint-machines", type=str, nargs="+",
        default=None,
        help="Endpoint machine types for Vertex AI grid. "
             "If not specified, uses current endpoint machine type only.",
    )
    parser.add_argument(
        "--duration", type=int, default=100,
        help="Duration in seconds per rate phase (default: 100)",
    )
    parser.add_argument(
        "--output-base",
        default="data/phase7_scale",
        help="Base output directory (default: data/phase7_scale)",
    )
    parser.add_argument(
        "--topic-prefix", default="benchmark",
        help="Prefix for Pub/Sub topic and subscription names (default: benchmark)",
    )
    parser.add_argument(
        "--env-file", default=".env",
        help="Path to .env file (default: .env)",
    )
    parser.add_argument(
        "--raw-predict", action="store_true", default=True,
        help="Use :rawPredict for Vertex AI endpoint calls (default: True)",
    )
    parser.add_argument(
        "--no-raw-predict", action="store_true",
        help="Use :predict instead of :rawPredict",
    )
    # Forwarded optimal settings from orchestrator
    parser.add_argument(
        "--harness-threads-local-gpu", type=int, default=None,
        help="Thread count for local_gpu (forwarded from Phase 2/6)",
    )
    parser.add_argument(
        "--harness-threads-vertex-ai", type=int, default=None,
        help="Thread count for vertex_ai (forwarded from Phase 2/6)",
    )
    parser.add_argument(
        "--max-batch-local-gpu", type=int, default=None,
        help="max_batch_size for local_gpu (forwarded from Phase 3/6)",
    )
    parser.add_argument(
        "--max-batch-vertex-ai", type=int, default=None,
        help="max_batch_size for vertex_ai (forwarded from Phase 3/6)",
    )
    parser.add_argument(
        "--min-batch-local-gpu", type=int, default=None,
        help="min_batch_size for local_gpu (forwarded from Phase 4/6)",
    )
    parser.add_argument(
        "--min-batch-vertex-ai", type=int, default=None,
        help="min_batch_size for vertex_ai (forwarded from Phase 4/6)",
    )
    parser.add_argument(
        "--machine-type", type=str, default=None,
        help="Dataflow worker machine type (forwarded from Phase 5)",
    )
    args = parser.parse_args()

    # --no-raw-predict overrides --raw-predict default
    if args.no_raw_predict:
        args.raw_predict = False

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(base_dir)

    output_base = args.output_base
    os.makedirs(output_base, exist_ok=True)

    # Build extra args forwarded to every run_benchmark.py call
    extra_args = [
        "--env_file", args.env_file,
        "--topic_prefix", args.topic_prefix,
    ]
    if not args.raw_predict:
        extra_args += ["--no_raw_predict"]

    # Build per-experiment tuning flags from forwarded settings
    local_gpu_flags = list(extra_args)
    if args.harness_threads_local_gpu:
        local_gpu_flags += ["--harness_threads_local_gpu",
                            str(args.harness_threads_local_gpu)]
    if args.max_batch_local_gpu:
        local_gpu_flags += ["--max_batch_size_local_gpu",
                            str(args.max_batch_local_gpu)]
    if args.min_batch_local_gpu:
        local_gpu_flags += ["--min_batch_size_local_gpu",
                            str(args.min_batch_local_gpu)]
    if args.machine_type:
        local_gpu_flags += ["--machine_type", args.machine_type]

    vertex_ai_flags = list(extra_args)
    if args.harness_threads_vertex_ai:
        vertex_ai_flags += ["--harness_threads_vertex_ai",
                            str(args.harness_threads_vertex_ai)]
    if args.max_batch_vertex_ai:
        vertex_ai_flags += ["--max_batch_size_vertex_ai",
                            str(args.max_batch_vertex_ai)]
    if args.min_batch_vertex_ai:
        vertex_ai_flags += ["--min_batch_size_vertex_ai",
                            str(args.min_batch_vertex_ai)]
    if args.machine_type:
        vertex_ai_flags += ["--machine_type", args.machine_type]

    total_start = time.time()
    results = []  # (label, success, elapsed, rate, stats)

    # ═══════════════════════════════════════════════════════════════
    #  LOCAL GPU — scaled rates (per_worker_capacity × num_workers)
    # ═══════════════════════════════════════════════════════════════
    if "local_gpu" in args.experiments:
        local_workers = args.local_gpu_workers
        rate_per_worker = args.local_gpu_rate_per_worker

        # Include machine type in output dirs/labels for per-machine Phase 7
        mt_short = ""
        if args.machine_type:
            mt_short = _short_machine_name(args.machine_type)

        print(f"\n{'=' * 70}")
        print(f"  LOCAL GPU SWEEP: {local_workers} workers")
        if mt_short:
            print(f"  Machine type: {args.machine_type} ({mt_short})")
        print(f"  Rate per worker: {rate_per_worker} msg/s")
        for nw in local_workers:
            print(f"    {nw} worker(s) → {nw * rate_per_worker} msg/s")
        print(f"{'=' * 70}\n")

        for nw in local_workers:
            rate = nw * rate_per_worker
            if mt_short:
                out_dir = os.path.join(output_base,
                                       f"local_gpu_{mt_short}_{nw}w")
                label = f"local_gpu {mt_short} ({nw}w)"
            else:
                out_dir = os.path.join(output_base, f"local_gpu_{nw}w")
                label = f"local_gpu ({nw}w)"
            success, elapsed = run_benchmark(
                "local_gpu", nw, rate, out_dir, args.duration, local_gpu_flags)
            stats = _read_stats(out_dir, "local_gpu", rate)
            results.append((label, success, elapsed, rate, stats))

    # ═══════════════════════════════════════════════════════════════
    #  VERTEX AI — grid: endpoint machine × replicas × workers
    # ═══════════════════════════════════════════════════════════════
    if "vertex_ai" in args.experiments:
        vertex_workers = args.vertex_ai_workers
        vertex_rate_cap = args.vertex_ai_rate
        rate_per_replica = args.vertex_ai_rate_per_replica
        replicas_list = sorted(args.vertex_ai_replicas)
        endpoint_machines = args.vertex_ai_endpoint_machines

        def compute_vertex_rate(replicas):
            """Compute proportional rate: per_replica × replicas, capped."""
            if rate_per_replica is not None:
                return min(rate_per_replica * replicas, vertex_rate_cap)
            return vertex_rate_cap

        if endpoint_machines:
            # Grid search: group by endpoint machine type (slow), then replicas (fast)
            print(f"\n{'=' * 70}")
            print(f"  VERTEX AI GRID SEARCH")
            print(f"  Endpoint machines: {endpoint_machines}")
            print(f"  Replicas: {replicas_list}")
            print(f"  Workers: {vertex_workers}")
            if rate_per_replica:
                print(f"  Rate: {rate_per_replica} msg/s per replica "
                      f"(capped at {vertex_rate_cap})")
                for r in replicas_list:
                    print(f"    {r} replica(s) → {compute_vertex_rate(r)} msg/s")
            else:
                print(f"  Rate: {vertex_rate_cap} msg/s (fixed)")
            total_runs = len(endpoint_machines) * len(replicas_list) * len(vertex_workers)
            print(f"  Total runs: {total_runs}")
            print(f"{'=' * 70}\n")

            for mt_idx, endpoint_mt in enumerate(endpoint_machines):
                short_mt = _short_machine_name(endpoint_mt)

                # Change endpoint machine type (slow — ~15 min rolling restart)
                print(f"\n{'=' * 70}")
                print(f"  ENDPOINT MACHINE {mt_idx + 1}/{len(endpoint_machines)}: "
                      f"{endpoint_mt}")
                print(f"{'=' * 70}\n")

                # Scale to 1 replica with new machine type first
                if not scale_endpoint(replicas=1, machine_type=endpoint_mt,
                                      env_file=args.env_file):
                    print(f"  ERROR: Failed to set endpoint to {endpoint_mt}. "
                          f"Skipping.", flush=True)
                    continue

                for replicas in replicas_list:
                    # Scale replicas (fast — ~2-3 min, no VM reboot)
                    if replicas != 1:  # already at 1 from machine change
                        if not scale_endpoint(replicas=replicas,
                                              env_file=args.env_file):
                            print(f"  WARNING: Failed to scale to {replicas} "
                                  f"replicas. Skipping.", flush=True)
                            continue

                    vertex_rate = compute_vertex_rate(replicas)
                    print(f"  Rate for {replicas} replica(s): "
                          f"{vertex_rate} msg/s", flush=True)

                    for nw in vertex_workers:
                        out_dir = os.path.join(
                            output_base,
                            f"vertex_ai_{short_mt}",
                            f"r{replicas}_w{nw}")
                        success, elapsed = run_benchmark(
                            "vertex_ai", nw, vertex_rate, out_dir,
                            args.duration, vertex_ai_flags)
                        stats = _read_stats(out_dir, "vertex_ai", vertex_rate)
                        label = f"vertex_ai {short_mt} (r{replicas}_w{nw})"
                        results.append((label, success, elapsed, vertex_rate,
                                        stats))
        else:
            # Simple sweep: no endpoint machine changes, just scale replicas
            print(f"\n{'=' * 70}")
            print(f"  VERTEX AI SWEEP: replicas {replicas_list}, "
                  f"workers {vertex_workers}")
            if rate_per_replica:
                print(f"  Rate: {rate_per_replica} msg/s per replica "
                      f"(capped at {vertex_rate_cap})")
            else:
                print(f"  Rate: {vertex_rate_cap} msg/s (fixed)")
            print(f"{'=' * 70}\n")

            for replicas in replicas_list:
                if not scale_endpoint(replicas=replicas,
                                      env_file=args.env_file):
                    print(f"  WARNING: Failed to scale to {replicas} replicas. "
                          f"Skipping.", flush=True)
                    continue

                vertex_rate = compute_vertex_rate(replicas)
                print(f"  Rate for {replicas} replica(s): "
                      f"{vertex_rate} msg/s", flush=True)

                for nw in vertex_workers:
                    out_dir = os.path.join(output_base, f"vertex_ai_r{replicas}_w{nw}")
                    success, elapsed = run_benchmark(
                        "vertex_ai", nw, vertex_rate, out_dir, args.duration,
                        vertex_ai_flags)
                    stats = _read_stats(out_dir, "vertex_ai", vertex_rate)
                    label = f"vertex_ai (r{replicas}_w{nw})"
                    results.append((label, success, elapsed, vertex_rate, stats))

    # ═══════════════════════════════════════════════════════════════
    #  SUMMARY
    # ═══════════════════════════════════════════════════════════════
    total_elapsed = (time.time() - total_start) / 60

    print(f"\n{'=' * 70}")
    print("  SCALE VERIFICATION COMPLETE")
    print(f"{'=' * 70}")
    print(f"  Total time: {total_elapsed:.0f} min ({total_elapsed / 60:.1f} hrs)\n")

    # Print results table
    print(f"  {'Config':<35} {'Rate':>6} {'Status':<6} {'Time':>6} {'Throughput':>12} "
          f"{'p50':>10} {'p95':>10} {'p99':>10}")
    print(f"  {'─' * 35} {'─' * 6} {'─' * 6} {'─' * 6} {'─' * 12} "
          f"{'─' * 10} {'─' * 10} {'─' * 10}")

    for label, success, elapsed, rate, stats in results:
        status = "OK" if success else "FAIL"
        if stats:
            print(f"  {label:<35} {rate:>5} {status:<6} {elapsed:>5.1f}m "
                  f"{stats['throughput']:>10.1f}/s "
                  f"{stats['latency_p50']:>8.0f}ms "
                  f"{stats['latency_p95']:>8.0f}ms "
                  f"{stats['latency_p99']:>8.0f}ms")
        else:
            print(f"  {label:<35} {rate:>5} {status:<6} {elapsed:>5.1f}m "
                  f"{'NO DATA':>10}")

    # Save summary JSON — merge into existing file to preserve results
    # from prior invocations (e.g., per-machine Local GPU + Vertex AI)
    summary_path = os.path.join(output_base, "sweep_summary.json")
    existing = {}
    if os.path.exists(summary_path):
        try:
            with open(summary_path) as f:
                existing = json.load(f)
            print(f"\n  Merging with {len(existing)} existing entries in "
                  f"sweep_summary.json", flush=True)
        except (json.JSONDecodeError, IOError):
            pass

    for label, success, elapsed, rate, stats in results:
        entry = {"rate": rate, "elapsed_min": round(elapsed, 1)}
        if stats:
            entry.update(stats)
        existing[label] = entry

    with open(summary_path, "w") as f:
        json.dump(existing, f, indent=2)
    print(f"\n  Summary saved: {summary_path} "
          f"({len(existing)} total entries)")

    print(f"\n{'=' * 70}\n")

    if not all(s for _, s, _, _, _ in results):
        sys.exit(1)


def _read_stats(output_dir, mode, rate):
    """Read benchmark_results.json and return stats for the given mode at the given rate."""
    path = os.path.join(output_dir, "benchmark_results.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            data = json.load(f)
        return data.get(mode, {}).get(str(rate), None)
    except (json.JSONDecodeError, KeyError):
        return None


if __name__ == "__main__":
    main()
