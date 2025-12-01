"""
Storage module for saving documents to JSONL format.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)


class JSONLStorage:
    """
    Handles storage of documents in JSONL (newline-delimited JSON) format.
    """

    def __init__(self, output_path: str, append: bool = False):
        """
        Initialize storage.

        Args:
            output_path: Path to output file
            append: If True, append to existing file; otherwise overwrite
        """
        self.output_path = Path(output_path)
        self.append = append

    def save(self, documents: List[Dict]) -> None:
        """
        Save documents to JSONL file.

        Args:
            documents: List of document dictionaries
        """
        mode = "a" if self.append else "w"
        try:
            with open(self.output_path, mode, encoding="utf-8") as f:
                for doc in documents:
                    json_line = json.dumps(doc, ensure_ascii=False)
                    f.write(json_line + "\n")
            logger.info(f"Saved {len(documents)} documents to {self.output_path}")
        except Exception as e:
            logger.error(f"Error saving to {self.output_path}: {e}")
            raise

    def save_single(self, document: Dict) -> None:
        """
        Save a single document (useful for streaming).

        Args:
            document: Document dictionary
        """
        mode = "a" if (self.append or self.output_path.exists()) else "w"
        try:
            with open(self.output_path, mode, encoding="utf-8") as f:
                json_line = json.dumps(document, ensure_ascii=False)
                f.write(json_line + "\n")
        except Exception as e:
            logger.error(f"Error saving document to {self.output_path}: {e}")
            raise

    def load(self) -> List[Dict]:
        """
        Load documents from JSONL file.

        Returns:
            List of document dictionaries
        """
        documents = []
        try:
            if not self.output_path.exists():
                logger.warning(f"File {self.output_path} does not exist")
                return documents

            with open(self.output_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        doc = json.loads(line)
                        documents.append(doc)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Error parsing line {line_num} in {self.output_path}: {e}")

            logger.info(f"Loaded {len(documents)} documents from {self.output_path}")
            return documents

        except Exception as e:
            logger.error(f"Error loading from {self.output_path}: {e}")
            raise

