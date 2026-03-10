include .env
export

.PHONY: init train-model generate-data create-topics \
        build-worker build-serve deploy-endpoint redeploy scale-endpoint \
        benchmark benchmark-all benchmark-capacity benchmark-capacity-2t benchmark-scale \
        benchmark-all-t4 benchmark-all-l4 \
        publish run-exp-a run-exp-b cancel-job \
        collect-a collect-b compare cleanup help

# ── Setup ──────────────────────────────────────────────────────

init: ## Install deps with uv (pins Python 3.11)
	uv sync

train-model: ## Fine-tune DistilBERT, upload to GCS
	uv run python scripts/train_model.py --output_path $(MODEL_PATH)

generate-data: ## Generate 100k synthetic transactions
	uv run python scripts/generate_data.py --count $(MAX_MESSAGES) --output data/test_transactions.txt

create-topics: ## Create input + output Pub/Sub topics and subscriptions
	gcloud pubsub topics create $(INPUT_TOPIC_SHORT) --project $(PROJECT_ID) || true
	gcloud pubsub topics create $(OUTPUT_TOPIC_SHORT) --project $(PROJECT_ID) || true
	gcloud pubsub subscriptions create $(OUTPUT_SUB_SHORT) \
		--topic $(OUTPUT_TOPIC_SHORT) \
		--project $(PROJECT_ID) \
		--ack-deadline 600 || true

# ── Build & Deploy ────────────────────────────────────────────

build-worker: ## Cloud Build: Dataflow GPU worker image
	gcloud builds submit . \
		--project $(PROJECT_ID) \
		--config cloudbuild-worker.yaml \
		--substitutions _IMAGE=$(WORKER_IMAGE) \
		--timeout 30m

build-serve: ## Cloud Build: Vertex AI serving image
	gcloud builds submit . \
		--project $(PROJECT_ID) \
		--config cloudbuild-serve.yaml \
		--substitutions _IMAGE=$(SERVE_IMAGE) \
		--timeout 30m

redeploy: ## Teardown + rebuild Vertex AI model/endpoint (run after code changes to handlers/pipeline)
	@echo "═══════════════════════════════════════════════════════════════"
	@echo "  REDEPLOY: Teardown and rebuild Vertex AI endpoint"
	@echo "  Using .env file: $(or $(ENV_FILE),.env)"
	@echo "═══════════════════════════════════════════════════════════════"
	@echo ""
	@echo "Step 1: Undeploy model from endpoint..."
	-gcloud ai endpoints undeploy-model $(VERTEX_ENDPOINT_ID) \
		--project $(PROJECT_ID) --region $(REGION) \
		--deployed-model-id benchmark_model
	@echo ""
	@echo "Step 2: Delete endpoint..."
	-gcloud ai endpoints delete $(VERTEX_ENDPOINT_ID) \
		--project $(PROJECT_ID) --region $(REGION) --quiet
	@echo ""
	@echo "Step 3: Delete model from registry..."
	-gcloud ai models delete $(VERTEX_MODEL_ID) \
		--project $(PROJECT_ID) --region $(REGION) --quiet
	@echo ""
	@echo "Step 4: Upload new model with updated container..."
	gcloud ai models upload \
		--project $(PROJECT_ID) \
		--region $(REGION) \
		--display-name benchmark-bert \
		--container-image-uri $(SERVE_IMAGE) \
		--artifact-uri $(MODEL_PATH) \
		--container-env-vars "MODEL_PATH=/model,NUM_LABELS=$(NUM_LABELS),MAX_SEQ_LENGTH=$(MAX_SEQ_LENGTH),CATEGORY_NAMES=$(CATEGORY_NAMES)" \
		--container-health-route /health \
		--container-predict-route /predict \
		--format "value(name)" | tail -1 | tee /dev/stderr | xargs -I{} echo "NEW_VERTEX_MODEL_ID={}"
	@echo ""
	@echo "Step 5: Create new endpoint..."
	gcloud ai endpoints create \
		--project $(PROJECT_ID) \
		--region $(REGION) \
		--display-name benchmark-endpoint \
		--format "value(name)" | tail -1 | tee /dev/stderr | xargs -I{} echo "NEW_VERTEX_ENDPOINT_ID={}"
	@echo ""
	@echo "═══════════════════════════════════════════════════════════════"
	@echo "  MANUAL STEPS REQUIRED:"
	@echo "  1. Update .env with new VERTEX_ENDPOINT_ID and VERTEX_MODEL_ID"
	@echo "  2. Deploy model to endpoint:"
	@echo "     gcloud ai endpoints deploy-model <NEW_ENDPOINT_ID> \\"
	@echo "       --project $(PROJECT_ID) --region $(REGION) \\"
	@echo "       --model <NEW_MODEL_ID> \\"
	@echo "       --display-name benchmark_model \\"
	@echo "       --machine-type $(MACHINE_TYPE) \\"
	@echo "       --accelerator type=$(GPU_TYPE),count=1 \\"
	@echo "       --min-replica-count 1 --max-replica-count 1"
	@echo "  3. Smoke test:"
	@echo "     gcloud ai endpoints predict <NEW_ENDPOINT_ID> \\"
	@echo "       --project $(PROJECT_ID) --region $(REGION) \\"
	@echo "       --json-request '{\"instances\": [{\"text\": \"test\"}]}'"
	@echo "═══════════════════════════════════════════════════════════════"

