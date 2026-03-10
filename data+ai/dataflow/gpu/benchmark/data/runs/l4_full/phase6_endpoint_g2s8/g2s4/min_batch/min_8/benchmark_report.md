# Benchmark Report

Generated: 2026-03-09 17:05:05

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
| 100 | 99.8 |
| 125 | 124.9 |

## End-to-End Latency (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 56.0 |
| 75 | p95 | 82.0 |
| 75 | p99 | 532.3 |
| 100 | p50 | 62.0 |
| 100 | p95 | 104.0 |
| 100 | p99 | 308.0 |
| 125 | p50 | 73.0 |
| 125 | p95 | 524.0 |
| 125 | p99 | 859.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.7 |
| 75 | p95 | 13.8 |
| 75 | p99 | 21.6 |
| 100 | p50 | 11.0 |
| 100 | p95 | 24.5 |
| 100 | p99 | 29.8 |
| 125 | p50 | 12.3 |
| 125 | p95 | 27.4 |
| 125 | p99 | 33.8 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
