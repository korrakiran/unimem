"""Command to create, list, and restore project state snapshots."""

from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table

from unimem.memory.manager import MemoryManager
from unimem.memory import snapshots
from unimem.utils.paths import find_project_root

app = typer.Typer(help="Manage point-in-time project state snapshots.")
console = Console()

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """If no subcommand is provided, default to creating a snapshot."""
    if ctx.invoked_subcommand is None:
        create_cmd()

@app.command("create")
def create_cmd():
    """Create a new point-in-time snapshot of the current state."""
    project_root = find_project_root()
    manager = MemoryManager(project_root)
    
    if not manager.is_initialized():
        console.print("[red]Unimem is not initialized. Run 'unimem init' first.[/red]")
        raise typer.Exit(code=1)
        
    try:
        state = manager.load_state()
        snapshot_path = snapshots.create_snapshot(project_root, state)
        console.print(f"[green]Snapshot created successfully: [bold]{snapshot_path.name}[/bold][/green]")
    except Exception as e:
        console.print(f"[red]Error creating snapshot: {e}[/red]")
        raise typer.Exit(code=1)

@app.command("list")
def list_cmd():
    """List all available snapshots in the project."""
    project_root = find_project_root()
    manager = MemoryManager(project_root)
    
    if not manager.is_initialized():
        console.print("[red]Unimem is not initialized. Run 'unimem init' first.[/red]")
        raise typer.Exit(code=1)
        
    try:
        snap_list = snapshots.list_snapshots(project_root)
        if not snap_list:
            console.print("[yellow]No snapshots found.[/yellow]")
            return
            
        table = Table(title="📷 Available Snapshots")
        table.add_column("Index", style="cyan", width=6)
        table.add_column("Filename", style="green")
        table.add_column("Created At", style="magenta")
        
        for i, path in enumerate(snap_list):
            # Parse timestamp from name like state_snapshot_2026-06-10T10-48-19.json
            name = path.name
            timestamp = name.replace("state_snapshot_", "").replace(".json", "").replace("-", ":")
            # Reconstruct first occurrences of : back
            parts = timestamp.split(":")
            if len(parts) >= 3:
                # state_snapshot_2026_06_10T10_48_19
                # Let's just display the name clean
                display_ts = path.name.replace("state_snapshot_", "").replace(".json", "")
            else:
                display_ts = timestamp
            table.add_row(str(i + 1), name, display_ts)
            
        console.print(table)
    except Exception as e:
        console.print(f"[red]Error listing snapshots: {e}[/red]")
        raise typer.Exit(code=1)

@app.command("restore")
def restore_cmd(
    name: str = typer.Argument(..., help="Name of the snapshot file or index to restore (1-based index).")
):
    """Restore the project state from a historical snapshot."""
    project_root = find_project_root()
    manager = MemoryManager(project_root)
    
    if not manager.is_initialized():
        console.print("[red]Unimem is not initialized. Run 'unimem init' first.[/red]")
        raise typer.Exit(code=1)
        
    try:
        snap_list = snapshots.list_snapshots(project_root)
        target_path = None
        
        # Check if the name represents an integer index
        if name.isdigit():
            idx = int(name) - 1
            if 0 <= idx < len(snap_list):
                target_path = snap_list[idx]
            else:
                console.print(f"[red]Invalid snapshot index. Must be between 1 and {len(snap_list)}.[/red]")
                raise typer.Exit(code=1)
        else:
            # Check by filename
            for path in snap_list:
                if path.name == name or path.name.replace(".json", "") == name:
                    target_path = path
                    break
                    
        if not target_path:
            console.print(f"[red]Snapshot '{name}' not found.[/red]")
            raise typer.Exit(code=1)
            
        restored_state = snapshots.restore_snapshot(project_root, target_path)
        console.print(f"[green]Successfully restored state from [bold]{target_path.name}[/bold][/green]")
        console.print(f"Project name: {restored_state.project_name}")
        console.print(f"Goal: {restored_state.current_goal}")
        console.print(f"Current Task: {restored_state.current_task}")
    except Exception as e:
        console.print(f"[red]Error restoring snapshot: {e}[/red]")
        raise typer.Exit(code=1)
