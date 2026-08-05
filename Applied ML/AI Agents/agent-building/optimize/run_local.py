"""Local eval engine — run every scenario through the concierge in-process.

No deployment, no simulation service: an ``InMemoryRunner`` drives the real
concierge agent, and each run is reduced to a ``RunTrace`` (routing + answer +
tools). Traces are written to ``optimize/results/local_traces.json`` for the
judge (``judge_local.py``) to score.

    uv run python optimize/run_local.py

Requires the demo data (``make setup``) and cloud auth, since the agents call
BigQuery / Conversational Analytics / Claude for real. The DISCOVERY specialist
runs over A2A, so start it first (``make discovery``) or those scenarios error
cleanly and show up as failures — never as crashes.
"""

from __future__ import annotations

import asyncio
import json
import sys
from dataclasses import asdict
from pathlib import Path

# Make the project root importable (config.py + agent packages live there).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from optimize.harness import extract_trace, load_scenarios  # noqa: E402
from optimize.harness.trace import RunTrace  # noqa: E402

RESULTS_DIR = Path(__file__).resolve().parent / "results"
TRACES_PATH = RESULTS_DIR / "local_traces.json"

APP_NAME = "agent_concierge"
USER_ID = "local_eval"


async def _run_one(runner, question: str) -> RunTrace:
    """Run a single question through the concierge, returning its trace."""
    from google.genai import types

    session = await runner.session_service.create_session(app_name=APP_NAME, user_id=USER_ID)
    message = types.Content(role="user", parts=[types.Part(text=question)])

    events = []
    try:
        async for event in runner.run_async(
            user_id=USER_ID, session_id=session.id, new_message=message
        ):
            events.append(event)
    except Exception as e:  # a live-service failure is a scenario failure, not a crash
        trace = extract_trace(events)
        trace.error = str(e)
        return trace
    return extract_trace(events)


async def _main() -> None:
    from google.adk.runners import InMemoryRunner

    from agent_concierge.agent import app

    scenarios = load_scenarios()
    # Drive the App (not the bare root_agent) so the BigQuery Agent Analytics
    # plugin travels with the run — local eval then also produces the event log
    # that observe_events.py summarizes, exercising all three Optimize parts.
    runner = InMemoryRunner(app=app)

    print(f"Running {len(scenarios)} scenarios through {APP_NAME} (in-process)...\n")
    records = []
    for scen in scenarios:
        print(f"  [{scen.id}] {scen.question}")
        trace = await _run_one(runner, scen.question)
        status = "ok" if trace.ok else f"ERROR: {trace.error or 'no answer'}"
        print(f"      -> routed_to={trace.routed_to} ({status})")
        records.append({"scenario_id": scen.id, "trace": asdict(trace)})

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    TRACES_PATH.write_text(json.dumps(records, indent=2) + "\n")
    print(f"\nWrote {len(records)} traces to {TRACES_PATH.relative_to(PROJECT_ROOT)}")
    print("Next: uv run python optimize/judge_local.py")


if __name__ == "__main__":
    asyncio.run(_main())
