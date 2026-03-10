# Benchmark Report

Generated: 2026-03-08 20:09:40

## Configuration

| Parameter | Value |
|---|---|
| Messages per phase | 100s per phase |
| Rates (msg/s) | 600 |
| Experiments | Local GPU |

## Throughput

| Rate (msg/s) | Local GPU |
|---|---|
| 600 | 595.7 |

## End-to-End Latency (ms)

| Rate | Percentile | Local GPU |
|---|---|---|
| 600 | p50 | 190.0 |
| 600 | p95 | 477.0 |
| 600 | p99 | 708.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Local GPU |
|---|---|---|
| 600 | p50 | 10.0 |
| 600 | p95 | 13.0 |
| 600 | p99 | 14.6 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
