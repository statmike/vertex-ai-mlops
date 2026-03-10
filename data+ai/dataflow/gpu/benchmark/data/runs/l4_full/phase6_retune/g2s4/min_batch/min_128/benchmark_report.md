# Benchmark Report

Generated: 2026-03-08 09:09:13

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
| 125 | 122.5 | — |

## End-to-End Latency (ms)

| Rate | Percentile | Local GPU | Vertex AI |
|---|---|---|---|
| 75 | p50 | 45.0 | — |
| 75 | p95 | 63.0 | — |
| 75 | p99 | 144.0 | — |
| 100 | p50 | 66.0 | — |
| 100 | p95 | 242.0 | — |
| 100 | p99 | 359.0 | — |
| 125 | p50 | 2096.0 | — |
| 125 | p95 | 2270.0 | — |
| 125 | p99 | 2310.0 | — |

## GPU Inference Time (ms)

| Rate | Percentile | Local GPU | Vertex AI |
|---|---|---|---|
| 75 | p50 | 5.5 | — |
| 75 | p95 | 11.2 | — |
| 75 | p99 | 12.3 | — |
| 100 | p50 | 9.7 | — |
| 100 | p95 | 11.8 | — |
| 100 | p99 | 12.8 | — |
| 125 | p50 | 8.6 | — |
| 125 | p95 | 11.5 | — |
| 125 | p99 | 12.4 | — |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
