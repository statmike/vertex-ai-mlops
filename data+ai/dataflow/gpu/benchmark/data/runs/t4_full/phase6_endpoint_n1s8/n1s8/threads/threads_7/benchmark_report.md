# Benchmark Report

Generated: 2026-03-09 20:40:16

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
| 75 | p95 | 83.0 |
| 75 | p99 | 613.0 |
| 100 | p50 | 63.0 |
| 100 | p95 | 245.0 |
| 100 | p99 | 1164.0 |
| 125 | p50 | 149.0 |
| 125 | p95 | 378.0 |
| 125 | p99 | 477.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.6 |
| 75 | p95 | 16.1 |
| 75 | p99 | 29.1 |
| 100 | p50 | 13.2 |
| 100 | p95 | 30.9 |
| 100 | p99 | 40.0 |
| 125 | p50 | 24.5 |
| 125 | p95 | 35.4 |
| 125 | p99 | 42.4 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
