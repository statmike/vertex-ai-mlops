#!/usr/bin/env python3
"""Phase 8: Cost analysis and recommendations.

Reads Phase 7 sweep results, filters to configurations that meet the
throughput/latency goal, computes $/hour for each, and outputs a ranked
comparison table.

Cost model:
  Local GPU:
    $/hour = workers_needed × (worker_machine_price + gpu_price)

  Vertex AI:
    $/hour = workers_needed × worker_machine_price
           + replicas × (endpoint_machine_price + endpoint_gpu_price)

Usage:
  uv run python scripts/cost_analysis.py --data-dir data/runs/my_run
  uv run python scripts/cost_analysis.py --data-dir data/runs/my_run \
      --target-rate 1000 --target-p99-ms 750
"""

import argparse
import json
import math
import os
import sys


def load_pricing(pricing_path="pricing.json"):
    """Load pricing data from JSON file."""
    if not os.path.exists(pricing_path):
        print(f"  WARNING: {pricing_path} not found, using defaults.", flush=True)
        return {
            "compute_engine": {
                "machines": {
                    "n1-standard-4": 0.19, "n1-standard-8": 0.38,
                    "g2-standard-4": 0.71, "g2-standard-8": 0.85,
                },
                "gpu_accelerators": {
                    "nvidia-tesla-t4": 0.35,
                },
            },
            "vertex_ai_prediction": {
                "machines": {
                    "n1-standard-4": 0.219, "n1-standard-8": 0.438,
                    "g2-standard-4": 0.81, "g2-standard-8": 0.98,
                },
                "gpu_accelerators": {
                    "nvidia-tesla-t4": 0.402,
                },
            },
            "gpu_inclusive_families": ["g2", "a2", "a3"],
        }
    with open(pricing_path) as f:
        return json.load(f)


def detect_gpu_type(env_file=".env"):
    """Detect GPU type from .env file."""
    if not os.path.exists(env_file):
        return "nvidia-tesla-t4"
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line.startswith("GPU_TYPE="):
                return line.split("=", 1)[1].strip()
    return "nvidia-tesla-t4"


def parse_config_label(label):
    """Parse a sweep summary label into its components.

    Examples:
      "local_gpu (3w)" -> {"experiment": "local_gpu", "workers": 3}
      "local_gpu n1s4 (3w)" -> {"experiment": "local_gpu",
          "machine_short": "n1s4", "workers": 3}
      "vertex_ai n1s4 (r10_w8)" -> {"experiment": "vertex_ai",
          "endpoint_machine_short": "n1s4", "replicas": 10, "workers": 8}
      "vertex_ai (r10_w8)" -> {"experiment": "vertex_ai",
          "replicas": 10, "workers": 8}
    """
    parts = label.split()
    config = {"experiment": parts[0]}

    if parts[0] == "local_gpu":
        # "local_gpu (3w)" or "local_gpu n1s4 (3w)"
        for part in parts[1:]:
            part = part.strip("()")
            if part.endswith("w"):
                try:
                    config["workers"] = int(part[:-1])
                except ValueError:
                    pass
            elif not part.startswith("("):
                config["machine_short"] = part
    else:
        # vertex_ai with optional machine short name
        for part in parts[1:]:
            part = part.strip("()")
            if part.startswith("r") and "_w" in part:
                r, w = part.split("_w")
                config["replicas"] = int(r[1:])
                config["workers"] = int(w)
            elif not part.startswith("("):
                config["endpoint_machine_short"] = part

    return config


def expand_machine_short(short):
    """Expand short machine name: n1s4 -> n1-standard-4."""
    if short and len(short) >= 3:
        # Pattern: {family}s{cpus} -> {family}-standard-{cpus}
        for prefix in ["n1", "n2", "g2", "a2", "a3"]:
            if short.startswith(prefix + "s"):
                cpus = short[len(prefix) + 1:]
                return f"{prefix}-standard-{cpus}"
    return short


_GPU_INCLUSIVE_FAMILIES_DEFAULT = ("g2", "a2", "a3")


