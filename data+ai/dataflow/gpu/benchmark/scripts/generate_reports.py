#!/usr/bin/env python3
"""Generate drill-through benchmark reports with charts.

Produces markdown reports and matplotlib chart PNGs for each phase,
GPU summary, and cross-GPU overall report.

Usage:
    uv run python scripts/generate_reports.py --data-dir data/runs/t4_full --phase 1
    uv run python scripts/generate_reports.py --data-dir data/runs/t4_full --gpu-summary
    uv run python scripts/generate_reports.py --overall
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np


# ---------------------------------------------------------------------------
# Style / Colors  (reused from generate_report_charts.py)
# ---------------------------------------------------------------------------

def setup_style():
    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "#f8f9fa",
        "axes.grid": True,
        "grid.alpha": 0.3,
        "grid.linestyle": "--",
        "font.size": 11,
        "axes.titlesize": 14,
        "axes.titleweight": "bold",
        "axes.labelsize": 12,
    })


LOCAL_COLOR = "#1a73e8"
VERTEX_COLOR = "#ea4335"
LOCAL_LIGHT = "#a8c7fa"
VERTEX_LIGHT = "#f6aea9"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_json(path):
    with open(path) as f:
        return json.load(f)


def detect_gpu_label(data_dir):
    """Detect GPU label from data directory name."""
    name = os.path.basename(os.path.normpath(data_dir)).lower()
    if "t4" in name:
        return "T4"
    if "l4" in name:
        return "L4"
    return "GPU"


def detect_machine_types(data_dir):
    """Detect available machine type short names from phase5_machine."""
    p5 = os.path.join(data_dir, "phase5_machine")
    if not os.path.isdir(p5):
        return []
    machines = []
    for entry in sorted(os.listdir(p5)):
        full = os.path.join(p5, entry)
        if os.path.isdir(full):
            machines.append(entry)
    return machines


def machine_short(name):
    """n1-standard-4 -> n1s4, g2-standard-8 -> g2s8."""
    return re.sub(r"-standard-", "s", name)


def fmt_ms(v):
    """Format milliseconds for tables."""
    if v is None:
        return "-"
    if abs(v) >= 1000:
        return f"{v:,.0f}"
    return f"{v:.0f}"


def fmt_tp(v):
    if v is None:
        return "-"
    return f"{v:.1f}"


def ensure_dir(d):
    os.makedirs(d, exist_ok=True)


# Machine specs lookup: vCPUs and RAM
MACHINE_SPECS = {
    "n1-standard-4": {"vcpus": 4, "ram_gb": 15},
    "n1-standard-8": {"vcpus": 8, "ram_gb": 30},
    "g2-standard-4": {"vcpus": 4, "ram_gb": 16},
    "g2-standard-8": {"vcpus": 8, "ram_gb": 32},
}

GPU_DISPLAY_NAMES = {
    "nvidia-tesla-t4": "NVIDIA Tesla T4 (16 GB)",
    "nvidia-l4": "NVIDIA L4 (24 GB)",
}

GPU_SHORT_LABELS = {
    "nvidia-tesla-t4": "t4",
    "nvidia-l4": "l4",
}


def gpu_short(gpu_type):
    """nvidia-tesla-t4 -> t4, nvidia-l4 -> l4."""
    return GPU_SHORT_LABELS.get(gpu_type, gpu_type)


def fmt_infra(count, role, machine_short_name, gpu_type=None):
    """Format infrastructure in compact notation.

    Examples:
        fmt_infra(10, "dataflow", "n1s4", "nvidia-tesla-t4")
            → "10×dataflow:n1s4+t4"
        fmt_infra(10, "dataflow", "n1s4")
            → "10×dataflow:n1s4"
        fmt_infra(10, "endpoint", "n1s4", "nvidia-tesla-t4")
            → "10×endpoint:n1s4+t4"
    """
    spec = machine_short_name
    if gpu_type:
        spec += f"+{gpu_short(gpu_type)}"
    return f"{count}\u00d7{role}:{spec}"


def fmt_infra_local(count, machine_short_name, gpu_type):
    """Full Local GPU infrastructure label."""
    return fmt_infra(count, "dataflow", machine_short_name, gpu_type)


def fmt_infra_vertex(worker_count, worker_machine_short,
                     replica_count, endpoint_machine_short, gpu_type):
    """Full Vertex AI infrastructure label (workers + replicas)."""
    w = fmt_infra(worker_count, "dataflow", worker_machine_short)
    r = fmt_infra(replica_count, "endpoint", endpoint_machine_short, gpu_type)
    return f"{w} + {r}"


def load_env_config(data_dir):
    """Load environment config from the .env file or cost_analysis.json."""
    config = {
        "gpu_type": "unknown",
        "gpu_display": "GPU",
        "default_machine": "unknown",
        "vertex_endpoint_machine": "unknown",
        "vertex_worker_machine": "n1-standard-4",
        "model": "BERT-base (3-class text classification, max_seq_length=128)",
        "region": "us-central1",
    }

    # Detect GPU type from cost_analysis.json
    cost_path = os.path.join(data_dir, "cost_analysis.json")
    if os.path.exists(cost_path):
        cd = load_json(cost_path)
        config["gpu_type"] = cd.get("gpu_type", config["gpu_type"])
        config["vertex_worker_machine"] = cd.get("vertex_worker_machine",
                                                  config["vertex_worker_machine"])

    # Default machine comes from GPU type, not cost_analysis (which stores
    # the best scaling machine, not the Phase 1 default)
    gpu_label = detect_gpu_label(data_dir)
    if gpu_label == "T4":
        if config["gpu_type"] == "unknown":
            config["gpu_type"] = "nvidia-tesla-t4"
        config["default_machine"] = "n1-standard-4"
    elif gpu_label == "L4":
        if config["gpu_type"] == "unknown":
            config["gpu_type"] = "nvidia-l4"
        config["default_machine"] = "g2-standard-4"

    config["vertex_endpoint_machine"] = config["default_machine"]
    config["gpu_display"] = GPU_DISPLAY_NAMES.get(config["gpu_type"], config["gpu_type"])
    return config


def fmt_machine_spec(machine_type, gpu_type=None, gpu_included=False):
    """Format a machine type with its specs.

    Returns e.g. 'n1-standard-4 (4 vCPUs, 15 GB RAM) + 1x NVIDIA Tesla T4'
    """
    specs = MACHINE_SPECS.get(machine_type, {})
    vcpus = specs.get("vcpus", "?")
    ram = specs.get("ram_gb", "?")
    parts = [f"{machine_type} ({vcpus} vCPUs, {ram} GB RAM)"]
    if gpu_type:
        gpu_name = GPU_DISPLAY_NAMES.get(gpu_type, gpu_type)
        family = machine_type.split("-")[0]
        if family in ("g2", "a2", "a3"):
            parts[0] += f" -- includes 1x {gpu_name}"
        else:
            parts.append(f"1x {gpu_name}")
    return " + ".join(parts)


def configuration_table(env, params):
    """Generate a unified configuration table for a phase report.

    Shows ALL benchmark parameters with their values and provenance so
    readers can compare any phase against any other phase at a glance.

    Args:
        env: dict from load_env_config()
        params: dict of parameter overrides. Each key maps to a dict with:
            - value: display string for the setting value
            - status: provenance string, e.g. "Default", "Optimized (Phase 2)",
                      or "**Swept: 1--12**" for the parameter under test.
    """
    # Compact infrastructure labels
    default_ms = machine_short(env["default_machine"])
    gt = env.get("gpu_type")
    vw_ms = machine_short(env.get("vertex_worker_machine", "n1-standard-4"))
    ep_ms = machine_short(
        env.get("vertex_endpoint_machine", env["default_machine"]))

    # Full parameter list in logical order
    ALL_PARAMS = [
        # Infrastructure
        ("Local GPU Infrastructure",
         fmt_infra(1, "dataflow", default_ms, gt), "Fixed"),
        ("Vertex AI Infrastructure",
         fmt_infra_vertex(1, vw_ms, 1, ep_ms, gt), "Fixed"),
        ("Model", env["model"], "Fixed"),
        ("Region", env["region"], "Fixed"),
        # Scaling
        ("Workers", "1", "Default"),
        ("Endpoint Replicas", "1", "Default"),
        # Pipeline tuning
        ("Harness Threads", "12", "Default"),
        ("max_batch_size", "64", "Default"),
        ("min_batch_size", "1", "Default"),
        # Test parameters
        ("Publish Rates", "varies", ""),
        ("Duration per Rate", "100s", "Fixed"),
    ]

    md = ["## Configuration\n"]
    md.append("| Parameter | Value | Status |\n")
    md.append("|---|---|---|\n")
    for name, default_val, default_status in ALL_PARAMS:
        override = params.get(name, {})
        val = override.get("value", default_val)
        status = override.get("status", default_status)
        md.append(f"| {name} | {val} | {status} |\n")
    md.append("\n")
    return "".join(md)


def _load_phase6_settings(data_dir, machine_type):
    """Load best settings from Phase 6 analysis for a given machine type.

    Returns a dict with keys like threads_local_gpu, max_batch_vertex_ai, etc.
    Falls back to empty dict if data not available.
    """
    ms = machine_short(machine_type)
    ap = os.path.join(data_dir, "phase6_retune", ms, "analysis.json")
    if os.path.exists(ap):
        a = load_json(ap)
        return a.get("best_settings", {})
    return {}


# ---------------------------------------------------------------------------
# Phase 1: Baseline Capacity
# ---------------------------------------------------------------------------

def chart_phase1_latency(data, chart_dir, gpu_label):
    """Latency vs Rate: p50 solid + p99 dashed, log y-axis."""
    rates = sorted(int(r) for r in data.get("local_gpu", data.get("vertex_ai", {})).keys())
    if not rates:
        return None

    fig, ax = plt.subplots(figsize=(10, 5.5))

    for mode, color, label in [
        ("local_gpu", LOCAL_COLOR, "Local GPU"),
        ("vertex_ai", VERTEX_COLOR, "Vertex AI"),
    ]:
        if mode not in data:
            continue
        p50 = [data[mode][str(r)]["latency_p50"] for r in rates]
        p99 = [data[mode][str(r)]["latency_p99"] for r in rates]
        ax.plot(rates, p50, "o-", color=color, linewidth=2.5, markersize=8,
                label=f"{label} p50")
        ax.fill_between(rates, p50, p99, alpha=0.15, color=color)
        ax.plot(rates, p99, "s--", color=color, linewidth=1, markersize=5,
                alpha=0.6, label=f"{label} p99")

    ax.set_yscale("log")
    ax.set_xlabel("Publish Rate (msg/s)")
    ax.set_ylabel("End-to-End Latency (ms)")
    ax.set_title(f"Phase 1: Latency vs Rate ({gpu_label}, Default Settings)")
    ax.legend(loc="upper left", fontsize=9)
    ax.set_xticks(rates)
    fig.tight_layout()
    fname = "phase1_latency.png"
    fig.savefig(os.path.join(chart_dir, fname), dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fname


def chart_phase1_throughput(data, chart_dir, gpu_label):
    """Throughput vs Rate: both experiments with ideal diagonal."""
    rates = sorted(int(r) for r in data.get("local_gpu", data.get("vertex_ai", {})).keys())
    if not rates:
        return None

    fig, ax = plt.subplots(figsize=(10, 5.5))

    for mode, color, label in [
        ("local_gpu", LOCAL_COLOR, "Local GPU"),
        ("vertex_ai", VERTEX_COLOR, "Vertex AI"),
    ]:
        if mode not in data:
            continue
        tp = [data[mode][str(r)]["throughput"] for r in rates]
        ax.plot(rates, tp, "o-", color=color, linewidth=2.5, markersize=8,
                label=label)

    ax.plot(rates, rates, "k--", linewidth=1, alpha=0.4,
            label="Ideal (rate = throughput)")
    ax.set_xlabel("Publish Rate (msg/s)")
    ax.set_ylabel("Achieved Throughput (msg/s)")
    ax.set_title(f"Phase 1: Throughput vs Rate ({gpu_label})")
    ax.legend(loc="upper left", fontsize=9)
    ax.set_xticks(rates)
    fig.tight_layout()
    fname = "phase1_throughput.png"
    fig.savefig(os.path.join(chart_dir, fname), dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fname


def report_phase1(data_dir, report_dir):
    gpu_label = detect_gpu_label(data_dir)
    env = load_env_config(data_dir)
    path = os.path.join(data_dir, "phase1_capacity", "benchmark_results.json")
    if not os.path.exists(path):
        print(f"  SKIP Phase 1: {path} not found")
        return
    data = load_json(path)
    chart_dir = os.path.join(report_dir, "charts")
    ensure_dir(chart_dir)

    c1 = chart_phase1_latency(data, chart_dir, gpu_label)
    c2 = chart_phase1_throughput(data, chart_dir, gpu_label)
    print(f"  Charts: {c1}, {c2}")

    rates = sorted(int(r) for r in data.get("local_gpu", data.get("vertex_ai", {})).keys())

    md = [f"# Phase 1: Baseline Capacity ({gpu_label})\n"]
    md.append("[< GPU Summary](gpu_report.md)\n")
    md.append("## Going In\n")
    md.append("Single worker, all default settings. The question: "
              "**how many msg/s can one worker handle before latency degrades?**\n")
    md.append(configuration_table(env, {
        "Publish Rates": {"value": f"{', '.join(str(r) for r in rates)} msg/s",
                          "status": "**Swept**"},
    }))

    md.append("## Results\n")
    for mode, label in [("local_gpu", "Local GPU"), ("vertex_ai", "Vertex AI")]:
        if mode not in data:
            continue
        md.append(f"**{label}**\n")
        md.append("| Rate | Throughput | Latency p50 | p95 | p99 | GPU p50 | GPU p99 |\n")
        md.append("|---:|---:|---:|---:|---:|---:|---:|\n")
        for r in rates:
            s = data[mode][str(r)]
            md.append(f"| {r} | {fmt_tp(s['throughput'])} | "
                      f"{fmt_ms(s['latency_p50'])} ms | {fmt_ms(s['latency_p95'])} ms | "
                      f"{fmt_ms(s['latency_p99'])} ms | {fmt_ms(s['gpu_p50'])} ms | "
                      f"{fmt_ms(s['gpu_p99'])} ms |\n")
        md.append("\n")

    if c1:
        md.append(f"![Latency vs Rate](charts/{c1})\n")
    if c2:
        md.append(f"![Throughput vs Rate](charts/{c2})\n")

    # Auto-detect saturation points
    md.append("## Conclusion\n")
    for mode, label in [("local_gpu", "Local GPU"), ("vertex_ai", "Vertex AI")]:
        if mode not in data:
            continue
        prev_rate = None
        for r in rates:
            s = data[mode][str(r)]
            if s["latency_p50"] > 500:
                if prev_rate is not None:
                    md.append(f"**{label} saturates between {prev_rate}--{r} msg/s** "
                              f"(p50 jumps to {fmt_ms(s['latency_p50'])} ms).\n\n")
                else:
                    md.append(f"**{label} is saturated at the lowest rate tested "
                              f"({r} msg/s).**\n\n")
                break
            prev_rate = r
        else:
            md.append(f"**{label} handles all rates tested (up to {rates[-1]} msg/s) "
                      f"with p50 < 500ms.**\n\n")

    out = os.path.join(report_dir, "phase1_baseline.md")
    with open(out, "w") as f:
        f.write("".join(md))
    print(f"  Report: {out}")


# ---------------------------------------------------------------------------
# Phase 2: Thread Sweep
# ---------------------------------------------------------------------------

def chart_phase2_thread_sweep(data_dir, chart_dir, gpu_label):
    """Latency at reference rate vs thread count for both experiments."""
    threads_dir = os.path.join(data_dir, "phase2_threads")
    if not os.path.isdir(threads_dir):
        return None

    thread_counts = sorted(
        int(d.replace("threads_", ""))
        for d in os.listdir(threads_dir)
        if d.startswith("threads_")
    )
    if not thread_counts:
        return None

    # Use a moderate reference rate (75 msg/s)
    ref_rate = "75"

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    for ax, mode, color, label in [
        (ax1, "local_gpu", LOCAL_COLOR, "Local GPU"),
        (ax2, "vertex_ai", VERTEX_COLOR, "Vertex AI"),
    ]:
        p50s = []
        p99s = []
        valid_tc = []
        for tc in thread_counts:
            path = os.path.join(threads_dir, f"threads_{tc}", "benchmark_results.json")
            if not os.path.exists(path):
                continue
            d = load_json(path)
            if mode not in d or ref_rate not in d[mode]:
                continue
            p50s.append(d[mode][ref_rate]["latency_p50"])
            p99s.append(d[mode][ref_rate]["latency_p99"])
            valid_tc.append(tc)

        if valid_tc:
            ax.plot(valid_tc, p50s, "o-", color=color, linewidth=2.5,
                    markersize=8, label="p50")
            ax.plot(valid_tc, p99s, "s--", color=color, linewidth=1.5,
                    markersize=6, alpha=0.6, label="p99")
            ax.set_yscale("log")
            ax.set_xlabel("Harness Thread Count")
            ax.set_ylabel(f"Latency at {ref_rate} msg/s (ms)")
            ax.set_title(f"{label}: Latency vs Threads")
            ax.set_xticks(valid_tc)
            ax.legend(fontsize=9)

    fig.suptitle(f"Phase 2: Thread Count Impact ({gpu_label})",
                 fontsize=15, fontweight="bold", y=1.02)
    fig.tight_layout()
    fname = "phase2_thread_sweep.png"
    fig.savefig(os.path.join(chart_dir, fname), dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fname


def chart_phase2_capacity(data_dir, chart_dir, gpu_label):
    """Bar chart: capacity at default (12) threads vs best thread count."""
    threads_dir = os.path.join(data_dir, "phase2_threads")
    if not os.path.isdir(threads_dir):
        return None

    thread_counts = sorted(
        int(d.replace("threads_", ""))
        for d in os.listdir(threads_dir)
        if d.startswith("threads_")
    )

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    for ax, mode, color, lighter, label in [
        (ax1, "local_gpu", LOCAL_COLOR, LOCAL_LIGHT, "Local GPU"),
        (ax2, "vertex_ai", VERTEX_COLOR, VERTEX_LIGHT, "Vertex AI"),
    ]:
        # Find best thread count: highest rate where p99 < 750ms
        best_tc = None
        best_cap = 0
        for tc in thread_counts:
            path = os.path.join(threads_dir, f"threads_{tc}", "benchmark_results.json")
            if not os.path.exists(path):
                continue
            d = load_json(path)
            if mode not in d:
                continue
            for rate_s in sorted(d[mode].keys(), key=int, reverse=True):
                s = d[mode][rate_s]
                if s["latency_p99"] < 750 and int(rate_s) > best_cap:
                    best_cap = int(rate_s)
                    best_tc = tc
                    break

        # Default 12 threads capacity
        default_cap = 0
        d12_path = os.path.join(threads_dir, "threads_12", "benchmark_results.json")
        if os.path.exists(d12_path):
            d12 = load_json(d12_path)
            if mode in d12:
                for rate_s in sorted(d12[mode].keys(), key=int, reverse=True):
                    if d12[mode][rate_s]["latency_p99"] < 750:
                        default_cap = int(rate_s)
                        break

        if best_tc is not None:
            labels = [f"12 threads\n(default)", f"{best_tc} threads\n(best)"]
            caps = [default_cap, best_cap]
            colors = [lighter, color]
            bars = ax.bar(labels, caps, color=colors, width=0.4, zorder=3)
            for bar, cap in zip(bars, caps):
                ax.text(bar.get_x() + bar.get_width() / 2, cap + 3,
                        f"{cap} msg/s", ha="center", fontweight="bold", fontsize=11)
            ax.set_ylabel("Per-Worker Capacity (msg/s, p99<750ms)")
            ax.set_title(f"{label}: Thread Optimization")
            ax.set_ylim(0, max(caps) * 1.25)

    fig.suptitle(f"Phase 2: Default vs Optimal Thread Count ({gpu_label})",
                 fontsize=15, fontweight="bold", y=1.02)
    fig.tight_layout()
    fname = "phase2_capacity.png"
    fig.savefig(os.path.join(chart_dir, fname), dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fname


def report_phase2(data_dir, report_dir):
    gpu_label = detect_gpu_label(data_dir)
    env = load_env_config(data_dir)
    threads_dir = os.path.join(data_dir, "phase2_threads")
    if not os.path.isdir(threads_dir):
        print(f"  SKIP Phase 2: {threads_dir} not found")
        return
    chart_dir = os.path.join(report_dir, "charts")
    ensure_dir(chart_dir)

    c1 = chart_phase2_thread_sweep(data_dir, chart_dir, gpu_label)
    c2 = chart_phase2_capacity(data_dir, chart_dir, gpu_label)
    print(f"  Charts: {c1}, {c2}")

    thread_counts = sorted(
        int(d.replace("threads_", ""))
        for d in os.listdir(threads_dir)
        if d.startswith("threads_")
    )

    md = [f"# Phase 2: Thread Count Tuning ({gpu_label})\n"]
    md.append("[< GPU Summary](gpu_report.md)\n")
    md.append("## Going In\n")
    md.append("Phase 1 showed default 12 harness threads create GPU lock contention "
              "for Local GPU (all threads compete for the single GPU) while providing "
              "natural HTTP parallelism for Vertex AI. The hypothesis: **fewer threads "
              "should reduce lock contention for Local GPU.**\n")
    md.append(configuration_table(env, {
        "Harness Threads": {"value": f"**{', '.join(str(t) for t in thread_counts)}**",
                            "status": "**Swept**"},
    }))

    md.append("## Results: Latency at 75 msg/s by Thread Count\n")
    for mode, label in [("local_gpu", "Local GPU"), ("vertex_ai", "Vertex AI")]:
        md.append(f"\n**{label}**\n")
        md.append("| Threads | Throughput | p50 | p95 | p99 |\n")
        md.append("|---:|---:|---:|---:|---:|\n")
        for tc in thread_counts:
            path = os.path.join(threads_dir, f"threads_{tc}", "benchmark_results.json")
            if not os.path.exists(path):
                continue
            d = load_json(path)
            if mode not in d or "75" not in d[mode]:
                continue
            s = d[mode]["75"]
            md.append(f"| {tc} | {fmt_tp(s['throughput'])} | "
                      f"{fmt_ms(s['latency_p50'])} ms | {fmt_ms(s['latency_p95'])} ms | "
                      f"{fmt_ms(s['latency_p99'])} ms |\n")

    if c1:
        md.append(f"\n![Thread Sweep](charts/{c1})\n")
    if c2:
        md.append(f"\n![Capacity Comparison](charts/{c2})\n")

    md.append("\n## Conclusion\n")
    md.append("Thread count has **opposite effects** on the two approaches:\n\n")
    md.append("- **Local GPU**: Fewer threads reduce GPU lock contention. "
              "With only 2-3 threads, one thread runs inference while the other "
              "tokenizes, dramatically improving capacity.\n")
    md.append("- **Vertex AI**: More threads mean more concurrent HTTP clients. "
              "Reducing threads starves the endpoint of work.\n\n")
    md.append("**Decision**: Per-experiment thread counts optimized separately.\n")

    out = os.path.join(report_dir, "phase2_threads.md")
    with open(out, "w") as f:
        f.write("".join(md))
    print(f"  Report: {out}")


# ---------------------------------------------------------------------------
# Phase 3: Batch Size
# ---------------------------------------------------------------------------

def chart_phase3_batch(data_dir, chart_dir, gpu_label):
    """2x2 grid: Local GPU + Vertex AI x two reference rates."""
    batch_dir = os.path.join(data_dir, "phase3_max_batch")
    if not os.path.isdir(batch_dir):
        return None

    batch_sizes = sorted(
        int(d.replace("batch_", ""))
        for d in os.listdir(batch_dir)
        if d.startswith("batch_")
    )
    if not batch_sizes:
        return None

    # Find two reference rates: one healthy, one near saturation
    first_data = load_json(os.path.join(batch_dir, f"batch_{batch_sizes[0]}",
                                        "benchmark_results.json"))
    all_rates = set()
    for mode in ["local_gpu", "vertex_ai"]:
        if mode in first_data:
            all_rates.update(int(r) for r in first_data[mode].keys())
    rates = sorted(all_rates)
    if len(rates) < 2:
        ref_rates = rates
    else:
        # Pick a mid-rate and the highest
        ref_rates = [rates[len(rates) // 2], rates[-1]]

    fig, axes = plt.subplots(2, len(ref_rates), figsize=(7 * len(ref_rates), 11))
    if len(ref_rates) == 1:
        axes = axes.reshape(2, 1)

    for col, rate in enumerate(ref_rates):
        for row, (mode, color, label) in enumerate([
            ("local_gpu", LOCAL_COLOR, "Local GPU"),
            ("vertex_ai", VERTEX_COLOR, "Vertex AI"),
        ]):
            ax = axes[row, col]
            p50s = []
            valid_bs = []
            for bs in batch_sizes:
                path = os.path.join(batch_dir, f"batch_{bs}", "benchmark_results.json")
                if not os.path.exists(path):
                    continue
                d = load_json(path)
                if mode not in d or str(rate) not in d[mode]:
                    continue
                p50s.append(d[mode][str(rate)]["latency_p50"])
                valid_bs.append(bs)

            if not valid_bs:
                ax.set_visible(False)
                continue

            x = np.arange(len(valid_bs))
            # Cap extreme outliers
            display = [min(v, 10000) for v in p50s]
            bars = ax.bar(x, display, 0.6, color=color, zorder=3)

            # Highlight best
            best_idx = int(np.argmin(p50s))
            dark = "#0d47a1" if mode == "local_gpu" else "#b71c1c"
            bars[best_idx].set_color(dark)
            ax.annotate(f"{p50s[best_idx]:.0f}ms",
                        xy=(best_idx, display[best_idx]),
                        fontsize=10, fontweight="bold", color=dark, ha="center",
                        xytext=(best_idx, max(display) * 0.85),
                        arrowprops=dict(arrowstyle="->", color=dark))

            # Mark anomalies
            for i, v in enumerate(p50s):
                if v > 10000:
                    ax.annotate(f"{v / 1000:.0f}s!", xy=(i, 10000), fontsize=8,
                                color="darkred", ha="center", fontweight="bold")

            ax.set_xticks(x)
            ax.set_xticklabels([str(bs) for bs in valid_bs])
            ax.set_xlabel("max_batch_size")
            ax.set_ylabel("Latency p50 (ms)")
            ax.set_title(f"{label} -- {rate} msg/s")

    fig.suptitle(f"Phase 3: Batch Size Sweep ({gpu_label})",
                 fontsize=15, fontweight="bold", y=1.01)
    fig.tight_layout()
    fname = "phase3_batch.png"
    fig.savefig(os.path.join(chart_dir, fname), dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fname


def report_phase3(data_dir, report_dir):
    gpu_label = detect_gpu_label(data_dir)
    env = load_env_config(data_dir)
    batch_dir = os.path.join(data_dir, "phase3_max_batch")
    if not os.path.isdir(batch_dir):
        print(f"  SKIP Phase 3: {batch_dir} not found")
        return
    chart_dir = os.path.join(report_dir, "charts")
    ensure_dir(chart_dir)

    batch_sizes = sorted(
        int(d.replace("batch_", ""))
        for d in os.listdir(batch_dir)
        if d.startswith("batch_")
    )

    c1 = chart_phase3_batch(data_dir, chart_dir, gpu_label)
    print(f"  Charts: {c1}")

    # Get all available rates
    first_data = load_json(os.path.join(batch_dir, f"batch_{batch_sizes[0]}",
                                        "benchmark_results.json"))

    # Get optimized threads from Phase 6 analysis (for the default machine)
    p6_settings = _load_phase6_settings(data_dir, env["default_machine"])
    threads_local = p6_settings.get("threads_local_gpu", "?")
    threads_vertex = p6_settings.get("threads_vertex_ai", "?")

    md = [f"# Phase 3: Batch Size Optimization ({gpu_label})\n"]
    md.append("[< GPU Summary](gpu_report.md)\n")
    md.append("## Going In\n")
    md.append("Thread counts are fixed from Phase 2. Now we sweep `max_batch_size` -- "
              "the max elements RunInference groups per `run_inference()` call.\n")
    md.append(configuration_table(env, {
        "Harness Threads": {"value": f"Local GPU={threads_local}, Vertex AI={threads_vertex}",
                            "status": "Optimized (Phase 2)"},
        "max_batch_size": {"value": f"**{', '.join(str(b) for b in batch_sizes)}**",
                           "status": "**Swept**"},
    }))

    # Build result tables per mode per rate
    md.append("## Results\n")
    for mode, label in [("local_gpu", "Local GPU"), ("vertex_ai", "Vertex AI")]:
        if mode not in first_data:
            continue
        rates = sorted(int(r) for r in first_data[mode].keys())
        for rate in rates:
            md.append(f"\n**{label} at {rate} msg/s**\n")
            md.append("| max_batch | Throughput | p50 | p95 | p99 |\n")
            md.append("|---:|---:|---:|---:|---:|\n")
            for bs in batch_sizes:
                path = os.path.join(batch_dir, f"batch_{bs}", "benchmark_results.json")
                if not os.path.exists(path):
                    continue
                d = load_json(path)
                if mode not in d or str(rate) not in d[mode]:
                    continue
                s = d[mode][str(rate)]
                md.append(f"| {bs} | {fmt_tp(s['throughput'])} | "
                          f"{fmt_ms(s['latency_p50'])} ms | "
                          f"{fmt_ms(s['latency_p95'])} ms | "
                          f"{fmt_ms(s['latency_p99'])} ms |\n")

    if c1:
        md.append(f"\n![Batch Size Sweep](charts/{c1})\n")

    md.append("\n## Conclusion\n")
    md.append("Larger batches amortize GPU kernel overhead (Local GPU) and "
              "HTTP round-trip overhead (Vertex AI). The optimal batch size balances "
              "throughput gains against accumulation wait time.\n")

    out = os.path.join(report_dir, "phase3_batch.md")
    with open(out, "w") as f:
        f.write("".join(md))
    print(f"  Report: {out}")


# ---------------------------------------------------------------------------
# Phase 4: Min Batch Size
# ---------------------------------------------------------------------------

def chart_phase4_minbatch(data_dir, chart_dir, gpu_label):
    """Latency vs min_batch_size at reference rate."""
    mb_dir = os.path.join(data_dir, "phase4_min_batch")
    if not os.path.isdir(mb_dir):
        return None

    min_sizes = sorted(
        int(d.replace("min_", ""))
        for d in os.listdir(mb_dir)
        if d.startswith("min_")
    )
    if not min_sizes:
        return None

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    for ax, mode, color, label in [
        (ax1, "local_gpu", LOCAL_COLOR, "Local GPU"),
        (ax2, "vertex_ai", VERTEX_COLOR, "Vertex AI"),
    ]:
        p50s, p99s, valid_ms = [], [], []
        for ms in min_sizes:
            path = os.path.join(mb_dir, f"min_{ms}", "benchmark_results.json")
            if not os.path.exists(path):
                continue
            d = load_json(path)
            if mode not in d or not d[mode]:
                continue
            # Use the first rate available
            rate_key = next(iter(d[mode]))
            s = d[mode][rate_key]
            p50s.append(s["latency_p50"])
            p99s.append(s["latency_p99"])
            valid_ms.append(ms)

        if not valid_ms:
            ax.set_visible(False)
            continue

        ax.plot(valid_ms, p50s, "o-", color=color, linewidth=2.5,
                markersize=8, label="p50")
        ax.plot(valid_ms, p99s, "s--", color=color, linewidth=1.5,
                markersize=6, alpha=0.6, label="p99")
        ax.set_xlabel("min_batch_size")
        ax.set_ylabel("Latency (ms)")
        ax.set_title(f"{label}: Latency vs min_batch_size")
        ax.set_xscale("log", base=2)
        ax.set_xticks(valid_ms)
        ax.get_xaxis().set_major_formatter(ticker.ScalarFormatter())
        ax.legend(fontsize=9)

    fig.suptitle(f"Phase 4: Min Batch Size Sweep ({gpu_label})",
                 fontsize=15, fontweight="bold", y=1.02)
    fig.tight_layout()
    fname = "phase4_minbatch.png"
    fig.savefig(os.path.join(chart_dir, fname), dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fname


def report_phase4(data_dir, report_dir):
    gpu_label = detect_gpu_label(data_dir)
    env = load_env_config(data_dir)
    mb_dir = os.path.join(data_dir, "phase4_min_batch")
    if not os.path.isdir(mb_dir):
        print(f"  SKIP Phase 4: {mb_dir} not found")
        return
    chart_dir = os.path.join(report_dir, "charts")
    ensure_dir(chart_dir)

    min_sizes = sorted(
        int(d.replace("min_", ""))
        for d in os.listdir(mb_dir)
        if d.startswith("min_")
    )

    c1 = chart_phase4_minbatch(data_dir, chart_dir, gpu_label)
    print(f"  Charts: {c1}")

    p6_settings = _load_phase6_settings(data_dir, env["default_machine"])
    threads_local = p6_settings.get("threads_local_gpu", "?")
    threads_vertex = p6_settings.get("threads_vertex_ai", "?")
    batch_local = p6_settings.get("max_batch_local_gpu", "?")
    batch_vertex = p6_settings.get("max_batch_vertex_ai", "?")

    md = [f"# Phase 4: Min Batch Size ({gpu_label})\n"]
    md.append("[< GPU Summary](gpu_report.md)\n")
    md.append("## Going In\n")
    md.append("`min_batch_size` controls how long RunInference waits to accumulate "
              "elements before calling `run_inference()`. Higher values increase "
              "batch efficiency but add wait time.\n")
    md.append(configuration_table(env, {
        "Harness Threads": {"value": f"Local GPU={threads_local}, Vertex AI={threads_vertex}",
                            "status": "Optimized (Phase 2)"},
        "max_batch_size": {"value": f"Local GPU={batch_local}, Vertex AI={batch_vertex}",
                           "status": "Optimized (Phase 3)"},
        "min_batch_size": {"value": f"**{', '.join(str(m) for m in min_sizes)}**",
                           "status": "**Swept**"},
    }))

    md.append("## Results\n")
    for mode, label in [("local_gpu", "Local GPU"), ("vertex_ai", "Vertex AI")]:
        md.append(f"\n**{label}**\n")
        md.append("| min_batch | Rate | Throughput | p50 | p95 | p99 |\n")
        md.append("|---:|---:|---:|---:|---:|---:|\n")
        for ms in min_sizes:
            path = os.path.join(mb_dir, f"min_{ms}", "benchmark_results.json")
            if not os.path.exists(path):
                continue
            d = load_json(path)
            if mode not in d:
                continue
            for rate_s in sorted(d[mode].keys(), key=int):
                s = d[mode][rate_s]
                md.append(f"| {ms} | {rate_s} | {fmt_tp(s['throughput'])} | "
                          f"{fmt_ms(s['latency_p50'])} ms | "
                          f"{fmt_ms(s['latency_p95'])} ms | "
                          f"{fmt_ms(s['latency_p99'])} ms |\n")

    if c1:
        md.append(f"\n![Min Batch Sweep](charts/{c1})\n")

    md.append("\n## Conclusion\n")
    md.append("The `min_batch_size` tradeoff: higher values force batches to fill, "
              "which improves GPU utilization but adds queue wait time. "
              "The optimal value depends on the incoming message rate.\n")

    out = os.path.join(report_dir, "phase4_minbatch.md")
    with open(out, "w") as f:
        f.write("".join(md))
    print(f"  Report: {out}")


# ---------------------------------------------------------------------------
# Phase 5: Machine Sweep
# ---------------------------------------------------------------------------

def chart_phase5_machines(data_dir, chart_dir, gpu_label):
    """Grouped bars: throughput + p99 per machine type."""
    machine_dir = os.path.join(data_dir, "phase5_machine")
    endpoint_dir = os.path.join(data_dir, "phase5_endpoint")

    if not os.path.isdir(machine_dir):
        return None

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    # Local GPU machines
    machine_analysis = os.path.join(machine_dir, "analysis.json")
    endpoint_analysis = os.path.join(endpoint_dir, "analysis.json")

    if os.path.exists(machine_analysis):
        ma = load_json(machine_analysis)
        labels, tps, p99s = [], [], []
        for mode in ["local_gpu", "vertex_ai"]:
            if mode not in ma:
                continue
            m = ma[mode]
            mtype = m.get("best_machine_type", "unknown")
            labels.append(f"{machine_short(mtype)}\n({mode.replace('_', ' ').title()})")
            tps.append(m.get("throughput", 0))
            p99s.append(m.get("latency_p99", 0))

        if labels:
            x = np.arange(len(labels))
            colors = [LOCAL_COLOR if "local" in l.lower() else VERTEX_COLOR for l in labels]
            bars = ax1.bar(x, tps, 0.5, color=colors, zorder=3)
            for bar, tp in zip(bars, tps):
                ax1.text(bar.get_x() + bar.get_width() / 2, tp + 2,
                         f"{tp:.0f}", ha="center", fontweight="bold", fontsize=10)
            ax1.set_xticks(x)
            ax1.set_xticklabels(labels, fontsize=9)
            ax1.set_ylabel("Throughput (msg/s)")
            ax1.set_title("Per-Worker Capacity by Machine")
            ax1.set_ylim(0, max(tps) * 1.25)

            bars2 = ax2.bar(x, p99s, 0.5, color=colors, zorder=3)
            for bar, p99 in zip(bars2, p99s):
                ax2.text(bar.get_x() + bar.get_width() / 2, p99 + 5,
                         f"{p99:.0f}", ha="center", fontweight="bold", fontsize=10)
            ax2.set_xticks(x)
            ax2.set_xticklabels(labels, fontsize=9)
            ax2.set_ylabel("Latency p99 (ms)")
            ax2.set_title("Tail Latency by Machine")
            ax2.set_ylim(0, max(p99s) * 1.25)

    fig.suptitle(f"Phase 5: Machine Type Comparison ({gpu_label})",
                 fontsize=15, fontweight="bold", y=1.02)
    fig.tight_layout()
    fname = "phase5_machines.png"
    fig.savefig(os.path.join(chart_dir, fname), dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fname


def report_phase5(data_dir, report_dir):
    gpu_label = detect_gpu_label(data_dir)
    env = load_env_config(data_dir)
    chart_dir = os.path.join(report_dir, "charts")
    ensure_dir(chart_dir)

    c1 = chart_phase5_machines(data_dir, chart_dir, gpu_label)
    print(f"  Charts: {c1}")

    # Detect tested machines
    machines_tested = detect_machine_types(data_dir)
    p6_settings = _load_phase6_settings(data_dir, env["default_machine"])
    threads_local = p6_settings.get("threads_local_gpu", "?")
    threads_vertex = p6_settings.get("threads_vertex_ai", "?")
    batch_local = p6_settings.get("max_batch_local_gpu", "?")
    batch_vertex = p6_settings.get("max_batch_vertex_ai", "?")
    min_local = p6_settings.get("min_batch_local_gpu", "?")
    min_vertex = p6_settings.get("min_batch_vertex_ai", "?")

    machine_list = ", ".join(machines_tested) if machines_tested else "varies"

    md = [f"# Phase 5: Machine Type Sweep ({gpu_label})\n"]
    md.append("[< GPU Summary](gpu_report.md)\n")
    md.append("## Going In\n")
    md.append("Do bigger worker machines (more vCPUs, more RAM) improve per-worker "
              "capacity? We compare the default machine to a larger variant.\n")
    md.append(configuration_table(env, {
        "Harness Threads": {"value": f"Local GPU={threads_local}, Vertex AI={threads_vertex}",
                            "status": "Optimized (Phase 2)"},
        "max_batch_size": {"value": f"Local GPU={batch_local}, Vertex AI={batch_vertex}",
                           "status": "Optimized (Phase 3)"},
        "min_batch_size": {"value": f"Local GPU={min_local}, Vertex AI={min_vertex}",
                           "status": "Optimized (Phase 4)"},
        "Local GPU Infrastructure": {
            "value": f"**{machine_list}** (swept)",
            "status": "**Swept**"},
        "Vertex AI Infrastructure": {
            "value": f"**{machine_list}** (swept)",
            "status": "**Swept**"},
    }))

    # Load analysis files
    for subdir, heading in [
        ("phase5_machine", "Worker Machine Analysis (Local GPU)"),
        ("phase5_endpoint", "Endpoint Machine Analysis (Vertex AI)"),
    ]:
        analysis_path = os.path.join(data_dir, subdir, "analysis.json")
        if not os.path.exists(analysis_path):
            continue
        a = load_json(analysis_path)
        md.append(f"\n## {heading}\n")
        md.append("| Experiment | Best Machine | Capacity | p50 | p99 |\n")
        md.append("|---|---|---:|---:|---:|\n")
        for mode, label in [("local_gpu", "Local GPU"), ("vertex_ai", "Vertex AI")]:
            if mode not in a:
                continue
            s = a[mode]
            md.append(f"| {label} | {s.get('best_machine_type', '?')} | "
                      f"{s.get('per_worker_capacity', s.get('best_rate', '?'))} msg/s | "
                      f"{fmt_ms(s.get('latency_p50'))} ms | "
                      f"{fmt_ms(s.get('latency_p99'))} ms |\n")

    # Phase 5b endpoint followup
    p5b_dir = os.path.join(data_dir, "phase5b_endpoint_followup")
    if os.path.isdir(p5b_dir):
        md.append("\n## Phase 5b: Endpoint Follow-Up\n")
        for entry in sorted(os.listdir(p5b_dir)):
            br_path = os.path.join(p5b_dir, entry, "benchmark_results.json")
            if not os.path.exists(br_path):
                continue
            d = load_json(br_path)
            md.append(f"\n**Endpoint machine: {entry}**\n")
            md.append("| Rate | Throughput | p50 | p99 |\n")
            md.append("|---:|---:|---:|---:|\n")
            for mode in ["vertex_ai", "local_gpu"]:
                if mode not in d:
                    continue
                for rate_s in sorted(d[mode].keys(), key=int):
                    s = d[mode][rate_s]
                    md.append(f"| {rate_s} | {fmt_tp(s['throughput'])} | "
                              f"{fmt_ms(s['latency_p50'])} ms | "
                              f"{fmt_ms(s['latency_p99'])} ms |\n")

    if c1:
        md.append(f"\n![Machine Comparison](charts/{c1})\n")

    md.append("\n## Conclusion\n")
    md.append("Machine type affects capacity differently for each approach. "
              "Larger machines provide more CPU headroom for tokenization and "
              "pipeline overhead, but GPU inference speed is hardware-bound.\n")

    out = os.path.join(report_dir, "phase5_machines.md")
    with open(out, "w") as f:
        f.write("".join(md))
    print(f"  Report: {out}")


# ---------------------------------------------------------------------------
# Phase 6: Re-Tune
# ---------------------------------------------------------------------------

def chart_phase6_capacity(data_dir, chart_dir, gpu_label):
    """Capacity curves from phase6_retune: p99 latency vs rate, threshold line."""
    retune_dir = os.path.join(data_dir, "phase6_retune")
    if not os.path.isdir(retune_dir):
        return None

    machines = sorted(d for d in os.listdir(retune_dir)
                      if os.path.isdir(os.path.join(retune_dir, d)))
    if not machines:
        return None

    n_machines = len(machines)
    fig, axes = plt.subplots(1, n_machines, figsize=(7 * n_machines, 5.5),
                             squeeze=False)

    for idx, mach in enumerate(machines):
        ax = axes[0, idx]
        cap_dir = os.path.join(retune_dir, mach, "capacity")
        if not os.path.isdir(cap_dir):
            ax.set_visible(False)
            continue

        rate_dirs = sorted(
            (int(d.replace("rate_", "")), d)
            for d in os.listdir(cap_dir)
            if d.startswith("rate_")
        )

        for mode, color, label in [
            ("local_gpu", LOCAL_COLOR, "Local GPU"),
            ("vertex_ai", VERTEX_COLOR, "Vertex AI"),
        ]:
            rates_plot, p99s = [], []
            for rate_val, rate_name in rate_dirs:
                br = os.path.join(cap_dir, rate_name, "benchmark_results.json")
                if not os.path.exists(br):
                    continue
                d = load_json(br)
                if mode not in d:
                    continue
                rate_key = str(rate_val)
                if rate_key not in d[mode]:
                    # Try first available key
                    rate_key = next(iter(d[mode]), None)
                    if rate_key is None:
                        continue
                rates_plot.append(rate_val)
                p99s.append(d[mode][rate_key]["latency_p99"])

            if rates_plot:
                ax.plot(rates_plot, p99s, "o-", color=color, linewidth=2.5,
                        markersize=7, label=label)

        ax.axhline(y=750, color="gray", linestyle="--", alpha=0.5,
                   label="p99 < 750ms threshold")
        ax.set_xlabel("Publish Rate (msg/s)")
        ax.set_ylabel("Latency p99 (ms)")
        ax.set_title(f"Capacity: {mach}")
        ax.legend(fontsize=9)

    fig.suptitle(f"Phase 6: Re-Tuned Capacity Curves ({gpu_label})",
                 fontsize=15, fontweight="bold", y=1.02)
    fig.tight_layout()
    fname = "phase6_capacity.png"
    fig.savefig(os.path.join(chart_dir, fname), dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fname


def chart_phase6_settings(data_dir, chart_dir, gpu_label):
    """Settings comparison: optimal settings per machine."""
    retune_dir = os.path.join(data_dir, "phase6_retune")
    if not os.path.isdir(retune_dir):
        return None

    machines = sorted(d for d in os.listdir(retune_dir)
                      if os.path.isdir(os.path.join(retune_dir, d)))
    if not machines:
        return None

    # Collect settings
    rows = []
    for mach in machines:
        ap = os.path.join(retune_dir, mach, "analysis.json")
        if not os.path.exists(ap):
            continue
        a = load_json(ap)
        bs = a.get("best_settings", {})
        rows.append((mach, bs))

    if not rows:
        return None

    settings_keys = [
        ("threads_local_gpu", "Threads\n(Local GPU)"),
        ("threads_vertex_ai", "Threads\n(Vertex AI)"),
        ("max_batch_local_gpu", "max_batch\n(Local GPU)"),
        ("max_batch_vertex_ai", "max_batch\n(Vertex AI)"),
        ("local_capacity", "Capacity\n(Local GPU)"),
        ("vertex_capacity", "Capacity\n(Vertex AI)"),
    ]

    fig, ax = plt.subplots(figsize=(max(8, len(rows) * 4), 5))
    x = np.arange(len(settings_keys))
    width = 0.8 / len(rows)

    for i, (mach, bs) in enumerate(rows):
        vals = [bs.get(k, 0) for k, _ in settings_keys]
        offset = (i - len(rows) / 2 + 0.5) * width
        bars = ax.bar(x + offset, vals, width, label=mach, zorder=3)
        for bar, v in zip(bars, vals):
            if v > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                        str(v), ha="center", fontsize=9, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels([lbl for _, lbl in settings_keys], fontsize=9)
    ax.set_ylabel("Value")
    ax.set_title(f"Phase 6: Optimal Settings per Machine ({gpu_label})")
    ax.legend()
    fig.tight_layout()
    fname = "phase6_settings.png"
    fig.savefig(os.path.join(chart_dir, fname), dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fname


def report_phase6(data_dir, report_dir):
    gpu_label = detect_gpu_label(data_dir)
    env = load_env_config(data_dir)
    retune_dir = os.path.join(data_dir, "phase6_retune")
    if not os.path.isdir(retune_dir):
        print(f"  SKIP Phase 6: {retune_dir} not found")
        return
    chart_dir = os.path.join(report_dir, "charts")
    ensure_dir(chart_dir)

    c1 = chart_phase6_capacity(data_dir, chart_dir, gpu_label)
    c2 = chart_phase6_settings(data_dir, chart_dir, gpu_label)
    print(f"  Charts: {c1}, {c2}")

    machines = sorted(d for d in os.listdir(retune_dir)
                      if os.path.isdir(os.path.join(retune_dir, d)))

    md = [f"# Phase 6: Re-Tune for Each Machine ({gpu_label})\n"]
    md.append("[< GPU Summary](gpu_report.md)\n")
    md.append("## Going In\n")
    md.append("Each machine type may have different optimal settings for threads, "
              "batch size, and min_batch_size. Phase 6 repeats the thread/batch "
              "sweeps for each machine and finds the optimal configuration.\n")
    md.append(configuration_table(env, {
        "Local GPU Infrastructure": {
            "value": ", ".join(machines),
            "status": "From Phase 5"},
        "Vertex AI Infrastructure": {
            "value": ", ".join(machines),
            "status": "From Phase 5"},
        "Harness Threads": {"value": "**re-swept per machine**",
                            "status": "**Swept**"},
        "max_batch_size": {"value": "**re-swept per machine**",
                           "status": "**Swept**"},
        "min_batch_size": {"value": "**re-swept per machine**",
                           "status": "**Swept**"},
        "Publish Rates": {"value": "fine-grained capacity sweep",
                          "status": "**Swept**"},
    }))

    for mach in machines:
        ap = os.path.join(retune_dir, mach, "analysis.json")
        if not os.path.exists(ap):
            continue
        a = load_json(ap)
        bs = a.get("best_settings", {})

        md.append(f"\n## Machine: {a.get('machine_type', mach)}\n")
        md.append("### Optimal Settings\n")
        md.append("| Setting | Local GPU | Vertex AI |\n")
        md.append("|---|---|---|\n")
        md.append(f"| Threads | {bs.get('threads_local_gpu', '-')} | "
                  f"{bs.get('threads_vertex_ai', '-')} |\n")
        md.append(f"| max_batch_size | {bs.get('max_batch_local_gpu', '-')} | "
                  f"{bs.get('max_batch_vertex_ai', '-')} |\n")
        md.append(f"| min_batch_size | {bs.get('min_batch_local_gpu', '-')} | "
                  f"{bs.get('min_batch_vertex_ai', '-')} |\n")
        md.append(f"| **Per-Worker Capacity** | **{bs.get('local_capacity', '-')} msg/s** | "
                  f"**{bs.get('vertex_capacity', '-')} msg/s** |\n")

        # Capacity analysis detail
        ca = a.get("capacity_analysis", {})
        if ca:
            md.append("\n### Capacity Verification\n")
            md.append("| Experiment | Rate | Throughput | p50 | p99 |\n")
            md.append("|---|---:|---:|---:|---:|\n")
            for mode, label in [("local_gpu", "Local GPU"), ("vertex_ai", "Vertex AI")]:
                if mode not in ca:
                    continue
                s = ca[mode]
                md.append(f"| {label} | {s.get('best_rate', '-')} | "
                          f"{fmt_tp(s.get('throughput'))} | "
                          f"{fmt_ms(s.get('latency_p50'))} ms | "
                          f"{fmt_ms(s.get('latency_p99'))} ms |\n")

    if c1:
        md.append(f"\n![Capacity Curves](charts/{c1})\n")
    if c2:
        md.append(f"\n![Settings Comparison](charts/{c2})\n")

    md.append("\n## Conclusion\n")
    md.append("Re-tuning for each machine type yields the final per-worker/per-replica "
              "capacity numbers used for scaling calculations in Phase 7.\n")

    out = os.path.join(report_dir, "phase6_retune.md")
    with open(out, "w") as f:
        f.write("".join(md))
    print(f"  Report: {out}")


# ---------------------------------------------------------------------------
# Phase 7: Scaling
# ---------------------------------------------------------------------------

def chart_phase7_local(data, chart_dir, gpu_label):
    """Local GPU: throughput vs worker count per machine type, ideal scaling line."""
    fig, ax = plt.subplots(figsize=(10, 5.5))

    machine_groups = {}
    for key, stats in data.items():
        if not key.startswith("local_gpu"):
            continue
        # Parse: "local_gpu n1s4 (2w)" -> machine=n1s4, workers=2
        m = re.match(r"local_gpu (\S+) \((\d+)w\)", key)
        if not m:
            continue
        mach, nw = m.group(1), int(m.group(2))
        machine_groups.setdefault(mach, []).append((nw, stats))

    colors_cycle = [LOCAL_COLOR, "#0d47a1", "#4285f4", "#8ab4f8"]
    for idx, (mach, entries) in enumerate(sorted(machine_groups.items())):
        entries.sort()
        workers = [e[0] for e in entries]
        tps = [e[1]["throughput"] for e in entries]
        rates = [e[1]["rate"] for e in entries]

        color = colors_cycle[idx % len(colors_cycle)]
        ax.plot(workers, tps, "o-", color=color, linewidth=2.5,
                markersize=8, label=f"{mach} (achieved)")
        ax.plot(workers, rates, "x--", color=color, linewidth=1,
                markersize=6, alpha=0.5, label=f"{mach} (target)")

        for w, tp in zip(workers, tps):
            ax.text(w, tp + max(tps) * 0.03, f"{tp:.0f}", ha="center",
                    fontsize=9, fontweight="bold")

    ax.set_xlabel("Worker Count")
    ax.set_ylabel("Throughput (msg/s)")
    ax.set_title(f"Local GPU: Linear Scaling ({gpu_label})")
    ax.legend(fontsize=9)
    fig.tight_layout()
    fname = "phase7_local_scaling.png"
    fig.savefig(os.path.join(chart_dir, fname), dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fname


def chart_phase7_vertex(data, chart_dir, gpu_label):
    """Vertex AI: heatmap of replicas x workers -> p99 latency."""
    # Collect Vertex AI entries
    entries = []
    for key, stats in data.items():
        if not key.startswith("vertex_ai"):
            continue
        # "vertex_ai n1s4 (r10_w8)" -> machine=n1s4, replicas=10, workers=8
        m = re.match(r"vertex_ai (\S+) \(r(\d+)_w(\d+)\)", key)
        if not m:
            continue
        mach, replicas, workers = m.group(1), int(m.group(2)), int(m.group(3))
        entries.append((mach, replicas, workers, stats))

    if not entries:
        return None

    # Group by machine
    machine_groups = {}
    for mach, rep, wk, stats in entries:
        machine_groups.setdefault(mach, []).append((rep, wk, stats))

    n_machines = len(machine_groups)
    fig, axes = plt.subplots(1, n_machines, figsize=(7 * n_machines, 5.5),
                             squeeze=False)

    for idx, (mach, group) in enumerate(sorted(machine_groups.items())):
        ax = axes[0, idx]
        replicas_set = sorted(set(r for r, _, _ in group))
        workers_set = sorted(set(w for _, w, _ in group))

        # Build heatmap data
        hmap = np.full((len(replicas_set), len(workers_set)), np.nan)
        for r, w, stats in group:
            ri = replicas_set.index(r)
            wi = workers_set.index(w)
            hmap[ri, wi] = stats.get("latency_p99", np.nan)

        im = ax.imshow(hmap, cmap="RdYlGn_r", aspect="auto",
                       vmin=0, vmax=3000)
        ax.set_xticks(range(len(workers_set)))
        ax.set_xticklabels(workers_set)
        ax.set_yticks(range(len(replicas_set)))
        ax.set_yticklabels(replicas_set)
        ax.set_xlabel("Workers")
        ax.set_ylabel("Replicas (rate multiplier)")
        ax.set_title(f"Vertex AI {mach}: p99 Latency (ms)")

        # Annotate cells
        for ri in range(len(replicas_set)):
            for wi in range(len(workers_set)):
                v = hmap[ri, wi]
                if np.isnan(v):
                    continue
                txt = f"{v:.0f}" if v < 10000 else f"{v / 1000:.0f}s"
                color = "white" if v > 1500 else "black"
                fontw = "bold" if v < 750 else "normal"
                ax.text(wi, ri, txt, ha="center", va="center",
                        fontsize=8, color=color, fontweight=fontw)

        fig.colorbar(im, ax=ax, shrink=0.8, label="p99 (ms)")

    fig.suptitle(f"Phase 7: Vertex AI Scaling Grid ({gpu_label})",
                 fontsize=15, fontweight="bold", y=1.02)
    fig.tight_layout()
    fname = "phase7_vertex_heatmap.png"
    fig.savefig(os.path.join(chart_dir, fname), dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fname


def report_phase7(data_dir, report_dir):
    gpu_label = detect_gpu_label(data_dir)
    env = load_env_config(data_dir)
    sweep_path = os.path.join(data_dir, "phase7_scale", "sweep_summary.json")
    if not os.path.exists(sweep_path):
        print(f"  SKIP Phase 7: {sweep_path} not found")
        return
    data = load_json(sweep_path)
    chart_dir = os.path.join(report_dir, "charts")
    ensure_dir(chart_dir)

    c1 = chart_phase7_local(data, chart_dir, gpu_label)
    c2 = chart_phase7_vertex(data, chart_dir, gpu_label)
    print(f"  Charts: {c1}, {c2}")

    # Detect scaling ranges from data
    local_workers = set()
    vertex_replicas = set()
    for key in data:
        m = re.match(r"local_gpu \S+ \((\d+)w\)", key)
        if m:
            local_workers.add(int(m.group(1)))
        m = re.match(r"vertex_ai \S+ \(r(\d+)_w\d+\)", key)
        if m:
            vertex_replicas.add(int(m.group(1)))

    # Collect machine types from data keys
    machine_types_seen = set()
    for key in data:
        m = re.match(r"(?:local_gpu|vertex_ai) (\S+)", key)
        if m:
            machine_types_seen.add(m.group(1))
    machines_str = ", ".join(sorted(machine_types_seen)) if machine_types_seen else "varies"

    md = [f"# Phase 7: Scaling Verification ({gpu_label})\n"]
    md.append("[< GPU Summary](gpu_report.md)\n")
    md.append("## Going In\n")
    md.append("With optimized per-worker settings from Phase 6, we verify scaling: "
              "does adding workers deliver proportional throughput? For Vertex AI, "
              "we also sweep endpoint replicas.\n")
    md.append(configuration_table(env, {
        "Local GPU Infrastructure": {"value": machines_str,
                                     "status": "From Phase 5"},
        "Vertex AI Infrastructure": {"value": machines_str,
                                      "status": "From Phase 5"},
        "Harness Threads": {"value": "per-machine optimal",
                            "status": "Optimized (Phase 6)"},
        "max_batch_size": {"value": "per-machine optimal",
                           "status": "Optimized (Phase 6)"},
        "min_batch_size": {"value": "per-machine optimal",
                           "status": "Optimized (Phase 6)"},
        "Workers": {"value": f"**{', '.join(str(w) for w in sorted(local_workers))}**",
                    "status": "**Swept**"},
        "Endpoint Replicas": {
            "value": f"**{', '.join(str(r) for r in sorted(vertex_replicas))}**",
            "status": "**Swept**"},
    }))

    # Local GPU table
    local_entries = [(k, v) for k, v in data.items() if k.startswith("local_gpu")]
    if local_entries:
        md.append("\n## Local GPU Scaling\n")
        md.append("| Config | Rate | Workers | Throughput | p50 | p99 |\n")
        md.append("|---|---:|---:|---:|---:|---:|\n")
        for key, stats in sorted(local_entries):
            m = re.match(r"local_gpu (\S+) \((\d+)w\)", key)
            if not m:
                continue
            mach, nw = m.group(1), m.group(2)
            md.append(f"| {mach} | {stats['rate']} | {nw} | "
                      f"{fmt_tp(stats['throughput'])} | "
                      f"{fmt_ms(stats['latency_p50'])} ms | "
                      f"{fmt_ms(stats['latency_p99'])} ms |\n")

    # Vertex AI table
    vertex_entries = [(k, v) for k, v in data.items() if k.startswith("vertex_ai")]
    if vertex_entries:
        md.append("\n## Vertex AI Scaling\n")
        md.append("| Config | Rate | Replicas | Workers | Throughput | p50 | p99 |\n")
        md.append("|---|---:|---:|---:|---:|---:|---:|\n")
        for key, stats in sorted(vertex_entries):
            m_v = re.match(r"vertex_ai (\S+) \(r(\d+)_w(\d+)\)", key)
            if not m_v:
                continue
            mach, rep, wk = m_v.group(1), m_v.group(2), m_v.group(3)
            md.append(f"| {mach} | {stats['rate']} | {rep} | {wk} | "
                      f"{fmt_tp(stats['throughput'])} | "
                      f"{fmt_ms(stats['latency_p50'])} ms | "
                      f"{fmt_ms(stats['latency_p99'])} ms |\n")

    if c1:
        md.append(f"\n![Local GPU Scaling](charts/{c1})\n")
    if c2:
        md.append(f"\n![Vertex AI Heatmap](charts/{c2})\n")

    md.append("\n## Conclusion\n")
    md.append("Local GPU scales linearly: each additional worker adds approximately "
              "the per-worker capacity measured in Phase 6.\n\n")
    md.append("Vertex AI scaling depends on the ratio of workers to replicas. "
              "Too many workers per replica causes endpoint contention; "
              "too few wastes capacity.\n")

    out = os.path.join(report_dir, "phase7_scaling.md")
    with open(out, "w") as f:
        f.write("".join(md))
    print(f"  Report: {out}")


# ---------------------------------------------------------------------------
# Phase 8: Cost Analysis
# ---------------------------------------------------------------------------

def chart_phase8_cost(cost_data, chart_dir, gpu_label):
    """Horizontal bars: $/hr for top qualifying configs, sorted by cost."""
    configs = cost_data.get("qualifying_configs", [])
    if not configs:
        return None

    # Take top 10 by cost
    top = sorted(configs, key=lambda c: c["cost_per_hour"])[:10]

    fig, ax = plt.subplots(figsize=(10, max(4, len(top) * 0.5 + 1)))

    labels = []
    costs = []
    colors = []
    for c in reversed(top):
        exp = c["experiment"]
        if exp == "local_gpu":
            mach = c.get("machine_short", "?")
            lbl = f"Local GPU {mach}\n{c['workers_needed']}w"
            colors.append(LOCAL_COLOR)
        else:
            ep_mach = c.get("endpoint_machine_short", "?")
            replicas = c.get("replicas", "?")
            lbl = f"Vertex AI {ep_mach}\n{c['workers_needed']}w + {replicas}r"
            colors.append(VERTEX_COLOR)
        labels.append(lbl)
        costs.append(c["cost_per_hour"])

    y = np.arange(len(labels))
    bars = ax.barh(y, costs, color=colors, zorder=3, height=0.6)
    for bar, cost in zip(bars, costs):
        ax.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height() / 2,
                f"${cost:.2f}/hr", va="center", fontweight="bold", fontsize=10)

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel("Cost ($/hr)")
    ax.set_title(f"Phase 8: Cost to Sustain {cost_data.get('target_rate', 1000)} msg/s ({gpu_label})")
    ax.set_xlim(0, max(costs) * 1.3)
    fig.tight_layout()
    fname = "phase8_cost_ranking.png"
    fig.savefig(os.path.join(chart_dir, fname), dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fname


def chart_phase8_breakdown(cost_data, chart_dir, gpu_label):
    """Stacked bars: worker cost vs endpoint cost for top configs."""
    configs = cost_data.get("qualifying_configs", [])
    pricing = cost_data.get("pricing", {})
    if not configs:
        return None

    top = sorted(configs, key=lambda c: c["cost_per_hour"])[:8]

    fig, ax = plt.subplots(figsize=(12, 5.5))

    labels = []
    worker_costs = []
    endpoint_costs = []

    gpu_inclusive = pricing.get("gpu_inclusive_families", ["g2", "a2", "a3"])

    for c in top:
        exp = c["experiment"]
        workers_needed = c.get("workers_needed", 0)

        if exp == "local_gpu":
            mach = c.get("worker_machine", "")
            mach_short = c.get("machine_short", "?")
            lbl = f"Local GPU\n{mach_short} x{workers_needed}"

            # Worker cost = machine + GPU (if not inclusive)
            ce_prices = pricing.get("compute_engine", {}).get("machines", {})
            gpu_prices = pricing.get("compute_engine", {}).get("gpu_accelerators", {})
            mach_price = ce_prices.get(mach, 0)
            family = mach.split("-")[0]
            gpu_price = 0 if family in gpu_inclusive else gpu_prices.get(
                cost_data.get("gpu_type", ""), 0)
            w_cost = workers_needed * (mach_price + gpu_price)
            e_cost = 0
        else:
            ep_mach = c.get("endpoint_machine", "")
            ep_short = c.get("endpoint_machine_short", "?")
            replicas = c.get("replicas", 0)
            lbl = f"Vertex AI\n{ep_short} {workers_needed}w+{replicas}r"

            # Worker cost
            vertex_wm = c.get("vertex_worker_machine", "n1-standard-4")
            ce_prices = pricing.get("compute_engine", {}).get("machines", {})
            w_cost = workers_needed * ce_prices.get(vertex_wm, 0.19)

            # Endpoint cost
            vp_prices = pricing.get("vertex_ai_prediction", {}).get("machines", {})
            vp_gpus = pricing.get("vertex_ai_prediction", {}).get("gpu_accelerators", {})
            ep_price = vp_prices.get(ep_mach, 0)
            family = ep_mach.split("-")[0]
            gpu_price = 0 if family in gpu_inclusive else vp_gpus.get(
                cost_data.get("gpu_type", ""), 0)
            e_cost = replicas * (ep_price + gpu_price)

        labels.append(lbl)
        worker_costs.append(w_cost)
        endpoint_costs.append(e_cost)

    x = np.arange(len(labels))
    ax.bar(x, worker_costs, 0.5, label="Worker Cost", color=LOCAL_COLOR, zorder=3)
    ax.bar(x, endpoint_costs, 0.5, bottom=worker_costs,
           label="Endpoint Cost", color=VERTEX_COLOR, zorder=3)

    for i, (wc, ec) in enumerate(zip(worker_costs, endpoint_costs)):
        total = wc + ec
        ax.text(i, total + 0.3, f"${total:.2f}", ha="center",
                fontweight="bold", fontsize=10)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("Cost ($/hr)")
    ax.set_title(f"Phase 8: Cost Breakdown ({gpu_label})")
    ax.legend()
    fig.tight_layout()
    fname = "phase8_cost_breakdown.png"
    fig.savefig(os.path.join(chart_dir, fname), dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fname


def report_phase8(data_dir, report_dir):
    gpu_label = detect_gpu_label(data_dir)
    env = load_env_config(data_dir)
    cost_path = os.path.join(data_dir, "cost_analysis.json")
    if not os.path.exists(cost_path):
        print(f"  SKIP Phase 8: {cost_path} not found")
        return
    cost_data = load_json(cost_path)
    chart_dir = os.path.join(report_dir, "charts")
    ensure_dir(chart_dir)

    c1 = chart_phase8_cost(cost_data, chart_dir, gpu_label)
    c2 = chart_phase8_breakdown(cost_data, chart_dir, gpu_label)
    print(f"  Charts: {c1}, {c2}")

    target = cost_data.get("target_rate", 1000)
    target_p99 = cost_data.get("target_p99_ms", 750)
    configs = cost_data.get("qualifying_configs", [])

    md = [f"# Phase 8: Cost Analysis ({gpu_label})\n"]
    md.append("[< GPU Summary](gpu_report.md)\n")
    md.append("## Going In\n")
    md.append(f"Target: sustain **{target} msg/s** with **p99 < {target_p99}ms**. "
              f"Which configuration is cheapest?\n")
    md.append(configuration_table(env, {
        "Harness Threads": {"value": "per-machine optimal",
                            "status": "Optimized (Phase 6)"},
        "max_batch_size": {"value": "per-machine optimal",
                           "status": "Optimized (Phase 6)"},
        "min_batch_size": {"value": "per-machine optimal",
                           "status": "Optimized (Phase 6)"},
        "Workers": {"value": "projected from capacity",
                    "status": "Projected"},
        "Endpoint Replicas": {"value": "projected from capacity",
                              "status": "Projected"},
        "Publish Rates": {"value": f"{target} msg/s target",
                          "status": "Target"},
    }))
    md.append("## Assumptions\n")
    md.append("- **Projected scaling**: per-worker capacity (tested in Phase 6) "
              "is extrapolated to calculate the total workers/replicas needed. "
              "Phase 7 verified linear scaling up to the tested worker counts.\n")
    md.append("- CPU-only Vertex AI workers (GPU is on the endpoint)\n")
    md.append("- On-demand pricing, us-central1\n")

    # Group configs that project to identical deployments so multiple
    # Phase 7 test points appear as validation rather than duplicates.
    grouped = {}  # key -> {info dict, validated_by: [descriptions]}
    for c in sorted(configs, key=lambda x: x["cost_per_hour"]):
        if c["experiment"] == "local_gpu":
            key = (c["experiment"], c.get("machine_short", "?"),
                   c.get("workers_needed", 0), None,
                   round(c["cost_per_hour"], 2))
            tested_w = c.get("workers", 0)
            validation = f"{tested_w}w"
        else:
            key = (c["experiment"],
                   c.get("endpoint_machine_short", "?"),
                   c.get("workers_needed", 0),
                   c.get("replicas", 0),
                   round(c["cost_per_hour"], 2))
            tested_r = c.get("tested_replicas", 0)
            tested_w = c.get("tested_workers", 0)
            validation = f"{tested_r}r/{tested_w}w"
        if key not in grouped:
            grouped[key] = {"config": c, "validated_by": []}
        grouped[key]["validated_by"].append(validation)

    md.append("\n## Qualifying Configurations (sorted by cost)\n")
    md.append("| Rank | Experiment | Config | Workers | Replicas | "
              "Basis | $/hr | $/M msgs | Breakdown |\n")
    md.append("|---:|---|---|---:|---:|---|---:|---:|---|\n")
    for i, (key, grp) in enumerate(
            sorted(grouped.items(), key=lambda x: x[0][4])[:15], 1):
        c = grp["config"]
        exp = c["experiment"].replace("_", " ").title()
        if c["experiment"] == "local_gpu":
            config = c.get("machine_short", "?")
            needed_w = c.get("workers_needed", 0)
            tested_max = max(int(v.rstrip("w")) for v in grp["validated_by"])
            if needed_w <= tested_max:
                basis = "Tested"
            else:
                pts = ", ".join(grp["validated_by"])
                basis = f"Projected (validated at {pts})"
        else:
            config = f"{c.get('endpoint_machine_short', '?')} endpoint"
            needed_w = c.get("workers_needed", 0)
            total_r = c.get("replicas", 0)
            # Check if any test point fully covers the projection
            tested = False
            for v in grp["validated_by"]:
                parts = v.split("/")
                tr = int(parts[0].rstrip("r"))
                tw = int(parts[1].rstrip("w"))
                if needed_w <= tw and total_r <= tr:
                    tested = True
                    break
            if tested:
                basis = "Tested"
            else:
                pts = ", ".join(grp["validated_by"])
                basis = f"Projected (validated at {pts})"
        md.append(f"| {i} | {exp} | {config} | "
                  f"{c.get('workers_needed', '-')} | "
                  f"{c.get('replicas', '-') or '-'} | "
                  f"{basis} | "
                  f"${c['cost_per_hour']:.2f} | "
                  f"${c.get('cost_per_million_msgs', 0):.2f} | "
                  f"{c.get('breakdown', '-')} |\n")

    if c1:
        md.append(f"\n![Cost Ranking](charts/{c1})\n")
    if c2:
        md.append(f"\n![Cost Breakdown](charts/{c2})\n")

    md.append("\n## Conclusion\n")
    if configs:
        best = min(configs, key=lambda x: x["cost_per_hour"])
        md.append(f"**Cheapest option: {best['experiment'].replace('_', ' ').title()} "
                  f"at ${best['cost_per_hour']:.2f}/hr** "
                  f"(${best.get('cost_per_million_msgs', 0):.2f} per million messages).\n\n")
        md.append(f"Configuration: {best.get('breakdown', 'N/A')}\n")

    out = os.path.join(report_dir, "phase8_cost.md")
    with open(out, "w") as f:
        f.write("".join(md))
    print(f"  Report: {out}")


# ---------------------------------------------------------------------------
# GPU Summary
# ---------------------------------------------------------------------------

def report_gpu_summary(data_dir, report_dir):
    gpu_label = detect_gpu_label(data_dir)
    ensure_dir(report_dir)

    md = [f"# {gpu_label} GPU Benchmark Report\n"]
    # Compute relative path from report_dir up to benchmark/reports/
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    overall_path = os.path.join(base, "reports", "benchmark_report.md")
    rel_overall = os.path.relpath(overall_path, report_dir)
    md.append(f"[< Overall Report]({rel_overall})\n")

    # Phase summary table
    md.append("## Phase Summary\n")
    md.append("| Phase | Focus | Key Finding |\n")
    md.append("|---|---|---|\n")

    phase_links = [
        ("1", "Baseline Capacity", "phase1_baseline.md"),
        ("2", "Thread Tuning", "phase2_threads.md"),
        ("3", "Batch Size", "phase3_batch.md"),
        ("4", "Min Batch Size", "phase4_minbatch.md"),
        ("5", "Machine Sweep", "phase5_machines.md"),
        ("6", "Re-Tune", "phase6_retune.md"),
        ("7", "Scaling", "phase7_scaling.md"),
        ("8", "Cost Analysis", "phase8_cost.md"),
    ]

    # Extract key findings from analysis files for each phase
    phase_findings = {}

    # Phase 1: saturation points from benchmark_results.json
    p1_path = os.path.join(data_dir, "phase1_capacity", "benchmark_results.json")
    if os.path.exists(p1_path):
        p1 = load_json(p1_path)
        p1_parts = []
        for mode, label in [("local_gpu", "Local"), ("vertex_ai", "Vertex")]:
            rates_data = p1.get(mode, {})
            prev_rate = None
            for rate_str in sorted(rates_data, key=lambda x: int(x)):
                m = rates_data[rate_str]
                if not isinstance(m, dict):
                    prev_rate = rate_str
                    continue
                p50 = m.get("latency_p50", 0)
                if p50 > 1000:
                    lo = prev_rate or "?"
                    p1_parts.append(f"{label} saturates {lo}--{rate_str} msg/s")
                    break
                prev_rate = rate_str
        if p1_parts:
            phase_findings["1"] = "; ".join(p1_parts)

    # Phase 2: best threads
    p2_path = os.path.join(data_dir, "phase2_threads", "analysis.json")
    if os.path.exists(p2_path):
        p2 = load_json(p2_path)
        parts = []
        for mode, label in [("local_gpu", "Local"), ("vertex_ai", "Vertex")]:
            if mode in p2:
                parts.append(f"{label}={p2[mode]['best_threads']} threads")
        if parts:
            phase_findings["2"] = "Optimal: " + ", ".join(parts)

    # Phase 3: best max_batch_size
    p3_path = os.path.join(data_dir, "phase3_max_batch", "analysis.json")
    if os.path.exists(p3_path):
        p3 = load_json(p3_path)
        parts = []
        for mode, label in [("local_gpu", "Local"), ("vertex_ai", "Vertex")]:
            if mode in p3:
                parts.append(f"{label}={p3[mode]['best_max_batch_size']}")
        if parts:
            phase_findings["3"] = "Optimal max_batch: " + ", ".join(parts)

    # Phase 4: best min_batch_size
    p4_path = os.path.join(data_dir, "phase4_min_batch", "analysis.json")
    if os.path.exists(p4_path):
        p4 = load_json(p4_path)
        parts = []
        for mode, label in [("local_gpu", "Local"), ("vertex_ai", "Vertex")]:
            if mode in p4:
                parts.append(f"{label}={p4[mode]['best_min_batch_size']}")
        if parts:
            phase_findings["4"] = "Optimal min_batch: " + ", ".join(parts)

    # Phase 5: best machine types
    p5_parts = []
    for sub, context in [("phase5_machine", "worker"),
                         ("phase5_endpoint", "endpoint")]:
        ap = os.path.join(data_dir, sub, "analysis.json")
        if os.path.exists(ap):
            a = load_json(ap)
            for mode, label in [("local_gpu", "Local"), ("vertex_ai", "Vertex")]:
                if mode in a:
                    best = machine_short(a[mode]["best_machine_type"])
                    p5_parts.append(f"{label} {context}={best}")
    if p5_parts:
        phase_findings["5"] = "Best: " + ", ".join(p5_parts)

    # Phase 6: final capacity per machine
    findings = {}
    retune_dir = os.path.join(data_dir, "phase6_retune")
    if os.path.isdir(retune_dir):
        for mach in sorted(os.listdir(retune_dir)):
            ap = os.path.join(retune_dir, mach, "analysis.json")
            if os.path.exists(ap):
                a = load_json(ap)
                bs = a.get("best_settings", {})
                findings[mach] = bs
    if findings:
        parts = []
        for mach, bs in findings.items():
            lc = bs.get("local_capacity", "?")
            vc = bs.get("vertex_capacity", "?")
            parts.append(f"{mach}: Local={lc}, Vertex={vc} msg/s")
        phase_findings["6"] = "; ".join(parts)

    # Phase 7: max tested throughput
    sw_path = os.path.join(data_dir, "phase7_scale", "sweep_summary.json")
    if os.path.exists(sw_path):
        sw = load_json(sw_path)
        local_keys = [k for k in sw if k.startswith("local_gpu")]
        vertex_keys = [k for k in sw if k.startswith("vertex_ai")]
        p7_parts = []
        if local_keys:
            best_k = max(local_keys, key=lambda k: sw[k].get("throughput", 0))
            tp = sw[best_k].get("throughput", 0)
            # Extract config like "4w" from "local_gpu n1s4 (4w)"
            config = best_k.split("(")[-1].rstrip(")") if "(" in best_k else best_k
            p7_parts.append(f"Local max {tp:.0f} msg/s ({config})")
        if vertex_keys:
            best_k = max(vertex_keys, key=lambda k: sw[k].get("throughput", 0))
            tp = sw[best_k].get("throughput", 0)
            config = best_k.split("(")[-1].rstrip(")") if "(" in best_k else best_k
            p7_parts.append(f"Vertex max {tp:.0f} msg/s ({config})")
        if p7_parts:
            phase_findings["7"] = "; ".join(p7_parts)

    # Phase 8: cost analysis
    cost_path = os.path.join(data_dir, "cost_analysis.json")
    best_cost = None
    if os.path.exists(cost_path):
        cd = load_json(cost_path)
        configs = cd.get("qualifying_configs", [])
        if configs:
            best_cost = min(configs, key=lambda x: x["cost_per_hour"])
            phase_findings["8"] = (
                f"Best: {best_cost['experiment'].replace('_', ' ')} "
                f"${best_cost['cost_per_hour']:.2f}/hr")

    for num, focus, fname in phase_links:
        report_path = os.path.join(report_dir, fname)
        link = f"[Phase {num}]({fname})" if os.path.exists(report_path) else f"Phase {num}"
        finding = phase_findings.get(num, "")
        md.append(f"| {link} | {focus} | {finding} |\n")

    # Best configuration callout
    if findings:
        md.append("\n## Best Configuration\n")
        for mach, bs in findings.items():
            md.append(f"\n### {mach}\n")
            md.append("| Setting | Local GPU | Vertex AI |\n")
            md.append("|---|---|---|\n")
            md.append(f"| Threads | {bs.get('threads_local_gpu', '-')} | "
                      f"{bs.get('threads_vertex_ai', '-')} |\n")
            md.append(f"| max_batch_size | {bs.get('max_batch_local_gpu', '-')} | "
                      f"{bs.get('max_batch_vertex_ai', '-')} |\n")
            md.append(f"| min_batch_size | {bs.get('min_batch_local_gpu', '-')} | "
                      f"{bs.get('min_batch_vertex_ai', '-')} |\n")
            md.append(f"| **Capacity** | **{bs.get('local_capacity', '-')} msg/s** | "
                      f"**{bs.get('vertex_capacity', '-')} msg/s** |\n")

    if best_cost:
        env = load_env_config(data_dir)
        gt = env.get("gpu_type", "")
        vw_ms = machine_short(env.get("vertex_worker_machine", "n1-standard-4"))
        if best_cost["experiment"] == "local_gpu":
            w = best_cost.get("workers_needed", 0)
            ms = best_cost.get("machine_short", "?")
            infra = fmt_infra_local(w, ms, gt)
        else:
            w = best_cost.get("workers_needed", 0)
            r = best_cost.get("replicas", 0)
            ep_ms = best_cost.get("endpoint_machine_short", "?")
            infra = fmt_infra_vertex(w, vw_ms, r, ep_ms, gt)
        md.append("\n## Cost Summary\n")
        md.append(f"Cheapest config to sustain {cd.get('target_rate', 1000)} msg/s "
                  f"(p99 < {cd.get('target_p99_ms', 750)}ms): "
                  f"**${best_cost['cost_per_hour']:.2f}/hr** "
                  f"(`{infra}`)\n")

    md.append("\n## Phase Reports\n")
    for num, focus, fname in phase_links:
        report_path = os.path.join(report_dir, fname)
        if os.path.exists(report_path):
            md.append(f"- [Phase {num}: {focus}]({fname})\n")
        else:
            md.append(f"- Phase {num}: {focus} *(not yet generated)*\n")

    out = os.path.join(report_dir, "gpu_report.md")
    with open(out, "w") as f:
        f.write("".join(md))
    print(f"  GPU Report: {out}")


# ---------------------------------------------------------------------------
# Overall Report (cross-GPU)
# ---------------------------------------------------------------------------

def chart_overall_capacity(t4_dir, l4_dir, chart_dir):
    """T4 vs L4 per-worker capacity comparison — grouped bar chart."""
    fig, ax = plt.subplots(figsize=(12, 6))

    groups = []  # (group_label, local_cap, vertex_cap, local_infra, vertex_infra)
    for data_dir, gpu_lbl in [(t4_dir, "T4"), (l4_dir, "L4")]:
        env = load_env_config(data_dir)
        retune = os.path.join(data_dir, "phase6_retune")
        if not os.path.isdir(retune):
            continue
        gt = env.get("gpu_type")
        vw = machine_short("n1-standard-4")
        for mach in sorted(os.listdir(retune)):
            ap = os.path.join(retune, mach, "analysis.json")
            if not os.path.exists(ap):
                continue
            a = load_json(ap)
            bs = a.get("best_settings", {})
            local_infra = fmt_infra(1, "dataflow", mach, gt)
            vertex_infra = fmt_infra_vertex(1, vw, 1, mach, gt)
            groups.append((
                f"{gpu_lbl} {mach}",
                bs.get("local_capacity", 0),
                bs.get("vertex_capacity", 0),
                local_infra,
                vertex_infra,
            ))

    if not groups:
        return None

    x = np.arange(len(groups))
    width = 0.35
    local_caps = [g[1] for g in groups]
    vertex_caps = [g[2] for g in groups]

    bars_l = ax.bar(x - width / 2, local_caps, width, label="Local GPU",
                    color=LOCAL_COLOR, zorder=3)
    bars_v = ax.bar(x + width / 2, vertex_caps, width, label="Vertex AI",
                    color=VERTEX_COLOR, zorder=3)

    for bar, cap in zip(bars_l, local_caps):
        ax.text(bar.get_x() + bar.get_width() / 2, cap + 2,
                f"{cap}", ha="center", fontweight="bold", fontsize=10,
                color=LOCAL_COLOR)
    for bar, cap in zip(bars_v, vertex_caps):
        ax.text(bar.get_x() + bar.get_width() / 2, cap + 2,
                f"{cap}", ha="center", fontweight="bold", fontsize=10,
                color=VERTEX_COLOR)

    # X-axis: group label + infrastructure notation
    xlabels = []
    for g in groups:
        xlabels.append(f"{g[0]}\nLocal: {g[3]}\nVertex: {g[4]}")
    ax.set_xticks(x)
    ax.set_xticklabels(xlabels, fontsize=7.5, linespacing=1.3)
    ax.set_ylabel("Capacity (msg/s per worker)")
    ax.set_title("Per-Worker Capacity: T4 vs L4 (Optimized Settings)")
    ax.set_ylim(0, max(max(local_caps), max(vertex_caps)) * 1.25)

    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=LOCAL_COLOR,
              label="Local GPU — dataflow:{machine}+{gpu}"),
        Patch(facecolor=VERTEX_COLOR,
              label="Vertex AI — dataflow:{machine} + endpoint:{machine}+{gpu}"),
    ]
    ax.legend(handles=legend_elements, loc="upper right", fontsize=9)

    fig.tight_layout()
    fname = "overall_capacity.png"
    fig.savefig(os.path.join(chart_dir, fname), dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fname


def chart_overall_cost(t4_dir, l4_dir, chart_dir):
    """T4 vs L4 cost comparison of best configs."""
    fig, ax = plt.subplots(figsize=(12, 5.5))

    entries = []
    for data_dir, gpu in [(t4_dir, "T4"), (l4_dir, "L4")]:
        cp = os.path.join(data_dir, "cost_analysis.json")
        if not os.path.exists(cp):
            continue
        cd = load_json(cp)
        configs = cd.get("qualifying_configs", [])
        if not configs:
            continue
        target = cd.get("target_rate", 1000)
        # Best local and best vertex
        local_configs = [c for c in configs if c["experiment"] == "local_gpu"]
        vertex_configs = [c for c in configs if c["experiment"] == "vertex_ai"]
        gt = cd.get("gpu_type", "")
        vw_ms = machine_short(cd.get("vertex_worker_machine", "n1-standard-4"))
        if local_configs:
            best_l = min(local_configs, key=lambda x: x["cost_per_hour"])
            w = best_l.get("workers_needed", 0)
            ms = best_l.get("machine_short", "?")
            lbl = fmt_infra_local(w, ms, gt)
            entries.append((
                f"{gpu} Local GPU\n{lbl}",
                best_l["cost_per_hour"], LOCAL_COLOR,
                best_l.get("breakdown", "")))
        if vertex_configs:
            best_v = min(vertex_configs, key=lambda x: x["cost_per_hour"])
            w = best_v.get("workers_needed", 0)
            r = best_v.get("replicas", 0)
            ep_ms = best_v.get("endpoint_machine_short", "?")
            lbl = fmt_infra_vertex(w, vw_ms, r, ep_ms, gt)
            entries.append((
                f"{gpu} Vertex AI\n{lbl}",
                best_v["cost_per_hour"], VERTEX_COLOR,
                best_v.get("breakdown", "")))

    if not entries:
        return None

    labels = [e[0] for e in entries]
    costs = [e[1] for e in entries]
    colors = [e[2] for e in entries]

    x = np.arange(len(labels))
    bars = ax.bar(x, costs, color=colors, width=0.5, zorder=3)
    for bar, cost in zip(bars, costs):
        ax.text(bar.get_x() + bar.get_width() / 2, cost + 0.2,
                f"${cost:.2f}/hr", ha="center", fontweight="bold", fontsize=11)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8, linespacing=1.2)
    ax.set_ylabel("Cost ($/hr)")
    ax.set_title(f"Cheapest Configuration: T4 vs L4 (for {target} msg/s at p99 < 750ms)")
    ax.set_ylim(0, max(costs) * 1.3)
    fig.tight_layout()
    fname = "overall_cost.png"
    fig.savefig(os.path.join(chart_dir, fname), dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fname


def chart_overall_architecture(chart_dir):
    """Architecture diagram: Local GPU vs Vertex AI data flow."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    for ax in [ax1, ax2]:
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 6)
        ax.axis("off")

    # Local GPU
    ax1.set_title("Local GPU Architecture", fontsize=14, fontweight="bold")
    boxes = [
        (1, 4.5, "Pub/Sub\n(input)"),
        (4, 4.5, "Dataflow\nWorker + GPU"),
        (7, 4.5, "Pub/Sub\n(output)"),
    ]
    for x, y, txt in boxes:
        ax1.add_patch(plt.Rectangle((x - 0.8, y - 0.5), 1.6, 1,
                                     facecolor="#e8f0fe", edgecolor=LOCAL_COLOR,
                                     linewidth=2))
        ax1.text(x, y, txt, ha="center", va="center", fontsize=9, fontweight="bold")
    ax1.annotate("", xy=(3.2, 4.5), xytext=(1.8, 4.5),
                 arrowprops=dict(arrowstyle="->", color=LOCAL_COLOR, lw=2))
    ax1.annotate("", xy=(6.2, 4.5), xytext=(4.8, 4.5),
                 arrowprops=dict(arrowstyle="->", color=LOCAL_COLOR, lw=2))
    ax1.text(5, 2.5, "Model runs IN-PROCESS\non worker GPU\n(no network hop)",
             ha="center", va="center", fontsize=10, style="italic",
             color=LOCAL_COLOR)

    # Vertex AI
    ax2.set_title("Vertex AI Architecture", fontsize=14, fontweight="bold")
    boxes2 = [
        (1, 4.5, "Pub/Sub\n(input)"),
        (4, 4.5, "Dataflow\nWorker (CPU)"),
        (7, 4.5, "Pub/Sub\n(output)"),
        (4, 2, "Vertex AI\nEndpoint"),
    ]
    for x, y, txt in boxes2:
        color = VERTEX_COLOR if "Vertex" in txt else LOCAL_COLOR
        fc = "#fce8e6" if "Vertex" in txt else "#e8f0fe"
        ax2.add_patch(plt.Rectangle((x - 0.8, y - 0.5), 1.6, 1,
                                     facecolor=fc, edgecolor=color,
                                     linewidth=2))
        ax2.text(x, y, txt, ha="center", va="center", fontsize=9, fontweight="bold")
    ax2.annotate("", xy=(3.2, 4.5), xytext=(1.8, 4.5),
                 arrowprops=dict(arrowstyle="->", color=LOCAL_COLOR, lw=2))
    ax2.annotate("", xy=(6.2, 4.5), xytext=(4.8, 4.5),
                 arrowprops=dict(arrowstyle="->", color=LOCAL_COLOR, lw=2))
    ax2.annotate("", xy=(4, 3), xytext=(4, 4),
                 arrowprops=dict(arrowstyle="<->", color=VERTEX_COLOR, lw=2))
    ax2.text(4.8, 3.5, "HTTP", ha="left", fontsize=9, color=VERTEX_COLOR,
             fontweight="bold")

    fig.tight_layout()
    fname = "overall_architecture.png"
    fig.savefig(os.path.join(chart_dir, fname), dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fname


def report_overall(base_dir):
    """Generate the top-level cross-GPU comparison report."""
    t4_dir = os.path.join(base_dir, "data", "runs", "t4_full")
    l4_dir = os.path.join(base_dir, "data", "runs", "l4_full")
    report_dir = os.path.join(base_dir, "reports")
    chart_dir = os.path.join(report_dir, "charts")
    ensure_dir(chart_dir)

    c1 = chart_overall_capacity(t4_dir, l4_dir, chart_dir)
    c2 = chart_overall_cost(t4_dir, l4_dir, chart_dir)
    c3 = chart_overall_architecture(chart_dir)
    print(f"  Charts: {c1}, {c2}, {c3}")

    md = ["# GPU Inference Benchmark: Overall Report\n"]

    md.append("## Architecture\n")
    md.append("Two inference approaches compared under identical conditions:\n\n")
    md.append("- **Local GPU**: Model runs directly on each Dataflow worker's GPU. "
              "Inference in-process, no network hop.\n")
    md.append("- **Vertex AI**: Workers send HTTP prediction requests to a "
              "Vertex AI endpoint. Model runs on separate managed infrastructure.\n")
    if c3:
        md.append(f"\n![Architecture](charts/{c3})\n")

    md.append("\n## Methodology\n")
    md.append("An 8-phase systematic capacity planning study to find the "
              "cheapest infrastructure that sustains "
              "**1000 msg/s at p99 < 750ms**:\n\n")
    md.append("1. **Baseline Capacity** -- single worker, default settings, "
              "rate sweep to find saturation\n")
    md.append("2. **Thread Tuning** -- sweep harness threads (1-12) per experiment\n")
    md.append("3. **Batch Size** -- sweep max_batch_size to optimize throughput\n")
    md.append("4. **Min Batch Size** -- tune accumulation wait tradeoff\n")
    md.append("5. **Machine Sweep** -- compare worker machine types\n")
    md.append("6. **Re-Tune** -- optimize settings per machine type\n")
    md.append("7. **Scaling** -- verify linear scaling with multiple workers\n")
    md.append("8. **Cost Analysis** -- find cheapest config for "
              "1000 msg/s at p99 < 750ms\n")

    # Cross-GPU comparison table
    md.append("\n## Cross-GPU Comparison\n")

    gpu_summaries = []
    for data_dir, gpu in [(t4_dir, "T4"), (l4_dir, "L4")]:
        if not os.path.isdir(data_dir):
            continue
        retune = os.path.join(data_dir, "phase6_retune")
        cost_path = os.path.join(data_dir, "cost_analysis.json")

        summary = {"gpu": gpu, "machines": {}}

        if os.path.isdir(retune):
            for mach in sorted(os.listdir(retune)):
                ap = os.path.join(retune, mach, "analysis.json")
                if os.path.exists(ap):
                    a = load_json(ap)
                    summary["machines"][mach] = a.get("best_settings", {})

        if os.path.exists(cost_path):
            cd = load_json(cost_path)
            configs = cd.get("qualifying_configs", [])
            if configs:
                summary["best_cost"] = min(configs, key=lambda x: x["cost_per_hour"])
            summary["target_rate"] = cd.get("target_rate", 1000)

        gpu_summaries.append(summary)

    if gpu_summaries:
        # Collect env configs per GPU for infrastructure rows
        gpu_envs = {}
        for data_dir, gpu in [(t4_dir, "T4"), (l4_dir, "L4")]:
            if os.path.isdir(data_dir):
                gpu_envs[gpu] = load_env_config(data_dir)

        md.append("| Metric |")
        for gs in gpu_summaries:
            for mach in gs["machines"]:
                md.append(f" {gs['gpu']} {mach} |")
        md.append("\n|---|")
        for gs in gpu_summaries:
            for _ in gs["machines"]:
                md.append("---|")
        md.append("\n")

        # Infrastructure rows using compact notation
        vw_short = machine_short("n1-standard-4")  # vertex workers are always n1s4

        md.append("| **Local GPU Infrastructure** |")
        for gs in gpu_summaries:
            env = gpu_envs.get(gs["gpu"], {})
            for mach in gs["machines"]:
                lbl = fmt_infra(1, "dataflow", mach, env.get("gpu_type"))
                md.append(f" {lbl} |")
        md.append("\n")

        md.append("| **Vertex AI Infrastructure** |")
        for gs in gpu_summaries:
            env = gpu_envs.get(gs["gpu"], {})
            for mach in gs["machines"]:
                lbl = fmt_infra_vertex(1, vw_short, 1, mach,
                                       env.get("gpu_type"))
                md.append(f" {lbl} |")
        md.append("\n")

        rows = [
            ("Local GPU Capacity",
             lambda bs: f"{bs.get('local_capacity', '-')} msg/s"),
            ("Vertex AI Capacity",
             lambda bs: f"{bs.get('vertex_capacity', '-')} msg/s"),
            ("Local GPU Threads", lambda bs: str(bs.get("threads_local_gpu", "-"))),
            ("Vertex AI Threads", lambda bs: str(bs.get("threads_vertex_ai", "-"))),
            ("Local GPU max_batch", lambda bs: str(bs.get("max_batch_local_gpu", "-"))),
            ("Vertex AI max_batch", lambda bs: str(bs.get("max_batch_vertex_ai", "-"))),
            ("Local GPU min_batch", lambda bs: str(bs.get("min_batch_local_gpu", "-"))),
            ("Vertex AI min_batch", lambda bs: str(bs.get("min_batch_vertex_ai", "-"))),
        ]
        for row_label, fn in rows:
            md.append(f"| {row_label} |")
            for gs in gpu_summaries:
                for mach, bs in gs["machines"].items():
                    md.append(f" {fn(bs)} |")
            md.append("\n")

    if c1:
        md.append(f"\n![Per-Worker Capacity](charts/{c1})\n")
    if c2:
        md.append(f"\n![Cost Comparison](charts/{c2})\n")

    # Final recommendation
    md.append("\n## Recommendation\n")
    for data_dir, gpu in [(t4_dir, "T4"), (l4_dir, "L4")]:
        gs = next((g for g in gpu_summaries if g["gpu"] == gpu), None)
        if not gs:
            continue
        bc = gs.get("best_cost")
        if not bc:
            continue
        env = gpu_envs.get(gpu, {})
        gt = env.get("gpu_type", "")
        vw_ms = machine_short(env.get("vertex_worker_machine", "n1-standard-4"))
        if bc["experiment"] == "local_gpu":
            w = bc.get("workers_needed", 0)
            ms = bc.get("machine_short", "?")
            infra = fmt_infra_local(w, ms, gt)
        else:
            w = bc.get("workers_needed", 0)
            r = bc.get("replicas", 0)
            ep_ms = bc.get("endpoint_machine_short", "?")
            infra = fmt_infra_vertex(w, vw_ms, r, ep_ms, gt)
        md.append(f"**{gpu}**: Cheapest to sustain "
                  f"{gs.get('target_rate', 1000)} msg/s at p99 < 750ms = "
                  f"**${bc['cost_per_hour']:.2f}/hr** "
                  f"(`{infra}`)\n\n")

    # Future Work
    md.append("\n## Future Work\n")
    md.append("Areas that could add value in a follow-up benchmark "
              "using the same GPU types and machine families:\n\n")
    md.append("1. **Full-scale validation** -- Run at the actual "
              "1000 msg/s target to confirm projections hold. "
              "Phase 7 tested up to ~750 msg/s; the final cost numbers "
              "extrapolate from there assuming linear scaling continues.\n")
    md.append("2. **Longer duration tests** -- Each rate was tested for "
              "100 seconds, enough to find the saturation knee but not "
              "long enough to reveal memory leaks, GC pauses, or "
              "throughput drift that may emerge over 10--30 minute "
              "sustained runs.\n")
    md.append("3. **Finer rate granularity near saturation** -- Phases "
              "used 25 msg/s increments. Sweeping at 5--10 msg/s steps "
              "around each saturation knee (e.g. 60--90 msg/s for T4 "
              "Local GPU) would sharpen capacity numbers.\n")
    md.append("4. **Sequence length sensitivity** -- All tests used "
              "`max_seq_length=128`. Longer inputs increase GPU compute "
              "per item and would shift the optimal batch size, thread "
              "count, and per-worker capacity.\n")
    md.append("5. **Model optimization** -- TensorRT, ONNX Runtime, or "
              "`torch.compile()` could substantially change GPU "
              "inference throughput without any pipeline tuning changes, "
              "potentially improving per-worker capacity.\n")
    md.append("6. **Worker-to-replica ratio sweep** -- Phase 7 tested "
              "a grid of replica and worker counts for Vertex AI. "
              "A more systematic sweep of the ratio (e.g. 1:1, 2:1, "
              "3:1 workers per replica) at larger scale could identify "
              "the most cost-efficient balance.\n")
    md.append("\n### Scaling Flexibility and Variable Rates\n")
    md.append("This benchmark tested steady-state throughput at fixed "
              "worker and replica counts. A dedicated follow-up study "
              "could test how well each approach handles real-world "
              "dynamics:\n\n")
    md.append("- **Variable and bursty traffic** -- Real workloads are "
              "not constant-rate. Testing with step changes, sinusoidal "
              "ramps, or Poisson-distributed arrivals would show how "
              "well each approach absorbs traffic spikes.\n")
    md.append("- **Cold start and warm-up latency** -- How long does a "
              "newly added Dataflow worker or Vertex AI replica take to "
              "reach steady-state throughput? This matters for "
              "autoscaling responsiveness.\n")
    md.append("- **Autoscaling behavior** -- Testing with Dataflow "
              "autoscaling enabled (and Vertex AI autoscaling for the "
              "endpoint) would measure scale-up/down lag, "
              "over-provisioning costs, and whether the system can "
              "self-right under load changes.\n")

    md.append("\n## GPU Reports\n")
    for data_dir, gpu in [(t4_dir, "T4"), (l4_dir, "L4")]:
        rp = os.path.join(data_dir, "reports", "gpu_report.md")
        rel = os.path.relpath(rp, report_dir)
        if os.path.exists(rp):
            md.append(f"- [{gpu} GPU Report]({rel})\n")
        else:
            md.append(f"- {gpu} GPU Report *(not yet generated)*\n")

    out = os.path.join(report_dir, "benchmark_report.md")
    with open(out, "w") as f:
        f.write("".join(md))
    print(f"  Overall Report: {out}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

PHASE_GENERATORS = {
    1: report_phase1,
    2: report_phase2,
    3: report_phase3,
    4: report_phase4,
    5: report_phase5,
    6: report_phase6,
    7: report_phase7,
    8: report_phase8,
}


def main():
    parser = argparse.ArgumentParser(
        description="Generate drill-through benchmark reports with charts."
    )
    parser.add_argument("--data-dir",
                        help="Data directory (e.g. data/runs/t4_full)")
    parser.add_argument("--phase", type=int, choices=range(1, 9),
                        help="Generate a single phase report (1-8)")
    parser.add_argument("--gpu-summary", action="store_true",
                        help="Generate GPU summary report")
    parser.add_argument("--overall", action="store_true",
                        help="Generate cross-GPU overall report")
    parser.add_argument("--all", action="store_true",
                        help="Generate all reports for --data-dir")
    args = parser.parse_args()

    setup_style()

    if args.overall:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        print("Generating overall report...")
        report_overall(base)
        return

    if not args.data_dir:
        parser.error("--data-dir is required (unless using --overall)")

    data_dir = os.path.abspath(args.data_dir)
    report_dir = os.path.join(data_dir, "reports")
    ensure_dir(report_dir)

    gpu_label = detect_gpu_label(data_dir)

    if args.phase:
        print(f"Generating Phase {args.phase} report for {gpu_label}...")
        PHASE_GENERATORS[args.phase](data_dir, report_dir)
    elif args.gpu_summary:
        print(f"Generating GPU summary for {gpu_label}...")
        report_gpu_summary(data_dir, report_dir)
    elif args.all:
        print(f"Generating all reports for {gpu_label}...")
        for phase_num in sorted(PHASE_GENERATORS.keys()):
            print(f"\n--- Phase {phase_num} ---")
            PHASE_GENERATORS[phase_num](data_dir, report_dir)
        print(f"\n--- GPU Summary ---")
        report_gpu_summary(data_dir, report_dir)
    else:
        parser.error("Specify --phase N, --gpu-summary, --all, or --overall")


if __name__ == "__main__":
    main()
