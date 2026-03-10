# Benchmark Report

Generated: 2026-03-08 19:47:01

## Configuration

| Parameter | Value |
|---|---|
| Messages per phase | 100s per phase |
| Rates (msg/s) | 400 |
| Experiments | Local GPU |

## Throughput

| Rate (msg/s) | Local GPU |
|---|---|
| 400 | 399.4 |

## End-to-End Latency (ms)

| Rate | Percentile | Local GPU |
|---|---|---|
| 400 | p50 | 68.0 |
| 400 | p95 | 222.0 |
| 400 | p99 | 397.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Local GPU |
|---|---|---|
| 400 | p50 | 8.5 |
| 400 | p95 | 11.4 |
| 400 | p99 | 12.4 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
