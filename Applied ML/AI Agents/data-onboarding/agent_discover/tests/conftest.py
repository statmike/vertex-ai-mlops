"""Shared fixtures for agent_discover tests."""

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_tool_context():
    """A MagicMock that behaves like tools.ToolContext with a dict state."""
    ctx = MagicMock()
    ctx.state = {}
    return ctx