def _gpu_included_in_machine(machine_type, pricing=None):
    """Check if GPU is included in machine type price (accelerator-optimized VMs).

    G2 (L4), A2 (A100), A3 (H100) machine families include GPUs in the
    machine price. N1/N2/E2/C2 etc. require separate GPU add-ons.

    Reads gpu_inclusive_families from pricing data if available; otherwise
    falls back to built-in defaults.
    """
    if not machine_type:
        return False
    families = _GPU_INCLUSIVE_FAMILIES_DEFAULT
    if pricing and "gpu_inclusive_families" in pricing:
        families = tuple(f.lower() for f in pricing["gpu_inclusive_families"])
    family = machine_type.split("-")[0].lower()
    return family in families


def compute_cost(config, pricing, gpu_type, worker_machine, target_rate,
                  vertex_worker_machine=None):
    """Compute $/hour for a configuration to serve target_rate.

    Returns dict with cost breakdown or None if insufficient data.

    For Vertex AI configs, both workers AND replicas are scaled
    proportionally to reach the target rate. Workers are priced as
    CPU-only machines (vertex_worker_machine) since they only do HTTP
    calls to the endpoint — no GPU needed on the Dataflow side.
    """
    experiment = config["experiment"]
    workers = config.get("workers", 1)
    throughput = config.get("throughput", 0)

    if throughput <= 0:
        return None

    if experiment == "local_gpu":
        # Use per-machine worker price if label includes machine type
        machine_short = config.get("machine_short")
        actual_worker_machine = (expand_machine_short(machine_short)
                                 if machine_short else worker_machine)

        # Scale up to target rate
        workers_needed = math.ceil(target_rate / (throughput / workers))
        ce = pricing["compute_engine"]
        machine_price = ce["machines"].get(actual_worker_machine, 0)
        # GPU-inclusive machine families (g2, a2, a3) already include GPU in
        # their price — don't add a separate GPU charge
        if _gpu_included_in_machine(actual_worker_machine, pricing):
            gpu_price = 0.0
        else:
            gpu_price = ce["gpu_accelerators"].get(gpu_type, 0)
        cost_per_hour = workers_needed * (machine_price + gpu_price)

        breakdown = f"{workers_needed}w × ${machine_price:.2f}"
        if gpu_price > 0:
            breakdown = f"{workers_needed}w × (${machine_price:.2f} + ${gpu_price:.2f})"
        else:
            breakdown += " (GPU included)"

        return {
            "workers_needed": workers_needed,
            "replicas": None,
            "worker_machine": actual_worker_machine,
            "cost_per_hour": round(cost_per_hour, 2),
            "cost_per_million_msgs": round(
                cost_per_hour / (target_rate * 3.6) * 1000, 2)
                if target_rate > 0 else 0,
            "breakdown": breakdown,
        }

    elif experiment == "vertex_ai":
        replicas = config.get("replicas", 1)
        # Determine endpoint machine type
        emt_short = config.get("endpoint_machine_short", "")
        emt = expand_machine_short(emt_short)

        # Scale BOTH workers AND replicas proportionally to reach target
        # rate. The tested config achieved `throughput` at `replicas`
        # replicas with `workers` workers — preserve that ratio.
        scale_factor = target_rate / throughput if throughput > 0 else 1
        replicas_needed = max(replicas, math.ceil(replicas * scale_factor))
        workers_needed = max(workers, math.ceil(workers * scale_factor))

        # Worker cost — Vertex AI Dataflow workers only send HTTP
        # requests to the endpoint; they don't need GPUs. Use CPU-only
        # machine pricing.
        ce = pricing["compute_engine"]
        vwm = vertex_worker_machine or "n1-standard-4"
        worker_machine_price = ce["machines"].get(vwm, 0)
        worker_cost = workers_needed * worker_machine_price

        # Endpoint cost (Vertex AI prediction pricing)
        vp = pricing["vertex_ai_prediction"]
        endpoint_machine_price = vp["machines"].get(emt, 0)
        if not emt or endpoint_machine_price == 0:
            print(f"  WARNING: No pricing for endpoint machine '{emt}' "
                  f"(label short='{emt_short}'). Endpoint cost will be "
                  f"underestimated.", flush=True)
        endpoint_gpu_price = vp["gpu_accelerators"].get(gpu_type, 0)
        # For GPU-inclusive families, the machine price already covers GPU
        if _gpu_included_in_machine(emt, pricing):
            endpoint_gpu_price = 0.0
        endpoint_cost = replicas_needed * (endpoint_machine_price
                                           + endpoint_gpu_price)

        cost_per_hour = worker_cost + endpoint_cost

        ep_breakdown = f"${endpoint_machine_price:.2f}"
        if endpoint_gpu_price > 0:
            ep_breakdown = (f"(${endpoint_machine_price:.2f}"
                           f" + ${endpoint_gpu_price:.2f})")
        else:
            ep_breakdown += " (GPU incl)"

        return {
            "workers_needed": workers_needed,
            "replicas": replicas_needed,
            "tested_replicas": replicas,
            "tested_workers": workers,
            "vertex_worker_machine": vwm,
            "endpoint_machine": emt,
            "cost_per_hour": round(cost_per_hour, 2),
            "cost_per_million_msgs": round(
                cost_per_hour / (target_rate * 3.6) * 1000, 2)
                if target_rate > 0 else 0,
            "breakdown": (f"{workers_needed}w × ${worker_machine_price:.2f}"
                         f" + {replicas_needed}r × {ep_breakdown}"),
        }

    return None


