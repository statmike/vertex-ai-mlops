# Benchmark Report

Generated: 2026-03-09 14:08:40

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
| 75 | p50 | 54.0 |
| 75 | p95 | 74.0 |
| 75 | p99 | 654.1 |
| 100 | p50 | 52.0 |
| 100 | p95 | 77.0 |
| 100 | p99 | 324.0 |
| 125 | p50 | 54.0 |
| 125 | p95 | 116.0 |
| 125 | p99 | 491.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.0 |
| 75 | p95 | 7.9 |
| 75 | p99 | 9.7 |
| 100 | p50 | 5.0 |
| 100 | p95 | 8.9 |
| 100 | p99 | 12.1 |
| 125 | p50 | 5.0 |
| 125 | p95 | 8.8 |
| 125 | p99 | 12.1 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
