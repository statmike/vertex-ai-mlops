"""Shared utilities for data-onboarding tools."""

import hashlib
import logging
import uuid


def log_tool_error(tool_name: str, error: Exception, context: str = "") -> str:
    """Log full traceback and return a sanitized error message for the agent."""
    logger = logging.getLogger(f"data_onboarding.tools.{tool_name}")
    ctx = f" ({context})" if context else ""
    logger.exception(f"Error in {tool_name}{ctx}")
    return f"Error in {tool_name}: {error}"


def compute_hash(data: bytes) -> str:
    """Compute SHA-256 hash of byte data."""
    return hashlib.sha256(data).hexdigest()


def generate_source_id(uri: str) -> str:
    """Generate a deterministic source ID from a URI.

    Uses a UUID5 based on the URI so the same source always gets the same ID.
    """
    return str(uuid.uuid5(uuid.NAMESPACE_URL, uri))
