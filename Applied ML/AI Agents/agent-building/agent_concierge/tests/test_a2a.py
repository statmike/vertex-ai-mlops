"""Tests for the concierge's A2A card-URL resolution.

Kept import-light on purpose: importing agent_concierge.agent would pull in the
ADK Claude client and the BigQuery telemetry plugin. The routing wiring is
exercised end-to-end by `adk web`; here we just pin the URL-building contract.
"""

from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH

from agent_concierge.utils import discovery_agent_card_url


def test_card_url_appends_well_known_path(monkeypatch):
    import config

    monkeypatch.setattr(config, "DISCOVERY_A2A_URL", "", raising=False)
    monkeypatch.setattr(config, "DISCOVERY_A2A_HOST", "localhost", raising=False)
    monkeypatch.setattr(config, "DISCOVERY_A2A_PORT", 8001, raising=False)

    url = discovery_agent_card_url()
    assert url.startswith("http://localhost:8001/")
    assert url.endswith(AGENT_CARD_WELL_KNOWN_PATH.lstrip("/"))
    assert "//.well-known" not in url  # no double slash from the join


def test_explicit_url_overrides_host_port(monkeypatch):
    import config

    monkeypatch.setattr(config, "DISCOVERY_A2A_URL", "https://svc.example.com/", raising=False)
    url = discovery_agent_card_url()
    assert url.startswith("https://svc.example.com/")
    assert url.endswith(AGENT_CARD_WELL_KNOWN_PATH.lstrip("/"))
