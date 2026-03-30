"""Agent Engine entrypoint — wraps the root agent in an AdkApp.

Agent Engine requires an AdkApp instance (not a raw ADK Agent) as the
entrypoint. The AdkApp wrapper registers the standard API methods
(stream_query, create_session, etc.) that Agent Engine exposes as
HTTP endpoints.

This thin wrapper keeps the deployment concern separate from the agent
code — agent_router/agent.py stays unchanged whether you run locally
with `adk web` or deploy to Agent Engine.
"""

from vertexai.agent_engines import AdkApp

from agent_router.agent import root_agent

app = AdkApp(agent=root_agent, enable_tracing=True)
