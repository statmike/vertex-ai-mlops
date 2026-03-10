# Benchmark Report

Generated: 2026-03-09 13:56:01

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
| 125 | 125.0 |

## End-to-End Latency (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 57.0 |
| 75 | p95 | 76.0 |
| 75 | p99 | 475.0 |
| 100 | p50 | 57.0 |
| 100 | p95 | 115.0 |
| 100 | p99 | 455.0 |
| 125 | p50 | 68.0 |
| 125 | p95 | 435.0 |
| 125 | p99 | 611.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.0 |
| 75 | p95 | 7.8 |
| 75 | p99 | 9.7 |
| 100 | p50 | 5.0 |
| 100 | p95 | 8.7 |
| 100 | p99 | 11.9 |
| 125 | p50 | 5.0 |
| 125 | p95 | 8.6 |
| 125 | p99 | 11.9 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
