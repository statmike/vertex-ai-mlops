# Benchmark Report

Generated: 2026-03-09 14:59:26

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
| 100 | 84.4 |
| 125 | 124.9 |

## End-to-End Latency (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 57.0 |
| 75 | p95 | 76.0 |
| 75 | p99 | 589.0 |
| 100 | p50 | 64.0 |
| 100 | p95 | 25921.3 |
| 100 | p99 | 39968.1 |
| 125 | p50 | 85.0 |
| 125 | p95 | 932.0 |
| 125 | p99 | 1072.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.4 |
| 75 | p95 | 7.7 |
| 75 | p99 | 9.6 |
| 100 | p50 | 5.4 |
| 100 | p95 | 11.1 |
| 100 | p99 | 23.5 |
| 125 | p50 | 14.7 |
| 125 | p95 | 30.2 |
| 125 | p99 | 35.0 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
