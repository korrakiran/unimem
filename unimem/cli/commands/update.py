"""CLI command to automatically update Unimem using the detected package manager."""

import sys
import subprocess
import typer
from rich.console import Console

console = Console()

def update_cmd():
    """Update Unimem to the latest version automatically."""
    console.print("[cyan]Detecting Unimem installation method...[/cyan]")
    
    # Check if installed via Homebrew
    is_brew = False
    executable = sys.executable
    if "cellar/unimem" in executable.lower() or "homebrew" in executable.lower():
        is_brew = True
    else:
        # Check if brew command is available and unimem is in brew list
        try:
            res = subprocess.run(["brew", "list", "unimem"], capture_output=True, text=True)
            if res.returncode == 0:
                is_brew = True
        except Exception:
            pass

    # Check if installed via pipx
    is_pipx = False
    if "pipx" in executable.lower() or "pipx" in sys.argv[0].lower():
        is_pipx = True

    try:
        if is_brew:
            console.print("[green]Detected Homebrew installation. Upgrading via brew...[/green]")
            cmd = ["brew", "upgrade", "korrakiran/unimem/unimem"]
        elif is_pipx:
            console.print("[green]Detected pipx installation. Upgrading via pipx...[/green]")
            cmd = ["pipx", "upgrade", "unimem"]
        else:
            console.print("[yellow]Could not determine package manager. Attempting pip upgrade...[/yellow]")
            cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "unimem"]

        console.print(f"[cyan]Running: {' '.join(cmd)}[/cyan]")
        
        # Run the update process with standard streams connected
        result = subprocess.run(cmd)
        if result.returncode == 0:
            # Use sys.stdout.write to avoid any lazy imports (like rich unicode data lookup)
            # which fail when the virtualenv files are hot-swapped on disk during the upgrade.
            sys.stdout.write("✓ Unimem upgraded successfully!\n")
            return
        else:
            console.print(f"[red]Upgrade failed with exit code: {result.returncode}[/red]")
            raise typer.Exit(code=result.returncode)

    except Exception as e:
        console.print(f"[red]Error during upgrade: {e}[/red]")
        raise typer.Exit(code=1)
