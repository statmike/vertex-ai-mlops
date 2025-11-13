"""
Combined Scale Testing Utilities for Dataflow Streaming + Vertex AI Endpoint

This module provides comprehensive testing infrastructure for analyzing the combined
performance of Dataflow Streaming pipelines that call Vertex AI Endpoints via RunInference.

Key Features:
- Synchronized metrics collection from both Dataflow and Vertex AI
- Bottleneck identification (Dataflow vs Endpoint)
- Worker-to-replica ratio analysis
- Combined timeline visualization
- Cost-efficiency calculations

Usage:
    from scale_testing_combined_utils import CombinedMetricsCollector, identify_bottleneck

    collector = CombinedMetricsCollector(
        project_id=PROJECT_ID,
        dataflow_job_id=JOB_ID,
        endpoint_id=ENDPOINT_ID,
        region=REGION,
        output_subscription=OUTPUT_SUB
    )

    metrics = collector.collect_combined_metrics(start_time, end_time)
    bottleneck = identify_bottleneck(metrics, latency_df)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Import existing collectors (composition over duplication)
from scale_testing_dataflow_utils import DataflowMetricsCollector, PubSubLoadGenerator
from scale_testing_utils import EndpointMetricsCollector


class CombinedMetricsCollector:
    """
    Collect and analyze metrics from both Dataflow Streaming and Vertex AI Endpoint.

    This collector synchronizes metric collection from both services to enable
    bottleneck identification and performance analysis of the combined system.
    """

    def __init__(
        self,
        project_id: str,
        dataflow_job_id: str,
        endpoint_id: str,
        region: str,
        output_subscription: str
    ):
        """
        Initialize combined metrics collector.

        Args:
            project_id: GCP project ID
            dataflow_job_id: Dataflow streaming job ID
            endpoint_id: Vertex AI endpoint ID
            region: GCP region (e.g., 'us-central1')
            output_subscription: Pub/Sub output subscription path
        """
        self.project_id = project_id
        self.dataflow_job_id = dataflow_job_id
        self.endpoint_id = endpoint_id
        self.region = region
        self.output_subscription = output_subscription

        # Initialize individual collectors
        self.dataflow_collector = DataflowMetricsCollector(
            project_id=project_id,
            job_id=dataflow_job_id,
            region=region,
            output_subscription=output_subscription
        )

        self.endpoint_collector = EndpointMetricsCollector(
            project_id=project_id,
            endpoint_id=endpoint_id,
            region=region
        )

    def collect_combined_metrics(
        self,
        start_time: datetime,
        end_time: datetime,
        resolution_seconds: int = 10
    ) -> Dict:
        """
        Collect synchronized metrics from both Dataflow and Vertex AI.

        Args:
            start_time: Start of time window
            end_time: End of time window
            resolution_seconds: Metric aggregation window (default: 10s)

        Returns:
            Dictionary with both 'dataflow' and 'endpoint' metrics
        """
        print(f"\n🔍 Collecting combined metrics...")
        print(f"   Time window: {start_time.strftime('%H:%M:%S')} → {end_time.strftime('%H:%M:%S')}")
        print(f"   Services: Dataflow + Vertex AI Endpoint")

        # Collect from both services (synchronized time window)
        dataflow_metrics = self.dataflow_collector.collect_metrics(
            start_time=start_time,
            end_time=end_time,
            resolution_seconds=resolution_seconds
        )

        endpoint_metrics = self.endpoint_collector.collect_metrics(
            start_time=start_time,
            end_time=end_time,
            resolution_seconds=resolution_seconds
        )

        print(f"\n✅ Combined metrics collected")

        return {
            'dataflow': dataflow_metrics,
            'endpoint': endpoint_metrics
        }


def identify_bottleneck(
    combined_metrics: Dict,
    latency_df: pd.DataFrame
) -> Tuple[str, Dict]:
    """
    Identify which service is the system bottleneck.

    Analysis Strategy (Option A - No Pipeline Instrumentation):
    - Compare Dataflow system lag vs Endpoint CPU utilization
    - Analyze latency components (window wait vs processing)
    - Correlate worker scaling vs endpoint scaling
    - Estimate endpoint contribution from Cloud Monitoring metrics

    Args:
        combined_metrics: Dict with 'dataflow' and 'endpoint' metrics
        latency_df: DataFrame with pipeline latency measurements

    Returns:
        Tuple of (bottleneck_type, analysis_dict)
        bottleneck_type: "dataflow", "endpoint", or "balanced"
        analysis_dict: Detailed reasoning and recommendations
    """
    dataflow = combined_metrics['dataflow']
    endpoint = combined_metrics['endpoint']

    analysis = {
        'bottleneck': None,
        'confidence': None,
        'reason': [],
        'recommendations': []
    }

    # Calculate key indicators
    indicators = {}

    # 1. Dataflow System Lag
    if 'system_lag' in dataflow and len(dataflow['system_lag']) > 0:
        max_lag_ms = dataflow['system_lag']['value'].max()
        mean_lag_ms = dataflow['system_lag']['value'].mean()
        indicators['dataflow_max_lag_ms'] = max_lag_ms
        indicators['dataflow_mean_lag_ms'] = mean_lag_ms
    else:
        indicators['dataflow_max_lag_ms'] = 0
        indicators['dataflow_mean_lag_ms'] = 0

    # 2. Endpoint CPU Utilization
    if 'cpu' in endpoint and len(endpoint['cpu']) > 0:
        max_cpu_pct = endpoint['cpu']['value'].max() * 100
        mean_cpu_pct = endpoint['cpu']['value'].mean() * 100
        indicators['endpoint_max_cpu_pct'] = max_cpu_pct
        indicators['endpoint_mean_cpu_pct'] = mean_cpu_pct
    else:
        indicators['endpoint_max_cpu_pct'] = 0
        indicators['endpoint_mean_cpu_pct'] = 0

    # 3. Latency Breakdown
    if len(latency_df) > 0:
        # Processing time includes endpoint call + Dataflow overhead
        mean_processing_ms = latency_df['processing_ms'].mean()
        mean_window_wait_ms = latency_df['window_wait_ms'].mean()
        mean_pipeline_latency_ms = latency_df['pipeline_latency_ms'].mean()

        # What % of pipeline latency is processing (includes endpoint)?
        processing_pct = (mean_processing_ms / mean_pipeline_latency_ms * 100) if mean_pipeline_latency_ms > 0 else 0

        indicators['mean_processing_ms'] = mean_processing_ms
        indicators['mean_window_wait_ms'] = mean_window_wait_ms
        indicators['processing_pct_of_total'] = processing_pct
    else:
        indicators['mean_processing_ms'] = 0
        indicators['mean_window_wait_ms'] = 0
        indicators['processing_pct_of_total'] = 0

    # 4. Endpoint Service Latency (from Cloud Monitoring)
    if 'latency' in endpoint and len(endpoint['latency']) > 0:
        # This is P95 latency from endpoint's perspective
        endpoint_service_latency_ms = endpoint['latency']['value'].mean()
        indicators['endpoint_service_latency_ms'] = endpoint_service_latency_ms
    else:
        indicators['endpoint_service_latency_ms'] = 0

    # 5. Worker vs Replica Scaling
    if 'workers' in dataflow and len(dataflow['workers']) > 0:
        max_workers = dataflow['workers']['value'].max()
        min_workers = dataflow['workers']['value'].min()
        indicators['worker_range'] = (min_workers, max_workers)
        indicators['workers_scaled'] = max_workers > min_workers
    else:
        indicators['worker_range'] = (0, 0)
        indicators['workers_scaled'] = False

    if 'replicas' in endpoint and len(endpoint['replicas']) > 0:
        max_replicas = endpoint['replicas']['value'].max()
        min_replicas = endpoint['replicas']['value'].min()
        indicators['replica_range'] = (min_replicas, max_replicas)
        indicators['replicas_scaled'] = max_replicas > min_replicas
    else:
        indicators['replica_range'] = (0, 0)
        indicators['replicas_scaled'] = False

    # BOTTLENECK DECISION LOGIC
    # ===========================

    # Strong Dataflow Bottleneck Indicators:
    dataflow_score = 0

    if indicators['dataflow_max_lag_ms'] > 60000:  # > 1 minute lag
        dataflow_score += 3
        analysis['reason'].append(f"High Dataflow system lag ({indicators['dataflow_max_lag_ms']/1000:.1f}s max)")
    elif indicators['dataflow_max_lag_ms'] > 10000:  # > 10 seconds lag
        dataflow_score += 1
        analysis['reason'].append(f"Moderate Dataflow system lag ({indicators['dataflow_max_lag_ms']/1000:.1f}s max)")

    if indicators['workers_scaled'] and indicators['dataflow_max_lag_ms'] > 5000:
        dataflow_score += 2
        analysis['reason'].append("Workers scaled but lag persists (worker capacity issue)")

    # Strong Endpoint Bottleneck Indicators:
    endpoint_score = 0

    if indicators['endpoint_max_cpu_pct'] > 70:
        endpoint_score += 3
        analysis['reason'].append(f"High endpoint CPU ({indicators['endpoint_max_cpu_pct']:.1f}% max)")
    elif indicators['endpoint_max_cpu_pct'] > 50:
        endpoint_score += 1
        analysis['reason'].append(f"Elevated endpoint CPU ({indicators['endpoint_max_cpu_pct']:.1f}% max)")

    # Processing time dominates (likely endpoint since it's in processing phase)
    if indicators['processing_pct_of_total'] > 60:
        endpoint_score += 2
        analysis['reason'].append(f"Processing time dominates latency ({indicators['processing_pct_of_total']:.1f}%)")

    # Endpoint service latency is high
    if indicators['endpoint_service_latency_ms'] > 500:
        endpoint_score += 2
        analysis['reason'].append(f"High endpoint service latency ({indicators['endpoint_service_latency_ms']:.1f}ms P95)")

    # Compare endpoint service latency to processing time
    if indicators['endpoint_service_latency_ms'] > 0 and indicators['mean_processing_ms'] > 0:
        endpoint_ratio = indicators['endpoint_service_latency_ms'] / indicators['mean_processing_ms']
        if endpoint_ratio > 0.8:  # Endpoint accounts for >80% of processing time
            endpoint_score += 3
            analysis['reason'].append(f"Endpoint latency accounts for ~{endpoint_ratio*100:.0f}% of processing time")

    # DECISION
    if endpoint_score > dataflow_score and endpoint_score >= 3:
        analysis['bottleneck'] = 'endpoint'
        analysis['confidence'] = 'high' if endpoint_score >= 5 else 'medium'
        analysis['recommendations'] = [
            "Increase Vertex AI endpoint min_replicas",
            "Use larger machine type for endpoint (e.g., n1-standard-8)",
            "Consider GPU acceleration for model inference",
            "Optimize model for lower inference time",
            "Reduce batch size sent to endpoint (less latency per request)"
        ]

    elif dataflow_score > endpoint_score and dataflow_score >= 3:
        analysis['bottleneck'] = 'dataflow'
        analysis['confidence'] = 'high' if dataflow_score >= 5 else 'medium'
        analysis['recommendations'] = [
            "Increase Dataflow MAX_WORKERS",
            "Use larger machine type for workers (e.g., n1-standard-8)",
            "Reduce window size for lower latency",
            "Optimize DoFn processing logic",
            "Check for backpressure in Pub/Sub"
        ]

    else:
        analysis['bottleneck'] = 'balanced'
        analysis['confidence'] = 'medium'
        analysis['reason'].append("Both services performing proportionally")
        analysis['recommendations'] = [
            "System is well-balanced at current load",
            "Monitor as load increases to identify future bottleneck",
            "Consider scaling both services together for higher throughput"
        ]

    # Store indicators for reference
    analysis['indicators'] = indicators

    return analysis['bottleneck'], analysis


def calculate_worker_replica_ratio(combined_metrics: Dict) -> Dict:
    """
    Calculate optimal worker-to-replica ratio based on observed metrics.

    Args:
        combined_metrics: Dict with 'dataflow' and 'endpoint' metrics

    Returns:
        Dictionary with ratio analysis and recommendations
    """
    dataflow = combined_metrics['dataflow']
    endpoint = combined_metrics['endpoint']

    # Get average worker and replica counts
    avg_workers = dataflow['workers']['value'].mean() if 'workers' in dataflow and len(dataflow['workers']) > 0 else 0
    avg_replicas = endpoint['replicas']['value'].mean() if 'replicas' in endpoint and len(endpoint['replicas']) > 0 else 0

    if avg_workers == 0 or avg_replicas == 0:
        return {
            'ratio': None,
            'recommendation': 'Insufficient data for ratio analysis'
        }

    ratio = avg_workers / avg_replicas

    analysis = {
        'avg_workers': avg_workers,
        'avg_replicas': avg_replicas,
        'ratio': ratio,
        'interpretation': None,
        'recommendation': None
    }

    # Interpret ratio
    if ratio > 10:
        analysis['interpretation'] = f"Many workers ({avg_workers:.1f}) per replica ({avg_replicas:.1f}) - endpoint may be underutilized"
        analysis['recommendation'] = "Consider reducing min_workers or increasing min_replicas"
    elif ratio > 5:
        analysis['interpretation'] = f"Moderate worker-to-replica ratio ({ratio:.1f}:1)"
        analysis['recommendation'] = "Ratio appears balanced for batch-oriented endpoint calls"
    elif ratio > 2:
        analysis['interpretation'] = f"Low worker-to-replica ratio ({ratio:.1f}:1)"
        analysis['recommendation'] = "Good for low-latency, small-batch scenarios"
    else:
        analysis['interpretation'] = f"Very low ratio ({ratio:.1f}:1) - more replicas than workers"
        analysis['recommendation'] = "Endpoint may be over-provisioned; consider reducing min_replicas"

    return analysis


def plot_combined_timeline(
    combined_metrics: Dict,
    latency_df: pd.DataFrame,
    load_pattern_data: pd.DataFrame = None,
    test_name: str = "Combined System Test"
) -> go.Figure:
    """
    Create comprehensive 6-panel timeline visualization showing both services.

    Panels:
    1. Message Rate (input load)
    2. Dataflow Workers (autoscaling)
    3. Dataflow System Lag
    4. Vertex Endpoint Replicas (autoscaling)
    5. Vertex Endpoint CPU %
    6. P95 Pipeline Latency (with breakdown)

    Args:
        combined_metrics: Dict with 'dataflow' and 'endpoint' metrics
        latency_df: DataFrame with pipeline latency measurements
        load_pattern_data: Optional DataFrame with message rate over time
        test_name: Test identifier for title

    Returns:
        Plotly figure with 6 subplots
    """
    dataflow = combined_metrics['dataflow']
    endpoint = combined_metrics['endpoint']

    fig = make_subplots(
        rows=6, cols=1,
        shared_xaxes=True,
        subplot_titles=(
            'Message Rate (Input Load)',
            'Dataflow Workers (Autoscaling)',
            'Dataflow System Lag (Processing Delay)',
            'Vertex Endpoint Replicas (Autoscaling)',
            'Vertex Endpoint CPU Utilization',
            'P95 Pipeline Latency (Breakdown)'
        ),
        vertical_spacing=0.05
    )

    # Row 1: Message Rate
    if load_pattern_data is not None and len(load_pattern_data) > 0:
        # Calculate message rate from load pattern data
        load_pattern_data = load_pattern_data.copy()
        load_pattern_data['timestamp'] = pd.to_datetime(load_pattern_data['publish_time'], unit='s')
        load_pattern_data['time_bucket'] = load_pattern_data['timestamp'].dt.floor('10s')
        msg_rate = load_pattern_data.groupby('time_bucket').size() / 10  # messages per second

        fig.add_trace(go.Scatter(
            x=msg_rate.index, y=msg_rate.values,
            name='Message Rate', mode='lines', line=dict(color='blue', width=2)
        ), row=1, col=1)

    # Row 2: Dataflow Workers
    if 'workers' in dataflow and len(dataflow['workers']) > 0:
        fig.add_trace(go.Scatter(
            x=dataflow['workers']['timestamp'], y=dataflow['workers']['value'],
            name='Workers', mode='lines+markers', line=dict(color='green', width=2),
            marker=dict(size=8)
        ), row=2, col=1)

    # Row 3: Dataflow System Lag
    if 'system_lag' in dataflow and len(dataflow['system_lag']) > 0:
        # Convert to seconds
        lag_seconds = dataflow['system_lag']['value'] / 1000
        fig.add_trace(go.Scatter(
            x=dataflow['system_lag']['timestamp'], y=lag_seconds,
            name='System Lag', mode='lines', line=dict(color='orange', width=2)
        ), row=3, col=1)

    # Row 4: Vertex Endpoint Replicas
    if 'replicas' in endpoint and len(endpoint['replicas']) > 0:
        fig.add_trace(go.Scatter(
            x=endpoint['replicas']['timestamp'], y=endpoint['replicas']['value'],
            name='Replicas', mode='lines+markers', line=dict(color='darkgreen', width=2),
            marker=dict(size=8)
        ), row=4, col=1)

    # Add target replicas if available
    if 'target_replicas' in endpoint and len(endpoint['target_replicas']) > 0:
        fig.add_trace(go.Scatter(
            x=endpoint['target_replicas']['timestamp'], y=endpoint['target_replicas']['value'],
            name='Target Replicas', mode='lines', line=dict(color='lightgreen', width=2, dash='dash')
        ), row=4, col=1)

    # Row 5: Endpoint CPU %
    if 'cpu' in endpoint and len(endpoint['cpu']) > 0:
        fig.add_trace(go.Scatter(
            x=endpoint['cpu']['timestamp'], y=endpoint['cpu']['value'] * 100,
            name='CPU %', mode='lines', line=dict(color='red', width=2)
        ), row=5, col=1)
        # Add autoscaling threshold line
        fig.add_hline(y=60, line_dash="dash", line_color="darkred", row=5, col=1,
                     annotation_text="Autoscale Threshold (60%)")

    # Row 6: P95 Pipeline Latency with Breakdown
    if len(latency_df) > 0:
        latency_df = latency_df.copy()
        latency_df['timestamp'] = pd.to_datetime(latency_df['receive_time'], unit='s')
        latency_df['window'] = latency_df['timestamp'].dt.floor('10s')

        # Calculate P95 for each component
        p95_total = latency_df.groupby('window')['pipeline_latency_ms'].quantile(0.95).reset_index()
        p95_window = latency_df.groupby('window')['window_wait_ms'].quantile(0.95).reset_index()
        p95_processing = latency_df.groupby('window')['processing_ms'].quantile(0.95).reset_index()

        # Total latency
        fig.add_trace(go.Scatter(
            x=p95_total['window'], y=p95_total['pipeline_latency_ms'],
            name='P95 Total Latency', mode='lines', line=dict(color='purple', width=3)
        ), row=6, col=1)

        # Stacked area for breakdown
        fig.add_trace(go.Scatter(
            x=p95_window['window'], y=p95_window['window_wait_ms'],
            name='Window Wait', mode='none', fill='tozeroy',
            fillcolor='rgba(100, 100, 250, 0.3)'
        ), row=6, col=1)

        fig.add_trace(go.Scatter(
            x=p95_processing['window'], y=p95_processing['processing_ms'],
            name='Processing (incl. endpoint)', mode='none', fill='tozeroy',
            fillcolor='rgba(250, 100, 100, 0.3)'
        ), row=6, col=1)

    # Update axes labels
    fig.update_xaxes(title_text="Time", row=6, col=1)
    fig.update_yaxes(title_text="msg/sec", row=1, col=1)
    fig.update_yaxes(title_text="Count", row=2, col=1)
    fig.update_yaxes(title_text="Seconds", row=3, col=1)
    fig.update_yaxes(title_text="Count", row=4, col=1)
    fig.update_yaxes(title_text="CPU %", row=5, col=1)
    fig.update_yaxes(title_text="ms", row=6, col=1)

    fig.update_layout(
        height=1400,
        title_text=f"{test_name} - Combined System Timeline",
        showlegend=True
    )

    return fig
