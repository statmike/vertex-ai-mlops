"""Tests for the concierge's A2A card resolution.

Kept import-light on purpose: importing agent_concierge.agent would pull in the
ADK Claude client and the BigQuery telemetry plugin. Here we pin the URL-building
contract for the local case, the resource-name parsing for the deployed case, and
the local-vs-deployed dispatch.
"""

from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH

from agent_concierge.utils.a2a import (
    DISCOVERY_A2A_CARD_ENV,
    _location_from_resource_name,
    _resource_name_from_a2a_url,
    discovery_agent_card,
)


def test_local_returns_well_known_url(monkeypatch):
    """Local discovery: a well-known card URL string RemoteA2aAgent resolves."""
    import config

    monkeypatch.delenv(DISCOVERY_A2A_CARD_ENV, raising=False)
    monkeypatch.setattr(config, "DISCOVERY_A2A_URL", "", raising=False)
    monkeypatch.setattr(config, "DISCOVERY_A2A_HOST", "localhost", raising=False)
    monkeypatch.setattr(config, "DISCOVERY_A2A_PORT", 8001, raising=False)

    card = discovery_agent_card()
    assert isinstance(card, str)
    assert card.startswith("http://localhost:8001/")
    assert card.endswith(AGENT_CARD_WELL_KNOWN_PATH.lstrip("/"))
    assert "//.well-known" not in card  # no double slash from the join


def test_baked_env_card_takes_priority(monkeypatch):
    """Deployed concierge: DISCOVERY_A2A_CARD is parsed, with no control-plane call.

    The baked card wins even when the base URL is a deployed Runtime endpoint —
    proving the deployed concierge never needs aiplatform.reasoningEngines.get.
    """
    import config

    # A minimal but valid AgentCard JSON (camelCase, as protobuf JSON emits).
    card_json = (
        '{"name": "agent_discovery", "description": "baked", '
        '"supportedInterfaces": [{"url": "https://x-aiplatform.googleapis.com/a2a", '
        '"protocolBinding": "HTTP+JSON"}]}'
    )
    monkeypatch.setenv(DISCOVERY_A2A_CARD_ENV, card_json)
    # Point at a deployed URL to prove the env var short-circuits the resource read.
    monkeypatch.setattr(
        config,
        "DISCOVERY_A2A_URL",
        "https://us-central1-aiplatform.googleapis.com/v1beta1/projects/1/"
        "locations/us-central1/reasoningEngines/123/a2a",
        raising=False,
    )

    card = discovery_agent_card()
    # Not a string (that's the local well-known path); it's a parsed AgentCard.
    assert not isinstance(card, str)
    assert card.name == "agent_discovery"


def test_explicit_local_url_overrides_host_port(monkeypatch):
    import config

    monkeypatch.setattr(config, "DISCOVERY_A2A_URL", "https://svc.example.com/", raising=False)
    card = discovery_agent_card()
    assert isinstance(card, str)
    assert card.startswith("https://svc.example.com/")
    assert card.endswith(AGENT_CARD_WELL_KNOWN_PATH.lstrip("/"))


def test_resource_name_parsed_from_deployed_a2a_url():
    """A deployed Runtime A2A URL yields the reasoningEngines resource name."""
    a2a_url = (
        "https://us-central1-aiplatform.googleapis.com/v1beta1/projects/1/"
        "locations/us-central1/reasoningEngines/123/a2a"
    )
    resource = _resource_name_from_a2a_url(a2a_url)
    assert resource == "projects/1/locations/us-central1/reasoningEngines/123"
    assert _location_from_resource_name(resource) == "us-central1"
