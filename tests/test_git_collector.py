"""Tests for GitCollector class using GitPython integration."""

import os
from pathlib import Path
from unimem.collector.git_collector import GitCollector

def test_is_git_repo(temp_dir, git_repo):
    """Verify repo identification."""
    assert not GitCollector.is_git_repo(temp_dir)
    assert GitCollector.is_git_repo(git_repo)

def test_get_current_branch(git_repo):
    """Verify active branch name retrieval."""
    branch = GitCollector.get_current_branch(git_repo)
    # Typically master or main depending on local default branch config
    assert branch in ("master", "main")

def test_get_latest_commit(git_repo):
    """Verify commit metadata extraction."""
    commit = GitCollector.get_latest_commit(git_repo)
    assert commit is not None
    assert "sha" in commit
    assert commit["message"] == "Initial commit"
    assert "Test User" in commit["author"]
    assert "test@example.com" in commit["author"]

def test_get_changed_files(git_repo):
    """Verify staged, unstaged, and untracked file categorization."""
    # Before edits
    changes = GitCollector.get_changed_files(git_repo)
    assert changes["staged"] == []
    assert changes["unstaged"] == []
    assert changes["untracked"] == []
    
    # Create an untracked file
    untracked_file = git_repo / "untracked.py"
    untracked_file.write_text("print('hello')", encoding="utf-8")
    
    changes = GitCollector.get_changed_files(git_repo)
    assert "untracked.py" in changes["untracked"]
    assert changes["staged"] == []
    assert changes["unstaged"] == []
    
    # Stage the file
    import git
    repo = git.Repo(git_repo)
    repo.index.add(["untracked.py"])
    
    changes = GitCollector.get_changed_files(git_repo)
    assert "untracked.py" in changes["staged"]
    assert "untracked.py" not in changes["untracked"]
    assert changes["unstaged"] == []
    
    # Modify the tracked file without staging
    readme = git_repo / "README.md"
    readme.write_text("# Updated Test Repo\n", encoding="utf-8")
    
    changes = GitCollector.get_changed_files(git_repo)
    assert "README.md" in changes["unstaged"]
    assert "untracked.py" in changes["staged"]
    
def test_get_diff(git_repo):
    """Verify git diff text rendering."""
    # Modify a file to generate a diff
    readme = git_repo / "README.md"
    readme.write_text("# Changed README\n", encoding="utf-8")
    
    diff_text = GitCollector.get_diff(git_repo, staged=False)
    assert "Changed README" in diff_text
    
    # Stage it
    import git
    repo = git.Repo(git_repo)
    repo.index.add(["README.md"])
    
    diff_text_cached = GitCollector.get_diff(git_repo, staged=True)
    assert "Changed README" in diff_text_cached
