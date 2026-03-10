# Benchmark Report

Generated: 2026-03-09 14:21:00

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
| 100 | 100.0 |
| 125 | 124.9 |

## End-to-End Latency (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 57.0 |
| 75 | p95 | 154.0 |
| 75 | p99 | 760.1 |
| 100 | p50 | 59.0 |
| 100 | p95 | 252.0 |
| 100 | p99 | 432.0 |
| 125 | p50 | 65.0 |
| 125 | p95 | 304.0 |
| 125 | p99 | 579.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.0 |
| 75 | p95 | 7.8 |
| 75 | p99 | 9.6 |
| 100 | p50 | 5.1 |
| 100 | p95 | 8.8 |
| 100 | p99 | 11.9 |
| 125 | p50 | 4.9 |
| 125 | p95 | 8.4 |
| 125 | p99 | 11.3 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
