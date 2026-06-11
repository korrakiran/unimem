"""Pydantic schemas representing ProjectState, Event, and Session structures."""

from typing import List, Optional
from pydantic import BaseModel, Field
from unimem.utils.timestamps import get_timestamp_str

class FileOperation(BaseModel):
    """Pydantic model representing a single tracked file operation."""
    file_path: str = Field(..., description="Path of the file relative to project root.")
    operation_type: str = Field(..., description="Operation type: created, modified, or deleted.")
    timestamp: str = Field(..., description="ISO 8601 timestamp of the operation.")
    task: str = Field(default="", description="The task this operation belongs to.")

class ProjectState(BaseModel):
    """Pydantic model representing the universal project intelligence state."""
    project_name: str = Field(default="", description="Name of the project.")
    description: str = Field(default="", description="High-level project description.")
    current_goal: str = Field(default="", description="The overarching current milestone or objective.")
    current_task: str = Field(default="", description="The task currently being worked on.")
    next_task: str = Field(default="", description="The next planned task to be picked up.")
    architecture: List[str] = Field(default_factory=list, description="Architecture notes or design details.")
    completed_features: List[str] = Field(default_factory=list, description="List of features that have been completed.")
    in_progress_features: List[str] = Field(default_factory=list, description="List of features currently in progress.")
    important_files: List[str] = Field(default_factory=list, description="List of critical files in the codebase.")
    recent_decisions: List[str] = Field(default_factory=list, description="Decisions made recently (e.g. choice of DB).")
    blocked_by: List[str] = Field(default_factory=list, description="Active blockers or dependencies.")
    tool_history: List[str] = Field(default_factory=list, description="History of tools/agents invoked in the project.")
    file_history: List[FileOperation] = Field(default_factory=list, description="Tracking of individual file operations.")
    last_updated: str = Field(default_factory=get_timestamp_str, description="ISO 8601 timestamp of last update.")

class Event(BaseModel):
    """Pydantic model representing a single activity event in the project lifecycle."""
    timestamp: str = Field(default_factory=get_timestamp_str, description="ISO 8601 timestamp of the event.")
    tool: str = Field(default="generic", description="The AI tool or client that triggered the event.")
    event_type: str = Field(default="generic", description="The category of event (e.g., file_change, command, session_start).")
    prompt: str = Field(default="", description="The user's prompt or instruction associated with the event.")
    response_summary: str = Field(default="", description="A summary of the AI response or command outcome.")
    files_changed: List[str] = Field(default_factory=list, description="Files modified during this event.")
    git_commit: Optional[str] = Field(default=None, description="The Git commit SHA if committed during this event.")
    task: str = Field(default="", description="The current task when the event was recorded.")

class Session(BaseModel):
    """Pydantic model representing an active session of an AI tool working on the project."""
    session_id: str = Field(..., description="Unique identifier for the session.")
    start_time: str = Field(default_factory=get_timestamp_str, description="ISO 8601 timestamp when session started.")
    end_time: Optional[str] = Field(default=None, description="ISO 8601 timestamp when session ended.")
    tool: str = Field(default="generic", description="AI tool used during this session.")
    prompts: List[str] = Field(default_factory=list, description="List of prompts run during the session.")
    summaries: List[str] = Field(default_factory=list, description="List of response summaries for prompts run.")
    files_changed: List[str] = Field(default_factory=list, description="Accumulated list of modified files.")
    events_count: int = Field(default=0, description="Total number of events tracked in this session.")
