# Benchmark Report

Generated: 2026-03-08 09:03:02

## Configuration

| Parameter | Value |
|---|---|
| Messages per phase | 100s per phase |
| Rates (msg/s) | 100 |
| Experiments | Local GPU, Vertex AI |

## Throughput

| Rate (msg/s) | Local GPU | Vertex AI |
|---|---|---|
| 100 | 97.5 | 99.9 |

## End-to-End Latency (ms)

| Rate | Percentile | Local GPU | Vertex AI |
|---|---|---|---|
| 100 | p50 | 2489.5 | 79.0 |
| 100 | p95 | 2813.0 | 238.0 |
| 100 | p99 | 2854.0 | 530.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Local GPU | Vertex AI |
|---|---|---|---|
| 100 | p50 | 19.9 | 16.7 |
| 100 | p95 | 27.9 | 37.1 |
| 100 | p99 | 30.5 | 47.8 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
