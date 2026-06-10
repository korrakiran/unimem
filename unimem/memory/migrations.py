"""Migration module to safely upgrade older schema versions of state.json."""

from typing import Any, Dict
from unimem.utils.logger import logger

def migrate_state(data: Dict[str, Any]) -> Dict[str, Any]:
    """Inspects the state dictionary and populates any missing fields with defaults.
    
    This acts as a simple forward-migration system as fields are added to ProjectState.
    """
    logger.debug("Running migrations on state data...")
    
    # List of default keys and their default factory/value
    defaults = {
        "project_name": "",
        "description": "",
        "current_goal": "",
        "current_task": "",
        "next_task": "",
        "architecture": [],
        "completed_features": [],
        "in_progress_features": [],
        "important_files": [],
        "recent_decisions": [],
        "blocked_by": [],
        "tool_history": [],
    }
    
    migrated = False
    for key, default_val in defaults.items():
        if key not in data:
            logger.info(f"Migration: Adding missing key '{key}' to state.")
            # We copy list default values to avoid shared references
            data[key] = list(default_val) if isinstance(default_val, list) else default_val
            migrated = True
            
    if migrated:
        logger.info("Project state successfully migrated to the latest schema version.")
        
    return data
