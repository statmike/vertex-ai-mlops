# Benchmark Report

Generated: 2026-03-09 21:58:45

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
| 75 | p95 | 77.0 |
| 75 | p99 | 114.0 |
| 100 | p50 | 62.0 |
| 100 | p95 | 96.0 |
| 100 | p99 | 197.0 |
| 125 | p50 | 71.0 |
| 125 | p95 | 486.0 |
| 125 | p99 | 864.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.4 |
| 75 | p95 | 12.5 |
| 75 | p99 | 19.1 |
| 100 | p50 | 11.1 |
| 100 | p95 | 25.3 |
| 100 | p99 | 31.4 |
| 125 | p50 | 14.0 |
| 125 | p95 | 29.9 |
| 125 | p99 | 35.7 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
