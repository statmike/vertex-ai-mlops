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

    def test_group_nodes_excluded_from_element_signal(self):
        """Group nodes excluded from element signal; 2 non-group nodes below threshold."""
        nodes = [
            {"id": "g1", "shape": "group_rectangle", "bounding_box": [0, 0, 1000, 1000]},
            {"id": "n1", "bounding_box": [100, 200, 200, 400]},
            {"id": "n2", "bounding_box": [300, 200, 400, 400]},
        ]
        result = _detect_bbox_swap(nodes, {"width": 1920, "height": 1080})
        assert result is False  # Only 2 non-group nodes, below threshold

    def test_group_extreme_ratio_triggers_swap(self):
        """Groups with extreme aspect ratios (>5:1) under normal should trigger swap.

        Simulates a failure case: landscape image (2634x1731), LLM returns
        coordinates with x/y swapped. Groups become extremely flat under normal
        interpretation (e.g., 228h x 1378w = 6:1) but reasonable under swapped
        (905h x 348w = 2.6:1). The non-group element signal leans toward swap
        (swapped_median < normal_median), so elements do not oppose.
        """
        nodes = [
            # Groups: extreme under normal, reasonable under swapped
            {"id": "g1", "shape": "group_rectangle", "bounding_box": [151, 176, 283, 699]},
            {"id": "g2", "shape": "group_rectangle", "bounding_box": [320, 66, 484, 947]},
            {"id": "g3", "shape": "group_rectangle", "bounding_box": [598, 59, 724, 926]},
            # Non-group nodes: mix of nearly-square and elongated elements.
            # Overall, the swapped median is slightly better than normal median
            # (reproducing the real case where 14/26 nodes favored swap).
            # Process boxes (nearly square, favor normal slightly):
            {"id": "n1", "bounding_box": [171, 196, 263, 286]},
            {"id": "n2", "bounding_box": [346, 86, 459, 169]},
            {"id": "n3", "bounding_box": [346, 258, 459, 341]},
            # Data stores / outputs (elongated, clearly favor swap):
            {"id": "n4", "bounding_box": [619, 79, 701, 174]},   # holiday_component
            {"id": "n5", "bounding_box": [619, 251, 702, 341]},  # outlier_component
            {"id": "n6", "bounding_box": [869, 172, 964, 305]},  # forecasted
            {"id": "n7", "bounding_box": [164, 774, 269, 907]},  # eval metrics
            {"id": "n8", "bounding_box": [784, 208, 824, 266]},  # aggregation
        ]
        result = _detect_bbox_swap(nodes, {"width": 2634, "height": 1731})
        assert result is True

    def test_group_reasonable_ratios_no_swap(self):
        """Groups with reasonable aspect ratios should NOT trigger swap."""
        nodes = [
            # Tall groups in a landscape image (reasonable, no swap needed)
            {"id": "g1", "shape": "group_rectangle", "bounding_box": [100, 50, 800, 300]},
            {"id": "g2", "shape": "group_rectangle", "bounding_box": [100, 350, 800, 600]},
            # Non-group nodes
            {"id": "n1", "bounding_box": [200, 100, 350, 250]},
            {"id": "n2", "bounding_box": [400, 100, 550, 250]},
            {"id": "n3", "bounding_box": [600, 100, 750, 250]},
        ]
        result = _detect_bbox_swap(nodes, {"width": 1920, "height": 1080})
        assert result is False

    def test_single_group_not_enough(self):
        """Need at least 2 groups with extreme ratios to trigger swap."""
        nodes = [
            {"id": "g1", "shape": "group_rectangle", "bounding_box": [320, 66, 484, 947]},
            {"id": "n1", "bounding_box": [100, 200, 200, 300]},
            {"id": "n2", "bounding_box": [300, 200, 400, 300]},
            {"id": "n3", "bounding_box": [500, 200, 600, 300]},
        ]
        result = _detect_bbox_swap(nodes, {"width": 2634, "height": 1731})
        assert result is False

    def test_group_swap_with_ambiguous_elements(self):
        """ARIMA regression: elements slightly favor normal but don't strongly oppose.

        The ARIMA flowchart (2634x1731) has elements that are nearly square in
        normalized space. Under normal interpretation, elements have slightly
        lower deviation (normal_median ≈ 0.36 vs swapped_median ≈ 0.55), so
        element_leans_swap is False. But the ratio (0.36/0.55 ≈ 0.65) exceeds
        the 0.6 strong-opposition threshold, so elements do NOT strongly oppose.

        Groups have moderate extreme ratios (1.79 for Preprocessing) that exceed
        log(5) ≈ 1.61 but not log(7) ≈ 1.95. With 2+ groups extreme under
        normal and 0 under swapped, plus no strong element opposition, swap
        should be detected.
        """
        # All 29 real ARIMA bboxes (3 groups + 26 non-group, x/y swapped by LLM).
        # Full set needed: the mix of high/low deviations yields normal_median/
        # swapped_median ≈ 0.65, which is above the 0.6 strong-opposition cutoff.
        nodes = [
            # 3 groups
            {"id": "g1", "shape": "group_rectangle",
             "bounding_box": [150, 177, 283, 700]},   # Preprocessing
            {"id": "g2", "shape": "group_rectangle",
             "bounding_box": [320, 69, 483, 941]},     # Modeling
            {"id": "g3", "shape": "group_rectangle",
             "bounding_box": [58, 598, 927, 724]},     # Decomposed
            # Input cylinders (wide x-span → higher normal deviation)
            {"id": "n1", "bounding_box": [17, 28, 113, 160]},
            {"id": "n2", "bounding_box": [17, 286, 112, 418]},
            # Preprocessing process boxes
            {"id": "n3", "bounding_box": [171, 197, 263, 286]},
            {"id": "n4", "bounding_box": [171, 330, 263, 419]},
            {"id": "n5", "bounding_box": [170, 465, 262, 553]},
            {"id": "n6", "bounding_box": [171, 599, 263, 680]},
            # Modeling process boxes
            {"id": "n7", "bounding_box": [346, 89, 459, 169]},
            {"id": "n8", "bounding_box": [346, 260, 459, 341]},
            {"id": "n9", "bounding_box": [346, 436, 459, 552]},
            {"id": "n10", "bounding_box": [346, 629, 457, 709]},
            {"id": "n11", "bounding_box": [340, 797, 463, 921]},
            # Intermediate data cylinders
            {"id": "n12", "bounding_box": [154, 488, 241, 571]},
            {"id": "n13", "bounding_box": [339, 488, 425, 571]},
            {"id": "n14", "bounding_box": [527, 488, 613, 571]},
            {"id": "n15", "bounding_box": [707, 488, 793, 571]},
            {"id": "n16", "bounding_box": [894, 488, 986, 571]},
            # Decomposed component cylinders
            {"id": "n17", "bounding_box": [78, 619, 175, 701]},
            {"id": "n18", "bounding_box": [254, 619, 340, 702]},
            {"id": "n19", "bounding_box": [412, 618, 568, 701]},
            {"id": "n20", "bounding_box": [625, 619, 716, 704]},
            {"id": "n21", "bounding_box": [809, 618, 907, 702]},
            # Aggregation
            {"id": "n22", "bounding_box": [208, 784, 269, 824]},
            # Output nodes
            {"id": "n23", "bounding_box": [171, 868, 307, 963]},
            {"id": "n24", "bounding_box": [446, 867, 721, 963]},
            {"id": "n25", "bounding_box": [782, 867, 927, 963]},
            # Eval metrics
            {"id": "n26", "bounding_box": [772, 164, 907, 269]},
        ]
        result = _detect_bbox_swap(nodes, {"width": 2634, "height": 1731})
        assert result is True

    def test_horizontal_groups_correctly_oriented_no_false_positive(self):
        """Wide horizontal groups in a correctly oriented landscape image.

        This is the false-positive guard: a top-to-bottom flowchart in a landscape
        image has wide horizontal group bands. Groups are extreme (>7:1) under normal,
        but the elements are correctly oriented (normal is better for elements),
        so group signal alone must NOT trigger a swap.
        """
        nodes = [
            # Wide horizontal groups (correct orientation, NOT swapped)
            {"id": "g1", "shape": "group_rectangle", "bounding_box": [50, 30, 250, 950]},
            {"id": "g2", "shape": "group_rectangle", "bounding_box": [300, 30, 500, 950]},
            {"id": "g3", "shape": "group_rectangle", "bounding_box": [550, 30, 750, 950]},
            # Non-group nodes: correctly oriented (taller than wide in normalized space
            # → pixel ratio closer to square under normal interpretation for landscape)
            {"id": "n1", "bounding_box": [100, 100, 200, 180]},  # y_span=100, x_span=80
            {"id": "n2", "bounding_box": [100, 300, 200, 380]},
            {"id": "n3", "bounding_box": [100, 500, 200, 580]},
            {"id": "n4", "bounding_box": [350, 100, 450, 180]},
            {"id": "n5", "bounding_box": [350, 300, 450, 380]},
        ]
        result = _detect_bbox_swap(nodes, {"width": 1920, "height": 1080})
        assert result is False


