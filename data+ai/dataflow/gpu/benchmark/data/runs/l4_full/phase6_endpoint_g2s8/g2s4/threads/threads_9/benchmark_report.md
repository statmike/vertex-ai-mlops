# Benchmark Report

Generated: 2026-03-09 14:22:09

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
| 100 | 99.8 |
| 125 | 124.8 |

## End-to-End Latency (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 57.0 |
| 75 | p95 | 433.0 |
| 75 | p99 | 674.0 |
| 100 | p50 | 65.0 |
| 100 | p95 | 715.0 |
| 100 | p99 | 1045.0 |
| 125 | p50 | 110.0 |
| 125 | p95 | 726.0 |
| 125 | p99 | 1001.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.4 |
| 75 | p95 | 8.0 |
| 75 | p99 | 9.8 |
| 100 | p50 | 5.3 |
| 100 | p95 | 8.6 |
| 100 | p99 | 11.1 |
| 125 | p50 | 5.3 |
| 125 | p95 | 8.6 |
| 125 | p99 | 11.3 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
