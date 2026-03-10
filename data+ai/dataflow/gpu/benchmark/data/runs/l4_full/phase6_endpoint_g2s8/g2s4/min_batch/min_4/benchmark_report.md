# Benchmark Report

Generated: 2026-03-09 16:51:32

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
| 75 | p50 | 58.0 |
| 75 | p95 | 92.0 |
| 75 | p99 | 434.0 |
| 100 | p50 | 61.0 |
| 100 | p95 | 127.0 |
| 100 | p99 | 278.0 |
| 125 | p50 | 75.0 |
| 125 | p95 | 505.0 |
| 125 | p99 | 781.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.9 |
| 75 | p95 | 14.4 |
| 75 | p99 | 23.3 |
| 100 | p50 | 10.7 |
| 100 | p95 | 24.1 |
| 100 | p99 | 29.7 |
| 125 | p50 | 12.9 |
| 125 | p95 | 27.9 |
| 125 | p99 | 34.4 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
