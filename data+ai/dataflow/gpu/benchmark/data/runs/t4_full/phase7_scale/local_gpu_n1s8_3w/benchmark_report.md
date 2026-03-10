# Benchmark Report

Generated: 2026-03-08 19:38:16

## Configuration

| Parameter | Value |
|---|---|
| Messages per phase | 100s per phase |
| Rates (msg/s) | 300 |
| Experiments | Local GPU |

## Throughput

| Rate (msg/s) | Local GPU |
|---|---|
| 300 | 299.6 |

## End-to-End Latency (ms)

| Rate | Percentile | Local GPU |
|---|---|---|
| 300 | p50 | 68.0 |
| 300 | p95 | 240.0 |
| 300 | p99 | 603.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Local GPU |
|---|---|---|
| 300 | p50 | 8.8 |
| 300 | p95 | 11.8 |
| 300 | p99 | 12.9 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
