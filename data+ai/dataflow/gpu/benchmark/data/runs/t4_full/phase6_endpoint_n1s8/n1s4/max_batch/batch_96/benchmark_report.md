# Benchmark Report

Generated: 2026-03-09 15:24:33

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
| 125 | 123.9 |

## End-to-End Latency (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 57.0 |
| 75 | p95 | 86.0 |
| 75 | p99 | 252.1 |
| 100 | p50 | 68.0 |
| 100 | p95 | 158.0 |
| 100 | p99 | 266.0 |
| 125 | p50 | 799.0 |
| 125 | p95 | 983.0 |
| 125 | p99 | 1105.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.8 |
| 75 | p95 | 17.0 |
| 75 | p99 | 29.6 |
| 100 | p50 | 13.1 |
| 100 | p95 | 33.2 |
| 100 | p99 | 41.3 |
| 125 | p50 | 28.7 |
| 125 | p95 | 36.9 |
| 125 | p99 | 43.0 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
