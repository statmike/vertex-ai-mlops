# Benchmark Report

Generated: 2026-03-09 23:00:05

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
| 75 | p95 | 81.0 |
| 75 | p99 | 531.0 |
| 100 | p50 | 61.0 |
| 100 | p95 | 110.0 |
| 100 | p99 | 572.1 |
| 125 | p50 | 72.0 |
| 125 | p95 | 349.0 |
| 125 | p99 | 728.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.6 |
| 75 | p95 | 14.7 |
| 75 | p99 | 27.4 |
| 100 | p50 | 10.8 |
| 100 | p95 | 25.7 |
| 100 | p99 | 32.2 |
| 125 | p50 | 15.0 |
| 125 | p95 | 30.4 |
| 125 | p99 | 35.6 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
