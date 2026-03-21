"""Tests for zip extraction in function_tool_download_files."""

import io
import zipfile
from unittest.mock import patch

from agent_acquire.tools.function_tool_download_files import _extract_zip


def _make_zip(members: dict[str, bytes]) -> bytes:
    """Build an in-memory zip archive from {path: content} pairs."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in members.items():
            zf.writestr(name, data)
    return buf.getvalue()


STAGING = "staging/root"
ARCHIVE_URL = "https://example.com/archive.zip"
URL_TO_PARENT = {ARCHIVE_URL: "https://example.com/"}


@patch(
    "agent_acquire.tools.function_tool_download_files.upload_bytes",
    side_effect=lambda data, path, **kwargs: f"gs://bucket/{path}",
)
@patch(
    "agent_acquire.tools.function_tool_download_files.compute_hash",
    return_value="abc123",
)
class TestExtractZip:
    def test_extracts_supported_files(self, mock_hash, mock_upload):
        zip_data = _make_zip({"data.csv": b"a,b\n1,2", "notes.txt": b"hello"})
        extracted, skipped = _extract_zip(zip_data, ARCHIVE_URL, STAGING, URL_TO_PARENT)

        assert len(extracted) == 2
        filenames = {f["filename"] for f in extracted}
        assert filenames == {"data.csv", "notes.txt"}
        assert not skipped

    def test_skips_unsupported_extensions(self, mock_hash, mock_upload):
        zip_data = _make_zip({"data.csv": b"a,b", "photo.png": b"\x89PNG"})
        extracted, skipped = _extract_zip(zip_data, ARCHIVE_URL, STAGING, URL_TO_PARENT)

        assert len(extracted) == 1
        assert extracted[0]["filename"] == "data.csv"
        assert "photo.png" in skipped

    def test_skips_directories(self, mock_hash, mock_upload):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("subdir/", "")  # directory entry
            zf.writestr("subdir/data.csv", "a,b")
        zip_data = buf.getvalue()

        extracted, skipped = _extract_zip(zip_data, ARCHIVE_URL, STAGING, URL_TO_PARENT)

        assert len(extracted) == 1
        assert extracted[0]["filename"] == "data.csv"
        assert "subdir/" in skipped

    def test_handles_basename_collisions(self, mock_hash, mock_upload):
        zip_data = _make_zip({
            "dir1/data.csv": b"a,b",
            "dir2/data.csv": b"c,d",
        })
        extracted, skipped = _extract_zip(zip_data, ARCHIVE_URL, STAGING, URL_TO_PARENT)

        assert len(extracted) == 2
        filenames = sorted(f["filename"] for f in extracted)
        assert filenames == ["data.csv", "data_1.csv"]

    def test_skips_nested_zips(self, mock_hash, mock_upload):
        inner_zip = _make_zip({"inner.csv": b"x"})
        zip_data = _make_zip({"data.csv": b"a,b", "nested.zip": inner_zip})

        extracted, skipped = _extract_zip(zip_data, ARCHIVE_URL, STAGING, URL_TO_PARENT)

        assert len(extracted) == 1
        assert extracted[0]["filename"] == "data.csv"
        assert "nested.zip" in skipped

    def test_handles_bad_zip(self, mock_hash, mock_upload):
        extracted, skipped = _extract_zip(b"not a zip", ARCHIVE_URL, STAGING, URL_TO_PARENT)

        assert extracted == []
        assert len(skipped) == 1
        assert "bad zip" in skipped[0].lower()

    def test_tracks_archive_provenance(self, mock_hash, mock_upload):
        zip_data = _make_zip({"subdir/report.csv": b"col1\nval1"})
        extracted, _ = _extract_zip(zip_data, ARCHIVE_URL, STAGING, URL_TO_PARENT)

        assert len(extracted) == 1
        f = extracted[0]
        assert f["archive_url"] == ARCHIVE_URL
        assert f["archive_member_path"] == "subdir/report.csv"
        assert f["parent_url"] == "https://example.com/"
        assert f["url"] == ARCHIVE_URL
