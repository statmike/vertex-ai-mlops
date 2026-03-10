# Benchmark Report

Generated: 2026-03-09 22:47:40

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
| 75 | p95 | 106.0 |
| 75 | p99 | 426.1 |
| 100 | p50 | 66.0 |
| 100 | p95 | 541.0 |
| 100 | p99 | 929.0 |
| 125 | p50 | 229.0 |
| 125 | p95 | 703.0 |
| 125 | p99 | 965.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.5 |
| 75 | p95 | 20.3 |
| 75 | p99 | 29.6 |
| 100 | p50 | 15.6 |
| 100 | p95 | 29.9 |
| 100 | p99 | 34.9 |
| 125 | p50 | 24.7 |
| 125 | p95 | 32.5 |
| 125 | p99 | 38.0 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
