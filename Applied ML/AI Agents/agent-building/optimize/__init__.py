"""Optimize pillar: evaluate, simulate, and observe the agent system.

Two engines, one goal — know whether the agents are good:

    Platform  — the Gen AI Evaluation & Simulation API (simulate_platform.py,
                evaluate_platform.py): a simulated user drives multi-turn
                conversations, then managed AutoRaters score them.
    Local     — an offline harness (run_local.py, judge_local.py, report.py)
                that runs the same scenarios through an in-process runner and
                scores them with a local LLM judge. No deployment required.

The reusable, unit-tested logic lives in ``harness/``; the top-level scripts are
thin CLIs that wire it to cloud services.
"""
