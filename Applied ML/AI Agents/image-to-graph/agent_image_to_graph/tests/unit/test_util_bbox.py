"""Tests for util_bbox.normalize_bbox()."""

from agent_image_to_graph.tools.util_bbox import normalize_bbox


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
