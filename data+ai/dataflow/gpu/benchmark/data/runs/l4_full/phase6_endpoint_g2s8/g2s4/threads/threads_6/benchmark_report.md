# Benchmark Report

Generated: 2026-03-09 13:45:17

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
| 125 | 124.8 |

## End-to-End Latency (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 57.0 |
| 75 | p95 | 79.0 |
| 75 | p99 | 869.0 |
| 100 | p50 | 67.0 |
| 100 | p95 | 1487.0 |
| 100 | p99 | 1926.0 |
| 125 | p50 | 134.0 |
| 125 | p95 | 3057.1 |
| 125 | p99 | 4376.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.4 |
| 75 | p95 | 7.6 |
| 75 | p99 | 9.4 |
| 100 | p50 | 5.4 |
| 100 | p95 | 8.5 |
| 100 | p99 | 11.2 |
| 125 | p50 | 5.3 |
| 125 | p95 | 8.2 |
| 125 | p99 | 10.5 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
