import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from google.adk import agents
from .tools import DOCUMENT_PROCESSING_TOOLS
from . import prompts

root_agent = agents.Agent(
    name = "document_agent",
    model = "gemini-2.0-flash",
    description = 'The primary agent that processes document related requests.',
    global_instruction = prompts.global_instructions,
    instruction = prompts.root_agent_instructions, 
    tools = DOCUMENT_PROCESSING_TOOLS
)
logging.info('[AGENT] Root agent successfully created.')