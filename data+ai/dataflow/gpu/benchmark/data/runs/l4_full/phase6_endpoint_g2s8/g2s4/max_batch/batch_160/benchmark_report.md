# Benchmark Report

Generated: 2026-03-09 15:49:10

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
| 75 | p95 | 113.0 |
| 75 | p99 | 250.0 |
| 100 | p50 | 60.0 |
| 100 | p95 | 106.0 |
| 100 | p99 | 569.0 |
| 125 | p50 | 68.0 |
| 125 | p95 | 430.0 |
| 125 | p99 | 684.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.9 |
| 75 | p95 | 17.9 |
| 75 | p99 | 26.3 |
| 100 | p50 | 11.6 |
| 100 | p95 | 24.9 |
| 100 | p99 | 30.0 |
| 125 | p50 | 13.2 |
| 125 | p95 | 28.3 |
| 125 | p99 | 34.8 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
