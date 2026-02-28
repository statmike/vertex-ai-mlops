"""Tests for util_common: strip_json_markdown_fence() and log_tool_error()."""

from agent_image_to_graph.tools.util_common import log_tool_error, strip_json_markdown_fence


class TestStripJsonMarkdownFence:
    """Test strip_json_markdown_fence()."""

    def test_plain_json(self):
        text = '{"key": "value"}'
        assert strip_json_markdown_fence(text) == '{"key": "value"}'

    def test_json_fence(self):
        text = '```json\n{"key": "value"}\n```'
        assert strip_json_markdown_fence(text) == '{"key": "value"}'

    def test_plain_fence(self):
        text = '```\n{"key": "value"}\n```'
        assert strip_json_markdown_fence(text) == '{"key": "value"}'

    def test_missing_closing_fence(self):
        text = '```json\n{"key": "value"}'
        result = strip_json_markdown_fence(text)
        assert '{"key": "value"}' in result

    def test_no_fences(self):
        text = "Just some text"
        assert strip_json_markdown_fence(text) == "Just some text"

    def test_whitespace_stripped(self):
        text = '  \n```json\n{"key": "value"}\n```\n  '
        result = strip_json_markdown_fence(text)
        assert result == '{"key": "value"}'

    def test_multiline_json(self):
        text = '```json\n{\n  "a": 1,\n  "b": 2\n}\n```'
        result = strip_json_markdown_fence(text)
        assert '"a": 1' in result
        assert '"b": 2' in result


class TestLogToolError:
    """Test log_tool_error()."""

    def test_returns_sanitized_message(self):
        error = ValueError("bad input")
        result = log_tool_error("test_tool", error)
        assert "Error in test_tool" in result
        assert "bad input" in result

    def test_with_context(self):
        error = RuntimeError("timeout")
        result = log_tool_error("my_tool", error, context="region_3")
        assert "Error in my_tool" in result
        assert "timeout" in result
