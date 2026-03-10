# Benchmark Report

Generated: 2026-03-08 02:09:32

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
| 75 | p50 | — | 57.0 |
| 75 | p95 | — | 96.0 |
| 75 | p99 | — | 642.1 |
| 100 | p50 | — | 82.0 |
| 100 | p95 | — | 432.1 |
| 100 | p99 | — | 722.0 |
| 125 | p50 | — | 1679.0 |
| 125 | p95 | — | 1965.0 |
| 125 | p99 | — | 2025.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Local GPU | Vertex AI |
|---|---|---|---|
| 75 | p50 | — | 6.1 |
| 75 | p95 | — | 20.9 |
| 75 | p99 | — | 35.9 |
| 100 | p50 | — | 17.1 |
| 100 | p95 | — | 37.6 |
| 100 | p99 | — | 46.5 |
| 125 | p50 | — | 17.8 |
| 125 | p95 | — | 37.6 |
| 125 | p99 | — | 46.8 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
