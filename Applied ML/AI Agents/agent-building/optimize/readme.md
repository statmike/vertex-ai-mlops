![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FApplied+ML%2FAI+Agents%2Fagent-building%2Foptimize&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20ML/AI%20Agents/agent-building/optimize/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/agent-building/optimize/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/agent-building/optimize/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/agent-building/optimize/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/agent-building/optimize/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Connect With Author On: </b> 
    <a href="https://www.linkedin.com/in/statmike"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a>
    <a href="https://www.github.com/statmike"><img src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub Logo" width="20px"></a> 
    <a href="https://www.youtube.com/@statmike-channel"><img src="https://upload.wikimedia.org/wikipedia/commons/f/fd/YouTube_full-color_icon_%282024%29.svg" alt="YouTube Logo" width="20px"></a>
    <a href="https://bsky.app/profile/statmike.bsky.social"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://x.com/statmike"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/Applied%20ML/AI%20Agents/agent-building/optimize/readme.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/Applied%20ML/AI%20Agents/agent-building/optimize/readme.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# Optimize — Evaluation, Simulation, Observability

This folder is **Phase 3**: the **Optimize** pillar of the Gemini Enterprise Agent
Platform. Once an agent is built (Phase 1) and deployed (Phase 2), you keep it
honest by measuring it. Optimize has three parts, and this folder exercises all
three:

| Part | What it answers | Here |
| --- | --- | --- |
| **Evaluation** | Is the agent's output good? | AutoRaters + a local LLM judge |
| **Simulation** | How does it behave over realistic multi-turn conversations? | managed user simulator + a local scenario file |
| **Observability** | What actually happened in production? | BigQuery event log + Cloud Trace |

The design principle: **anything that needs no cloud is a tested library, and
each cloud call is a thin script over it.** The reusable logic lives in
[`harness/`](./harness) and is covered by offline unit tests
([`tests/`](./tests)); the scripts just wire it to the platform.

## Two evaluation engines, same questions

You get two engines that answer the same question — *does the concierge route
correctly and answer well?* — from two directions.

### Local engine (offline, deterministic, free)

Drives the concierge with ADK's `InMemoryRunner`, distills each run to a compact
trace (routing decision, final answer, tools called), then scores it: routing is
checked deterministically, answer quality by a Gemini LLM judge.

```bash
uv run python optimize/run_local.py     # 1. run scenarios -> results/local_traces.json
uv run python optimize/judge_local.py   # 2. judge + report -> results/local_scores.json, report.md
```

- **Ground truth** lives in [`harness/scenarios.json`](./harness/scenarios.json):
  each scenario has a question, the `expected_agent`, and a reference answer.
- **Trace extraction, judge parsing, scoring, and report rendering** are pure
  functions in `harness/` — run `uv run pytest optimize/` to verify them without
  touching the cloud.

### Platform engine (managed Simulation + AutoRaters)

Uses the managed **Gen AI Evaluation & Simulation API**: it *generates* realistic
conversation scenarios from the agent's own definition (passing the whole
multi-agent topology so it understands the router and its specialists), drives a
**simulated user** through multi-turn conversations, then scores the resulting
answers with prebuilt AutoRaters.

```bash
uv run python optimize/simulate_platform.py   # generate scenarios + simulate -> results/platform_traces.json
uv run python optimize/evaluate_platform.py   # score with managed AutoRaters
uv run python optimize/optimize_platform.py   # Agent Optimizer: cluster failures into patterns
```

Raters used by `evaluate_platform.py`: `FINAL_RESPONSE_QUALITY` and
`GENERAL_QUALITY`.

### Agent Optimizer — why answers lose

Evaluation gives you a *score*; the **Agent Optimizer**
(`client.evals.generate_loss_clusters(...)`) gives you the *reasons*. It reads the
failed-rubric signals from a rubric-based AutoRater and groups the failures into
semantic **loss patterns** with an L1/L2 taxonomy and representative examples —
each pattern is a candidate instruction fix. On our own simulated run it surfaces
patterns like *"Instruction Following / Over-Punting"* (the agent declines a
request for last-30-days data by mislabeling it a "prediction") and *"Hallucination
of Action"* (claims it "reviewed the shipping docs" without a tool call) — concrete,
fixable behaviors, not just a number.

This is a **preview** feature served only in the `global` region, and two of its
constraints interact awkwardly with a multi-agent system; `optimize_platform.py`
resolves the tension so the analysis actually runs (see the note below).

The published Quality Flywheel adds a *step 5* that closes the loop
automatically — an Optimizer service (`client.optimizer.optimize`) that rewrites
system instructions from the failure data. That surface is **not yet in the
installed SDK** (2.0 exposes `client.prompt_optimizer`, a heavier data-driven
prompt-tuning job, not the flywheel optimizer), so we stop at loss clusters and
treat each pattern as a candidate instruction fix to apply by hand — which is the
same signal the auto-optimizer would act on.

