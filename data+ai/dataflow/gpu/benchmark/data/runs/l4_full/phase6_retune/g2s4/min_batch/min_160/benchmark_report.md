# Benchmark Report

Generated: 2026-03-08 09:25:02

## Configuration

| Parameter | Value |
|---|---|
| Messages per phase | 100s per phase |
| Rates (msg/s) | 75, 100, 125 |
| Experiments | Local GPU, Vertex AI |

## Throughput

| Rate (msg/s) | Local GPU | Vertex AI |
|---|---|---|
| 75 | 75.0 | — |
| 100 | 99.9 | — |
| 125 | 122.6 | — |

## End-to-End Latency (ms)

| Rate | Percentile | Local GPU | Vertex AI |
|---|---|---|---|
| 75 | p50 | 46.0 | — |
| 75 | p95 | 64.0 | — |
| 75 | p99 | 194.1 | — |
| 100 | p50 | 57.0 | — |
| 100 | p95 | 226.0 | — |
| 100 | p99 | 489.0 | — |
| 125 | p50 | 1827.0 | — |
| 125 | p95 | 2218.0 | — |
| 125 | p99 | 2263.0 | — |

## GPU Inference Time (ms)

| Rate | Percentile | Local GPU | Vertex AI |
|---|---|---|---|
| 75 | p50 | 5.7 | — |
| 75 | p95 | 11.2 | — |
| 75 | p99 | 12.1 | — |
| 100 | p50 | 9.7 | — |
| 100 | p95 | 11.7 | — |
| 100 | p99 | 12.6 | — |
| 125 | p50 | 8.6 | — |
| 125 | p95 | 11.4 | — |
| 125 | p99 | 12.3 | — |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
