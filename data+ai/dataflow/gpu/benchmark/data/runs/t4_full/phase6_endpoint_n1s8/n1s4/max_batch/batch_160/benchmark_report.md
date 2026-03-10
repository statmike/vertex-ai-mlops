# Benchmark Report

Generated: 2026-03-09 15:49:04

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
| 125 | 124.0 |

## End-to-End Latency (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 55.5 |
| 75 | p95 | 81.0 |
| 75 | p99 | 427.0 |
| 100 | p50 | 64.0 |
| 100 | p95 | 220.0 |
| 100 | p99 | 883.0 |
| 125 | p50 | 830.0 |
| 125 | p95 | 1073.0 |
| 125 | p99 | 1215.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.6 |
| 75 | p95 | 15.8 |
| 75 | p99 | 29.2 |
| 100 | p50 | 14.2 |
| 100 | p95 | 32.5 |
| 100 | p99 | 39.2 |
| 125 | p50 | 28.8 |
| 125 | p95 | 36.9 |
| 125 | p99 | 42.5 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
