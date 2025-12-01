"""
Crawler module for discovering and fetching web pages.
"""

import time
import logging
from typing import Set, List, Optional, Tuple
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.robotparser import RobotFileParser
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class Crawler:
    """
    Web crawler that follows internal links with throttling and error handling.
    """

    def __init__(
        self,
        start_url: str,
        max_pages: int = 100,
        max_depth: int = 5,
        delay: float = 1.0,
        timeout: int = 10,
        respect_robots: bool = True,
        url_pattern: Optional[str] = None,
    ):
        """
        Initialize the crawler.

        Args:
            start_url: Seed URL to start crawling from
            max_pages: Maximum number of pages to crawl
            max_depth: Maximum depth to crawl from start URL
            delay: Delay between requests in seconds
            timeout: Request timeout in seconds
            respect_robots: Whether to respect robots.txt
            url_pattern: Optional regex pattern to filter URLs (e.g., '/docs/')
        """
        self.start_url = start_url
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.delay = delay
        self.timeout = timeout
        self.respect_robots = respect_robots
        self.url_pattern = url_pattern

        # Parse base domain
        parsed = urlparse(start_url)
        self.base_domain = f"{parsed.scheme}://{parsed.netloc}"
        self.base_path = parsed.path.rstrip("/")

        # Track visited URLs and their depths
        self.visited: Set[str] = set()
        self.to_visit: List[Tuple[str, int]] = []  # (url, depth)
        self.fetched_pages: List[dict] = []

        # Setup session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; AI-Collection-Bot/1.0)"
        })

        # Robots.txt parser
        self.robots_parser = None
        if self.respect_robots:
            self._load_robots_txt()

    def _load_robots_txt(self):
        """Load and parse robots.txt for the domain."""
        try:
            robots_url = urljoin(self.base_domain, "/robots.txt")
            self.robots_parser = RobotFileParser()
            self.robots_parser.set_url(robots_url)
            self.robots_parser.read()
            logger.info(f"Loaded robots.txt from {robots_url}")
        except Exception as e:
            logger.warning(f"Could not load robots.txt: {e}")
            self.robots_parser = None

    def _is_allowed(self, url: str) -> bool:
        """Check if URL is allowed by robots.txt."""
        if not self.robots_parser:
            return True
        try:
            return self.robots_parser.can_fetch(self.session.headers["User-Agent"], url)
        except Exception:
            return True

    def _is_valid_url(self, url: str) -> bool:
        """
        Check if URL should be crawled.

        Filters out:
        - External domains
        - Already visited URLs
        - Non-content pages (login, search, etc.)
        - URLs not matching pattern if specified
        """
        try:
            parsed = urlparse(url)
            url_domain = f"{parsed.scheme}://{parsed.netloc}"

            # Must be same domain
            if url_domain != self.base_domain:
                return False

            # Check if already visited
            if url in self.visited:
                return False

            # Check robots.txt
            if not self._is_allowed(url):
                return False

            # Filter out common non-content pages
            path_lower = parsed.path.lower()
            # Check path and query string
            full_path = (parsed.path + "?" + parsed.query).lower() if parsed.query else path_lower
            excluded_patterns = [
                "/login",
                "/logout",
                "/signin",
                "/signup",
                "/register",
                "/search",
                "/api/",
                "/admin/",
                "/cart",
                "/checkout",
                ".pdf",
                ".jpg",
                ".jpeg",
                ".png",
                ".gif",
                ".zip",
                ".exe",
            ]
            if any(pattern in full_path for pattern in excluded_patterns):
                return False

            # Check URL pattern if specified
            if self.url_pattern and self.url_pattern not in url:
                return False

            return True

        except Exception as e:
            logger.warning(f"Error validating URL {url}: {e}")
            return False

    def _extract_links(self, html_content: str, base_url: str) -> Set[str]:
        """Extract all links from HTML content."""
        from bs4 import BeautifulSoup

        links = set()
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            for tag in soup.find_all("a", href=True):
                href = tag["href"]
                # Resolve relative URLs
                absolute_url = urljoin(base_url, href)
                # Remove fragments
                parsed = urlparse(absolute_url)
                clean_url = urlunparse((
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path,
                    parsed.params,
                    parsed.query,
                    "",  # Remove fragment
                ))
                links.add(clean_url)
        except Exception as e:
            logger.warning(f"Error extracting links from {base_url}: {e}")

        return links

    def _fetch_page(self, url: str) -> Optional[dict]:
        """Fetch a single page and return its content."""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            return {
                "url": url,
                "status_code": response.status_code,
                "content": response.text,
                "content_type": response.headers.get("Content-Type", ""),
            }
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout fetching {url}")
            return None
        except requests.exceptions.HTTPError as e:
            logger.warning(f"HTTP error fetching {url}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request error fetching {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
            return None

    def crawl(self) -> List[dict]:
        """
        Start crawling from the seed URL.

        Returns:
            List of fetched page dictionaries with url, status_code, content, content_type
        """
        logger.info(f"Starting crawl from {self.start_url}")
        self.to_visit = [(self.start_url, 0)]

        while self.to_visit and len(self.fetched_pages) < self.max_pages:
            url, depth = self.to_visit.pop(0)

            # Skip if too deep
            if depth > self.max_depth:
                continue

            # Skip if already visited
            if url in self.visited:
                continue

            # Validate URL
            if not self._is_valid_url(url):
                continue

            # Mark as visited
            self.visited.add(url)

            # Fetch page
            logger.info(f"Fetching [{len(self.fetched_pages) + 1}/{self.max_pages}]: {url}")
            page_data = self._fetch_page(url)

            if page_data:
                # Only process HTML content
                if "text/html" in page_data["content_type"]:
                    self.fetched_pages.append(page_data)

                    # Extract links for next depth level
                    if depth < self.max_depth:
                        links = self._extract_links(page_data["content"], url)
                        for link in links:
                            if link not in self.visited:
                                self.to_visit.append((link, depth + 1))

                # Throttle requests
                if len(self.fetched_pages) < self.max_pages:
                    time.sleep(self.delay)

        logger.info(f"Crawl complete. Fetched {len(self.fetched_pages)} pages.")
        return self.fetched_pages

