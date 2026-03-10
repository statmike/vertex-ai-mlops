# Benchmark Report

Generated: 2026-03-08 18:41:26

## Configuration

| Parameter | Value |
|---|---|
| Messages per phase | 100s per phase |
| Rates (msg/s) | 50 |
| Experiments | Local GPU |

## Throughput

| Rate (msg/s) | Local GPU |
|---|---|
| 50 | 50.0 |

## End-to-End Latency (ms)

| Rate | Percentile | Local GPU |
|---|---|---|
| 50 | p50 | 46.0 |
| 50 | p95 | 65.0 |
| 50 | p99 | 235.1 |

## GPU Inference Time (ms)

| Rate | Percentile | Local GPU |
|---|---|---|
| 50 | p50 | 4.9 |
| 50 | p95 | 11.4 |
| 50 | p99 | 18.1 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
