from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from typing import Any

from shellsense.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class GitIntelligenceResult:
    repo_root: str = ""
    branch: str = ""
    status_lines: list[str] = field(default_factory=list)
    recent_commits: list[dict[str, str]] = field(default_factory=list)
    ahead_behind: str = ""
    stashed: int = 0
    untracked: int = 0
    modified: int = 0
    is_clean: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "repo_root": self.repo_root,
            "branch": self.branch,
            "is_clean": self.is_clean,
            "modified": self.modified,
            "untracked": self.untracked,
            "stashed": self.stashed,
            "ahead_behind": self.ahead_behind,
            "recent_commits": self.recent_commits[-5:],
        }


class GitIntelligence:
    def __init__(self) -> None:
        self._git_dir: str | None = None

    def _run_git(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                ["git"] + args,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except Exception as e:
            logger.debug("Git command failed: %s", e)
            result: subprocess.CompletedProcess[str] = subprocess.CompletedProcess(
                args, 1, "", str(e)
            )
            return result

    def _is_git_repo(self) -> bool:
        r = self._run_git(["rev-parse", "--is-inside-work-tree"])
        return r.returncode == 0 and r.stdout.strip() == "true"

    def get_status(self) -> GitIntelligenceResult:
        result = GitIntelligenceResult()

        if not self._is_git_repo():
            return result

        r = self._run_git(["rev-parse", "--show-toplevel"])
        if r.returncode == 0:
            result.repo_root = r.stdout.strip()
        else:
            return result

        r = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"])
        if r.returncode == 0:
            result.branch = r.stdout.strip()

        r = self._run_git(["status", "--porcelain"])
        if r.returncode == 0:
            result.status_lines = [l for l in r.stdout.strip().split("\n") if l.strip()]
            for line in result.status_lines:
                if line.startswith("??"):
                    result.untracked += 1
                elif line.startswith(" M") or line.startswith("M ") or "AM" in line:
                    result.modified += 1
            result.is_clean = len(result.status_lines) == 0

        stashed_out = self._run_git(["stash", "list"])
        if stashed_out.returncode == 0:
            result.stashed = len(
                [l for l in stashed_out.stdout.strip().split("\n") if l.strip()]
            )

        r = self._run_git(["log", "--oneline", "-10"])
        if r.returncode == 0:
            for line in r.stdout.strip().split("\n"):
                if line.strip():
                    parts = line.strip().split(" ", 1)
                    result.recent_commits.append(
                        {
                            "hash": parts[0] if len(parts) > 0 else "",
                            "message": parts[1] if len(parts) > 1 else "",
                        }
                    )

        r = self._run_git(["rev-list", "--left-right", "--count", "@{upstream}...HEAD"])
        if r.returncode == 0 and r.stdout.strip():
            result.ahead_behind = r.stdout.strip()

        return result

    def explain_command(self, git_command: str) -> str:
        r = self._run_git(["help", git_command])
        if r.returncode == 0:
            return r.stdout or ""
        r = self._run_git(git_command.split() + ["--help"])
        if r.returncode == 0:
            return r.stdout or ""
        return ""

    def get_short_log(self, count: int = 10) -> str:
        r = self._run_git(["log", f"-{count}", "--oneline", "--graph", "--decorate"])
        if r.returncode == 0:
            return r.stdout or ""
        return ""

    def get_diff(self, path: str = "") -> str:
        args = ["diff", "--stat"]
        if path:
            args.append(path)
        r = self._run_git(args)
        if r.returncode == 0:
            return r.stdout or ""
        return ""


def get_git_status() -> GitIntelligenceResult:
    git = GitIntelligence()
    return git.get_status()
