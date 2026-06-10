"""Watchdog file event handler to convert filesystem notifications into Unimem events."""

from pathlib import Path
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from unimem.memory.manager import MemoryManager
from unimem.memory.schemas import Event
from unimem.collector.file_collector import FileCollector
from unimem.utils.logger import logger
from unimem.utils.timestamps import get_timestamp_str

class UnimemFileSystemEventHandler(FileSystemEventHandler):
    """Listens to filesystem events and writes event summaries to Unimem."""

    def __init__(self, project_root: Path):
        super().__init__()
        self.project_root = project_root
        self.manager = MemoryManager(project_root)

    def _should_process(self, path_str: str) -> bool:
        """Filter out files that should be ignored."""
        path = Path(path_str)
        # Avoid processing directories as file changes
        if path.is_dir():
            return False
        return not FileCollector.should_ignore(path, self.project_root)

    def _record_file_event(self, event_type: str, path: str, dest_path: str = "") -> None:
        """Create and write a filesystem event to Unimem."""
        try:
            rel_path = str(Path(path).relative_to(self.project_root))
            files = [rel_path]
            
            if event_type == "moved" and dest_path:
                rel_dest = str(Path(dest_path).relative_to(self.project_root))
                files.append(rel_dest)
                summary = f"Moved file from '{rel_path}' to '{rel_dest}'"
            elif event_type == "created":
                summary = f"Created file '{rel_path}'"
            elif event_type == "deleted":
                summary = f"Deleted file '{rel_path}'"
            else:
                summary = f"Modified file '{rel_path}'"

            # Avoid recording events if Unimem is not initialized
            if not self.manager.is_initialized():
                return

            event = Event(
                tool="watcher",
                event_type=f"file_{event_type}",
                prompt="",
                response_summary=summary,
                files_changed=files
            )
            self.manager.record_event(event, auto_snapshot=True)
            logger.debug(f"[watcher] Recorded {event_type} event for {rel_path}")
        except Exception as e:
            logger.debug(f"Error handling watcher event: {e}")

    def on_created(self, event: FileSystemEvent) -> None:
        if self._should_process(event.src_path):
            self._record_file_event("created", event.src_path)

    def on_modified(self, event: FileSystemEvent) -> None:
        if self._should_process(event.src_path):
            self._record_file_event("modified", event.src_path)

    def on_deleted(self, event: FileSystemEvent) -> None:
        if self._should_process(event.src_path):
            self._record_file_event("deleted", event.src_path)

    def on_moved(self, event: FileSystemEvent) -> None:
        # dest_path is present in moved event
        if self._should_process(event.src_path) or (hasattr(event, 'dest_path') and self._should_process(event.dest_path)):
            dest = getattr(event, 'dest_path', "")
            self._record_file_event("moved", event.src_path, dest)
