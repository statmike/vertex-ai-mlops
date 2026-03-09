"""Tests for URL parsing and scope checking utilities."""

from agent_acquire.tools.util_crawl import (
    extract_links,
    get_file_extension,
    is_downloadable_file,
    is_same_origin,
    normalize_url,
    should_follow_link,
)


class TestNormalizeUrl:
    def test_removes_fragment(self):
        assert normalize_url("https://example.com/page#section") == "https://example.com/page"

    def test_removes_trailing_slash(self):
        assert normalize_url("https://example.com/page/") == "https://example.com/page"

    def test_preserves_root_path(self):
        result = normalize_url("https://example.com/")
        assert result == "https://example.com/"

    def test_preserves_query_params(self):
        assert "q=test" in normalize_url("https://example.com/search?q=test")


class TestIsSameOrigin:
    def test_same_origin(self):
        assert is_same_origin("https://example.com/a", "https://example.com/b")

    def test_different_host(self):
        assert not is_same_origin("https://example.com/a", "https://other.com/b")

    def test_different_scheme(self):
        assert not is_same_origin("https://example.com/a", "http://example.com/b")


class TestShouldFollowLink:
    def test_mailto_rejected(self):
        assert not should_follow_link("https://example.com", "mailto:user@example.com")

    def test_javascript_rejected(self):
        assert not should_follow_link("https://example.com", "javascript:void(0)")

    def test_fragment_rejected(self):
        assert not should_follow_link("https://example.com", "#section")

    def test_empty_rejected(self):
        assert not should_follow_link("https://example.com", "")

    def test_valid_http_accepted(self):
        assert should_follow_link("https://example.com", "https://example.com/page")


class TestIsDownloadableFile:
    def test_csv_file(self):
        assert is_downloadable_file("https://example.com/data.csv")

    def test_json_file(self):
        assert is_downloadable_file("https://example.com/data.json")

    def test_parquet_file(self):
        assert is_downloadable_file("https://example.com/data.parquet")

    def test_html_page(self):
        assert is_downloadable_file("https://example.com/page.html")

    def test_no_extension(self):
        assert not is_downloadable_file("https://example.com/page")

    def test_unknown_extension(self):
        assert not is_downloadable_file("https://example.com/file.xyz")


class TestGetFileExtension:
    def test_csv(self):
        assert get_file_extension("https://example.com/data.csv") == "csv"

    def test_no_extension(self):
        assert get_file_extension("https://example.com/page") == ""

    def test_uppercase(self):
        assert get_file_extension("https://example.com/data.CSV") == "csv"


class TestExtractLinks:
    def test_extracts_links(self):
        html = """
        <html><body>
            <a href="/data.csv">Data</a>
            <a href="/page2">Page 2</a>
        </body></html>
        """
        links = extract_links(html, "https://example.com")
        assert len(links) == 2
        urls = [link["url"] for link in links]
        assert "https://example.com/data.csv" in urls

    def test_deduplicates(self):
        html = """
        <html><body>
            <a href="/data.csv">Data</a>
            <a href="/data.csv">Data Again</a>
        </body></html>
        """
        links = extract_links(html, "https://example.com")
        assert len(links) == 1

    def test_marks_files(self):
        html = '<html><body><a href="/data.csv">Data</a></body></html>'
        links = extract_links(html, "https://example.com")
        assert links[0]["is_file"] is True

    def test_marks_pages(self):
        html = '<html><body><a href="/about">About</a></body></html>'
        links = extract_links(html, "https://example.com")
        assert links[0]["is_file"] is False
