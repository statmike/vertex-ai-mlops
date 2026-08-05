"""Agent Runtime entrypoint for the concierge.

Agent Runtime needs an ``AdkApp`` (not a raw ADK ``Agent``) as its entrypoint so
it can register ``stream_query``, ``create_session``, the Memory Bank methods,
etc. as API endpoints.

We wrap the concierge's ADK ``App`` — not just its ``root_agent`` — so the
BigQuery observability plugin travels with it. Memory Bank needs no builder here:
once deployed, ``AdkApp`` uses ``VertexAiMemoryBankService`` on this same Runtime
instance by default. Sessions are the managed cloud service, also automatic.
"""

from vertexai.agent_engines import AdkApp

from agent_concierge.agent import app as concierge_app

app = AdkApp(app=concierge_app, enable_tracing=True)
