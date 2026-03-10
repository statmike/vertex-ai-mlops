# Benchmark Report

Generated: 2026-03-09 17:43:20

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
| 125 | 124.5 |

## End-to-End Latency (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 58.0 |
| 75 | p95 | 86.0 |
| 75 | p99 | 581.0 |
| 100 | p50 | 65.0 |
| 100 | p95 | 129.0 |
| 100 | p99 | 467.0 |
| 125 | p50 | 420.0 |
| 125 | p95 | 572.0 |
| 125 | p99 | 638.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.5 |
| 75 | p95 | 13.4 |
| 75 | p99 | 21.7 |
| 100 | p50 | 10.2 |
| 100 | p95 | 24.4 |
| 100 | p99 | 30.9 |
| 125 | p50 | 10.9 |
| 125 | p95 | 27.4 |
| 125 | p99 | 33.9 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
