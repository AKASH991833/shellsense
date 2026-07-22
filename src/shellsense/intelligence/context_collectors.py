from __future__ import annotations

import os
import platform
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from shellsense.utils.logging import get_logger
from shellsense.utils.platform import get_system_info

logger = get_logger(__name__)


@dataclass
class TerminalContext:
    current_command: str = ""
    command_args: list[str] = field(default_factory=list)
    working_directory: str = ""
    shell: str = ""
    operating_system: str = ""
    distribution: str = ""
    kernel_version: str = ""
    user: str = ""
    hostname: str = ""
    system_time: str = ""
    python_virtual_env: str = ""
    is_container: bool = False
    git_repo: str = ""
    git_branch: str = ""
    git_status: str = ""
    env_vars: dict[str, str] = field(default_factory=dict)
    package_managers: list[str] = field(default_factory=list)
    recent_history: list[str] = field(default_factory=list)
    mounted_filesystems: list[str] = field(default_factory=list)
    processes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "current_command": self.current_command,
            "command_args": self.command_args,
            "working_directory": self.working_directory,
            "shell": self.shell,
            "operating_system": self.operating_system,
            "distribution": self.distribution,
            "kernel_version": self.kernel_version,
            "user": self.user,
            "hostname": self.hostname,
            "system_time": self.system_time,
            "python_virtual_env": self.python_virtual_env,
            "is_container": self.is_container,
            "git_repo": self.git_repo,
            "git_branch": self.git_branch,
            "git_status": self.git_status,
            "package_managers": self.package_managers,
            "recent_history": self.recent_history,
        }

    def summary(self) -> str:
        parts = [f"OS: {self.operating_system}"]
        if self.distribution:
            parts.append(f"Distro: {self.distribution}")
        if self.shell:
            parts.append(f"Shell: {self.shell}")
        if self.working_directory:
            parts.append(f"Dir: {self.working_directory}")
        if self.git_branch:
            parts.append(f"Git: {self.git_branch}")
        return " | ".join(parts)


