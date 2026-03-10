# Benchmark Report

Generated: 2026-03-08 21:40:30

## Configuration

| Parameter | Value |
|---|---|
| Messages per phase | 100s per phase |
| Rates (msg/s) | 750 |
| Experiments | Local GPU |

## Throughput

| Rate (msg/s) | Local GPU |
|---|---|
| 750 | 748.7 |

## End-to-End Latency (ms)

| Rate | Percentile | Local GPU |
|---|---|---|
| 750 | p50 | 116.0 |
| 750 | p95 | 296.0 |
| 750 | p99 | 959.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Local GPU |
|---|---|---|
| 750 | p50 | 8.4 |
| 750 | p95 | 11.2 |
| 750 | p99 | 12.3 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
