"""Tear down all GCP resources created for the benchmark."""

import argparse
import subprocess
import sys


def run_cmd(cmd, ignore_errors=True):
    """Run a shell command, optionally ignoring errors."""
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        if ignore_errors:
            print(f"    (skipped: {result.stderr.strip()})")
        else:
            print(f"    ERROR: {result.stderr.strip()}")
            sys.exit(1)
    else:
        print(f"    OK")


def cleanup(project_id, region, input_topic, output_topic, output_subscription,
            vertex_endpoint_id, vertex_model_id):
    print(f"\nCleaning up resources in project {project_id}...\n")

    # Pub/Sub subscriptions
    print("Deleting Pub/Sub subscriptions...")
    # Output subscription
    sub_name = output_subscription.split("/")[-1] if "/" in output_subscription else output_subscription
    run_cmd(["gcloud", "pubsub", "subscriptions", "delete", sub_name,
             "--project", project_id, "--quiet"])

    # Pub/Sub topics
    print("\nDeleting Pub/Sub topics...")
    for topic in [input_topic, output_topic]:
        topic_name = topic.split("/")[-1] if "/" in topic else topic
        run_cmd(["gcloud", "pubsub", "topics", "delete", topic_name,
                 "--project", project_id, "--quiet"])

    # Vertex AI endpoint
    if vertex_endpoint_id:
        print(f"\nUndeploying and deleting Vertex AI endpoint {vertex_endpoint_id}...")
        # Undeploy all models first
        run_cmd([
            "gcloud", "ai", "endpoints", "undeploy-model", vertex_endpoint_id,
            "--project", project_id, "--region", region,
            "--deployed-model-id", "benchmark_model",
            "--quiet",
        ])
        # Delete endpoint
        run_cmd([
            "gcloud", "ai", "endpoints", "delete", vertex_endpoint_id,
            "--project", project_id, "--region", region, "--quiet",
        ])

    # Vertex AI model
    if vertex_model_id:
        print(f"\nDeleting Vertex AI model {vertex_model_id}...")
        run_cmd([
            "gcloud", "ai", "models", "delete", vertex_model_id,
            "--project", project_id, "--region", region, "--quiet",
        ])

    print("\nCleanup complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project_id", required=True)
    parser.add_argument("--region", default="us-central1")
    parser.add_argument("--input_topic", default="benchmark-input")
    parser.add_argument("--output_topic", default="benchmark-output")
    parser.add_argument("--output_subscription", default="benchmark-output-sub")
    parser.add_argument("--vertex_endpoint_id", default="")
    parser.add_argument("--vertex_model_id", default="")
    args = parser.parse_args()

    cleanup(
        args.project_id, args.region,
        args.input_topic, args.output_topic, args.output_subscription,
        args.vertex_endpoint_id, args.vertex_model_id,
    )