scale-endpoint: ## Scale Vertex AI endpoint replicas (SCALE_REPLICAS in .env)
	uv run python scripts/scale_endpoint.py --replicas $(SCALE_REPLICAS)

deploy-endpoint: ## Upload model + create endpoint + deploy
	@echo "Step 1: Upload model to Vertex AI Model Registry"
	gcloud ai models upload \
		--project $(PROJECT_ID) \
		--region $(REGION) \
		--display-name benchmark-bert \
		--container-image-uri $(SERVE_IMAGE) \
		--artifact-uri $(MODEL_PATH) \
		--container-env-vars "MODEL_PATH=/model,NUM_LABELS=$(NUM_LABELS),MAX_SEQ_LENGTH=$(MAX_SEQ_LENGTH),CATEGORY_NAMES=$(CATEGORY_NAMES)" \
		--container-health-route /health \
		--container-predict-route /predict \
		--format "value(name)" | tail -1 | xargs -I{} echo "VERTEX_MODEL_ID={}" >> .env.deploy
	@echo "Step 2: Create endpoint"
	gcloud ai endpoints create \
		--project $(PROJECT_ID) \
		--region $(REGION) \
		--display-name benchmark-endpoint \
		--format "value(name)" | tail -1 | xargs -I{} echo "VERTEX_ENDPOINT_ID={}" >> .env.deploy
	@echo "Step 3: Deploy model to endpoint"
	@echo ">>> Update .env with VERTEX_ENDPOINT_ID and VERTEX_MODEL_ID from .env.deploy, then run:"
	@echo "    gcloud ai endpoints deploy-model $(VERTEX_ENDPOINT_ID) \\"
	@echo "      --project $(PROJECT_ID) --region $(REGION) \\"
	@echo "      --model $(VERTEX_MODEL_ID) \\"
	@echo "      --display-name benchmark_model \\"
	@echo "      --machine-type $(MACHINE_TYPE) \\"
	@echo "      --accelerator type=$(GPU_TYPE),count=1 \\"
	@echo "      --min-replica-count 1 --max-replica-count 1"

# ── Benchmark (automated) ────────────────────────────────────

benchmark-all: ## Run all 8 phases end-to-end (results in data/runs/<timestamp>/)
	uv run python scripts/run_all_phases.py

benchmark-all-t4: ## Run all 8 phases for T4 GPU config
	mkdir -p data/runs/t4_full
	uv run python scripts/run_all_phases.py \
		--env-file .env.t4 --run-name t4_full \
		--local-gpu-workers 1 2 3 4 \
		--topic-prefix bench-t4 \
		2>&1 | tee data/runs/t4_full/t4_full.log

benchmark-all-l4: ## Run all 8 phases for L4 GPU config
	mkdir -p data/runs/l4_full
	uv run python scripts/run_all_phases.py \
		--env-file .env.l4 --run-name l4_full \
		--local-gpu-workers 1 2 4 6 8 10 \
		--topic-prefix bench-l4 \
		2>&1 | tee data/runs/l4_full/l4_full.log

benchmark: ## Run full benchmark: both experiments end-to-end with comparison
	uv run python scripts/run_benchmark.py \
		--count $(MAX_MESSAGES) --rates 50 75 100

benchmark-capacity: ## Phase 1: single-worker capacity across rates (100s per rate)
	uv run python scripts/run_benchmark.py \
		--duration 100 --rates 25 50 75 100 125 150 \
		--num_workers 1

benchmark-capacity-2t: ## Quick test: capacity with 2 harness threads
	uv run python scripts/run_benchmark.py \
		--duration 100 --rates 25 50 75 100 125 150 \
		--num_workers 1 --harness_threads 2

benchmark-scale: ## Phase 7: verify at scale with calculated worker count
	uv run python scripts/run_benchmark.py \
		--duration 100 --rates 1000 \
		--num_workers $(SCALE_WORKERS) \
		--harness_threads_local_gpu 2

# ── Run (manual) ─────────────────────────────────────────────

publish: ## Publish messages to input topic at configured rate
	uv run python scripts/publish.py \
		--project_id $(PROJECT_ID) \
		--topic_id $(INPUT_TOPIC_SHORT) \
		--data_file data/test_transactions.txt \
		--rate $(PUBLISH_RATE) \
		--max_messages $(MAX_MESSAGES)

