"""Tests for private helper functions in validate_graph.py."""

from agent_image_to_graph.tools.function_tool_validate_graph import (
    _detect_bbox_swap,
    _format_report,
    _type_matches,
    _validate_against_schema,
)


class TestTypeMatches:
    """Test _type_matches() for all JSON Schema types."""

    def test_string(self):
        assert _type_matches("hello", "string") is True
        assert _type_matches(42, "string") is False

    def test_integer(self):
        assert _type_matches(42, "integer") is True
        assert _type_matches("42", "integer") is False

    def test_number(self):
        assert _type_matches(42, "number") is True
        assert _type_matches(3.14, "number") is True
        assert _type_matches("42", "number") is False

    def test_boolean(self):
        assert _type_matches(True, "boolean") is True
        assert _type_matches(1, "boolean") is False

    def test_array(self):
        assert _type_matches([1, 2], "array") is True
        assert _type_matches("list", "array") is False

    def test_object(self):
        assert _type_matches({"a": 1}, "object") is True
        assert _type_matches([1], "object") is False

    def test_unknown_type_returns_true(self):
        assert _type_matches("anything", "custom_type") is True


class TestFormatReport:
    """Test _format_report()."""

    def test_no_issues(self):
        report = _format_report([], [], node_count=5, edge_count=3)
        assert "PASSED" in report
        assert "No errors or warnings" in report

    def test_errors_only(self):
        report = _format_report(["Missing id"], [], node_count=1, edge_count=0)
        assert "FAILED" in report
        assert "Missing id" in report

    def test_warnings_only(self):
        report = _format_report([], ["Disconnected node"], node_count=2, edge_count=1)
        assert "PASSED with warnings" in report
        assert "Disconnected node" in report

    def test_errors_and_warnings(self):
        report = _format_report(["error1"], ["warn1"], node_count=1, edge_count=1)
        assert "FAILED" in report
        assert "error1" in report
        assert "warn1" in report

    def test_schema_source_shown(self):
        report = _format_report([], [], node_count=1, edge_count=0, schema_source="input")
        assert "input" in report


class TestDetectBboxSwap:
    """Test _detect_bbox_swap()."""

    def test_square_image_no_swap(self):
        """Square images can't detect swap — should return False."""
        nodes = [
            {"id": f"n{i}", "bounding_box": [i * 100, i * 50, i * 100 + 80, i * 50 + 80]}
            for i in range(5)
        ]
        result = _detect_bbox_swap(nodes, {"width": 1000, "height": 1000})
        assert result is False

    def test_landscape_correct_coords(self):
        """Landscape image with correct [y,x,y,x] — no swap needed.

        For a 1920x1080 image, boxes roughly square in pixel space need:
        y-span / x-span ≈ 1920/1080 ≈ 1.78
        So y-span ~178, x-span ~100 → pixel h=178/1000*1080≈192, w=100/1000*1920≈192
        """
        nodes = [
            {"id": "n1", "bounding_box": [100, 100, 278, 200]},
            {"id": "n2", "bounding_box": [300, 100, 478, 200]},
            {"id": "n3", "bounding_box": [500, 100, 678, 200]},
            {"id": "n4", "bounding_box": [100, 300, 278, 400]},
        ]
        result = _detect_bbox_swap(nodes, {"width": 1920, "height": 1080})
        assert result is False

    def test_fewer_than_3_nodes(self):
        """Fewer than 3 non-group nodes → can't reliably detect."""
        nodes = [
            {"id": "n1", "bounding_box": [100, 200, 300, 400]},
            {"id": "n2", "bounding_box": [400, 500, 600, 700]},
        ]
        result = _detect_bbox_swap(nodes, {"width": 1920, "height": 1080})
        assert result is False

    def test_no_dimensions(self):
        """Missing image dimensions → False."""
        nodes = [{"id": "n1", "bounding_box": [100, 200, 300, 400]}]
        result = _detect_bbox_swap(nodes, {})
        assert result is False

    def test_group_nodes_excluded(self):
        """Group nodes should be excluded from swap detection."""
        nodes = [
            {"id": "g1", "shape": "group_rectangle", "bounding_box": [0, 0, 1000, 1000]},
            {"id": "n1", "bounding_box": [100, 200, 200, 400]},
            {"id": "n2", "bounding_box": [300, 200, 400, 400]},
        ]
        result = _detect_bbox_swap(nodes, {"width": 1920, "height": 1080})
        assert result is False  # Only 2 non-group nodes, below threshold


class TestValidateAgainstSchema:
    """Test _validate_against_schema()."""

    def test_missing_required_fields(self, sample_schema):
        nodes = [{"id": "n1"}]  # missing 'label'
        edges = []
        errors, warnings = _validate_against_schema(nodes, edges, sample_schema, "input")
        assert any("label" in e for e in errors)

    def test_type_mismatch_warning(self, sample_schema):
        nodes = [{"id": "n1", "label": "Test", "confidence": 42}]  # int, expected string
        edges = []
        errors, warnings = _validate_against_schema(nodes, edges, sample_schema, "input")
        assert any("confidence" in w for w in warnings)

    def test_valid_passes(self, sample_schema):
        nodes = [{"id": "n1", "label": "Test"}]
        edges = [{"id": "e1", "source": "n1", "target": "n2"}]
        errors, warnings = _validate_against_schema(nodes, edges, sample_schema, "input")
        assert len(errors) == 0
