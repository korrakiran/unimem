"""Session tracking helper class and context manager for AI coding sessions."""

from pathlib import Path
from typing import Optional
from unimem.memory.manager import MemoryManager
from unimem.memory.schemas import Session
from unimem.utils.logger import logger

class AgentSession:
    """Context manager for tracking an AI agent's session lifetime."""

    def __init__(self, project_root: Path, tool: str):
        self.manager = MemoryManager(project_root)
        self.tool = tool
        self.session: Optional[Session] = None

    def __enter__(self) -> "AgentSession":
        """Start the session when entering the context."""
        if not self.manager.is_initialized():
            logger.debug("Unimem is not initialized. Session will not be tracked.")
            return self
            
        try:
            self.session = self.manager.start_session(self.tool)
            logger.debug(f"Session started: {self.session.session_id} for tool: {self.tool}")
        except Exception as e:
            logger.error(f"Error starting Unimem session: {e}")
            
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """End the session and save context when exiting."""
        if self.session is None:
            return
            
        try:
            self.manager.end_session(self.session.session_id)
            logger.debug(f"Session ended: {self.session.session_id}")
        except Exception as e:
            logger.error(f"Error ending Unimem session: {e}")
            
    def get_session_id(self) -> Optional[str]:
        """Get current session ID if active."""
        return self.session.session_id if self.session else None
