# Benchmark Report

Generated: 2026-03-09 20:15:01

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
| 125 | 123.7 |

## End-to-End Latency (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 56.0 |
| 75 | p95 | 87.0 |
| 75 | p99 | 605.1 |
| 100 | p50 | 66.0 |
| 100 | p95 | 197.0 |
| 100 | p99 | 535.0 |
| 125 | p50 | 844.0 |
| 125 | p95 | 1149.0 |
| 125 | p99 | 1214.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.4 |
| 75 | p95 | 14.7 |
| 75 | p99 | 23.0 |
| 100 | p50 | 11.4 |
| 100 | p95 | 26.9 |
| 100 | p99 | 32.7 |
| 125 | p50 | 12.2 |
| 125 | p95 | 27.5 |
| 125 | p99 | 32.8 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
