"""
Vertex AI Endpoint Scale Testing Utilities

Comprehensive testing infrastructure for analyzing endpoint performance,
autoscaling behavior, and optimal configurations.
"""

import asyncio
import aiohttp
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from google.cloud import monitoring_v3
import plotly.graph_objects as go
from plotly.subplots import make_subplots


async def run_endpoint_test(
    endpoint_url: str,
    credentials,
    auth_req,
    test_data: List,
    num_requests: int,
    batch_size: int = 1,
    pattern: str = "burst",
    target_rps: int = None,
    duration: int = None,
    max_concurrent: int = 100,
    test_name: str = "Load Test"
) -> Dict:
    """
    Universal endpoint testing function supporting multiple load patterns.

    Args:
        endpoint_url: Vertex AI endpoint prediction URL
        credentials: Google Cloud credentials
        auth_req: Auth request object
        test_data: List of instances to send
        num_requests: Total number of requests
        batch_size: Instances per request
        pattern: Load pattern - "burst", "sustained", or "ramp"
        target_rps: Target requests/sec (for sustained/ramp)
        duration: Test duration in seconds (for sustained)
        max_concurrent: Maximum concurrent requests
        test_name: Test identifier for results

    Returns:
        {
            'results_df': DataFrame with per-request metrics,
            'summary': Dict with aggregate metrics,
            'start_time': Test start datetime,
            'end_time': Test end datetime
        }
    """

    # Prepare test instances
    instances = [test_data[0]] * batch_size

    # Auth
    credentials.refresh(auth_req)
    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json"
    }
    payload = {"instances": instances}

    # Results tracking
    results = []
    semaphore = asyncio.Semaphore(max_concurrent)
    start_time = datetime.now()

    async def make_request(session, request_id, scheduled_time=None):
        """Make single request with timing breakdown"""
        queue_start = time.time()

        async with semaphore:
            queue_end = time.time()
            queueing_ms = (queue_end - queue_start) * 1000

            request_start = time.time()
            try:
                async with session.post(
                    endpoint_url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=300)
                ) as response:
                    request_end = time.time()
                    request_ms = (request_end - request_start) * 1000
                    total_ms = (request_end - queue_start) * 1000

                    success = response.status == 200
                    if success:
                        await response.json()

                    return {
                        'timestamp': datetime.fromtimestamp(request_start),
                        'request_id': request_id,
                        'batch_size': batch_size,
                        'queueing_ms': queueing_ms,
                        'request_ms': request_ms,
                        'total_ms': total_ms,
                        'success': success,
                        'status_code': response.status,
                        'scheduled_time': scheduled_time
                    }
            except Exception as e:
                request_end = time.time()
                return {
                    'timestamp': datetime.fromtimestamp(request_start),
                    'request_id': request_id,
                    'batch_size': batch_size,
                    'queueing_ms': queueing_ms,
                    'request_ms': (request_end - request_start) * 1000,
                    'total_ms': (request_end - queue_start) * 1000,
                    'success': False,
                    'status_code': 0,
                    'error': str(e)[:200]
                }

    # Pattern-specific execution
    connector = aiohttp.TCPConnector(limit=max_concurrent)
    async with aiohttp.ClientSession(connector=connector) as session:

        if pattern == "burst":
            # Send all requests ASAP
            print(f"\n{'='*70}")
            print(f"{test_name}")
            print(f"{'='*70}")
            print(f"Pattern: BURST")
            print(f"Requests: {num_requests:,} | Batch: {batch_size} | Concurrency: {max_concurrent}")
            print(f"Total instances: {num_requests * batch_size:,}")
            print(f"\n⏳ Running burst test...")
            print(f"   Expected duration: {(num_requests / max_concurrent) * 0.2:.0f}-{(num_requests / max_concurrent) * 0.5:.0f}s")

            test_start = time.time()
            tasks = [asyncio.create_task(make_request(session, i)) for i in range(num_requests)]
            results = await asyncio.gather(*tasks)
            elapsed = time.time() - test_start

        elif pattern == "sustained":
            # Maintain target RPS for duration
            print(f"\n{'='*70}")
            print(f"{test_name}")
            print(f"{'='*70}")
            print(f"Pattern: SUSTAINED")
            print(f"Target: {target_rps} RPS × {duration}s = {target_rps * duration:,} requests")
            print(f"Batch: {batch_size} | Concurrency: {max_concurrent}")
            print(f"\n⏳ Running sustained load test ({duration}s = {duration//60} mins {duration%60}s)...")
            print(f"   This test will take approximately {duration//60} minutes {duration%60} seconds")
            print(f"   Progress updates every 60 seconds...")

            interval = 1.0 / target_rps
            total_requests = target_rps * duration
            test_start = time.time()
            active_tasks = []
            last_progress = 0

            for i in range(total_requests):
                target_time = test_start + (i * interval)
                wait = target_time - time.time()
                if wait > 0:
                    await asyncio.sleep(wait)

                task = asyncio.create_task(make_request(session, i, target_time))
                active_tasks.append(task)

                # Progress every 60s
                elapsed_time = time.time() - test_start
                if int(elapsed_time) >= last_progress + 60:
                    last_progress = int(elapsed_time)
                    print(f"   [{last_progress:3d}s] {i+1:,} requests sent...")

            # Wait for all tasks to complete
            print(f"   Waiting for all requests to complete...")
            results = await asyncio.gather(*active_tasks)
            elapsed = time.time() - test_start

        elif pattern == "ramp":
            # Gradually increase from 0 to target_rps
            print(f"\n{'='*70}")
            print(f"{test_name}")
            print(f"{'='*70}")
            print(f"Pattern: RAMP")
            print(f"Ramp: 0 → {target_rps} RPS over {duration}s ({duration//60} mins {duration%60}s)")
            print(f"Batch: {batch_size} | Concurrency: {max_concurrent}")
            print(f"\n⏳ Running ramp test...")
            print(f"   This test will take approximately {duration//60} minutes {duration%60} seconds")
            print(f"   RPS will gradually increase from 0 to {target_rps}")
            print(f"   Progress updates every 60 seconds...")

            test_start = time.time()
            request_id = 0
            last_progress = 0

            while time.time() - test_start < duration:
                elapsed_time = time.time() - test_start
                current_rps = (elapsed_time / duration) * target_rps
                interval = 1.0 / max(current_rps, 0.1)  # Avoid division by zero

                task = asyncio.create_task(make_request(session, request_id))
                results.append(await task)
                request_id += 1

                # Progress every 60s
                if int(elapsed_time) >= last_progress + 60:
                    last_progress = int(elapsed_time)
                    print(f"   [{last_progress:3d}s] Current RPS: {current_rps:.1f} | Requests sent: {request_id:,}")

                await asyncio.sleep(interval)

            elapsed = time.time() - test_start

    end_time = datetime.now()

    # Convert to DataFrame
    df = pd.DataFrame(results)
    success_df = df[df['success'] == True]

    # Print summary
    print(f"\n✅ Complete in {elapsed:.1f}s")
    print(f"   Success: {len(success_df):,}/{len(df):,} ({len(success_df)/len(df)*100:.1f}%)")

    if len(success_df) > 0:
        print(f"   Total Latency:  {success_df['total_ms'].mean():.1f}ms (mean) | {success_df['total_ms'].quantile(0.95):.1f}ms (p95)")
        print(f"   Queueing:       {success_df['queueing_ms'].mean():.1f}ms (mean) | {success_df['queueing_ms'].quantile(0.95):.1f}ms (p95)")
        print(f"   Request:        {success_df['request_ms'].mean():.1f}ms (mean) | {success_df['request_ms'].quantile(0.95):.1f}ms (p95)")

        queue_pct = (success_df['queueing_ms'].mean() / success_df['total_ms'].mean() * 100) if success_df['total_ms'].mean() > 0 else 0
        if queue_pct > 50:
            print(f"   ⚠️  Bottleneck: Client-side queueing ({queue_pct:.0f}%)")
        elif queue_pct > 10:
            print(f"   ⚙️  Mixed bottleneck: {queue_pct:.0f}% queueing, {100-queue_pct:.0f}% endpoint")
        else:
            print(f"   ✅ Bottleneck: Endpoint processing ({100-queue_pct:.0f}%)")

    if len(df[df['success'] == False]) > 0:
        print(f"\n   ❌ Failures: {len(df[df['success'] == False]):,}")
        error_codes = df[df['success'] == False]['status_code'].value_counts()
        for code, count in error_codes.head(5).items():
            print(f"      HTTP {code}: {count} requests")

    # Summary metrics
    summary = {
        'test_name': test_name,
        'pattern': pattern,
        'num_requests': len(df),
        'batch_size': batch_size,
        'total_instances': len(df) * batch_size,
        'duration_seconds': elapsed,
        'success_rate': len(success_df) / len(df) if len(df) > 0 else 0,
        'mean_latency_ms': success_df['total_ms'].mean() if len(success_df) > 0 else None,
        'p95_latency_ms': success_df['total_ms'].quantile(0.95) if len(success_df) > 0 else None,
        'mean_queueing_ms': success_df['queueing_ms'].mean() if len(success_df) > 0 else None,
        'bottleneck': 'client' if queue_pct > 50 else 'endpoint' if queue_pct < 10 else 'mixed'
    }

    return {
        'results_df': df,
        'summary': summary,
        'start_time': start_time,
        'end_time': end_time
    }


