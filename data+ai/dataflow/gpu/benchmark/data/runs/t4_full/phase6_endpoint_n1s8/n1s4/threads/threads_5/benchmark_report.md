# Benchmark Report

Generated: 2026-03-09 13:30:52

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
| 125 | 122.0 |

## End-to-End Latency (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 56.0 |
| 75 | p95 | 102.0 |
| 75 | p99 | 640.0 |
| 100 | p50 | 69.0 |
| 100 | p95 | 212.0 |
| 100 | p99 | 367.0 |
| 125 | p50 | 661.0 |
| 125 | p95 | 1594.0 |
| 125 | p99 | 1970.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 4.9 |
| 75 | p95 | 7.8 |
| 75 | p99 | 10.2 |
| 100 | p50 | 4.9 |
| 100 | p95 | 8.7 |
| 100 | p99 | 12.0 |
| 125 | p50 | 4.8 |
| 125 | p95 | 8.1 |
| 125 | p99 | 10.7 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