class TestContentBasedSwapCheck:
    """Test content-based swap detection (Signal 3 in _detect_bbox_swap)."""

    @staticmethod
    def _make_image(width: int, height: int, marks: list[tuple[int, int]]) -> bytes:
        """Create a white image with black 10x10 marks at given (x, y) pixel positions."""
        import io

        from PIL import Image, ImageDraw

        img = Image.new("L", (width, height), 255)
        draw = ImageDraw.Draw(img)
        for mx, my in marks:
            draw.rectangle([mx - 5, my - 5, mx + 5, my + 5], fill=0)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def test_content_swap_detected(self):
        """Bboxes with x/y swapped: normal points to white, swapped points to content."""
        # Landscape image 2000x1000
        img_w, img_h = 2000, 1000
        # Nodes with x/y swapped bboxes: stored as [x, y, x, y] instead of [y, x, y, x].
        # The actual component is at (x_actual, y_actual) in the image.
        # The stored bbox center is (cy_norm=x_actual_norm, cx_norm=y_actual_norm).
        # The swapped interpretation checks pixel (cy_norm/1000*img_w, cx_norm/1000*img_h)
        # which maps back to the actual component position.
        nodes = []
        marks = []
        for i in range(8):
            # Actual component position in normalized coords
            x_actual = 100 + i * 100  # 100..800
            y_actual = 200            # narrow band
            # Stored bbox is SWAPPED: [x_actual, y_actual, x_actual, y_actual]
            nodes.append({
                "id": f"n{i}",
                "bounding_box": [x_actual - 10, y_actual - 10,
                                 x_actual + 10, y_actual + 10],
            })
            # Mark at the actual component pixel position
            mark_px = int(x_actual / 1000 * img_w)
            mark_py = int(y_actual / 1000 * img_h)
            marks.append((mark_px, mark_py))

        image_bytes = self._make_image(img_w, img_h, marks)
        result = _detect_bbox_swap(
            nodes, {"width": img_w, "height": img_h}, image_bytes,
        )
        assert result is True

    def test_content_no_swap_when_correct(self):
        """Bboxes already correct: normal interpretation hits content."""
        img_w, img_h = 2000, 1000
        nodes = []
        marks = []
        for i in range(8):
            y_center = 100 + i * 100
            x_center = 500
            nodes.append({
                "id": f"n{i}",
                "bounding_box": [y_center - 10, x_center - 10,
                                 y_center + 10, x_center + 10],
            })
            # Mark at the NORMAL position (already correct):
            px = int(x_center / 1000 * img_w)
            py = int(y_center / 1000 * img_h)
            marks.append((px, py))

        image_bytes = self._make_image(img_w, img_h, marks)
        result = _detect_bbox_swap(
            nodes, {"width": img_w, "height": img_h}, image_bytes,
        )
        assert result is False

    def test_content_no_image_falls_back(self):
        """Without source image bytes, content signal is skipped."""
        nodes = [
            {"id": f"n{i}", "bounding_box": [i * 100, 200, i * 100 + 20, 220]}
            for i in range(5)
        ]
        # Element signal alone doesn't trigger swap for these small nearly-square nodes
        result = _detect_bbox_swap(
            nodes, {"width": 2000, "height": 1000}, None,
        )
        assert result is False

    def test_content_does_not_override_strong_element_opposition(self):
        """Content signal is blocked when elements strongly oppose swap.

        This prevents false positives on diagrams where the element signal
        is confident and a noisy content check might disagree.
        """
        img_w, img_h = 1920, 1080
        # Create nodes where the element signal strongly favors normal
        # (tall-narrow in normalized space → close to square in pixel space for landscape)
        nodes = [
            {"id": "n1", "bounding_box": [100, 100, 300, 150]},  # y_span=200, x_span=50
            {"id": "n2", "bounding_box": [400, 100, 600, 150]},
            {"id": "n3", "bounding_box": [700, 100, 900, 150]},
            {"id": "n4", "bounding_box": [100, 300, 300, 350]},
            {"id": "n5", "bounding_box": [400, 300, 600, 350]},
        ]
        # Place marks at swapped positions to make content signal favor swap
        marks = []
        for n in nodes:
            bb = n["bounding_box"]
            cy, cx = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
            s_px = int(cy / 1000 * img_w)
            s_py = int(cx / 1000 * img_h)
            marks.append((s_px, s_py))

        image_bytes = self._make_image(img_w, img_h, marks)
        result = _detect_bbox_swap(
            nodes, {"width": img_w, "height": img_h}, image_bytes,
        )
        # Element signal strongly opposes swap, so content signal is blocked
        assert result is False


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
