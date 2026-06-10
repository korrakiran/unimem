"""Tests for the Typer CLI application commands."""

import os
from pathlib import Path
from typer.testing import CliRunner

from unimem.cli.app import app
from unimem.memory.manager import MemoryManager
from unimem.utils.paths import get_state_file

runner = CliRunner()

def test_cli_version():
    """Verify version command flag."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "version" in result.stdout

def test_cli_init(temp_dir, monkeypatch):
    """Verify 'unimem init' creates state file in the active folder."""
    # Mock current working directory to temp_dir
    monkeypatch.chdir(temp_dir)
    
    result = runner.invoke(app, ["init", "--name", "TestApp", "--desc", "My test app description"])
    assert result.exit_code == 0
    assert "Successfully initialized Unimem" in result.stdout
    
    # Check that state.json was created
    assert get_state_file(temp_dir).exists()
    
    # Running init again should warn
    result2 = runner.invoke(app, ["init"])
    assert "already initialized" in result2.stdout

def test_cli_status(initialized_unimem, monkeypatch):
    """Verify 'unimem status' renders project data."""
    monkeypatch.chdir(initialized_unimem)
    
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "TestProject" in result.stdout
    assert "A test project description" in result.stdout

def test_cli_continue(initialized_unimem, monkeypatch):
    """Verify 'unimem continue' formats project handoff."""
    monkeypatch.chdir(initialized_unimem)
    
    result = runner.invoke(app, ["continue"])
    assert result.exit_code == 0
    assert "PROJECT HANDOFF" in result.stdout
    assert "TestProject" in result.stdout

def test_cli_doctor(initialized_unimem, monkeypatch):
    """Verify 'unimem doctor' diagnostic tool report."""
    monkeypatch.chdir(initialized_unimem)
    
    result = runner.invoke(app, ["doctor"])
    if result.exit_code != 0:
        print("Doctor Command stdout:")
        print(result.stdout)
        if result.exception:
            print("Doctor Command exception:")
            print(result.exception)
    assert result.exit_code == 0
    assert "Diagnostic Checks" in result.stdout
    assert "Initialization" in result.stdout

def test_cli_summary(initialized_unimem, monkeypatch):
    """Verify 'unimem summary' compiles project events."""
    monkeypatch.chdir(initialized_unimem)
    
    result = runner.invoke(app, ["summary"])
    assert result.exit_code == 0
    assert "Rebuild complete" in result.stdout

def test_cli_snapshot_commands(initialized_unimem, monkeypatch):
    """Verify 'unimem snapshot' create, list, and restore flow."""
    monkeypatch.chdir(initialized_unimem)
    
    # Create snapshot
    result_create = runner.invoke(app, ["snapshot", "create"])
    assert result_create.exit_code == 0
    assert "Snapshot created successfully" in result_create.stdout
    
    # List snapshots
    result_list = runner.invoke(app, ["snapshot", "list"])
    assert result_list.exit_code == 0
    assert "Available Snapshots" in result_list.stdout
    
    # Restore snapshot
    result_restore = runner.invoke(app, ["snapshot", "restore", "1"])
    assert result_restore.exit_code == 0
    assert "Successfully restored state" in result_restore.stdout
