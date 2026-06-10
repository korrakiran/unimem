"""Test fixtures for unimem test suites."""

import os
import shutil
import tempfile
from pathlib import Path
import pytest
import git

from unimem.memory.manager import MemoryManager

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    test_dir = tempfile.mkdtemp()
    yield Path(test_dir)
    shutil.rmtree(test_dir)

@pytest.fixture
def git_repo():
    """Create a temporary directory initialized as a Git repository with a commit."""
    test_dir = tempfile.mkdtemp()
    test_path = Path(test_dir)
    repo = git.Repo.init(test_path)
    # Configure user name/email so commits can be created in environments
    with repo.config_writer() as cw:
        cw.set_value("user", "name", "Test User")
        cw.set_value("user", "email", "test@example.com")
        
    # Create an initial file and commit
    test_file = test_path / "README.md"
    test_file.write_text("# Test Repo\n", encoding="utf-8")
    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")
    
    yield test_path
    shutil.rmtree(test_dir)

@pytest.fixture
def initialized_unimem(temp_dir):
    """Return a path to a directory with Unimem initialized."""
    manager = MemoryManager(temp_dir)
    manager.initialize("TestProject", "A test project description.")
    return temp_dir
