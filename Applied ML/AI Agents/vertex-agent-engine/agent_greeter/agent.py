"""Greeter agent — handles greetings and introductions.

This sub-agent demonstrates a simple agent with a tool that provides
personalized greetings based on the time of day.
"""

from google.adk.agents import Agent

from config import TOOL_MODEL  # sub-agents with tools use the tool model

from .tools import get_greeting


greeter_agent = Agent(
    model=TOOL_MODEL,
    name="agent_greeter",
    description="Greets users and introduces what the system can do.",
    instruction="""You are a friendly greeter. When a user says hello or asks what
    you can do:

    1. Use the **get_greeting** tool to get a time-appropriate greeting
    2. Welcome them warmly
    3. Explain that you're part of a multi-agent system with two capabilities:
       - Looking up facts about the solar system
       - Performing calculations

    Keep it brief and friendly.""",
    tools=[get_greeting],
)
