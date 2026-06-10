"""Command to run health checks and diagnostics on Unimem environment."""

from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table

from unimem.memory.manager import MemoryManager
from unimem.collector.git_collector import GitCollector
from unimem.utils.paths import (
    find_project_root,
    get_unimem_dir,
    get_events_dir,
    get_sessions_dir,
    get_snapshots_dir,
    get_decisions_dir,
    get_state_file,
)

app = typer.Typer()
console = Console()

@app.command("doctor")
def doctor_cmd():
    """Run diagnostic checks on the Unimem setup in this directory."""
    project_root = find_project_root()
    manager = MemoryManager(project_root)
    
    console.print("[cyan]Running Unimem Diagnostics...[/cyan]\n")
    
    table = Table(title="Diagnostic Checks")
    table.add_column("Component", style="bold")
    table.add_column("Status", width=10)
    table.add_column("Details")
    
    all_ok = True
    
    # Check 1: Initialization
    if manager.is_initialized():
        table.add_row("Initialization", "[green]OK[/green]", "Unimem initialized directory found.")
    else:
        table.add_row("Initialization", "[yellow]WARN[/yellow]", "Unimem is not initialized. Run 'unimem init' to fix.")
        all_ok = False
        
    # Check 2: State File Health
    if manager.is_initialized():
        try:
            state = manager.load_state()
            table.add_row("State File Integrity", "[green]OK[/green]", f"state.json loaded successfully (Project: {state.project_name}).")
        except Exception as e:
            table.add_row("State File Integrity", "[red]ERROR[/red]", f"Failed to parse state.json: {e}")
            all_ok = False
            
    # Check 3: Directories Existence & Writable
    if manager.is_initialized():
        dirs_to_check = {
            "Events": get_events_dir(project_root),
            "Sessions": get_sessions_dir(project_root),
            "Snapshots": get_snapshots_dir(project_root),
            "Decisions": get_decisions_dir(project_root)
        }
        for name, path in dirs_to_check.items():
            if not path.exists():
                table.add_row(f"{name} Folder", "[red]ERROR[/red]", f"Directory '{path.name}' is missing.")
                all_ok = False
            elif not os.access(path, os.W_OK):
                table.add_row(f"{name} Folder", "[red]ERROR[/red]", f"Directory '{path.name}' is not writable.")
                all_ok = False
            else:
                table.add_row(f"{name} Folder", "[green]OK[/green]", "Directory exists and is writable.")
                
    # Check 4: Git Integration
    is_git = GitCollector.is_git_repo(project_root)
    if is_git:
        table.add_row("Git Integration", "[green]OK[/green]", "Valid Git repository detected.")
    else:
        table.add_row("Git Integration", "[yellow]WARN[/yellow]", "No Git repository found (untracked mode).")
        
    # Check 5: Libraries
    try:
        import watchdog
        import git
        try:
            import importlib.metadata
            wd_version = importlib.metadata.version("watchdog")
        except Exception:
            wd_version = "installed"
        table.add_row("Dependencies", "[green]OK[/green]", f"watchdog ({wd_version}) & gitpython imported successfully.")
    except Exception as e:
        table.add_row("Dependencies", "[red]ERROR[/red]", f"Missing dependencies: {e}")
        all_ok = False
        
    console.print(table)
    
    if all_ok:
        console.print("\n[bold green]✓ Unimem environment is fully healthy![/bold green]")
    else:
        console.print("\n[bold red]✗ Diagnostics found issues. Please review details above.[/bold red]")
        raise typer.Exit(code=1)
        
# Import os for directory checks
import os