class EndpointMetricsCollector:
    """
    Collect and analyze Vertex AI Endpoint metrics.

    Collects ALL available metrics:
    - Resource: CPU, Memory, Replicas
    - Performance: Latency, Throughput, Errors
    - Business: Requests/sec, Inferences/sec
    """

    def __init__(self, project_id, endpoint_id, region):
        self.project_id = project_id
        self.endpoint_id = endpoint_id
        self.region = region
        self.monitoring_client = monitoring_v3.MetricServiceClient()
        self.project_name = f"projects/{project_id}"

    def _query_metric(self, metric_type, start_time, end_time, resolution_seconds=10, aligner='ALIGN_MEAN'):
        """Query a single metric from Cloud Monitoring"""
        interval = monitoring_v3.TimeInterval({
            "end_time": {"seconds": int(end_time.timestamp())},
            "start_time": {"seconds": int(start_time.timestamp())}
        })

        # Build filter
        metric_filter = (
            f'resource.type="aiplatform.googleapis.com/Endpoint" AND '
            f'resource.labels.endpoint_id="{self.endpoint_id}" AND '
            f'metric.type="{metric_type}"'
        )

        # Aggregation
        aggregation = monitoring_v3.Aggregation({
            "alignment_period": {"seconds": resolution_seconds},
            "per_series_aligner": getattr(monitoring_v3.Aggregation.Aligner, aligner),
        })

        request = monitoring_v3.ListTimeSeriesRequest({
            "name": self.project_name,
            "filter": metric_filter,
            "interval": interval,
            "aggregation": aggregation,
            "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL
        })

        # Collect data points
        data_points = []
        try:
            for result in self.monitoring_client.list_time_series(request=request):
                for point in result.points:
                    # Extract value based on type
                    if hasattr(point.value, 'int64_value'):
                        value = float(point.value.int64_value)
                    elif hasattr(point.value, 'double_value'):
                        value = point.value.double_value
                    elif hasattr(point.value, 'distribution_value'):
                        # For distribution metrics (like latency), use the mean
                        value = point.value.distribution_value.mean
                    else:
                        continue  # Skip if we can't extract a value

                    data_points.append({
                        'timestamp': pd.Timestamp(point.interval.end_time),
                        'value': value
                    })
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg or "Cannot find metric" in error_msg:
                print(f"⚠️  Warning: Metric not available: {metric_type} (may not be supported for this endpoint)")
            else:
                print(f"⚠️  Warning: Could not fetch {metric_type}: {error_msg[:200]}")

        return pd.DataFrame(data_points).sort_values('timestamp') if data_points else pd.DataFrame(columns=['timestamp', 'value'])

    def collect_metrics(self, start_time, end_time, resolution_seconds=10):
        """
        Collect all metrics for time window.

        Args:
            start_time: datetime (subtract 2 mins for metric lag)
            end_time: datetime (add 2 mins for metric lag)
            resolution_seconds: Aggregation window (10s default)

        Returns:
            dict of DataFrames, one per metric
        """
        # Add buffer for metric propagation
        buffered_start = start_time - timedelta(minutes=2)
        buffered_end = end_time + timedelta(minutes=2)

        print(f"\n🔍 Collecting endpoint metrics...")
        print(f"   Time window: {buffered_start.strftime('%H:%M:%S')} → {buffered_end.strftime('%H:%M:%S')}")
        print(f"   Waiting 90 seconds for metrics to propagate...")
        time.sleep(90)  # Wait for Cloud Monitoring lag

        metrics = {}

        # Resource metrics
        print(f"   Collecting CPU utilization...")
        metrics['cpu'] = self._query_metric(
            'aiplatform.googleapis.com/prediction/online/cpu/utilization',
            buffered_start, buffered_end, resolution_seconds
        )

        print(f"   Collecting memory usage...")
        metrics['memory'] = self._query_metric(
            'aiplatform.googleapis.com/prediction/online/memory/bytes_used',
            buffered_start, buffered_end, resolution_seconds
        )

        print(f"   Collecting replica count...")
        metrics['replicas'] = self._query_metric(
            'aiplatform.googleapis.com/prediction/online/replicas',
            buffered_start, buffered_end, resolution_seconds, aligner='ALIGN_MAX'
        )

        print(f"   Collecting target replica count...")
        metrics['target_replicas'] = self._query_metric(
            'aiplatform.googleapis.com/prediction/online/target_replicas',
            buffered_start, buffered_end, resolution_seconds, aligner='ALIGN_MAX'
        )

        # Request metrics
        print(f"   Collecting prediction count...")
        metrics['predictions'] = self._query_metric(
            'aiplatform.googleapis.com/prediction/online/prediction_count',
            buffered_start, buffered_end, resolution_seconds, aligner='ALIGN_RATE'
        )

        print(f"   Collecting response count...")
        metrics['responses'] = self._query_metric(
            'aiplatform.googleapis.com/prediction/online/response_count',
            buffered_start, buffered_end, resolution_seconds, aligner='ALIGN_RATE'
        )

        print(f"   Collecting prediction latencies...")
        metrics['latency'] = self._query_metric(
            'aiplatform.googleapis.com/prediction/online/prediction_latencies',
            buffered_start, buffered_end, resolution_seconds, aligner='ALIGN_PERCENTILE_95'
        )

        print(f"   Collecting error count...")
        metrics['errors'] = self._query_metric(
            'aiplatform.googleapis.com/prediction/online/error_count',
            buffered_start, buffered_end, resolution_seconds, aligner='ALIGN_RATE'
        )

        print(f"✅ Metrics collection complete")
        for metric_name, df in metrics.items():
            print(f"   {metric_name}: {len(df)} data points")

        return metrics

    def analyze_autoscaling(self, metrics):
        """
        Detect and analyze autoscaling events.

        Returns:
            DataFrame of autoscaling events
        """
        events = []

        if 'replicas' not in metrics or len(metrics['replicas']) == 0:
            return pd.DataFrame(columns=['trigger_time', 'scale_complete_time', 'cpu_at_trigger',
                                        'replicas_before', 'replicas_after', 'scale_up_lag_seconds'])

        replica_df = metrics['replicas'].copy()
        cpu_df = metrics.get('cpu', pd.DataFrame())

        # Find replica count changes
        replica_df['replica_change'] = replica_df['value'].diff()
        replica_changes = replica_df[replica_df['replica_change'] > 0]  # Scale-up events only

        for idx, change in replica_changes.iterrows():
            time_scaled = change['timestamp']
            replicas_after = change['value']
            replicas_before = replica_df[replica_df['timestamp'] < time_scaled].iloc[-1]['value'] if len(replica_df[replica_df['timestamp'] < time_scaled]) > 0 else 1

            # Look back for CPU trigger
            window_start = time_scaled - timedelta(minutes=5)
            cpu_window = cpu_df[
                (cpu_df['timestamp'] >= window_start) &
                (cpu_df['timestamp'] < time_scaled)
            ]

            if len(cpu_window) > 0:
                max_cpu = cpu_window['value'].max()
                trigger_time = cpu_window[cpu_window['value'] == max_cpu].iloc[0]['timestamp']

                events.append({
                    'trigger_time': trigger_time,
                    'scale_complete_time': time_scaled,
                    'cpu_at_trigger': max_cpu * 100,  # Convert to percentage
                    'replicas_before': replicas_before,
                    'replicas_after': replicas_after,
                    'scale_up_lag_seconds': (time_scaled - trigger_time).total_seconds()
                })

        return pd.DataFrame(events)

    def calculate_efficiency_metrics(self, metrics, test_results):
        """
        Calculate efficiency metrics combining endpoint metrics and test results.
        """
        stats = {}

        if 'predictions' in metrics and len(metrics['predictions']) > 0:
            stats['service_throughput_rps'] = metrics['predictions']['value'].mean()

        if 'cpu' in metrics and len(metrics['cpu']) > 0:
            stats['avg_cpu_pct'] = metrics['cpu']['value'].mean() * 100
            stats['max_cpu_pct'] = metrics['cpu']['value'].max() * 100

        if 'memory' in metrics and len(metrics['memory']) > 0:
            stats['avg_memory_pct'] = metrics['memory']['value'].mean() * 100
            stats['max_memory_pct'] = metrics['memory']['value'].max() * 100

        if 'replicas' in metrics and len(metrics['replicas']) > 0:
            stats['avg_replicas'] = metrics['replicas']['value'].mean()
            stats['max_replicas'] = metrics['replicas']['value'].max()

        if 'latency' in metrics and len(metrics['latency']) > 0:
            stats['service_p95_latency_ms'] = metrics['latency']['value'].quantile(0.95)

        # Client-side metrics from test results
        success_df = test_results[test_results['success'] == True]
        if len(success_df) > 0:
            total_instances = success_df['batch_size'].sum()
            test_duration = (success_df['timestamp'].max() - success_df['timestamp'].min()).total_seconds()
            stats['client_throughput_instances_per_sec'] = total_instances / test_duration if test_duration > 0 else 0
            stats['client_p95_latency_ms'] = success_df['total_ms'].quantile(0.95)

        return stats


