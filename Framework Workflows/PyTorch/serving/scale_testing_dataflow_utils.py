"""
Dataflow Streaming Scale Testing Utilities

This module provides reusable infrastructure for systematically testing
Dataflow Streaming pipelines with Apache Beam RunInference.

Key Components:
- PubSubLoadGenerator: Generate different load patterns to Pub/Sub topics
- DataflowMetricsCollector: Collect comprehensive metrics from Cloud Monitoring and Pub/Sub
- Visualization functions: Plot timelines and analyze bottlenecks

Usage:
    from dataflow_testing_utils import PubSubLoadGenerator, DataflowMetricsCollector

    # Generate load
    generator = PubSubLoadGenerator(project_id, topic_name)
    results = await generator.run_load_test(
        pattern="sustained",
        target_rate=100,
        duration=300
    )

    # Collect metrics
    collector = DataflowMetricsCollector(project_id, job_id, region)
    metrics = collector.collect_metrics(start_time, end_time)
"""

import asyncio
import time
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

from google.cloud import pubsub_v1, monitoring_v3
from google.api_core import retry
import plotly.graph_objects as go
from plotly.subplots import make_subplots


class PubSubLoadGenerator:
    """
    Generate load patterns to Pub/Sub topics for testing Dataflow pipelines.

    Supports three load patterns:
    - Burst: Send all messages as fast as possible
    - Sustained: Maintain constant message rate over duration
    - Ramp: Gradually increase from 0 to target rate
    """

    def __init__(self, project_id: str, topic_name: str):
        """
        Initialize Pub/Sub load generator.

        Args:
            project_id: GCP project ID
            topic_name: Name of Pub/Sub topic (not full path)
        """
        self.project_id = project_id
        self.topic_name = topic_name
        self.publisher = pubsub_v1.PublisherClient()
        self.topic_path = self.publisher.topic_path(project_id, topic_name)

    async def run_load_test(
        self,
        pattern: str,
        num_messages: int = None,
        target_rate: int = None,
        duration: int = None,
        test_id: str = None,
        test_name: str = "Load Test"
    ) -> Dict:
        """
        Generate messages following specified load pattern.

        Args:
            pattern: "burst", "sustained", or "ramp"
            num_messages: Total messages for burst pattern
            target_rate: Messages/second for sustained/ramp
            duration: Seconds for sustained/ramp patterns
            test_id: Unique identifier for this test run
            test_name: Human-readable test name

        Returns:
            Dict with test results including message IDs and publish times
        """
        if test_id is None:
            test_id = f"{pattern}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        if pattern == "burst":
            return await self._run_burst(num_messages, test_id, test_name)
        elif pattern == "sustained":
            return await self._run_sustained(target_rate, duration, test_id, test_name)
        elif pattern == "ramp":
            return await self._run_ramp(target_rate, duration, test_id, test_name)
        else:
            raise ValueError(f"Unknown pattern: {pattern}. Use 'burst', 'sustained', or 'ramp'")

    async def _run_burst(self, num_messages: int, test_id: str, test_name: str) -> Dict:
        """Send messages as fast as possible."""
        print(f"\n{'='*70}")
        print(f"{test_name}")
        print(f"{'='*70}")
        print(f"Pattern: BURST")
        print(f"Messages: {num_messages:,}")
        print(f"\n⏳ Sending {num_messages:,} messages as fast as possible...")

        start_time = datetime.now()
        message_data = []

        # Prepare all messages
        for i in range(num_messages):
            message_id = str(uuid.uuid4())
            publish_time = time.time()

            message = {
                "message_id": message_id,
                "publish_time": publish_time,
                "features": [0.1] * 30,  # Dummy features for autoencoder
                "test_id": test_id,
                "sequence": i
            }

            # Publish asynchronously
            future = self.publisher.publish(
                self.topic_path,
                json.dumps(message).encode("utf-8")
            )

            message_data.append({
                "message_id": message_id,
                "publish_time": publish_time,
                "sequence": i
            })

            # Progress updates every 1000 messages
            if (i + 1) % 1000 == 0:
                print(f"   Sent {i + 1:,}/{num_messages:,} messages...")

        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()

        print(f"\n✅ Complete in {elapsed:.1f}s")
        print(f"   Rate: {num_messages / elapsed:.1f} messages/sec")

        return {
            "pattern": "burst",
            "test_id": test_id,
            "test_name": test_name,
            "num_messages": num_messages,
            "start_time": start_time,
            "end_time": end_time,
            "elapsed_seconds": elapsed,
            "actual_rate": num_messages / elapsed,
            "message_data": pd.DataFrame(message_data)
        }

    async def _run_sustained(
        self,
        target_rate: int,
        duration: int,
        test_id: str,
        test_name: str
    ) -> Dict:
        """Maintain constant message rate over duration."""
        print(f"\n{'='*70}")
        print(f"{test_name}")
        print(f"{'='*70}")
        print(f"Pattern: SUSTAINED")
        print(f"Target: {target_rate} messages/sec × {duration}s = {target_rate * duration:,} messages")
        print(f"\n⏳ Running sustained load test ({duration}s = {duration//60} mins {duration%60}s)...")
        print(f"   Progress updates every 60 seconds...")

        start_time = datetime.now()
        message_data = []
        last_progress = 0

        interval = 1.0 / target_rate  # Time between messages
        test_start = time.time()

        total_messages = target_rate * duration

        for i in range(total_messages):
            target_time = test_start + (i * interval)
            wait = target_time - time.time()
            if wait > 0:
                await asyncio.sleep(wait)

            message_id = str(uuid.uuid4())
            publish_time = time.time()

            message = {
                "message_id": message_id,
                "publish_time": publish_time,
                "features": [0.1] * 30,
                "test_id": test_id,
                "sequence": i
            }

            # Publish
            self.publisher.publish(
                self.topic_path,
                json.dumps(message).encode("utf-8")
            )

            message_data.append({
                "message_id": message_id,
                "publish_time": publish_time,
                "sequence": i
            })

            # Progress every 60s
            elapsed_time = time.time() - test_start
            if int(elapsed_time) >= last_progress + 60:
                last_progress = int(elapsed_time)
                print(f"   [{last_progress:3d}s] {i+1:,} messages sent...")

        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()

        print(f"\n✅ Complete in {elapsed:.1f}s")
        print(f"   Sent: {total_messages:,} messages")
        print(f"   Rate: {total_messages / elapsed:.1f} messages/sec")

        return {
            "pattern": "sustained",
            "test_id": test_id,
            "test_name": test_name,
            "target_rate": target_rate,
            "duration": duration,
            "num_messages": total_messages,
            "start_time": start_time,
            "end_time": end_time,
            "elapsed_seconds": elapsed,
            "actual_rate": total_messages / elapsed,
            "message_data": pd.DataFrame(message_data)
        }

    async def _run_ramp(
        self,
        target_rate: int,
        duration: int,
        test_id: str,
        test_name: str
    ) -> Dict:
        """Gradually increase rate from 1 msg/sec to target over duration."""
        print(f"\n{'='*70}")
        print(f"{test_name}")
        print(f"{'='*70}")
        print(f"Pattern: RAMP")
        print(f"Ramp: 1 → {target_rate} messages/sec over {duration}s ({duration//60} mins {duration%60}s)")
        print(f"\n⏳ Running ramp test...")
        print(f"   Progress updates every 60 seconds...")

        start_time = datetime.now()
        message_data = []
        last_progress = 0

        test_start = time.time()
        message_count = 0

        while time.time() - test_start < duration:
            elapsed = time.time() - test_start

            # Calculate current rate (linear ramp)
            # Start at 1 msg/sec minimum to avoid extremely long intervals
            current_rate = max(1.0, (elapsed / duration) * target_rate)

            if current_rate > 0:
                interval = 1.0 / current_rate

                message_id = str(uuid.uuid4())
                publish_time = time.time()

                message = {
                    "message_id": message_id,
                    "publish_time": publish_time,
                    "features": [0.1] * 30,
                    "test_id": test_id,
                    "sequence": message_count,
                    "current_rate": current_rate
                }

                # Publish
                self.publisher.publish(
                    self.topic_path,
                    json.dumps(message).encode("utf-8")
                )

                message_data.append({
                    "message_id": message_id,
                    "publish_time": publish_time,
                    "sequence": message_count,
                    "current_rate": current_rate
                })

                message_count += 1

                # Sleep to maintain rate
                await asyncio.sleep(interval)
            else:
                await asyncio.sleep(0.1)

            # Progress every 60s
            if int(elapsed) >= last_progress + 60:
                last_progress = int(elapsed)
                print(f"   [{last_progress:3d}s] Current rate: {current_rate:.1f} msg/sec | Sent: {message_count:,}")

        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()

        print(f"\n✅ Complete in {elapsed:.1f}s")
        print(f"   Sent: {message_count:,} messages")
        print(f"   Avg rate: {message_count / elapsed:.1f} messages/sec")

        return {
            "pattern": "ramp",
            "test_id": test_id,
            "test_name": test_name,
            "target_rate": target_rate,
            "duration": duration,
            "num_messages": message_count,
            "start_time": start_time,
            "end_time": end_time,
            "elapsed_seconds": elapsed,
            "actual_rate": message_count / elapsed,
            "message_data": pd.DataFrame(message_data)
        }


