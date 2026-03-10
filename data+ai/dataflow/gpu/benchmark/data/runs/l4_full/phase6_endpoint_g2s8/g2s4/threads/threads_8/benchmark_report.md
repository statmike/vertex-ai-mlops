# Benchmark Report

Generated: 2026-03-09 14:09:02

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
| 75 | p50 | 56.0 |
| 75 | p95 | 75.0 |
| 75 | p99 | 139.0 |
| 100 | p50 | 100.0 |
| 100 | p95 | 1390.0 |
| 100 | p99 | 1641.0 |
| 125 | p50 | 65.0 |
| 125 | p95 | 713.0 |
| 125 | p99 | 1371.1 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.4 |
| 75 | p95 | 7.5 |
| 75 | p99 | 9.2 |
| 100 | p50 | 5.3 |
| 100 | p95 | 8.5 |
| 100 | p99 | 11.3 |
| 125 | p50 | 5.3 |
| 125 | p95 | 8.7 |
| 125 | p99 | 11.7 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
