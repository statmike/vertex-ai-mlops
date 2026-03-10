# Benchmark Report

Generated: 2026-03-09 22:35:18

## Configuration

| Parameter | Value |
|---|---|
| Messages per phase | 100s per phase |
| Rates (msg/s) | 75, 100, 125 |
| Experiments | Vertex AI |

## Throughput

| Rate (msg/s) | Vertex AI |
|---|---|
| 75 | 61.9 |
| 100 | 99.9 |
| 125 | 124.9 |

## End-to-End Latency (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 55.0 |
| 75 | p95 | 76.0 |
| 75 | p99 | 128.0 |
| 100 | p50 | 60.0 |
| 100 | p95 | 102.0 |
| 100 | p99 | 231.0 |
| 125 | p50 | 66.0 |
| 125 | p95 | 174.0 |
| 125 | p99 | 332.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.2 |
| 75 | p95 | 12.6 |
| 75 | p99 | 21.6 |
| 100 | p50 | 11.4 |
| 100 | p95 | 26.5 |
| 100 | p99 | 33.5 |
| 125 | p50 | 14.4 |
| 125 | p95 | 29.8 |
| 125 | p99 | 34.9 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
