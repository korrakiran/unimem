"""Generic adapter that runs arbitrary commands wrapped in Unimem session state."""

import os
import subprocess
import sys
from typing import Dict, Any, List
from pathlib import Path

from unimem.adapters.base import BaseAdapter
from unimem.adapters.registry import AdapterRegistry
from unimem.memory.manager import MemoryManager
from unimem.memory.schemas import Event
from unimem.collector.git_collector import GitCollector
from unimem.collector.file_collector import FileCollector
from unimem.utils.logger import logger

@AdapterRegistry.register("generic")
class GenericAdapter(BaseAdapter):
    """Generic adapter for running tools inside Unimem context environment."""

    def load_context(self) -> Dict[str, Any]:
        """Load project state and return environment configurations."""
        manager = MemoryManager(self.project_root)
        if not manager.is_initialized():
            return {}
            
        try:
            state = manager.load_state()
            memory_md_path = self.project_root / ".unimem" / "memory.md"
            context_md = ""
            if memory_md_path.exists():
                with open(memory_md_path, "r", encoding="utf-8") as f:
                    context_md = f.read()
                    
            return {
                "project_name": state.project_name,
                "current_goal": state.current_goal,
                "current_task": state.current_task,
                "context_md": context_md,
                "state_json": state.model_dump_json()
            }
        except Exception as e:
            logger.error(f"Failed to load generic context: {e}")
            return {}

    def save_session(self, session_id: str, summary: str, files_changed: List[str]) -> None:
        """Saves session info by delegating to MemoryManager."""
        manager = MemoryManager(self.project_root)
        if not manager.is_initialized():
            return
            
        # Recording the event also triggers state update and snapshot
        event = Event(
            tool="generic",
            event_type="agent_run",
            prompt=f"Session execution summary for session {session_id}",
            response_summary=summary,
            files_changed=files_changed
        )
        manager.record_event(event)

    def launch(self, command: List[str]) -> subprocess.CompletedProcess:
        """Launch a tool subprocess with Unimem variables injected into env."""
        if not command:
            raise ValueError("No command provided to launch.")
            
        manager = MemoryManager(self.project_root)
        session_id = None
        
        # Start Unimem session tracking
        if manager.is_initialized():
            session = manager.start_session("generic")
            session_id = session.session_id
            
        # Compile environment context variables
        context = self.load_context()
        env = os.environ.copy()
        if context:
            env["UNIMEM_ACTIVE"] = "true"
            env["UNIMEM_PROJECT"] = context.get("project_name", "")
            env["UNIMEM_CONTEXT_MD"] = context.get("context_md", "")
            env["UNIMEM_STATE_JSON"] = context.get("state_json", "")
            env["UNIMEM_SESSION_ID"] = session_id or ""
            
        # Track initial modified file list for comparison later
        initial_changed = []
        if GitCollector.is_git_repo(self.project_root):
            git_stats = GitCollector.get_changed_files(self.project_root)
            initial_changed = git_stats["unstaged"] + git_stats["staged"] + git_stats["untracked"]
            
        logger.info(f"Launching subprocess: {' '.join(command)}")
        try:
            # Execute command
            result = subprocess.run(
                command,
                env=env,
                check=False,
                shell=False
            )
            
            # Identify changed files
            final_changed = []
            if GitCollector.is_git_repo(self.project_root):
                git_stats = GitCollector.get_changed_files(self.project_root)
                all_changed = git_stats["unstaged"] + git_stats["staged"] + git_stats["untracked"]
                final_changed = sorted(list(set(all_changed) - set(initial_changed)))
            else:
                final_changed = FileCollector.get_recently_modified_files(self.project_root, limit=5)
                
            # Finalize session
            if session_id and manager.is_initialized():
                summary = f"Subprocess command finished with exit code {result.returncode}."
                self.save_session(session_id, summary, final_changed)
                manager.end_session(session_id)
                
            return result
        except Exception as e:
            logger.error(f"Error launching subprocess: {e}")
            if session_id and manager.is_initialized():
                manager.end_session(session_id)
            raise
