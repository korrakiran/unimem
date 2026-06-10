"""State builder orchestration to compile and update state.json using event streams."""

from pathlib import Path
from typing import List
from unimem.memory.manager import MemoryManager
from unimem.memory.schemas import ProjectState, Event
from unimem.storage.json_store import JsonStore
from unimem.summarizer.local import LocalSummarizer
from unimem.utils.paths import get_events_dir
from unimem.utils.logger import logger

def rebuild_state(project_root: Path, summarizer_type: str = "local") -> ProjectState:
    """Read all event files chronologically, apply the summarizer, and save the updated state."""
    manager = MemoryManager(project_root)
    if not manager.is_initialized():
        raise FileNotFoundError(f"Unimem is not initialized at {project_root}")
        
    # Instantiate the selected summarizer
    if summarizer_type.lower() == "local":
        summarizer = LocalSummarizer()
    else:
        logger.warning(f"Summarizer '{summarizer_type}' not supported. Using 'local'.")
        summarizer = LocalSummarizer()
        
    # Read and sort all events chronologically
    events_dir = get_events_dir(project_root)
    events: List[Event] = []
    
    if events_dir.exists():
        event_files = list(events_dir.glob("*.json"))
        # Sort by file name (which starts with timestamp)
        event_files.sort(key=lambda p: p.name)
        
        for f in event_files:
            try:
                data = JsonStore.load(f)
                events.append(Event(**data))
            except Exception as e:
                logger.debug(f"Failed to load event file {f.name}: {e}")
                
    # Load current state as the baseline
    current_state = manager.load_state()
    
    # Process events through the summarizer
    updated_state = summarizer.summarize(current_state, events)
    
    # Save the updated state
    manager.save_state(updated_state)
    logger.info("[green]Project state rebuilt successfully from events.[/green]")
    
    return updated_state
