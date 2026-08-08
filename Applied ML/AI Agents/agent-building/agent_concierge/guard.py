"""Model Armor guardrails — the Govern pillar, at the model boundary.

[Model Armor](https://docs.cloud.google.com/security-command-center/docs/model-armor-overview)
screens what goes *into* and comes *out of* the model against a policy template:
prompt-injection / jailbreak attempts, malicious URLs, and responsible-AI harms
(hate, harassment, sexual, dangerous). The template is provisioned once in
`scripts/setup.py`; here we enforce it on every turn.

**Why callbacks, not a Plugin.** ADK's plugin hooks are the natural home for a
cross-cutting guard, but `adk web` (the local dev UI this project runs on) does
not apply an `App`'s plugins to the agent it serves. Agent-level
`before_model_callback` / `after_model_callback` run in *both* `adk web` and a
deployed `AdkApp`, so the guard is wired there and is active everywhere.

- `before_model_callback` sanitizes the newest user prompt. On a match it returns
  a canned `LlmResponse`, which short-circuits the model call — the prompt never
  reaches the LLM.
- `after_model_callback` sanitizes the model's answer. On a match it replaces the
  content with a safe refusal.

Fully guarded: with no `GOOGLE_CLOUD_PROJECT` or an empty `MODEL_ARMOR_TEMPLATE`,
the exported callbacks are `None` and the agent runs exactly as before. A Model
Armor API error is logged and *fails open* (the turn proceeds) — a telemetry/guard
outage must not take the assistant down.
"""

from __future__ import annotations

import logging

from config import (
    GOOGLE_CLOUD_PROJECT,
    MODEL_ARMOR_LOCATION,
    MODEL_ARMOR_TEMPLATE,
)

logger = logging.getLogger(__name__)

# What the user sees when the guard blocks a turn. Deliberately generic — it must
# not echo the flagged content or reveal which filter tripped.
_BLOCKED_PROMPT_MESSAGE = (
    "I can't help with that request. Please rephrase and try again."
)
_BLOCKED_RESPONSE_MESSAGE = (
    "I'm not able to share that response. Please try asking a different way."
)

# The guard is active only when both a project and a template name are configured.
_ENABLED = bool(GOOGLE_CLOUD_PROJECT and MODEL_ARMOR_TEMPLATE)

_client = None  # lazily built regional Model Armor client (see _get_client)


def _template_path() -> str:
    return (
        f"projects/{GOOGLE_CLOUD_PROJECT}/locations/{MODEL_ARMOR_LOCATION}"
        f"/templates/{MODEL_ARMOR_TEMPLATE}"
    )


def _get_client():
    """Build (once) a Model Armor client pinned to the template's region.

    Model Armor is regional and served from a per-region REST endpoint
    (``modelarmor.<location>.rep.googleapis.com``); the global endpoint does not
    serve it. Built lazily so importing this module never makes a network call.
    """
    global _client
    if _client is None:
        from google.api_core.client_options import ClientOptions
        from google.cloud import modelarmor_v1

        _client = modelarmor_v1.ModelArmorClient(
            transport="rest",
            client_options=ClientOptions(
                api_endpoint=f"modelarmor.{MODEL_ARMOR_LOCATION}.rep.googleapis.com"
            ),
        )
    return _client


def _latest_user_text(llm_request) -> str:
    """Concatenate the text parts of the newest user message in the request."""
    for content in reversed(llm_request.contents or []):
        if content.role == "user":
            return "".join(p.text for p in (content.parts or []) if getattr(p, "text", None))
    return ""


def _response_text(llm_response) -> str:
    """Concatenate the text parts of a model response."""
    content = getattr(llm_response, "content", None)
    if content is None:
        return ""
    return "".join(p.text for p in (content.parts or []) if getattr(p, "text", None))


def _is_match(sanitization_result) -> bool:
    """True when Model Armor flagged the content (any filter matched)."""
    from google.cloud import modelarmor_v1

    return (
        sanitization_result.filter_match_state
        == modelarmor_v1.FilterMatchState.MATCH_FOUND
    )


def before_model_callback(callback_context, llm_request):
    """Screen the user prompt; short-circuit with a refusal if Model Armor blocks it.

    Returns an ``LlmResponse`` (which ADK sends in place of calling the model) on a
    match, or ``None`` to let the request proceed unchanged.
    """
    prompt = _latest_user_text(llm_request)
    if not prompt.strip():
        return None
    try:
        from google.cloud import modelarmor_v1

        result = _get_client().sanitize_user_prompt(
            request=modelarmor_v1.SanitizeUserPromptRequest(
                name=_template_path(),
                user_prompt_data=modelarmor_v1.DataItem(text=prompt),
            )
        )
    except Exception as e:  # noqa: BLE001 — a guard outage must fail open, not crash
        logger.warning(f"Model Armor prompt screen failed ({e}); allowing turn.")
        return None

    if _is_match(result.sanitization_result):
        logger.info("Model Armor blocked a user prompt.")
        return _refusal_response(_BLOCKED_PROMPT_MESSAGE)
    return None


def after_model_callback(callback_context, llm_response):
    """Screen the model's answer; replace it with a refusal if Model Armor blocks it.

    Returns a replacement ``LlmResponse`` on a match, or ``None`` to keep the
    original response. Streaming partials and empty/non-text responses are skipped.
    """
    if getattr(llm_response, "partial", False):
        return None  # sanitize the assembled final response, not each chunk
    answer = _response_text(llm_response)
    if not answer.strip():
        return None
    try:
        from google.cloud import modelarmor_v1

        result = _get_client().sanitize_model_response(
            request=modelarmor_v1.SanitizeModelResponseRequest(
                name=_template_path(),
                model_response_data=modelarmor_v1.DataItem(text=answer),
            )
        )
    except Exception as e:  # noqa: BLE001 — fail open
        logger.warning(f"Model Armor response screen failed ({e}); allowing turn.")
        return None

    if _is_match(result.sanitization_result):
        logger.info("Model Armor blocked a model response.")
        return _refusal_response(_BLOCKED_RESPONSE_MESSAGE)
    return None


def _refusal_response(message: str):
    """Build an LlmResponse carrying a safe refusal message."""
    from google.adk.models.llm_response import LlmResponse
    from google.genai import types as genai_types

    return LlmResponse(
        content=genai_types.Content(role="model", parts=[genai_types.Part(text=message)])
    )


# Exported to agent.py. None when the guard is disabled, so the agent wires
# nothing and behaves identically to a build without Model Armor.
model_armor_before_callback = before_model_callback if _ENABLED else None
model_armor_after_callback = after_model_callback if _ENABLED else None

if not _ENABLED:
    logger.info(
        "Model Armor guard disabled (set GOOGLE_CLOUD_PROJECT + MODEL_ARMOR_TEMPLATE)."
    )
