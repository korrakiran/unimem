"""Main Typer CLI application entry point compiling all subcommands."""

from pathlib import Path
from typing import List
import typer
from rich.console import Console

# Import commands
from unimem import __version__
from unimem.cli.commands.init import init_cmd
from unimem.cli.commands.status import status_cmd
from unimem.cli.commands.snapshot import app as snapshot_app
from unimem.cli.commands.summary import summary_cmd
from unimem.cli.commands.continue_cmd import continue_cmd
from unimem.cli.commands.doctor import doctor_cmd
from unimem.adapters.registry import AdapterRegistry, load_builtin_adapters
from unimem.watcher.filesystem import FilesystemWatcher
from unimem.utils.paths import find_project_root
from unimem.memory.manager import MemoryManager

app = typer.Typer(
    name="unimem",
    help="Unimem - Universal Project Memory Layer for AI Coding Agents",
    add_completion=False,
)

console = Console()

# Register sub-typers and command functions
app.command("init")(init_cmd)
app.command("status")(status_cmd)
app.add_typer(snapshot_app, name="snapshot")
app.command("summary")(summary_cmd)
app.command("continue")(continue_cmd)
app.command("doctor")(doctor_cmd)

@app.command("watch")
def watch_cmd():
    """Start the filesystem watcher to log file changes as Unimem events in real time."""
    project_root = find_project_root()
    manager = MemoryManager(project_root)
    
    if not manager.is_initialized():
        console.print("[red]Unimem is not initialized. Run 'unimem init' first.[/red]")
        raise typer.Exit(code=1)
        
    watcher = FilesystemWatcher(project_root)
    try:
        watcher.run_forever()
    except Exception as e:
        console.print(f"[red]Watcher encountered an error: {e}[/red]")
        raise typer.Exit(code=1)

@app.command("run", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def run_cmd(
    ctx: typer.Context,
    adapter: str = typer.Option(
        "generic", 
        "--adapter", "-a", 
        help="Adapter name to use (e.g. generic, claude, gemini, codex)."
    )
):
    """Run an agent command inside the Unimem memory tracking sandbox.
    
    Example: unimem run -a claude -- claude
    """
    project_root = find_project_root()
    manager = MemoryManager(project_root)
    
    if not manager.is_initialized():
        console.print("[red]Unimem is not initialized. Run 'unimem init' first.[/red]")
        raise typer.Exit(code=1)
        
    # Get extra arguments (the command to run)
    command = ctx.args
    if not command:
        console.print("[red]Error: No command specified to execute.[/red]")
        console.print("Provide a command after '--'. Example: [cyan]unimem run -a claude -- claude[/cyan]")
        raise typer.Exit(code=1)
        
    # Load adapters
    load_builtin_adapters()
    
    try:
        # Get and launch adapter
        adapter_inst = AdapterRegistry.get_adapter(adapter, project_root)
        console.print(f"[cyan]Running using '{adapter}' adapter...[/cyan]")
        adapter_inst.launch(command)
    except Exception as e:
        console.print(f"[red]Error launching adapter: {e}[/red]")
        raise typer.Exit(code=1)

def version_callback(value: bool):
    if value:
        console.print(f"Unimem version: {__version__}")
        raise typer.Exit()

@app.callback()
def main(
    version: bool = typer.Option(
        None, 
        "--version", "-v", 
        callback=version_callback, 
        is_eager=True, 
        help="Show version and exit."
    )
):
    pass

if __name__ == "__main__":
    app()
