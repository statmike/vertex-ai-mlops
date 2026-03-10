"""Publish transaction messages to Pub/Sub at a controlled rate."""

import argparse
import time

from google.cloud import pubsub_v1


def publish(project_id, topic_id, data_file, rate, max_messages):
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_id)

    with open(data_file, "r") as f:
        lines = [line.strip() for line in f if line.strip()]

    if max_messages:
        lines = lines[:max_messages]

    print(f"Publishing {len(lines)} messages to {topic_path} at {rate} msg/s")
    published = 0
    futures = []
    start_time = time.time()

    for i, text in enumerate(lines):
        publish_time_ms = str(int(time.time() * 1000))
        future = publisher.publish(
            topic_path,
            data=text.encode("utf-8"),
            publish_time_ms=publish_time_ms,
        )
        futures.append(future)
        published += 1

        # Rate limiting
        if rate > 0:
            expected_time = (i + 1) / rate
            elapsed = time.time() - start_time
            if elapsed < expected_time:
                time.sleep(expected_time - elapsed)

        if published % 1000 == 0:
            print(f"  Published {published}/{len(lines)}...")

    # Wait for all publishes to complete
    for future in futures:
        future.result()

    elapsed = time.time() - start_time
    actual_rate = published / elapsed if elapsed > 0 else 0
    print(f"Done. Published {published} messages in {elapsed:.1f}s ({actual_rate:.0f} msg/s)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project_id", required=True)
    parser.add_argument("--topic_id", required=True, help="Topic short name (not full path)")
    parser.add_argument("--data_file", default="data/test_transactions.txt")
    parser.add_argument("--rate", type=int, default=100, help="Messages per second (0=unlimited)")
    parser.add_argument("--max_messages", type=int, default=0, help="Max messages (0=all)")
    args = parser.parse_args()
    publish(args.project_id, args.topic_id, args.data_file, args.rate, args.max_messages)
