# Benchmark Report

Generated: 2026-03-09 22:23:28

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
| 75 | p50 | 59.0 |
| 75 | p95 | 85.0 |
| 75 | p99 | 354.1 |
| 100 | p50 | 65.0 |
| 100 | p95 | 154.0 |
| 100 | p99 | 641.0 |
| 125 | p50 | 79.0 |
| 125 | p95 | 215.0 |
| 125 | p99 | 358.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.5 |
| 75 | p95 | 12.8 |
| 75 | p99 | 23.6 |
| 100 | p50 | 10.4 |
| 100 | p95 | 25.7 |
| 100 | p99 | 32.0 |
| 125 | p50 | 14.8 |
| 125 | p95 | 30.2 |
| 125 | p99 | 35.4 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
