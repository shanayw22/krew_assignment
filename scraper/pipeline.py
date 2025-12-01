"""
Main pipeline that orchestrates crawling, extraction, and enrichment.
"""

import logging
from typing import List, Dict, Optional
from .crawler import Crawler
from .extractor import ContentExtractor
from .enricher import DocumentEnricher
from .storage import JSONLStorage

logger = logging.getLogger(__name__)


class ScrapingPipeline:
    """
    Main pipeline that coordinates crawling, extraction, enrichment, and storage.
    """

    def __init__(
        self,
        start_url: str,
        max_pages: int = 100,
        max_depth: int = 5,
        delay: float = 1.0,
        timeout: int = 10,
        output_path: str = "output.jsonl",
        url_pattern: Optional[str] = None,
        respect_robots: bool = True,
        append: bool = False,
    ):
        """
        Initialize the scraping pipeline.

        Args:
            start_url: Seed URL to start crawling
            max_pages: Maximum number of pages to crawl
            max_depth: Maximum crawl depth
            delay: Delay between requests (seconds)
            timeout: Request timeout (seconds)
            output_path: Path to output JSONL file
            url_pattern: Optional URL pattern filter
            respect_robots: Whether to respect robots.txt
            append: Append to existing output file instead of overwriting
        """
        self.crawler = Crawler(
            start_url=start_url,
            max_pages=max_pages,
            max_depth=max_depth,
            delay=delay,
            timeout=timeout,
            url_pattern=url_pattern,
            respect_robots=respect_robots,
        )
        self.extractor = ContentExtractor()
        self.enricher = DocumentEnricher()
        self.storage = JSONLStorage(output_path, append=append)

    def run(self) -> List[Dict]:
        """
        Run the complete scraping pipeline.

        Returns:
            List of enriched document dictionaries
        """
        logger.info("Starting scraping pipeline")

        # Step 1: Crawl
        logger.info("Step 1: Crawling pages...")
        fetched_pages = self.crawler.crawl()

        if not fetched_pages:
            logger.warning("No pages were fetched")
            return []

        # Step 2: Extract and enrich
        logger.info("Step 2: Extracting and enriching content...")
        enriched_documents = []

        for page_data in fetched_pages:
            try:
                # Extract content
                extracted = self.extractor.extract(page_data["content"], page_data["url"])

                # Create base document
                document = {
                    "url": page_data["url"],
                    "title": extracted["title"],
                    "body_text": extracted["body_text"],
                }

                # Enrich with metadata
                enriched = self.enricher.enrich(document)
                enriched_documents.append(enriched)

            except Exception as e:
                logger.error(f"Error processing {page_data.get('url', 'unknown')}: {e}")
                continue

        # Step 3: Save
        logger.info("Step 3: Saving documents...")
        self.storage.save(enriched_documents)

        logger.info(f"Pipeline complete. Processed {len(enriched_documents)} documents.")
        return enriched_documents