> **Two hard constraints, and how the script satisfies both at once.** *(1)* Loss
> clustering only carries signal from the **`MULTI_TURN_*` agentic raters** — hand
> it a `FINAL_RESPONSE_QUALITY` result and the operation completes with an *empty*
> response (no error, no clusters). *(2)* Those same multi-turn raters **reject a
> multi-agent trace** (`does not support multiagent evaluation`, 400) — and the
> concierge is a router over three specialists. The two constraints look
> contradictory. The resolution: wrap each flattened prompt/final-answer as a
> **synthetic single-turn `AgentData` that declares one agent**. One turn + one
> declared agent satisfies the multi-turn rater, and it *is* `AgentData` with
> conversation turns, which is what clustering requires. Routing correctness across
> the real four-agent topology stays covered offline by the local engine.

> **Multi-agent limitation, worth knowing.** The prebuilt raters that read the
> raw agent trace (`MULTI_TURN_TASK_SUCCESS`, `MULTI_TURN_TOOL_USE_QUALITY`,
> `MULTI_TURN_TRAJECTORY_QUALITY`) currently **reject a multi-agent system** with
> `400 … does not support multiagent evaluation` — and the concierge is exactly
> that (a router over three specialists). So `evaluate_platform.py` flattens each
> simulated conversation to a plain prompt + final answer and scores *that* with
> the final-response raters, which judge answer text regardless of how many agents
> produced it. Routing correctness across the full system is still measured
> offline by the local engine. Two more preview edges the scripts handle: the
> scenario-generation model is `global`-only (`allow_cross_region_model=True`),
> and Gemini-3 `thought_signature` bytes must be persisted as base64 to survive
> the trace round-trip.

**Why both?** The local engine is fast, free, and runs in CI on every change with
a scenario set you control. The platform engine explores conversations you didn't
think to write and scores them with managed raters. Use the local harness as your
regression gate; use the platform engine to discover new failure modes.

## Observability — what happened in production

The concierge runs with the ADK **BigQuery Agent Analytics plugin**
([`agent_concierge/bq_plugin.py`](../agent_concierge/bq_plugin.py)), which logs
every event — LLM calls, tool invocations, transfers — to a partitioned BigQuery
table. `observe_events.py` reads that table and prints two rollups:

```bash
uv run python optimize/observe_events.py --days 7
```

- **Events by type** with error rate — LLM requests, tool completions, errors.
- **Activity by agent** — events, distinct sessions, distinct users per agent,
  which shows how traffic distributes across the router and its specialists.

The SQL lives in [`harness/observability.py`](./harness/observability.py) (table
ids are validated before interpolation, and it's unit-tested). For distributed
traces and spans, deployed agents also emit to **Cloud Trace** — deploy with
`enable_tracing=True` (Phase 2 does) and open Cloud Trace in the Console.

## Layout

```
optimize/
├── harness/                 # tested, offline library (imported by the scripts)
│   ├── scenarios.py/json    # ground-truth eval scenarios + loader/validation
│   ├── trace.py             # ADK events -> compact RunTrace
│   ├── scoring.py           # judge prompt/parse, ScoredRun, aggregate
│   ├── report.py            # RunTrace/ScoredRun -> Markdown report
│   └── observability.py     # event-log summary SQL (validated, testable)
├── tests/                   # offline unit tests for everything in harness/
├── run_local.py             # local engine, step 1: run scenarios
├── judge_local.py           # local engine, step 2: judge + report
├── simulate_platform.py     # platform engine, step 1: generate + simulate
├── evaluate_platform.py     # platform engine, step 2: AutoRaters
├── optimize_platform.py     # platform engine, step 3: Agent Optimizer (loss clusters)
├── observe_events.py        # observability: summarize the BQ event log
└── results/                 # generated traces, scores, reports (gitignored)
```

## Docs

- [Gen AI evaluation service overview](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/evaluation-overview)
- [Evaluate agents](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/evaluation-agents)
- [Evaluate your agents — Quality Flywheel, loss analysis & Optimizer](https://docs.cloud.google.com/gemini-enterprise-agent-platform/optimize/evaluation/evaluate-agents)
- [`Evals` client reference (`generate_loss_clusters`)](https://docs.cloud.google.com/python/docs/reference/agentplatform/latest/vertexai._genai.evals.Evals)
- [ADK BigQuery Agent Analytics plugin](https://google.github.io/adk-docs/observability/bigquery-agent-analytics/)
- [Agent Runtime tracing / Cloud Trace](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/manage/tracing)
