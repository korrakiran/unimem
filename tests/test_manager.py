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
