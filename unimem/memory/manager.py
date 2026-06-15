"""MemoryManager orchestrates all reading/writing of states, events, and sessions."""

import os
import re
from datetime import datetime, timezone
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

    def bootstrap_if_needed(self, project_name: str = "", description: str = "") -> bool:
        """Create the Unimem project structure when it does not yet exist.

        Returns True when initialization happened, False if the project was already initialized.
        """
        if self.is_initialized():
            return False

        if not project_name:
            project_name = self.project_root.name

        self.initialize(project_name, description)
        return True

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

    def reconcile_from_memory_md(self, state: ProjectState, memory_file: Path) -> None:
        """Parse memory.md and update ProjectState in-place with its values."""
        try:
            content = FileStore.read(memory_file)
            
            # Parse description
            desc_match = re.search(r"# Unimem Project Memory:[^\n]*\n+(.*?)\n+---", content, re.DOTALL)
            if desc_match:
                desc = desc_match.group(1).strip()
                if desc and desc != "No description provided.":
                    state.description = desc
                    
            # Parse Current Goal, Current Task, Next Task
            goal_match = re.search(r"\*\s*\*+Current Goal\*+:\s*(.*)", content, re.IGNORECASE)
            if goal_match:
                val = goal_match.group(1).strip()
                state.current_goal = "" if val.lower() == "not set" else val
                
            task_match = re.search(r"\*\s*\*+Current Task\*+:\s*(.*)", content, re.IGNORECASE)
            if task_match:
                val = task_match.group(1).strip()
                state.current_task = "" if val.lower() == "not set" else val
                
            next_match = re.search(r"\*\s*\*+Next Task\*+:\s*(.*)", content, re.IGNORECASE)
            if next_match:
                val = next_match.group(1).strip()
                state.next_task = "" if val.lower() == "not set" else val

            # Helper to extract list items under a header
            def extract_list_items(section_title: str) -> List[str]:
                pattern = rf"(?:^|\n)#+\s*{re.escape(section_title)}[^\n]*\n(.*?)(?=\n#+|$)"
                match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
                if not match:
                    return []
                section_text = match.group(1)
                items = []
                for line in section_text.strip().split("\n"):
                    line = line.strip()
                    if line.startswith("-") or line.startswith("*"):
                        val = line.lstrip("-* ").strip()
                        if val and val.lower() != "none":
                            items.append(val)
                return items

            in_progress = extract_list_items("In Progress")
            if in_progress:
                state.in_progress_features = in_progress
                
            completed = extract_list_items("Completed")
            if completed:
                state.completed_features = completed
                
            architecture = extract_list_items("Architecture Notes")
            if architecture:
                state.architecture = architecture
                
            decisions = extract_list_items("Recent Decisions")
            if decisions:
                state.recent_decisions = decisions
                
            important_files = extract_list_items("Important Files")
            if important_files:
                state.important_files = important_files
                
            blocked_by = extract_list_items("Blocked By")
            if blocked_by:
                state.blocked_by = blocked_by
                
            tool_history = extract_list_items("Tools Used")
            if tool_history:
                state.tool_history = tool_history
                
        except Exception as e:
            logger.debug(f"Failed to reconcile state from memory.md: {e}")

    def load_state(self, reconcile_memory: bool = True) -> ProjectState:
        """Load project state, applying migrations if necessary."""
        state_file = get_state_file(self.project_root)
        if not state_file.exists():
            raise FileNotFoundError(f"Unimem not initialized. Run 'unimem init' first at {self.project_root}")

        # Recover any sessions that were orphaned by a crash before loading state
        self.recover_orphan_sessions()

        data = JsonStore.load(state_file)
        migrated_data = migrate_state(data)
        state = ProjectState(**migrated_data)
        
        # Reconcile from memory.md if requested (lazy load)
        if reconcile_memory:
            memory_file = get_memory_md(self.project_root)
            if memory_file.exists() and memory_file.stat().st_mtime > state_file.stat().st_mtime:
                self.reconcile_from_memory_md(state, memory_file)
            
        return state

    def save_state(self, state: ProjectState, update_memory: bool = True) -> None:
        """Save the ProjectState to state.json and optionally update memory.md."""
        self.archive_old_completed_tasks(state)
        state.last_updated = get_timestamp_str()
        state_file = get_state_file(self.project_root)
        JsonStore.save(state_file, state.model_dump())
        if update_memory:
            self.update_memory_md(state)
            self._update_rules_files()

    def recover_orphan_sessions(self) -> List[str]:
        """Close sessions whose end_time is None and start_time is older than 10 minutes.

        Returns a list of recovered session IDs.
        """
        sessions_dir = get_sessions_dir(self.project_root)
        if not sessions_dir.exists():
            return []

        recovered = []
        now = datetime.now(timezone.utc)
        orphan_threshold_seconds = 10 * 60  # 10 minutes

        for session_file in sessions_dir.glob("session_*.json"):
            try:
                data = JsonStore.load(session_file)
                session = Session(**data)
                if session.end_time is not None:
                    continue  # Already closed

                # Parse start_time — handles both offset-aware and naive ISO strings
                start_str = session.start_time
                try:
                    start_dt = datetime.fromisoformat(start_str)
                    if start_dt.tzinfo is None:
                        start_dt = start_dt.replace(tzinfo=timezone.utc)
                except ValueError:
                    continue  # Unparseable timestamp; skip

                age_seconds = (now - start_dt).total_seconds()
                if age_seconds >= orphan_threshold_seconds:
                    logger.info(
                        f"Recovering orphan session {session.session_id} "
                        f"(tool={session.tool}, age={age_seconds:.0f}s)"
                    )
                    self.end_session(session.session_id)
                    recovered.append(session.session_id)
            except Exception as e:
                logger.debug(f"Failed to inspect session file {session_file.name}: {e}")

        return recovered

    def _update_rules_files(self) -> None:
        """Write agent rule files to project root so tools read them automatically."""
        rules_content = """# Unimem Agent Instructions
# These are MANDATORY instructions. You MUST follow all rules below exactly without exception.

Unimem is active in this project. You are resuming work from a previous session.

CRITICAL STARTUP RULE:
Do NOT scan, list, or search the entire project repository or folder tree on startup. This wastes token context and is inefficient. Instead, follow these steps immediately:

1. Read the structured project state at `.unimem/state.json` first to get the exact roadmap, goals, tasks, and file listings.
2. Read the human-readable project memory at `.unimem/memory.md` next to get the narrative context, recent decisions, and details.
3. Trust `.unimem/state.json` and `.unimem/memory.md` as the absolute sources of truth for the project state. Do NOT attempt to reconstruct them or scan the repository first.

CRITICAL WORKFLOW RULES:

- You MUST update `.unimem/state.json` with your file changes. To optimize token consumption, batch state syncs: group 3-5 file operations in memory/history before performing a single `.unimem/state.json` write instead of a read→edit→sync cycle for every individual file operation.

- Lazy-load `.unimem/memory.md`: Only read or parse `.unimem/memory.md` when the task type requires it (e.g. handoffs, summaries, or complex task planning), rather than injecting or loading it on every simple file operation.

- When you finish or pause work, always update `.unimem/state.json` first to document completed features, goals, or tasks, then run `unimem summary` to synchronize changes into `memory.md` and keep the supporting `.unimem/` logs aligned.

- When you complete the current task, run: unimem task done --next "describe the next task"

- If you are interrupted or about to stop, always run: unimem task done --next "describe next task" before exiting so context is preserved for the next agent.

UNIMEM UPDATE GUIDELINES:
Run `unimem summary` at checkpoint moments to prevent mid-process context loss:

ALWAYS run `unimem summary` at:
- Major milestones (feature/module completion, architectural decisions)
- Every 45 minutes of continuous work (safety checkpoint)
- Before stopping or pausing work
- At the end of the work session
- After completing a significant refactor or bug fix

DO NOT run `unimem summary` for:
- CSS or styling tweaks (unless part of a major UI overhaul)
- Code formatting or comments
- Typo fixes
- Simple variable renames
- Dependency version bumps
- Whitespace changes

For minor changes: Make the change, build/test, update state.json, but skip `unimem summary` unless approaching a checkpoint time or milestone.

CRASH RECOVERY:
If an agent crashes mid-work:
1. The next agent reads `.unimem/state.json` and its `file_history` to see exactly what was created/modified
2. The next agent reads `.unimem/memory.md` for the last completed milestone
3. The next agent reconstructs only the in-progress work since the last checkpoint, not the entire project

CRITICAL GIT RULE:
- Do NOT stage, commit, or push the `.unimem` directory or any files inside it (such as `.unimem/state.json` or `.unimem/memory.md`). They are local-only project memory.
- Do NOT stage, commit, or push any temporary files, logs, or screenshots (especially those in `/var/folders/`, `/tmp/`, or similar temp folders).
- Do NOT stage, commit, or push any of the auto-generated agent rules or instruction files (such as `AGENTS.md`, `.cursorrules`, `.aiderules`, `.aider.instructions.md`, etc.). These are local configurations and must remain untracked.
"""
        try:
            # List of all major AI agent and editor rule files
            rule_files = [
                "AGENTS.md",
                "CLAUDE.md",
                ".cursorrules",
                ".clauderules",
                ".windsurfrules",
                ".clinerules",
                ".antigravityrules",
                ".geminirules",
                ".aiderules",
                ".aider.instructions.md",
                ".supermavenrules",
                ".codeiumrules",
                ".continuerules",
                ".doublerules",
                ".tabninerules",
                ".phindrules"
            ]
            for rule_file in rule_files:
                FileStore.write(self.project_root / rule_file, rules_content)
            
            # Write to .github/copilot-instructions.md for Copilot
            copilot_dir = self.project_root / ".github"
            try:
                copilot_dir.mkdir(parents=True, exist_ok=True)
                FileStore.write(copilot_dir / "copilot-instructions.md", rules_content)
            except Exception as e:
                logger.debug(f"Failed to write copilot instructions: {e}")
        except Exception as e:
            logger.debug(f"Failed to write agent rule files: {e}")

    def rebuild_state_from_events(self, summarizer_type: str = "local", update_memory: bool = True) -> ProjectState:
        """Rebuild state from recorded events directly within the manager to avoid circular imports."""
        from unimem.summarizer.local import LocalSummarizer
        
        # Instantiate summarizer
        if summarizer_type.lower() == "local":
            summarizer = LocalSummarizer()
        else:
            summarizer = LocalSummarizer()
            
        # Read and sort all events chronologically
        events_dir = get_events_dir(self.project_root)
        events = []
        
        if events_dir.exists():
            event_files = list(events_dir.glob("*.json"))
            event_files.sort(key=lambda p: p.name)
            
            for f in event_files:
                try:
                    data = JsonStore.load(f)
                    events.append(Event(**data))
                except Exception as e:
                    logger.debug(f"Failed to load event file {f.name}: {e}")
                    
        # Load current state as the baseline (skip memory reconciliation here)
        current_state = self.load_state(reconcile_memory=False)
        
        # Process events through the summarizer
        updated_state = summarizer.summarize(current_state, events)
        
        # Save the updated state
        self.save_state(updated_state, update_memory=update_memory)
        
        return updated_state

    def record_event(self, event: Event, auto_snapshot: bool = True) -> Path:
        """Record an event to the events folder and continuously update state.json and memory.md."""
        events_dir = get_events_dir(self.project_root)
        events_dir.mkdir(parents=True, exist_ok=True)
        
        # Populate task from current state if not specified (skip memory reconciliation here)
        if not getattr(event, "task", ""):
            try:
                state = self.load_state(reconcile_memory=False)
                event.task = state.current_task
            except Exception:
                pass

        timestamp = event.timestamp.replace(":", "-")
        event_file = events_dir / f"event_{timestamp}_{uuid.uuid4().hex[:8]}.json"
        
        # Save event
        JsonStore.save(event_file, event.model_dump())
        logger.debug(f"Event recorded: {event_file.name}")
        
        # Rebuild state from all events to keep it continuously updated and sync memory.md in real-time
        try:
            state = self.rebuild_state_from_events(update_memory=False)
            
            if auto_snapshot:
                create_snapshot(self.project_root, state)
        except FileNotFoundError:
            pass # Not initialized yet
        except Exception as e:
            logger.debug(f"Failed to auto-rebuild state on event record: {e}")
            
        return event_file

    def record_events_batch(self, events: List[Event], auto_snapshot: bool = True) -> List[Path]:
        """Record a batch of events to the events folder and perform a single update to state.json."""
        events_dir = get_events_dir(self.project_root)
        events_dir.mkdir(parents=True, exist_ok=True)
        
        # Load the state once at the start to populate tasks for all events if needed
        current_task = ""
        try:
            state = self.load_state(reconcile_memory=False)
            current_task = state.current_task
        except Exception:
            pass
            
        event_files = []
        for event in events:
            if not getattr(event, "task", ""):
                event.task = current_task
                
            timestamp = event.timestamp.replace(":", "-")
            event_file = events_dir / f"event_{timestamp}_{uuid.uuid4().hex[:8]}.json"
            JsonStore.save(event_file, event.model_dump())
            event_files.append(event_file)
            
        # Rebuild state only ONCE after saving all event files in the batch
        try:
            state = self.rebuild_state_from_events(update_memory=False)
            if auto_snapshot:
                create_snapshot(self.project_root, state)
        except FileNotFoundError:
            pass
        except Exception as e:
            logger.debug(f"Failed to auto-rebuild state on batch event record: {e}")
            
        return event_files

    def archive_old_completed_tasks(self, state: ProjectState) -> None:
        """Prune done tasks/features older than 7 days from state.json and save them to archive.json."""
        archive_file = self.project_root / ".unimem" / "archive.json"
        
        # Load existing archive if it exists
        archive_data = {}
        if archive_file.exists():
            try:
                archive_data = JsonStore.load(archive_file)
            except Exception:
                pass
        if "completed_tasks" not in archive_data:
            archive_data["completed_tasks"] = []
            
        now = datetime.now(timezone.utc)
        retained_features = []
        archived_any = False
        
        # We need to find completion timestamps. Let's build a map from events and file history
        task_timestamps = {}
        
        # Scan file history
        for op in state.file_history:
            if op.task:
                try:
                    dt = datetime.fromisoformat(op.timestamp.replace("Z", "+00:00"))
                    task_name = op.task.strip()
                    if task_name not in task_timestamps or dt > task_timestamps[task_name]:
                        task_timestamps[task_name] = dt
                except Exception:
                    pass
                    
        # Scan events folder
        events_dir = get_events_dir(self.project_root)
        if events_dir.exists():
            for f in events_dir.glob("*.json"):
                try:
                    data = JsonStore.load(f)
                    ev_task = data.get("task", "")
                    ev_ts = data.get("timestamp", "")
                    if ev_task and ev_ts:
                        dt = datetime.fromisoformat(ev_ts.replace("Z", "+00:00"))
                        task_name = ev_task.strip()
                        if task_name not in task_timestamps or dt > task_timestamps[task_name]:
                            task_timestamps[task_name] = dt
                except Exception:
                    pass

        for feature in state.completed_features:
            feature_name = feature.strip()
            # Try to find the completion timestamp
            completion_dt = None
            # Direct match
            if feature_name in task_timestamps:
                completion_dt = task_timestamps[feature_name]
            else:
                # Case-insensitive / partial match
                for t_name, dt in task_timestamps.items():
                    if t_name.lower() == feature_name.lower() or feature_name.lower() in t_name.lower():
                        completion_dt = dt
                        break
            
            if completion_dt:
                age_days = (now - completion_dt).days
                if age_days > 7:
                    # Archive it
                    archive_data["completed_tasks"].append({
                        "task": feature,
                        "completed_at": completion_dt.isoformat()
                    })
                    archived_any = True
                    continue
            
            retained_features.append(feature)
            
        if archived_any:
            state.completed_features = retained_features
            # Prune file_history of archived tasks
            archived_task_names = {t["task"].strip().lower() for t in archive_data["completed_tasks"]}
            state.file_history = [
                op for op in state.file_history
                if not (op.task and op.task.strip().lower() in archived_task_names)
            ]
            JsonStore.save(archive_file, archive_data)
            logger.info(f"Archived completed tasks older than 7 days to {archive_file.name}")

    def complete_task(self, next_task: str = "") -> ProjectState:
        """Complete the current task and promote the next one."""
        state = self.load_state(reconcile_memory=True)
        if state.current_task:
            state.completed_features.append(state.current_task)
        state.current_task = state.next_task
        state.next_task = next_task
        self.save_state(state)
        return state

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
        state = self.load_state(reconcile_memory=True)
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
