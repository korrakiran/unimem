"""Snapshot manager for taking and restoring historical points of ProjectState."""

import os
from pathlib import Path
from typing import List
from unimem.memory.schemas import ProjectState
from unimem.storage.json_store import JsonStore
from unimem.utils.paths import get_snapshots_dir
from unimem.utils.timestamps import get_timestamp_str

def create_snapshot(project_root: Path, state: ProjectState) -> Path:
    """Take a snapshot of the current project state and save it in the snapshots folder."""
    snapshots_dir = get_snapshots_dir(project_root)
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = get_timestamp_str().replace(":", "-") # Safe path name
    snapshot_filename = f"state_snapshot_{timestamp}.json"
    snapshot_path = snapshots_dir / snapshot_filename
    
    # Save the project state
    JsonStore.save(snapshot_path, state.model_dump())
    return snapshot_path

def list_snapshots(project_root: Path) -> List[Path]:
    """List all available snapshots in chronological order."""
    snapshots_dir = get_snapshots_dir(project_root)
    if not snapshots_dir.exists():
        return []
        
    # Find all json snapshots and sort them
    snapshots = list(snapshots_dir.glob("state_snapshot_*.json"))
    snapshots.sort(key=lambda p: p.name)
    return snapshots

def restore_snapshot(project_root: Path, snapshot_path: Path) -> ProjectState:
    """Restore a state.json from a historical snapshot file."""
    if not snapshot_path.exists():
        raise FileNotFoundError(f"Snapshot not found: {snapshot_path}")
        
    data = JsonStore.load(snapshot_path)
    # Parse back into a ProjectState object to validate it
    state = ProjectState(**data)
    
    # Save it to the main state.json file
    from unimem.utils.paths import get_state_file
    state_file = get_state_file(project_root)
    JsonStore.save(state_file, state.model_dump())
    
    return state
