from google.adk import agents

from agent_orchestrator.config import AGENT_MODEL_INSTANCE as AGENT_MODEL

from . import prompts, tools
from .catalog import _catalog_summary
from .tools.callback_rerank import rerank_and_transfer


def _build_instruction():
    """Build the agent instruction with pre-loaded catalog data."""
    base = prompts.agent_instructions
    if _catalog_summary:
        return (
            f"{base}\n\n"
            f"## Pre-loaded Data Catalog\n\n"
            f"The following datasets and tables are available. Use these exact "
            f"`project.dataset.table` references when calling tools.\n\n"
            f"{_catalog_summary}"
        )
    return base


root_agent = agents.Agent(
    name="agent_context",
    model=AGENT_MODEL,
    description="Discovers relevant BigQuery datasets and tables for a user's question by querying metadata catalogs and table documentation.",
    global_instruction=prompts.global_instructions,
    instruction=_build_instruction(),
    tools=tools.TOOLS,
    before_agent_callback=rerank_and_transfer,
    disallow_transfer_to_peers=False,
)
