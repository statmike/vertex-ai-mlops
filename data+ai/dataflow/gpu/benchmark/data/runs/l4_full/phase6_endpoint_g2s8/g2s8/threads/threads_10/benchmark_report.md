# Benchmark Report

Generated: 2026-03-09 22:10:35

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
| 75 | p50 | 57.0 |
| 75 | p95 | 81.0 |
| 75 | p99 | 653.1 |
| 100 | p50 | 63.0 |
| 100 | p95 | 109.0 |
| 100 | p99 | 272.0 |
| 125 | p50 | 74.0 |
| 125 | p95 | 459.0 |
| 125 | p99 | 750.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.4 |
| 75 | p95 | 13.5 |
| 75 | p99 | 23.8 |
| 100 | p50 | 11.1 |
| 100 | p95 | 25.6 |
| 100 | p99 | 32.1 |
| 125 | p50 | 14.3 |
| 125 | p95 | 29.9 |
| 125 | p99 | 35.8 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
