# Benchmark Report

Generated: 2026-03-09 20:28:21

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
| 75 | p95 | 87.0 |
| 75 | p99 | 621.0 |
| 100 | p50 | 65.0 |
| 100 | p95 | 122.0 |
| 100 | p99 | 331.0 |
| 125 | p50 | 521.0 |
| 125 | p95 | 674.0 |
| 125 | p99 | 735.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.8 |
| 75 | p95 | 15.1 |
| 75 | p99 | 24.6 |
| 100 | p50 | 11.3 |
| 100 | p95 | 28.0 |
| 100 | p99 | 35.3 |
| 125 | p50 | 13.5 |
| 125 | p95 | 30.8 |
| 125 | p99 | 37.8 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
