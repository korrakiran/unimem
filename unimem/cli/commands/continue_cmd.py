"""Command to display project handoff context optimized for AI agent consumption."""

from pathlib import Path
import typer
from rich.console import Console
from unimem.memory.manager import MemoryManager
from unimem.utils.paths import find_project_root

app = typer.Typer()
console = Console()

@app.command("continue")
def continue_cmd(
    raw: bool = typer.Option(
        False, 
        "--raw", "-r", 
        help="Print raw markdown without any terminal formatting (ideal for piping to LLMs)."
    )
):
    """Output the project handoff intelligence for another AI agent to resume work immediately."""
    project_root = find_project_root()
    manager = MemoryManager(project_root)

    if not manager.is_initialized():
        manager.bootstrap_if_needed()
        if not raw:
            console.print(f"[green]Initialized Unimem in {project_root}.[/green]")
        
    try:
        state = manager.load_state()
    except Exception as e:
        if raw:
            print(f"ERROR: Failed to load state: {e}")
        else:
            console.print(f"[red]Failed to load state: {e}[/red]")
        raise typer.Exit(code=1)
        
    # Build text output
    comp_list = "\n".join([f"- {item}" for item in state.completed_features]) if state.completed_features else "- None"
    ip_list = "\n".join([f"- {item}" for item in state.in_progress_features]) if state.in_progress_features else "- None"
    dec_list = "\n".join([f"- {item}" for item in state.recent_decisions]) if state.recent_decisions else "- None"
    files_list = "\n".join([f"- {item}" for item in state.important_files]) if state.important_files else "- None"
    
    handoff_text = f"""PROJECT HANDOFF

Project:
{state.project_name}

Description:
{state.description or "No description provided."}

Current Goal:
{state.current_goal or "Not set"}

Current Task:
{state.current_task or "Not set"}

Completed:
{comp_list}

In Progress:
{ip_list}

Next Task:
{state.next_task or "Not set"}

Recent Decisions:
{dec_list}

Important Files:
{files_list}
"""
    
    if raw:
        # Print directly to stdout without rich processing (e.g. for pipelines or command piping)
        print(handoff_text.strip())
    else:
        # Pretty print using rich
        from rich.panel import Panel
        console.print(Panel(
            handoff_text.strip(),
            title="🏁 Unimem Handoff Context",
            border_style="bold green",
            expand=False
        ))