class ContextCollector:
    def __init__(self) -> None:
        self._cache: dict[str, Any] = {}
        self._env_allowlist: list[str] = [
            "SHELL",
            "TERM",
            "USER",
            "HOME",
            "PATH",
            "LANG",
            "LC_ALL",
            "DISPLAY",
            "EDITOR",
            "PAGER",
        ]
        self._history_cache: list[str] = []
        self._history_max: int = 20

    def set_env_allowlist(self, keys: list[str]) -> None:
        self._env_allowlist = list(keys)

    def collect_current_command(self) -> str:
        try:
            ppid = os.getppid()
            with open(f"/proc/{ppid}/cmdline") as f:
                cmd = f.read().replace("\0", " ").strip()
                return cmd
        except Exception:
            pass
        return ""

    def collect_working_directory(self) -> str:
        try:
            return os.getcwd()
        except Exception:
            return ""

    def collect_shell(self) -> str:
        return os.environ.get("SHELL", "")

    def collect_operating_system(self) -> str:
        return platform.system().lower()

    def collect_distribution(self) -> str:
        try:
            info = get_system_info()
            return info.distro or ""
        except Exception:
            return ""

    def collect_kernel_version(self) -> str:
        return platform.release()

    def collect_user(self) -> str:
        return os.environ.get("USER", os.environ.get("LOGNAME", ""))

    def collect_hostname(self) -> str:
        try:
            return platform.node()
        except Exception:
            return ""

    def collect_system_time(self) -> str:
        try:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return ""

    def collect_virtual_env(self) -> str:
        venv = os.environ.get("VIRTUAL_ENV", "")
        if venv:
            return Path(venv).name
        conda = os.environ.get("CONDA_DEFAULT_ENV", "")
        if conda:
            return f"conda:{conda}"
        return ""

    def collect_container(self) -> bool:
        try:
            if os.path.isfile("/.dockerenv"):
                return True
            if os.path.isfile("/run/.containerenv"):
                return True
            cgroup = "/proc/1/cgroup"
            if os.path.isfile(cgroup):
                with open(cgroup) as f:
                    content = f.read()
                    if (
                        "docker" in content
                        or "containerd" in content
                        or "kubepods" in content
                    ):
                        return True
        except Exception:
            pass
        return False

    def collect_git_info(self) -> dict[str, str]:
        result: dict[str, str] = {"repo": "", "branch": "", "status": ""}
        try:
            r = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if r.returncode == 0:
                result["repo"] = r.stdout.strip()
                br = subprocess.run(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if br.returncode == 0:
                    result["branch"] = br.stdout.strip()
                st = subprocess.run(
                    ["git", "status", "--porcelain"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if st.returncode == 0:
                    result["status"] = st.stdout.strip()
        except Exception:
            pass
        return result

    def collect_env_vars(self) -> dict[str, str]:
        result: dict[str, str] = {}
        for key in self._env_allowlist:
            val = os.environ.get(key)
            if val is not None:
                result[key] = val
        return result

    def collect_package_managers(self) -> list[str]:
        managers = []
        for pm, check in [
            ("apt", ["which", "apt-get"]),
            ("dnf", ["which", "dnf"]),
            ("yum", ["which", "yum"]),
            ("pacman", ["which", "pacman"]),
            ("zypper", ["which", "zypper"]),
            ("snap", ["which", "snap"]),
            ("flatpak", ["which", "flatpak"]),
            ("brew", ["which", "brew"]),
            ("pip", ["which", "pip3"]),
            ("npm", ["which", "npm"]),
            ("cargo", ["which", "cargo"]),
            ("go", ["which", "go"]),
        ]:
            try:
                r = subprocess.run(check, capture_output=True, text=True, timeout=5)
                if r.returncode == 0:
                    managers.append(pm)
            except Exception:
                pass
        return managers

    def collect_recent_history(self, max_lines: int = 20) -> list[str]:
        self._history_max = max_lines
        if self._history_cache:
            return self._history_cache[:max_lines]
        shell = os.environ.get("SHELL", "")
        history_file = ""
        if "zsh" in shell:
            history_file = os.environ.get(
                "HISTFILE", os.path.expanduser("~/.zsh_history")
            )
        elif "bash" in shell:
            history_file = os.path.expanduser("~/.bash_history")
        elif "fish" in shell:
            history_file = os.path.expanduser("~/.local/share/fish/fish_history")
        if not history_file or not os.path.isfile(history_file):
            return []
        try:
            with open(history_file, errors="ignore") as f:
                lines = f.readlines()
            self._history_cache = [l.strip() for l in lines if l.strip()][-max_lines:]
            return self._history_cache
        except Exception:
            return []

    def collect_mounted_filesystems(self) -> list[str]:
        try:
            r = subprocess.run(
                [
                    "df",
                    "-h",
                    "--type=ext4",
                    "--type=ext3",
                    "--type=xfs",
                    "--type=btrfs",
                    "--type=zfs",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if r.returncode == 0:
                return [l.strip() for l in r.stdout.strip().split("\n") if l.strip()]
        except Exception:
            pass
        return []

    def collect_processes(self, max_lines: int = 20) -> list[str]:
        try:
            r = subprocess.run(
                ["ps", "aux", "--sort=-%mem"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if r.returncode == 0:
                return [
                    l.strip()
                    for l in r.stdout.strip().split("\n")[:max_lines]
                    if l.strip()
                ]
        except Exception:
            pass
        return []

    def collect_all(self) -> TerminalContext:
        shell = self.collect_shell()
        os_name = self.collect_operating_system()
        distro = self.collect_distribution()
        cwd = self.collect_working_directory()
        git = self.collect_git_info()
        system = platform.uname()

        return TerminalContext(
            current_command=self.collect_current_command(),
            working_directory=cwd,
            shell=shell,
            operating_system=os_name,
            distribution=distro,
            kernel_version=system.release,
            user=self.collect_user(),
            hostname=system.node,
            system_time=self.collect_system_time(),
            python_virtual_env=self.collect_virtual_env(),
            is_container=self.collect_container(),
            git_repo=git.get("repo", ""),
            git_branch=git.get("branch", ""),
            git_status=git.get("status", ""),
            env_vars=self.collect_env_vars(),
            package_managers=self.collect_package_managers(),
        )

    def clear_cache(self) -> None:
        self._cache.clear()
        self._history_cache.clear()
