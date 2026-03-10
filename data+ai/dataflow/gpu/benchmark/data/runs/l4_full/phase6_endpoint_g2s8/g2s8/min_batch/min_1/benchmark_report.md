# Benchmark Report

Generated: 2026-03-10 00:13:18

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
| 125 | 124.9 |

## End-to-End Latency (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 54.0 |
| 75 | p95 | 75.0 |
| 75 | p99 | 187.0 |
| 100 | p50 | 61.0 |
| 100 | p95 | 112.0 |
| 100 | p99 | 664.1 |
| 125 | p50 | 70.0 |
| 125 | p95 | 232.0 |
| 125 | p99 | 493.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.0 |
| 75 | p95 | 12.5 |
| 75 | p99 | 21.7 |
| 100 | p50 | 12.5 |
| 100 | p95 | 27.6 |
| 100 | p99 | 33.1 |
| 125 | p50 | 17.0 |
| 125 | p95 | 30.6 |
| 125 | p99 | 35.5 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
