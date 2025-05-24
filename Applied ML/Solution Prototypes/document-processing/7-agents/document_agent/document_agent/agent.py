from google.adk import agents
from .tools import DOCUMENT_PROCESSING_TOOLS
from . import prompts

classification_insights_agent = agents.Agent(
    name = "classification_reporter_agent",
    model = "gemini-2.0-flash",
    description = "Interprets and reports document classification results from a Markdown table.",
    global_instruction = prompts.global_instructions,
    instruction = prompts.classification_insights_agent_instructions,
    #allow_transfer = False,
    # tools=[] # This agent is primarily for LLM-based interpretation and formatting
)

extraction_insights_agent = agents.Agent(
    name = "extraction_insights_agent",
    model = "gemini-2.0-flash",
    description = "Summarizes extracted document content and answers user questions about it.",
    global_instruction = prompts.global_instructions,
    instruction = prompts.extraction_insights_agent_instructions,
    #allow_transfer = False,
    # tools = [] # This agent might not need specific ADK tools if it's purely LLM-based for this task
)

root_agent = agents.Agent(
    name = "document_agent",
    model = "gemini-2.0-flash",
    description = 'The primary agent that processes document related requests.',
    global_instruction = prompts.global_instructions,
    instruction = prompts.root_agent_instructions,
    sub_agents = [
        extraction_insights_agent,
        classification_insights_agent
    ],
    tools = DOCUMENT_PROCESSING_TOOLS
)

