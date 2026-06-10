"""Command to manage project tasks."""

from pathlib import Path
import typer
from rich.console import Console
from unimem.memory.manager import MemoryManager
from unimem.utils.paths import find_project_root

app = typer.Typer(help="Manage project tasks")
console = Console()

@app.command("done")
def done_cmd(
    next_task: str = typer.Option(
        "", 
        "--next", 
        help="Description of the next task."
    )
):
    """Complete the current task and promote the next one."""
    project_root = find_project_root()
    manager = MemoryManager(project_root)

    if not manager.is_initialized():
        manager.bootstrap_if_needed()
        console.print(f"[green]Initialized Unimem in {project_root}.[/green]")
        
    try:
        # Complete task and promote
        manager.complete_task(next_task)
        
        # Load the updated state to print
        state = manager.load_state()
        
        console.print("[green]Task completed and promoted successfully![/green]")
        console.print(f"  [bold]Current Goal:[/bold] {state.current_goal or 'Not set'}")
        console.print(f"  [bold]Current Task:[/bold] {state.current_task or 'Not set'}")
        console.print(f"  [bold]Next Task:[/bold]    {state.next_task or 'Not set'}")
    except Exception as e:
        console.print(f"[red]Error completing task: {e}[/red]")
        raise typer.Exit(code=1)
