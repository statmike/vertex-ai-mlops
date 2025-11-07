# Scale Testing Plan: Vertex AI Endpoints and Dataflow Streaming

## Overview

This document outlines a comprehensive plan for testing the latency and scaling characteristics of:
1. **Vertex AI Endpoints** (PyTorch model serving)
2. **Dataflow Streaming Jobs** (RunInference with local models)
3. **Combined Scenario** (Dataflow Streaming calling Vertex AI Endpoints)

The goal is to demonstrate how these services scale under different load patterns, identify bottlenecks, and provide guidance on configuration choices that impact performance.

---

## Notebook Series Structure

### 1. `scale-test-vertex-endpoint.ipynb`
**Focus**: Load testing Vertex AI Endpoints to understand scaling behavior and latency characteristics.

**Objectives**:
- Measure endpoint latency under various load patterns
- Identify when autoscaling triggers and how long new replicas take to come online
- Understand the impact of machine type (n1-standard-4) on throughput and latency
- Demonstrate endpoint behavior during scaling events (cold start lag, warm-up time)

### 2. `scale-test-dataflow-streaming.ipynb`
**Focus**: Load testing Dataflow Streaming jobs with local PyTorch model inference.

**Objectives**:
- Measure end-to-end pipeline latency (Pub/Sub → RunInference → BigQuery/Pub/Sub)
- Identify when Dataflow autoscaling triggers and worker provisioning time
- Measure per-step latency within the pipeline (data ingestion, windowing, inference, output)
- Understand the impact of worker machine type (n1-standard-4) and autoscaling parameters

### 3. `scale-test-combined.ipynb`
**Focus**: Load testing Dataflow Streaming calling Vertex AI Endpoints to identify system bottlenecks.

**Objectives**:
- Measure combined system latency with two scaling layers
- Identify bottlenecks: Is it Dataflow workers or Vertex endpoint capacity?
- Demonstrate how to tune both services together for optimal performance
- Show failure scenarios (endpoint throttling, backpressure handling, retries)

---

## Common Testing Components

### Load Generation Tools

#### Vertex AI Endpoints
- **Tool**: Locust (HTTP-based load testing)
- **Why**: Endpoints are online prediction services accessible via REST API
- **Metrics to Collect**:
  - Request latency (p50, p95, p99)
  - Requests per second (RPS)
  - Error rate
  - Concurrent users/requests

#### Dataflow Streaming (Pub/Sub Input)
- **Tool**: Google Cloud Pub/Sub Python SDK
- **Why**: Simple, familiar, and easy to follow
- **Alternative**: Apache Beam test stream (mention as option)
- **Metrics to Collect**:
  - Messages published per second
  - End-to-end latency (publish → BigQuery)
  - Pub/Sub backlog size
  - Dataflow worker count

### Metrics Collection Strategy

**Collection Method**:
- Export metrics to BigQuery tables during tests
- Timestamp all measurements at **second-level granularity**
- Capture both service metrics (from APIs/SDKs) and application metrics

**Visualization**:
- Post-test analysis using matplotlib/plotly
- Time-series plots showing:
  - Latency over time
  - Throughput over time
  - Scaling events (vertical lines/annotations)
  - Error rates

**Storage Schema** (BigQuery):
```sql
-- Vertex Endpoint Metrics Table
CREATE TABLE scale_test_metrics.vertex_endpoint_results (
  test_run_id STRING,
  timestamp TIMESTAMP,
  request_id STRING,
  latency_ms FLOAT64,
  status_code INT64,
  replica_count INT64,
  load_pattern STRING
);

-- Dataflow Streaming Metrics Table
CREATE TABLE scale_test_metrics.dataflow_streaming_results (
  test_run_id STRING,
  timestamp TIMESTAMP,
  message_id STRING,
  publish_time TIMESTAMP,
  process_time TIMESTAMP,
  end_to_end_latency_ms FLOAT64,
  worker_count INT64,
  backlog_size INT64,
  load_pattern STRING
);

-- Combined Scenario Metrics Table
CREATE TABLE scale_test_metrics.combined_scenario_results (
  test_run_id STRING,
  timestamp TIMESTAMP,
  message_id STRING,
  pubsub_publish_time TIMESTAMP,
  dataflow_receive_time TIMESTAMP,
  endpoint_request_time TIMESTAMP,
  endpoint_response_time TIMESTAMP,
  bigquery_write_time TIMESTAMP,
  total_latency_ms FLOAT64,
  dataflow_worker_count INT64,
  vertex_replica_count INT64,
  load_pattern STRING
);
```

