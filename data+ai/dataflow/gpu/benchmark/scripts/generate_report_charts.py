#!/usr/bin/env python3
"""Generate publication-quality charts for the full benchmark report.

Reads phase result JSON files and creates focused visualizations that
tell the story of each phase's conclusion.
"""

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np


def load_json(path):
    with open(path) as f:
        return json.load(f)


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


def chart_phase1(data, output_dir):
    """Phase 1: The Saturation Cliff — latency explodes at capacity limit."""
    rates = [25, 50, 75, 100, 125, 150]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    # Left: Latency vs Rate
    for mode, color, label in [
        ("local_gpu", LOCAL_COLOR, "Local GPU"),
        ("vertex_ai", VERTEX_COLOR, "Vertex AI"),
    ]:
        p50 = [data[mode][str(r)]["latency_p50"] for r in rates]
        p99 = [data[mode][str(r)]["latency_p99"] for r in rates]
        ax1.plot(rates, p50, "o-", color=color, linewidth=2.5, markersize=8, label=f"{label} p50")
        ax1.fill_between(rates, p50, p99, alpha=0.15, color=color)
        ax1.plot(rates, p99, "s--", color=color, linewidth=1, markersize=5, alpha=0.6, label=f"{label} p99")

    ax1.set_yscale("log")
    ax1.set_xlabel("Publish Rate (msg/s)")
    ax1.set_ylabel("End-to-End Latency (ms)")
    ax1.set_title("Latency vs Rate — 12 Threads (Default)")
    ax1.axvline(x=62.5, color=LOCAL_COLOR, linestyle=":", alpha=0.5)
    ax1.annotate("Local GPU\nsaturates", xy=(62.5, 500), fontsize=9,
                 color=LOCAL_COLOR, ha="center")
    ax1.axvline(x=112.5, color=VERTEX_COLOR, linestyle=":", alpha=0.5)
    ax1.annotate("Vertex AI\nsaturates", xy=(112.5, 200), fontsize=9,
                 color=VERTEX_COLOR, ha="center")
    ax1.legend(loc="upper left", fontsize=9)
    ax1.set_xticks(rates)

    # Right: Throughput vs Rate
    for mode, color, label in [
        ("local_gpu", LOCAL_COLOR, "Local GPU"),
        ("vertex_ai", VERTEX_COLOR, "Vertex AI"),
    ]:
        tp = [data[mode][str(r)]["throughput"] for r in rates]
        ax2.plot(rates, tp, "o-", color=color, linewidth=2.5, markersize=8, label=label)

    ax2.plot(rates, rates, "k--", linewidth=1, alpha=0.4, label="Ideal (rate = throughput)")
    ax2.set_xlabel("Publish Rate (msg/s)")
    ax2.set_ylabel("Achieved Throughput (msg/s)")
    ax2.set_title("Throughput vs Rate — Where It Saturates")
    ax2.legend(loc="upper left", fontsize=9)
    ax2.set_xticks(rates)

    fig.suptitle("Phase 1: Single-Worker Capacity with Default Settings",
                 fontsize=15, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "phase1_saturation.png"),
                dpi=150, bbox_inches="tight")
    plt.close(fig)


def chart_phase2(p1_data, p2_data, output_dir):
    """Phase 2: Thread Impact — opposite effects for Local GPU vs Vertex AI."""
    rates = [25, 50, 75, 100, 125, 150]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    # Left: Local GPU — 12 threads vs 2 threads
    p50_12t = [p1_data["local_gpu"][str(r)]["latency_p50"] for r in rates]
    p50_2t = [p2_data["local_gpu"][str(r)]["latency_p50"] for r in rates]
    ax1.plot(rates, p50_12t, "o-", color=LOCAL_LIGHT, linewidth=2, markersize=7,
             label="12 threads (default)")
    ax1.plot(rates, p50_2t, "o-", color=LOCAL_COLOR, linewidth=2.5, markersize=8,
             label="2 threads")
    ax1.set_yscale("log")
    ax1.set_xlabel("Publish Rate (msg/s)")
    ax1.set_ylabel("Latency p50 (ms)")
    ax1.set_title("Local GPU: 2 Threads Doubles Capacity")
    ax1.legend(fontsize=10)
    ax1.set_xticks(rates)
    ax1.axhspan(0, 200, alpha=0.05, color="green")
    ax1.annotate("2 threads: healthy\nthrough 100 msg/s",
                 xy=(87, 35), fontsize=9, color=LOCAL_COLOR,
                 fontweight="bold")

    # Right: Vertex AI — 12 threads vs 2 threads
    p50_12t = [p1_data["vertex_ai"][str(r)]["latency_p50"] for r in rates]
    p50_2t = [p2_data["vertex_ai"][str(r)]["latency_p50"] for r in rates]
    ax2.plot(rates, p50_12t, "o-", color=VERTEX_COLOR, linewidth=2.5, markersize=8,
             label="12 threads (default)")
    ax2.plot(rates, p50_2t, "o-", color=VERTEX_LIGHT, linewidth=2, markersize=7,
             label="2 threads")
    ax2.set_yscale("log")
    ax2.set_xlabel("Publish Rate (msg/s)")
    ax2.set_ylabel("Latency p50 (ms)")
    ax2.set_title("Vertex AI: 2 Threads Destroys Throughput")
    ax2.legend(fontsize=10)
    ax2.set_xticks(rates)
    ax2.annotate("2 threads: can't even\nhandle 50 msg/s",
                 xy=(50, 30000), fontsize=9, color="#888",
                 fontweight="bold")

    fig.suptitle("Phase 2: Thread Count Has Opposite Effects",
                 fontsize=15, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "phase2_threads.png"),
                dpi=150, bbox_inches="tight")
    plt.close(fig)


