# Benchmark Report

Generated: 2026-03-10 01:04:30

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
| 75 | p95 | 77.0 |
| 75 | p99 | 245.1 |
| 100 | p50 | 60.0 |
| 100 | p95 | 108.0 |
| 100 | p99 | 463.0 |
| 125 | p50 | 68.0 |
| 125 | p95 | 163.0 |
| 125 | p99 | 332.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.1 |
| 75 | p95 | 12.8 |
| 75 | p99 | 24.6 |
| 100 | p50 | 11.5 |
| 100 | p95 | 25.9 |
| 100 | p99 | 31.8 |
| 125 | p50 | 15.9 |
| 125 | p95 | 30.2 |
| 125 | p99 | 35.7 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
