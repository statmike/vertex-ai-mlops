# Benchmark Report

Generated: 2026-03-09 15:11:46

## Configuration

| Parameter | Value |
|---|---|
| Messages per phase | 100s per phase |
| Rates (msg/s) | 75, 100, 125 |
| Experiments | Vertex AI |

## Throughput

| Rate (msg/s) | Vertex AI |
|---|---|
| 75 | 74.9 |
| 100 | 99.9 |
| 125 | 124.1 |

## End-to-End Latency (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 57.0 |
| 75 | p95 | 87.0 |
| 75 | p99 | 216.0 |
| 100 | p50 | 65.0 |
| 100 | p95 | 126.0 |
| 100 | p99 | 250.0 |
| 125 | p50 | 849.0 |
| 125 | p95 | 1417.0 |
| 125 | p99 | 1589.0 |

## GPU Inference Time (ms)

| Rate | Percentile | Vertex AI |
|---|---|---|
| 75 | p50 | 5.9 |
| 75 | p95 | 17.7 |
| 75 | p99 | 30.2 |
| 100 | p50 | 13.4 |
| 100 | p95 | 32.3 |
| 100 | p99 | 40.4 |
| 125 | p50 | 28.5 |
| 125 | p95 | 36.7 |
| 125 | p99 | 42.1 |

## Charts

### Latency vs Publish Rate
![Latency](charts/latency.png)

### GPU Inference Time vs Publish Rate
![GPU Time](charts/gpu_time.png)

### Throughput vs Publish Rate
![Throughput](charts/throughput.png)
