"""Unit tests for Crawler."""

import unittest
from unittest.mock import Mock, patch, MagicMock
from scraper.crawler import Crawler


class TestCrawler(unittest.TestCase):
    """Test cases for Crawler."""

    def setUp(self):
        """Set up test fixtures."""
        self.start_url = "https://example.com"
        self.crawler = Crawler(
            start_url=self.start_url,
            max_pages=10,
            max_depth=3,
            delay=0.1,
            timeout=5,
            respect_robots=False,  # Disable for testing
        )

    def test_init(self):
        """Test crawler initialization."""
        self.assertEqual(self.crawler.start_url, self.start_url)
        self.assertEqual(self.crawler.max_pages, 10)
        self.assertEqual(self.crawler.max_depth, 3)
        self.assertEqual(self.crawler.delay, 0.1)

    def test_is_valid_url_same_domain(self):
        """Test URL validation for same domain."""
        self.assertTrue(self.crawler._is_valid_url("https://example.com/page"))
        self.assertTrue(self.crawler._is_valid_url("https://example.com/another/page"))

    def test_is_valid_url_external_domain(self):
        """Test URL validation rejects external domains."""
        self.assertFalse(self.crawler._is_valid_url("https://other.com/page"))

    def test_is_valid_url_excludes_non_content(self):
        """Test URL validation excludes non-content pages."""
        self.assertFalse(self.crawler._is_valid_url("https://example.com/login"))
        self.assertFalse(self.crawler._is_valid_url("https://example.com/search?q=test"))
        self.assertFalse(self.crawler._is_valid_url("https://example.com/api/data"))

    def test_is_valid_url_excludes_media_files(self):
        """Test URL validation excludes media files."""
        self.assertFalse(self.crawler._is_valid_url("https://example.com/image.jpg"))
        self.assertFalse(self.crawler._is_valid_url("https://example.com/document.pdf"))

    def test_extract_links_basic(self):
        """Test link extraction from HTML."""
        html = """
        <html>
        <body>
            <a href="/page1">Page 1</a>
            <a href="/page2">Page 2</a>
            <a href="https://example.com/page3">Page 3</a>
        </body>
        </html>
        """
        links = self.crawler._extract_links(html, "https://example.com")
        self.assertIn("https://example.com/page1", links)
        self.assertIn("https://example.com/page2", links)
        self.assertIn("https://example.com/page3", links)

    def test_extract_links_removes_fragments(self):
        """Test that link extraction removes URL fragments."""
        html = '<a href="/page#section">Link</a>'
        links = self.crawler._extract_links(html, "https://example.com")
        self.assertIn("https://example.com/page", links)
        # Fragment should be removed
        for link in links:
            self.assertNotIn("#", link)

    @patch("scraper.crawler.requests.Session")
    def test_fetch_page_success(self, mock_session_class):
        """Test successful page fetch."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Content</body></html>"
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session.headers = {"User-Agent": "test"}
        mock_session_class.return_value = mock_session

        crawler = Crawler(start_url="https://example.com", respect_robots=False)
        result = crawler._fetch_page("https://example.com/page")

        self.assertIsNotNone(result)
        self.assertEqual(result["url"], "https://example.com/page")
        self.assertEqual(result["status_code"], 200)
        self.assertIn("Content", result["content"])

    @patch("scraper.crawler.requests.Session")
    def test_fetch_page_timeout(self, mock_session_class):
        """Test page fetch handles timeout."""
        import requests

        mock_session = Mock()
        mock_session.get.side_effect = requests.exceptions.Timeout()
        mock_session.headers = {"User-Agent": "test"}
        mock_session_class.return_value = mock_session

        crawler = Crawler(start_url="https://example.com", respect_robots=False)
        result = crawler._fetch_page("https://example.com/page")

        self.assertIsNone(result)

    def test_url_pattern_filter(self):
        """Test URL pattern filtering."""
        crawler = Crawler(
            start_url="https://example.com",
            url_pattern="/docs/",
            respect_robots=False,
        )

        self.assertTrue(crawler._is_valid_url("https://example.com/docs/page"))
        self.assertFalse(crawler._is_valid_url("https://example.com/blog/page"))


if __name__ == "__main__":
    unittest.main()