def chart_phase3(data_dir, output_dir):
    """Phase 3: Batch Size — two panels: 100 msg/s (healthy) and 125 msg/s (stress)."""
    batch_sizes = [4, 8, 16, 32, 64, 128, 256]

    fig, axes = plt.subplots(2, 2, figsize=(14, 11))

    for col, (rate, rate_label) in enumerate([("100", "100 msg/s (Near Saturation)"),
                                               ("125", "125 msg/s (Beyond Saturation)")]):
        local_p50 = []
        vertex_p50 = []
        for bs in batch_sizes:
            path = os.path.join(data_dir, f"phase3_batch/batch_{bs}/benchmark_results.json")
            d = load_json(path)
            local_p50.append(d["local_gpu"][rate]["latency_p50"])
            vertex_p50.append(d["vertex_ai"][rate]["latency_p50"])

        x = np.arange(len(batch_sizes))
        labels = [str(bs) for bs in batch_sizes]

        # Top row: Local GPU
        ax = axes[0, col]
        bars = ax.bar(x, local_p50, 0.6, color=LOCAL_COLOR, zorder=3)
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.set_xlabel("max_batch_size")
        ax.set_ylabel("Latency p50 (ms)")
        ax.set_title(f"Local GPU — {rate_label}")

        # Highlight best
        best_idx = int(np.argmin(local_p50))
        bars[best_idx].set_color("#0d47a1")
        ax.annotate(f"{local_p50[best_idx]:.0f}ms",
                     xy=(best_idx, local_p50[best_idx]),
                     fontsize=10, fontweight="bold", color="#0d47a1", ha="center",
                     xytext=(best_idx, max(local_p50) * 0.85),
                     arrowprops=dict(arrowstyle="->", color="#0d47a1"))

        # Bottom row: Vertex AI
        ax = axes[1, col]
        # Cap extreme outliers for readability
        vertex_display = [min(v, 5000) for v in vertex_p50]
        bars = ax.bar(x, vertex_display, 0.6, color=VERTEX_COLOR, zorder=3)
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.set_xlabel("max_batch_size")
        ax.set_ylabel("Latency p50 (ms)")
        ax.set_title(f"Vertex AI — {rate_label}")

        # Mark anomalies
        for i, v in enumerate(vertex_p50):
            if v > 5000:
                ax.annotate(f"{v/1000:.0f}s!", xy=(i, 5000), fontsize=8,
                             color="darkred", ha="center", fontweight="bold")

        # Highlight best (among non-anomalous)
        valid = [(i, v) for i, v in enumerate(vertex_p50) if v < 5000]
        if valid:
            best_idx, best_val = min(valid, key=lambda x: x[1])
            bars[best_idx].set_color("#b71c1c")
            ax.annotate(f"{best_val:.0f}ms",
                         xy=(best_idx, best_val),
                         fontsize=10, fontweight="bold", color="#b71c1c", ha="center",
                         xytext=(best_idx, max(vertex_display) * 0.85),
                         arrowprops=dict(arrowstyle="->", color="#b71c1c"))

    fig.suptitle("Phase 3: Batch Size Sweep (2 threads Local GPU, 12 threads Vertex AI)",
                 fontsize=15, fontweight="bold", y=1.01)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "phase3_batch.png"),
                dpi=150, bbox_inches="tight")
    plt.close(fig)


def _get_first_rate_stats(results_json, mode):
    """Get stats from the first (and usually only) rate key for a mode."""
    mode_data = results_json.get(mode, {})
    if not mode_data:
        return None, None
    rate_key = next(iter(mode_data))
    return rate_key, mode_data[rate_key]


