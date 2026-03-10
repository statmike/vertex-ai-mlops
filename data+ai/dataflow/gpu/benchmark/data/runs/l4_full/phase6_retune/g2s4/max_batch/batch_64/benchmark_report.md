# Benchmark Report

Generated: 2026-03-08 06:02:28

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
| 125 | — | 123.3 |

## End-to-End Latency (ms)

| Rate | Percentile | Local GPU | Vertex AI |
|---|---|---|---|
| 75 | p50 | — | 55.0 |
| 75 | p95 | — | 80.0 |
| 75 | p99 | — | 360.1 |
| 100 | p50 | — | 68.0 |
| 100 | p95 | — | 142.0 |
| 100 | p99 | — | 455.0 |
| 125 | p50 | — | 1209.0 |
| 125 | p95 | — | 1438.0 |
| 125 | p99 | — | 1511.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Local GPU | Vertex AI |
|---|---|---|---|
| 75 | p50 | — | 6.3 |
| 75 | p95 | — | 17.4 |
| 75 | p99 | — | 30.0 |
| 100 | p50 | — | 16.8 |
| 100 | p95 | — | 34.7 |
| 100 | p99 | — | 44.1 |
| 125 | p50 | — | 29.5 |
| 125 | p95 | — | 37.1 |
| 125 | p99 | — | 46.3 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
