"""Shared configuration loaded from environment variables.

All settings are read from the .env file at the project root.
Each variable has a sensible default so the project works out of the box.
"""

import os
from pathlib import Path

import dotenv

# Load .env from project root
dotenv.load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

# --- Google Cloud ---
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

# --- Agent model (reasoning and routing) ---
AGENT_MODEL = os.getenv("AGENT_MODEL", "gemini-3-flash-preview")
AGENT_MODEL_LOCATION = os.getenv("AGENT_MODEL_LOCATION", "global")

# --- Tool model (tool-calling agents — can differ for cost/latency tradeoffs) ---
TOOL_MODEL = os.getenv("TOOL_MODEL", "gemini-3-flash-preview")
TOOL_MODEL_LOCATION = os.getenv("TOOL_MODEL_LOCATION", "global")
