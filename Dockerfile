FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY scraper/ ./scraper/
COPY scrape_site.py .
COPY analytics.py .

# Create output directory
RUN mkdir -p /app/output

# Set default command
ENTRYPOINT ["python", "scrape_site.py"]

# Example usage:
# docker build -t web-scraper .
# docker run -v $(pwd)/output:/app/output web-scraper \
#   --start-url https://quotes.toscrape.com --max-pages 10 --output /app/output/result.jsonl

