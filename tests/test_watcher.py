"""Tests for filesystem watchdog event handlers."""

from pathlib import Path
from watchdog.events import FileCreatedEvent, FileModifiedEvent, FileDeletedEvent, FileMovedEvent
from unimem.watcher.handlers import UnimemFileSystemEventHandler
from unimem.memory.manager import MemoryManager
from unimem.utils.paths import get_events_dir

def test_watcher_should_process(temp_dir):
    """Verify file filters ignore .git, .unimem, and cache dirs."""
    handler = UnimemFileSystemEventHandler(temp_dir)
    
    assert handler._should_process(str(temp_dir / "main.py"))
    assert handler._should_process(str(temp_dir / "src" / "index.js"))
    
    # Should ignore files in ignored dirs
    assert not handler._should_process(str(temp_dir / ".git" / "config"))
    assert not handler._should_process(str(temp_dir / ".unimem" / "state.json"))
    assert not handler._should_process(str(temp_dir / "__pycache__" / "app.pyc"))
    assert not handler._should_process(str(temp_dir / ".venv" / "bin" / "pip"))

def test_watcher_records_event(initialized_unimem):
    """Verify that file events write events via MemoryManager."""
    handler = UnimemFileSystemEventHandler(initialized_unimem)
    manager = MemoryManager(initialized_unimem)
    
    # Pre-count events
    events_dir = get_events_dir(initialized_unimem)
    initial_event_count = len(list(events_dir.glob("*.json")))
    
    # Simulate a file creation event
    test_file = initialized_unimem / "new_module.py"
    event = FileCreatedEvent(str(test_file))
    handler.on_created(event)
    handler.batch_operations()
    
    # Verify a new event was recorded
    event_files = list(events_dir.glob("*.json"))
    assert len(event_files) == initial_event_count + 1
    
    # Sort and load the latest event
    event_files.sort(key=lambda p: p.name)
    latest_event_file = event_files[-1]
    
    from unimem.storage.json_store import JsonStore
    from unimem.memory.schemas import Event
    
    ev_data = JsonStore.load(latest_event_file)
    recorded_event = Event(**ev_data)
    
    assert recorded_event.tool == "watcher"
    assert recorded_event.event_type == "file_created"
    assert "new_module.py" in recorded_event.files_changed
