"""Gemini API client with retry and token tracking."""

import asyncio
import logging
import os

from google import genai

from agent_orchestrator.config import TOOL_MODEL, TOOL_MODEL_LOCATION

logger = logging.getLogger(__name__)

MAX_RETRIES = 10
INITIAL_BACKOFF = 2.0
BACKOFF_MULTIPLIER = 2.0
MAX_BACKOFF = 120.0


def _get_client() -> genai.Client:
    """Create a genai Client, using TOOL_MODEL_LOCATION if set."""
    if TOOL_MODEL_LOCATION:
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        if not project:
            raise RuntimeError(
                "GOOGLE_CLOUD_PROJECT is not set. "
                "Required when TOOL_MODEL_LOCATION is configured."
            )
        return genai.Client(
            vertexai=True,
            project=project,
            location=TOOL_MODEL_LOCATION,
        )
    return genai.Client()


async def generate_content(
    contents: list,
    model: str | None = None,
    tool_context=None,
    tool_name: str | None = None,
) -> genai.types.GenerateContentResponse:
    """Call Gemini with automatic retry on transient errors (429, 499).

    Args:
        contents: Content parts to send.
        model: Model name (defaults to TOOL_MODEL).
        tool_context: Optional ADK ToolContext for token tracking.
        tool_name: Label for tracking.

    Returns:
        The Gemini response.
    """
    model = model or TOOL_MODEL
    client = _get_client()
    backoff = INITIAL_BACKOFF

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=model,
                contents=contents,
            )

            if tool_context is not None:
                try:
                    usage = response.usage_metadata
                    entry = {
                        "tool": tool_name or "unknown",
                        "model": response.model_version or model or TOOL_MODEL,
                        "prompt_tokens": usage.prompt_token_count if usage else 0,
                        "completion_tokens": usage.candidates_token_count if usage else 0,
                        "total_tokens": usage.total_token_count if usage else 0,
                    }
                    prev = list(tool_context.state.get("tool_llm_usage", []))
                    prev.append(entry)
                    tool_context.state["tool_llm_usage"] = prev
                except Exception:
                    pass

            return response

        except Exception as e:
            error_str = str(e)
            is_retryable = (
                "429" in error_str
                or "RESOURCE_EXHAUSTED" in error_str
                or "499" in error_str
                or "CANCELLED" in error_str
            )

            if is_retryable and attempt < MAX_RETRIES:
                logger.warning(
                    f"Gemini transient error (attempt {attempt}/{MAX_RETRIES}), "
                    f"retrying in {backoff:.1f}s..."
                )
                await asyncio.sleep(backoff)
                backoff = min(backoff * BACKOFF_MULTIPLIER, MAX_BACKOFF)
                continue

            raise
