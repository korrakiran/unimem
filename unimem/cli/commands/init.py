"""Command to initialize Unimem in a project directory."""

from pathlib import Path
import typer
from rich.console import Console
from unimem.memory.manager import MemoryManager
from unimem.utils.paths import find_project_root

app = typer.Typer()
console = Console()

@app.command("init")
def init_cmd(
    name: str = typer.Option(
        None, 
        "--name", "-n", 
        help="Name of the project. Defaults to the current directory name."
    ),
    description: str = typer.Option(
        "", 
        "--desc", "-d", 
        help="Short description of the project."
    )
):
    """Initialize a new Unimem project memory layer in the current directory."""
    project_root = Path.cwd().resolve()
    
    # If no name provided, use directory name
    if not name:
        name = project_root.name
        
    manager = MemoryManager(project_root)
    if manager.is_initialized():
        console.print(f"[yellow]Unimem is already initialized in {project_root}.[/yellow]")
        raise typer.Exit()
        
    try:
        manager.initialize(name, description)
    except Exception as e:
        console.print(f"[red]Error initializing Unimem: {e}[/red]")
        raise typer.Exit(code=1)
