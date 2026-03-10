# Benchmark Report

Generated: 2026-03-08 20:47:11

## Configuration

| Parameter | Value |
|---|---|
| Messages per phase | 100s per phase |
| Rates (msg/s) | 75 |
| Experiments | Local GPU |

## Throughput

| Rate (msg/s) | Local GPU |
|---|---|
| 75 | 75.0 |

## End-to-End Latency (ms)

| Rate | Percentile | Local GPU |
|---|---|---|
| 75 | p50 | 43.0 |
| 75 | p95 | 62.0 |
| 75 | p99 | 563.1 |

## GPU Inference Time (ms)

| Rate | Percentile | Local GPU |
|---|---|---|
| 75 | p50 | 5.0 |
| 75 | p95 | 10.1 |
| 75 | p99 | 11.2 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
