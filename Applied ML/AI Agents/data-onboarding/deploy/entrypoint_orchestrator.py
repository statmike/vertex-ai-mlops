"""Agent Engine entrypoint for the orchestrator agent.

Agent Engine requires an AdkApp instance (not a raw ADK Agent) as the
entrypoint object so it can register stream_query, create_session, etc.
"""

from vertexai.agent_engines import AdkApp

from agent_orchestrator.agent import root_agent

app = AdkApp(agent=root_agent, enable_tracing=True)
