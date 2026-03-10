# Benchmark Report

Generated: 2026-03-09 13:43:25

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
| 75 | p95 | 73.0 |
| 75 | p99 | 399.1 |
| 100 | p50 | 55.0 |
| 100 | p95 | 82.0 |
| 100 | p99 | 261.0 |
| 125 | p50 | 64.0 |
| 125 | p95 | 260.0 |
| 125 | p99 | 467.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 4.9 |
| 75 | p95 | 7.7 |
| 75 | p99 | 9.7 |
| 100 | p50 | 4.9 |
| 100 | p95 | 8.6 |
| 100 | p99 | 11.5 |
| 125 | p50 | 4.8 |
| 125 | p95 | 8.2 |
| 125 | p99 | 11.0 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
