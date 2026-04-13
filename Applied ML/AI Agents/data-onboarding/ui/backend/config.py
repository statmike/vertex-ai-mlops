"""Configuration from environment variables."""

import os

from dotenv import load_dotenv

load_dotenv()

GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
AGENT_ENGINE_RESOURCE_ID = os.getenv("AGENT_ENGINE_RESOURCE_ID", "")
AGENT_MODE = os.getenv("AGENT_MODE", "agent_engine")  # "local" or "agent_engine"
VOICE_MODEL = os.getenv("VOICE_MODEL", "gemini-live-2.5-flash-native-audio")
CHAT_SCOPE = os.getenv("CHAT_SCOPE", "")

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))


def get_resource_name() -> str:
    """Full Agent Engine resource name."""
    if "/" in AGENT_ENGINE_RESOURCE_ID:
        return AGENT_ENGINE_RESOURCE_ID
    return (
        f"projects/{GOOGLE_CLOUD_PROJECT}"
        f"/locations/{GOOGLE_CLOUD_LOCATION}"
        f"/reasoningEngines/{AGENT_ENGINE_RESOURCE_ID}"
    )
