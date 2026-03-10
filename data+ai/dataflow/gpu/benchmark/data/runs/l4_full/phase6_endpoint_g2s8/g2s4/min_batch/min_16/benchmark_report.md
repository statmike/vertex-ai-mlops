# Benchmark Report

Generated: 2026-03-09 17:17:35

## Configuration

| Parameter | Value |
|---|---|
| Messages per phase | 100s per phase |
| Rates (msg/s) | 75, 100, 125 |
| Experiments | Vertex AI |

## Throughput

| Rate (msg/s) | Vertex AI |
|---|---|
| 75 | 75.0 |
| 100 | 100.0 |
| 125 | 124.9 |

## End-to-End Latency (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 57.0 |
| 75 | p95 | 83.0 |
| 75 | p99 | 616.1 |
| 100 | p50 | 64.0 |
| 100 | p95 | 202.0 |
| 100 | p99 | 554.0 |
| 125 | p50 | 83.0 |
| 125 | p95 | 341.0 |
| 125 | p99 | 504.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.6 |
| 75 | p95 | 13.0 |
| 75 | p99 | 19.4 |
| 100 | p50 | 10.6 |
| 100 | p95 | 24.2 |
| 100 | p99 | 30.5 |
| 125 | p50 | 12.3 |
| 125 | p95 | 28.0 |
| 125 | p99 | 34.0 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
