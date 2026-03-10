"""CLI entry point for the benchmark pipeline."""

import argparse
import logging
from types import SimpleNamespace

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

from benchmark.pipeline import build_pipeline

logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description="GPU Inference Benchmark Pipeline")

    # Mode
    parser.add_argument(
        "--mode",
        required=True,
        choices=["local_gpu", "vertex_ai"],
        help="Inference mode: local_gpu or vertex_ai",
    )

    # Pub/Sub
    parser.add_argument("--input_topic", required=True, help="Input Pub/Sub topic")
    parser.add_argument("--output_topic", required=True, help="Output Pub/Sub topic")

    # Model
    parser.add_argument("--model_path", required=True, help="GCS path to model artifacts")
    parser.add_argument("--num_labels", type=int, default=3, help="Number of classification labels")
    parser.add_argument("--max_seq_length", type=int, default=128, help="Max token sequence length")
    parser.add_argument(
        "--category_names",
        default="INCOME_WAGE,INCOME_GIG,EXPENSE",
        help="Comma-separated category names",
    )

    # Device (for local_gpu mode)
    parser.add_argument(
        "--device",
        default="GPU",
        help="Device for local inference: GPU or CPU",
    )

    # Vertex AI (for vertex_ai mode)
    parser.add_argument("--vertex_endpoint_id", default="", help="Vertex AI endpoint ID")
    parser.add_argument("--vertex_region", default="us-central1", help="Vertex AI region")
    parser.add_argument("--raw_predict", action="store_true",
                        help="Use :rawPredict instead of :predict for Vertex AI calls")
    parser.add_argument("--vertex_endpoint_dns", default="",
                        help="Dedicated endpoint DNS (overrides regional domain)")

    # Batch size (RunInference batching)
    parser.add_argument("--min_batch_size", type=int, default=1,
                        help="Minimum batch size for RunInference (default: 1)")
    parser.add_argument("--max_batch_size", type=int, default=64,
                        help="Maximum batch size for RunInference (default: 64)")

    # Input source (subscription overrides topic for orchestrated benchmarks)
    parser.add_argument(
        "--input_subscription",
        default="",
        help="Input Pub/Sub subscription (full path, overrides --input_topic)",
    )

    return parser.parse_known_args()


def run():
    logging.basicConfig(level=logging.INFO)
    args, pipeline_args = parse_args()

    config = SimpleNamespace(
        mode=args.mode,
        input_topic=args.input_topic,
        input_subscription=args.input_subscription,
        output_topic=args.output_topic,
        model_path=args.model_path,
        num_labels=args.num_labels,
        max_seq_length=args.max_seq_length,
        category_names=args.category_names,
        device=args.device.lower(),
        vertex_endpoint_id=args.vertex_endpoint_id,
        vertex_region=args.vertex_region,
        raw_predict=args.raw_predict,
        vertex_endpoint_dns=args.vertex_endpoint_dns,
        min_batch_size=args.min_batch_size,
        max_batch_size=args.max_batch_size,
        project=None,
    )

    options = PipelineOptions(pipeline_args, streaming=True, save_main_session=True)
    # Extract project from pipeline options for Vertex AI endpoint URL
    all_opts = options.get_all_options()
    config.project = all_opts.get("project", "")

    logger.info("Starting benchmark pipeline: mode=%s", config.mode)

    with beam.Pipeline(options=options) as p:
        build_pipeline(p, config)


if __name__ == "__main__":
    run()
