# Benchmark Report

Generated: 2026-03-09 16:15:21

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
| 75 | p50 | 55.0 |
| 75 | p95 | 77.0 |
| 75 | p99 | 202.0 |
| 100 | p50 | 60.0 |
| 100 | p95 | 101.0 |
| 100 | p99 | 471.0 |
| 125 | p50 | 94.0 |
| 125 | p95 | 912.0 |
| 125 | p99 | 1334.1 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.2 |
| 75 | p95 | 12.6 |
| 75 | p99 | 19.8 |
| 100 | p50 | 11.5 |
| 100 | p95 | 24.6 |
| 100 | p99 | 31.0 |
| 125 | p50 | 13.7 |
| 125 | p95 | 28.0 |
| 125 | p99 | 33.6 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
