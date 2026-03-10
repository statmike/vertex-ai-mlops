# Benchmark Report

Generated: 2026-03-09 16:52:26

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
| 125 | 123.7 |

## End-to-End Latency (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 58.0 |
| 75 | p95 | 84.0 |
| 75 | p99 | 673.0 |
| 100 | p50 | 70.0 |
| 100 | p95 | 185.0 |
| 100 | p99 | 641.0 |
| 125 | p50 | 864.0 |
| 125 | p95 | 1061.0 |
| 125 | p99 | 1170.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.6 |
| 75 | p95 | 15.8 |
| 75 | p99 | 30.9 |
| 100 | p50 | 12.1 |
| 100 | p95 | 32.0 |
| 100 | p99 | 39.5 |
| 125 | p50 | 27.6 |
| 125 | p95 | 36.5 |
| 125 | p99 | 42.6 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
