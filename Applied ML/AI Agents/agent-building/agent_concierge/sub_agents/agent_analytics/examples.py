"""Example Store wiring for the analytics agent (Build — few-shot retrieval).

The [Example Store](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/example-stores/overview)
is a managed, semantically-searchable store of curated ``(question -> ideal
answer)`` examples. Instead of hard-coding a fixed few-shot block in the prompt,
the agent retrieves the *few most similar* examples for each incoming question
and injects them dynamically — so a "revenue last quarter" question is steered by
past revenue examples, a "top products" question by product examples.

ADK does the retrieval for us: ``VertexAiExampleStore`` (a ``BaseExampleProvider``)
is wrapped in an ``ExampleTool`` that, on every turn, searches the store with the
user's question and prepends the matches to the LLM request. The seed examples
live in ``scripts/setup.py`` (provisioning, not agent code).

Resolving the store: Vertex assigns a numeric resource id at creation (a custom
id is not honored), so we can't reconstruct the resource name from config. Two
paths, in priority order: (1) if ``EXAMPLE_STORE_NAME`` (a full resource name) is
set, use it directly — no network call at import; (2) otherwise list the region's
stores and match on ``EXAMPLE_STORE_DISPLAY_NAME``, the deterministic name setup
gives it. If neither resolves, the tool is ``None`` and the agent runs unsteered.
"""

from __future__ import annotations

import logging

from config import (
    EXAMPLE_STORE_DISPLAY_NAME,
    EXAMPLE_STORE_LOCATION,
    EXAMPLE_STORE_NAME,
    GOOGLE_CLOUD_PROJECT,
)

logger = logging.getLogger(__name__)

# The feature is even *configurable* only with a project and some way to identify
# the store (an explicit resource name, or a display name to search for).
_CONFIGURED = bool(
    GOOGLE_CLOUD_PROJECT and (EXAMPLE_STORE_NAME or EXAMPLE_STORE_DISPLAY_NAME)
)


def _resolve_store_resource_name() -> str | None:
    """Return the store's full resource name, or None if it can't be resolved.

    Prefers the explicit ``EXAMPLE_STORE_NAME`` override (no network call);
    otherwise lists the region's stores and matches on display name. Any failure
    (SDK missing, no credentials, store absent) resolves to None so the agent
    degrades gracefully to no example steering rather than failing to import.
    """
    if EXAMPLE_STORE_NAME:
        return EXAMPLE_STORE_NAME
    try:
        import vertexai
        from vertexai.preview import example_stores

        vertexai.init(project=GOOGLE_CLOUD_PROJECT, location=EXAMPLE_STORE_LOCATION)
        for store in example_stores.ExampleStore.list():
            if _display_name_of(store) == EXAMPLE_STORE_DISPLAY_NAME:
                return store.resource_name
    except Exception as e:  # noqa: BLE001 — resolution is best-effort
        logger.info("Could not resolve Example Store by display name: %s", e)
        return None
    logger.info(
        "No Example Store with display name %r found in %s.",
        EXAMPLE_STORE_DISPLAY_NAME,
        EXAMPLE_STORE_LOCATION,
    )
    return None


def _display_name_of(store) -> str | None:
    """Read a store's display name across SDK shapes (attr or backing resource)."""
    name = getattr(store, "display_name", None)
    if name:
        return name
    gca = getattr(store, "_gca_resource", None)
    return getattr(gca, "display_name", None)


def _build_example_tool(resource_name: str):
    """Build the ExampleTool backed by the Vertex Example Store.

    Imported lazily so this module is import-safe (and testable) without the ADK
    example extras installed or credentials present.
    """
    from google.adk.examples import VertexAiExampleStore
    from google.adk.tools.example_tool import ExampleTool

    provider = VertexAiExampleStore(resource_name)
    return ExampleTool(examples=provider)


# Exported to agent.py. None when the store can't be resolved, so the agent's
# tools list simply omits it and behaves identically to a build without a store.
_resolved_name = _resolve_store_resource_name() if _CONFIGURED else None
example_tool = _build_example_tool(_resolved_name) if _resolved_name else None

if example_tool is None:
    logger.info(
        "Example Store disabled (set GOOGLE_CLOUD_PROJECT + a provisioned store; "
        "run scripts/setup.py, or set EXAMPLE_STORE_NAME to the resource name)."
    )
