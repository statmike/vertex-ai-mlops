"""End-to-end GPU inference benchmark with multi-rate phases.

Runs two Dataflow streaming experiments under identical conditions:
  Exp A: Local GPU inference (model on worker's T4)
  Exp B: Vertex AI endpoint inference (HTTP to endpoint with T4)

When both experiments are selected (default), they run in parallel — each
has its own Dataflow job and Pub/Sub subscriptions with no shared services.

For each experiment the script:
  1. Creates fresh Pub/Sub subscriptions (input + output)
  2. Launches the Dataflow pipeline (reads from subscription, not topic)
  3. Waits for workers to be healthy via warmup messages
  4. For each rate in --rates:
     a. Drains the output subscription
     b. Publishes N benchmark messages (background thread)
     c. Collects all N output messages (concurrent with publishing)
     d. Saves results to data/results_{mode}_{rate}.json
  5. Cancels the Dataflow job
  6. Cleans up subscriptions

After all experiments, generates:
  - Per-rate JSON result files
  - Summary JSON (benchmark_results.json)
  - Markdown report with comparison tables (benchmark_report.md)
  - Charts: latency, GPU time, throughput (data/charts/*.png)

Usage:
  uv run python scripts/run_benchmark.py
  uv run python scripts/run_benchmark.py --count 100000 --rates 50 75 100
  uv run python scripts/run_benchmark.py --experiments local_gpu
"""

import argparse
import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from google.api_core.exceptions import AlreadyExists, NotFound
from google.cloud import pubsub_v1


# ── Constants ────────────────────────────────────────────────────

# GPU-optimized GCE machine families require onHostMaintenance=TERMINATE,
# which Dataflow only sets when a GPU accelerator is attached. Vertex AI
# workers don't attach GPUs, so they must use N1 to avoid scheduling failures.
GPU_OPTIMIZED_PREFIXES = ("g2-", "a2-", "a3-")


def resolve_machine_type(machine_type, mode, env):
    """Resolve machine type, converting GPU-optimized families to N1 for vertex_ai.

    When a GPU-optimized machine type (G2, A2, A3) is requested for a vertex_ai
    Dataflow worker, it is converted to the N1 equivalent preserving the vCPU
    count. For example, g2-standard-8 → n1-standard-8.
    """
    if machine_type:
        if mode == "vertex_ai" and any(machine_type.startswith(p)
                                       for p in GPU_OPTIMIZED_PREFIXES):
            vcpu_str = machine_type.rsplit("-", 1)[-1]
            return f"n1-standard-{vcpu_str}"
        return machine_type
    if mode == "vertex_ai":
        fallback = env.get("MACHINE_TYPE", "n1-standard-4")
        if any(fallback.startswith(p) for p in GPU_OPTIMIZED_PREFIXES):
            vcpu_str = fallback.rsplit("-", 1)[-1]
            return f"n1-standard-{vcpu_str}"
        return fallback
    return env["MACHINE_TYPE"]


# ── Configuration ───────────────────────────────────────────────


def load_env(path=".env"):
    """Parse KEY=VALUE lines from .env file."""
    env = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


# ── Pub/Sub helpers ─────────────────────────────────────────────


def create_topic(project, topic_short):
    """Create a Pub/Sub topic, ignoring AlreadyExists."""
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project, topic_short)
    try:
        publisher.create_topic(request={"name": topic_path})
        print(f"  Created topic: {topic_short}", flush=True)
    except AlreadyExists:
        print(f"  Topic exists: {topic_short}", flush=True)
    return topic_path


def delete_topic(project, topic_short):
    """Delete a Pub/Sub topic, ignoring NotFound."""
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project, topic_short)
    try:
        publisher.delete_topic(request={"topic": topic_path})
        print(f"  Deleted topic: {topic_short}", flush=True)
    except NotFound:
        pass


def create_subscription(project, topic_short, sub_short):
    """Create a fresh subscription, draining stale messages if it exists."""
    subscriber = pubsub_v1.SubscriberClient()
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project, topic_short)
    sub_path = subscriber.subscription_path(project, sub_short)
    try:
        subscriber.create_subscription(
            request={
                "name": sub_path,
                "topic": topic_path,
                "ack_deadline_seconds": 600,
            }
        )
        print(f"  Created subscription: {sub_short}", flush=True)
    except AlreadyExists:
        print(f"  Subscription exists, draining: {sub_short}", flush=True)
        drain_subscription(project, sub_short)
    return sub_path


def delete_subscription(project, sub_short):
    """Delete a subscription, ignoring NotFound."""
    subscriber = pubsub_v1.SubscriberClient()
    sub_path = subscriber.subscription_path(project, sub_short)
    try:
        subscriber.delete_subscription(request={"subscription": sub_path})
        print(f"  Deleted subscription: {sub_short}", flush=True)
    except NotFound:
        pass


def drain_subscription(project, sub_short):
    """Pull and ack all pending messages from a subscription."""
    subscriber = pubsub_v1.SubscriberClient()
    sub_path = subscriber.subscription_path(project, sub_short)
    drained = 0
    while True:
        try:
            resp = subscriber.pull(
                request={"subscription": sub_path, "max_messages": 1000},
                timeout=5,
            )
        except Exception:
            break
        if not resp.received_messages:
            break
        ack_ids = [m.ack_id for m in resp.received_messages]
        subscriber.acknowledge(
            request={"subscription": sub_path, "ack_ids": ack_ids}
        )
        drained += len(ack_ids)
    if drained:
        print(f"  Drained {drained} stale messages", flush=True)


