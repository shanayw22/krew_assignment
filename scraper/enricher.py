"""
Enrichment module for adding AI-relevant metadata to documents.
"""

import re
import logging
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class DocumentEnricher:
    """
    Enriches documents with metadata useful for AI workflows.
    """

    # Common language patterns (simple heuristic)
    LANGUAGE_PATTERNS = {
        "en": [
            r"\bthe\b",
            r"\band\b",
            r"\bis\b",
            r"\bto\b",
            r"\bof\b",
        ],
        "es": [
            r"\bel\b",
            r"\bla\b",
            r"\bde\b",
            r"\bque\b",
            r"\by\b",
        ],
        "fr": [
            r"\ble\b",
            r"\bla\b",
            r"\bde\b",
            r"\bet\b",
            r"\bà\b",
        ],
        "de": [
            r"\bder\b",
            r"\bdie\b",
            r"\bund\b",
            r"\bin\b",
            r"\bist\b",
        ],
    }

    # Content type patterns based on URL path
    CONTENT_TYPE_PATTERNS = {
        "article": [r"/article/", r"/post/", r"/blog/", r"/news/"],
        "doc_page": [r"/docs/", r"/documentation/", r"/guide/", r"/manual/"],
        "product_page": [r"/product/", r"/item/", r"/shop/"],
        "tutorial": [r"/tutorial/", r"/how-to/", r"/learn/"],
        "about": [r"/about", r"/contact", r"/team"],
    }

    def __init__(self):
        """Initialize the document enricher."""
        pass

    def detect_language(self, text: str) -> str:
        """
        Simple language detection heuristic.

        Args:
            text: Text content to analyze

        Returns:
            Language code (default: 'en')
        """
        if not text or len(text) < 50:
            return "en"  # Default

        text_lower = text.lower()
        scores = {}

        for lang, patterns in self.LANGUAGE_PATTERNS.items():
            score = sum(len(re.findall(pattern, text_lower, re.IGNORECASE)) for pattern in patterns)
            scores[lang] = score

        if scores:
            detected_lang = max(scores, key=scores.get)
            if scores[detected_lang] > 0:
                return detected_lang

        return "en"  # Default to English

    def detect_content_type(self, url: str, title: str, body_text: str) -> str:
        """
        Detect content type based on URL, title, and content.

        Args:
            url: Page URL
            title: Page title
            body_text: Body text content

        Returns:
            Content type string
        """
        url_lower = url.lower()
        title_lower = title.lower()

        # Check URL patterns
        for content_type, patterns in self.CONTENT_TYPE_PATTERNS.items():
            if any(pattern in url_lower for pattern in patterns):
                return content_type

        # Check title patterns
        if any(word in title_lower for word in ["tutorial", "how to", "guide"]):
            return "tutorial"
        if any(word in title_lower for word in ["blog", "post", "article"]):
            return "article"
        if any(word in title_lower for word in ["documentation", "docs", "api"]):
            return "doc_page"

        # Default
        return "page"

    def estimate_reading_time(self, word_count: int) -> int:
        """
        Estimate reading time in minutes.

        Assumes average reading speed of 200 words per minute.

        Args:
            word_count: Number of words

        Returns:
            Estimated reading time in minutes
        """
        return max(1, round(word_count / 200))

    def is_mostly_code(self, text: str) -> bool:
        """
        Heuristic to detect if content is mostly code.

        Args:
            text: Text content

        Returns:
            True if content appears to be mostly code
        """
        if not text:
            return False

        # Count code-like patterns
        code_indicators = [
            r"function\s+\w+\s*\(",
            r"def\s+\w+\s*\(",
            r"class\s+\w+",
            r"import\s+\w+",
            r"#include",
            r"<\?php",
            r"console\.log",
            r"\.getElementById",
        ]

        code_matches = sum(len(re.findall(pattern, text, re.IGNORECASE)) for pattern in code_indicators)
        total_length = len(text)

        # If code indicators make up significant portion, likely code
        # Require at least 3 matches and code density > 1% (code_matches * 100 chars per match)
        return code_matches >= 3 and (code_matches * 100) > total_length

    def enrich(self, document: dict) -> dict:
        """
        Enrich a document with metadata.

        Args:
            document: Base document with url, title, body_text

        Returns:
            Enriched document with additional metadata
        """
        body_text = document.get("body_text", "")
        url = document.get("url", "")

        # Basic counts
        char_count = len(body_text)
        word_count = len(body_text.split()) if body_text else 0

        # Language detection
        language = self.detect_language(body_text)

        # Content type
        content_type = self.detect_content_type(url, document.get("title", ""), body_text)

        # Timestamp
        fetched_at = datetime.now(timezone.utc).isoformat()

        # Additional signals
        reading_time = self.estimate_reading_time(word_count)
        is_mostly_code = self.is_mostly_code(body_text)

        # Extract domain and path for potential filtering
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        path = parsed_url.path

        # Build enriched document
        enriched = {
            **document,
            "char_count": char_count,
            "word_count": word_count,
            "language": language,
            "content_type": content_type,
            "fetched_at": fetched_at,
            "reading_time_minutes": reading_time,
            "is_mostly_code": is_mostly_code,
            "domain": domain,
            "path": path,
        }

        return enriched

