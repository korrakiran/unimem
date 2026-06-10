"""Command to rebuild the project state from recorded events."""

from pathlib import Path
import typer
from rich.console import Console

from unimem.config.settings import load_settings
from unimem.summarizer.state_builder import rebuild_state
from unimem.utils.paths import find_project_root
from unimem.memory.manager import MemoryManager

app = typer.Typer()
console = Console()

@app.command("summary")
def summary_cmd(
    summarizer: str = typer.Option(
        None, 
        "--engine", "-e", 
        help="Summarizer engine to use (e.g. 'local')."
    )
):
    """Compile recorded event logs into a consolidated ProjectState and update memory.md."""
    project_root = find_project_root()
    manager = MemoryManager(project_root)

    if not manager.is_initialized():
        manager.bootstrap_if_needed()
        console.print(f"[green]Initialized Unimem in {project_root}.[/green]")
        
    # Resolve summarizer type
    if not summarizer:
        settings = load_settings()
        summarizer = settings.default_summarizer or "local"
        
    console.print(f"[cyan]Compiling project events using '{summarizer}' engine...[/cyan]")
    try:
        state = rebuild_state(project_root, summarizer_type=summarizer)
        console.print("[green]Rebuild complete! Here is a summary of the project state:[/green]")
        console.print(f"  [bold]Project:[/bold]       {state.project_name}")
        console.print(f"  [bold]Goal:[/bold]          {state.current_goal}")
        console.print(f"  [bold]Current Task:[/bold]  {state.current_task}")
        console.print(f"  [bold]Next Task:[/bold]     {state.next_task}")
        console.print(f"  [bold]Important Files:[/bold] {', '.join(state.important_files[:5]) or 'None'}")
    except Exception as e:
        console.print(f"[red]Error rebuilding state: {e}[/red]")
        raise typer.Exit(code=1)