---

## Load Patterns to Test

### 1. Constant Load
- **Description**: Steady request rate for extended period
- **Purpose**: Establish baseline latency and throughput
- **Duration**: 10-15 minutes
- **Example**: 100 RPS for 10 minutes

### 2. Gradual Ramp-Up
- **Description**: Linearly increase load over time
- **Purpose**: Identify autoscaling trigger points and scaling lag
- **Duration**: 20-30 minutes
- **Example**: Start at 10 RPS, increase by 10 RPS every 2 minutes

### 3. Spike Traffic
- **Description**: Sudden surge in traffic
- **Purpose**: Test cold-start behavior and scaling responsiveness
- **Duration**: 5-10 minutes of high load after baseline
- **Example**: 50 RPS baseline → 500 RPS spike → back to 50 RPS

### 4. Sustained High Load
- **Description**: Prolonged high traffic volume
- **Purpose**: Test stability at scale and identify resource limits
- **Duration**: 15-20 minutes
- **Example**: 500-1000 RPS sustained

### 5. Burst Pattern
- **Description**: Periodic bursts of traffic
- **Purpose**: Test autoscaling oscillation and scale-down behavior
- **Duration**: 20-30 minutes
- **Example**: 1 minute at 100 RPS, 2 minutes at 10 RPS, repeat

---

## Key Metrics to Capture

### Vertex AI Endpoint Metrics

#### From Vertex AI SDK (`aiplatform.Endpoint`)
```python
# Endpoint scaling information
endpoint = aiplatform.Endpoint(endpoint_name)
deployed_model = endpoint.list_models()[0]

# Check replica count (requires API calls or Cloud Monitoring)
# This may require using Cloud Monitoring API to get actual replica count over time
```

#### From Cloud Monitoring API
- **Metric**: `aiplatform.googleapis.com/prediction/online/prediction_count`
- **Metric**: `aiplatform.googleapis.com/prediction/online/prediction_latencies`
- **Metric**: `aiplatform.googleapis.com/prediction/online/replica_count`
- **Metric**: `aiplatform.googleapis.com/prediction/online/cpu/utilization`

#### From Locust
- Request latency distribution (p50, p95, p99)
- Requests per second
- Failure rate
- Response time over time

**Console Navigation for Screenshots**:
- **Endpoint Metrics**: `Vertex AI > Online prediction > Endpoints > [endpoint-name] > METRICS tab`
  - [PLACEHOLDER: Screenshot showing prediction count, latency, and replica count graphs]
- **Detailed Monitoring**: `Vertex AI > Online prediction > Endpoints > [endpoint-name] > METRICS tab > View in Cloud Monitoring`
  - [PLACEHOLDER: Screenshot showing custom metrics dashboard with replica scaling events]

### Dataflow Streaming Metrics

#### From Dataflow SDK (if available)
```python
# Note: Dataflow doesn't have a direct Python SDK for runtime metrics
# We'll need to use Cloud Monitoring API or Dataflow REST API
```

#### From Cloud Monitoring API
- **Metric**: `dataflow.googleapis.com/job/system_lag`
- **Metric**: `dataflow.googleapis.com/job/data_watermark_age`
- **Metric**: `dataflow.googleapis.com/job/current_num_vcpus`
- **Metric**: `dataflow.googleapis.com/job/element_count`
- **Metric**: `dataflow.googleapis.com/job/estimated_backlog_bytes`

#### From Dataflow REST API
- Worker count over time
- Per-step execution time
- Backlog size

**Console Navigation for Screenshots**:
- **Job Graph with Latency**: `Dataflow > Jobs > [job-name] > JOB GRAPH tab`
  - [PLACEHOLDER: Screenshot showing pipeline graph with per-step latency metrics]
- **Worker Metrics**: `Dataflow > Jobs > [job-name] > JOB METRICS tab > Autoscaling`
  - [PLACEHOLDER: Screenshot showing worker count over time and autoscaling events]
- **System Lag**: `Dataflow > Jobs > [job-name] > JOB METRICS tab > System Lag`
  - [PLACEHOLDER: Screenshot showing system lag graph during load test]
- **Throughput**: `Dataflow > Jobs > [job-name] > JOB METRICS tab > Throughput`
  - [PLACEHOLDER: Screenshot showing elements/sec processed by pipeline]

### Pub/Sub Metrics

