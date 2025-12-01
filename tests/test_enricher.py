"""Unit tests for DocumentEnricher."""

import unittest
from datetime import datetime
from scraper.enricher import DocumentEnricher


class TestDocumentEnricher(unittest.TestCase):
    """Test cases for DocumentEnricher."""

    def setUp(self):
        """Set up test fixtures."""
        self.enricher = DocumentEnricher()

    def test_detect_language_english(self):
        """Test English language detection."""
        text = "The quick brown fox jumps over the lazy dog. This is a test."
        language = self.enricher.detect_language(text)
        self.assertEqual(language, "en")

    def test_detect_language_short_text(self):
        """Test language detection with short text defaults to English."""
        text = "Hi"
        language = self.enricher.detect_language(text)
        self.assertEqual(language, "en")

    def test_detect_language_empty_text(self):
        """Test language detection with empty text."""
        language = self.enricher.detect_language("")
        self.assertEqual(language, "en")

    def test_detect_content_type_article(self):
        """Test content type detection for articles."""
        url = "https://example.com/blog/article/my-article"
        title = "My Article"
        body = "Article content here"
        content_type = self.enricher.detect_content_type(url, title, body)
        self.assertEqual(content_type, "article")

    def test_detect_content_type_doc_page(self):
        """Test content type detection for documentation."""
        url = "https://example.com/docs/getting-started"
        title = "Getting Started"
        body = "Documentation content"
        content_type = self.enricher.detect_content_type(url, title, body)
        self.assertEqual(content_type, "doc_page")

    def test_detect_content_type_tutorial(self):
        """Test content type detection for tutorials."""
        url = "https://example.com/tutorial/python-basics"
        title = "Python Basics Tutorial"
        body = "Tutorial content"
        content_type = self.enricher.detect_content_type(url, title, body)
        self.assertEqual(content_type, "tutorial")

    def test_detect_content_type_default(self):
        """Test content type defaults to 'page'."""
        url = "https://example.com/some-page"
        title = "Some Page"
        body = "Content"
        content_type = self.enricher.detect_content_type(url, title, body)
        self.assertEqual(content_type, "page")

    def test_estimate_reading_time(self):
        """Test reading time estimation."""
        # 200 words = 1 minute
        word_count = 200
        reading_time = self.enricher.estimate_reading_time(word_count)
        self.assertEqual(reading_time, 1)

        # 1000 words = 5 minutes
        word_count = 1000
        reading_time = self.enricher.estimate_reading_time(word_count)
        self.assertEqual(reading_time, 5)

        # Minimum 1 minute
        word_count = 50
        reading_time = self.enricher.estimate_reading_time(word_count)
        self.assertEqual(reading_time, 1)

    def test_is_mostly_code_true(self):
        """Test code detection for code-heavy content."""
        text = """
        function myFunction() {
            console.log('Hello');
            var x = 10;
            return x;
        }
        function anotherFunction() {
            console.log('World');
            var y = 20;
        }
        class MyClass {
            constructor() {
                this.value = 5;
            }
        }
        class AnotherClass {
            constructor() {
                this.data = [];
            }
        }
        import { something } from 'module';
        import { other } from 'other';
        """
        is_code = self.enricher.is_mostly_code(text)
        self.assertTrue(is_code)

    def test_is_mostly_code_false(self):
        """Test code detection for regular text."""
        text = "This is a regular article with lots of text content. It discusses various topics and provides information to the reader."
        is_code = self.enricher.is_mostly_code(text)
        self.assertFalse(is_code)

    def test_enrich_basic(self):
        """Test basic document enrichment."""
        document = {
            "url": "https://example.com/article",
            "title": "Test Article",
            "body_text": "This is a test article with some content. It has multiple sentences.",
        }

        enriched = self.enricher.enrich(document)

        # Check required fields
        self.assertEqual(enriched["url"], document["url"])
        self.assertEqual(enriched["title"], document["title"])
        self.assertEqual(enriched["body_text"], document["body_text"])

        # Check metadata fields
        self.assertIn("char_count", enriched)
        self.assertIn("word_count", enriched)
        self.assertIn("language", enriched)
        self.assertIn("content_type", enriched)
        self.assertIn("fetched_at", enriched)
        self.assertIn("reading_time_minutes", enriched)
        self.assertIn("is_mostly_code", enriched)
        self.assertIn("domain", enriched)
        self.assertIn("path", enriched)

        # Check values
        self.assertGreater(enriched["char_count"], 0)
        self.assertGreater(enriched["word_count"], 0)
        self.assertIsInstance(enriched["language"], str)
        self.assertIsInstance(enriched["content_type"], str)
        self.assertIsInstance(enriched["fetched_at"], str)
        self.assertGreaterEqual(enriched["reading_time_minutes"], 1)
        self.assertIsInstance(enriched["is_mostly_code"], bool)

    def test_enrich_empty_body(self):
        """Test enrichment with empty body text."""
        document = {
            "url": "https://example.com/page",
            "title": "Empty Page",
            "body_text": "",
        }

        enriched = self.enricher.enrich(document)
        self.assertEqual(enriched["char_count"], 0)
        self.assertEqual(enriched["word_count"], 0)
        self.assertEqual(enriched["reading_time_minutes"], 1)  # Minimum

    def test_enrich_domain_extraction(self):
        """Test domain extraction from URL."""
        document = {
            "url": "https://docs.example.com/path/to/page",
            "title": "Test",
            "body_text": "Content",
        }

        enriched = self.enricher.enrich(document)
        self.assertEqual(enriched["domain"], "docs.example.com")
        self.assertEqual(enriched["path"], "/path/to/page")


if __name__ == "__main__":
    unittest.main()

