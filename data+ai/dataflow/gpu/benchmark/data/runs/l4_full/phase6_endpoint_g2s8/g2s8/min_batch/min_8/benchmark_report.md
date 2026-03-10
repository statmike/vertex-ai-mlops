# Benchmark Report

Generated: 2026-03-10 00:39:41

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
| 75 | p50 | 54.0 |
| 75 | p95 | 76.0 |
| 75 | p99 | 277.0 |
| 100 | p50 | 59.0 |
| 100 | p95 | 110.0 |
| 100 | p99 | 605.0 |
| 125 | p50 | 65.0 |
| 125 | p95 | 163.0 |
| 125 | p99 | 357.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.1 |
| 75 | p95 | 13.4 |
| 75 | p99 | 24.9 |
| 100 | p50 | 11.6 |
| 100 | p95 | 26.9 |
| 100 | p99 | 32.7 |
| 125 | p50 | 16.1 |
| 125 | p95 | 30.2 |
| 125 | p99 | 36.1 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
