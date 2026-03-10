# Benchmark Report

Generated: 2026-03-08 16:39:45

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
| 125 | 123.4 | — |

## End-to-End Latency (ms)

| Rate | Percentile | Local GPU | Vertex AI |
|---|---|---|---|
| 75 | p50 | 44.0 | — |
| 75 | p95 | 61.0 | — |
| 75 | p99 | 81.0 | — |
| 100 | p50 | 50.0 | — |
| 100 | p95 | 129.0 | — |
| 100 | p99 | 416.0 | — |
| 125 | p50 | 1353.0 | — |
| 125 | p95 | 1543.0 | — |
| 125 | p99 | 1574.0 | — |

## GPU Inference Time (ms)

| Rate | Percentile | Local GPU | Vertex AI |
|---|---|---|---|
| 75 | p50 | 5.0 | — |
| 75 | p95 | 10.5 | — |
| 75 | p99 | 11.6 | — |
| 100 | p50 | 8.8 | — |
| 100 | p95 | 11.5 | — |
| 100 | p99 | 12.5 | — |
| 125 | p50 | 8.4 | — |
| 125 | p95 | 11.3 | — |
| 125 | p99 | 12.3 | — |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
