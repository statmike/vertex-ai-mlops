import os
from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.agents.loop_agent import LoopAgent
from google.adk.agents.llm_agent import Agent
from root_agent.config import MODEL

# Import the native Agent objects directly from the sub-modules
from root_agent.sub_agents.extractor_agent.agent import extractor
from root_agent.sub_agents.qualification_agent.agent import qualification
from root_agent.sub_agents.answering_agent.agent import answering
from root_agent.sub_agents.critique_agent.agent import critique
from root_agent.sub_agents.writer_agent.agent import writer
from root_agent.prompts import ROOT_AGENT_INSTRUCTION

# Define a loop between answering and critique
answering_critique_loop = LoopAgent(
    name="answering_critique_loop",
    description="Loop answering and critique until questions pass quality check, or reach max iterations.",
    sub_agents=[answering, critique],
    max_iterations=2
)

# The rigid workflow pipeline
rfi_workflow_pipeline = SequentialAgent(
    name="rfi_workflow_pipeline",
    description="Linear pipeline that parses RFI documents, qualifies them, answers them, and critiques them in sequence.",
    sub_agents=[extractor, qualification, answering_critique_loop, writer]
)


# The conversational Root
root_agent = Agent(
    name="rfi_steering_agent",
    model=MODEL,
    description="You are an expert orchestrator for automating RFI responses. Your job is to greet users and hand it over to the the rfi_workflow_pipeline sub-agent when they provide input files.",
    instruction=ROOT_AGENT_INSTRUCTION,
    sub_agents=[rfi_workflow_pipeline]
)
