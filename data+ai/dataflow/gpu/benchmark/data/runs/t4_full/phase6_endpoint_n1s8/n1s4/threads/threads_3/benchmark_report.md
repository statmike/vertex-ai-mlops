# Benchmark Report

Generated: 2026-03-09 13:04:40

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
| 125 | 122.2 |

## End-to-End Latency (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 57.0 |
| 75 | p95 | 152.0 |
| 75 | p99 | 958.0 |
| 100 | p50 | 114.0 |
| 100 | p95 | 739.0 |
| 100 | p99 | 928.0 |
| 125 | p50 | 2375.0 |
| 125 | p95 | 2834.0 |
| 125 | p99 | 2923.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 4.8 |
| 75 | p95 | 7.5 |
| 75 | p99 | 9.1 |
| 100 | p50 | 4.8 |
| 100 | p95 | 8.1 |
| 100 | p99 | 10.6 |
| 125 | p50 | 4.6 |
| 125 | p95 | 8.9 |
| 125 | p99 | 17.2 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