#### From Cloud Monitoring API
- **Metric**: `pubsub.googleapis.com/subscription/backlog_bytes`
- **Metric**: `pubsub.googleapis.com/subscription/num_undelivered_messages`
- **Metric**: `pubsub.googleapis.com/subscription/pull_request_count`
- **Metric**: `pubsub.googleapis.com/topic/send_message_operation_count`

**Console Navigation for Screenshots**:
- **Subscription Metrics**: `Pub/Sub > Subscriptions > [subscription-name] > METRICS tab`
  - [PLACEHOLDER: Screenshot showing backlog size and undelivered messages during load test]

---

## Testing Methodology

### Pre-Test Setup

1. **Deploy Infrastructure**:
   - Run `dataflow-setup.ipynb` to create BigQuery tables and Pub/Sub topics
   - Deploy Vertex AI endpoint (using either pre-built or custom container notebooks)
   - Start Dataflow streaming job (for streaming and combined tests)

2. **Create Metrics Tables**:
   - Execute BigQuery DDL to create test results tables
   - Set up service accounts with appropriate permissions

3. **Baseline Measurements**:
   - Send small number of requests to warm up services
   - Record baseline latency and resource utilization

### During Test Execution

1. **Start Monitoring**:
   - Begin collecting metrics from Cloud Monitoring API
   - Start Locust test (for Vertex endpoint tests)
   - Start Pub/Sub publisher (for Dataflow tests)

2. **Execute Load Pattern**:
   - Follow predefined load pattern schedule
   - Log all requests/messages with timestamps
   - Capture scaling events (when detected)

3. **Continuous Monitoring**:
   - Poll Cloud Monitoring API every 10-30 seconds
   - Write metrics to BigQuery in near real-time
   - Monitor for errors/failures

### Post-Test Analysis

1. **Data Collection**:
   - Query BigQuery for all test run metrics
   - Export Cloud Monitoring data for test time window
   - Combine metrics from multiple sources

2. **Visualization**:
   - Plot latency over time with scaling events annotated
   - Create throughput graphs showing RPS/messages per second
   - Generate latency distribution histograms (p50/p95/p99)
   - Show resource utilization (workers, replicas, CPU)

3. **Analysis**:
   - Identify scaling trigger points (what load triggered autoscaling?)
   - Measure scaling lag (how long until new resources come online?)
   - Calculate steady-state performance (latency/throughput when fully scaled)
   - Identify bottlenecks (which component limits overall performance?)

---

## Notebook 1: `scale-test-vertex-endpoint.ipynb`

### Sections

#### 1. Setup
- Install Locust
- Create BigQuery metrics table
- Initialize Vertex AI SDK
- Get endpoint details (current replica count, machine type)

#### 2. Locust Configuration
```python
from locust import HttpUser, task, between
import json
import time

class VertexEndpointUser(HttpUser):
    wait_time = between(0.1, 0.5)  # Adjust for desired RPS

    def on_start(self):
        # Setup authentication headers
        pass

    @task
    def predict(self):
        payload = {"instances": [[0.1] * 30]}
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        start_time = time.time()
        response = self.client.post(
            f"/v1/projects/{PROJECT_ID}/locations/{REGION}/endpoints/{ENDPOINT_ID}:predict",
            json=payload,
            headers=headers
        )
        latency = (time.time() - start_time) * 1000

        # Log to BigQuery
        log_to_bigquery(latency, response.status_code)
```

#### 3. Monitoring Setup
- Function to poll Cloud Monitoring API for replica count
- Function to write metrics to BigQuery
- Background thread to collect metrics during test

#### 4. Test Execution
- Run each load pattern (constant, ramp-up, spike, sustained, burst)
- Collect metrics throughout
- Annotate scaling events

#### 5. Analysis and Visualization
- Query BigQuery for results
- Plot latency over time with replica count overlay
- Calculate scaling lag (time from load increase to replica increase)
- Show latency distribution before/during/after scaling

**Key Questions to Answer**:
- What latency can we expect at different load levels?
- How long does it take for autoscaling to trigger?
- How long do new replicas take to come online?
- What is the cold-start penalty for new replicas?
- What is the maximum sustainable throughput for n1-standard-4?

**Impact of Machine Type**:
- Brief discussion of how different machine types would change these metrics
- CPU-intensive vs memory-intensive models
- GPU acceleration for larger models

---

## Notebook 2: `scale-test-dataflow-streaming.ipynb`

### Sections

#### 1. Setup
- Create BigQuery metrics tables
- Start Dataflow streaming job (if not already running)
- Initialize Pub/Sub publisher
- Set up Cloud Monitoring API client

