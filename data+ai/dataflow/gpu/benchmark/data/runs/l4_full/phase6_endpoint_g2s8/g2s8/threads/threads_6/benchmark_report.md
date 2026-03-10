# Benchmark Report

Generated: 2026-03-09 21:21:10

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
| 125 | 124.8 |

## End-to-End Latency (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 56.0 |
| 75 | p95 | 80.0 |
| 75 | p99 | 545.1 |
| 100 | p50 | 61.0 |
| 100 | p95 | 111.0 |
| 100 | p99 | 686.0 |
| 125 | p50 | 74.0 |
| 125 | p95 | 217.0 |
| 125 | p99 | 427.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.3 |
| 75 | p95 | 13.1 |
| 75 | p99 | 20.2 |
| 100 | p50 | 10.8 |
| 100 | p95 | 23.9 |
| 100 | p99 | 29.5 |
| 125 | p50 | 12.0 |
| 125 | p95 | 25.9 |
| 125 | p99 | 31.1 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