class DataflowMetricsCollector:
    """
    Collect comprehensive metrics for Dataflow Streaming jobs.

    Metrics collected:
    - Worker count (autoscaling)
    - System lag (processing delay)
    - Backlog size (unprocessed messages)
    - Throughput (elements/second)
    - End-to-end latency (from Pub/Sub output)
    """

    def __init__(self, project_id: str, job_id: str, region: str, output_subscription: str):
        """
        Initialize metrics collector.

        Args:
            project_id: GCP project ID
            job_id: Dataflow job ID
            region: GCP region (e.g., 'us-central1')
            output_subscription: Full path to output subscription
        """
        self.project_id = project_id
        self.job_id = job_id
        self.region = region
        self.output_subscription = output_subscription

        self.monitoring_client = monitoring_v3.MetricServiceClient()
        self.subscriber = pubsub_v1.SubscriberClient()

    def collect_metrics(
        self,
        start_time: datetime,
        end_time: datetime,
        resolution_seconds: int = 10
    ) -> Dict:
        """
        Collect all metrics for the specified time window.

        Args:
            start_time: Start of time window
            end_time: End of time window
            resolution_seconds: Metric sampling resolution

        Returns:
            Dict with DataFrames for each metric type
        """
        print(f"\n🔍 Collecting Dataflow metrics...")
        print(f"   Time window: {start_time.strftime('%H:%M:%S')} → {end_time.strftime('%H:%M:%S')}")
        print(f"   Waiting 90 seconds for metrics to propagate...")
        time.sleep(90)

        # Add buffer to time window
        buffered_start = start_time - timedelta(seconds=120)
        buffered_end = end_time + timedelta(seconds=120)

        metrics = {}

        # Worker count (use active_worker_instances for actual worker count, not vCPUs)
        print(f"   Collecting worker count...")
        metrics['workers'] = self._query_dataflow_metric(
            'dataflow.googleapis.com/job/active_worker_instances',
            buffered_start, buffered_end, resolution_seconds, aligner='ALIGN_MAX'
        )

        # System lag
        print(f"   Collecting system lag...")
        metrics['system_lag'] = self._query_dataflow_metric(
            'dataflow.googleapis.com/job/system_lag',
            buffered_start, buffered_end, resolution_seconds
        )

        # Element count (throughput) - per-pcollection metric
        # This is a GAUGE metric - we'll get the sum across all pcollections
        print(f"   Collecting element count...")
        metrics['element_count'] = self._query_dataflow_metric(
            'dataflow.googleapis.com/job/element_count',
            buffered_start, buffered_end, resolution_seconds,
            aligner='ALIGN_MEAN'  # GAUGE metrics need ALIGN_MEAN, ALIGN_MAX, or ALIGN_MIN
        )

        # Pub/Sub backlog
        print(f"   Collecting Pub/Sub backlog...")
        metrics['backlog'] = self._query_pubsub_metric(
            'pubsub.googleapis.com/subscription/num_undelivered_messages',
            buffered_start, buffered_end, resolution_seconds
        )

        print(f"✅ Metrics collection complete")
        for key, df in metrics.items():
            if df is not None and len(df) > 0:
                print(f"   {key}: {len(df)} data points")
            else:
                print(f"   {key}: 0 data points")

        return metrics

    def _query_dataflow_metric(
        self,
        metric_type: str,
        start_time: datetime,
        end_time: datetime,
        resolution_seconds: int,
        aligner: str = 'ALIGN_MEAN'
    ) -> pd.DataFrame:
        """
        Query Dataflow metric from Cloud Monitoring.

        For sparse gauge metrics (active_worker_instances), queries RAW data without aggregation
        to avoid aggregation producing zeros, then resamples in pandas.
        """
        try:
            interval = monitoring_v3.TimeInterval({
                "start_time": {"seconds": int(start_time.timestamp())},
                "end_time": {"seconds": int(end_time.timestamp())}
            })

            # Build filter - job_id is a metric label, not a resource label
            filter_str = (
                f'metric.type="{metric_type}" '
                f'AND resource.type="dataflow_job" '
                f'AND metric.labels.job_id="{self.job_id}"'
            )

            # For sparse gauge metrics, query raw data without aggregation
            # to avoid ALIGN_MAX producing zeros on sparse data
            sparse_gauge_metrics = [
                'dataflow.googleapis.com/job/active_worker_instances'
            ]

            if metric_type in sparse_gauge_metrics:
                # Query raw data points
                request = monitoring_v3.ListTimeSeriesRequest({
                    "name": f"projects/{self.project_id}",
                    "filter": filter_str,
                    "interval": interval,
                })
            else:
                # For other metrics, use aggregation as before
                aggregation = monitoring_v3.Aggregation({
                    "alignment_period": {"seconds": resolution_seconds},
                    "per_series_aligner": getattr(monitoring_v3.Aggregation.Aligner, aligner),
                })

                # Check if this is a per-collection/per-stage metric that needs aggregation
                if 'element_count' in metric_type or 'per_stage' in metric_type:
                    aggregation.cross_series_reducer = monitoring_v3.Aggregation.Reducer.REDUCE_SUM
                    aggregation.group_by_fields = []  # Aggregate all series for this job

                request = monitoring_v3.ListTimeSeriesRequest({
                    "name": f"projects/{self.project_id}",
                    "filter": filter_str,
                    "interval": interval,
                    "aggregation": aggregation,
                })

            data_points = []
            for result in self.monitoring_client.list_time_series(request=request):
                for point in result.points:
                    # For worker count metric, use int64_value first (it's an integer metric)
                    # Check int64_value first because double_value always exists but is 0.0 for int metrics
                    if hasattr(point.value, 'int64_value') and point.value.int64_value is not None and point.value.int64_value > 0:
                        value = point.value.int64_value
                    else:
                        value = point.value.double_value if hasattr(point.value, 'double_value') else 0.0

                    data_points.append({
                        'timestamp': pd.Timestamp(point.interval.end_time),
                        'value': float(value) if value is not None else 0.0
                    })

            if not data_points:
                return pd.DataFrame(columns=['timestamp', 'value'])

            df = pd.DataFrame(data_points).sort_values('timestamp')

            # For sparse gauge metrics, resample in pandas to get consistent time buckets
            # This preserves the actual values instead of aggregating to zero
            if metric_type in sparse_gauge_metrics and len(df) > 0:
                df = df.set_index('timestamp')
                # Forward-fill sparse values (use last known value for gaps)
                df = df.resample(f'{resolution_seconds}s').max().ffill().reset_index()

            return df.reset_index(drop=True)

        except Exception as e:
            print(f"⚠️  Warning: Could not fetch {metric_type}: {str(e)[:200]}")
            return pd.DataFrame(columns=['timestamp', 'value'])

    def _query_pubsub_metric(
        self,
        metric_type: str,
        start_time: datetime,
        end_time: datetime,
        resolution_seconds: int
    ) -> pd.DataFrame:
        """Query Pub/Sub metric from Cloud Monitoring."""
        try:
            # Extract subscription ID from full path
            subscription_id = self.output_subscription.split('/')[-1]

            interval = monitoring_v3.TimeInterval({
                "start_time": {"seconds": int(start_time.timestamp())},
                "end_time": {"seconds": int(end_time.timestamp())}
            })

            aggregation = monitoring_v3.Aggregation({
                "alignment_period": {"seconds": resolution_seconds},
                "per_series_aligner": monitoring_v3.Aggregation.Aligner.ALIGN_MEAN,
            })

            request = monitoring_v3.ListTimeSeriesRequest({
                "name": f"projects/{self.project_id}",
                "filter": f'metric.type="{metric_type}" AND resource.labels.subscription_id="{subscription_id}"',
                "interval": interval,
                "aggregation": aggregation,
            })

            data_points = []
            for result in self.monitoring_client.list_time_series(request=request):
                for point in result.points:
                    value = point.value.double_value if hasattr(point.value, 'double_value') else point.value.int64_value
                    data_points.append({
                        'timestamp': pd.Timestamp(point.interval.end_time),
                        'value': float(value) if value is not None else 0.0
                    })

            if not data_points:
                return pd.DataFrame(columns=['timestamp', 'value'])

            return pd.DataFrame(data_points).sort_values('timestamp').reset_index(drop=True)

        except Exception as e:
            print(f"⚠️  Warning: Could not fetch {metric_type}: {str(e)[:200]}")
            return pd.DataFrame(columns=['timestamp', 'value'])

    def collect_end_to_end_latency(
        self,
        test_id: str,
        expected_messages: int,
        timeout: int = 120
    ) -> pd.DataFrame:
        """
        Collect latency measurements from Pub/Sub output.

        Latency Metrics Explained:
        - pipeline_latency_ms: Time from publish to arriving in output queue (PIPELINE PERFORMANCE)
                               = pipeline_output_time - publish_time
                               This is the ONLY metric that matters for pipeline efficiency.
                               Includes all processing: model inference, transforms, windowing, etc.

        - queue_wait_ms: Time sitting in output subscription before test framework pulls it
                        = receive_time - pipeline_output_time
                        This is NOT pipeline latency - it's test framework overhead.

        - total_e2e_ms: Complete journey including queue wait
                       = receive_time - publish_time
                       = pipeline_latency_ms + queue_wait_ms

        Note: window_start and window_end are included as metadata but are NOT used
              for latency calculation. Windowing time is already included in pipeline_latency_ms.

        Args:
            test_id: Test identifier to filter messages
            expected_messages: Expected number of messages
            timeout: Timeout in seconds

        Returns:
            DataFrame with latency measurements per message
        """
        print(f"\n📊 Collecting end-to-end latency from Pub/Sub output...")
        print(f"   Subscription: {self.output_subscription}")
        print(f"   Test ID: {test_id}")
        print(f"   Expected messages: {expected_messages:,}")

        latencies = []
        messages_collected = 0
        start_collection = time.time()
        consecutive_timeouts = 0
        max_consecutive_timeouts = 5  # Stop after 5 consecutive timeouts

        while messages_collected < expected_messages:
            if time.time() - start_collection > timeout:
                print(f"   ⏱️  Overall timeout reached after {timeout}s")
                print(f"   Collected {messages_collected}/{expected_messages} messages before timeout")
                break

            try:
                response = self.subscriber.pull(
                    request={
                        "subscription": self.output_subscription,
                        "max_messages": 100
                    },
                    timeout=30  # Increased from 10s to 30s to handle windowing delays
                )

                # Reset timeout counter on successful pull
                consecutive_timeouts = 0

                if not response.received_messages:
                    time.sleep(2)  # Sleep longer between empty pulls
                    continue

                for msg in response.received_messages:
                    try:
                        data = json.loads(msg.message.data.decode("utf-8"))

                        # Filter by test_id
                        if data.get("test_id") != test_id:
                            continue

                        receive_time = time.time()

                        # All timestamps are Unix timestamps (float) - no conversion needed
                        latencies.append({
                            "message_id": data["message_id"],
                            "publish_time": data["publish_time"],
                            "window_start": data["window_start"],
                            "window_end": data["window_end"],
                            "pipeline_output_time": data["pipeline_output_time"],
                            "receive_time": receive_time,
                            # PIPELINE PERFORMANCE METRICS
                            # This is the ONLY metric that matters - time from publish to pipeline output
                            "pipeline_latency_ms": (data["pipeline_output_time"] - data["publish_time"]) * 1000,
                            # TEST FRAMEWORK METRICS (includes queue wait time before we pull it)
                            "queue_wait_ms": (receive_time - data["pipeline_output_time"]) * 1000,
                            "total_e2e_ms": (receive_time - data["publish_time"]) * 1000
                        })

                        messages_collected += 1

                    except (json.JSONDecodeError, KeyError) as e:
                        continue

                # Acknowledge messages
                ack_ids = [m.ack_id for m in response.received_messages]
                self.subscriber.acknowledge(
                    request={"subscription": self.output_subscription, "ack_ids": ack_ids}
                )

                if messages_collected % 100 == 0 and messages_collected > 0:
                    elapsed = time.time() - start_collection
                    print(f"   Collected {messages_collected:,}/{expected_messages:,} messages... ({elapsed:.0f}s elapsed)")

            except Exception as e:
                error_str = str(e)
                if "Deadline Exceeded" in error_str or "504" in error_str:
                    consecutive_timeouts += 1
                    if consecutive_timeouts <= max_consecutive_timeouts:
                        # Don't print every timeout, just track them
                        if consecutive_timeouts == 1:
                            print(f"   ⏳ Waiting for messages (window processing delay)...")
                        time.sleep(5)  # Wait longer after timeout
                        continue
                    else:
                        print(f"   ⚠️  Too many consecutive timeouts ({consecutive_timeouts}), stopping collection")
                        break
                else:
                    print(f"   ⚠️  Error pulling messages: {e}")
                    time.sleep(1)

        print(f"✅ Latency collection complete: {messages_collected:,} messages")

        if not latencies:
            return pd.DataFrame(columns=[
                'message_id', 'publish_time', 'window_start', 'window_end',
                'pipeline_output_time', 'receive_time', 'pipeline_latency_ms',
                'queue_wait_ms', 'total_e2e_ms'
            ])

        return pd.DataFrame(latencies)

    def analyze_autoscaling(self, metrics: Dict) -> pd.DataFrame:
        """
        Detect worker autoscaling events.

        Args:
            metrics: Dict with 'workers' DataFrame

        Returns:
            DataFrame with scaling events
        """
        if 'workers' not in metrics or len(metrics['workers']) == 0:
            return pd.DataFrame(columns=[
                'trigger_time', 'scale_complete_time', 'workers_before',
                'workers_after', 'scale_up_lag_seconds'
            ])

        workers_df = metrics['workers'].copy()

        # Detect changes in worker count
        workers_df['worker_change'] = workers_df['value'].diff()

        # Find scale-up events (worker_change > 0)
        scale_events = workers_df[workers_df['worker_change'] > 0].copy()

        if len(scale_events) == 0:
            return pd.DataFrame(columns=[
                'trigger_time', 'scale_complete_time', 'workers_before',
                'workers_after', 'scale_up_lag_seconds'
            ])

        events = []
        for idx, row in scale_events.iterrows():
            # Find previous row
            prev_idx = workers_df.index[workers_df.index < idx].max() if idx > 0 else None

            if prev_idx is not None:
                prev_row = workers_df.loc[prev_idx]

                events.append({
                    'trigger_time': prev_row['timestamp'],
                    'scale_complete_time': row['timestamp'],
                    'workers_before': int(prev_row['value']),
                    'workers_after': int(row['value']),
                    'scale_up_lag_seconds': (row['timestamp'] - prev_row['timestamp']).total_seconds()
                })

        return pd.DataFrame(events)


