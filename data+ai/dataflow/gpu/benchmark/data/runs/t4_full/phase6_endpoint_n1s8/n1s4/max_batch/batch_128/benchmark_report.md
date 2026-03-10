# Benchmark Report

Generated: 2026-03-09 15:37:00

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
| 125 | 123.8 |

## End-to-End Latency (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 58.0 |
| 75 | p95 | 87.0 |
| 75 | p99 | 291.0 |
| 100 | p50 | 67.0 |
| 100 | p95 | 174.0 |
| 100 | p99 | 697.0 |
| 125 | p50 | 761.0 |
| 125 | p95 | 961.0 |
| 125 | p99 | 1109.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.7 |
| 75 | p95 | 17.5 |
| 75 | p99 | 31.5 |
| 100 | p50 | 12.3 |
| 100 | p95 | 32.4 |
| 100 | p99 | 40.0 |
| 125 | p50 | 28.5 |
| 125 | p95 | 36.5 |
| 125 | p99 | 42.6 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
