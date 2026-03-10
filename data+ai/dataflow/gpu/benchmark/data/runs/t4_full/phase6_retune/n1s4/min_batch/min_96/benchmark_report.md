# Benchmark Report

Generated: 2026-03-08 08:35:20

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
| 125 | — | 122.8 |

## End-to-End Latency (ms)

| Rate | Percentile | Local GPU | Vertex AI |
|---|---|---|---|
| 75 | p50 | — | 55.0 |
| 75 | p95 | — | 84.0 |
| 75 | p99 | — | 854.0 |
| 100 | p50 | — | 73.5 |
| 100 | p95 | — | 565.0 |
| 100 | p99 | — | 1135.1 |
| 125 | p50 | — | 1314.0 |
| 125 | p95 | — | 1842.0 |
| 125 | p99 | — | 2043.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Local GPU | Vertex AI |
|---|---|---|---|
| 75 | p50 | — | 6.0 |
| 75 | p95 | — | 18.0 |
| 75 | p99 | — | 32.5 |
| 100 | p50 | — | 16.0 |
| 100 | p95 | — | 36.2 |
| 100 | p99 | — | 46.7 |
| 125 | p50 | — | 17.6 |
| 125 | p95 | — | 37.0 |
| 125 | p99 | — | 46.4 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
