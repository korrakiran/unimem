"""Low-level file storage utility for writing and reading raw file contents."""

import os
from pathlib import Path
from typing import Union

class FileStore:
    """Manages raw file operations with automatic directory creation."""

    @staticmethod
    def write(path: Union[str, Path], content: str) -> None:
        """Write text content to a file, creating parent directories if they don't exist."""
        target_path = Path(path)
        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            raise IOError(f"Failed to write to file {target_path}: {e}") from e

    @staticmethod
    def read(path: Union[str, Path]) -> str:
        """Read text content from a file. Raises FileNotFoundError if it doesn't exist."""
        target_path = Path(path)
        if not target_path.exists():
            raise FileNotFoundError(f"File not found: {target_path}")
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            raise IOError(f"Failed to read from file {target_path}: {e}") from e

    @staticmethod
    def delete(path: Union[str, Path]) -> None:
        """Delete a file if it exists."""
        target_path = Path(path)
        if target_path.exists():
            try:
                target_path.unlink()
            except Exception as e:
                raise IOError(f"Failed to delete file {target_path}: {e}") from e
