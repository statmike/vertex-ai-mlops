# Benchmark Report

Generated: 2026-03-08 16:07:43

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
| 100 | 100.0 | — |
| 125 | 123.8 | — |

## End-to-End Latency (ms)

| Rate | Percentile | Local GPU | Vertex AI |
|---|---|---|---|
| 75 | p50 | 44.0 | — |
| 75 | p95 | 62.0 | — |
| 75 | p99 | 314.1 | — |
| 100 | p50 | 50.0 | — |
| 100 | p95 | 127.0 | — |
| 100 | p99 | 555.0 | — |
| 125 | p50 | 1000.0 | — |
| 125 | p95 | 1162.0 | — |
| 125 | p99 | 1211.0 | — |

## GPU Inference Time (ms)

| Rate | Percentile | Local GPU | Vertex AI |
|---|---|---|---|
| 75 | p50 | 5.2 | — |
| 75 | p95 | 10.5 | — |
| 75 | p99 | 11.8 | — |
| 100 | p50 | 8.3 | — |
| 100 | p95 | 11.3 | — |
| 100 | p99 | 12.2 | — |
| 125 | p50 | 8.2 | — |
| 125 | p95 | 11.2 | — |
| 125 | p99 | 12.3 | — |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
