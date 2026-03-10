# Benchmark Report

Generated: 2026-03-09 15:37:25

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
| 125 | 124.1 |

## End-to-End Latency (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 58.0 |
| 75 | p95 | 81.0 |
| 75 | p99 | 211.0 |
| 100 | p50 | 65.0 |
| 100 | p95 | 108.0 |
| 100 | p99 | 212.0 |
| 125 | p50 | 398.0 |
| 125 | p95 | 3457.0 |
| 125 | p99 | 4572.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.3 |
| 75 | p95 | 13.5 |
| 75 | p99 | 20.8 |
| 100 | p50 | 10.3 |
| 100 | p95 | 24.1 |
| 100 | p99 | 29.8 |
| 125 | p50 | 9.4 |
| 125 | p95 | 26.4 |
| 125 | p99 | 32.5 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
