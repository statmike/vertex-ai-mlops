from google.adk import agents
from google.adk.tools import agent_tool
from . import tools
from . import prompts
from . import callbacks

comparison_insights_agent = agents.Agent(
    name = "comparison_insights_agent",
    model = "gemini-2.0-flash",
    description = "Compares formatting differences between an original document and a vendor template.",
    global_instruction = prompts.global_instructions,
    instruction = prompts.comparison_insights_agent_instructions,
)

classification_insights_agent = agents.Agent(
    name = "classification_insights_agent",
    model = "gemini-2.0-flash",
    description = "Generates a document comparison tables and summarizes it for the user and includes a final determination of classification.",
    global_instruction = prompts.global_instructions,
    instruction = prompts.classification_insights_agent_instructions,
    tools = tools.DOCUMENT_CLASSIFICATION_TOOLS
)

extraction_insights_agent = agents.Agent(
    name = "extraction_insights_agent",
    model = "gemini-2.0-flash",
    description = "Generates and summarizes extracted document content and answers user questions about it.",
    global_instruction = prompts.global_instructions,
    instruction = prompts.extraction_insights_agent_instructions,
)

root_agent = agents.Agent(
    name = "document_agent",
    model = "gemini-2.0-flash",
    description = 'The primary agent that processes document related requests.',
    global_instruction = prompts.global_instructions,
    instruction = prompts.root_agent_instructions,
    sub_agents = [
        comparison_insights_agent,
        classification_insights_agent,
        extraction_insights_agent,
    ],
    tools = tools.DOCUMENT_PROCESSING_TOOLS,
    before_agent_callback = callbacks.before_agent_get_user_file
)

