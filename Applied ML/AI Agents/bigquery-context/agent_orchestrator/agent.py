"""Root orchestrator using SequentialAgent → ParallelAgent → compare agent.

Workflow:
1. ParallelAgent runs all five discovery approaches concurrently
2. Compare agent reads all five results from state and synthesizes
"""

from google.adk import agents

from agent_bq_tools.agent import root_agent as bq_tools_agent
from agent_context_prefilter.agent import root_agent as context_prefilter_agent
from agent_dataplex_context.agent import root_agent as dataplex_context_agent
from agent_dataplex_search.agent import root_agent as dataplex_search_agent
from agent_semantic_context.agent import root_agent as semantic_context_agent
from config import AGENT_MODEL

from . import prompts
from .callback_build_comparison import build_comparison

# Step 1: Run all five discovery approaches in parallel
parallel_discovery = agents.ParallelAgent(
    name="parallel_discovery",
    description="Runs all five table discovery approaches concurrently.",
    sub_agents=[
        bq_tools_agent,
        dataplex_search_agent,
        dataplex_context_agent,
        context_prefilter_agent,
        semantic_context_agent,
    ],
)

# Step 2: Compare results from all five approaches
compare_agent = agents.Agent(
    name="compare_results",
    model=AGENT_MODEL,
    description="Compares and synthesizes results from all five discovery approaches.",
    global_instruction=prompts.global_instructions,
    instruction=prompts.compare_agent_instructions,
    before_agent_callback=build_comparison,
)

# Root: sequential pipeline
root_agent = agents.SequentialAgent(
    name="agent_orchestrator",
    description=(
        "Orchestrates five parallel BigQuery table discovery approaches "
        "(BQ tools, Dataplex search, Dataplex context, context pre-filter, "
        "semantic context) and compares their results."
    ),
    sub_agents=[
        parallel_discovery,
        compare_agent,
    ],
)
