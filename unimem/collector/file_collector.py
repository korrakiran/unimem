"""Filesystem scanner to discover workspace files, extensions, and modification times."""

import os
from pathlib import Path
from typing import List, Dict, Any

class FileCollector:
    """Collects filesystem details and highlights important or recently changed files."""
    
    # Standard ignore directories and files
    DEFAULT_IGNORES = {
        ".git", ".unimem", ".venv", "venv", "node_modules", 
        "build", "dist", "__pycache__", ".pytest_cache", ".eggs", 
        ".DS_Store", "package-lock.json", "poetry.lock"
    }

    @classmethod
    def should_ignore(cls, path: Path, project_root: Path) -> bool:
        """Check if a file or directory should be ignored during scans."""
        try:
            rel_parts = path.relative_to(project_root).parts
        except ValueError:
            return True
            
        for part in rel_parts:
            if part in cls.DEFAULT_IGNORES:
                return True
            if part.startswith(".") and part != ".":
                return True
        return False

    @classmethod
    def scan_project(cls, project_root: Path) -> Dict[str, Any]:
        """Scan the project and return file counts, size summaries, and extension statistics."""
        extensions: Dict[str, int] = {}
        total_size = 0
        total_files = 0
        all_files: List[Path] = []
        
        for root, dirs, files in os.walk(project_root):
            # Prune ignored directories in-place to prevent traversing them
            dirs[:] = [d for d in dirs if not cls.should_ignore(Path(root) / d, project_root)]
            
            for file in files:
                file_path = Path(root) / file
                if cls.should_ignore(file_path, project_root):
                    continue
                    
                total_files += 1
                try:
                    size = file_path.stat().st_size
                    total_size += size
                except Exception:
                    size = 0
                    
                ext = file_path.suffix.lower() or "no_ext"
                extensions[ext] = extensions.get(ext, 0) + 1
                all_files.append(file_path)
                
        return {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "extension_counts": extensions,
            "files": all_files
        }

    @classmethod
    def get_recently_modified_files(cls, project_root: Path, limit: int = 10) -> List[str]:
        """Get relative paths of files modified recently, sorted by modification time descending."""
        scan_results = cls.scan_project(project_root)
        files = scan_results.get("files", [])
        
        file_mtimes = []
        for f in files:
            try:
                mtime = f.stat().st_mtime
                file_mtimes.append((f, mtime))
            except Exception:
                pass
                
        # Sort by mtime descending
        file_mtimes.sort(key=lambda item: item[1], reverse=True)
        
        recent = []
        for f, _ in file_mtimes[:limit]:
            try:
                rel_path = str(f.relative_to(project_root))
                recent.append(rel_path)
            except ValueError:
                pass
                
        return recent
