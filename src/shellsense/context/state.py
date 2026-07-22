from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ShellState:
    cwd: str = ""
    git_root: str = ""
    git_branch: str = ""
    git_is_dirty: bool = False
    project_type: str = ""
    conda_env: str = ""
    virtualenv: str = ""
    sudo_mode: bool = False
    has_dockerfile: bool = False
    has_compose: bool = False
    kube_context: str = ""
    has_terraform: bool = False
    cloud_profile: str = ""
    last_command: str = ""
    last_exit_code: int = 0
    recent_history: list[str] = field(default_factory=list)
