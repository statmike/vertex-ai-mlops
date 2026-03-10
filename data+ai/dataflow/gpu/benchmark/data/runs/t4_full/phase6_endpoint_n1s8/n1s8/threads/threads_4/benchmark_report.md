# Benchmark Report

Generated: 2026-03-09 20:02:30

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
| 125 | 122.8 |

## End-to-End Latency (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 56.0 |
| 75 | p95 | 83.0 |
| 75 | p99 | 353.0 |
| 100 | p50 | 83.0 |
| 100 | p95 | 282.0 |
| 100 | p99 | 790.0 |
| 125 | p50 | 1768.0 |
| 125 | p95 | 2107.0 |
| 125 | p99 | 2177.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.2 |
| 75 | p95 | 14.1 |
| 75 | p99 | 21.0 |
| 100 | p50 | 12.1 |
| 100 | p95 | 24.3 |
| 100 | p99 | 29.1 |
| 125 | p50 | 9.4 |
| 125 | p95 | 22.5 |
| 125 | p99 | 27.7 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
