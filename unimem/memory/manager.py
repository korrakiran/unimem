"""MemoryManager orchestrates all reading/writing of states, events, and sessions."""

import os
from pathlib import Path
from typing import List, Optional
import uuid

from unimem.config.constants import (
    MEM_DIR_NAME,
    EVENTS_DIR_NAME,
    SESSIONS_DIR_NAME,
    SNAPSHOTS_DIR_NAME,
    DECISIONS_DIR_NAME,
)
from unimem.memory.schemas import ProjectState, Event, Session
from unimem.memory.migrations import migrate_state
from unimem.memory.snapshots import create_snapshot
from unimem.storage.json_store import JsonStore
from unimem.storage.file_store import FileStore
from unimem.utils.logger import logger
from unimem.utils.paths import (
    get_unimem_dir,
    get_events_dir,
    get_sessions_dir,
    get_snapshots_dir,
    get_decisions_dir,
    get_state_file,
    get_memory_md,
)
from unimem.utils.timestamps import get_timestamp_str

class MemoryManager:
    """Manages reading, writing, updating, and exporting Unimem project data."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.unimem_dir = get_unimem_dir(project_root)

    def is_initialized(self) -> bool:
        """Check if .unimem is initialized in the project root."""
        return self.unimem_dir.is_dir() and get_state_file(self.project_root).exists()

    def initialize(self, project_name: str, description: str = "") -> None:
        """Initialize the .unimem/ structure with default files."""
        logger.info(f"Initializing Unimem at project root: {self.project_root}")
        
        # Create directories
        get_unimem_dir(self.project_root).mkdir(parents=True, exist_ok=True)
        get_events_dir(self.project_root).mkdir(parents=True, exist_ok=True)
        get_sessions_dir(self.project_root).mkdir(parents=True, exist_ok=True)
        get_snapshots_dir(self.project_root).mkdir(parents=True, exist_ok=True)
        get_decisions_dir(self.project_root).mkdir(parents=True, exist_ok=True)
        
        # Create default ProjectState
        state = ProjectState(
            project_name=project_name,
            description=description,
            current_goal="Initialize the repository and basic components",
            current_task="Setup Unimem configuration and first files",
            next_task="Verify CLI command executions",
        )
        self.save_state(state)
        self.update_memory_md(state)
        
        # Record initialization event
        init_event = Event(
            tool="unimem_cli",
            event_type="init",
            prompt="unimem init",
            response_summary=f"Initialized Unimem project memory for {project_name}."
        )
        self.record_event(init_event, auto_snapshot=False)
        logger.info("[green]Successfully initialized Unimem![/green]")

    def load_state(self) -> ProjectState:
        """Load project state, applying migrations if necessary."""
        state_file = get_state_file(self.project_root)
        if not state_file.exists():
            raise FileNotFoundError(f"Unimem not initialized. Run 'unimem init' first at {self.project_root}")
            
        data = JsonStore.load(state_file)
        migrated_data = migrate_state(data)
        state = ProjectState(**migrated_data)
        return state

    def save_state(self, state: ProjectState) -> None:
        """Save the ProjectState to state.json and update memory.md."""
        state.last_updated = get_timestamp_str()
        state_file = get_state_file(self.project_root)
        JsonStore.save(state_file, state.model_dump())
        self.update_memory_md(state)
        self._update_rules_files()

    def _update_rules_files(self) -> None:
        """Write agent rule files (.cursorrules, .clauderules) to project root so tools read them automatically."""
        rules_content = """# Unimem Agent Instructions

Unimem is active in this project. You are resuming work from a previous session.

Before you begin coding:
1. Read the project memory file at `.unimem/memory.md` to get your full context:
   - Current Goal & Task focus
   - Completed and In-Progress features
   - Architectural decisions
   - Important files to locate
2. Trust `.unimem/memory.md` as the source of truth for the project state.

When you finish or pause work:
- Update the Unimem state (e.g. by running `unimem summary` or updating `.unimem/state.json`) so the next agent can seamlessly take over.
"""
        try:
            FileStore.write(self.project_root / ".cursorrules", rules_content)
            FileStore.write(self.project_root / ".clauderules", rules_content)
        except Exception as e:
            logger.debug(f"Failed to write agent rule files: {e}")

    def record_event(self, event: Event, auto_snapshot: bool = True) -> Path:
        """Record an event to the events folder."""
        events_dir = get_events_dir(self.project_root)
        events_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = event.timestamp.replace(":", "-")
        event_file = events_dir / f"event_{timestamp}_{uuid.uuid4().hex[:8]}.json"
        
        # Save event
        JsonStore.save(event_file, event.model_dump())
        logger.debug(f"Event recorded: {event_file.name}")
        
        # Update state tool history if not already present
        try:
            state = self.load_state()
            if event.tool and event.tool not in state.tool_history:
                state.tool_history.append(event.tool)
                
            # If files changed, update important files list if they look important
            for f in event.files_changed:
                if f not in state.important_files and not f.startswith(".unimem") and not f.startswith(".git"):
                    state.important_files.append(f)
                    
            self.save_state(state)
            
            if auto_snapshot:
                create_snapshot(self.project_root, state)
        except FileNotFoundError:
            pass # Not initialized yet
            
        return event_file

    def add_decision(self, decision_title: str, context: str, decision: str) -> Path:
        """Add a design or architectural decision document."""
        decisions_dir = get_decisions_dir(self.project_root)
        decisions_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = get_timestamp_str()
        safe_ts = timestamp.replace(":", "-")
        filename = f"decision_{safe_ts}.md"
        decision_file = decisions_dir / filename
        
        content = f"""# Decision: {decision_title}

