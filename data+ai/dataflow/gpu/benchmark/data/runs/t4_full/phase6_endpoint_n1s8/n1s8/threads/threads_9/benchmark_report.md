# Benchmark Report

Generated: 2026-03-09 21:04:45

## Configuration

| Parameter | Value |
|---|---|
| Messages per phase | 100s per phase |
| Rates (msg/s) | 75, 100, 125 |
| Experiments | Vertex AI |

## Throughput

| Rate (msg/s) | Vertex AI |
|---|---|
| 75 | 74.9 |
| 100 | 99.9 |
| 125 | 124.3 |

## End-to-End Latency (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 56.0 |
| 75 | p95 | 86.0 |
| 75 | p99 | 669.0 |
| 100 | p50 | 66.0 |
| 100 | p95 | 145.0 |
| 100 | p99 | 462.0 |
| 125 | p50 | 712.0 |
| 125 | p95 | 865.0 |
| 125 | p99 | 937.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.4 |
| 75 | p95 | 16.5 |
| 75 | p99 | 31.8 |
| 100 | p50 | 13.8 |
| 100 | p95 | 32.3 |
| 100 | p99 | 39.9 |
| 125 | p50 | 28.7 |
| 125 | p95 | 36.7 |
| 125 | p99 | 42.2 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