def plot_dataflow_timeline(
    test_results: Dict,
    metrics: Dict,
    latency_df: pd.DataFrame,
    test_name: str = "Dataflow Load Test"
) -> go.Figure:
    """
    Create comprehensive timeline visualization.

    Args:
        test_results: Publisher results dict
        metrics: Service metrics dict
        latency_df: Latency measurements DataFrame
        test_name: Test name for title

    Returns:
        Plotly figure with 5-row timeline
    """
    fig = make_subplots(
        rows=5, cols=1,
        shared_xaxes=True,
        subplot_titles=(
            'Incoming Message Rate',
            'Worker Count (Autoscaling)',
            'System Lag (Processing Delay: Oldest To Current Message)',
            'Output Subscription Queue',
            'P95 Pipeline Latency (publish → output queue, excludes queue wait)'
        ),
        vertical_spacing=0.06
    )

    # Row 1: Message Rate
    if 'message_data' in test_results and len(test_results['message_data']) > 0:
        try:
            msg_df = test_results['message_data'].copy()
            msg_df['timestamp'] = pd.to_datetime(msg_df['publish_time'], unit='s')

            # Calculate rate (messages per 10-second window)
            msg_df['window'] = msg_df['timestamp'].dt.floor('10s')
            rate = msg_df.groupby('window').size().reset_index(name='count')
            rate['rate'] = rate['count'] / 10  # Convert to messages/sec

            fig.add_trace(go.Scatter(
                x=rate['window'], y=rate['rate'],
                name='Publish Rate', mode='lines', line=dict(color='blue', width=2)
            ), row=1, col=1)
        except Exception as e:
            print(f"⚠️  Could not plot message rate: {e}")
            # Continue without message rate panel rather than failing entire plot

    # Row 2: Worker Count
    if 'workers' in metrics and len(metrics['workers']) > 0:
        fig.add_trace(go.Scatter(
            x=metrics['workers']['timestamp'], y=metrics['workers']['value'],
            name='Workers', mode='lines+markers', line=dict(color='green', width=2),
            marker=dict(size=6)
        ), row=2, col=1)

    # Row 3: System Lag
    if 'system_lag' in metrics and len(metrics['system_lag']) > 0:
        # Convert to milliseconds
        lag_df = metrics['system_lag'].copy()
        lag_df['value_ms'] = lag_df['value'] / 1000  # Convert from microseconds

        fig.add_trace(go.Scatter(
            x=lag_df['timestamp'], y=lag_df['value_ms'],
            name='System Lag', mode='lines', line=dict(color='orange', width=2)
        ), row=3, col=1)

    # Row 4: Backlog
    if 'backlog' in metrics and len(metrics['backlog']) > 0:
        fig.add_trace(go.Scatter(
            x=metrics['backlog']['timestamp'], y=metrics['backlog']['value'],
            name='Backlog', mode='lines', line=dict(color='red', width=2)
        ), row=4, col=1)

    # Row 5: P95 Latency
    if len(latency_df) > 0:
        # Use publish_time for timeline alignment (not receive_time which shows when test pulled messages)
        latency_df['timestamp'] = pd.to_datetime(latency_df['publish_time'], unit='s')
        latency_df['window'] = latency_df['timestamp'].dt.floor('10s')

        # Use pipeline_latency_ms (the actual pipeline performance metric)
        p95_latency = latency_df.groupby('window')['pipeline_latency_ms'].quantile(0.95).reset_index()

        fig.add_trace(go.Scatter(
            x=p95_latency['window'], y=p95_latency['pipeline_latency_ms'],
            name='P95 Pipeline Latency', mode='lines', line=dict(color='purple', width=2)
        ), row=5, col=1)

        # Smart Y-axis scaling: Use 99th percentile to ignore outlier spikes
        # This keeps the axis focused on steady-state latency, not shutdown artifacts
        if len(p95_latency) > 0:
            y_99th = p95_latency['pipeline_latency_ms'].quantile(0.99)
            y_max = y_99th * 1.2  # Add 20% headroom
            fig.update_yaxes(range=[0, y_max], row=5, col=1)

    # Update layout
    fig.update_layout(
        title=test_name,
        height=1200,
        showlegend=True,
        hovermode='x unified'
    )

    # Update y-axis labels
    fig.update_yaxes(title_text="Messages/sec", row=1, col=1)
    fig.update_yaxes(title_text="Workers", row=2, col=1)
    fig.update_yaxes(title_text="Lag (ms)", row=3, col=1)
    fig.update_yaxes(title_text="Messages", row=4, col=1)
    fig.update_yaxes(title_text="Latency (ms)", row=5, col=1)

    fig.update_xaxes(title_text="Time", row=5, col=1)

    return fig


