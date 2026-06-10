"""Abstract base class for all AI agent adapters."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List

class BaseAdapter(ABC):
    """Abstract base class that connects specific AI agent environments with Unimem."""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    @abstractmethod
    def load_context(self) -> Dict[str, Any]:
        """Extract and format the project intelligence data for the target agent.
        
        Returns:
            Dict[str, Any]: Agent-formatted context (e.g., prompt snippets or env vars).
        """
        pass

    @abstractmethod
    def save_session(self, session_id: str, summary: str, files_changed: List[str]) -> None:
        """Record and end the current session with a summary and modified file list.
        
        Args:
            session_id: The active session identifier.
            summary: Brief summary of what was accomplished.
            files_changed: List of relative paths of changed files.
        """
        pass

    @abstractmethod
    def launch(self, command: List[str]) -> Any:
        """Launch the AI agent process, wrapping its execution in a Unimem session.
        
        Args:
            command: The command line list to run the agent.
        """
        pass
