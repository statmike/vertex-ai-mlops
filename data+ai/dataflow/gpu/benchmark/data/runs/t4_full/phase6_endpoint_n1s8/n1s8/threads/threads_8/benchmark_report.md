# Benchmark Report

Generated: 2026-03-09 20:52:58

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
| 125 | 124.5 |

## End-to-End Latency (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 58.0 |
| 75 | p95 | 90.0 |
| 75 | p99 | 409.1 |
| 100 | p50 | 67.0 |
| 100 | p95 | 136.0 |
| 100 | p99 | 378.0 |
| 125 | p50 | 388.0 |
| 125 | p95 | 585.0 |
| 125 | p99 | 779.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.7 |
| 75 | p95 | 16.8 |
| 75 | p99 | 28.5 |
| 100 | p50 | 12.3 |
| 100 | p95 | 32.1 |
| 100 | p99 | 41.2 |
| 125 | p50 | 26.4 |
| 125 | p95 | 35.9 |
| 125 | p99 | 43.4 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
