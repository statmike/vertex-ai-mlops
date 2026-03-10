# Benchmark Report

Generated: 2026-03-08 16:49:25

## Configuration

| Parameter | Value |
|---|---|
| Messages per phase | 100s per phase |
| Rates (msg/s) | 50 |
| Experiments | Local GPU, Vertex AI |

## Throughput

| Rate (msg/s) | Local GPU | Vertex AI |
|---|---|---|
| 50 | 50.0 | 50.0 |

## End-to-End Latency (ms)

| Rate | Percentile | Local GPU | Vertex AI |
|---|---|---|---|
| 50 | p50 | 45.0 | 55.0 |
| 50 | p95 | 63.1 | 81.0 |
| 50 | p99 | 476.1 | 762.1 |

## GPU Inference Time (ms)

| Rate | Percentile | Local GPU | Vertex AI |
|---|---|---|---|
| 50 | p50 | 4.6 | 4.9 |
| 50 | p95 | 8.9 | 12.6 |
| 50 | p99 | 10.9 | 27.5 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
