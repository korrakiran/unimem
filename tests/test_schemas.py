"""Tests for unimem memory schemas."""

from unimem.memory.schemas import ProjectState, Event, Session
from unimem.utils.timestamps import get_timestamp_str

def test_project_state_defaults():
    """Verify default values of ProjectState."""
    state = ProjectState()
    assert state.project_name == ""
    assert state.description == ""
    assert state.current_goal == ""
    assert state.architecture == []
    assert state.tool_history == []
    assert isinstance(state.last_updated, str)
    assert len(state.last_updated) > 0

def test_project_state_custom():
    """Verify custom fields of ProjectState."""
    state = ProjectState(
        project_name="MyProj",
        description="A desc",
        current_goal="Goal",
        current_task="Task",
        next_task="Next",
        architecture=["Postgres"],
        completed_features=["Auth"],
        in_progress_features=["API"],
        important_files=["main.py"],
        recent_decisions=["Use Postgres"],
        blocked_by=["Docker"],
        tool_history=["gemini"],
    )
    assert state.project_name == "MyProj"
    assert state.description == "A desc"
    assert state.current_goal == "Goal"
    assert state.current_task == "Task"
    assert state.next_task == "Next"
    assert state.architecture == ["Postgres"]
    assert state.completed_features == ["Auth"]
    assert state.in_progress_features == ["API"]
    assert state.important_files == ["main.py"]
    assert state.recent_decisions == ["Use Postgres"]
    assert state.blocked_by == ["Docker"]
    assert state.tool_history == ["gemini"]

def test_event_defaults_and_custom():
    """Verify Event schema serialization and properties."""
    event = Event(
        tool="claude",
        event_type="git_commit",
        prompt="git commit -m 'feat: login'",
        response_summary="Committed login feature changes.",
        files_changed=["auth.py"],
        git_commit="abcdef123456"
    )
    
    assert event.tool == "claude"
    assert event.event_type == "git_commit"
    assert event.prompt == "git commit -m 'feat: login'"
    assert event.response_summary == "Committed login feature changes."
    assert event.files_changed == ["auth.py"]
    assert event.git_commit == "abcdef123456"
    assert isinstance(event.timestamp, str)

def test_session_schema():
    """Verify Session schema validation."""
    session = Session(
        session_id="session-12345",
        tool="gemini",
        prompts=["write login"],
        summaries=["done login"],
        files_changed=["login.py"]
    )
    assert session.session_id == "session-12345"
    assert session.tool == "gemini"
    assert session.prompts == ["write login"]
    assert session.summaries == ["done login"]
    assert session.files_changed == ["login.py"]
    assert session.end_time is None
