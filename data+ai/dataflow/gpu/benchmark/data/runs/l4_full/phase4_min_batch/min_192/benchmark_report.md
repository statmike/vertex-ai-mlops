# Benchmark Report

Generated: 2026-03-08 02:23:48

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
| 125 | 122.2 | — |

## End-to-End Latency (ms)

| Rate | Percentile | Local GPU | Vertex AI |
|---|---|---|---|
| 75 | p50 | 46.0 | — |
| 75 | p95 | 126.0 | — |
| 75 | p99 | 412.1 | — |
| 100 | p50 | 56.0 | — |
| 100 | p95 | 668.0 | — |
| 100 | p99 | 1252.1 | — |
| 125 | p50 | 1830.0 | — |
| 125 | p95 | 2443.0 | — |
| 125 | p99 | 2508.0 | — |

## GPU Inference Time (ms)

| Rate | Percentile | Local GPU | Vertex AI |
|---|---|---|---|
| 75 | p50 | 6.0 | — |
| 75 | p95 | 11.4 | — |
| 75 | p99 | 12.3 | — |
| 100 | p50 | 9.9 | — |
| 100 | p95 | 11.9 | — |
| 100 | p99 | 12.8 | — |
| 125 | p50 | 8.8 | — |
| 125 | p95 | 11.8 | — |
| 125 | p99 | 12.8 | — |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
