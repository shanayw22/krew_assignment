"""Unit tests for JSONLStorage."""

import unittest
import json
import tempfile
import os
from scraper.storage import JSONLStorage


class TestJSONLStorage(unittest.TestCase):
    """Test cases for JSONLStorage."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl")
        self.temp_file.close()
        self.storage = JSONLStorage(self.temp_file.name, append=False)

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_save_single_document(self):
        """Test saving a single document."""
        document = {
            "url": "https://example.com",
            "title": "Test",
            "body_text": "Content",
        }

        self.storage.save_single(document)

        # Verify file was created
        self.assertTrue(os.path.exists(self.temp_file.name))

        # Read and verify content
        with open(self.temp_file.name, "r") as f:
            line = f.readline().strip()
            loaded = json.loads(line)
            self.assertEqual(loaded["url"], document["url"])
            self.assertEqual(loaded["title"], document["title"])

    def test_save_multiple_documents(self):
        """Test saving multiple documents."""
        documents = [
            {"url": "https://example.com/1", "title": "Page 1", "body_text": "Content 1"},
            {"url": "https://example.com/2", "title": "Page 2", "body_text": "Content 2"},
            {"url": "https://example.com/3", "title": "Page 3", "body_text": "Content 3"},
        ]

        self.storage.save(documents)

        # Verify all documents were saved
        loaded = self.storage.load()
        self.assertEqual(len(loaded), 3)
        self.assertEqual(loaded[0]["url"], documents[0]["url"])
        self.assertEqual(loaded[1]["url"], documents[1]["url"])
        self.assertEqual(loaded[2]["url"], documents[2]["url"])

    def test_load_documents(self):
        """Test loading documents from file."""
        documents = [
            {"url": "https://example.com/1", "title": "Page 1", "body_text": "Content 1"},
            {"url": "https://example.com/2", "title": "Page 2", "body_text": "Content 2"},
        ]

        self.storage.save(documents)

        # Load and verify
        loaded = self.storage.load()
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0]["title"], "Page 1")
        self.assertEqual(loaded[1]["title"], "Page 2")

    def test_load_nonexistent_file(self):
        """Test loading from non-existent file returns empty list."""
        storage = JSONLStorage("/nonexistent/file.jsonl")
        loaded = storage.load()
        self.assertEqual(loaded, [])

    def test_append_mode(self):
        """Test append mode."""
        documents1 = [{"url": "https://example.com/1", "title": "Page 1", "body_text": "Content 1"}]
        documents2 = [{"url": "https://example.com/2", "title": "Page 2", "body_text": "Content 2"}]

        # Save first batch
        storage1 = JSONLStorage(self.temp_file.name, append=False)
        storage1.save(documents1)

        # Append second batch
        storage2 = JSONLStorage(self.temp_file.name, append=True)
        storage2.save(documents2)

        # Verify both are present
        loaded = storage1.load()
        self.assertEqual(len(loaded), 2)

    def test_unicode_content(self):
        """Test saving and loading unicode content."""
        document = {
            "url": "https://example.com",
            "title": "Test with émojis 🎉 and unicode 中文",
            "body_text": "Content with special chars: ñ, ü, 日本語",
        }

        self.storage.save_single(document)
        loaded = self.storage.load()

        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["title"], document["title"])
        self.assertEqual(loaded[0]["body_text"], document["body_text"])

    def test_empty_documents_list(self):
        """Test saving empty documents list."""
        self.storage.save([])
        loaded = self.storage.load()
        self.assertEqual(loaded, [])


if __name__ == "__main__":
    unittest.main()

