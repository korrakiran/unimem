"""Filesystem watcher management using Watchdog observers."""

import time
from pathlib import Path
from typing import Optional
from watchdog.observers import Observer
from unimem.watcher.handlers import UnimemFileSystemEventHandler
from unimem.utils.logger import logger

class FilesystemWatcher:
    """Manages the startup and shutdown of the filesystem watch service."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.handler = UnimemFileSystemEventHandler(project_root)
        self.observer: Optional[Observer] = None

    def start(self) -> None:
        """Start monitoring the project directory for file events."""
        logger.info(f"[cyan]Starting Unimem filesystem watcher on {self.project_root}...[/cyan]")
        
        self.observer = Observer()
        self.observer.schedule(self.handler, path=str(self.project_root), recursive=True)
        self.observer.start()
        
        logger.info("[green]Watcher service is running. Press Ctrl+C to exit.[/green]")

    def stop(self) -> None:
        """Stop the filesystem monitor."""
        if self.observer:
            logger.info("Stopping filesystem watcher...")
            self.observer.stop()
            self.observer.join()
            self.observer = None
            logger.info("Watcher service stopped.")

    def run_forever(self) -> None:
        """Keep the watcher running until interrupted (blocking)."""
        self.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Watcher interrupted by user.")
        finally:
            self.stop()
