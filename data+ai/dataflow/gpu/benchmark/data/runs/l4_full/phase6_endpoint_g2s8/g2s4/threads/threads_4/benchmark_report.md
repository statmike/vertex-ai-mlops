# Benchmark Report

Generated: 2026-03-09 13:21:12

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
| 125 | 123.8 |

## End-to-End Latency (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 58.0 |
| 75 | p95 | 90.0 |
| 75 | p99 | 427.1 |
| 100 | p50 | 61.0 |
| 100 | p95 | 233.0 |
| 100 | p99 | 910.0 |
| 125 | p50 | 1058.0 |
| 125 | p95 | 1281.0 |
| 125 | p99 | 1320.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.4 |
| 75 | p95 | 7.4 |
| 75 | p99 | 9.2 |
| 100 | p50 | 5.4 |
| 100 | p95 | 8.6 |
| 100 | p99 | 11.2 |
| 125 | p50 | 5.2 |
| 125 | p95 | 8.2 |
| 125 | p99 | 10.7 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
