# Benchmark Report

Generated: 2026-03-09 22:06:58

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
| 75 | p95 | 82.0 |
| 75 | p99 | 459.0 |
| 100 | p50 | 64.0 |
| 100 | p95 | 148.0 |
| 100 | p99 | 556.0 |
| 125 | p50 | 145.0 |
| 125 | p95 | 638.0 |
| 125 | p99 | 895.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.1 |
| 75 | p95 | 15.2 |
| 75 | p99 | 27.1 |
| 100 | p50 | 11.8 |
| 100 | p95 | 29.9 |
| 100 | p99 | 38.6 |
| 125 | p50 | 19.9 |
| 125 | p95 | 34.7 |
| 125 | p99 | 41.3 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
