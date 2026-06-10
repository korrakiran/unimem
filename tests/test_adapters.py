"""Tests for the agent adapter classes and registry."""

from pathlib import Path
import pytest
from unimem.adapters.registry import AdapterRegistry, load_builtin_adapters
from unimem.adapters.generic import GenericAdapter
from unimem.adapters.claude import ClaudeAdapter
from unimem.adapters.gemini import GeminiAdapter
from unimem.adapters.codex import CodexAdapter
from unimem.memory.manager import MemoryManager

def test_adapter_registry(temp_dir):
    """Verify built-in adapters register automatically."""
    load_builtin_adapters()
    
    # List active adapters
    adapters = AdapterRegistry.list_adapters()
    assert "generic" in adapters
    assert "claude" in adapters
    assert "gemini" in adapters
    assert "codex" in adapters
    
    # Resolve instances
    a_generic = AdapterRegistry.get_adapter("generic", temp_dir)
    assert isinstance(a_generic, GenericAdapter)
    
    a_claude = AdapterRegistry.get_adapter("claude", temp_dir)
    assert isinstance(a_claude, ClaudeAdapter)
    
    # Check fallback
    a_unknown = AdapterRegistry.get_adapter("nonexistent_tool", temp_dir)
    assert isinstance(a_unknown, GenericAdapter)

def test_generic_adapter_load_context(initialized_unimem):
    """Verify loading context creates appropriate prompt dict."""
    adapter = GenericAdapter(initialized_unimem)
    ctx = adapter.load_context()
    
    assert ctx["project_name"] == "TestProject"
    assert "context_md" in ctx
    assert "state_json" in ctx

def test_generic_adapter_launch(initialized_unimem):
    """Verify executing subprocesses via the adapter runs and writes session logs."""
    adapter = GenericAdapter(initialized_unimem)
    manager = MemoryManager(initialized_unimem)
    
    # Run a simple echo command as a subprocess
    # Using python executable to echo safely across platforms
    import sys
    command = [sys.executable, "-c", "print('hello from adapter')"]
    
    result = adapter.launch(command)
    assert result.returncode == 0
    
    # Verify a session was recorded and closed
    session_files = list((initialized_unimem / ".unimem" / "sessions").glob("*.json"))
    assert len(session_files) >= 1
    
    # Read the session file
    from unimem.storage.json_store import JsonStore
    from unimem.memory.schemas import Session
    
    session_data = JsonStore.load(session_files[0])
    session = Session(**session_data)
    
    assert session.tool == "generic"
    assert session.end_time is not None
