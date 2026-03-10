# Benchmark Report

Generated: 2026-03-08 19:10:31

## Configuration

| Parameter | Value |
|---|---|
| Messages per phase | 100s per phase |
| Rates (msg/s) | 200 |
| Experiments | Local GPU |

## Throughput

| Rate (msg/s) | Local GPU |
|---|---|
| 200 | 199.6 |

## End-to-End Latency (ms)

| Rate | Percentile | Local GPU |
|---|---|---|
| 200 | p50 | 48.0 |
| 200 | p95 | 114.0 |
| 200 | p99 | 309.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Local GPU |
|---|---|---|
| 200 | p50 | 10.1 |
| 200 | p95 | 20.9 |
| 200 | p99 | 31.1 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