def main():
    parser = argparse.ArgumentParser(
        description="Phase 8: Cost analysis and recommendations"
    )
    parser.add_argument(
        "--data-dir", required=True,
        help="Run directory containing phase7_scale/sweep_summary.json",
    )
    parser.add_argument(
        "--target-rate", type=int, default=1000,
        help="Target throughput in msg/s (default: 1000)",
    )
    parser.add_argument(
        "--target-p99-ms", type=int, default=750,
        help="Target p99 latency in ms (default: 750)",
    )
    parser.add_argument(
        "--pricing-file", default="pricing.json",
        help="Path to pricing JSON file (default: pricing.json)",
    )
    parser.add_argument(
        "--env-file", default=".env",
        help="Path to .env file for GPU type detection (default: .env)",
    )
    parser.add_argument(
        "--worker-machine", default=None,
        help="Dataflow worker machine type for Local GPU (auto-detected from Phase 6 if not set)",
    )
    parser.add_argument(
        "--vertex-worker-machine", default="n1-standard-4",
        help="Dataflow worker machine type for Vertex AI cost projection. "
             "Vertex AI workers only do HTTP calls — no GPU needed. "
             "(default: n1-standard-4)",
    )
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(base_dir)

    # Load pricing
    pricing = load_pricing(args.pricing_file)
    gpu_type = detect_gpu_type(args.env_file)

    # Detect worker machine from Phase 6 analysis
    worker_machine = args.worker_machine
    if not worker_machine:
        retune_path = os.path.join(args.data_dir, "phase6_retune", "analysis.json")
        if os.path.exists(retune_path):
            with open(retune_path) as f:
                retune = json.load(f)
            worker_machine = retune.get("best_settings", {}).get("machine_type")
        if not worker_machine:
            # Fall back to .env
            env_path = args.env_file
            if os.path.exists(env_path):
                with open(env_path) as f:
                    for line in f:
                        if line.strip().startswith("MACHINE_TYPE="):
                            worker_machine = line.strip().split("=", 1)[1]
                            break
        if not worker_machine:
            worker_machine = "n1-standard-4"

    # Load Phase 7 results
    sweep_path = os.path.join(args.data_dir, "phase7_scale", "sweep_summary.json")
    if not os.path.exists(sweep_path):
        print(f"  ERROR: {sweep_path} not found. Run Phase 7 first.", flush=True)
        sys.exit(1)

    with open(sweep_path) as f:
        sweep_data = json.load(f)

    # Filter to qualifying configurations
    qualifying = []
    for label, data in sweep_data.items():
        tp = data.get("processing_throughput", data.get("throughput", 0))
        p99 = data.get("latency_p99", 99999)

        # Must meet throughput (90% of rate) AND p99 threshold
        if tp >= data.get("rate", 0) * 0.90 and p99 < args.target_p99_ms:
            config = parse_config_label(label)
            config["throughput"] = tp
            config["p50"] = data.get("latency_p50", 0)
            config["p99"] = p99
            config["rate"] = data.get("rate", 0)

            cost = compute_cost(config, pricing, gpu_type, worker_machine,
                               args.target_rate,
                               vertex_worker_machine=args.vertex_worker_machine)
            if cost:
                config.update(cost)
                qualifying.append(config)

    # Sort by cost
    qualifying.sort(key=lambda x: x.get("cost_per_hour", 99999))

    # Print results
    print(f"\n{'=' * 90}")
    print(f"  COST ANALYSIS — {args.target_rate} msg/s at p99 < {args.target_p99_ms}ms")
    print(f"{'=' * 90}")
    print(f"  GPU type:              {gpu_type}")
    print(f"  Local GPU workers:     {worker_machine}")
    print(f"  Vertex AI workers:     {args.vertex_worker_machine} (CPU-only, no GPU)")
    print(f"  Pricing source:        {pricing.get('source', 'unknown')}")
    print(f"  Region:                {pricing.get('region', 'unknown')}")
    print()

    if not qualifying:
        print("  No configurations met the target goal.")
        print(f"  Checked {len(sweep_data)} configs from {sweep_path}")
        print()

        # Show best non-qualifying for diagnostics
        print("  Top 5 configurations by throughput (not meeting goal):")
        sorted_all = sorted(sweep_data.items(),
                           key=lambda x: x[1].get("processing_throughput",
                                                    x[1].get("throughput", 0)),
                           reverse=True)[:5]
        for label, data in sorted_all:
            tp = data.get("processing_throughput", data.get("throughput", 0))
            p99 = data.get("latency_p99", 0)
            print(f"    {label}: throughput={tp:.0f}, p99={p99:.0f}ms")
    else:
        # Header
        print(f"  {'Config':<40} {'Rate':>6} {'Tput':>6} {'p50':>6} {'p99':>6} "
              f"{'Wrkrs':>6} {'Repls':>6} {'$/hr':>8} {'$/M msgs':>9}")
        print(f"  {'─' * 40} {'─' * 6} {'─' * 6} {'─' * 6} {'─' * 6} "
              f"{'─' * 6} {'─' * 6} {'─' * 8} {'─' * 9}")

        for cfg in qualifying:
            exp = cfg["experiment"]
            proj_workers = cfg.get("workers_needed", "?")
            proj_replicas = cfg.get("replicas", "-")
            replicas_str = str(proj_replicas) if proj_replicas else "-"

            emt = cfg.get("endpoint_machine_short", "")
            if exp == "local_gpu":
                wm = cfg.get("worker_machine", worker_machine)
                label = f"Local GPU ({wm})"
            else:
                label = f"Vertex AI ({emt} r{proj_replicas})"

            print(f"  {label:<40} {cfg['rate']:>5} {cfg['throughput']:>5.0f} "
                  f"{cfg['p50']:>5.0f} {cfg['p99']:>5.0f} "
                  f"{proj_workers:>6} {replicas_str:>6} "
                  f"${cfg['cost_per_hour']:>7.2f} ${cfg['cost_per_million_msgs']:>8.2f}")

    # Notes
    print("  Notes:")
    print("  - Rate/Tput/p50/p99 are from the benchmark test at tested scale")
    print("  - Wrkrs/Repls are PROJECTED to reach the target rate")
    print("    (proportional scaling from tested config)")
    print("  - Vertex AI workers use CPU-only machines "
          f"({args.vertex_worker_machine}) — no GPU needed")
    print("  - Local GPU workers include GPU in machine cost")
    print("  - Projections assume linear scaling; actual results may vary")
    print(f"\n{'=' * 90}\n")

    # Save results
    output = {
        "target_rate": args.target_rate,
        "target_p99_ms": args.target_p99_ms,
        "gpu_type": gpu_type,
        "worker_machine": worker_machine,
        "vertex_worker_machine": args.vertex_worker_machine,
        "pricing": pricing,
        "qualifying_configs": qualifying,
        "total_configs_checked": len(sweep_data),
    }

    output_path = os.path.join(args.data_dir, "cost_analysis.json")
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"  Cost analysis saved: {output_path}", flush=True)


if __name__ == "__main__":
    main()
