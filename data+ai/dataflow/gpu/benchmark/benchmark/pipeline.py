"""Streaming pipeline: Pub/Sub in -> RunInference -> Pub/Sub out."""

import json
import time

import apache_beam as beam
from apache_beam.ml.inference.base import KeyedModelHandler, RunInference

from benchmark.handlers import LocalGPUHandler, VertexAIHandler


def decode_message(msg):
    """Decode PubsubMessage -> (text, publish_time_ms)."""
    text = msg.data.decode("utf-8").strip()
    publish_time_ms = int(msg.attributes.get("publish_time_ms", 0))
    return (text, publish_time_ms)


def to_kv(element):
    """(text, publish_time_ms) -> ((text, publish_time_ms), text) for KeyedModelHandler."""
    text, publish_time_ms = element
    return ((text, publish_time_ms), text)


class FormatResult(beam.DoFn):
    """Convert (key, PredictionResult) -> PubsubMessage with latency attributes."""

    def __init__(self, config):
        self.category_names = None
        self._category_names_raw = config.category_names

    def setup(self):
        if self._category_names_raw:
            self.category_names = self._category_names_raw.split(",")

    def process(self, element):
        key, prediction = element
        text, publish_time_ms = key
        processed_time_ms = int(time.time() * 1000)
        info = prediction.inference

        class_idx = info["class_idx"]
        if self.category_names and isinstance(class_idx, int):
            predicted_class = self.category_names[class_idx]
        else:
            predicted_class = str(class_idx)

        inference_start_ms = info.get("inference_start_ms", 0)
        # queue_wait: time from publish to inference start (Pub/Sub + Beam queue)
        queue_wait_ms = inference_start_ms - publish_time_ms if inference_start_ms else 0
        # inference_overhead: time from inference start to format complete (tokenize + infer + format)
        inference_overhead_ms = processed_time_ms - inference_start_ms if inference_start_ms else 0

        msg = beam.io.gcp.pubsub.PubsubMessage(
            data=text.encode("utf-8"),
            attributes={
                "predicted_class": predicted_class,
                "confidence": f"{info['confidence']:.4f}",
                "pure_inference_time_ms": f"{info['pure_inference_time_ms']:.2f}",
                "latency_ms": str(processed_time_ms - publish_time_ms),
                "publish_time_ms": str(publish_time_ms),
                "processed_time_ms": str(processed_time_ms),
                "inference_start_ms": str(inference_start_ms),
                "queue_wait_ms": str(queue_wait_ms),
                "inference_overhead_ms": str(inference_overhead_ms),
            },
        )
        yield msg


def build_pipeline(p, config):
    """Pub/Sub in -> RunInference -> Pub/Sub out. Handler selected by config.mode."""

    handler = (
        LocalGPUHandler(config)
        if config.mode == "local_gpu"
        else VertexAIHandler(config)
    )

    if getattr(config, "input_subscription", ""):
        read_source = beam.io.ReadFromPubSub(
            subscription=config.input_subscription, with_attributes=True
        )
    else:
        read_source = beam.io.ReadFromPubSub(
            topic=config.input_topic, with_attributes=True
        )

    (
        p
        | "Read" >> read_source
        | "Decode" >> beam.Map(decode_message)
        | "Filter" >> beam.Filter(lambda x: bool(x[0]))
        | "Key" >> beam.Map(to_kv)
        | "Infer" >> RunInference(KeyedModelHandler(handler))
        | "Format" >> beam.ParDo(FormatResult(config))
        | "Write" >> beam.io.WriteToPubSub(
            topic=config.output_topic, with_attributes=True
        )
    )
