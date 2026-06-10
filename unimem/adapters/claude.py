"""Claude Code agent adapter, subclassing GenericAdapter for session execution wrapper."""

from typing import List
from unimem.adapters.generic import GenericAdapter
from unimem.adapters.registry import AdapterRegistry
from unimem.memory.manager import MemoryManager
from unimem.utils.logger import logger

@AdapterRegistry.register("claude")
class ClaudeAdapter(GenericAdapter):
    """Adapter for wrapping Claude Code sessions."""

    def launch(self, command: List[str] = None) -> None:
        """Launch Claude Code, defaulting to standard CLI execution."""
        if not command:
            # Default to claude command or npx execution
            command = ["claude"]
            
        logger.info("[cyan]Initializing Claude Code Unimem Adapter...[/cyan]")
        
        # Override the tool name in manager to 'claude' by starting the session manually
        manager = MemoryManager(self.project_root)
        session_id = None
        if manager.is_initialized():
            session = manager.start_session("claude")
            session_id = session.session_id
            
        # We temporarily set the env variables to run via superclass launch
        # but manage the session registration under the 'claude' tool name.
        try:
            # We call the super class but we handle session manually to ensure 'claude' is recorded
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
            logger.info(f"Running Claude Code: {' '.join(command)}")
            result = subprocess.run(command, env=env, shell=False)
            
            final_changed = []
            if GitCollector.is_git_repo(self.project_root):
                git_stats = GitCollector.get_changed_files(self.project_root)
                all_changed = git_stats["unstaged"] + git_stats["staged"] + git_stats["untracked"]
                final_changed = sorted(list(set(all_changed) - set(initial_changed)))
                
            if session_id and manager.is_initialized():
                from unimem.memory.schemas import Event
                event = Event(
                    tool="claude",
                    event_type="agent_run",
                    prompt=f"Claude session finished with exit code {result.returncode}",
                    response_summary=f"Claude completed task with exit code {result.returncode}.",
                    files_changed=final_changed
                )
                manager.record_event(event)
                manager.end_session(session_id)
        except FileNotFoundError:
            logger.error("[red]Claude command not found. Please ensure 'claude' CLI is installed or specify path.[/red]")
            if session_id and manager.is_initialized():
                manager.end_session(session_id)
        except Exception as e:
            logger.error(f"Error executing Claude: {e}")
            if session_id and manager.is_initialized():
                manager.end_session(session_id)
