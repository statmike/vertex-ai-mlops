# Benchmark Report

Generated: 2026-03-09 16:14:19

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
| 125 | 121.3 |

## End-to-End Latency (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 61.0 |
| 75 | p95 | 99.0 |
| 75 | p99 | 908.1 |
| 100 | p50 | 74.0 |
| 100 | p95 | 217.0 |
| 100 | p99 | 567.0 |
| 125 | p50 | 1378.0 |
| 125 | p95 | 3231.0 |
| 125 | p99 | 3920.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.9 |
| 75 | p95 | 16.4 |
| 75 | p99 | 28.6 |
| 100 | p50 | 9.9 |
| 100 | p95 | 31.1 |
| 100 | p99 | 39.7 |
| 125 | p50 | 12.0 |
| 125 | p95 | 33.9 |
| 125 | p99 | 40.4 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
