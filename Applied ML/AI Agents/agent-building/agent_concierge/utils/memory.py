"""Memory Bank wiring for the concierge (Scale pillar).

Agent Runtime gives every deployed ADK agent a managed **Memory Bank** for free:
``AdkApp`` uses ``VertexAiMemoryBankService`` as its default memory service once
deployed (locally it falls back to in-memory). But two pieces are the agent's job:

    Retrieval  — ``PreloadMemoryTool`` loads relevant memories into the prompt at
                 the start of each turn (baseline user context); ``LoadMemoryTool``
                 lets the model pull more on demand.
    Generation — memories are NOT written automatically. The agent must call
                 ``add_session_to_memory`` after a turn to distill it into memory.

Both are exposed here so ``agent.py`` just spreads them onto the root agent.
"""

from __future__ import annotations

import contextlib

from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.load_memory_tool import LoadMemoryTool
from google.adk.tools.preload_memory_tool import PreloadMemoryTool

# Tools that surface stored memories to the model. Add to the root agent's tools.
MEMORY_TOOLS = [PreloadMemoryTool(), LoadMemoryTool()]


async def add_session_to_memory(callback_context: CallbackContext) -> None:
    """after_agent_callback that distills the finished turn into Memory Bank.

    Non-blocking: it triggers generation and returns. No-op (best effort) when no
    memory service is configured — e.g. running offline in tests — so the agent
    behaves identically whether or not Memory Bank is present.
    """
    # No memory service wired (local/offline) — nothing to persist.
    with contextlib.suppress(ValueError, AttributeError):
        await callback_context.add_session_to_memory()
    return None
