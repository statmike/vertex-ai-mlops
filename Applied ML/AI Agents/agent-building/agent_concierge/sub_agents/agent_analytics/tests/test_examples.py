"""Tests for the analytics Example Store wiring.

The store is a managed cloud resource, so these tests never touch it: the ADK
provider/tool imports and the resolution lookup are patched. We verify the pure
parts — the resource name override wins with no network call, display-name
matching finds the store, unresolved config yields ``None``, and the tool is
built from a ``VertexAiExampleStore`` provider.
"""

from unittest.mock import MagicMock, patch

from agent_concierge.sub_agents.agent_analytics import examples


def test_resolve_prefers_explicit_resource_name():
    """EXAMPLE_STORE_NAME is returned verbatim with no listing/network call."""
    name = "projects/p/locations/us-central1/exampleStores/123"
    # If it tried to list, this import patch would prove it didn't need to.
    with (
        patch.object(examples, "EXAMPLE_STORE_NAME", name),
        patch.dict("sys.modules", {"vertexai": MagicMock()}),
    ):
        assert examples._resolve_store_resource_name() == name


def test_resolve_matches_by_display_name():
    match = MagicMock()
    match.display_name = "agent-building-examples"
    match.resource_name = "projects/p/locations/us-central1/exampleStores/999"
    other = MagicMock()
    other.display_name = "something-else"
    other.resource_name = "projects/p/locations/us-central1/exampleStores/000"

    fake_vertexai = MagicMock()
    fake_es = MagicMock()
    fake_es.ExampleStore.list.return_value = [other, match]
    preview_mod = MagicMock()
    preview_mod.example_stores = fake_es

    with (
        patch.object(examples, "EXAMPLE_STORE_NAME", ""),
        patch.object(examples, "EXAMPLE_STORE_DISPLAY_NAME", "agent-building-examples"),
        patch.dict(
            "sys.modules",
            {"vertexai": fake_vertexai, "vertexai.preview": preview_mod},
        ),
    ):
        # vertexai.preview.example_stores is what the function imports.
        fake_vertexai.preview = preview_mod
        assert examples._resolve_store_resource_name() == match.resource_name


def test_resolve_returns_none_when_no_display_name_matches():
    other = MagicMock()
    other.display_name = "nope"

    fake_vertexai = MagicMock()
    fake_es = MagicMock()
    fake_es.ExampleStore.list.return_value = [other]
    preview_mod = MagicMock()
    preview_mod.example_stores = fake_es
    fake_vertexai.preview = preview_mod

    with (
        patch.object(examples, "EXAMPLE_STORE_NAME", ""),
        patch.object(examples, "EXAMPLE_STORE_DISPLAY_NAME", "agent-building-examples"),
        patch.dict(
            "sys.modules",
            {"vertexai": fake_vertexai, "vertexai.preview": preview_mod},
        ),
    ):
        assert examples._resolve_store_resource_name() is None


def test_resolve_returns_none_on_error():
    """A failure resolving (no creds, SDK missing) degrades to None, not a raise."""
    fake_vertexai = MagicMock()
    fake_vertexai.init.side_effect = RuntimeError("no credentials")
    with (
        patch.object(examples, "EXAMPLE_STORE_NAME", ""),
        patch.object(examples, "EXAMPLE_STORE_DISPLAY_NAME", "agent-building-examples"),
        patch.dict("sys.modules", {"vertexai": fake_vertexai}),
    ):
        assert examples._resolve_store_resource_name() is None


def test_display_name_of_reads_backing_resource():
    """Falls back to _gca_resource.display_name when the attribute is absent."""
    store = MagicMock(spec=[])  # no display_name attribute
    store._gca_resource = MagicMock()
    store._gca_resource.display_name = "from-gca"
    assert examples._display_name_of(store) == "from-gca"


def test_build_example_tool_wraps_vertex_provider():
    fake_provider = MagicMock(name="VertexAiExampleStore")
    fake_provider_cls = MagicMock(return_value=fake_provider)
    fake_tool = MagicMock(name="ExampleTool")
    fake_tool_cls = MagicMock(return_value=fake_tool)

    provider_mod = MagicMock()
    provider_mod.VertexAiExampleStore = fake_provider_cls
    tool_mod = MagicMock()
    tool_mod.ExampleTool = fake_tool_cls

    rn = "projects/p/locations/us-central1/exampleStores/123"
    with patch.dict(
        "sys.modules",
        {
            "google.adk.examples": provider_mod,
            "google.adk.tools.example_tool": tool_mod,
        },
    ):
        tool = examples._build_example_tool(rn)

    fake_provider_cls.assert_called_once_with(rn)
    fake_tool_cls.assert_called_once_with(examples=fake_provider)
    assert tool is fake_tool
