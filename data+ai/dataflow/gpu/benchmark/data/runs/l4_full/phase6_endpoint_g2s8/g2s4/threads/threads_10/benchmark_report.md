# Benchmark Report

Generated: 2026-03-09 14:34:32

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
| 75 | p95 | 73.0 |
| 75 | p99 | 214.0 |
| 100 | p50 | 57.0 |
| 100 | p95 | 90.0 |
| 100 | p99 | 276.0 |
| 125 | p50 | 61.0 |
| 125 | p95 | 398.0 |
| 125 | p99 | 912.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.4 |
| 75 | p95 | 7.6 |
| 75 | p99 | 9.4 |
| 100 | p50 | 5.4 |
| 100 | p95 | 8.3 |
| 100 | p99 | 11.0 |
| 125 | p50 | 5.3 |
| 125 | p95 | 8.2 |
| 125 | p99 | 10.7 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
