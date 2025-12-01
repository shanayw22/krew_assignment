
# Implementation

## Overview

This is a production-ready web scraping pipeline designed for AI collections workflows. It crawls websites, extracts and cleans content, enriches documents with AI-relevant metadata, and outputs structured JSONL files ready for downstream AI systems (RAG, search, fine-tuning, etc.).

## Site Chosen

**Recommended Site: [quotes.toscrape.com](http://quotes.toscrape.com/)**

This site is ideal for testing because:
- It explicitly allows scraping (designed for this purpose)
- Has a clear structure with internal links
- Contains text-rich content perfect for AI workflows
- No authentication or complex JavaScript required
- Fast and reliable for testing

**Alternative Sites:**
- Documentation sites (e.g., `https://docs.python.org`)
- Blog sites that allow scraping
- Any public site with clear content structure

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Dependencies

- `requests` - HTTP library for fetching web pages
- `beautifulsoup4` - HTML parsing and content extraction
- `lxml` - Fast XML/HTML parser (used by BeautifulSoup)

## Usage

### Basic Usage

```bash
python scrape_site.py --start-url https://quotes.toscrape.com --max-pages 50
```

### Advanced Usage

```bash
# Scrape with custom settings
python scrape_site.py \
  --start-url https://quotes.toscrape.com \
  --max-pages 100 \
  --max-depth 5 \
  --delay 1.5 \
  --output quotes.jsonl

# Scrape only specific URL patterns (e.g., documentation pages)
python scrape_site.py \
  --start-url https://docs.python.org \
  --max-pages 200 \
  --url-pattern /docs/ \
  --output python_docs.jsonl

# Append to existing file
python scrape_site.py \
  --start-url https://example.com \
  --max-pages 50 \
  --output existing.jsonl \
  --append

# Disable robots.txt checking (use with caution)
python scrape_site.py \
  --start-url https://example.com \
  --max-pages 50 \
  --no-robots
```

### Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--start-url` | Seed URL to start crawling (required) | - |
| `--max-pages` | Maximum number of pages to crawl | 100 |
| `--max-depth` | Maximum crawl depth from start URL | 5 |
| `--delay` | Delay between requests (seconds) | 1.0 |
| `--timeout` | Request timeout (seconds) | 10 |
| `--output` | Output JSONL file path | output.jsonl |
| `--url-pattern` | Filter URLs matching pattern (e.g., `/docs/`) | None |
| `--no-robots` | Don't respect robots.txt | False |
| `--append` | Append to existing output file | False |
| `--verbose`, `-v` | Enable verbose logging | False |

### Analytics

Analyze the scraped collection:

```bash
# Print statistics
python analytics.py output.jsonl

# Output as JSON
python analytics.py output.jsonl --json
```

## Data Schema

Each document in the output JSONL file follows this schema (see `schema.json` for JSON Schema):

```json
{
  "url": "https://example.com/page",
  "title": "Page Title",
  "body_text": "Cleaned main content text...",
  "char_count": 1234,
  "word_count": 200,
  "language": "en",
  "content_type": "article",
  "fetched_at": "2024-01-01T12:00:00Z",
  "reading_time_minutes": 1,
  "is_mostly_code": false,
  "domain": "example.com",
  "path": "/page"
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `url` | string | Canonical URL of the document |
| `title` | string | Page title extracted from HTML |
| `body_text` | string | Cleaned main body text (HTML removed, normalized) |
| `char_count` | integer | Character count of body_text |
| `word_count` | integer | Word count of body_text |
| `language` | string | Detected language code (ISO 639-1, e.g., "en", "es") |
| `content_type` | string | Type: "article", "doc_page", "product_page", "tutorial", "about", "page" |
| `fetched_at` | string | ISO 8601 timestamp (UTC) when document was fetched |
| `reading_time_minutes` | integer | Estimated reading time (200 words/minute) |
| `is_mostly_code` | boolean | True if content appears to be mostly code |
| `domain` | string | Domain name extracted from URL |
| `path` | string | URL path component |

## Design Decisions

### Page Selection Strategy

The crawler keeps pages that:
1. **Same domain**: Only follows links within the same domain as the start URL
2. **Not visited**: Tracks visited URLs to avoid duplicates (idempotency)
3. **Content pages**: Filters out common non-content pages:
   - Login/logout pages
   - Search result pages
   - API endpoints
   - Admin pages
   - Media files (.pdf, .jpg, etc.)
4. **Respects robots.txt**: By default, checks and respects robots.txt rules
5. **URL pattern filtering**: Optional pattern matching (e.g., only `/docs/` pages)
6. **Depth limiting**: Prevents infinite crawling with max-depth parameter

### Content Extraction Strategy

The extractor uses a multi-strategy approach:

1. **Title Extraction** (priority order):
   - `<title>` tag
   - `<h1>` tag
   - `og:title` meta tag
   - `twitter:title` meta tag
   - Fallback: "Untitled"

2. **Main Content Extraction**:
   - Tries semantic HTML5 elements: `<main>`, `<article>`, `[role='main']`
   - Falls back to common class names: `.content`, `.main-content`, `.post-content`
   - If none found, uses heuristic: finds the largest text container
   - Removes boilerplate: nav, header, footer, aside, scripts, styles, ads

3. **Text Cleaning**:
   - Strips HTML tags
   - Normalizes whitespace (multiple spaces → single space)
   - Normalizes newlines (multiple newlines → paragraph breaks)
   - Removes leading/trailing whitespace

### AI Workflow Support

The metadata fields are designed to support common AI workflows:

- **RAG (Retrieval-Augmented Generation)**: 
  - `word_count`, `char_count` help filter by length
  - `language` enables multilingual filtering
  - `content_type` allows filtering by document type
  - `is_mostly_code` helps separate code from prose

- **Search & Ranking**:
  - `reading_time_minutes` helps rank by content depth
  - `content_type` enables category-based search
  - `domain`, `path` support URL-based filtering

- **Fine-tuning & Training**:
  - `language` enables language-specific datasets
  - `content_type` allows balanced training sets
  - `word_count` helps filter training data by length
  - `fetched_at` enables temporal analysis

- **Quality Control**:
  - `char_count`, `word_count` help filter low-quality/short pages
  - `is_mostly_code` identifies code-heavy content
  - Clean `body_text` ensures high-quality input

## Project Structure

```
krew_assignment/
├── scraper/              # Main package
│   ├── __init__.py
│   ├── crawler.py        # Web crawler
│   ├── extractor.py      # Content extraction
│   ├── enricher.py       # Metadata enrichment
│   ├── storage.py         # JSONL storage
│   └── pipeline.py       # Main pipeline orchestrator
├── tests/                # Unit tests
│   ├── test_crawler.py
│   ├── test_extractor.py
│   ├── test_enricher.py
│   ├── test_storage.py
│   └── test_pipeline.py
├── scrape_site.py        # CLI entry point
├── analytics.py          # Analytics script
├── requirements.txt      # Python dependencies
├── schema.json           # JSON Schema for documents
├── Dockerfile            # Docker containerization
└── README.md             # This file
```

## Running Tests

Run all unit tests:

```bash
python -m pytest tests/ -v
```

Or using unittest:

```bash
python -m unittest discover tests -v
```

## Docker Usage

Build the Docker image:

```bash
docker build -t web-scraper .
```

Run the scraper:

```bash
docker run -v $(pwd)/output:/app/output web-scraper \
  --start-url https://quotes.toscrape.com \
  --max-pages 10 \
  --output /app/output/result.jsonl
```

## Robustness Features

### Error Handling

- **Network errors**: Handles timeouts, connection errors, HTTP errors (4xx/5xx)
- **Parsing errors**: Gracefully handles malformed HTML
- **Individual page failures**: Continues crawling even if individual pages fail
- **Retry strategy**: Automatic retries for transient errors (429, 5xx)

### Idempotency

- Tracks visited URLs to prevent duplicates
- Can append to existing files without creating duplicates
- Consistent URL normalization (removes fragments, normalizes paths)

### Throttling

- Configurable delay between requests (default: 1 second)
- Respects robots.txt crawl-delay directives
- Prevents overwhelming target servers

### Maintainability

- Clear separation of concerns:
  - `Crawler`: Discovery and fetching
  - `Extractor`: Content extraction and cleaning
  - `Enricher`: Metadata enrichment
  - `Storage`: Persistence
  - `Pipeline`: Orchestration
- Comprehensive logging for debugging
- Type hints for better code clarity
- Unit tests for all components

## Future Work

Ideas for production improvements:

1. **Scheduling & Automation**:
   - Cron-based scheduling
   - Incremental updates (only fetch changed pages)
   - Change detection using content hashing

2. **Monitoring & Observability**:
   - Metrics collection (pages crawled, errors, timing)
   - Health checks
   - Alerting for failures

3. **Advanced Features**:
   - JavaScript rendering (Selenium/Playwright) for SPAs
   - Sitemap.xml parsing for faster discovery
   - Content deduplication across sources
   - Multi-source aggregation
   - Incremental indexing

4. **Scalability**:
   - Distributed crawling (multiple workers)
   - Queue-based architecture (Redis/RabbitMQ)
   - Database storage instead of files
   - Caching layer for fetched pages

5. **Quality Improvements**:
   - Machine learning-based content extraction
   - Better language detection (using libraries like `langdetect`)
   - Content quality scoring
   - Automatic topic classification

6. **Integration**:
   - Direct integration with vector databases (Pinecone, Weaviate)
   - API endpoints for programmatic access
   - Webhook notifications on completion
   - Integration with CI/CD pipelines

## Example Output

After running the scraper, you'll get a JSONL file like:

```jsonl
{"url": "https://quotes.toscrape.com/", "title": "Quotes to Scrape", "body_text": "Quotes to Scrape\n\nLogin\n\nQuotes by Tag\n\nViewing tag: love\n\n    \"The world as we have created it is a process of our thinking. It cannot be changed without changing our thinking.\"\n    by Albert Einstein\n    (about)\n    Tags: change deep-thoughts thinking world\n\n    \"It is our choices, Harry, that show what we truly are, far more than our abilities.\"\n    by J.K. Rowling\n    (about)\n    Tags: abilities choices\n\n    \"There are only two ways to live your life. One is as though nothing is a miracle. The other is as though everything is a miracle.\"\n    by Albert Einstein\n    (about)\n    Tags: inspirational life live miracle miracles\n\nNext\n\nTop Ten tags\n\nlove\ninspirational\nlife\nhumor\nbooks\nreading\nfriendship\nfriends\ntruth\nsimile\n\nScrapinghub\n\n", "char_count": 1234, "word_count": 156, "language": "en", "content_type": "page", "fetched_at": "2024-01-01T12:00:00Z", "reading_time_minutes": 1, "is_mostly_code": false, "domain": "quotes.toscrape.com", "path": "/"}
{"url": "https://quotes.toscrape.com/page/2/", "title": "Quotes to Scrape", "body_text": "...", "char_count": 987, "word_count": 120, "language": "en", "content_type": "page", "fetched_at": "2024-01-01T12:00:05Z", "reading_time_minutes": 1, "is_mostly_code": false, "domain": "quotes.toscrape.com", "path": "/page/2/"}
```

## License

This is an assignment project. Use responsibly and respect website terms of service and robots.txt.
