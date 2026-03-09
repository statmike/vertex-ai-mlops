"""Tests for shared utility functions."""

from agent_acquire.tools.util_common import compute_hash, generate_source_id


class TestComputeHash:
    def test_deterministic(self):
        data = b"hello world"
        assert compute_hash(data) == compute_hash(data)

    def test_different_data_different_hash(self):
        assert compute_hash(b"hello") != compute_hash(b"world")

    def test_returns_hex_string(self):
        result = compute_hash(b"test")
        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 hex length


class TestGenerateSourceId:
    def test_deterministic(self):
        uri = "https://example.com/data.csv"
        assert generate_source_id(uri) == generate_source_id(uri)

    def test_different_uris_different_ids(self):
        assert generate_source_id("https://a.com") != generate_source_id("https://b.com")

    def test_returns_uuid_format(self):
        result = generate_source_id("https://example.com")
        assert len(result) == 36  # UUID format: 8-4-4-4-12
        assert result.count("-") == 4
