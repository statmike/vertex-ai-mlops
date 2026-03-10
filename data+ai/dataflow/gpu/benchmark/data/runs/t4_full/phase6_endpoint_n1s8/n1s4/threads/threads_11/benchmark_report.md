# Benchmark Report

Generated: 2026-03-09 14:46:20

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
| 75 | p50 | 56.0 |
| 75 | p95 | 109.0 |
| 75 | p99 | 278.0 |
| 100 | p50 | 55.0 |
| 100 | p95 | 125.0 |
| 100 | p99 | 514.1 |
| 125 | p50 | 64.0 |
| 125 | p95 | 251.0 |
| 125 | p99 | 371.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.0 |
| 75 | p95 | 7.7 |
| 75 | p99 | 9.8 |
| 100 | p50 | 5.0 |
| 100 | p95 | 8.6 |
| 100 | p99 | 11.5 |
| 125 | p50 | 5.0 |
| 125 | p95 | 8.4 |
| 125 | p99 | 11.2 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