def warmup(project, topic_short, output_sub, timeout_s=900,
           data_file="data/test_transactions.txt"):
    """Send messages until pipeline produces output, confirming end-to-end health."""
    publisher = pubsub_v1.PublisherClient()
    subscriber = pubsub_v1.SubscriberClient()
    topic_path = publisher.topic_path(project, topic_short)
    sub_path = subscriber.subscription_path(project, output_sub)

    sent = 0
    received = 0
    deadline = time.time() + timeout_s

    while received == 0 and time.time() < deadline:
        # Send a small batch of warmup messages
        for _ in range(10):
            publisher.publish(
                topic_path,
                data=f"warmup-{sent}".encode(),
                publish_time_ms=str(int(time.time() * 1000)),
            )
            sent += 1

        time.sleep(15)

        # Check for output
        try:
            resp = subscriber.pull(
                request={"subscription": sub_path, "max_messages": 100},
                timeout=10,
            )
            if resp.received_messages:
                ack_ids = [m.ack_id for m in resp.received_messages]
                subscriber.acknowledge(
                    request={"subscription": sub_path, "ack_ids": ack_ids}
                )
                received += len(resp.received_messages)
                print(
                    f"    Pipeline is warm! ({received} messages processed)",
                    flush=True,
                )
        except Exception:
            pass

        if received == 0:
            elapsed = int(time.time() - (deadline - timeout_s))
            print(
                f"    Waiting for pipeline... ({elapsed}s, sent {sent} warmup messages)",
                flush=True,
            )

    if received == 0:
        print("  WARNING: No warmup messages received within timeout!", flush=True)
        return False

    # Drain any remaining warmup messages from output
    time.sleep(5)
    while True:
        try:
            resp = subscriber.pull(
                request={"subscription": sub_path, "max_messages": 1000},
                timeout=5,
            )
            if not resp.received_messages:
                break
            ack_ids = [m.ack_id for m in resp.received_messages]
            subscriber.acknowledge(
                request={"subscription": sub_path, "ack_ids": ack_ids}
            )
            received += len(resp.received_messages)
        except Exception:
            break

    print(f"  Connectivity warmup done: sent={sent}, drained={received}", flush=True)

    # Phase 2: Sustained warmup — send 200 messages at 50 msg/s using real
    # data to warm GPU caches, cuDNN autotuner, and connection pools (G10)
    if data_file and os.path.exists(data_file):
        print("  Sustained warmup: 200 messages at 50 msg/s...", flush=True)
        publish_messages(project, topic_short, data_file, rate=50, count=200)
        time.sleep(10)  # let them process
        drain_subscription(project, output_sub)
        print("  Sustained warmup complete.", flush=True)

    return True


