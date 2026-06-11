"""Tests for MemoryManager logic."""

import os
from pathlib import Path
from unimem.memory.manager import MemoryManager
from unimem.memory.schemas import ProjectState, Event
from unimem.utils.paths import (
    get_state_file,
    get_memory_md,
    get_events_dir,
    get_sessions_dir,
    get_decisions_dir,
)

def test_manager_initialization(temp_dir):
    """Verify that initialize creates correct files and folders."""
    manager = MemoryManager(temp_dir)
    assert not manager.is_initialized()
    
    manager.initialize("NewProj", "Description of project")
    assert manager.is_initialized()
    
    # Check folder directories exist
    assert get_events_dir(temp_dir).is_dir()
    assert get_sessions_dir(temp_dir).is_dir()
    assert get_decisions_dir(temp_dir).is_dir()
    
    # Check initial files exist
    assert get_state_file(temp_dir).exists()
    assert get_memory_md(temp_dir).exists()
    
    # Validate loaded state
    state = manager.load_state()
    assert state.project_name == "NewProj"
    assert state.description == "Description of project"

def test_manager_save_state(initialized_unimem):
    """Verify that saving state writes to disk and updates memory.md."""
    manager = MemoryManager(initialized_unimem)
    state = manager.load_state()
    
    state.current_goal = "Build Auth"
    state.completed_features.append("Database Setup")
    manager.save_state(state)
    
    # Reload and verify
    reloaded_state = manager.load_state()
    assert reloaded_state.current_goal == "Build Auth"
    assert "Database Setup" in reloaded_state.completed_features
    
    # Check if memory.md contains updated values
    md_content = get_memory_md(initialized_unimem).read_text(encoding="utf-8")
    assert "Build Auth" in md_content
    assert "Database Setup" in md_content

def test_manager_record_event(initialized_unimem):
    """Verify event tracking write operations."""
    manager = MemoryManager(initialized_unimem)
    
    event = Event(
        tool="test_tool",
        event_type="custom_action",
        prompt="do something",
        response_summary="did something",
        files_changed=["main.py"]
    )
    
    event_file = manager.record_event(event, auto_snapshot=False)
    assert event_file.exists()
    assert event_file.parent == get_events_dir(initialized_unimem)
    
    # Check if state was updated
    state = manager.load_state()
    assert "test_tool" in state.tool_history
    assert "main.py" in state.important_files

def test_manager_decisions(initialized_unimem):
    """Verify design decision logs and markdown files."""
    manager = MemoryManager(initialized_unimem)
    
    dec_file = manager.add_decision(
        decision_title="SQLite choice",
        context="Need simple file-based storage",
        decision="We chose SQLite"
    )
    
    assert dec_file.exists()
    assert dec_file.parent == get_decisions_dir(initialized_unimem)
    
    dec_content = dec_file.read_text(encoding="utf-8")
    assert "SQLite choice" in dec_content
    assert "We chose SQLite" in dec_content
    
    # Check state updated
    state = manager.load_state()
    assert any("SQLite choice" in d for d in state.recent_decisions)

def test_manager_session_lifecycle(initialized_unimem):
    """Verify session tracking start, update, and end flow."""
    manager = MemoryManager(initialized_unimem)
    
    session = manager.start_session("aider")
    session_id = session.session_id
    assert session_id is not None
    assert session.tool == "aider"
    assert session.end_time is None
    
    # Log an event within the session window
    ev = Event(
        tool="aider",
        event_type="modification",
        prompt="modify code",
        response_summary="code modified successfully",
        files_changed=["app.py"]
    )
    manager.record_event(ev, auto_snapshot=False)
    
    # End session
    ended_session = manager.end_session(session_id)
    assert ended_session is not None
    assert ended_session.session_id == session_id
    assert ended_session.end_time is not None
    assert "modify code" in ended_session.prompts
    assert "code modified successfully" in ended_session.summaries
    assert "app.py" in ended_session.files_changed

