# Benchmark Report

Generated: 2026-03-09 23:32:01

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
| 75 | p95 | 80.0 |
| 75 | p99 | 313.1 |
| 100 | p50 | 63.0 |
| 100 | p95 | 140.0 |
| 100 | p99 | 538.0 |
| 125 | p50 | 110.0 |
| 125 | p95 | 448.0 |
| 125 | p99 | 590.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.3 |
| 75 | p95 | 15.5 |
| 75 | p99 | 26.1 |
| 100 | p50 | 13.1 |
| 100 | p95 | 31.4 |
| 100 | p99 | 39.7 |
| 125 | p50 | 22.1 |
| 125 | p95 | 35.0 |
| 125 | p99 | 41.6 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