def publish_messages(project, topic_short, data_file, rate, count):
    """Publish messages at a controlled rate. Returns elapsed time in seconds."""
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project, topic_short)

    with open(data_file) as f:
        lines = [line.strip() for line in f if line.strip()]
    # Cycle data if file has fewer lines than count
    if len(lines) < count:
        lines = (lines * (count // len(lines) + 1))[:count]
    else:
        lines = lines[:count]

    print(f"  Publishing {count} messages at {rate} msg/s...", flush=True)
    futures = []
    start = time.time()
    for i, text in enumerate(lines):
        pub_time_ms = str(int(time.time() * 1000))
        future = publisher.publish(
            topic_path, data=text.encode(), publish_time_ms=pub_time_ms
        )
        futures.append(future)

        # Rate limit
        if rate > 0:
            expected = (i + 1) / rate
            elapsed = time.time() - start
            if elapsed < expected:
                time.sleep(expected - elapsed)

        if (i + 1) % 5000 == 0:
            print(f"    Published {i + 1}/{count}...", flush=True)

    for f in futures:
        f.result(timeout=60)

    elapsed = time.time() - start
    print(
        f"  Published {count} messages in {elapsed:.1f}s ({count / elapsed:.0f} msg/s)",
        flush=True,
    )
    return elapsed


def collect_results(project, sub_short, expected_count, timeout_minutes=30,
                    idle_timeout_s=60):
    """Async pull from output subscription until expected_count, idle timeout, or hard timeout.

    Exits early if no new messages arrive for idle_timeout_s seconds,
    preventing hangs when a few messages are lost at high saturation rates.
    """
    subscriber = pubsub_v1.SubscriberClient()
    sub_path = subscriber.subscription_path(project, sub_short)
    results = []
    lock = threading.Lock()
    done = threading.Event()
    last_progress = [time.time()]

    def callback(message):
        with lock:
            result = {
                "text": message.data.decode("utf-8"),
                "latency_ms": float(message.attributes["latency_ms"]),
                "pure_inference_time_ms": float(
                    message.attributes["pure_inference_time_ms"]
                ),
                "predicted_class": message.attributes["predicted_class"],
                "confidence": float(message.attributes["confidence"]),
                "publish_time_ms": float(message.attributes["publish_time_ms"]),
                "processed_time_ms": float(message.attributes["processed_time_ms"]),
            }
            # New timing attributes (G4: inference_start_ms)
            if "queue_wait_ms" in message.attributes:
                result["queue_wait_ms"] = float(message.attributes["queue_wait_ms"])
            if "inference_overhead_ms" in message.attributes:
                result["inference_overhead_ms"] = float(message.attributes["inference_overhead_ms"])
            results.append(result)
            message.ack()
            n = len(results)
            last_progress[0] = time.time()

        if n % 5000 == 0:
            print(f"    Collected {n}/{expected_count}...", flush=True)
        if n >= expected_count:
            done.set()

    print(f"  Collecting results (expecting {expected_count})...", flush=True)
    future = subscriber.subscribe(sub_path, callback)

    try:
        deadline = time.time() + timeout_minutes * 60
        while not done.is_set() and time.time() < deadline:
            done.wait(timeout=10)
            with lock:
                idle = time.time() - last_progress[0]
                n = len(results)
            if n > 0 and idle > idle_timeout_s:
                print(
                    f"  No new messages for {idle_timeout_s}s, stopping collection "
                    f"({n}/{expected_count} collected).",
                    flush=True,
                )
                break
    except KeyboardInterrupt:
        print("\n  Interrupted.", flush=True)
    finally:
        future.cancel()
        try:
            future.result(timeout=10)
        except Exception:
            pass

    print(f"  Collected {len(results)} messages", flush=True)
    return results


# ── Dataflow helpers ────────────────────────────────────────────


def get_running_jobs(project, region, name_prefix=None):
    """Return set of currently running Dataflow job IDs.

    If name_prefix is given, only return jobs whose name starts with that prefix.
    This enables parallel runs with different prefixes to ignore each other's jobs.
    """
    filter_expr = "state=Running"
    if name_prefix:
        filter_expr += f" AND name:{name_prefix}*"
    result = subprocess.run(
        [
            "gcloud", "dataflow", "jobs", "list",
            "--project", project, "--region", region,
            "--filter", filter_expr,
            "--format", "value(id)",
        ],
        capture_output=True,
        text=True,
    )
    return set(result.stdout.strip().split("\n")) - {""}


def launch_pipeline(mode, env, input_sub_path, input_topic_path, output_topic_path,
                    harness_threads=None, num_workers=None, max_batch_size=None,
                    min_batch_size=None, raw_predict=False, job_name_prefix="benchmark",
                    machine_type=None):
    """Launch a Dataflow pipeline via subprocess, return Popen handle."""
    worker_count = str(num_workers) if num_workers else env["MIN_WORKERS"]
    # Unique job name: prefix-mode-timestamp (Dataflow requires lowercase, hyphens only)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    job_name = f"{job_name_prefix}-{mode.replace('_', '-')}-{timestamp}"
    # Resolve machine type: explicit override > .env default.
    # GPU-optimized families (G2, A2, A3) are converted to N1 equivalents
    # for vertex_ai workers (preserving vCPU count).
    resolved_machine = resolve_machine_type(machine_type, mode, env)
    cmd = [
        "uv", "run", "python", "-m", "benchmark.run",
        "--runner", "DataflowRunner",
        "--job_name", job_name,
        "--project", env["PROJECT_ID"],
        "--region", env["REGION"],
        "--machine_type", resolved_machine,
        "--num_workers", worker_count,
        "--sdk_container_image", env["WORKER_IMAGE"],
        "--sdk_location", "container",
        "--experiment", "use_runner_v2",
        "--experiment", "no_use_multiple_sdk_containers",
        "--disk_size_gb", "50",
        "--enable_streaming_engine",
        "--staging_location", env["STAGING"],
        "--temp_location", env["TEMP"],
        "--mode", mode,
        "--input_subscription", input_sub_path,
        "--input_topic", input_topic_path,
        "--output_topic", output_topic_path,
        "--model_path", env["MODEL_PATH"],
        "--num_labels", env["NUM_LABELS"],
        "--max_seq_length", env["MAX_SEQ_LENGTH"],
        "--category_names", env["CATEGORY_NAMES"],
    ]

    if num_workers:
        cmd += ["--max_num_workers", worker_count]

    if harness_threads:
        cmd += ["--number_of_worker_harness_threads", str(harness_threads)]

    if max_batch_size:
        cmd += ["--max_batch_size", str(max_batch_size)]

    if min_batch_size:
        cmd += ["--min_batch_size", str(min_batch_size)]

    if mode == "local_gpu":
        cmd += [
            "--device", "GPU",
            "--dataflow_service_option",
            f"worker_accelerator=type:{env['GPU_TYPE']};count:1;install-nvidia-driver",
        ]
    elif mode == "vertex_ai":
        cmd += [
            "--vertex_endpoint_id", env["VERTEX_ENDPOINT_ID"],
            "--vertex_region", env["REGION"],
        ]
        if raw_predict:
            cmd += ["--raw_predict"]
        endpoint_dns = env.get("VERTEX_ENDPOINT_DNS", "")
        if endpoint_dns:
            cmd += ["--vertex_endpoint_dns", endpoint_dns]

    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return proc


# Shared state for parallel job detection — prevents two threads from
# claiming the same Dataflow job ID.
_claimed_jobs = set()
_claimed_jobs_lock = threading.Lock()


def wait_for_new_job(project, region, known_jobs, timeout_minutes=15, name_prefix=None):
    """Poll until a NEW Dataflow job appears in RUNNING state."""
    print(
        f"  Waiting for Dataflow job to start (up to {timeout_minutes}m)...",
        flush=True,
    )
    deadline = time.time() + timeout_minutes * 60
    while time.time() < deadline:
        current = get_running_jobs(project, region, name_prefix=name_prefix)
        new_jobs = current - known_jobs
        if new_jobs:
            with _claimed_jobs_lock:
                unclaimed = new_jobs - _claimed_jobs
                if unclaimed:
                    job_id = unclaimed.pop()
                    _claimed_jobs.add(job_id)
                    print(f"  Job running: {job_id}", flush=True)
                    return job_id
        time.sleep(15)
    raise TimeoutError("Timed out waiting for Dataflow job to start")


def cancel_job(project, region, job_id):
    """Cancel a Dataflow job."""
    print(f"  Cancelling job {job_id}...", flush=True)
    subprocess.run(
        [
            "gcloud", "dataflow", "jobs", "cancel", job_id,
            "--project", project, "--region", region,
        ],
        capture_output=True,
    )
    print("  Job cancelled.", flush=True)


def pin_worker_count(project, region, job_id, num_workers, max_retries=10,
                     retry_delay=30):
    """Pin worker count by setting min=max via gcloud update-options.

    Without this, Streaming Engine autoscaler defaults to minNumWorkers=1
    and can scale down during or after benchmark measurement.

    Retries on FAILED_PRECONDITION (job not yet fully initialized).
    """
    print(f"  Pinning worker count: min={num_workers}, max={num_workers}", flush=True)
    for attempt in range(max_retries):
        result = subprocess.run(
            [
                "gcloud", "dataflow", "jobs", "update-options", job_id,
                "--project", project, "--region", region,
                f"--min-num-workers={num_workers}",
                f"--max-num-workers={num_workers}",
            ],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            print(f"  Worker count pinned to {num_workers}.", flush=True)
            return True
        if "FAILED_PRECONDITION" in result.stderr and attempt < max_retries - 1:
            print(f"    Job not yet initialized, retrying in {retry_delay}s "
                  f"(attempt {attempt + 1}/{max_retries})...", flush=True)
            time.sleep(retry_delay)
        else:
            print(f"  WARNING: Failed to pin workers: {result.stderr.strip()}",
                  flush=True)
            return False
    return False


def wait_for_workers(project, region, job_id, expected_workers, timeout_s=600,
                     has_gpu=False, vcpus_per_worker=4):
    """Wait until all expected workers are active for a Dataflow job.

    Polls CurrentVcpuCount (and CurrentGpuCount for GPU jobs) via
    `gcloud beta dataflow metrics list --source=service`. Worker count
    is derived from vCPUs / vcpus_per_worker.

    Returns True if all workers are confirmed active, False on timeout.
    """
    expected_vcpus = expected_workers * vcpus_per_worker

    print(f"  Waiting for {expected_workers} workers "
          f"({expected_vcpus} vCPUs, {expected_workers if has_gpu else 0} GPUs)...",
          flush=True)

    deadline = time.time() + timeout_s
    last_vcpus = 0
    last_gpus = 0

    while time.time() < deadline:
        try:
            result = subprocess.run(
                ["gcloud", "beta", "dataflow", "metrics", "list", job_id,
                 "--project", project, "--region", region,
                 "--source", "service", "--format", "json"],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0 and result.stdout.strip():
                metrics = json.loads(result.stdout)
                vcpus = 0
                gpus = 0
                for metric in metrics:
                    name = metric.get("name", {}).get("name", "")
                    if name == "CurrentVcpuCount":
                        vcpus = int(metric.get("scalar", 0))
                    elif name == "CurrentGpuCount":
                        gpus = int(metric.get("scalar", 0))

                workers = vcpus // vcpus_per_worker

                if vcpus != last_vcpus or gpus != last_gpus:
                    print(f"    Workers: {workers}/{expected_workers} "
                          f"(vCPUs: {vcpus}/{expected_vcpus}"
                          f"{f', GPUs: {gpus}/{expected_workers}' if has_gpu else ''})",
                          flush=True)
                    last_vcpus = vcpus
                    last_gpus = gpus

                if workers >= expected_workers:
                    if has_gpu and gpus < expected_workers:
                        pass  # Still waiting for GPUs
                    else:
                        print(f"  All {expected_workers} workers active.", flush=True)
                        return True
        except Exception as e:
            print(f"    Metrics check failed: {e}", flush=True)

        time.sleep(15)

    workers = last_vcpus // vcpus_per_worker
    print(f"  WARNING: Timed out waiting for workers. "
          f"Have {workers}/{expected_workers}.", flush=True)
    return False


# ── Stats ───────────────────────────────────────────────────────


def compute_stats(results, expected_count=None):
    """Compute summary statistics from collected results.

    Args:
        results: List of result dicts from collect_results().
        expected_count: Number of messages published (for loss rate tracking).
    """
    if not results:
        return {}

    lats = np.array([r["latency_ms"] for r in results])
    infs = np.array([r["pure_inference_time_ms"] for r in results])
    confs = np.array([r["confidence"] for r in results])

    pub_times = [r["publish_time_ms"] for r in results]
    proc_times = [r["processed_time_ms"] for r in results]
    elapsed_s = (max(proc_times) - min(pub_times)) / 1000.0
    throughput = len(results) / elapsed_s if elapsed_s > 0 else 0

    # Processing throughput: excludes ramp-up time (G11)
    proc_elapsed_s = (max(proc_times) - min(proc_times)) / 1000.0
    processing_throughput = round(
        len(results) / proc_elapsed_s if proc_elapsed_s > 0 else 0, 1)

    stats = {
        "count": len(results),
        "elapsed_s": round(elapsed_s, 1),
        "throughput": round(throughput, 1),
        "processing_throughput": processing_throughput,
        "latency_p50": round(float(np.percentile(lats, 50)), 1),
        "latency_p95": round(float(np.percentile(lats, 95)), 1),
        "latency_p99": round(float(np.percentile(lats, 99)), 1),
        "latency_mean": round(float(np.mean(lats)), 1),
        "gpu_p50": round(float(np.percentile(infs, 50)), 1),
        "gpu_p95": round(float(np.percentile(infs, 95)), 1),
        "gpu_p99": round(float(np.percentile(infs, 99)), 1),
        "gpu_mean": round(float(np.mean(infs)), 1),
        "confidence_mean": round(float(np.mean(confs)), 4),
    }

    # Loss rate tracking (G5)
    if expected_count is not None:
        stats["published_count"] = expected_count
        stats["collected_count"] = len(results)
        # Clamp at 0: Pub/Sub at-least-once delivery can produce duplicates,
        # which would make loss_rate negative. Report duplicates separately.
        if expected_count > 0:
            raw_loss = 1.0 - len(results) / expected_count
            stats["loss_rate"] = round(max(0.0, raw_loss), 4)
            if raw_loss < 0:
                stats["duplicate_rate"] = round(-raw_loss, 4)
        else:
            stats["loss_rate"] = 0

    # Queue wait and inference overhead percentiles (G4)
    queue_waits = [r["queue_wait_ms"] for r in results if "queue_wait_ms" in r]
    if queue_waits:
        qw = np.array(queue_waits)
        stats["queue_wait_p50"] = round(float(np.percentile(qw, 50)), 1)
        stats["queue_wait_p95"] = round(float(np.percentile(qw, 95)), 1)
        stats["queue_wait_p99"] = round(float(np.percentile(qw, 99)), 1)

    inf_overheads = [r["inference_overhead_ms"] for r in results if "inference_overhead_ms" in r]
    if inf_overheads:
        io = np.array(inf_overheads)
        stats["inference_overhead_p50"] = round(float(np.percentile(io, 50)), 1)
        stats["inference_overhead_p95"] = round(float(np.percentile(io, 95)), 1)
        stats["inference_overhead_p99"] = round(float(np.percentile(io, 99)), 1)

    return stats


# ── Console reporting ──────────────────────────────────────────


def print_rate_summary(mode, rate, stats):
    """Print a summary table for one rate phase."""
    print(f"\n  ── {mode} @ {rate} msg/s ──")
    print(f"  Messages:   {stats.get('count', 0):,}")
    print(f"  Throughput: {stats.get('throughput', 0):.1f} msg/s")
    print(
        f"  Latency:    p50={stats.get('latency_p50', 0):.0f}ms  "
        f"p95={stats.get('latency_p95', 0):.0f}ms  "
        f"p99={stats.get('latency_p99', 0):.0f}ms"
    )
    print(
        f"  GPU time:   p50={stats.get('gpu_p50', 0):.1f}ms  "
        f"p95={stats.get('gpu_p95', 0):.1f}ms  "
        f"p99={stats.get('gpu_p99', 0):.1f}ms"
    )


def print_final_comparison(all_stats, rates):
    """Print a final multi-rate comparison table."""
    print(f"\n{'=' * 80}")
    print("  BENCHMARK RESULTS — MULTI-RATE COMPARISON")
    print(f"{'=' * 80}")

    modes = sorted(all_stats.keys())
    if not modes:
        print("  No results to compare.")
        return

    # Header
    cols = []
    for mode in modes:
        for rate in rates:
            cols.append(f"{mode}@{rate}")

    header = f"  {'Metric':<25}"
    for col in cols:
        header += f" {col:>18}"
    print(f"\n{header}")
    print(f"  {'-' * 25}" + f" {'-' * 18}" * len(cols))

    rows = [
        ("Messages", "count", ",.0f"),
        ("Throughput (msg/s)", "throughput", ".1f"),
        ("Latency p50 (ms)", "latency_p50", ".1f"),
        ("Latency p95 (ms)", "latency_p95", ".1f"),
        ("Latency p99 (ms)", "latency_p99", ".1f"),
        ("GPU time p50 (ms)", "gpu_p50", ".1f"),
        ("GPU time p95 (ms)", "gpu_p95", ".1f"),
        ("GPU time p99 (ms)", "gpu_p99", ".1f"),
    ]

    for label, key, fmt in rows:
        line = f"  {label:<25}"
        for mode in modes:
            for rate in rates:
                stats = all_stats.get(mode, {}).get(rate, {})
                val = stats.get(key, "—")
                if isinstance(val, (int, float)):
                    val = f"{val:{fmt}}"
                line += f" {val:>18}"
        print(line)

    print(f"\n{'=' * 80}\n")


# ── Charts ──────────────────────────────────────────────────────


def generate_charts(all_stats, rates, output_dir):
    """Generate PNG charts for latency, GPU time, and throughput."""
    charts_dir = os.path.join(output_dir, "charts")
    os.makedirs(charts_dir, exist_ok=True)

    modes = sorted(all_stats.keys())
    if not modes:
        return

    mode_colors = {"local_gpu": "#1f77b4", "vertex_ai": "#ff7f0e"}
    mode_labels = {"local_gpu": "Local GPU", "vertex_ai": "Vertex AI"}

    # ── Latency chart (p50 + p95, log Y) ──
    fig, ax = plt.subplots(figsize=(8, 5))
    for mode in modes:
        color = mode_colors.get(mode, "#333333")
        label = mode_labels.get(mode, mode)
        p50s = [all_stats[mode].get(r, {}).get("latency_p50", None) for r in rates]
        p95s = [all_stats[mode].get(r, {}).get("latency_p95", None) for r in rates]
        ax.plot(rates, p50s, "o-", color=color, label=f"{label} p50")
        ax.plot(rates, p95s, "s--", color=color, alpha=0.6, label=f"{label} p95")
    ax.set_xlabel("Publish Rate (msg/s)")
    ax.set_ylabel("Latency (ms)")
    ax.set_title("End-to-End Latency vs Publish Rate")
    ax.set_yscale("log")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(charts_dir, "latency.png"), dpi=150)
    plt.close(fig)
    print(f"  Chart saved: charts/latency.png", flush=True)

    # ── GPU time chart (p50 + p95) ──
    fig, ax = plt.subplots(figsize=(8, 5))
    for mode in modes:
        color = mode_colors.get(mode, "#333333")
        label = mode_labels.get(mode, mode)
        p50s = [all_stats[mode].get(r, {}).get("gpu_p50", None) for r in rates]
        p95s = [all_stats[mode].get(r, {}).get("gpu_p95", None) for r in rates]
        ax.plot(rates, p50s, "o-", color=color, label=f"{label} p50")
        ax.plot(rates, p95s, "s--", color=color, alpha=0.6, label=f"{label} p95")
    ax.set_xlabel("Publish Rate (msg/s)")
    ax.set_ylabel("GPU Inference Time (ms)")
    ax.set_title("Pure GPU Inference Time vs Publish Rate")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(charts_dir, "gpu_time.png"), dpi=150)
    plt.close(fig)
    print(f"  Chart saved: charts/gpu_time.png", flush=True)

    # ── Throughput chart (grouped bar) ──
    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(rates))
    width = 0.35
    for i, mode in enumerate(modes):
        color = mode_colors.get(mode, "#333333")
        label = mode_labels.get(mode, mode)
        vals = [all_stats[mode].get(r, {}).get("throughput", 0) for r in rates]
        offset = (i - (len(modes) - 1) / 2) * width
        ax.bar(x + offset, vals, width, label=label, color=color)
    ax.set_xlabel("Publish Rate (msg/s)")
    ax.set_ylabel("Throughput (msg/s)")
    ax.set_title("Achieved Throughput vs Publish Rate")
    ax.set_xticks(x)
    ax.set_xticklabels([str(r) for r in rates])
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(os.path.join(charts_dir, "throughput.png"), dpi=150)
    plt.close(fig)
    print(f"  Chart saved: charts/throughput.png", flush=True)


# ── Markdown report ─────────────────────────────────────────────


def generate_report(all_stats, rates, count, output_dir):
    """Generate a markdown benchmark report with tables and chart references."""
    modes = sorted(all_stats.keys())
    mode_labels = {"local_gpu": "Local GPU", "vertex_ai": "Vertex AI"}
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = []
    lines.append("# Benchmark Report")
    lines.append("")
    lines.append(f"Generated: {timestamp}")
    lines.append("")

    # Config table
    lines.append("## Configuration")
    lines.append("")
    lines.append("| Parameter | Value |")
    lines.append("|---|---|")
    lines.append(f"| Messages per phase | {count} |")
    lines.append(f"| Rates (msg/s) | {', '.join(str(r) for r in rates)} |")
    lines.append(f"| Experiments | {', '.join(mode_labels.get(m, m) for m in modes)} |")
    lines.append("")

    # Throughput comparison
    lines.append("## Throughput")
    lines.append("")
    header = "| Rate (msg/s) |"
    separator = "|---|"
    for mode in modes:
        header += f" {mode_labels.get(mode, mode)} |"
        separator += "---|"
    lines.append(header)
    lines.append(separator)
    for rate in rates:
        row = f"| {rate} |"
        for mode in modes:
            val = all_stats.get(mode, {}).get(rate, {}).get("throughput", "—")
            if isinstance(val, (int, float)):
                val = f"{val:.1f}"
            row += f" {val} |"
        lines.append(row)
    lines.append("")

    # Latency comparison
    lines.append("## End-to-End Latency (ms)")
    lines.append("")
    header = "| Rate | Percentile |"
    separator = "|---|---|"
    for mode in modes:
        header += f" {mode_labels.get(mode, mode)} |"
        separator += "---|"
    lines.append(header)
    lines.append(separator)
    for rate in rates:
        for pct_label, pct_key in [("p50", "latency_p50"), ("p95", "latency_p95"), ("p99", "latency_p99")]:
            row = f"| {rate} | {pct_label} |"
            for mode in modes:
                val = all_stats.get(mode, {}).get(rate, {}).get(pct_key, "—")
                if isinstance(val, (int, float)):
                    val = f"{val:.1f}"
                row += f" {val} |"
            lines.append(row)
    lines.append("")

    # GPU time comparison
    lines.append("## GPU Inference Time (ms)")
    lines.append("")
    header = "| Rate | Percentile |"
    separator = "|---|---|"
    for mode in modes:
        header += f" {mode_labels.get(mode, mode)} |"
        separator += "---|"
    lines.append(header)
    lines.append(separator)
    for rate in rates:
        for pct_label, pct_key in [("p50", "gpu_p50"), ("p95", "gpu_p95"), ("p99", "gpu_p99")]:
            row = f"| {rate} | {pct_label} |"
            for mode in modes:
                val = all_stats.get(mode, {}).get(rate, {}).get(pct_key, "—")
                if isinstance(val, (int, float)):
                    val = f"{val:.1f}"
                row += f" {val} |"
            lines.append(row)
    lines.append("")

    # Charts
    lines.append("## Charts")
    lines.append("")
    lines.append("### Latency vs Publish Rate")
    lines.append("![Latency](charts/latency.png)")
    lines.append("")
    lines.append("### GPU Inference Time vs Publish Rate")
    lines.append("![GPU Time](charts/gpu_time.png)")
    lines.append("")
    lines.append("### Throughput vs Publish Rate")
    lines.append("![Throughput](charts/throughput.png)")
    lines.append("")

    report_path = os.path.join(output_dir, "benchmark_report.md")
    with open(report_path, "w") as f:
        f.write("\n".join(lines))
    print(f"  Report saved: {report_path}", flush=True)


# ── Orchestration ───────────────────────────────────────────────


def run_experiment(mode, label, env, args):
    """Run one experiment: launch once, run all rate phases, then cancel.

    Returns dict mapping rate -> results list.
    """
    print(f"\n{'=' * 70}", flush=True)
    print(f"  {label}", flush=True)
    print(f"{'=' * 70}", flush=True)

    project = env["PROJECT_ID"]
    region = env["REGION"]
    slug = mode.replace("_", "-")
    prefix = getattr(args, "topic_prefix", "benchmark")
    input_topic_short = f"{prefix}-input-{slug}"
    output_topic_short = f"{prefix}-output-{slug}"
    input_sub = f"{prefix}-input-{slug}-sub"
    output_sub = f"{prefix}-output-{slug}-sub"

    proc = None
    job_id = None
    rate_results = {}

    total_phases = len(args.rates)
    has_worker_check = args.num_workers is not None
    total_steps = (3 + total_phases) + (1 if has_worker_check else 0)

    try:
        # Phase 1: Create per-experiment topics and subscriptions
        step = 1
        print(f"\n[{step}/{total_steps}] Creating topics and subscriptions...", flush=True)
        input_topic_path = create_topic(project, input_topic_short)
        output_topic_path = create_topic(project, output_topic_short)
        input_sub_path = create_subscription(
            project, input_topic_short, input_sub
        )
        create_subscription(project, output_topic_short, output_sub)

        # Phase 2: Launch pipeline
        step = 2
        # Resolve per-experiment harness threads: specific flag > global flag > default
        per_exp_threads = getattr(args, f"harness_threads_{mode}", None)
        harness_threads = per_exp_threads if per_exp_threads is not None else args.harness_threads
        # Resolve per-experiment batch size: specific flag > global flag > default
        per_exp_batch = getattr(args, f"max_batch_size_{mode}", None)
        max_batch_size = per_exp_batch if per_exp_batch is not None else args.max_batch_size
        # Resolve per-experiment min batch size
        per_exp_min_batch = getattr(args, f"min_batch_size_{mode}", None)
        min_batch_size = per_exp_min_batch if per_exp_min_batch is not None else args.min_batch_size
        # Resolve machine type override
        machine_type = getattr(args, "machine_type", None)
        if harness_threads:
            print(f"  Using {harness_threads} harness threads", flush=True)
        if max_batch_size:
            print(f"  Using max_batch_size={max_batch_size}", flush=True)
        if min_batch_size:
            print(f"  Using min_batch_size={min_batch_size}", flush=True)
        if machine_type:
            print(f"  Using machine_type={machine_type}", flush=True)
        print(f"\n[{step}/{total_steps}] Launching Dataflow pipeline (mode={mode})...", flush=True)
        # Use mode-specific prefix so each experiment only sees its own jobs
        job_prefix = f"{prefix}-{slug}"
        known_jobs = get_running_jobs(project, region, name_prefix=job_prefix)
        raw_predict = getattr(args, "raw_predict", False)
        if raw_predict and mode == "vertex_ai":
            print(f"  Using rawPredict endpoint", flush=True)
        proc = launch_pipeline(
            mode, env, input_sub_path, input_topic_path, output_topic_path,
            harness_threads=harness_threads,
            num_workers=args.num_workers,
            max_batch_size=max_batch_size,
            min_batch_size=min_batch_size,
            raw_predict=raw_predict,
            job_name_prefix=prefix,
            machine_type=machine_type,
        )
        job_id = wait_for_new_job(project, region, known_jobs, name_prefix=job_prefix)

        # Pin worker count to prevent autoscaler from scaling down.
        # Failure to pin means results will be unreliable (autoscaler
        # can change worker count mid-benchmark), so treat as fatal.
        if args.num_workers:
            if not pin_worker_count(project, region, job_id, args.num_workers):
                print("  ERROR: Failed to pin worker count. "
                      "Results would be unreliable. Cancelling job.",
                      flush=True)
                cancel_job(project, region, job_id)
                return {}

        # Phase 3: Warmup (once for all rates)
        step = 3
        print(f"\n[{step}/{total_steps}] Warming up pipeline...", flush=True)
        if not warmup(project, input_topic_short, output_sub,
                      data_file=args.data_file):
            print("  ERROR: Warmup failed. Cancelling job.", flush=True)
            if job_id:
                cancel_job(project, region, job_id)
            return {}

        # Phase 3b: Verify all workers are active (when worker count is pinned)
        if has_worker_check:
            step += 1
            print(f"\n[{step}/{total_steps}] Verifying all {args.num_workers} "
                  f"workers are active...", flush=True)
            has_gpu = (mode == "local_gpu")
            # Derive vCPUs from the resolved machine type (same logic as launch_pipeline)
            resolved_mt = resolve_machine_type(machine_type, mode, env)
            try:
                vcpus = int(resolved_mt.rsplit("-", 1)[-1])
            except ValueError:
                vcpus = 4
                print(f"  WARNING: Could not parse vCPU count from "
                      f"'{resolved_mt}', assuming {vcpus}", flush=True)
            workers_ready = wait_for_workers(
                project, region, job_id, args.num_workers,
                timeout_s=600, has_gpu=has_gpu, vcpus_per_worker=vcpus,
            )
            if not workers_ready:
                print("  WARNING: Not all workers are active. "
                      "Results may undercount true capacity.", flush=True)

        # Phases N..N+R: One rate phase per rate
        for rate_idx, rate in enumerate(args.rates):
            step = (4 if not has_worker_check else 5) + rate_idx
            count = rate * args.duration if args.duration else args.count
            print(
                f"\n[{step}/{total_steps}] Rate phase: {rate} msg/s "
                f"({count:,} messages, {count / rate:.0f}s)...",
                flush=True,
            )

            # Drain both subscriptions before this phase to prevent
            # residual messages from prior phase contaminating results
            print("  Draining subscriptions...", flush=True)
            drain_subscription(project, input_sub)
            drain_subscription(project, output_sub)

            # Publish in background thread, collect in main thread
            publish_error = [None]

            def publish_worker(r=rate, c=count):
                try:
                    publish_messages(
                        project, input_topic_short,
                        args.data_file, r, c,
                    )
                except Exception as e:
                    publish_error[0] = e

            pub_thread = threading.Thread(target=publish_worker, daemon=True)
            pub_thread.start()

            # Collect concurrently in main thread
            results = collect_results(
                project, output_sub, count, args.timeout
            )

            # Wait for publisher: timeout based on expected duration + buffer
            pub_timeout = max(120, int(count / max(rate, 1)) + 60)
            pub_thread.join(timeout=pub_timeout)
            if pub_thread.is_alive():
                print(f"  WARNING: Publisher still running after {pub_timeout}s",
                      flush=True)
            if publish_error[0]:
                print(f"  WARNING: Publisher error: {publish_error[0]}", flush=True)

            rate_results[rate] = results

            # Per-rate summary
            stats = compute_stats(results, expected_count=count)
            print_rate_summary(mode, rate, stats)

        # Final step: Cancel job
        print(f"\n[Cleanup] Cancelling job and cleaning up...", flush=True)
        if job_id:
            cancel_job(project, region, job_id)

        return rate_results

    except KeyboardInterrupt:
        print("\n  Interrupted by user.", flush=True)
        if job_id:
            cancel_job(project, region, job_id)
        return rate_results

    except Exception as e:
        print(f"\n  ERROR: {type(e).__name__}: {e}", flush=True)
        if job_id:
            cancel_job(project, region, job_id)
        return rate_results

    finally:
        if proc:
            proc.terminate()
        delete_subscription(project, input_sub)
        delete_subscription(project, output_sub)
        delete_topic(project, input_topic_short)
        delete_topic(project, output_topic_short)


def main():
    parser = argparse.ArgumentParser(
        description="Run GPU inference benchmark (Local GPU vs Vertex AI) with multiple rate phases"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=100000,
        help="Number of benchmark messages per rate phase (default: 100000). Ignored if --duration is set.",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=None,
        help="Duration in seconds per rate phase. Overrides --count: message count = rate * duration.",
    )
    parser.add_argument(
        "--rates",
        type=int,
        nargs="+",
        default=[50, 75, 100],
        help="Publish rates in msg/s (default: 50 75 100)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=45,
        help="Collection timeout in minutes per rate phase (default: 45)",
    )
    parser.add_argument(
        "--data_file",
        default="data/test_transactions.txt",
        help="Input data file",
    )
    parser.add_argument(
        "--output_dir",
        default="data",
        help="Directory for result JSON files (default: data)",
    )
    parser.add_argument(
        "--experiments",
        nargs="+",
        default=["local_gpu", "vertex_ai"],
        choices=["local_gpu", "vertex_ai"],
        help="Which experiments to run (default: both)",
    )
    parser.add_argument(
        "--harness_threads",
        type=int,
        default=None,
        help="Override --number_of_worker_harness_threads for all experiments (default: Dataflow default, 12 for streaming)",
    )
    parser.add_argument(
        "--harness_threads_local_gpu",
        type=int,
        default=None,
        help="Override harness threads for local_gpu only (takes precedence over --harness_threads)",
    )
    parser.add_argument(
        "--harness_threads_vertex_ai",
        type=int,
        default=None,
        help="Override harness threads for vertex_ai only (takes precedence over --harness_threads)",
    )
    parser.add_argument(
        "--num_workers",
        type=int,
        default=None,
        help="Fixed worker count (sets both --num_workers and --max_num_workers, disabling autoscaling)",
    )
    parser.add_argument(
        "--max_batch_size",
        type=int,
        default=None,
        help="Max batch size for RunInference (default: handler default of 64)",
    )
    parser.add_argument(
        "--max_batch_size_local_gpu",
        type=int,
        default=None,
        help="Override max batch size for local_gpu only (takes precedence over --max_batch_size)",
    )
    parser.add_argument(
        "--max_batch_size_vertex_ai",
        type=int,
        default=None,
        help="Override max batch size for vertex_ai only (takes precedence over --max_batch_size)",
    )
    parser.add_argument(
        "--min_batch_size",
        type=int,
        default=None,
        help="Min batch size for RunInference — forces Beam to accumulate at least N elements before "
             "calling run_inference(). Default: 1 (process immediately).",
    )
    parser.add_argument(
        "--min_batch_size_local_gpu",
        type=int,
        default=None,
        help="Override min batch size for local_gpu only (takes precedence over --min_batch_size)",
    )
    parser.add_argument(
        "--min_batch_size_vertex_ai",
        type=int,
        default=None,
        help="Override min batch size for vertex_ai only (takes precedence over --min_batch_size)",
    )
    parser.add_argument(
        "--machine_type",
        default=None,
        help="Override machine type from .env for all experiments (e.g. n1-standard-8). "
             "For vertex_ai, also overrides the default n1-standard-4.",
    )
    parser.add_argument(
        "--topic_prefix",
        default="benchmark",
        help="Prefix for Pub/Sub topic and subscription names (default: benchmark). "
             "Use different prefixes to run multiple benchmarks in parallel.",
    )
    parser.add_argument(
        "--env_file",
        default=".env",
        help="Path to .env file (default: .env). Use separate files for different GPU configs.",
    )
    parser.add_argument(
        "--raw_predict",
        action="store_true",
        default=True,
        help="Use :rawPredict instead of :predict for Vertex AI endpoint calls (default: True)",
    )
    parser.add_argument(
        "--no_raw_predict",
        action="store_true",
        help="Use :predict instead of :rawPredict for Vertex AI endpoint calls",
    )
    args = parser.parse_args()

    # --no_raw_predict overrides --raw_predict default
    if args.no_raw_predict:
        args.raw_predict = False

    env = load_env(args.env_file)
    os.makedirs(args.output_dir, exist_ok=True)

    # Reset shared state for parallel job detection
    _claimed_jobs.clear()

    # Build list of experiments to run
    experiments = [
        (mode, label)
        for mode, label in [
            ("local_gpu", "Exp A: Dataflow + Local GPU"),
            ("vertex_ai", "Exp B: Dataflow + Vertex AI"),
        ]
        if mode in args.experiments
    ]

    # all_stats[mode][rate] = stats dict
    all_stats = {}

    def run_and_collect(mode, label):
        """Run one experiment and return (mode, rate_results) tuple."""
        rate_results = run_experiment(mode, label, env, args)
        return mode, rate_results

    # Run experiments in parallel when running both, sequential for single
    if len(experiments) > 1:
        print(f"\nRunning {len(experiments)} experiments in parallel...\n", flush=True)
        threads = []
        thread_results = []
        lock = threading.Lock()

        def thread_target(mode, label):
            result = run_and_collect(mode, label)
            with lock:
                thread_results.append(result)

        for mode, label in experiments:
            t = threading.Thread(target=thread_target, args=(mode, label), daemon=True)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        for mode, rate_results in thread_results:
            all_stats[mode] = {}
            for rate, results in rate_results.items():
                output_file = os.path.join(
                    args.output_dir, f"results_{mode}_{rate}.json"
                )
                with open(output_file, "w") as f:
                    json.dump(results, f, indent=2)
                print(f"  Results saved to {output_file}", flush=True)
                expected = rate * args.duration if args.duration else args.count
                all_stats[mode][rate] = compute_stats(results, expected_count=expected)
    else:
        for mode, label in experiments:
            rate_results = run_experiment(mode, label, env, args)
            all_stats[mode] = {}
            for rate, results in rate_results.items():
                output_file = os.path.join(
                    args.output_dir, f"results_{mode}_{rate}.json"
                )
                with open(output_file, "w") as f:
                    json.dump(results, f, indent=2)
                print(f"  Results saved to {output_file}", flush=True)
                expected = rate * args.duration if args.duration else args.count
                all_stats[mode][rate] = compute_stats(results, expected_count=expected)

    # Final comparison
    if all_stats:
        print_final_comparison(all_stats, args.rates)

        # Save summary JSON
        # Convert int keys to strings for JSON serialization
        json_stats = {}
        for mode, rate_stats in all_stats.items():
            json_stats[mode] = {str(rate): stats for rate, stats in rate_stats.items()}

        summary_file = os.path.join(args.output_dir, "benchmark_results.json")
        with open(summary_file, "w") as f:
            json.dump(json_stats, f, indent=2)
        print(f"Summary saved to {summary_file}", flush=True)

        # Generate charts and report
        print("\nGenerating charts and report...", flush=True)
        generate_charts(all_stats, args.rates, args.output_dir)
        report_count = f"{args.duration}s per phase" if args.duration else f"{args.count:,} per phase"
        generate_report(all_stats, args.rates, report_count, args.output_dir)

    print("\nDone.", flush=True)


if __name__ == "__main__":
    main()
