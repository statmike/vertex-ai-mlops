# Phase 5: Machine Type Sweep (T4)
[< GPU Summary](gpu_report.md)
## Going In
Do bigger worker machines (more vCPUs, more RAM) improve per-worker capacity? We compare the default machine to a larger variant.
## Configuration
| Parameter | Value | Status |
|---|---|---|
| Local GPU Infrastructure | **n1-standard-4, n1-standard-8** (swept) | **Swept** |
| Vertex AI Infrastructure | **n1-standard-4, n1-standard-8** (swept) | **Swept** |
| Model | BERT-base (3-class text classification, max_seq_length=128) | Fixed |
| Region | us-central1 | Fixed |
| Workers | 1 | Default |
| Endpoint Replicas | 1 | Default |
| Harness Threads | Local GPU=3, Vertex AI=6 | Optimized (Phase 2) |
| max_batch_size | Local GPU=64, Vertex AI=128 | Optimized (Phase 3) |
| min_batch_size | Local GPU=4, Vertex AI=64 | Optimized (Phase 4) |
| Publish Rates | varies |  |
| Duration per Rate | 100s | Fixed |


## Worker Machine Analysis (Local GPU)
| Experiment | Best Machine | Capacity | p50 | p99 |
|---|---|---:|---:|---:|
| Local GPU | n1-standard-4 | 50 msg/s | 45 ms | 157 ms |
| Vertex AI | n1-standard-4 | 100 msg/s | 80 ms | 428 ms |

## Endpoint Machine Analysis (Vertex AI)
| Experiment | Best Machine | Capacity | p50 | p99 |
|---|---|---:|---:|---:|
| Vertex AI | n1-standard-4 | 100 msg/s | 105 ms | 573 ms |

## Phase 5b: Endpoint Follow-Up

**Endpoint machine: n1s8**
| Rate | Throughput | p50 | p99 |
|---:|---:|---:|---:|
| 50 | 50.0 | 55 ms | 111 ms |
| 75 | 75.0 | 54 ms | 553 ms |
| 100 | 100.0 | 52 ms | 482 ms |
| 125 | 124.9 | 56 ms | 630 ms |
| 150 | 149.6 | 311 ms | 3,526 ms |

![Machine Comparison](charts/phase5_machines.png)

## Conclusion
Machine type affects capacity differently for each approach. Larger machines provide more CPU headroom for tokenization and pipeline overhead, but GPU inference speed is hardware-bound.
