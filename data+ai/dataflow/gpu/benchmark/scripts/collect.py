"""Subscribe to output topic, collect result messages, compute and print stats."""

import argparse
import json
import sys
import threading
import time

import numpy as np
from google.cloud import pubsub_v1


def collect_results(project_id, subscription_id, expected_count, timeout_minutes=30):
    """Pull messages from the output subscription until expected_count or timeout."""
    subscriber = pubsub_v1.SubscriberClient()
    sub_path = subscriber.subscription_path(project_id, subscription_id)
    results = []
    lock = threading.Lock()
    done = threading.Event()

    def callback(message):
        with lock:
            results.append({
                "text": message.data.decode("utf-8"),
                "latency_ms": float(message.attributes["latency_ms"]),
                "pure_inference_time_ms": float(message.attributes["pure_inference_time_ms"]),
                "predicted_class": message.attributes["predicted_class"],
                "confidence": float(message.attributes["confidence"]),
                "publish_time_ms": float(message.attributes["publish_time_ms"]),
                "processed_time_ms": float(message.attributes["processed_time_ms"]),
            })
            message.ack()
            count = len(results)

        if count % 5000 == 0:
            print(f"  Collected {count}/{expected_count}...", flush=True)
        if count >= expected_count:
            done.set()

    print(f"Subscribing to {sub_path}, expecting {expected_count} messages...", flush=True)
    future = subscriber.subscribe(sub_path, callback)

    try:
        done.wait(timeout=timeout_minutes * 60)
    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        future.cancel()
        future.result(timeout=10)

    print(f"Collected {len(results)} messages total.", flush=True)
    return results


def print_report(results, label):
    """Compute and print stats for a single experiment's results."""
    if not results:
        print(f"\n{label}: No results collected.")
        return

    lats = np.array([r["latency_ms"] for r in results])
    infs = np.array([r["pure_inference_time_ms"] for r in results])
    confs = np.array([r["confidence"] for r in results])

    # Compute throughput from actual timestamps
    pub_times = [r["publish_time_ms"] for r in results]
    proc_times = [r["processed_time_ms"] for r in results]
    first_pub = min(pub_times)
    last_proc = max(proc_times)
    elapsed_s = (last_proc - first_pub) / 1000.0
    throughput = len(results) / elapsed_s if elapsed_s > 0 else 0

    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    print(f"  Messages processed:  {len(results)}")
    print(f"  Elapsed time:        {elapsed_s:.1f}s")
    print(f"  Throughput:          {throughput:.0f} msg/s")
    print()
    print(f"  End-to-end latency (ms):")
    print(f"    p50  = {np.percentile(lats, 50):.0f}")
    print(f"    p95  = {np.percentile(lats, 95):.0f}")
    print(f"    p99  = {np.percentile(lats, 99):.0f}")
    print(f"    mean = {np.mean(lats):.0f}")
    print(f"    max  = {np.max(lats):.0f}")
    print()
    print(f"  Pure inference time (ms):")
    print(f"    p50  = {np.percentile(infs, 50):.1f}")
    print(f"    p95  = {np.percentile(infs, 95):.1f}")
    print(f"    p99  = {np.percentile(infs, 99):.1f}")
    print(f"    mean = {np.mean(infs):.1f}")
    print()
    print(f"  Confidence:")
    print(f"    mean = {np.mean(confs):.4f}")
    print(f"    min  = {np.min(confs):.4f}")
    print()

    # Class distribution
    class_counts = {}
    for r in results:
        cls = r["predicted_class"]
        class_counts[cls] = class_counts.get(cls, 0) + 1
    print(f"  Class distribution:")
    for cls, count in sorted(class_counts.items()):
        pct = 100 * count / len(results)
        print(f"    {cls}: {count} ({pct:.1f}%)")
    print()


def save_results(results, output_file):
    """Save raw results to JSON for later comparison."""
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project_id", required=True)
    parser.add_argument("--subscription_id", required=True, help="Subscription short name")
    parser.add_argument("--expected_count", type=int, default=100000)
    parser.add_argument("--timeout_minutes", type=int, default=30)
    parser.add_argument("--label", default="Experiment", help="Label for the report")
    parser.add_argument("--output_file", default="", help="Save raw results to JSON")
    args = parser.parse_args()

    results = collect_results(
        args.project_id, args.subscription_id,
        args.expected_count, args.timeout_minutes,
    )

    print_report(results, args.label)

    if args.output_file:
        save_results(results, args.output_file)