#### 2. Load Generator
```python
from google.cloud import pubsub_v1
import json
import time
import uuid

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_NAME)

def publish_message(message_data):
    """Publish message and record timestamp"""
    message_id = str(uuid.uuid4())
    publish_time = time.time()

    message = {
        "message_id": message_id,
        "publish_time": publish_time,
        "features": [0.1] * 30
    }

    future = publisher.publish(
        topic_path,
        json.dumps(message).encode("utf-8")
    )
    future.result()  # Wait for publish confirmation

    return message_id, publish_time

def execute_load_pattern(pattern_name, duration_seconds, messages_per_second):
    """Execute a specific load pattern"""
    start_time = time.time()
    message_count = 0

    while time.time() - start_time < duration_seconds:
        interval_start = time.time()

        # Publish messages for this second
        for _ in range(messages_per_second):
            publish_message({"data": "test"})
            message_count += 1

        # Sleep to maintain desired RPS
        elapsed = time.time() - interval_start
        sleep_time = max(0, 1.0 - elapsed)
        time.sleep(sleep_time)

    return message_count
```

#### 3. Monitoring Setup
- Function to query Dataflow metrics via Cloud Monitoring API
- Function to query BigQuery for processed messages
- Calculate end-to-end latency (publish time → BigQuery write time)

#### 4. Test Execution
- Run each load pattern
- Monitor Dataflow worker count
- Track system lag and backlog size
- Measure per-step latency from Dataflow console

#### 5. Analysis and Visualization
- Query BigQuery for results (join published messages with processed results)
- Plot end-to-end latency over time
- Show worker count changes during load patterns
- Analyze per-step latency (which step is the bottleneck?)
- Calculate processing lag during scaling events

**Key Questions to Answer**:
- What is the baseline end-to-end latency for the pipeline?
- How does latency change during autoscaling events?
- What is the worker provisioning time?
- What is the maximum throughput per worker?
- How does windowing (1-minute windows) impact latency?
- What causes backlog buildup (insufficient workers or slow processing)?

**Impact of Configuration**:
- How would changing MIN_WORKERS/MAX_WORKERS affect scaling behavior?
- Impact of different machine types on per-worker throughput
- Tradeoffs between window size and latency

**Dataflow Metrics Deep Dive**:
- System lag vs data watermark age
- Understanding autoscaling triggers
- Per-step execution time breakdown

**Console Navigation**:
- How to read the job graph for bottleneck identification
- Interpreting autoscaling graphs
- Reading throughput and system lag metrics

---

## Notebook 3: `scale-test-combined.ipynb`

### Sections

#### 1. Setup
- Verify both Vertex endpoint and Dataflow streaming job are running
- Create combined metrics table in BigQuery
- Initialize monitoring for both services

#### 2. Instrumented Pipeline
```python
# We'll need to modify the Dataflow pipeline to log timestamps at each stage
# This might require re-deploying with additional logging

def format_result_with_timestamps(element, window=beam.DoFn.WindowParam):
    """Enhanced format_result that captures timing information"""
    prediction = element[1]

    return {
        "message_id": element[0].get("message_id"),
        "pubsub_publish_time": element[0].get("publish_time"),
        "dataflow_receive_time": time.time(),
        "endpoint_request_time": element.get("endpoint_request_time"),
        "endpoint_response_time": element.get("endpoint_response_time"),
        "anomaly_score": prediction["anomaly_score"],
        "encoded": prediction["encoded"],
        "timestamp": datetime.utcnow().isoformat(),
    }
```

#### 3. Dual Monitoring
- Monitor Dataflow worker count
- Monitor Vertex endpoint replica count
- Track both Pub/Sub backlog and endpoint request queue
- Measure latency at each stage

#### 4. Load Testing Strategy
```python
# Test multiple scenarios to identify bottlenecks

# Scenario 1: Low load - both services idle
execute_combined_test(messages_per_second=10, duration_minutes=5)

# Scenario 2: Dataflow bottleneck - overwhelm workers
execute_combined_test(messages_per_second=500, duration_minutes=10)

# Scenario 3: Endpoint bottleneck - slow endpoint responses
# (This might require temporarily reducing endpoint replicas)

# Scenario 4: Balanced load - both services scale together
execute_combined_test(
    messages_per_second=100,
    ramp_up=True,
    max_messages_per_second=1000,
    duration_minutes=20
)
```

