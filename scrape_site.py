#!/usr/bin/env python3
"""
CLI script for running the web scraping pipeline.
"""

import argparse
import logging
import sys
from scraper.pipeline import ScrapingPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Web scraping pipeline for AI collections workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python scrape_site.py --start-url https://quotes.toscrape.com --max-pages 50

  # With custom output and URL pattern
  python scrape_site.py --start-url https://docs.python.org --max-pages 100 \\
    --output docs.jsonl --url-pattern /docs/

  # Fast crawl with lower delay
  python scrape_site.py --start-url https://quotes.toscrape.com \\
    --max-pages 20 --delay 0.5
        """,
    )

    parser.add_argument(
        "--start-url",
        required=True,
        help="Seed URL to start crawling from",
    )

    parser.add_argument(
        "--max-pages",
        type=int,
        default=100,
        help="Maximum number of pages to crawl (default: 100)",
    )

    parser.add_argument(
        "--max-depth",
        type=int,
        default=5,
        help="Maximum crawl depth from start URL (default: 5)",
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay between requests in seconds (default: 1.0)",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Request timeout in seconds (default: 10)",
    )

    parser.add_argument(
        "--output",
        default="output.jsonl",
        help="Output JSONL file path (default: output.jsonl)",
    )

    parser.add_argument(
        "--url-pattern",
        default=None,
        help="Optional URL pattern to filter pages (e.g., '/docs/')",
    )

    parser.add_argument(
        "--no-robots",
        action="store_true",
        help="Don't respect robots.txt",
    )

    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to existing output file instead of overwriting",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate arguments
    if args.max_pages < 1:
        logger.error("--max-pages must be at least 1")
        sys.exit(1)

    if args.delay < 0:
        logger.error("--delay must be non-negative")
        sys.exit(1)

    if args.timeout < 1:
        logger.error("--timeout must be at least 1")
        sys.exit(1)

    try:
        # Create and run pipeline
        pipeline = ScrapingPipeline(
            start_url=args.start_url,
            max_pages=args.max_pages,
            max_depth=args.max_depth,
            delay=args.delay,
            timeout=args.timeout,
            output_path=args.output,
            url_pattern=args.url_pattern,
            respect_robots=not args.no_robots,
            append=args.append,
        )

        documents = pipeline.run()

        if documents:
            logger.info(f"Successfully scraped {len(documents)} documents")
            logger.info(f"Output saved to {args.output}")
            sys.exit(0)
        else:
            logger.warning("No documents were scraped")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=args.verbose)
        sys.exit(1)


if __name__ == "__main__":
    main()

