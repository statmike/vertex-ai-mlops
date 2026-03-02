"""Tests for util_bbox.normalize_bbox() and detect_bbox_corrections()."""

from agent_image_to_graph.tools.util_bbox import detect_bbox_corrections, normalize_bbox


class TestNormalizeBboxDict:
    """Dict format: {top, left, bottom, right}."""

    def test_valid_dict(self):
        result = normalize_bbox({"top": 10, "left": 20, "bottom": 100, "right": 200})
        assert result == [10, 20, 100, 200]

    def test_missing_keys(self):
        assert normalize_bbox({"top": 10, "left": 20}) is None

    def test_non_numeric_values(self):
        assert normalize_bbox({"top": "a", "left": "b", "bottom": "c", "right": "d"}) is None

    def test_float_values_converted_to_int(self):
        result = normalize_bbox({"top": 10.7, "left": 20.3, "bottom": 100.9, "right": 200.1})
        assert result == [10, 20, 100, 200]


class TestNormalizeBboxList:
    """List format: [y_min, x_min, y_max, x_max]."""

    def test_valid_list(self):
        result = normalize_bbox([50, 100, 200, 300])
        assert result == [50, 100, 200, 300]

    def test_wrong_length(self):
        assert normalize_bbox([1, 2, 3]) is None
        assert normalize_bbox([1, 2, 3, 4, 5]) is None

    def test_float_to_int_conversion(self):
        result = normalize_bbox([10.5, 20.5, 30.5, 40.5])
        assert result == [10, 20, 30, 40]


class TestNormalizeBboxTuple:
    """Tuple format."""

    def test_valid_tuple(self):
        result = normalize_bbox((50, 100, 200, 300))
        assert result == [50, 100, 200, 300]


class TestNormalizeBboxAutoCorrect:
    """Auto-correction of inverted coordinates."""

    def test_inverted_y_dict(self):
        """top > bottom in dict format → swapped."""
        result = normalize_bbox({"top": 500, "left": 20, "bottom": 100, "right": 200})
        assert result == [100, 20, 500, 200]

    def test_inverted_y_list(self):
        """y_min > y_max in list format → swapped."""
        result = normalize_bbox([500, 20, 100, 200])
        assert result == [100, 20, 500, 200]

    def test_inverted_x(self):
        """left > right → swapped."""
        result = normalize_bbox({"top": 10, "left": 400, "bottom": 100, "right": 200})
        assert result == [10, 200, 100, 400]

    def test_both_inverted(self):
        """Both axes inverted → both swapped."""
        result = normalize_bbox({"top": 500, "left": 400, "bottom": 100, "right": 200})
        assert result == [100, 200, 500, 400]

    def test_equal_values_unchanged(self):
        """Equal min/max (zero-size box) is valid, no swap needed."""
        result = normalize_bbox([100, 200, 100, 200])
        assert result == [100, 200, 100, 200]


class TestNormalizeBboxClamping:
    """Clamping to 0-1000 range."""

    def test_negative_values_clamped(self):
        result = normalize_bbox([-10, -20, 100, 200])
        assert result == [0, 0, 100, 200]

    def test_over_1000_clamped(self):
        result = normalize_bbox([10, 20, 1050, 1100])
        assert result == [10, 20, 1000, 1000]

    def test_combined_invert_and_clamp(self):
        """Inverted + out-of-range → swap first, then clamp."""
        result = normalize_bbox({"top": 1100, "left": -5, "bottom": 50, "right": 900})
        assert result == [50, 0, 1000, 900]


class TestNormalizeBboxInvalid:
    """Invalid inputs."""

    def test_none(self):
        assert normalize_bbox(None) is None

    def test_string(self):
        assert normalize_bbox("10,20,30,40") is None

    def test_empty_dict(self):
        assert normalize_bbox({}) is None

    def test_empty_list(self):
        assert normalize_bbox([]) is None

    def test_non_numeric_list(self):
        assert normalize_bbox(["a", "b", "c", "d"]) is None


class TestDetectBboxCorrections:
    """Tests for detect_bbox_corrections()."""

    def test_no_correction_needed(self):
        assert detect_bbox_corrections([10, 20, 100, 200], [10, 20, 100, 200]) is None

    def test_y_inverted(self):
        result = detect_bbox_corrections([500, 20, 100, 200], [100, 20, 500, 200])
        assert result is not None
        assert result["y_inverted"] is True
        assert result["x_inverted"] is False
        assert result["clamped"] is False

    def test_x_inverted(self):
        result = detect_bbox_corrections([10, 400, 100, 200], [10, 200, 100, 400])
        assert result is not None
        assert result["y_inverted"] is False
        assert result["x_inverted"] is True
        assert result["clamped"] is False

    def test_both_inverted(self):
        result = detect_bbox_corrections([500, 400, 100, 200], [100, 200, 500, 400])
        assert result is not None
        assert result["y_inverted"] is True
        assert result["x_inverted"] is True
        assert result["clamped"] is False

    def test_clamped(self):
        result = detect_bbox_corrections([-10, 20, 100, 1100], [0, 20, 100, 1000])
        assert result is not None
        assert result["y_inverted"] is False
        assert result["x_inverted"] is False
        assert result["clamped"] is True

    def test_combined_invert_and_clamp(self):
        result = detect_bbox_corrections([1100, -5, 50, 900], [50, 0, 1000, 900])
        assert result is not None
        assert result["y_inverted"] is True
        assert result["x_inverted"] is False
        assert result["clamped"] is True
