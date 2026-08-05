"""Tests for A2A client selection.

The rule: a local (localhost) discovery URL needs no auth, so RemoteA2aAgent
builds its own plain client (None here); a deployed googleapis.com URL gets an
authenticated, token-refreshing client.
"""

from unittest.mock import MagicMock

from agent_concierge.utils import authed_httpx_client_for


def test_local_url_gets_no_client():
    assert authed_httpx_client_for("http://localhost:8001/.well-known/agent.json") is None


def test_runtime_url_gets_authed_client(monkeypatch):
    # Avoid touching real credentials: stub google.auth.default.
    import google.auth

    monkeypatch.setattr(google.auth, "default", lambda scopes=None: (MagicMock(), "proj"))

    url = (
        "https://us-central1-aiplatform.googleapis.com/v1beta1/projects/p/"
        "locations/us-central1/reasoningEngines/123/.well-known/agent.json"
    )
    client = authed_httpx_client_for(url)
    assert client is not None
    assert client.auth is not None
