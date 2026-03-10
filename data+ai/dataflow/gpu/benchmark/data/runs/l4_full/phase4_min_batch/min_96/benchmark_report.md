# Benchmark Report

Generated: 2026-03-08 01:36:00

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
| 100 | 99.6 | — |
| 125 | 121.5 | — |

## End-to-End Latency (ms)

| Rate | Percentile | Local GPU | Vertex AI |
|---|---|---|---|
| 75 | p50 | 47.0 | — |
| 75 | p95 | 73.0 | — |
| 75 | p99 | 444.0 | — |
| 100 | p50 | 654.5 | — |
| 100 | p95 | 985.0 | — |
| 100 | p99 | 1017.0 | — |
| 125 | p50 | 2722.0 | — |
| 125 | p95 | 2932.0 | — |
| 125 | p99 | 2975.0 | — |

## GPU Inference Time (ms)

| Rate | Percentile | Local GPU | Vertex AI |
|---|---|---|---|
| 75 | p50 | 7.6 | — |
| 75 | p95 | 12.1 | — |
| 75 | p99 | 13.5 | — |
| 100 | p50 | 10.5 | — |
| 100 | p95 | 13.4 | — |
| 100 | p99 | 14.9 | — |
| 125 | p50 | 9.1 | — |
| 125 | p95 | 12.7 | — |
| 125 | p99 | 14.3 | — |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
