"""Helpers for consuming the Discovery agent over A2A.

The concierge talks to Discovery as a remote agent. The agent card lives at a
well-known path under the server's base URL; we import that path constant from
the a2a SDK rather than hardcoding the suffix, so we never drift if it changes.
"""

from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH

from config import discovery_a2a_base_url


def discovery_agent_card_url() -> str:
    """Full URL of the discovery agent's A2A card (base + well-known path)."""
    return f"{discovery_a2a_base_url()}/{AGENT_CARD_WELL_KNOWN_PATH.lstrip('/')}"
