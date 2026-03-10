# Benchmark Report

Generated: 2026-03-08 21:12:30

## Configuration

| Parameter | Value |
|---|---|
| Messages per phase | 100s per phase |
| Rates (msg/s) | 450 |
| Experiments | Local GPU |

## Throughput

| Rate (msg/s) | Local GPU |
|---|---|
| 450 | 449.3 |

## End-to-End Latency (ms)

| Rate | Percentile | Local GPU |
|---|---|---|
| 450 | p50 | 58.0 |
| 450 | p95 | 170.0 |
| 450 | p99 | 337.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Local GPU |
|---|---|---|
| 450 | p50 | 8.4 |
| 450 | p95 | 11.2 |
| 450 | p99 | 12.2 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
