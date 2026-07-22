from __future__ import annotations

import os
import subprocess
from pathlib import Path

from shellsense.context.state import ShellState
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)


class ShellStateInferrer:

    def __init__(self) -> None:
        self._history_cache: list[str] = []

    def infer(self) -> ShellState:
        state = ShellState()
        state.cwd = os.getcwd()
        self._infer_git(state)
        self._infer_project_type(state)
        self._infer_python_env(state)
        self._infer_docker(state)
        self._infer_kube_context(state)
        self._infer_terraform(state)
        self._infer_cloud_context(state)
        self._infer_sudo_mode(state)
        self._infer_recent_history(state)
        return state

    def _run(self, cmd: list[str], timeout: int = 3) -> str:
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )
            return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return ""

    def _file_exists(self, *parts: Path | str) -> bool:
        return Path(*parts).exists()

    def _infer_git(self, state: ShellState) -> None:
        root = self._run(["git", "rev-parse", "--show-toplevel"])
        if root:
            state.git_root = root
            branch = self._run(["git", "branch", "--show-current"], timeout=2)
            state.git_branch = branch
            status = self._run(["git", "status", "--porcelain"], timeout=2)
            state.git_is_dirty = bool(status.strip())

    def _infer_project_type(self, state: ShellState) -> None:
        cwd = Path(state.cwd)
        checks = [
            (
                "python",
                [
                    "pyproject.toml",
                    "setup.py",
                    "setup.cfg",
                    "Pipfile",
                    "requirements.txt",
                    "tox.ini",
                    "noxfile.py",
                ],
            ),
            ("node", ["package.json", "yarn.lock", "pnpm-lock.yaml"]),
            ("go", ["go.mod", "go.sum"]),
            ("rust", ["Cargo.toml"]),
            ("ruby", ["Gemfile", "Rakefile"]),
            ("php", ["composer.json"]),
            ("java", ["pom.xml", "build.gradle", "build.gradle.kts"]),
        ]
        for project_type, markers in checks:
            if any(self._file_exists(cwd, m) for m in markers):
                state.project_type = project_type
                return

    def _infer_python_env(self, state: ShellState) -> None:
        conda = os.environ.get("CONDA_DEFAULT_ENV", "")
        if conda:
            state.conda_env = conda
        venv = os.environ.get("VIRTUAL_ENV", "")
        if venv:
            if os.name == "nt":
                state.virtualenv = os.path.basename(venv.rstrip("\\"))
            else:
                state.virtualenv = os.path.basename(venv)

    def _infer_docker(self, state: ShellState) -> None:
        cwd = Path(state.cwd)
        state.has_dockerfile = self._file_exists(cwd, "Dockerfile") or any(
            self._file_exists(cwd, f"Dockerfile.{ext}")
            for ext in ["dev", "prod", "staging"]
        )
        state.has_compose = any(
            self._file_exists(cwd, name)
            for name in [
                "docker-compose.yml",
                "docker-compose.yaml",
                "compose.yml",
                "compose.yaml",
            ]
        )

    def _infer_kube_context(self, state: ShellState) -> None:
        config = os.environ.get("KUBECONFIG", "")
        has_kube_files = bool(
            config or self._file_exists(Path.home(), ".kube", "config")
        )
        if has_kube_files:
            ctx = self._run(["kubectl", "config", "current-context"])
            if ctx:
                state.kube_context = ctx

    def _infer_terraform(self, state: ShellState) -> None:
        cwd = Path(state.cwd)
        state.has_terraform = bool(list(cwd.rglob("*.tf"))[:1])

    def _infer_cloud_context(self, state: ShellState) -> None:
        aws_profile = os.environ.get("AWS_PROFILE") or os.environ.get(
            "AWS_DEFAULT_PROFILE", ""
        )
        gcloud_project = os.environ.get("CLOUDSDK_CORE_PROJECT", "")
        state.cloud_profile = aws_profile or gcloud_project or ""

    def _infer_sudo_mode(self, state: ShellState) -> None:
        history = self._get_history(1)
        if history and history[0].startswith("sudo "):
            state.sudo_mode = True
            state.last_command = history[0]

    def _infer_recent_history(self, state: ShellState) -> None:
        state.recent_history = self._get_history(10)

    def _get_history(self, limit: int = 10) -> list[str]:
        histfile = os.environ.get("HISTFILE", "")
        if not histfile:
            for candidate in [
                os.path.expanduser("~/.bash_history"),
                os.path.expanduser("~/.zsh_history"),
            ]:
                if os.path.isfile(candidate):
                    histfile = candidate
                    break
        if not histfile or not os.path.isfile(histfile):
            return self._history_cache[-limit:]

        try:
            with open(histfile, "rb") as f:
                raw = f.read(65536)
        except OSError:
            return self._history_cache[-limit:]

        lines = []
        for line in raw.decode("utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            if "\x00" in line:
                parts = line.split("\x00")
                line = parts[-1].strip()
            lines.append(line)

        if len(lines) > limit:
            lines = lines[-limit:]

        self._history_cache = lines
        return lines
