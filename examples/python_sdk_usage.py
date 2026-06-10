"""Example script demonstrating programmatic usage of Unimem memory and session manager."""

import os
from pathlib import Path
from unimem.memory.manager import MemoryManager
from unimem.collector.sessions import AgentSession
from unimem.memory.schemas import Event

def main():
    # 1. Resolve project root (uses current working directory here)
    project_root = Path.cwd().resolve()
    print(f"Project root resolved: {project_root}")
    
    # 2. Instantiate Memory Manager
    manager = MemoryManager(project_root)
    
    # 3. Initialize if not already done
    if not manager.is_initialized():
        print("Initializing Unimem memory layer...")
        manager.initialize("Example Project", "Programmatic API usage demo.")
    else:
        print("Unimem already initialized.")
        
    # 4. Load current state
    state = manager.load_state()
    print(f"Loaded Project: {state.project_name}")
    print(f"Current Goal: {state.current_goal}")
    print(f"Current Task: {state.current_task}")
    
    # 5. Track a programmatic AI session using context manager
    print("\nStarting simulated agent coding session...")
    with AgentSession(project_root, tool="custom_script_agent") as session:
        print(f"Session Active ID: {session.get_session_id()}")
        
        # Simulate making some code edits
        test_file = project_root / "temp_edit.py"
        test_file.write_text("print('edited by agent')", encoding="utf-8")
        
        # Record event associated with the session
        event = Event(
            tool="custom_script_agent",
            event_type="file_change",
            prompt="Write edit script",
            response_summary="Created temp_edit.py demonstrating automatic tracking.",
            files_changed=["temp_edit.py"]
        )
        manager.record_event(event)
        
    # Clean up edit file
    if test_file.exists():
        test_file.unlink()
        
    print("Session closed successfully.")
    
    # 6. Read updated state
    updated_state = manager.load_state()
    print(f"\nUpdated Tool History: {updated_state.tool_history}")

if __name__ == "__main__":
    main()
