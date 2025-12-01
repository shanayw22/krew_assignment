"""Unit tests for ContentExtractor."""

import unittest
from scraper.extractor import ContentExtractor


class TestContentExtractor(unittest.TestCase):
    """Test cases for ContentExtractor."""

    def setUp(self):
        """Set up test fixtures."""
        self.extractor = ContentExtractor()

    def test_extract_title_from_title_tag(self):
        """Test extracting title from <title> tag."""
        html = "<html><head><title>Test Page Title</title></head><body>Content</body></html>"
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        title = self.extractor.extract_title(soup)
        self.assertEqual(title, "Test Page Title")

    def test_extract_title_from_h1(self):
        """Test extracting title from <h1> tag when <title> is missing."""
        html = "<html><body><h1>Main Heading</h1><p>Content</p></body></html>"
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        title = self.extractor.extract_title(soup)
        self.assertEqual(title, "Main Heading")

    def test_extract_title_from_og_meta(self):
        """Test extracting title from og:title meta tag."""
        html = """
        <html>
        <head>
            <meta property="og:title" content="OG Title" />
        </head>
        <body>Content</body>
        </html>
        """
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        title = self.extractor.extract_title(soup)
        self.assertEqual(title, "OG Title")

    def test_extract_title_fallback(self):
        """Test title extraction fallback to 'Untitled'."""
        html = "<html><body><p>No title here</p></body></html>"
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        title = self.extractor.extract_title(soup)
        self.assertEqual(title, "Untitled")

    def test_extract_body_text_basic(self):
        """Test basic body text extraction."""
        html = """
        <html>
        <body>
            <article>
                <h1>Article Title</h1>
                <p>First paragraph with some content.</p>
                <p>Second paragraph with more content.</p>
            </article>
        </body>
        </html>
        """
        text = self.extractor.extract_body_text(html)
        self.assertIn("Article Title", text)
        self.assertIn("First paragraph", text)
        self.assertIn("Second paragraph", text)

    def test_extract_body_text_removes_boilerplate(self):
        """Test that boilerplate elements are removed."""
        html = """
        <html>
        <head><title>Test</title></head>
        <body>
            <nav>Navigation</nav>
            <header>Header</header>
            <main>
                <p>Main content here</p>
            </main>
            <footer>Footer</footer>
            <script>console.log('script');</script>
        </body>
        </html>
        """
        text = self.extractor.extract_body_text(html)
        self.assertIn("Main content here", text)
        self.assertNotIn("Navigation", text)
        self.assertNotIn("Header", text)
        self.assertNotIn("Footer", text)
        self.assertNotIn("console.log", text)

    def test_clean_text_normalizes_whitespace(self):
        """Test that text cleaning normalizes whitespace."""
        text = "This   has    multiple    spaces"
        cleaned = self.extractor._clean_text(text)
        self.assertEqual(cleaned, "This has multiple spaces")

    def test_clean_text_normalizes_newlines(self):
        """Test that text cleaning normalizes newlines."""
        text = "Line 1\n\n\n\nLine 2"
        cleaned = self.extractor._clean_text(text)
        self.assertNotIn("\n\n\n", cleaned)

    def test_extract_full_document(self):
        """Test full document extraction."""
        html = """
        <html>
        <head><title>Test Document</title></head>
        <body>
            <article>
                <h1>Document Title</h1>
                <p>This is the main content of the document.</p>
            </article>
        </body>
        </html>
        """
        result = self.extractor.extract(html, "https://example.com/test")
        self.assertEqual(result["title"], "Test Document")
        self.assertIn("Document Title", result["body_text"])
        self.assertIn("main content", result["body_text"])

    def test_extract_handles_malformed_html(self):
        """Test that extraction handles malformed HTML gracefully."""
        html = "<html><body><p>Unclosed tag</body></html>"
        result = self.extractor.extract(html, "https://example.com/test")
        self.assertIsInstance(result["title"], str)
        self.assertIsInstance(result["body_text"], str)

    def test_extract_empty_html(self):
        """Test extraction with empty HTML."""
        html = "<html><body></body></html>"
        result = self.extractor.extract(html, "https://example.com/test")
        self.assertIsInstance(result["title"], str)
        self.assertEqual(result["body_text"], "")


if __name__ == "__main__":
    unittest.main()