def chart_phase5(data_dir, output_dir):
    """Phase 5: Worker Sweep — throughput and latency vs worker count.

    Local GPU uses scaled rates (per_worker_capacity × num_workers).
    Vertex AI uses a fixed rate (1000 msg/s).
    The chart auto-detects the rate from each result file.
    """
    sweep_dir = os.path.join(data_dir, "phase5_sweep")

    # Collect Local GPU results
    local_workers = []
    local_rates = []
    local_tp = []
    local_p50 = []
    local_p99 = []
    for nw in range(1, 20):
        path = os.path.join(sweep_dir, f"local_gpu_{nw}w", "benchmark_results.json")
        if not os.path.exists(path):
            continue
        d = load_json(path)
        rate_key, s = _get_first_rate_stats(d, "local_gpu")
        if s is None:
            continue
        local_workers.append(nw)
        local_rates.append(int(rate_key))
        local_tp.append(s["throughput"])
        local_p50.append(s["latency_p50"])
        local_p99.append(s["latency_p99"])

    # Collect Vertex AI results
    vertex_workers = []
    vertex_tp = []
    vertex_p50 = []
    vertex_p99 = []
    for nw in range(1, 20):
        path = os.path.join(sweep_dir, f"vertex_ai_{nw}w", "benchmark_results.json")
        if not os.path.exists(path):
            continue
        d = load_json(path)
        rate_key, s = _get_first_rate_stats(d, "vertex_ai")
        if s is None:
            continue
        vertex_workers.append(nw)
        vertex_tp.append(s["throughput"])
        vertex_p50.append(s["latency_p50"])
        vertex_p99.append(s["latency_p99"])

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 11))

    # Top-left: Local GPU throughput vs target rate
    ax1.bar(local_workers, local_tp, color=LOCAL_COLOR, zorder=3, label="Achieved")
    # Show target rate line for each worker count
    ax1.plot(local_workers, local_rates, "k--", linewidth=1.5, alpha=0.6,
             marker="D", markersize=5, label="Target rate")
    for w, tp, rate in zip(local_workers, local_tp, local_rates):
        ax1.text(w, tp + 8, f"{tp:.0f}", ha="center", fontweight="bold", fontsize=10)
    ax1.set_xlabel("Workers")
    ax1.set_ylabel("Throughput (msg/s)")
    ax1.set_title("Local GPU: Linear Scaling Verification")
    ax1.set_xticks(local_workers)
    max_y = max(max(local_tp), max(local_rates)) * 1.15 if local_tp else 500
    ax1.set_ylim(0, max_y)
    ax1.legend()

    # Top-right: Vertex AI throughput
    ax2.bar(vertex_workers, vertex_tp, color=VERTEX_COLOR, zorder=3)
    ax2.axhline(y=1000, color="black", linestyle="--", alpha=0.4, label="Target: 1000 msg/s")
    for w, tp in zip(vertex_workers, vertex_tp):
        ax2.text(w, tp + 15, f"{tp:.0f}", ha="center", fontsize=8,
                 fontweight="bold" if tp > 900 else "normal")
    ax2.set_xlabel("Workers (10 endpoint replicas)")
    ax2.set_ylabel("Throughput (msg/s)")
    ax2.set_title("Vertex AI: Finding the Sweet Spot")
    ax2.set_xticks(vertex_workers)
    ax2.set_ylim(0, 1100)
    ax2.legend()

    # Bottom-left: Local GPU latency
    ax3.plot(local_workers, [p / 1000 for p in local_p50], "o-", color=LOCAL_COLOR,
             linewidth=2.5, markersize=8, label="p50")
    ax3.plot(local_workers, [p / 1000 for p in local_p99], "s--", color=LOCAL_LIGHT,
             linewidth=1.5, markersize=6, label="p99")
    ax3.set_xlabel("Workers")
    ax3.set_ylabel("Latency (seconds)")
    ax3.set_title("Local GPU: Latency at Scaled Rates")
    ax3.set_xticks(local_workers)
    ax3.legend()

    # Bottom-right: Vertex AI latency
    ax4.plot(vertex_workers, [p / 1000 for p in vertex_p50], "o-", color=VERTEX_COLOR,
             linewidth=2.5, markersize=8, label="p50")
    ax4.plot(vertex_workers, [p / 1000 for p in vertex_p99], "s--", color=VERTEX_LIGHT,
             linewidth=1.5, markersize=6, label="p99")
    ax4.set_xlabel("Workers (10 endpoint replicas)")
    ax4.set_ylabel("Latency (seconds)")
    ax4.set_title("Vertex AI: Tail Latency vs Workers")
    ax4.set_xticks(vertex_workers)
    ax4.legend()

    fig.suptitle("Phase 5: Worker Sweep",
                 fontsize=15, fontweight="bold", y=1.01)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "phase5_sweep.png"),
                dpi=150, bbox_inches="tight")
    plt.close(fig)


