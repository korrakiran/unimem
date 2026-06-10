"""Command to display the current Unimem and git status."""

from pathlib import Path
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns

from unimem.memory.manager import MemoryManager
from unimem.collector.git_collector import GitCollector
from unimem.utils.paths import find_project_root, get_events_dir
from unimem.storage.json_store import JsonStore
from unimem.memory.schemas import Event

app = typer.Typer()
console = Console()

@app.command("status")
def status_cmd():
    """Display Unimem initialization, project state details, and Git status."""
    project_root = find_project_root()
    manager = MemoryManager(project_root)
    
    if not manager.is_initialized():
        console.print("[red]Unimem is not initialized in this project.[/red]")
        console.print("Run [cyan]unimem init[/cyan] to initialize.")
        raise typer.Exit(code=1)
        
    try:
        state = manager.load_state()
    except Exception as e:
        console.print(f"[red]Error loading state: {e}[/red]")
        raise typer.Exit(code=1)
        
    # Header Panel
    console.print(Panel(
        f"[bold cyan]{state.project_name}[/bold cyan]\n[italic]{state.description or 'No description'}[/italic]\n\n"
        f"[bold]Root:[/bold] {project_root}",
        title="Unimem Status",
        expand=False
    ))
    
    # Goal / Task Panel
    console.print(Panel(
        f"[bold green]Goal:[/bold green] {state.current_goal or 'Not set'}\n"
        f"[bold yellow]Current Task:[/bold yellow] {state.current_task or 'Not set'}\n"
        f"[bold blue]Next Task:[/bold blue] {state.next_task or 'Not set'}",
        title="🎯 Current Focus",
        expand=False
    ))
    
    # Git Integration details
    is_git = GitCollector.is_git_repo(project_root)
    git_status_text = ""
    if is_git:
        branch = GitCollector.get_current_branch(project_root)
        latest_commit = GitCollector.get_latest_commit(project_root)
        changes = GitCollector.get_changed_files(project_root)
        
        git_status_text = f"[bold]Branch:[/bold] {branch}\n"
        if latest_commit:
            git_status_text += f"[bold]Latest Commit:[/bold] {latest_commit['sha'][:7]} - {latest_commit['message']}\n"
            
        total_changed = len(changes["staged"]) + len(changes["unstaged"]) + len(changes["untracked"])
        git_status_text += f"[bold]Modified/Untracked Files:[/bold] {total_changed} files"
        
        # Display the modified files if any
        if total_changed > 0:
            git_status_text += "\n"
            for f in changes["staged"]:
                git_status_text += f"  [green]staged:   {f}[/green]\n"
            for f in changes["unstaged"]:
                git_status_text += f"  [yellow]modified: {f}[/yellow]\n"
            for f in changes["untracked"]:
                git_status_text += f"  [red]untracked: {f}[/red]\n"
    else:
        git_status_text = "[yellow]Not a Git repository.[/yellow]"
        
    console.print(Panel(
        git_status_text.strip(),
        title="🌿 Git Status",
        expand=False
    ))
    
    # List recent events
    events_dir = get_events_dir(project_root)
    if events_dir.exists():
        event_files = list(events_dir.glob("*.json"))
        event_files.sort(key=lambda p: p.name, reverse=True) # Show newest first
        
        if event_files:
            table = Table(title="🕒 Recent Events")
            table.add_column("Timestamp", style="dim", width=20)
            table.add_column("Tool", style="cyan")
            table.add_column("Type", style="magenta")
            table.add_column("Summary", style="green")
            
            for f in event_files[:5]: # Show latest 5
                try:
                    data = JsonStore.load(f)
                    ev = Event(**data)
                    # format timestamp for display (e.g. ignore sub-seconds)
                    ts = ev.timestamp.split(".")[0] if "." in ev.timestamp else ev.timestamp
                    table.add_row(ts, ev.tool, ev.event_type, ev.response_summary)
                except Exception:
                    pass
            console.print(table)
        else:
            console.print("[dim]No events logged yet.[/dim]")
