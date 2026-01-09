# BigQuery Agent Analytics Plugin
# Shared analytics logging for all ADK agents in concept-bq
#
# Usage in any agent's agent.py:
#   from bq_plugin import bq_analytics_plugin
#   from google.adk.apps import App
#   app = App(name="agent_name", root_agent=root_agent, plugins=[bq_analytics_plugin])

from .bq_plugin import bq_analytics_plugin
