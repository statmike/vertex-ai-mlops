import asyncio
import logging
import os
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

TOOL_MODEL = os.getenv('TOOL_MODEL', 'gemini-2.5-flash')
TOOL_MODEL_LOCATION = os.getenv('TOOL_MODEL_LOCATION', '')

# Retry configuration
MAX_RETRIES = 10
INITIAL_BACKOFF = 2.0  # seconds
BACKOFF_MULTIPLIER = 2.0
MAX_BACKOFF = 120.0  # seconds


def _get_client() -> genai.Client:
    """Create a genai Client, using TOOL_MODEL_LOCATION if set."""
    if TOOL_MODEL_LOCATION:
        return genai.Client(
            vertexai=True,
            project=os.getenv('GOOGLE_CLOUD_PROJECT'),
            location=TOOL_MODEL_LOCATION,
        )
    return genai.Client()


async def generate_content(
    contents: list,
    model: str | None = None,
) -> genai.types.GenerateContentResponse:
    """
    Call Gemini generate_content with automatic retry on 429 (rate limit) errors.

    Uses exponential backoff: 2s, 4s, 8s, 16s, 32s (capped at 60s).
    Uses TOOL_MODEL_LOCATION for the API endpoint if set (e.g., 'global' for preview models).

    Args:
        contents: List of content parts to send to Gemini.
        model: Model name. Defaults to TOOL_MODEL from env.

    Returns:
        The Gemini GenerateContentResponse.

    Raises:
        Exception: If all retries are exhausted or a non-retryable error occurs.
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
            return response

        except Exception as e:
            error_str = str(e)
            is_429 = '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str

            if is_429 and attempt < MAX_RETRIES:
                logger.warning(
                    f"Gemini 429 rate limit (attempt {attempt}/{MAX_RETRIES}), "
                    f"retrying in {backoff:.1f}s..."
                )
                await asyncio.sleep(backoff)
                backoff = min(backoff * BACKOFF_MULTIPLIER, MAX_BACKOFF)
                continue

            # Non-retryable error or retries exhausted
            raise
