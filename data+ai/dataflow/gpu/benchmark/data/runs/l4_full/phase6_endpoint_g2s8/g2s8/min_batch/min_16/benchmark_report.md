# Benchmark Report

Generated: 2026-03-10 00:51:24

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
| 75 | p95 | 164.0 |
| 75 | p99 | 547.0 |
| 100 | p50 | 61.0 |
| 100 | p95 | 104.0 |
| 100 | p99 | 481.0 |
| 125 | p50 | 70.0 |
| 125 | p95 | 220.0 |
| 125 | p99 | 527.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.8 |
| 75 | p95 | 23.5 |
| 75 | p99 | 30.0 |
| 100 | p50 | 11.5 |
| 100 | p95 | 25.9 |
| 100 | p99 | 31.5 |
| 125 | p50 | 15.2 |
| 125 | p95 | 30.3 |
| 125 | p99 | 35.5 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
