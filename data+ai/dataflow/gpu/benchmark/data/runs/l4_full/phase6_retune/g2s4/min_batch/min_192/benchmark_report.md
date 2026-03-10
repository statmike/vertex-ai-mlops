# Benchmark Report

Generated: 2026-03-08 09:40:52

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
| 125 | 122.9 | — |

## End-to-End Latency (ms)

| Rate | Percentile | Local GPU | Vertex AI |
|---|---|---|---|
| 75 | p50 | 44.0 | — |
| 75 | p95 | 62.0 | — |
| 75 | p99 | 278.0 | — |
| 100 | p50 | 51.0 | — |
| 100 | p95 | 183.0 | — |
| 100 | p99 | 619.0 | — |
| 125 | p50 | 1616.0 | — |
| 125 | p95 | 1862.0 | — |
| 125 | p99 | 1912.0 | — |

## GPU Inference Time (ms)

| Rate | Percentile | Local GPU | Vertex AI |
|---|---|---|---|
| 75 | p50 | 5.2 | — |
| 75 | p95 | 11.2 | — |
| 75 | p99 | 12.2 | — |
| 100 | p50 | 9.5 | — |
| 100 | p95 | 11.6 | — |
| 100 | p99 | 12.6 | — |
| 125 | p50 | 8.8 | — |
| 125 | p95 | 11.7 | — |
| 125 | p99 | 12.8 | — |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
