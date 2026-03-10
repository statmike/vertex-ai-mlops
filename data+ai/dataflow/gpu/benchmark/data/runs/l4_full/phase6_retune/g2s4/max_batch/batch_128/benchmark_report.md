# Benchmark Report

Generated: 2026-03-08 06:34:21

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
| 125 | — | 123.4 |

## End-to-End Latency (ms)

| Rate | Percentile | Local GPU | Vertex AI |
|---|---|---|---|
| 75 | p50 | — | 57.0 |
| 75 | p95 | — | 84.0 |
| 75 | p99 | — | 527.0 |
| 100 | p50 | — | 73.0 |
| 100 | p95 | — | 159.0 |
| 100 | p99 | — | 413.0 |
| 125 | p50 | — | 1348.0 |
| 125 | p95 | — | 1560.0 |
| 125 | p99 | — | 1627.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Local GPU | Vertex AI |
|---|---|---|---|
| 75 | p50 | — | 6.6 |
| 75 | p95 | — | 17.5 |
| 75 | p99 | — | 30.9 |
| 100 | p50 | — | 14.9 |
| 100 | p95 | — | 33.5 |
| 100 | p99 | — | 43.4 |
| 125 | p50 | — | 15.3 |
| 125 | p95 | — | 34.6 |
| 125 | p99 | — | 44.7 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
