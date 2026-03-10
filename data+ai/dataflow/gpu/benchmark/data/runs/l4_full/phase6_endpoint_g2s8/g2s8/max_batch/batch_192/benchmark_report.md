# Benchmark Report

Generated: 2026-03-09 23:37:15

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
| 75 | p50 | 55.0 |
| 75 | p95 | 77.0 |
| 75 | p99 | 417.1 |
| 100 | p50 | 61.0 |
| 100 | p95 | 109.0 |
| 100 | p99 | 464.0 |
| 125 | p50 | 69.0 |
| 125 | p95 | 301.0 |
| 125 | p99 | 718.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.2 |
| 75 | p95 | 13.9 |
| 75 | p99 | 25.8 |
| 100 | p50 | 10.7 |
| 100 | p95 | 25.0 |
| 100 | p99 | 30.9 |
| 125 | p50 | 14.7 |
| 125 | p95 | 30.1 |
| 125 | p99 | 35.4 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
