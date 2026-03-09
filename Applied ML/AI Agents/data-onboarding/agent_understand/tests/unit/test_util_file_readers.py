"""Tests for multi-format file readers."""

import json

from agent_understand.tools.util_file_readers import (
    read_csv,
    read_file,
    read_json,
    read_text,
)


class TestReadCsv:
    def test_basic_csv(self):
        data = b"name,age,city\nAlice,30,NYC\nBob,25,LA\n"
        result = read_csv(data, "test.csv")
        assert result["type"] == "tabular"
        assert result["rows"] == 2
        assert len(result["columns"]) == 3
        assert result["columns"][0]["name"] == "name"

    def test_tsv_file(self):
        data = b"name\tage\nAlice\t30\n"
        result = read_csv(data, "test.tsv")
        assert result["rows"] == 1
        assert len(result["columns"]) == 2

    def test_column_statistics(self):
        data = b"val\n1\n2\n3\n"
        result = read_csv(data, "test.csv")
        col = result["columns"][0]
        assert col["null_count"] == 0
        assert col["unique_count"] == 3


class TestReadJson:
    def test_json_array(self):
        data = json.dumps([{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]).encode()
        result = read_json(data, "test.json")
        assert result["type"] == "tabular"
        assert result["rows"] == 2

    def test_jsonl(self):
        data = b'{"a": 1}\n{"a": 2}\n{"a": 3}\n'
        result = read_json(data, "test.jsonl")
        assert result["rows"] == 3

    def test_single_object(self):
        data = json.dumps({"name": "test", "value": 42}).encode()
        result = read_json(data, "test.json")
        assert result["type"] == "tabular"
        assert result["rows"] == 1


class TestReadText:
    def test_basic_text(self):
        data = b"Hello, world!\nThis is a test."
        result = read_text(data, "readme.txt")
        assert result["type"] == "text"
        assert "Hello, world!" in result["content"]
        assert result["line_count"] == 2


class TestReadFile:
    def test_routes_csv(self):
        data = b"a,b\n1,2\n"
        result = read_file(data, "test.csv", "csv")
        assert result["type"] == "tabular"

    def test_routes_json(self):
        data = b'[{"x": 1}]'
        result = read_file(data, "test.json", "json")
        assert result["type"] == "tabular"

    def test_routes_text(self):
        data = b"Some markdown content"
        result = read_file(data, "readme.md", "md")
        assert result["type"] == "text"

    def test_unknown_extension(self):
        data = b"binary data"
        result = read_file(data, "file.xyz", "xyz")
        assert "error" in result
