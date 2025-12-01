"""Unit tests for ScrapingPipeline."""

import unittest
from unittest.mock import Mock, patch, MagicMock
from scraper.pipeline import ScrapingPipeline


class TestScrapingPipeline(unittest.TestCase):
    """Test cases for ScrapingPipeline."""

    def setUp(self):
        """Set up test fixtures."""
        self.pipeline = ScrapingPipeline(
            start_url="https://example.com",
            max_pages=5,
            max_depth=2,
            delay=0.1,
            timeout=5,
            output_path="test_output.jsonl",
            respect_robots=False,
        )

    def test_init(self):
        """Test pipeline initialization."""
        self.assertIsNotNone(self.pipeline.crawler)
        self.assertIsNotNone(self.pipeline.extractor)
        self.assertIsNotNone(self.pipeline.enricher)
        self.assertIsNotNone(self.pipeline.storage)

    @patch("scraper.pipeline.Crawler")
    @patch("scraper.pipeline.ContentExtractor")
    @patch("scraper.pipeline.DocumentEnricher")
    @patch("scraper.pipeline.JSONLStorage")
    def test_run_complete_flow(self, mock_storage_class, mock_enricher_class, mock_extractor_class, mock_crawler_class):
        """Test complete pipeline run."""
        # Setup mocks
        mock_crawler = Mock()
        mock_crawler.crawl.return_value = [
            {
                "url": "https://example.com/page1",
                "content": "<html><head><title>Page 1</title></head><body><p>Content 1</p></body></html>",
                "status_code": 200,
                "content_type": "text/html",
            },
            {
                "url": "https://example.com/page2",
                "content": "<html><head><title>Page 2</title></head><body><p>Content 2</p></body></html>",
                "status_code": 200,
                "content_type": "text/html",
            },
        ]
        mock_crawler_class.return_value = mock_crawler

        mock_extractor = Mock()
        mock_extractor.extract.side_effect = [
            {"title": "Page 1", "body_text": "Content 1"},
            {"title": "Page 2", "body_text": "Content 2"},
        ]
        mock_extractor_class.return_value = mock_extractor

        mock_enricher = Mock()
        mock_enricher.enrich.side_effect = [
            {
                "url": "https://example.com/page1",
                "title": "Page 1",
                "body_text": "Content 1",
                "word_count": 2,
                "char_count": 10,
                "language": "en",
                "content_type": "page",
                "fetched_at": "2024-01-01T00:00:00Z",
            },
            {
                "url": "https://example.com/page2",
                "title": "Page 2",
                "body_text": "Content 2",
                "word_count": 2,
                "char_count": 10,
                "language": "en",
                "content_type": "page",
                "fetched_at": "2024-01-01T00:00:00Z",
            },
        ]
        mock_enricher_class.return_value = mock_enricher

        mock_storage = Mock()
        mock_storage_class.return_value = mock_storage

        # Create pipeline with mocked dependencies
        pipeline = ScrapingPipeline(
            start_url="https://example.com",
            max_pages=5,
            respect_robots=False,
        )
        pipeline.crawler = mock_crawler
        pipeline.extractor = mock_extractor
        pipeline.enricher = mock_enricher
        pipeline.storage = mock_storage

        # Run pipeline
        result = pipeline.run()

        # Verify
        self.assertEqual(len(result), 2)
        mock_crawler.crawl.assert_called_once()
        self.assertEqual(mock_extractor.extract.call_count, 2)
        self.assertEqual(mock_enricher.enrich.call_count, 2)
        mock_storage.save.assert_called_once()

    @patch("scraper.pipeline.Crawler")
    def test_run_no_pages_fetched(self, mock_crawler_class):
        """Test pipeline handles case when no pages are fetched."""
        mock_crawler = Mock()
        mock_crawler.crawl.return_value = []
        mock_crawler_class.return_value = mock_crawler

        pipeline = ScrapingPipeline(
            start_url="https://example.com",
            max_pages=5,
            respect_robots=False,
        )
        pipeline.crawler = mock_crawler

        result = pipeline.run()
        self.assertEqual(result, [])

    @patch("scraper.pipeline.Crawler")
    @patch("scraper.pipeline.ContentExtractor")
    def test_run_handles_extraction_error(self, mock_extractor_class, mock_crawler_class):
        """Test pipeline handles extraction errors gracefully."""
        mock_crawler = Mock()
        mock_crawler.crawl.return_value = [
            {
                "url": "https://example.com/page1",
                "content": "<html>Content</html>",
                "status_code": 200,
                "content_type": "text/html",
            },
        ]
        mock_crawler_class.return_value = mock_crawler

        mock_extractor = Mock()
        mock_extractor.extract.side_effect = Exception("Extraction error")
        mock_extractor_class.return_value = mock_extractor

        pipeline = ScrapingPipeline(
            start_url="https://example.com",
            max_pages=5,
            respect_robots=False,
        )
        pipeline.crawler = mock_crawler
        pipeline.extractor = mock_extractor

        # Should not raise, but log error
        result = pipeline.run()
        self.assertEqual(len(result), 0)


if __name__ == "__main__":
    unittest.main()

