"""Path utilities for locating project root and .unimem subdirectories."""

import os
from pathlib import Path
from typing import Optional

from unimem.config.constants import (
    MEM_DIR_NAME,
    EVENTS_DIR_NAME,
    SESSIONS_DIR_NAME,
    SNAPSHOTS_DIR_NAME,
    DECISIONS_DIR_NAME,
    STATE_FILE_NAME,
    MEMORY_MD_NAME,
)

def find_project_root(start_path: Optional[Path] = None) -> Path:
    """Find the project root by looking for .unimem or .git directories.
    
    Traverses parent directories from start_path (defaults to current working directory).
    If neither is found, returns the current working directory.
    """
    if start_path is None:
        start_path = Path.cwd()
        
    start_path = start_path.resolve()
    current = start_path
    
    # Traverse upwards to find .unimem or .git
    while True:
        if (current / MEM_DIR_NAME).is_dir() or (current / ".git").exists():
            return current
        
        # Stop at root
        if current.parent == current:
            break
        current = current.parent
        
    # Default to starting path
    return start_path

def get_unimem_dir(project_root: Path) -> Path:
    """Get the path to the .unimem directory."""
    return project_root / MEM_DIR_NAME

def get_events_dir(project_root: Path) -> Path:
    """Get the path to the .unimem/events directory."""
    return get_unimem_dir(project_root) / EVENTS_DIR_NAME

def get_sessions_dir(project_root: Path) -> Path:
    """Get the path to the .unimem/sessions directory."""
    return get_unimem_dir(project_root) / SESSIONS_DIR_NAME

def get_snapshots_dir(project_root: Path) -> Path:
    """Get the path to the .unimem/snapshots directory."""
    return get_unimem_dir(project_root) / SNAPSHOTS_DIR_NAME

def get_decisions_dir(project_root: Path) -> Path:
    """Get the path to the .unimem/decisions directory."""
    return get_unimem_dir(project_root) / DECISIONS_DIR_NAME

def get_state_file(project_root: Path) -> Path:
    """Get the path to .unimem/state.json."""
    return get_unimem_dir(project_root) / STATE_FILE_NAME

def get_memory_md(project_root: Path) -> Path:
    """Get the path to .unimem/memory.md."""
    return get_unimem_dir(project_root) / MEMORY_MD_NAME