**Date**: {timestamp}

## Context
{context}

## Decision
{decision}

## Status
Approved
"""
        FileStore.write(decision_file, content)
        
        # Update project state
        state = self.load_state()
        state.recent_decisions.append(f"{decision_title} ({timestamp})")
        self.save_state(state)
        
        # Record event
        self.record_event(Event(
            tool="unimem_cli",
            event_type="decision",
            prompt=f"unimem decision: {decision_title}",
            response_summary=f"Recorded decision: {decision_title}"
        ))
        
        return decision_file

    def start_session(self, tool: str) -> Session:
        """Start a new session for an AI tool."""
        session_id = uuid.uuid4().hex
        session = Session(session_id=session_id, tool=tool)
        
        session_path = get_sessions_dir(self.project_root) / f"session_{session_id}.json"
        JsonStore.save(session_path, session.model_dump())
        
        # Record start event
        start_event = Event(
            tool=tool,
            event_type="session_start",
            prompt="session start",
            response_summary=f"Started tracking session for agent: {tool}."
        )
        self.record_event(start_event, auto_snapshot=False)
        
        return session

    def end_session(self, session_id: str) -> Optional[Session]:
        """End a tracking session, saving final session summary and files changed."""
        session_path = get_sessions_dir(self.project_root) / f"session_{session_id}.json"
        if not session_path.exists():
            logger.warning(f"Session file {session_path} not found.")
            return None
            
        data = JsonStore.load(session_path)
        session = Session(**data)
        session.end_time = get_timestamp_str()
        
        # Query all events that occurred during this session to aggregate stats
        events_dir = get_events_dir(self.project_root)
        session_events = []
        if events_dir.exists():
            for ev_file in events_dir.glob("*.json"):
                try:
                    ev_data = JsonStore.load(ev_file)
                    ev = Event(**ev_data)
                    if ev.timestamp >= session.start_time and ev.timestamp <= session.end_time and ev.tool == session.tool:
                        session_events.append(ev)
                except Exception:
                    pass
                    
        # Aggregate prompts, summaries, and files changed from events
        session.events_count = len(session_events)
        changed_files_set = set(session.files_changed)
        for ev in session_events:
            if ev.prompt and ev.prompt not in session.prompts:
                session.prompts.append(ev.prompt)
            if ev.response_summary and ev.response_summary not in session.summaries:
                session.summaries.append(ev.response_summary)
            for f in ev.files_changed:
                changed_files_set.add(f)
        session.files_changed = list(changed_files_set)
        
        # Save updated session
        JsonStore.save(session_path, session.model_dump())
        
        # Record end event
        end_event = Event(
            tool=session.tool,
            event_type="session_end",
            prompt="session end",
            response_summary=f"Ended session {session_id}. Tracked {session.events_count} events."
        )
        self.record_event(end_event, auto_snapshot=True)
        
        return session

    def update_memory_md(self, state: ProjectState) -> None:
        """Generate a clean, beautiful Markdown memory document representing current project status."""
        memory_file = get_memory_md(self.project_root)
        
        arch_list = "\n".join([f"- {item}" for item in state.architecture]) if state.architecture else "- None"
        comp_list = "\n".join([f"- {item}" for item in state.completed_features]) if state.completed_features else "- None"
        ip_list = "\n".join([f"- {item}" for item in state.in_progress_features]) if state.in_progress_features else "- None"
        files_list = "\n".join([f"- {item}" for item in state.important_files]) if state.important_files else "- None"
        dec_list = "\n".join([f"- {item}" for item in state.recent_decisions]) if state.recent_decisions else "- None"
        blocked_list = "\n".join([f"- {item}" for item in state.blocked_by]) if state.blocked_by else "- None"
        tools_list = "\n".join([f"- {item}" for item in state.tool_history]) if state.tool_history else "- None"
        
        md_content = f"""# Unimem Project Memory: {state.project_name}

{state.description or "No description provided."}

---

## 🎯 Current Focus
* **Current Goal**: {state.current_goal or "Not set"}
* **Current Task**: {state.current_task or "Not set"}
* **Next Task**: {state.next_task or "Not set"}

## 🛠️ Features
### In Progress
{ip_list}

### Completed
{comp_list}

## 🏛️ Architecture & Decisions
### Architecture Notes
{arch_list}

### Recent Decisions
{dec_list}

## 🔍 Context details
### Important Files
{files_list}

### Blocked By
{blocked_list}

### Tools Used
{tools_list}

---
*Last updated: {state.last_updated}*
"""
        FileStore.write(memory_file, md_content)