def plot_timeline_with_metrics(test_results, metrics, test_name="Test"):
    """
    Create comprehensive timeline visualization showing:
    - Request rate (client-side)
    - CPU utilization (service-side)
    - Replica count (autoscaling)
    - Latency (user experience)
    """
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        subplot_titles=(
            'Request Rate (Client Perspective)',
            'CPU Utilization (Service Perspective)',
            'Replica Count (Autoscaling)',
            'P95 Latency (User Experience)'
        ),
        vertical_spacing=0.08
    )

    # Row 1: Request rate from test results
    success_df = test_results[test_results['success'] == True].copy()
    if len(success_df) > 0:
        success_df['time_bucket'] = success_df['timestamp'].dt.floor('10s')
        rps_data = success_df.groupby('time_bucket').size() / 10  # Requests per 10s bucket / 10 = RPS
        fig.add_trace(go.Scatter(
            x=rps_data.index, y=rps_data.values,
            name='Request Rate', mode='lines', line=dict(color='blue', width=2)
        ), row=1, col=1)

    # Row 2: CPU utilization
    if 'cpu' in metrics and len(metrics['cpu']) > 0:
        fig.add_trace(go.Scatter(
            x=metrics['cpu']['timestamp'], y=metrics['cpu']['value'] * 100,
            name='CPU %', mode='lines', line=dict(color='red', width=2)
        ), row=2, col=1)
        fig.add_hline(y=60, line_dash="dash", line_color="orange", row=2, col=1,
                     annotation_text="Autoscale Threshold")

    # Row 3: Replica count
    if 'replicas' in metrics and len(metrics['replicas']) > 0:
        fig.add_trace(go.Scatter(
            x=metrics['replicas']['timestamp'], y=metrics['replicas']['value'],
            name='Actual Replicas', mode='lines+markers', line=dict(color='green', width=2),
            marker=dict(size=8)
        ), row=3, col=1)

    # Add target replicas if available
    if 'target_replicas' in metrics and len(metrics['target_replicas']) > 0:
        fig.add_trace(go.Scatter(
            x=metrics['target_replicas']['timestamp'], y=metrics['target_replicas']['value'],
            name='Target Replicas', mode='lines', line=dict(color='lightgreen', width=2, dash='dash')
        ), row=3, col=1)

    # Row 4: P95 Latency
    if len(success_df) > 0:
        latency_p95 = success_df.groupby('time_bucket')['total_ms'].quantile(0.95)
        fig.add_trace(go.Scatter(
            x=latency_p95.index, y=latency_p95.values,
            name='P95 Latency', mode='lines', line=dict(color='purple', width=2)
        ), row=4, col=1)

    fig.update_xaxes(title_text="Time", row=4, col=1)
    fig.update_yaxes(title_text="RPS", row=1, col=1)
    fig.update_yaxes(title_text="CPU %", row=2, col=1)
    fig.update_yaxes(title_text="Count", row=3, col=1)
    fig.update_yaxes(title_text="ms", row=4, col=1)

    fig.update_layout(height=1000, title_text=f"{test_name} - Complete Timeline Analysis")
    return fig
