"""Agent Runtime entrypoint for the discovery agent — native A2A (object mode).

The deployable ``A2aAgent`` lives in ``agent_discovery.a2a_app``, not here. Object
mode cloudpickles the agent *by reference*, so every function it captures (the
card, the executor builder) must resolve on the remote — and only the
``agent_discovery`` package is shipped as an extra package, not ``deploy``. This
module is a thin re-export so ``deploy.py`` can load ``app`` by its configured
entrypoint the same way it does for the source-mode concierge. See
``agent_discovery/a2a_app.py`` for the wiring and the ADK 2.x rationale.
"""

from agent_discovery.a2a_app import app  # noqa: F401