run-exp-a: ## Exp A: Dataflow + local GPU (RunInference + LocalGPUHandler)
	uv run python -m benchmark.run \
		--runner DataflowRunner \
		--project $(PROJECT_ID) --region $(REGION) \
		--machine_type $(MACHINE_TYPE) \
		--num_workers $(MIN_WORKERS) \
		--dataflow_service_option "worker_accelerator=type:$(GPU_TYPE);count:1;install-nvidia-driver" \
		--sdk_container_image $(WORKER_IMAGE) --sdk_location container \
		--experiment use_runner_v2 \
		--experiment no_use_multiple_sdk_containers \
		--disk_size_gb 50 \
		--enable_streaming_engine \
		--staging_location $(STAGING) --temp_location $(TEMP) \
		--mode local_gpu --device GPU \
		--input_topic $(INPUT_TOPIC) --output_topic $(OUTPUT_TOPIC) \
		--model_path $(MODEL_PATH) \
		--num_labels $(NUM_LABELS) --max_seq_length $(MAX_SEQ_LENGTH) \
		--category_names $(CATEGORY_NAMES)

run-exp-b: ## Exp B: Dataflow + Vertex AI (RunInference + VertexAIHandler)
	uv run python -m benchmark.run \
		--runner DataflowRunner \
		--project $(PROJECT_ID) --region $(REGION) \
		--machine_type n1-standard-4 \
		--num_workers $(MIN_WORKERS) \
		--sdk_container_image $(WORKER_IMAGE) --sdk_location container \
		--experiment use_runner_v2 \
		--experiment no_use_multiple_sdk_containers \
		--disk_size_gb 50 \
		--enable_streaming_engine \
		--staging_location $(STAGING) --temp_location $(TEMP) \
		--mode vertex_ai \
		--vertex_endpoint_id $(VERTEX_ENDPOINT_ID) --vertex_region $(REGION) \
		--input_topic $(INPUT_TOPIC) --output_topic $(OUTPUT_TOPIC) \
		--model_path $(MODEL_PATH) \
		--num_labels $(NUM_LABELS) --max_seq_length $(MAX_SEQ_LENGTH) \
		--category_names $(CATEGORY_NAMES)

cancel-job: ## Cancel running Dataflow job
	@echo "Active streaming jobs:"
	@gcloud dataflow jobs list --project $(PROJECT_ID) --region $(REGION) \
		--filter "state=Running" --format "value(id)" | head -1 | \
		xargs -I{} gcloud dataflow jobs cancel {} --project $(PROJECT_ID) --region $(REGION)

# ── Measure & Cleanup ────────────────────────────────────────

collect-a: ## Pull Exp A results from output subscription, print stats
	uv run python scripts/collect.py \
		--project_id $(PROJECT_ID) \
		--subscription_id $(OUTPUT_SUB_SHORT) \
		--expected_count $(MAX_MESSAGES) \
		--label "Exp A (Local GPU)" \
		--output_file data/results_exp_a.json

collect-b: ## Pull Exp B results from output subscription, print stats
	uv run python scripts/collect.py \
		--project_id $(PROJECT_ID) \
		--subscription_id $(OUTPUT_SUB_SHORT) \
		--expected_count $(MAX_MESSAGES) \
		--label "Exp B (Vertex AI)" \
		--output_file data/results_exp_b.json

compare: ## Print side-by-side comparison from collected results
	@uv run python -c " \
	import json, numpy as np; \
	for label, path in [('Exp A (Local GPU)', 'data/results_exp_a.json'), ('Exp B (Vertex AI)', 'data/results_exp_b.json')]: \
	    data = json.load(open(path)); \
	    lats = np.array([r['latency_ms'] for r in data]); \
	    infs = np.array([r['pure_inference_time_ms'] for r in data]); \
	    pub = [r['publish_time_ms'] for r in data]; \
	    proc = [r['processed_time_ms'] for r in data]; \
	    elapsed = (max(proc) - min(pub)) / 1000; \
	    tp = len(data) / elapsed if elapsed > 0 else 0; \
	    print(f'\n{label}:'); \
	    print(f'  Count:      {len(data)}'); \
	    print(f'  Throughput: {tp:.0f} msg/s'); \
	    print(f'  Latency    p50={np.percentile(lats,50):.0f}ms  p95={np.percentile(lats,95):.0f}ms  p99={np.percentile(lats,99):.0f}ms'); \
	    print(f'  GPU time   p50={np.percentile(infs,50):.1f}ms  p95={np.percentile(infs,95):.1f}ms  p99={np.percentile(infs,99):.1f}ms') \
	"

cleanup: ## Tear down ALL GCP resources
	uv run python scripts/cleanup.py \
		--project_id $(PROJECT_ID) \
		--region $(REGION) \
		--input_topic $(INPUT_TOPIC_SHORT) \
		--output_topic $(OUTPUT_TOPIC_SHORT) \
		--output_subscription $(OUTPUT_SUB_SHORT) \
		--vertex_endpoint_id $(VERTEX_ENDPOINT_ID) \
		--vertex_model_id $(VERTEX_MODEL_ID)

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
