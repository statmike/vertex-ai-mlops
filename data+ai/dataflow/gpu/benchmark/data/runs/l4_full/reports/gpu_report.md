# L4 GPU Benchmark Report
[< Overall Report](../../../../reports/benchmark_report.md)
## Phase Summary
| Phase | Focus | Key Finding |
|---|---|---|
| [Phase 1](phase1_baseline.md) | Baseline Capacity | Local saturates 75--100 msg/s; Vertex saturates 100--125 msg/s |
| [Phase 2](phase2_threads.md) | Thread Tuning | Optimal: Local=2 threads, Vertex=10 threads |
| [Phase 3](phase3_batch.md) | Batch Size | Optimal max_batch: Local=224, Vertex=64 |
| [Phase 4](phase4_minbatch.md) | Min Batch Size | Optimal min_batch: Local=160, Vertex=32 |
| [Phase 5](phase5_machines.md) | Machine Sweep | Best: Local worker=g2s4, Vertex worker=g2s8, Vertex endpoint=g2s4 |
| [Phase 6](phase6_retune.md) | Re-Tune | g2s4: Local=100, Vertex=75 msg/s; g2s8: Local=75, Vertex=100 msg/s |
| [Phase 7](phase7_scaling.md) | Scaling | Local max 993 msg/s (10w); Vertex max 998 msg/s (r10_w8) |
| [Phase 8](phase8_cost.md) | Cost Analysis | Best: local gpu $7.07/hr |

## Best Configuration

### g2s4
| Setting | Local GPU | Vertex AI |
|---|---|---|
| Threads | 2 | 7 |
| max_batch_size | 256 | 96 |
| min_batch_size | 8 | 32 |
| **Capacity** | **100 msg/s** | **75 msg/s** |

### g2s8
| Setting | Local GPU | Vertex AI |
|---|---|---|
| Threads | 2 | 9 |
| max_batch_size | 224 | 160 |
| min_batch_size | 192 | 1 |
| **Capacity** | **75 msg/s** | **100 msg/s** |

## Cost Summary
Cheapest config to sustain 1000 msg/s (p99 < 750ms): **$7.07/hr** (`10×dataflow:g2s4+l4`)

## Phase Reports
- [Phase 1: Baseline Capacity](phase1_baseline.md)
- [Phase 2: Thread Tuning](phase2_threads.md)
- [Phase 3: Batch Size](phase3_batch.md)
- [Phase 4: Min Batch Size](phase4_minbatch.md)
- [Phase 5: Machine Sweep](phase5_machines.md)
- [Phase 6: Re-Tune](phase6_retune.md)
- [Phase 7: Scaling](phase7_scaling.md)
- [Phase 8: Cost Analysis](phase8_cost.md)