#### 5. Bottleneck Identification
```python
def identify_bottleneck(metrics_df):
    """
    Analyze metrics to determine bottleneck

    Returns:
    - "dataflow": Dataflow workers are the bottleneck
    - "vertex": Vertex endpoint is the bottleneck
    - "balanced": Both services scaling appropriately
    """

    # Calculate component latencies
    dataflow_latency = (
        metrics_df["endpoint_request_time"] -
        metrics_df["dataflow_receive_time"]
    ).mean()

    endpoint_latency = (
        metrics_df["endpoint_response_time"] -
        metrics_df["endpoint_request_time"]
    ).mean()

    # Check for backpressure indicators
    dataflow_backlog = metrics_df["pubsub_backlog_size"].mean()
    endpoint_error_rate = (
        metrics_df["endpoint_status_code"] != 200
    ).mean()

    # Bottleneck logic
    if dataflow_backlog > THRESHOLD and endpoint_error_rate < 0.01:
        return "dataflow", {
            "reason": "Pub/Sub backlog building up",
            "recommendation": "Increase MAX_WORKERS or use larger machine type"
        }
    elif endpoint_error_rate > 0.05:
        return "vertex", {
            "reason": "High endpoint error rate (throttling)",
            "recommendation": "Increase endpoint replica count or use larger machine type"
        }
    elif endpoint_latency > dataflow_latency * 2:
        return "vertex", {
            "reason": "Endpoint latency dominates total latency",
            "recommendation": "Scale endpoint replicas or optimize model inference"
        }
    else:
        return "balanced", {
            "reason": "Both services scaling appropriately",
            "recommendation": "Continue monitoring under sustained load"
        }
```

#### 6. Failure Scenario Testing
```python
# Test 1: Endpoint throttling
# Temporarily reduce endpoint replicas to 1, send high load
# Observe: Dataflow retries, backpressure, error handling

# Test 2: Pub/Sub backpressure
# Send messages faster than pipeline can process
# Observe: Backlog growth, autoscaling response, eventual consistency

# Test 3: Endpoint unavailability
# Simulate endpoint failure by sending invalid requests
# Observe: Error handling, dead letter queue (if implemented), recovery
```

#### 7. Comprehensive Analysis
- Plot latency breakdown (Pub/Sub → Dataflow → Endpoint → BigQuery)
- Show scaling timeline (when did each service scale?)
- Identify correlation between load and scaling
- Calculate cost implications of different configurations

**Key Questions to Answer**:
- Which component is typically the bottleneck?
- How do the two autoscaling systems interact?
- What is the optimal worker-to-replica ratio?
- How should we configure both services for a target SLA?
- What is the total end-to-end latency (p50, p95, p99)?
- How do failures in one component affect the overall system?

**Tuning Recommendations**:
- When to scale Dataflow workers vs Vertex replicas
- Impact of machine type choices on each component
- Balancing cost vs performance
- Setting appropriate MIN/MAX values for both services

**Console Navigation for Combined View**:
- Split-screen approach: Dataflow console + Vertex AI console
- [PLACEHOLDER: Screenshot showing both dashboards side-by-side during load test]
- Using Cloud Monitoring to create custom dashboard with both services
- [PLACEHOLDER: Screenshot of custom dashboard showing Dataflow workers + Vertex replicas on same timeline]

---

## Additional Considerations

### Failure Scenarios and Resilience

#### Vertex AI Endpoint Failures
- **Scenario**: Endpoint returns 429 (throttling) or 503 (overload)
- **Test**: Intentionally overwhelm endpoint to trigger throttling
- **Metrics**: Error rate, retry count, recovery time
- **Observations**: How does Dataflow handle retries? Does backlog build up?

#### Dataflow Worker Failures
- **Scenario**: Worker crashes or becomes unhealthy
- **Test**: Monitor natural failures during sustained load
- **Metrics**: Worker replacement time, impact on throughput
- **Observations**: Does Dataflow automatically replace failed workers?

#### Pub/Sub Backpressure
- **Scenario**: Messages publish faster than consumption
- **Test**: Burst traffic exceeding pipeline capacity
- **Metrics**: Backlog size, message age, scaling response time
- **Observations**: How long does it take to drain backlog after spike?

#### Network Issues
- **Scenario**: Transient network errors between Dataflow and Vertex
- **Test**: May occur naturally; document if observed
- **Metrics**: Request timeout rate, retry success rate
- **Observations**: How does retry logic handle transient failures?

### Cost Considerations

While not the primary focus, each notebook should briefly mention:

