# Benchmark Report

Generated: 2026-03-09 14:47:01

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
| 75 | p95 | 76.0 |
| 75 | p99 | 170.0 |
| 100 | p50 | 56.0 |
| 100 | p95 | 133.0 |
| 100 | p99 | 618.0 |
| 125 | p50 | 59.0 |
| 125 | p95 | 342.1 |
| 125 | p99 | 904.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.4 |
| 75 | p95 | 7.8 |
| 75 | p99 | 9.7 |
| 100 | p50 | 5.4 |
| 100 | p95 | 8.5 |
| 100 | p99 | 11.0 |
| 125 | p50 | 5.3 |
| 125 | p95 | 8.5 |
| 125 | p99 | 11.2 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
