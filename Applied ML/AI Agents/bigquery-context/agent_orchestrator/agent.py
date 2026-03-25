"""Root orchestrator using SequentialAgent → ParallelAgent → compare agent.

Workflow:
1. ParallelAgent runs all three discovery approaches concurrently
2. Compare agent reads all three results from state and synthesizes
"""

from google.adk import agents

from config import AGENT_MODEL
from agent_bq_tools.agent import root_agent as bq_tools_agent
from agent_catalog_search.agent import root_agent as catalog_search_agent
from agent_knowledge_context.agent import root_agent as knowledge_context_agent
from . import prompts


# Step 1: Run all three discovery approaches in parallel
parallel_discovery = agents.ParallelAgent(
    name="parallel_discovery",
    description="Runs all three table discovery approaches concurrently.",
    sub_agents=[
        bq_tools_agent,
        catalog_search_agent,
        knowledge_context_agent,
    ],
)

# Step 2: Compare results from all three approaches
compare_agent = agents.Agent(
    name="compare_results",
    model=AGENT_MODEL,
    description="Compares and synthesizes results from all three discovery approaches.",
    global_instruction=prompts.global_instructions,
    instruction=prompts.compare_agent_instructions,
)

# Root: sequential pipeline
root_agent = agents.SequentialAgent(
    name="agent_orchestrator",
    description=(
        "Orchestrates three parallel BigQuery table discovery approaches "
        "(BQ tools, Dataplex catalog search, Knowledge Context API) and "
        "compares their results."
    ),
    sub_agents=[
        parallel_discovery,
        compare_agent,
    ],
)
