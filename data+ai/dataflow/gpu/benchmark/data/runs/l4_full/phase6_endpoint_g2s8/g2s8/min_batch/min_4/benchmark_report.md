# Benchmark Report

Generated: 2026-03-10 00:26:54

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
| 100 | 99.8 |
| 125 | 124.9 |

## End-to-End Latency (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 54.0 |
| 75 | p95 | 82.0 |
| 75 | p99 | 735.0 |
| 100 | p50 | 59.0 |
| 100 | p95 | 101.0 |
| 100 | p99 | 413.1 |
| 125 | p50 | 64.0 |
| 125 | p95 | 153.0 |
| 125 | p99 | 304.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.4 |
| 75 | p95 | 16.1 |
| 75 | p99 | 28.1 |
| 100 | p50 | 12.0 |
| 100 | p95 | 26.4 |
| 100 | p99 | 31.9 |
| 125 | p50 | 15.4 |
| 125 | p95 | 30.2 |
| 125 | p99 | 35.8 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
