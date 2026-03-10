# Benchmark Report

Generated: 2026-03-09 21:33:38

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
| 125 | 124.9 |

## End-to-End Latency (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 58.0 |
| 75 | p95 | 84.0 |
| 75 | p99 | 335.0 |
| 100 | p50 | 62.0 |
| 100 | p95 | 121.0 |
| 100 | p99 | 491.2 |
| 125 | p50 | 71.0 |
| 125 | p95 | 643.1 |
| 125 | p99 | 1177.1 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 6.6 |
| 75 | p95 | 14.1 |
| 75 | p99 | 20.9 |
| 100 | p50 | 11.1 |
| 100 | p95 | 24.6 |
| 100 | p99 | 30.4 |
| 125 | p50 | 12.4 |
| 125 | p95 | 28.1 |
| 125 | p99 | 35.0 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