def test_manager_reconcile_from_memory_md(initialized_unimem):
    """Verify that state is reconciled from memory.md when memory.md is newer."""
    manager = MemoryManager(initialized_unimem)
    
    # 1. Modify memory.md manually
    memory_file = get_memory_md(initialized_unimem)
    state_file = get_state_file(initialized_unimem)
    
    # Ensure memory_file has a later mtime than state_file
    new_mtime = state_file.stat().st_mtime + 5
    
    md_content = """# Unimem Project Memory: CustomProj
    
This is a custom reconciled description.

---

## 🎯 Current Focus
* **Current Goal**: Reconcile memory files
* **Current Task**: Write unit tests for reconciliation
* **Next Task**: Clean up code

## 🛠️ Features
### In Progress
- Feature A
- Feature B

### Completed
- Feature C

## 🏛️ Architecture & Decisions
### Architecture Notes
- Microservices

### Recent Decisions
- Decided to use gRPC (2026-06-10)

## 🔍 Context details
### Important Files
- handler.go
- main.go

### Blocked By
- Port configuration

### Tools Used
- pytest
"""
    memory_file.write_text(md_content, encoding="utf-8")
    os.utime(memory_file, (new_mtime, new_mtime))
    
    # 2. Load state - this should trigger reconciliation
    state = manager.load_state()
    
    assert state.description == "This is a custom reconciled description."
    assert state.current_goal == "Reconcile memory files"
    assert state.current_task == "Write unit tests for reconciliation"
    assert state.next_task == "Clean up code"
    assert "Feature A" in state.in_progress_features
    assert "Feature B" in state.in_progress_features
    assert "Feature C" in state.completed_features
    assert "Microservices" in state.architecture
    assert "Decided to use gRPC (2026-06-10)" in state.recent_decisions
    assert "handler.go" in state.important_files
    assert "Port configuration" in state.blocked_by
    assert "pytest" in state.tool_history

def test_manager_complete_task_and_promotion(initialized_unimem):
    """Verify that complete_task functions correctly and LocalSummarizer promotion works."""
    manager = MemoryManager(initialized_unimem)
    
    # Setup initial state
    state = manager.load_state()
    state.current_task = "Implement API auth"
    state.next_task = "Add integration tests"
    manager.save_state(state)
    
    # 1. Test complete_task method
    manager.complete_task("Refactor auth module")
    
    updated = manager.load_state()
    assert "Implement API auth" in updated.completed_features
    assert updated.current_task == "Add integration tests"
    assert updated.next_task == "Refactor auth module"
    
    # 2. Test LocalSummarizer heuristic promotion
    updated.current_task = "Task A"
    updated.next_task = "Task B"
    manager.save_state(updated)
    
    # Record an event that completes "Task A"
    from unimem.memory.schemas import Event
    event = Event(
        tool="watcher",
        event_type="git_commit",
        prompt="",
        response_summary="complete Task A",
        files_changed=[]
    )
    manager.record_event(event)
    
    final_state = manager.load_state()
    assert final_state.current_task == "Task B"
    assert final_state.next_task == ""

def test_manager_continuous_state_json_and_file_history(initialized_unimem):
    """Verify that file events continuously update state.json (and file_history) but do not update memory.md."""
    manager = MemoryManager(initialized_unimem)
    
    # Set a current task in the state
    state = manager.load_state()
    state.current_task = "Task-123"
    manager.save_state(state)
    
    # Store initial mtimes of state.json and memory.md
    state_file = get_state_file(initialized_unimem)
    memory_file = get_memory_md(initialized_unimem)
    
    initial_memory_mtime = memory_file.stat().st_mtime
    
    # Record a file created event
    ev1 = Event(
        tool="watcher",
        event_type="file_created",
        prompt="",
        response_summary="Created file 'src/main.py'",
        files_changed=["src/main.py"]
    )
    
    import time
    time.sleep(0.1) # ensure time difference for mtime if checked
    manager.record_event(ev1, auto_snapshot=False)
    
    # Verify memory.md was NOT updated (mtime did not change)
    assert memory_file.stat().st_mtime == initial_memory_mtime
    
    # Verify state.json WAS updated and has file_history entry
    reloaded_state = manager.load_state()
    assert len(reloaded_state.file_history) == 1
    op1 = reloaded_state.file_history[0]
    assert op1.file_path == "src/main.py"
    assert op1.operation_type == "created"
    assert op1.task == "Task-123"
    assert op1.timestamp == ev1.timestamp

    # Now run rebuild_state_from_events (as summary command would) with update_memory=True
    time.sleep(0.1)
    manager.rebuild_state_from_events(update_memory=True)
    
    # Verify memory.md WAS updated now
    assert memory_file.stat().st_mtime > initial_memory_mtime
