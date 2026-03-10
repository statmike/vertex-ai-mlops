# Benchmark Report

Generated: 2026-03-08 19:53:14

## Configuration

| Parameter | Value |
|---|---|
| Messages per phase | 100s per phase |
| Rates (msg/s) | 200 |
| Experiments | Local GPU |

## Throughput

| Rate (msg/s) | Local GPU |
|---|---|
| 200 | 199.8 |

## End-to-End Latency (ms)

| Rate | Percentile | Local GPU |
|---|---|---|
| 200 | p50 | 113.0 |
| 200 | p95 | 282.0 |
| 200 | p99 | 613.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Local GPU |
|---|---|---|
| 200 | p50 | 10.0 |
| 200 | p95 | 12.2 |
| 200 | p99 | 13.3 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
