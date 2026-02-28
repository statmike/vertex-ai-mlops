"""Tests for function_tool_load_schema."""

import json

import pytest

from agent_image_to_graph.tools.function_tool_load_schema import load_schema


class TestLoadSchema:
    """Test load_schema tool with mocked ToolContext."""

    @pytest.mark.asyncio
    async def test_valid_schema(self, mock_tool_context, temp_schema_file):
        result = await load_schema(temp_schema_file, mock_tool_context)
        assert "Schema loaded" in result
        assert mock_tool_context.state["input_schema"] is not None
        assert mock_tool_context.state["schema"] is not None

    @pytest.mark.asyncio
    async def test_missing_file(self, mock_tool_context):
        result = await load_schema("/nonexistent/schema.json", mock_tool_context)
        assert "Error: File not found" in result

    @pytest.mark.asyncio
    async def test_invalid_json(self, mock_tool_context, tmp_path):
        bad_path = tmp_path / "bad.json"
        bad_path.write_text("not valid json{{{")
        result = await load_schema(str(bad_path), mock_tool_context)
        assert "Invalid JSON" in result

    @pytest.mark.asyncio
    async def test_non_dict_json(self, mock_tool_context, tmp_path):
        list_path = tmp_path / "list.json"
        list_path.write_text("[1, 2, 3]")
        result = await load_schema(str(list_path), mock_tool_context)
        assert "must contain a JSON object" in result

    @pytest.mark.asyncio
    async def test_oversized_schema(self, mock_tool_context, tmp_path):
        big_path = tmp_path / "big.json"
        big_path.write_bytes(b"\x00" * (11 * 1024 * 1024))
        result = await load_schema(str(big_path), mock_tool_context)
        assert "too large" in result

    @pytest.mark.asyncio
    async def test_pydantic_schema_resolves_refs(self, mock_tool_context, tmp_path):
        pydantic_schema = {
            "title": "Test",
            "$defs": {
                "Node": {
                    "type": "object",
                    "properties": {"id": {"type": "string"}, "label": {"type": "string"}},
                    "required": ["id", "label"],
                }
            },
            "type": "object",
            "properties": {
                "nodes": {"type": "array", "items": {"$ref": "#/$defs/Node"}},
            },
        }
        path = tmp_path / "pydantic.json"
        path.write_text(json.dumps(pydantic_schema))
        result = await load_schema(str(path), mock_tool_context)
        assert "Node fields" in result
        assert "Node required" in result
