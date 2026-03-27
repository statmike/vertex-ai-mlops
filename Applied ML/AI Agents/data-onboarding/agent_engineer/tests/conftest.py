"""Shared fixtures for agent_engineer tests.

Mocks the geminidataanalytics SDK so tests can run without it installed.
"""

import sys
from unittest.mock import MagicMock

import pytest

# Mock the geminidataanalytics SDK before any agent_engineer imports
_mock_gda = MagicMock()
sys.modules.setdefault("google.cloud.geminidataanalytics_v1alpha", _mock_gda)


@pytest.fixture
def mock_tool_context():
    """A MagicMock that behaves like tools.ToolContext with a dict state."""
    ctx = MagicMock()
    ctx.state = {}
    return ctx
