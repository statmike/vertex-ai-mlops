"""Agent Runtime entrypoint for the discovery agent.

Discovery is the independently-deployable half of the system: it ships on its own
lifecycle and the concierge reaches it over A2A. Agent Runtime auto-generates and
hosts an A2A agent card for any deployed ADK agent, so once this is live the
concierge points ``DISCOVERY_A2A_URL`` at the Runtime endpoint and the same
``RemoteA2aAgent`` wiring keeps working — now over an authenticated hop.

We wrap the raw ``root_agent`` (Claude on Vertex); it has no plugins of its own.
"""

from vertexai.agent_engines import AdkApp

from agent_discovery.agent import root_agent

app = AdkApp(agent=root_agent, enable_tracing=True)
