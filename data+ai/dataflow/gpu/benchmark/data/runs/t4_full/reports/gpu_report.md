# T4 GPU Benchmark Report
[< Overall Report](../../../../reports/benchmark_report.md)
## Phase Summary
| Phase | Focus | Key Finding |
|---|---|---|
| [Phase 1](phase1_baseline.md) | Baseline Capacity | Local saturates 50--75 msg/s; Vertex saturates 75--100 msg/s |
| [Phase 2](phase2_threads.md) | Thread Tuning | Optimal: Local=5 threads, Vertex=7 threads |
| [Phase 3](phase3_batch.md) | Batch Size | Optimal max_batch: Local=64, Vertex=160 |
| [Phase 4](phase4_minbatch.md) | Min Batch Size | Optimal min_batch: Local=4, Vertex=16 |
| [Phase 5](phase5_machines.md) | Machine Sweep | Best: Local worker=n1s4, Vertex worker=n1s4, Vertex endpoint=n1s4 |
| [Phase 6](phase6_retune.md) | Re-Tune | n1s4: Local=50, Vertex=100 msg/s; n1s8: Local=100, Vertex=100 msg/s |
| [Phase 7](phase7_scaling.md) | Scaling | Local max 399 msg/s (4w); Vertex max 995 msg/s (r10_w11) |
| [Phase 8](phase8_cost.md) | Cost Analysis | Best: local gpu $7.30/hr |

## Best Configuration

### n1s4
| Setting | Local GPU | Vertex AI |
|---|---|---|
| Threads | 3 | 6 |
| max_batch_size | 64 | 128 |
| min_batch_size | 4 | 64 |
| **Capacity** | **50 msg/s** | **100 msg/s** |

### n1s8
| Setting | Local GPU | Vertex AI |
|---|---|---|
| Threads | 2 | 6 |
| max_batch_size | 192 | 64 |
| min_batch_size | 32 | 16 |
| **Capacity** | **100 msg/s** | **100 msg/s** |

## Cost Summary
Cheapest config to sustain 1000 msg/s (p99 < 750ms): **$7.30/hr** (`10×dataflow:n1s8+t4`)

## Phase Reports
- [Phase 1: Baseline Capacity](phase1_baseline.md)
- [Phase 2: Thread Tuning](phase2_threads.md)
- [Phase 3: Batch Size](phase3_batch.md)
- [Phase 4: Min Batch Size](phase4_minbatch.md)
- [Phase 5: Machine Sweep](phase5_machines.md)
- [Phase 6: Re-Tune](phase6_retune.md)
- [Phase 7: Scaling](phase7_scaling.md)
- [Phase 8: Cost Analysis](phase8_cost.md)