def create_queuing_diagnostic(
    latency_df: pd.DataFrame,
    worker_metrics: Optional[pd.DataFrame] = None,
    test_name: str = "Dataflow Pipeline"
) -> go.Figure:
    """
    Create queuing diagnostic visualization for Dataflow pipelines (local model inference).

    This diagnostic exposes WHERE latency comes from and WHY workers don't scale.

    Key insights revealed:
    - What % of latency is window assignment vs internal queuing
    - How queue depth grows over time
    - Whether workers scaled in response to queuing

    Args:
        latency_df: DataFrame with columns:
            - publish_time: Unix timestamp when message published
            - window_end: Unix timestamp of window boundary (or UNIX_SECONDS(window_end))
            - pipeline_output_time: Unix timestamp when message output
            - sequence: Message sequence number (optional)
        worker_metrics: Optional DataFrame with:
            - timestamp: Datetime
            - value: Worker count
        test_name: Name of test for title

    Returns:
        Plotly figure with 4-panel diagnostic:
        - Panel 1: Pie chart showing latency attribution
        - Panel 2: Stacked area showing components over time
        - Panel 3: Heatmap showing when messages get stuck
        - Panel 4: Worker scaling vs queue depth
    """

    # Calculate latency components
    df = latency_df.copy()

    # Handle different column name conventions
    if 'window_end' not in df.columns:
        if 'window_end_unix' in df.columns:
            df['window_end'] = df['window_end_unix']
        elif 'window_start' in df.columns and 'window_start_unix' not in df.columns:
            # window_end is TIMESTAMP, convert to unix
            df['window_end'] = pd.to_datetime(df['window_end']).astype(int) / 10**9

    df['window_wait_sec'] = df['window_end'] - df['publish_time']
    df['internal_queue_sec'] = df['pipeline_output_time'] - df['window_end']
    df['total_latency_sec'] = df['pipeline_output_time'] - df['publish_time']

    # Create timestamps for plotting
    df['publish_datetime'] = pd.to_datetime(df['publish_time'], unit='s')

    # Calculate aggregate statistics
    total_window_time = df['window_wait_sec'].sum()
    total_queue_time = df['internal_queue_sec'].sum()
    total_latency_time = df['total_latency_sec'].sum()

    window_pct = (total_window_time / total_latency_time) * 100
    queue_pct = (total_queue_time / total_latency_time) * 100

    # Create figure with 4 panels
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            f'Latency Attribution: {queue_pct:.1f}% is Internal Queuing',
            'Latency Components Over Time (Stacked)',
            'Queue Depth Over Time: P95 Shows Worst-Case Delays',
            'Worker Scaling vs Internal Queue Depth'
        ),
        specs=[
            [{"type": "pie"}, {"type": "scatter"}],
            [{"type": "scatter"}, {"type": "xy", "secondary_y": True}]
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.15
    )

    # Panel 1: Pie chart showing attribution with average times for context
    window_avg = total_window_time / len(df)
    queue_avg = total_queue_time / len(df)

    fig.add_trace(go.Pie(
        labels=[
            f'Window Assignment<br>(metadata)<br>avg: {window_avg:.2f}s',
            f'Internal Queue<br>(BOTTLENECK)<br>avg: {queue_avg:.2f}s'
        ],
        values=[window_pct, queue_pct],
        marker=dict(colors=['lightblue', 'red']),
        textinfo='label+percent',
        textposition='inside',
        hovertemplate='%{label}<br>%{percent}<extra></extra>'
    ), row=1, col=1)

    # Panel 2: Stacked area chart over time
    df_time = df.sort_values('publish_datetime')
    sample_interval = max(1, len(df_time) // 500)  # Max 500 points
    df_sampled = df_time[::sample_interval]

    fig.add_trace(go.Scatter(
        x=df_sampled['publish_datetime'],
        y=df_sampled['window_wait_sec'],
        name='Window (metadata)',
        mode='none',
        stackgroup='one',
        fillcolor='lightblue',
        hovertemplate='Window: %{y:.2f}s<extra></extra>'
    ), row=1, col=2)

    fig.add_trace(go.Scatter(
        x=df_sampled['publish_datetime'],
        y=df_sampled['internal_queue_sec'],
        name='Internal Queue',
        mode='none',
        stackgroup='one',
        fillcolor='red',
        hovertemplate='Queue: %{y:.2f}s<extra></extra>'
    ), row=1, col=2)

    # Smart Y-axis limiting for Panel 2 to handle extreme queue times
    if len(df_sampled) > 0:
        max_total = (df_sampled['window_wait_sec'] + df_sampled['internal_queue_sec']).max()
        p99_total = (df_sampled['window_wait_sec'] + df_sampled['internal_queue_sec']).quantile(0.99)

        # If max is more than 3x the p99, cap at p99 * 1.5 to improve readability
        if max_total > p99_total * 3:
            y_limit = p99_total * 1.5
            fig.update_yaxes(range=[0, y_limit], row=1, col=2)

            # Add annotation about clipping
            fig.add_annotation(
                text=f"Y-axis capped at {y_limit:.1f}s (P99×1.5)<br>for readability",
                xref="x2", yref="y2",
                x=df_sampled['publish_datetime'].iloc[len(df_sampled)//2],
                y=y_limit * 0.85,
                showarrow=False,
                font=dict(size=10, color="gray"),
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="gray",
                borderwidth=1,
                borderpad=4
            )

    # Panel 3: Queue depth over time
    df_heatmap = df.copy()
    df_heatmap['time_bucket'] = pd.cut(
        df_heatmap['publish_time'],
        bins=50,
        labels=False
    )

    heatmap_data = df_heatmap.groupby('time_bucket').agg({
        'internal_queue_sec': ['mean', lambda x: x.quantile(0.50), lambda x: x.quantile(0.95)],
        'publish_datetime': 'first'
    }).reset_index()

    heatmap_data.columns = ['time_bucket', 'queue_mean', 'queue_p50', 'queue_p95', 'timestamp']

    fig.add_trace(go.Scatter(
        x=heatmap_data['timestamp'],
        y=heatmap_data['queue_p95'],
        name='P95 Queue Time',
        mode='lines',
        line=dict(color='darkred', width=3),
        fill='tozeroy',
        fillcolor='rgba(255,0,0,0.3)',
        hovertemplate='P95 Queue: %{y:.2f}s<extra></extra>'
    ), row=2, col=1)

    fig.add_trace(go.Scatter(
        x=heatmap_data['timestamp'],
        y=heatmap_data['queue_mean'],
        name='Mean Queue Time',
        mode='lines',
        line=dict(color='orange', width=2),
        hovertemplate='Mean Queue: %{y:.2f}s<extra></extra>'
    ), row=2, col=1)

    # Panel 4: Worker scaling vs queue depth
    if worker_metrics is not None and len(worker_metrics) > 0:
        worker_df = worker_metrics.copy()
        worker_df['timestamp'] = pd.to_datetime(worker_df['timestamp'])

        # Plot worker count on primary y-axis
        fig.add_trace(go.Scatter(
            x=worker_df['timestamp'],
            y=worker_df['value'],
            name='Worker Count',
            mode='lines+markers',
            line=dict(color='blue', width=3),
            marker=dict(size=8),
            yaxis='y3',
            hovertemplate='Workers: %{y}<extra></extra>'
        ), row=2, col=2)

        # Plot queue depth on secondary y-axis
        fig.add_trace(go.Scatter(
            x=heatmap_data['timestamp'],
            y=heatmap_data['queue_p95'],
            name='P95 Queue Depth',
            mode='lines',
            line=dict(color='red', width=2),
            yaxis='y4',
            hovertemplate='Queue: %{y:.2f}s<extra></extra>'
        ), row=2, col=2)

        # Configure secondary y-axis
        fig.update_yaxes(title_text="Worker Count", row=2, col=2, secondary_y=False)
        fig.update_yaxes(title_text="Queue Depth (sec)", row=2, col=2, secondary_y=True)

    else:
        # No worker metrics - just show queue depth
        fig.add_trace(go.Scatter(
            x=heatmap_data['timestamp'],
            y=heatmap_data['queue_p95'],
            name='P95 Queue Depth',
            mode='lines',
            line=dict(color='red', width=3),
            fill='tozeroy',
            hovertemplate='Queue: %{y:.2f}s<extra></extra>'
        ), row=2, col=2)

        # Add annotation about missing worker data
        fig.add_annotation(
            text="Worker metrics not available<br>Cannot show autoscaling correlation",
            xref="x4", yref="y4",
            x=heatmap_data['timestamp'].iloc[len(heatmap_data)//2],
            y=heatmap_data['queue_p95'].max() / 2,
            showarrow=False,
            font=dict(size=14, color="gray"),
            bgcolor="white",
            bordercolor="gray",
            borderwidth=1
        )
        fig.update_yaxes(title_text="Queue Depth (sec)", row=2, col=2)

    # Update axes labels
    fig.update_xaxes(title_text="Time", row=1, col=2)
    fig.update_xaxes(title_text="Time", row=2, col=1)
    fig.update_xaxes(title_text="Time", row=2, col=2)
    fig.update_yaxes(title_text="Latency (sec)", row=1, col=2)
    fig.update_yaxes(title_text="Queue Depth (sec)", row=2, col=1)

    fig.update_layout(
        title_text=f"{test_name}: Queuing Diagnostic",
        showlegend=True,
        height=1000,
        hovermode='x unified'
    )

    return fig


def print_queuing_summary(
    latency_df: pd.DataFrame,
    worker_metrics: Optional[pd.DataFrame] = None
):
    """
    Print text summary of queuing analysis for Dataflow pipelines.

    Args:
        latency_df: DataFrame with latency breakdowns
        worker_metrics: Optional worker count data
    """
    df = latency_df.copy()

    # Calculate components
    if 'window_end' not in df.columns:
        if 'window_end_unix' in df.columns:
            df['window_end'] = df['window_end_unix']
        elif 'window_start' in df.columns:
            df['window_end'] = pd.to_datetime(df['window_end']).astype(int) / 10**9

    if 'window_wait_sec' not in df.columns:
        df['window_wait_sec'] = df['window_end'] - df['publish_time']
    if 'internal_queue_sec' not in df.columns:
        df['internal_queue_sec'] = df['pipeline_output_time'] - df['window_end']
    if 'total_latency_sec' not in df.columns:
        df['total_latency_sec'] = df['pipeline_output_time'] - df['publish_time']

    # Statistics
    total_window_time = df['window_wait_sec'].sum()
    total_queue_time = df['internal_queue_sec'].sum()
    total_latency_time = df['total_latency_sec'].sum()

    window_pct = (total_window_time / total_latency_time) * 100
    queue_pct = (total_queue_time / total_latency_time) * 100

    print("\n" + "="*80)
    print("QUEUING DIAGNOSTIC SUMMARY")
    print("="*80)
    print(f"\nTotal messages analyzed: {len(df):,}")
    print(f"\nLatency Attribution:")
    print(f"  Window assignment (metadata): {window_pct:>6.1f}%  ({df['window_wait_sec'].mean():.3f}s avg)")
    print(f"  Internal queue (bottleneck):  {queue_pct:>6.1f}%  ({df['internal_queue_sec'].mean():.3f}s avg)")
    print(f"\nInternal Queue Statistics:")
    print(f"  Mean:  {df['internal_queue_sec'].mean():>8.3f}s")
    print(f"  P50:   {df['internal_queue_sec'].quantile(0.50):>8.3f}s")
    print(f"  P95:   {df['internal_queue_sec'].quantile(0.95):>8.3f}s")
    print(f"  P99:   {df['internal_queue_sec'].quantile(0.99):>8.3f}s")
    print(f"  Max:   {df['internal_queue_sec'].max():>8.3f}s")

    if worker_metrics is not None and len(worker_metrics) > 0:
        print(f"\nWorker Scaling:")
        print(f"  Min workers: {worker_metrics['value'].min()}")
        print(f"  Max workers: {worker_metrics['value'].max()}")
        print(f"  Mean workers: {worker_metrics['value'].mean():.1f}")

        if worker_metrics['value'].nunique() == 1:
            print(f"\n  ⚠️  WARNING: Workers never scaled! Stayed at {worker_metrics['value'].iloc[0]}")
            print(f"      This explains the {queue_pct:.1f}% internal queuing!")

    print("\n" + "="*80)
    print("KEY FINDINGS")
    print("="*80)
    print(f"✓ {queue_pct:.1f}% of latency is from INTERNAL QUEUING")
    print(f"✓ Only {window_pct:.1f}% is from window assignment (metadata)")
    print(f"✓ Window configuration is NOT the bottleneck")

    if worker_metrics is not None and len(worker_metrics) > 0 and worker_metrics['value'].nunique() == 1:
        print(f"\n✗ Workers NEVER SCALED despite autoscaling configuration")
        print(f"✗ This is why messages queue internally instead of being processed")
        print(f"\n💡 RECOMMENDED FIXES:")
        print(f"   1. Use --autoscaling_algorithm=THROUGHPUT_BASED")
        print(f"   2. Set --target_worker_utilization=0.7 (scale at 70% capacity)")
        print(f"   3. Verify --num_workers sets INITIAL workers (may need explicit start count)")
        print(f"   4. Reduce max_batch_duration_secs to reduce internal buffering")

    print("="*80)
