import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from watchdog.events import FileModifiedEvent

from unimem.memory.manager import MemoryManager
from unimem.memory.schemas import Event
from unimem.watcher.handlers import UnimemFileSystemEventHandler
from unimem.adapters.generic import GenericAdapter
from unimem.storage.json_store import JsonStore
from unimem.utils.paths import get_events_dir, get_state_file

def test_batch_state_syncs(initialized_unimem):
    """Verify that file events are batched and processed in groups of 5."""
    handler = UnimemFileSystemEventHandler(initialized_unimem)
    events_dir = get_events_dir(initialized_unimem)
    
    # 1. Enqueue 4 events - should not write to disk yet
    initial_event_count = len(list(events_dir.glob("*.json")))
    for i in range(4):
        test_file = initialized_unimem / f"file_{i}.txt"
        handler.on_modified(FileModifiedEvent(str(test_file)))
        
    assert len(handler._pending_events) == 4
    assert len(list(events_dir.glob("*.json"))) == initial_event_count
    
    # 2. Enqueue the 5th event - should trigger batch_operations flush
    test_file_5 = initialized_unimem / "file_4.txt"
    handler.on_modified(FileModifiedEvent(str(test_file_5)))
    
    assert len(handler._pending_events) == 0
    assert len(list(events_dir.glob("*.json"))) == initial_event_count + 5

def test_lazy_load_memory_md(initialized_unimem):
    """Verify that memory.md is lazy-loaded and not read/injected unnecessarily."""
    manager = MemoryManager(initialized_unimem)
    
    # 1. Verify load_state with reconcile_memory=False skips memory reconciliation
    state_file = get_state_file(initialized_unimem)
    memory_file = initialized_unimem / ".unimem" / "memory.md"
    
    # Modify memory.md manually to have a later mtime
    new_mtime = state_file.stat().st_mtime + 10
    memory_file.write_text("# Unimem Project Memory: LazyProj\n\n---\n\n## 🎯 Current Focus\n* **Current Goal**: Goal modified in memory\n", encoding="utf-8")
    os.utime(memory_file, (new_mtime, new_mtime))
    
    # Load state with reconcile_memory=False -> goal should remain unchanged
    state_no_rec = manager.load_state(reconcile_memory=False)
    assert state_no_rec.current_goal == "Initialize the repository and basic components"
    
    # Load state with reconcile_memory=True -> goal should be updated
    state_rec = manager.load_state(reconcile_memory=True)
    assert state_rec.current_goal == "Goal modified in memory"

    # 2. Verify lazy-loading in GenericAdapter context injection
    adapter = GenericAdapter(initialized_unimem)
    
    # Case A: Task/Goal requires memory (contains 'plan')
    state = manager.load_state()
    state.current_task = "Write test plan for optimizations"
    manager.save_state(state)
    context_a = adapter.load_context()
    assert "Goal modified in memory" in context_a["context_md"]
    
    # Case B: Task/Goal does not require memory (simple coding task)
    state = manager.load_state()
    state.current_task = "Fix typo in utils"
    state.current_goal = "Routine maintenance"
    manager.save_state(state)
    context_b = adapter.load_context()
    assert context_b["context_md"] == "Unimem active. Read .unimem/memory.md for full project memory."

def test_archive_completed_tasks(initialized_unimem):
    """Verify that completed tasks older than 7 days are archived and pruned from state.json."""
    manager = MemoryManager(initialized_unimem)
    state = manager.load_state()
    
    # Setup completed tasks
    state.completed_features = ["Recent Task", "Old Task"]
    state.file_history = []
    manager.save_state(state)
    
    # Record events with timestamps representing task completions
    # 'Recent Task' completed now
    now_str = datetime.now(timezone.utc).isoformat()
    manager.record_event(Event(
        tool="unimem_cli",
        event_type="task_completed",
        response_summary="Completed Recent Task",
        task="Recent Task",
        timestamp=now_str
    ))
    
    # 'Old Task' completed 10 days ago
    old_str = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    manager.record_event(Event(
        tool="unimem_cli",
        event_type="task_completed",
        response_summary="Completed Old Task",
        task="Old Task",
        timestamp=old_str
    ))
    
    # Force rebuild state to ensure events are compiled
    manager.rebuild_state_from_events(update_memory=False)
    
    # Re-run save_state to trigger archiving
    updated_state = manager.load_state()
    manager.save_state(updated_state)
    
    # Verify pruned state
    final_state = manager.load_state()
    assert "Recent Task" in final_state.completed_features
    assert "Old Task" not in final_state.completed_features
    
    # Verify archive file
    archive_file = initialized_unimem / ".unimem" / "archive.json"
    assert archive_file.exists()
    archive_data = JsonStore.load(archive_file)
    completed_tasks = [t["task"] for t in archive_data["completed_tasks"]]
    assert "Old Task" in completed_tasks

def test_delta_tracking(initialized_unimem):
    """Verify that file history is deduplicated by file path (delta tracking)."""
    manager = MemoryManager(initialized_unimem)
    
    # Record multiple events modifying the same file
    manager.record_event(Event(
        tool="watcher",
        event_type="file_modified",
        files_changed=["src/main.py"],
        timestamp=datetime.now(timezone.utc).isoformat()
    ))
    
    manager.record_event(Event(
        tool="watcher",
        event_type="file_modified",
        files_changed=["src/main.py"],
        timestamp=(datetime.now(timezone.utc) + timedelta(seconds=5)).isoformat()
    ))
    
    # Verify only one entry exists for src/main.py in file_history
    state = manager.load_state()
    main_ops = [op for op in state.file_history if op.file_path == "src/main.py"]
    assert len(main_ops) == 1
