# Benchmark Report

Generated: 2026-03-08 17:46:09

## Configuration

| Parameter | Value |
|---|---|
| Messages per phase | 100s per phase |
| Rates (msg/s) | 200 |
| Experiments | Local GPU, Vertex AI |

## Throughput

| Rate (msg/s) | Local GPU | Vertex AI |
|---|---|---|
| 200 | 188.6 | 189.7 |

## End-to-End Latency (ms)

| Rate | Percentile | Local GPU | Vertex AI |
|---|---|---|---|
| 200 | p50 | 5026.5 | 5309.0 |
| 200 | p95 | 6450.0 | 6517.0 |
| 200 | p99 | 6547.0 | 6995.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Local GPU | Vertex AI |
|---|---|---|---|
| 200 | p50 | 4.7 | 9.1 |
| 200 | p95 | 11.1 | 32.2 |
| 200 | p99 | 12.8 | 39.0 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
