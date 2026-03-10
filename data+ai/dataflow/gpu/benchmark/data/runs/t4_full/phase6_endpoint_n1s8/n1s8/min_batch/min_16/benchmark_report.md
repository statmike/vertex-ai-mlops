# Benchmark Report

Generated: 2026-03-09 23:56:19

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
| 75 | p95 | 78.0 |
| 75 | p99 | 124.0 |
| 100 | p50 | 66.0 |
| 100 | p95 | 168.0 |
| 100 | p99 | 810.0 |
| 125 | p50 | 162.0 |
| 125 | p95 | 476.0 |
| 125 | p99 | 533.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.1 |
| 75 | p95 | 14.1 |
| 75 | p99 | 23.0 |
| 100 | p50 | 12.7 |
| 100 | p95 | 30.5 |
| 100 | p99 | 39.1 |
| 125 | p50 | 20.9 |
| 125 | p95 | 34.7 |
| 125 | p99 | 42.1 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
