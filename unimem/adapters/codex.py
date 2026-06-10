"""Codex CLI agent adapter, subclassing GenericAdapter for session execution wrapper."""

from typing import List
from unimem.adapters.generic import GenericAdapter
from unimem.adapters.registry import AdapterRegistry
from unimem.memory.manager import MemoryManager
from unimem.utils.logger import logger

@AdapterRegistry.register("codex")
class CodexAdapter(GenericAdapter):
    """Adapter for wrapping Codex CLI sessions."""

    def launch(self, command: List[str] = None) -> None:
        """Launch Codex CLI, defaulting to standard CLI execution."""
        if not command:
            command = ["codex"]
            
        logger.info("[cyan]Initializing Codex CLI Unimem Adapter...[/cyan]")
        
        manager = MemoryManager(self.project_root)
        session_id = None
        if manager.is_initialized():
            session = manager.start_session("codex")
            session_id = session.session_id
            
        try:
            import os
            context = self.load_context()
            env = os.environ.copy()
            if context:
                env["UNIMEM_ACTIVE"] = "true"
                env["UNIMEM_PROJECT"] = context.get("project_name", "")
                env["UNIMEM_CONTEXT_MD"] = context.get("context_md", "")
                env["UNIMEM_STATE_JSON"] = context.get("state_json", "")
                env["UNIMEM_SESSION_ID"] = session_id or ""
                
            from unimem.collector.git_collector import GitCollector
            initial_changed = []
            if GitCollector.is_git_repo(self.project_root):
                git_stats = GitCollector.get_changed_files(self.project_root)
                initial_changed = git_stats["unstaged"] + git_stats["staged"] + git_stats["untracked"]
                
            import subprocess
            logger.info(f"Running Codex CLI: {' '.join(command)}")
            result = subprocess.run(command, env=env, shell=False)
            
            final_changed = []
            if GitCollector.is_git_repo(self.project_root):
                git_stats = GitCollector.get_changed_files(self.project_root)
                all_changed = git_stats["unstaged"] + git_stats["staged"] + git_stats["untracked"]
                final_changed = sorted(list(set(all_changed) - set(initial_changed)))
                
            if session_id and manager.is_initialized():
                from unimem.memory.schemas import Event
                event = Event(
                    tool="codex",
                    event_type="agent_run",
                    prompt=f"Codex session finished with exit code {result.returncode}",
                    response_summary=f"Codex completed task with exit code {result.returncode}.",
                    files_changed=final_changed
                )
                manager.record_event(event)
                manager.end_session(session_id)
        except FileNotFoundError:
            logger.error("[red]Codex command not found. Please ensure Codex CLI is installed or specify path.[/red]")
            if session_id and manager.is_initialized():
                manager.end_session(session_id)
        except Exception as e:
            logger.error(f"Error executing Codex: {e}")
            if session_id and manager.is_initialized():
                manager.end_session(session_id)
