# Benchmark Report

Generated: 2026-03-09 21:31:00

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
| 75 | p50 | 58.0 |
| 75 | p95 | 92.0 |
| 75 | p99 | 628.0 |
| 100 | p50 | 68.0 |
| 100 | p95 | 180.0 |
| 100 | p99 | 684.0 |
| 125 | p50 | 886.5 |
| 125 | p95 | 1046.0 |
| 125 | p99 | 1138.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 6.1 |
| 75 | p95 | 17.8 |
| 75 | p99 | 31.0 |
| 100 | p50 | 12.4 |
| 100 | p95 | 32.0 |
| 100 | p99 | 39.7 |
| 125 | p50 | 28.6 |
| 125 | p95 | 36.9 |
| 125 | p99 | 43.3 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
