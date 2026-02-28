import os

# Model and location configuration (read early, before ADK imports).
# ADK uses GOOGLE_CLOUD_LOCATION to determine the Vertex AI API endpoint,
# so AGENT_MODEL_LOCATION overrides it if set.
AGENT_MODEL = os.getenv("AGENT_MODEL", "gemini-2.5-flash")
AGENT_MODEL_LOCATION = os.getenv("AGENT_MODEL_LOCATION", "")
if AGENT_MODEL_LOCATION:
    os.environ["GOOGLE_CLOUD_LOCATION"] = AGENT_MODEL_LOCATION

from google.adk import agents  # noqa: E402

from . import prompts, tools  # noqa: E402

root_agent = agents.Agent(
    name="agent_graph_qa",
    model=AGENT_MODEL,
    description="A Q&A agent that answers questions about diagram graphs extracted by agent_image_to_graph. Can load results from disk or receive them via session state from the parent agent.",
    global_instruction=prompts.global_instructions,
    instruction=prompts.agent_instructions,
    tools=tools.TOOLS,
)
