# Benchmark Report

Generated: 2026-03-10 01:34:09

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
| 75 | p50 | 55.0 |
| 75 | p95 | 75.0 |
| 75 | p99 | 136.0 |
| 100 | p50 | 60.0 |
| 100 | p95 | 139.0 |
| 100 | p99 | 743.0 |
| 125 | p50 | 70.0 |
| 125 | p95 | 348.0 |
| 125 | p99 | 825.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.1 |
| 75 | p95 | 12.6 |
| 75 | p99 | 23.2 |
| 100 | p50 | 11.6 |
| 100 | p95 | 26.3 |
| 100 | p99 | 31.7 |
| 125 | p50 | 15.9 |
| 125 | p95 | 30.4 |
| 125 | p99 | 35.8 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
