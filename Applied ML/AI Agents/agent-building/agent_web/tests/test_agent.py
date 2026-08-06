"""Tests for the web-grounding agent wiring (offline).

Pins the contract that this agent carries exactly the built-in google_search
grounding tool and nothing else (grounding tools can't be mixed with function
tools in one agent).
"""

from google.adk.tools import google_search
from google.adk.tools.google_search_tool import GoogleSearchTool

from agent_web.agent import root_agent


def test_agent_carries_only_google_search():
    assert root_agent.tools == [google_search]
    assert all(isinstance(t, GoogleSearchTool) for t in root_agent.tools)


def test_agent_identity():
    import config

    assert root_agent.name == "agent_web"
    assert root_agent.model == config.WEB_MODEL
