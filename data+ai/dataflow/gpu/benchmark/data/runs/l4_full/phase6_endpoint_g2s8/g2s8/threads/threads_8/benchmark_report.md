# Benchmark Report

Generated: 2026-03-09 21:46:26

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
| 100 | 99.9 |
| 125 | 124.8 |

## End-to-End Latency (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 57.0 |
| 75 | p95 | 84.0 |
| 75 | p99 | 859.0 |
| 100 | p50 | 62.0 |
| 100 | p95 | 139.0 |
| 100 | p99 | 653.0 |
| 125 | p50 | 71.0 |
| 125 | p95 | 265.0 |
| 125 | p99 | 710.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.1 |
| 75 | p95 | 13.7 |
| 75 | p99 | 24.0 |
| 100 | p50 | 11.2 |
| 100 | p95 | 25.2 |
| 100 | p99 | 30.5 |
| 125 | p50 | 14.3 |
| 125 | p95 | 29.8 |
| 125 | p99 | 35.6 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
