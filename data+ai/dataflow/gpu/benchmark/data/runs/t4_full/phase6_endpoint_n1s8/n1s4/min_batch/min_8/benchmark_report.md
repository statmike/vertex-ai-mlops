# Benchmark Report

Generated: 2026-03-09 17:05:08

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
| 125 | 124.2 |

## End-to-End Latency (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 55.0 |
| 75 | p95 | 79.0 |
| 75 | p99 | 405.1 |
| 100 | p50 | 65.0 |
| 100 | p95 | 151.0 |
| 100 | p99 | 533.0 |
| 125 | p50 | 755.0 |
| 125 | p95 | 958.0 |
| 125 | p99 | 1099.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.4 |
| 75 | p95 | 15.7 |
| 75 | p99 | 31.2 |
| 100 | p50 | 14.2 |
| 100 | p95 | 32.5 |
| 100 | p99 | 39.9 |
| 125 | p50 | 28.9 |
| 125 | p95 | 36.9 |
| 125 | p99 | 42.3 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
