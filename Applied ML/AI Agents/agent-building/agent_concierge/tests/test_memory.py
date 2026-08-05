"""Tests for the Memory Bank callback.

The callback must persist a finished turn when a memory service is present, and
degrade to a silent no-op when one isn't (local/offline), so the agent behaves
identically either way.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from agent_concierge.utils import add_session_to_memory


@pytest.mark.asyncio
async def test_persists_when_memory_service_present():
    ctx = MagicMock()
    ctx.add_session_to_memory = AsyncMock()

    result = await add_session_to_memory(ctx)

    ctx.add_session_to_memory.assert_awaited_once()
    assert result is None


@pytest.mark.asyncio
async def test_noop_when_no_memory_service():
    ctx = MagicMock()
    ctx.add_session_to_memory = AsyncMock(side_effect=ValueError("no memory service"))

    # Must not raise — swallowed so the turn still completes.
    assert await add_session_to_memory(ctx) is None
