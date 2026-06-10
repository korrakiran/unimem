"""JSON file storage utility for structured data access."""

import json
from pathlib import Path
from typing import Any, Union
from unimem.storage.file_store import FileStore

class JsonStore:
    """Manages reading and writing JSON files."""

    @staticmethod
    def save(path: Union[str, Path], data: Any, indent: int = 2) -> None:
        """Serialize and save data to a JSON file."""
        try:
            content = json.dumps(data, indent=indent, default=str)
            FileStore.write(path, content)
        except Exception as e:
            raise IOError(f"Failed to serialize JSON to {path}: {e}") from e

    @staticmethod
    def load(path: Union[str, Path]) -> Any:
        """Load and deserialize data from a JSON file."""
        target_path = Path(path)
        content = FileStore.read(target_path)
        try:
            return json.loads(content)
        except Exception as e:
            raise ValueError(f"Failed to parse JSON from {target_path}: {e}") from e
