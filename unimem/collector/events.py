"""Helper methods for generating and dispatching structured events."""

from typing import List, Optional
from unimem.memory.schemas import Event
from unimem.utils.timestamps import get_timestamp_str

def make_file_change_event(tool: str, files: List[str], summary: str = "") -> Event:
    """Create an Event object for file changes."""
    return Event(
        timestamp=get_timestamp_str(),
        tool=tool,
        event_type="file_change",
        prompt="",
        response_summary=summary or f"Modified files: {', '.join(files)}",
        files_changed=files,
    )

def make_command_event(tool: str, command: str, stdout_summary: str, files_changed: List[str]) -> Event:
    """Create an Event object for shell commands."""
    return Event(
        timestamp=get_timestamp_str(),
        tool=tool,
        event_type="command",
        prompt=f"Run command: {command}",
        response_summary=stdout_summary,
        files_changed=files_changed
    )

def make_interaction_event(tool: str, prompt: str, summary: str, files_changed: List[str], git_commit: Optional[str] = None) -> Event:
    """Create an Event object representing an AI interaction or step."""
    return Event(
        timestamp=get_timestamp_str(),
        tool=tool,
        event_type="interaction",
        prompt=prompt,
        response_summary=summary,
        files_changed=files_changed,
        git_commit=git_commit
    )
