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
# Note: EndpointMetricsCollector is imported inside __init__ to use the working implementation


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

        # Import EndpointMetricsCollector from the WORKING implementation
        from scale_testing_utils import EndpointMetricsCollector as WorkingEndpointCollector

        self.endpoint_collector = WorkingEndpointCollector(
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

    # 3. Pipeline Latency Analysis
    if len(latency_df) > 0:
        # Pipeline latency includes all processing (endpoint + Dataflow + windowing)
        mean_pipeline_latency_ms = latency_df['pipeline_latency_ms'].mean()
        p95_pipeline_latency_ms = latency_df['pipeline_latency_ms'].quantile(0.95)

        indicators['mean_pipeline_latency_ms'] = mean_pipeline_latency_ms
        indicators['p95_pipeline_latency_ms'] = p95_pipeline_latency_ms
    else:
        indicators['mean_pipeline_latency_ms'] = 0
        indicators['p95_pipeline_latency_ms'] = 0

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

    # Endpoint service latency is high
    if indicators['endpoint_service_latency_ms'] > 500:
        endpoint_score += 2
        analysis['reason'].append(f"High endpoint service latency ({indicators['endpoint_service_latency_ms']:.1f}ms P95)")

    # Compare endpoint service latency to pipeline latency
    if indicators['endpoint_service_latency_ms'] > 0 and indicators['mean_pipeline_latency_ms'] > 0:
        endpoint_ratio = indicators['endpoint_service_latency_ms'] / indicators['mean_pipeline_latency_ms']
        if endpoint_ratio > 0.5:  # Endpoint accounts for >50% of pipeline latency
            endpoint_score += 3
            analysis['reason'].append(f"Endpoint latency accounts for ~{endpoint_ratio*100:.0f}% of pipeline latency")
        elif endpoint_ratio > 0.3:  # Endpoint accounts for >30% of pipeline latency
            endpoint_score += 1
            analysis['reason'].append(f"Endpoint contributes {endpoint_ratio*100:.0f}% of pipeline latency")

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
    Create comprehensive 7-panel timeline visualization showing both services.

    Panels:
    1. Message Rate (input load)
    2. Dataflow Workers (autoscaling)
    3. Dataflow System Lag
    4. Output Subscription Backlog (messages queued)
    5. Vertex Endpoint Replicas (autoscaling)
    6. Vertex Endpoint CPU %
    7. P95 Pipeline Latency (with breakdown)

    Args:
        combined_metrics: Dict with 'dataflow' and 'endpoint' metrics
        latency_df: DataFrame with pipeline latency measurements
        load_pattern_data: Optional DataFrame with message rate over time
        test_name: Test identifier for title

    Returns:
        Plotly figure with 7 subplots
    """
    dataflow = combined_metrics['dataflow']
    endpoint = combined_metrics['endpoint']

    fig = make_subplots(
        rows=7, cols=1,
        shared_xaxes=True,
        subplot_titles=(
            'Message Rate (Input Load)',
            'Dataflow Workers (Autoscaling)',
            'Dataflow System Lag (Processing Delay: Oldest To Current Message)',
            'Output Subscription Backlog (Messages Queued)',
            'Vertex Endpoint Replicas (Autoscaling)',
            'Vertex Endpoint CPU Utilization',
            'P95 Pipeline Latency (publish → output queue, includes endpoint)'
        ),
        vertical_spacing=0.04
    )

    # Row 1: Message Rate
    if load_pattern_data is not None and len(load_pattern_data) > 0:
        try:
            # Calculate message rate from load pattern data
            load_pattern_data = load_pattern_data.copy()
            load_pattern_data['timestamp'] = pd.to_datetime(load_pattern_data['publish_time'], unit='s')
            load_pattern_data['time_bucket'] = load_pattern_data['timestamp'].dt.floor('10s')
            msg_rate = load_pattern_data.groupby('time_bucket').size() / 10  # messages per second

            fig.add_trace(go.Scatter(
                x=msg_rate.index, y=msg_rate.values,
                name='Message Rate', mode='lines', line=dict(color='blue', width=2)
            ), row=1, col=1)
        except Exception as e:
            print(f"⚠️  Could not plot message rate: {e}")
            # Continue without message rate panel rather than failing entire plot

    # Row 2: Dataflow Workers
    if 'workers' in dataflow and len(dataflow['workers']) > 0:
        fig.add_trace(go.Scatter(
            x=dataflow['workers']['timestamp'], y=dataflow['workers']['value'],
            name='Workers', mode='lines+markers', line=dict(color='green', width=2),
            marker=dict(size=8)
        ), row=2, col=1)

    # Row 3: Dataflow System Lag
    if 'system_lag' in dataflow and len(dataflow['system_lag']) > 0:
        # Convert to milliseconds for consistency
        lag_ms = dataflow['system_lag']['value'] / 1000
        fig.add_trace(go.Scatter(
            x=dataflow['system_lag']['timestamp'], y=lag_ms,
            name='System Lag', mode='lines', line=dict(color='orange', width=2)
        ), row=3, col=1)

    # Row 4: Output Subscription Backlog (NEW PANEL)
    if 'backlog' in dataflow and len(dataflow['backlog']) > 0:
        fig.add_trace(go.Scatter(
            x=dataflow['backlog']['timestamp'], y=dataflow['backlog']['value'],
            name='Backlog', mode='lines', line=dict(color='brown', width=2),
            fill='tozeroy', fillcolor='rgba(165,42,42,0.2)'
        ), row=4, col=1)

    # Row 5: Vertex Endpoint Replicas
    if 'replicas' in endpoint and len(endpoint['replicas']) > 0:
        fig.add_trace(go.Scatter(
            x=endpoint['replicas']['timestamp'], y=endpoint['replicas']['value'],
            name='Replicas', mode='lines+markers', line=dict(color='darkgreen', width=2),
            marker=dict(size=8)
        ), row=5, col=1)

    # Add target replicas if available
    if 'target_replicas' in endpoint and len(endpoint['target_replicas']) > 0:
        fig.add_trace(go.Scatter(
            x=endpoint['target_replicas']['timestamp'], y=endpoint['target_replicas']['value'],
            name='Target Replicas', mode='lines', line=dict(color='lightgreen', width=2, dash='dash')
        ), row=5, col=1)

    # Row 6: Endpoint CPU %
    if 'cpu' in endpoint and len(endpoint['cpu']) > 0:
        fig.add_trace(go.Scatter(
            x=endpoint['cpu']['timestamp'], y=endpoint['cpu']['value'] * 100,
            name='CPU %', mode='lines', line=dict(color='red', width=2)
        ), row=6, col=1)
        # Add autoscaling threshold line
        fig.add_hline(y=60, line_dash="dash", line_color="darkred", row=6, col=1,
                     annotation_text="Autoscale Threshold (60%)")

    # Row 7: P95 Pipeline Latency (FIXED: use publish_time for better timeline)
    if len(latency_df) > 0:
        latency_df = latency_df.copy()

        # Use publish_time (when message sent) instead of receive_time (when pulled)
        # This gives better timeline alignment with test execution
        # Use publish_time for timeline alignment (not receive_time which shows when test pulled messages)
        latency_df['timestamp'] = pd.to_datetime(latency_df['publish_time'], unit='s')

        latency_df['window'] = latency_df['timestamp'].dt.floor('10s')

        # Calculate P95 pipeline latency
        p95_latency = latency_df.groupby('window')['pipeline_latency_ms'].quantile(0.95).reset_index()

        # Pipeline latency (includes all processing: endpoint + Dataflow + windowing)
        fig.add_trace(go.Scatter(
            x=p95_latency['window'], y=p95_latency['pipeline_latency_ms'],
            name='P95 Pipeline Latency', mode='lines', line=dict(color='purple', width=3)
        ), row=7, col=1)

        # Smart Y-axis scaling: Use 99th percentile to ignore outlier spikes
        if len(p95_latency) > 0:
            y_99th = p95_latency['pipeline_latency_ms'].quantile(0.99)
            y_max = y_99th * 1.2  # Add 20% headroom
            fig.update_yaxes(range=[0, y_max], row=7, col=1)

    # Update axes labels
    fig.update_xaxes(title_text="Time", row=7, col=1)
    fig.update_yaxes(title_text="msg/sec", row=1, col=1)
    fig.update_yaxes(title_text="Count", row=2, col=1)
    fig.update_yaxes(title_text="ms", row=3, col=1)
    fig.update_yaxes(title_text="Messages", row=4, col=1)
    fig.update_yaxes(title_text="Count", row=5, col=1)
    fig.update_yaxes(title_text="CPU %", row=6, col=1)
    fig.update_yaxes(title_text="ms", row=7, col=1)

    fig.update_layout(
        height=1600,  # Increased from 1400 for 7 panels
        title_text=f"{test_name} - Combined System Timeline",
        showlegend=True
    )

    return fig


def create_queuing_diagnostic(
    latency_df: pd.DataFrame,
    dataflow_metrics: Optional[Dict] = None,
    endpoint_metrics: Optional[Dict] = None,
    test_name: str = "Combined System Test"
) -> go.Figure:
    """
    Create comprehensive latency diagnostic for Dataflow + Vertex AI Endpoint.

    This diagnostic reveals WHERE latency comes from and WHY autoscaling doesn't respond.

    Key insights revealed:
    - What % of latency is pipeline processing vs test framework overhead
    - How pipeline latency changes over time
    - Whether workers and replicas scaled in response to latency increases
    - Correlation between Dataflow workers and endpoint replicas

    Args:
        latency_df: DataFrame with columns:
            - publish_time: Unix timestamp when message published
            - pipeline_output_time: Unix timestamp when message output from pipeline
            - receive_time: Unix timestamp when test framework pulled message
        dataflow_metrics: Dict with 'workers', 'lag', 'backlog' DataFrames (from collect_combined_metrics)
        endpoint_metrics: Dict with 'cpu', 'replicas' DataFrames (from collect_combined_metrics)
        test_name: Name of test for title

    Returns:
        Plotly figure with 4-panel diagnostic:
        - Panel 1: Pie chart showing latency attribution (pipeline vs test overhead)
        - Panel 2: P95 pipeline latency trends over time
        - Panel 3: Mean and P95 pipeline latency distribution
        - Panel 4: Worker + replica scaling vs pipeline latency (autoscaling correlation)
    """

    # Calculate REAL latency components (not window-based)
    df = latency_df.copy()

    # Pipeline processing = time inside the Dataflow pipeline
    df['pipeline_processing_sec'] = df['pipeline_output_time'] - df['publish_time']

    # Test framework overhead = time sitting in output Pub/Sub before test pulls it
    df['test_overhead_sec'] = df['receive_time'] - df['pipeline_output_time']

    # Total end-to-end
    df['total_e2e_sec'] = df['receive_time'] - df['publish_time']

    # Create timestamps for plotting
    df['publish_datetime'] = pd.to_datetime(df['publish_time'], unit='s')

    # Calculate aggregate statistics
    total_pipeline_time = df['pipeline_processing_sec'].sum()
    total_overhead_time = df['test_overhead_sec'].sum()
    total_e2e_time = df['total_e2e_sec'].sum()

    pipeline_pct = (total_pipeline_time / total_e2e_time) * 100
    overhead_pct = (total_overhead_time / total_e2e_time) * 100

    # Create figure with 4 panels
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            f'Latency Attribution: {pipeline_pct:.1f}% is Pipeline Processing',
            'P95 Pipeline Latency Trends Over Time',
            'Pipeline Latency Distribution: Mean and P95',
            'Autoscaling Response: Workers + Replicas vs Pipeline Latency'
        ),
        specs=[
            [{"type": "pie"}, {"type": "scatter"}],
            [{"type": "scatter"}, {"type": "xy", "secondary_y": True}]
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.15
    )

    # Panel 1: Pie chart showing REAL latency attribution
    pipeline_avg = total_pipeline_time / len(df)
    overhead_avg = total_overhead_time / len(df)

    fig.add_trace(go.Pie(
        labels=[
            f'Pipeline Processing<br>(actual work)<br>avg: {pipeline_avg:.2f}s',
            f'Test Framework Overhead<br>(output queue wait)<br>avg: {overhead_avg:.2f}s'
        ],
        values=[pipeline_pct, overhead_pct],
        marker=dict(colors=['#2E86AB', '#A23B72']),
        textinfo='label+percent',
        textposition='inside',
        hovertemplate='%{label}<br>%{percent}<extra></extra>'
    ), row=1, col=1)

    # Panel 2: P95 pipeline latency trends over time
    df_time = df.copy()
    df_time['time_bucket'] = df_time['publish_datetime'].dt.floor('10s')

    p95_trend = df_time.groupby('time_bucket')['pipeline_processing_sec'].quantile(0.95).reset_index()
    p95_trend.columns = ['time_bucket', 'p95_latency']

    fig.add_trace(go.Scatter(
        x=p95_trend['time_bucket'],
        y=p95_trend['p95_latency'],
        name='P95 Pipeline Latency',
        mode='lines',
        line=dict(color='#2E86AB', width=2),
        fill='tozeroy',
        fillcolor='rgba(46, 134, 171, 0.2)',
        hovertemplate='P95: %{y:.2f}s<extra></extra>'
    ), row=1, col=2)

    # Smart Y-axis limiting for Panel 2
    if len(p95_trend) > 0:
        max_latency = p95_trend['p95_latency'].max()
        p99_latency = p95_trend['p95_latency'].quantile(0.99)

        # If max is more than 3x the p99, cap at p99 * 1.5 to improve readability
        if max_latency > p99_latency * 3:
            y_limit = p99_latency * 1.5
            fig.update_yaxes(range=[0, y_limit], row=1, col=2)

            # Add annotation about clipping
            fig.add_annotation(
                text=f"Y-axis capped at {y_limit:.1f}s (P99×1.5)<br>for readability",
                xref="x2", yref="y2",
                x=p95_trend['time_bucket'].iloc[len(p95_trend)//2],
                y=y_limit * 0.85,
                showarrow=False,
                font=dict(size=10, color="gray"),
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="gray",
                borderwidth=1,
                borderpad=4
            )

    # Panel 3: Pipeline latency distribution (mean and P95)
    df_distribution = df.copy()
    df_distribution['time_bucket'] = pd.cut(
        df_distribution['publish_time'],
        bins=50,
        labels=False
    )

    distribution_data = df_distribution.groupby('time_bucket').agg({
        'pipeline_processing_sec': ['mean', lambda x: x.quantile(0.95)],
        'publish_datetime': 'first'
    }).reset_index()

    distribution_data.columns = ['time_bucket', 'latency_mean', 'latency_p95', 'timestamp']

    fig.add_trace(go.Scatter(
        x=distribution_data['timestamp'],
        y=distribution_data['latency_p95'],
        name='P95 Pipeline Latency',
        mode='lines',
        line=dict(color='#A23B72', width=3),
        fill='tozeroy',
        fillcolor='rgba(162, 59, 114, 0.2)',
        hovertemplate='P95: %{y:.2f}s<extra></extra>'
    ), row=2, col=1)

    fig.add_trace(go.Scatter(
        x=distribution_data['timestamp'],
        y=distribution_data['latency_mean'],
        name='Mean Pipeline Latency',
        mode='lines',
        line=dict(color='#F18F01', width=2),
        hovertemplate='Mean: %{y:.2f}s<extra></extra>'
    ), row=2, col=1)

    # Panel 4: Autoscaling response (workers + replicas vs pipeline latency)
    has_scaling_data = False

    if dataflow_metrics and 'workers' in dataflow_metrics and len(dataflow_metrics['workers']) > 0:
        worker_df = dataflow_metrics['workers'].copy()
        worker_df['timestamp'] = pd.to_datetime(worker_df['timestamp'])

        fig.add_trace(go.Scatter(
            x=worker_df['timestamp'],
            y=worker_df['value'],
            name='Dataflow Workers',
            mode='lines+markers',
            line=dict(color='#2E86AB', width=2),
            marker=dict(size=6),
            yaxis='y3',
            hovertemplate='Workers: %{y}<extra></extra>'
        ), row=2, col=2)
        has_scaling_data = True

    if endpoint_metrics and 'replicas' in endpoint_metrics and len(endpoint_metrics['replicas']) > 0:
        replica_df = endpoint_metrics['replicas'].copy()
        replica_df['timestamp'] = pd.to_datetime(replica_df['timestamp'])

        fig.add_trace(go.Scatter(
            x=replica_df['timestamp'],
            y=replica_df['value'],
            name='Endpoint Replicas',
            mode='lines+markers',
            line=dict(color='#06A77D', width=2),
            marker=dict(size=6),
            yaxis='y3',
            hovertemplate='Replicas: %{y}<extra></extra>'
        ), row=2, col=2)
        has_scaling_data = True

    # Always plot pipeline latency on secondary axis
    fig.add_trace(go.Scatter(
        x=distribution_data['timestamp'],
        y=distribution_data['latency_p95'],
        name='P95 Pipeline Latency',
        mode='lines',
        line=dict(color='#A23B72', width=2),
        yaxis='y4',
        hovertemplate='P95 Latency: %{y:.2f}s<extra></extra>'
    ), row=2, col=2)

    if has_scaling_data:
        fig.update_yaxes(title_text="Workers / Replicas", row=2, col=2, secondary_y=False)
        fig.update_yaxes(title_text="Pipeline Latency (sec)", row=2, col=2, secondary_y=True)
    else:
        fig.add_annotation(
            text="Autoscaling metrics not available",
            xref="x4", yref="y4",
            x=distribution_data['timestamp'].iloc[len(distribution_data)//2],
            y=distribution_data['latency_p95'].max() / 2,
            showarrow=False,
            font=dict(size=14, color="gray"),
            bgcolor="white",
            bordercolor="gray",
            borderwidth=1
        )
        fig.update_yaxes(title_text="Pipeline Latency (sec)", row=2, col=2)

    # Update axes labels
    fig.update_xaxes(title_text="Time", row=1, col=2)
    fig.update_xaxes(title_text="Time", row=2, col=1)
    fig.update_xaxes(title_text="Time", row=2, col=2)
    fig.update_yaxes(title_text="Latency (sec)", row=1, col=2)
    fig.update_yaxes(title_text="Latency (sec)", row=2, col=1)

    fig.update_layout(
        title_text=f"{test_name}: Latency Diagnostic & Autoscaling Analysis",
        showlegend=True,
        height=1000,
        hovermode='x unified'
    )

    return fig


def print_queuing_summary(
    latency_df: pd.DataFrame,
    dataflow_metrics: Optional[Dict] = None,
    endpoint_metrics: Optional[Dict] = None
):
    """
    Print text summary of latency analysis for Dataflow + Vertex AI Endpoint.

    Args:
        latency_df: DataFrame with latency breakdowns
        dataflow_metrics: Optional dict with Dataflow metrics
        endpoint_metrics: Optional dict with endpoint metrics
    """
    df = latency_df.copy()

    # Calculate REAL latency components
    if 'pipeline_processing_sec' not in df.columns:
        df['pipeline_processing_sec'] = df['pipeline_output_time'] - df['publish_time']
    if 'test_overhead_sec' not in df.columns:
        df['test_overhead_sec'] = df['receive_time'] - df['pipeline_output_time']
    if 'total_e2e_sec' not in df.columns:
        df['total_e2e_sec'] = df['receive_time'] - df['publish_time']

    # Statistics
    total_pipeline_time = df['pipeline_processing_sec'].sum()
    total_overhead_time = df['test_overhead_sec'].sum()
    total_e2e_time = df['total_e2e_sec'].sum()

    pipeline_pct = (total_pipeline_time / total_e2e_time) * 100
    overhead_pct = (total_overhead_time / total_e2e_time) * 100

    print("\n" + "="*80)
    print("LATENCY DIAGNOSTIC SUMMARY")
    print("="*80)
    print(f"\nTotal messages analyzed: {len(df):,}")
    print(f"\nLatency Attribution:")
    print(f"  Pipeline processing (actual work): {pipeline_pct:>6.1f}%  ({df['pipeline_processing_sec'].mean():.3f}s avg)")
    print(f"  Test framework overhead:           {overhead_pct:>6.1f}%  ({df['test_overhead_sec'].mean():.3f}s avg)")
    print(f"\nPipeline Processing Statistics:")
    print(f"  Mean:  {df['pipeline_processing_sec'].mean():>8.3f}s")
    print(f"  P50:   {df['pipeline_processing_sec'].quantile(0.50):>8.3f}s")
    print(f"  P95:   {df['pipeline_processing_sec'].quantile(0.95):>8.3f}s")
    print(f"  P99:   {df['pipeline_processing_sec'].quantile(0.99):>8.3f}s")
    print(f"  Max:   {df['pipeline_processing_sec'].max():>8.3f}s")

    # Dataflow worker scaling analysis
    if dataflow_metrics and 'workers' in dataflow_metrics and len(dataflow_metrics['workers']) > 0:
        worker_df = dataflow_metrics['workers']
        print(f"\nDataflow Worker Scaling:")
        print(f"  Min workers: {worker_df['value'].min()}")
        print(f"  Max workers: {worker_df['value'].max()}")
        print(f"  Mean workers: {worker_df['value'].mean():.1f}")

        if worker_df['value'].nunique() == 1:
            print(f"\n  ⚠️  WARNING: Workers never scaled! Stayed at {worker_df['value'].iloc[0]}")
            print(f"      Pipeline latency suffers when workers don't scale to handle load!")

    # Endpoint replica scaling analysis
    if endpoint_metrics and 'replicas' in endpoint_metrics and len(endpoint_metrics['replicas']) > 0:
        replica_df = endpoint_metrics['replicas']
        print(f"\nVertex AI Endpoint Scaling:")
        print(f"  Min replicas: {replica_df['value'].min()}")
        print(f"  Max replicas: {replica_df['value'].max()}")
        print(f"  Mean replicas: {replica_df['value'].mean():.1f}")

        if replica_df['value'].nunique() == 1:
            print(f"\n  ℹ️  Endpoint stayed at {replica_df['value'].iloc[0]} replica(s)")

    print("\n" + "="*80)
    print("KEY FINDINGS")
    print("="*80)
    print(f"✓ {pipeline_pct:.1f}% of end-to-end latency is actual pipeline processing")
    print(f"✓ Only {overhead_pct:.1f}% is test framework overhead (output queue wait)")
    print(f"✓ Focus optimization efforts on pipeline processing, not test framework")

    if dataflow_metrics and 'workers' in dataflow_metrics:
        worker_df = dataflow_metrics['workers']
        if len(worker_df) > 0 and worker_df['value'].nunique() == 1:
            print(f"\n✗ Dataflow workers NEVER SCALED despite autoscaling configuration")
            print(f"✗ This prevents pipeline from handling increased load efficiently")
            print(f"\n💡 RECOMMENDED FIXES:")
            print(f"   1. Use --autoscaling_algorithm=THROUGHPUT_BASED")
            print(f"   2. Set --max_num_workers higher (currently may be capped too low)")
            print(f"   3. Reduce BatchElements max_batch_duration_secs for faster processing")
            print(f"   4. Monitor Dataflow system lag and backlog metrics for scaling signals")

    print("="*80)
