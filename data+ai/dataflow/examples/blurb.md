# Model Hot-Swap on Dataflow — Swap ML Models at Runtime Without Restarting Your Pipeline

Streaming ML pipelines shouldn't need a restart just to update a model. These notebooks demonstrate **runtime model hot-swap** on Google Cloud Dataflow using Apache Beam's `RunInference` — swap between HuggingFace sentiment models while data keeps flowing, verify the switch, and roll back if needed.

**Two approaches, same goal:**

- **[Event Mode](https://github.com/statmike/vertex-ai-mlops/blob/main/data%2Bai/dataflow/examples/dataflow-runinference-model-hotswap-event-mode.ipynb)** — Trigger swaps with a Pub/Sub message. Rollback is the same operation as deployment: just publish the previous model identifier. Best for enterprise workflows that need explicit control, CI/CD integration, or instant rollback.

- **[Watch Mode](https://github.com/statmike/vertex-ai-mlops/blob/main/data%2Bai/dataflow/examples/dataflow-runinference-model-hotswap-watch-mode.ipynb)** — Trigger swaps by uploading new model artifacts to GCS. Beam polls for new files automatically. Simpler pipeline code, but rollback requires re-uploading the old model under a new filename.

**What you'll learn:**

- How `RunInference` side inputs work in streaming mode — and why `AsSingleton` without a `default_value` silently reverts your model between panes
- `PersistentRunInference` — a subclass that fixes the reversion issue (required for both modes)
- Event mode: continuous side input propagation with `ModelReemitFn` + `PeriodicImpulse` heartbeat
- Watch mode: `WatchFilePattern` internals, the empty `model_path` guard for pre-existing files, and the rollback tradeoff
- End-to-end verification: v1 predictions, v2 swap, v1 rollback — all confirmed 10/10

Each notebook is fully self-contained — set your project ID, run all cells, and clean up when done.

**Links:**

- [Examples README](https://github.com/statmike/vertex-ai-mlops/blob/main/data%2Bai/dataflow/examples/README.md)
    - [Event-Mode Notebook](https://github.com/statmike/vertex-ai-mlops/blob/main/data%2Bai/dataflow/examples/dataflow-runinference-model-hotswap-event-mode.ipynb)
    - [Watch-Mode Notebook](https://github.com/statmike/vertex-ai-mlops/blob/main/data%2Bai/dataflow/examples/dataflow-runinference-model-hotswap-watch-mode.ipynb)
