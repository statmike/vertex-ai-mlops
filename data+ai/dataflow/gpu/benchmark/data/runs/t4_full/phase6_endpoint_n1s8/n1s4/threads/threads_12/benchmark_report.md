# Benchmark Report

Generated: 2026-03-09 14:58:33

## Configuration

| Parameter | Value |
|---|---|
| Messages per phase | 100s per phase |
| Rates (msg/s) | 75, 100, 125 |
| Experiments | Vertex AI |

## Throughput

| Rate (msg/s) | Vertex AI |
|---|---|
| 75 | 75.0 |
| 100 | 99.9 |
| 125 | 124.0 |

## End-to-End Latency (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 63.0 |
| 75 | p95 | 687.0 |
| 75 | p99 | 992.0 |
| 100 | p50 | 59.0 |
| 100 | p95 | 576.0 |
| 100 | p99 | 841.0 |
| 125 | p50 | 1042.0 |
| 125 | p95 | 9249.4 |
| 125 | p99 | 10346.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.0 |
| 75 | p95 | 8.2 |
| 75 | p99 | 10.6 |
| 100 | p50 | 5.0 |
| 100 | p95 | 8.7 |
| 100 | p99 | 12.0 |
| 125 | p50 | 27.5 |
| 125 | p95 | 36.5 |
| 125 | p99 | 41.7 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
