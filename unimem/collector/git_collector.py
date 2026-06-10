"""Git metadata collector using GitPython to inspect repo state, branch, commits, and diffs."""

from pathlib import Path
from typing import Dict, List, Optional
import git

class GitCollector:
    """Collects Git metrics and state details for Unimem."""

    @staticmethod
    def is_git_repo(path: Path) -> bool:
        """Check if path is inside a Git repository."""
        try:
            git.Repo(path, search_parent_directories=True)
            return True
        except (git.InvalidGitRepositoryError, git.NoSuchPathError):
            return False

    @staticmethod
    def _get_repo(path: Path) -> Optional[git.Repo]:
        """Safely open and return a git.Repo instance."""
        try:
            return git.Repo(path, search_parent_directories=True)
        except Exception:
            return None

    @classmethod
    def get_current_branch(cls, path: Path) -> str:
        """Get the current active branch name."""
        repo = cls._get_repo(path)
        if not repo:
            return "unknown"
        try:
            if repo.head.is_detached:
                return f"detached-at-{repo.head.commit.hexsha[:7]}"
            return repo.active_branch.name
        except Exception:
            # Could be empty repository with no commits yet
            return "main (no commits)"

    @classmethod
    def get_latest_commit(cls, path: Path) -> Optional[Dict[str, str]]:
        """Get dictionary details about the latest commit on the current branch."""
        repo = cls._get_repo(path)
        if not repo:
            return None
        try:
            commit = repo.head.commit
            return {
                "sha": commit.hexsha,
                "message": commit.message.strip(),
                "author": f"{commit.author.name} <{commit.author.email}>",
                "timestamp": str(commit.committed_datetime),
            }
        except Exception:
            return None

    @classmethod
    def get_changed_files(cls, path: Path) -> Dict[str, List[str]]:
        """Get a list of staged, unstaged, and untracked files."""
        repo = cls._get_repo(path)
        if not repo:
            return {"staged": [], "unstaged": [], "untracked": []}
            
        staged = []
        unstaged = []
        untracked = [str(f) for f in repo.untracked_files]
        
        try:
            # Diff between HEAD and index (staged changes)
            if repo.head.is_valid():
                for diff in repo.index.diff("HEAD"):
                    if diff.a_path:
                        staged.append(diff.a_path)
            else:
                # Initial commit, all added files in index are staged
                for path_index, _ in repo.index.entries:
                    staged.append(path_index[0])
                    
            # Diff between index and working tree (unstaged changes)
            for diff in repo.index.diff(None):
                if diff.a_path:
                    unstaged.append(diff.a_path)
        except Exception:
            pass
            
        return {
            "staged": sorted(list(set(staged))),
            "unstaged": sorted(list(set(unstaged))),
            "untracked": sorted(untracked)
        }

    @classmethod
    def get_diff(cls, path: Path, staged: bool = False) -> str:
        """Get the Git diff as a string."""
        repo = cls._get_repo(path)
        if not repo:
            return ""
        try:
            if staged:
                # Diff between HEAD and index
                if repo.head.is_valid():
                    return repo.git.diff("--cached")
                return ""
            else:
                # Diff between index and working tree
                return repo.git.diff()
        except Exception as e:
            return f"Error getting git diff: {e}"

    @classmethod
    def get_recent_commits(cls, path: Path, limit: int = 5) -> List[Dict[str, str]]:
        """Get a list of recent commits."""
        repo = cls._get_repo(path)
        if not repo or not repo.head.is_valid():
            return []
        try:
            commits = list(repo.iter_commits(max_count=limit))
            return [
                {
                    "sha": c.hexsha[:7],
                    "message": c.summary,
                    "author": c.author.name,
                    "date": c.committed_datetime.strftime("%Y-%m-%d %H:%M"),
                }
                for c in commits
            ]
        except Exception:
            return []
