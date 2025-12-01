#!/usr/bin/env python3
"""
Analytics script for analyzing scraped documents.
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from scraper.storage import JSONLStorage


def load_documents(file_path: str):
    """Load documents from JSONL file."""
    storage = JSONLStorage(file_path)
    return storage.load()


def print_statistics(documents):
    """Print statistics about the document collection."""
    if not documents:
        print("No documents found.")
        return

    print(f"\n{'='*60}")
    print("DOCUMENT COLLECTION STATISTICS")
    print(f"{'='*60}\n")

    # Basic counts
    print(f"Total Documents: {len(documents)}")

    # Word and character counts
    word_counts = [doc.get("word_count", 0) for doc in documents]
    char_counts = [doc.get("char_count", 0) for doc in documents]

    if word_counts:
        print(f"\nWord Count Statistics:")
        print(f"  Average: {sum(word_counts) / len(word_counts):.1f}")
        print(f"  Median: {sorted(word_counts)[len(word_counts) // 2]}")
        print(f"  Min: {min(word_counts)}")
        print(f"  Max: {max(word_counts)}")

    if char_counts:
        print(f"\nCharacter Count Statistics:")
        print(f"  Average: {sum(char_counts) / len(char_counts):.1f}")
        print(f"  Median: {sorted(char_counts)[len(char_counts) // 2]}")
        print(f"  Min: {min(char_counts)}")
        print(f"  Max: {max(char_counts)}")

    # Language distribution
    languages = [doc.get("language", "unknown") for doc in documents]
    language_counts = Counter(languages)
    print(f"\nLanguage Distribution:")
    for lang, count in language_counts.most_common():
        percentage = (count / len(documents)) * 100
        print(f"  {lang}: {count} ({percentage:.1f}%)")

    # Content type distribution
    content_types = [doc.get("content_type", "unknown") for doc in documents]
    type_counts = Counter(content_types)
    print(f"\nContent Type Distribution:")
    for content_type, count in type_counts.most_common():
        percentage = (count / len(documents)) * 100
        print(f"  {content_type}: {count} ({percentage:.1f}%)")

    # Reading time statistics
    reading_times = [doc.get("reading_time_minutes", 0) for doc in documents]
    if reading_times:
        total_reading_time = sum(reading_times)
        avg_reading_time = sum(reading_times) / len(reading_times)
        print(f"\nReading Time Statistics:")
        print(f"  Total: {total_reading_time} minutes")
        print(f"  Average: {avg_reading_time:.1f} minutes per document")

    # Code content
    code_docs = sum(1 for doc in documents if doc.get("is_mostly_code", False))
    print(f"\nCode Content:")
    print(f"  Documents with mostly code: {code_docs} ({code_docs/len(documents)*100:.1f}%)")

    # Domain distribution
    domains = [doc.get("domain", "unknown") for doc in documents]
    domain_counts = Counter(domains)
    if len(domain_counts) > 1:
        print(f"\nDomain Distribution:")
        for domain, count in domain_counts.most_common():
            percentage = (count / len(documents)) * 100
            print(f"  {domain}: {count} ({percentage:.1f}%)")

    print(f"\n{'='*60}\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze scraped document collection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "input_file",
        help="Path to input JSONL file",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output statistics as JSON",
    )

    args = parser.parse_args()

    # Check if file exists
    if not Path(args.input_file).exists():
        print(f"Error: File '{args.input_file}' does not exist.", file=sys.stderr)
        sys.exit(1)

    try:
        documents = load_documents(args.input_file)

        if args.json:
            # Output as JSON
            stats = {
                "total_documents": len(documents),
                "word_count": {
                    "average": sum(doc.get("word_count", 0) for doc in documents) / len(documents) if documents else 0,
                    "min": min((doc.get("word_count", 0) for doc in documents), default=0),
                    "max": max((doc.get("word_count", 0) for doc in documents), default=0),
                },
                "language_distribution": dict(Counter(doc.get("language", "unknown") for doc in documents)),
                "content_type_distribution": dict(Counter(doc.get("content_type", "unknown") for doc in documents)),
            }
            print(json.dumps(stats, indent=2))
        else:
            print_statistics(documents)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