#### Vertex AI Endpoint Costs
- Cost per replica-hour (n1-standard-4)
- Trade-off: More replicas = higher cost but lower latency
- Autoscaling helps balance cost and performance

#### Dataflow Costs
- Worker vCPU-hours and memory-hours
- Persistent disk costs
- Trade-off: More workers = higher cost but higher throughput

#### Combined Costs
- Example calculation for typical workload
- Cost implications of different MIN/MAX configurations
- Recommendation: Start conservative, scale based on observed needs

### Machine Type Impact

#### Current Configuration (n1-standard-4)
- **Vertex**: 4 vCPUs, 15 GB memory per replica
- **Dataflow**: 4 vCPUs, 15 GB memory per worker
- Baseline for all tests in this series

#### Alternative Machine Types (Brief Discussion)

**For Vertex AI Endpoints**:
- **n1-standard-2**: Lower cost, lower throughput per replica
- **n1-standard-8**: Higher cost, higher throughput per replica
- **c2-standard-4**: Compute-optimized for CPU-intensive models
- **n1-highmem-4**: Memory-optimized for large models
- **GPU types**: For models requiring GPU acceleration

**For Dataflow Workers**:
- **n1-standard-2**: Lower cost per worker, may need more workers
- **n1-standard-8**: Higher throughput per worker, fewer workers needed
- **c2-standard-4**: Better for CPU-intensive processing
- **Custom machine types**: Fine-tune vCPU/memory ratio

**Impact on Testing**:
- Changing machine types would shift the baseline metrics
- Autoscaling behavior would remain similar but at different thresholds
- Cost-performance tradeoffs would change

---

## Success Criteria

Each notebook should successfully demonstrate:

### Vertex AI Endpoint Tests
✅ Measure latency across multiple load patterns
✅ Capture autoscaling events (replica count changes)
✅ Identify scaling lag (time to provision new replicas)
✅ Show latency distribution at different scales
✅ Document maximum sustainable throughput

### Dataflow Streaming Tests
✅ Measure end-to-end pipeline latency
✅ Capture worker autoscaling events
✅ Identify per-step latency bottlenecks
✅ Show backlog behavior during load spikes
✅ Document worker provisioning time

### Combined Tests
✅ Identify system bottlenecks (Dataflow vs Vertex)
✅ Measure total end-to-end latency
✅ Demonstrate both autoscaling systems working together
✅ Show failure handling and recovery
✅ Provide tuning recommendations based on observations

---

## Timeline and Deliverables

### Phase 1: Infrastructure Setup
- Create BigQuery metrics tables
- Set up Cloud Monitoring API access
- Deploy test infrastructure
- **Deliverable**: Infrastructure ready for testing

### Phase 2: Vertex Endpoint Testing
- Implement `scale-test-vertex-endpoint.ipynb`
- Run all load patterns
- Collect and analyze metrics
- **Deliverable**: Complete notebook with analysis and screenshots

### Phase 3: Dataflow Streaming Testing
- Implement `scale-test-dataflow-streaming.ipynb`
- Run all load patterns
- Collect and analyze metrics
- **Deliverable**: Complete notebook with analysis and screenshots

### Phase 4: Combined Testing
- Implement `scale-test-combined.ipynb`
- Run combined scenarios
- Perform bottleneck analysis
- **Deliverable**: Complete notebook with recommendations

### Phase 5: Documentation
- Add screenshots to all notebooks
- Write summary findings document
- Create recommendations guide
- **Deliverable**: Complete documentation with visual aids

---

## Next Steps

1. **Review this plan** and confirm approach
2. **Set up test infrastructure** (BigQuery tables, monitoring access)
3. **Implement notebooks sequentially** (Vertex → Dataflow → Combined)
4. **Collect screenshots** during test execution
5. **Document findings** and create recommendations

---

## Notes for Implementation

- All tests should be **reproducible** with clear setup instructions
- Code should be **well-commented** to explain testing methodology
- Visualizations should be **clear and informative** (labels, legends, annotations)
- **Error handling** should be robust (tests shouldn't fail due to transient issues)
- **Screenshots** should have arrows/annotations highlighting key information
- Each notebook should **stand alone** but reference others for comprehensive view

---

## Open Questions

- Should we test with real transaction data or synthetic data?
- Do we need to test different model sizes or just the current autoencoder?
- Should we include cost calculators in the notebooks?
- Do we want to test across multiple regions?
- Should we create a automated test suite or manual execution?

---

**Document Status**: Planning Phase
**Last Updated**: 2025-11-07
**Author**: Planning for future implementation
