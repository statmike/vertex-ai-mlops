# Benchmark Report

Generated: 2026-03-08 14:43:44

## Configuration

| Parameter | Value |
|---|---|
| Messages per phase | 100s per phase |
| Rates (msg/s) | 75, 100, 125 |
| Experiments | Local GPU, Vertex AI |

## Throughput

| Rate (msg/s) | Local GPU | Vertex AI |
|---|---|---|
| 75 | — | 75.0 |
| 100 | — | 99.9 |
| 125 | — | 122.6 |

## End-to-End Latency (ms)

| Rate | Percentile | Local GPU | Vertex AI |
|---|---|---|---|
| 75 | p50 | — | 56.0 |
| 75 | p95 | — | 80.0 |
| 75 | p99 | — | 139.0 |
| 100 | p50 | — | 74.0 |
| 100 | p95 | — | 349.0 |
| 100 | p99 | — | 763.0 |
| 125 | p50 | — | 1807.0 |
| 125 | p95 | — | 2047.0 |
| 125 | p99 | — | 2126.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Local GPU | Vertex AI |
|---|---|---|---|
| 75 | p50 | — | 6.4 |
| 75 | p95 | — | 17.8 |
| 75 | p99 | — | 31.4 |
| 100 | p50 | — | 21.3 |
| 100 | p95 | — | 36.9 |
| 100 | p99 | — | 47.3 |
| 125 | p50 | — | 31.6 |
| 125 | p95 | — | 38.2 |
| 125 | p99 | — | 47.1 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