def chart_summary(p1, p2, data_dir, output_dir):
    """Summary: Side-by-side comparison of best configs at scale.

    Finds the best worker count for each experiment by highest throughput
    with p99 < 10s, then compares them.
    """
    sweep_dir = os.path.join(data_dir, "phase5_sweep")

    # Find best Local GPU config (highest worker count available)
    local_best = None
    for nw in range(20, 0, -1):
        path = os.path.join(sweep_dir, f"local_gpu_{nw}w", "benchmark_results.json")
        if os.path.exists(path):
            d = load_json(path)
            _, s = _get_first_rate_stats(d, "local_gpu")
            if s:
                local_best = (nw, s)
                break

    # Find best Vertex AI config (highest throughput with p99 < 10s)
    vertex_best = None
    for nw in range(1, 20):
        path = os.path.join(sweep_dir, f"vertex_ai_{nw}w", "benchmark_results.json")
        if not os.path.exists(path):
            continue
        d = load_json(path)
        _, s = _get_first_rate_stats(d, "vertex_ai")
        if s and s["latency_p99"] < 10000:
            if vertex_best is None or s["throughput"] > vertex_best[1]["throughput"]:
                vertex_best = (nw, s)

    if not local_best or not vertex_best:
        print("  WARNING: Insufficient data for summary chart", flush=True)
        return

    local_nw, local_s = local_best
    vertex_nw, vertex_s = vertex_best

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    # Left: Throughput comparison
    configs = [
        (f"Local GPU\n{local_nw} workers", local_s["throughput"], LOCAL_COLOR),
        (f"Vertex AI\n{vertex_nw}w + 10 replicas", vertex_s["throughput"], VERTEX_COLOR),
    ]
    labels = [c[0] for c in configs]
    throughputs = [c[1] for c in configs]
    colors = [c[2] for c in configs]

    bars = ax1.bar(labels, throughputs, color=colors, width=0.4, zorder=3)
    target = max(throughputs) * 1.1
    for bar, tp in zip(bars, throughputs):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + target * 0.02,
                 f"{tp:.0f}", ha="center", fontweight="bold", fontsize=14)
    ax1.set_ylabel("Throughput (msg/s)")
    ax1.set_title("Best Config: Throughput")
    ax1.set_ylim(0, target)

    # Right: Latency comparison (p50, p95, p99)
    x = np.arange(2)
    width = 0.25
    p50s = [local_s["latency_p50"], vertex_s["latency_p50"]]
    p95s = [local_s["latency_p95"], vertex_s["latency_p95"]]
    p99s = [local_s["latency_p99"], vertex_s["latency_p99"]]

    ax2.bar(x - width, [p / 1000 for p in p50s], width, color=colors, label="p50", zorder=3)
    ax2.bar(x, [p / 1000 for p in p95s], width, color=colors, label="p95", zorder=3, alpha=0.6)
    ax2.bar(x + width, [p / 1000 for p in p99s], width, color=colors, label="p99", zorder=3, alpha=0.3)
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels)
    ax2.set_ylabel("Latency (seconds)")
    ax2.set_title("Best Config: Latency Distribution")
    ax2.legend(["p50", "p95", "p99"])

    for i, (p50, p99) in enumerate(zip(p50s, p99s)):
        ax2.annotate(f"p99={p99/1000:.1f}s", xy=(i + width, p99 / 1000),
                     fontsize=9, fontweight="bold", color=colors[i], ha="center",
                     xytext=(i + width, p99 / 1000 + max(p99s) / 1000 * 0.1),
                     arrowprops=dict(arrowstyle="->", color=colors[i]))

    fig.suptitle("Phase 5: Best Configuration Comparison",
                 fontsize=15, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "summary_comparison.png"),
                dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Generate report charts from benchmark results"
    )
    parser.add_argument(
        "--data-dir", default="data",
        help="Root data directory containing phase results (default: data). "
             "For multi-run support, pass data/runs/<run-name>/.",
    )
    args = parser.parse_args()

    data_dir = args.data_dir
    output_dir = os.path.join(data_dir, "report_charts")
    os.makedirs(output_dir, exist_ok=True)

    setup_style()

    p1 = load_json(os.path.join(data_dir, "phase1_capacity/benchmark_results.json"))
    p2 = load_json(os.path.join(data_dir, "phase2_threads/benchmark_results.json"))

    chart_phase1(p1, output_dir)
    print("  Generated: phase1_saturation.png")

    chart_phase2(p1, p2, output_dir)
    print("  Generated: phase2_threads.png")

    chart_phase3(data_dir, output_dir)
    print("  Generated: phase3_batch.png")

    chart_phase5(data_dir, output_dir)
    print("  Generated: phase5_sweep.png")

    chart_summary(p1, p2, data_dir, output_dir)
    print("  Generated: summary_comparison.png")


if __name__ == "__main__":
    main()
