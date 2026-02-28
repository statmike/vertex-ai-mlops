"""Tests for util_schema: resolve_items() and _resolve_ref()."""

from agent_image_to_graph.tools.util_schema import _resolve_ref, resolve_items


class TestResolveItems:
    """Test resolve_items() for both direct and $ref schemas."""

    def test_direct_items(self, sample_schema):
        """Items defined inline (no $ref)."""
        result = resolve_items(sample_schema, "nodes")
        assert "properties" in result
        assert "id" in result["properties"]

    def test_ref_resolution(self, sample_pydantic_schema):
        """Items using $ref into $defs."""
        result = resolve_items(sample_pydantic_schema, "nodes")
        assert "properties" in result
        assert "id" in result["properties"]
        assert result.get("required") == ["id", "label", "element_type"]

    def test_missing_element(self, sample_schema):
        """Non-existent element key returns empty dict."""
        result = resolve_items(sample_schema, "nonexistent")
        assert result == {}

    def test_empty_schema(self):
        """Empty schema returns empty dict."""
        result = resolve_items({}, "nodes")
        assert result == {}

    def test_edges_resolution(self, sample_pydantic_schema):
        """Edges are also resolved correctly."""
        result = resolve_items(sample_pydantic_schema, "edges")
        assert "properties" in result
        assert result.get("required") == ["id", "source", "target"]


class TestResolveRef:
    """Test _resolve_ref() directly."""

    def test_valid_ref(self, sample_pydantic_schema):
        result = _resolve_ref(sample_pydantic_schema, "#/$defs/FlowchartNode")
        assert result is not None
        assert "properties" in result

    def test_invalid_ref_no_hash(self):
        result = _resolve_ref({}, "invalid/ref")
        assert result == {}

    def test_missing_path(self, sample_pydantic_schema):
        result = _resolve_ref(sample_pydantic_schema, "#/$defs/DoesNotExist")
        assert result == {}

    def test_non_dict_target(self):
        schema = {"$defs": {"Foo": "not_a_dict"}}
        result = _resolve_ref(schema, "#/$defs/Foo")
        assert result == {}
