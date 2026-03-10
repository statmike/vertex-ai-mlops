# Benchmark Report

Generated: 2026-03-09 15:24:28

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
| 75 | p95 | 83.0 |
| 75 | p99 | 270.1 |
| 100 | p50 | 68.0 |
| 100 | p95 | 220.0 |
| 100 | p99 | 598.0 |
| 125 | p50 | 100.0 |
| 125 | p95 | 442.0 |
| 125 | p99 | 638.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.7 |
| 75 | p95 | 13.4 |
| 75 | p99 | 20.3 |
| 100 | p50 | 10.1 |
| 100 | p95 | 24.2 |
| 100 | p99 | 30.2 |
| 125 | p50 | 10.5 |
| 125 | p95 | 27.0 |
| 125 | p99 | 32.9 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
