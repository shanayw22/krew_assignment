"""
Content extraction and cleaning module.
"""

import re
import logging
from typing import Optional
from bs4 import BeautifulSoup, Comment

logger = logging.getLogger(__name__)


class ContentExtractor:
    """
    Extracts and cleans content from HTML pages.
    """

    # Common selectors for main content
    MAIN_CONTENT_SELECTORS = [
        "main",
        "article",
        "[role='main']",
        ".content",
        ".main-content",
        ".post-content",
        ".entry-content",
        "#content",
        "#main",
    ]

    # Selectors to remove (boilerplate)
    REMOVE_SELECTORS = [
        "nav",
        "header",
        "footer",
        "aside",
        ".sidebar",
        ".navigation",
        ".menu",
        ".footer",
        ".header",
        "script",
        "style",
        ".advertisement",
        ".ads",
        ".social-share",
        ".comments",
        ".comment-section",
    ]

    def __init__(self):
        """Initialize the content extractor."""
        pass

    def extract_title(self, soup: BeautifulSoup) -> str:
        """
        Extract page title.

        Tries multiple strategies:
        1. <title> tag
        2. <h1> tag
        3. og:title meta tag
        4. twitter:title meta tag
        """
        # Try <title> tag
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)
            if title:
                return title

        # Try <h1>
        h1_tag = soup.find("h1")
        if h1_tag:
            title = h1_tag.get_text(strip=True)
            if title:
                return title

        # Try meta tags
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"]

        twitter_title = soup.find("meta", attrs={"name": "twitter:title"})
        if twitter_title and twitter_title.get("content"):
            return twitter_title["content"]

        return "Untitled"

    def _remove_boilerplate(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Remove boilerplate elements from the soup."""
        # Remove comments
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        # Remove unwanted elements
        for selector in self.REMOVE_SELECTORS:
            for element in soup.select(selector):
                element.decompose()

        return soup

    def _find_main_content(self, soup: BeautifulSoup) -> Optional[BeautifulSoup]:
        """Find the main content area using various strategies."""
        # Try common content selectors
        for selector in self.MAIN_CONTENT_SELECTORS:
            element = soup.select_one(selector)
            if element:
                return element

        # Fallback: try to find the largest text container
        # This is a heuristic approach
        body = soup.find("body")
        if body:
            # Find the element with the most text content
            candidates = body.find_all(["div", "section", "article"])
            if candidates:
                best_candidate = max(
                    candidates,
                    key=lambda e: len(e.get_text(strip=True)),
                    default=None,
                )
                if best_candidate and len(best_candidate.get_text(strip=True)) > 100:
                    return best_candidate

        # Last resort: return body
        return soup.find("body") or soup

    def extract_body_text(self, html_content: str) -> str:
        """
        Extract and clean main body text from HTML.

        Args:
            html_content: Raw HTML content

        Returns:
            Cleaned text content
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # Remove boilerplate
            soup = self._remove_boilerplate(soup)

            # Find main content
            main_content = self._find_main_content(soup)
            if not main_content:
                # Fallback to entire body
                main_content = soup.find("body") or soup

            # Extract text
            text = main_content.get_text(separator=" ", strip=True)

            # Clean text
            text = self._clean_text(text)

            return text

        except Exception as e:
            logger.error(f"Error extracting body text: {e}")
            # Fallback: basic HTML stripping
            return self._basic_html_strip(html_content)

    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text.

        - Normalize whitespace
        - Remove excessive newlines
        - Remove leading/trailing whitespace
        """
        # Normalize whitespace (multiple spaces to single space)
        text = re.sub(r" +", " ", text)

        # Normalize newlines (multiple newlines to double newline for paragraphs)
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)

        # Remove leading/trailing whitespace from each line
        lines = [line.strip() for line in text.split("\n")]
        text = "\n".join(lines)

        # Final strip
        text = text.strip()

        return text

    def _basic_html_strip(self, html: str) -> str:
        """Basic HTML tag stripping as fallback."""
        # Remove script and style tags and their content
        html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)

        # Remove HTML tags
        html = re.sub(r"<[^>]+>", "", html)

        # Decode HTML entities
        html = html.replace("&nbsp;", " ")
        html = html.replace("&amp;", "&")
        html = html.replace("&lt;", "<")
        html = html.replace("&gt;", ">")
        html = html.replace("&quot;", '"')
        html = html.replace("&#39;", "'")

        return self._clean_text(html)

    def extract(self, html_content: str, url: str) -> dict:
        """
        Extract all content from HTML.

        Args:
            html_content: Raw HTML content
            url: URL of the page

        Returns:
            Dictionary with title and body_text
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")

            title = self.extract_title(soup)
            body_text = self.extract_body_text(html_content)

            return {
                "title": title,
                "body_text": body_text,
            }

        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return {
                "title": "Error extracting title",
                "body_text": "",
            }

