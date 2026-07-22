from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass, field
from typing import Any

from shellsense.database.manager import DatabaseManager
from shellsense.intelligence.context_collectors import TerminalContext
from shellsense.knowledge.engine import KnowledgeEngine
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)

ERROR_PATTERNS: dict[str, dict[str, Any]] = {
    "permission_denied": {
        "patterns": [r"permission denied", r"operation not permitted", r"eacces"],
        "category": "permission",
        "severity": "medium",
        "suggestion": "Use `sudo` or check file permissions with `ls -l`.",
    },
    "command_not_found": {
        "patterns": [r"command not found", r"not found", r"no such file or directory"],
        "category": "missing_command",
        "severity": "high",
        "suggestion": "Install the required package or check the command name.",
    },
    "file_not_found": {
        "patterns": [r"no such file or directory", r"cannot access", r"file not found"],
        "category": "missing_file",
        "severity": "high",
        "suggestion": "Verify the file path exists and is spelled correctly.",
    },
    "port_in_use": {
        "patterns": [r"address already in use", r"port already in use", r"eperm"],
        "category": "network",
        "severity": "medium",
        "suggestion": "Check what is using the port with `ss -tlnp` or `lsof -i :PORT`.",
    },
    "service_failed": {
        "patterns": [
            r"failed to start",
            r"service.*failed",
            r"unit.*failed",
            r"status=1",
        ],
        "category": "service",
        "severity": "high",
        "suggestion": "Check service logs with `journalctl -xe -u SERVICE`.",
    },
    "dependency_error": {
        "patterns": [
            r"dependency",
            r"requires",
            r"unmet",
            r"depends on",
            r"not satisfiable",
        ],
        "category": "package",
        "severity": "high",
        "suggestion": "Install missing dependencies or use `apt --fix-broken install`.",
    },
    "disk_full": {
        "patterns": [r"disk full", r"no space left", r"device .* no space"],
        "category": "system",
        "severity": "critical",
        "suggestion": "Free up space: `du -sh /* | sort -h`, clean package cache, remove old logs.",
    },
    "network_unreachable": {
        "patterns": [
            r"network is unreachable",
            r"connection refused",
            r"could not resolve",
            r"timeout",
        ],
        "category": "network",
        "severity": "high",
        "suggestion": "Check network connectivity with `ping`, DNS with `dig`, or firewall with `ufw status`.",
    },
    "ssl_error": {
        "patterns": [r"ssl", r"certificate", r"tls", r"self.signed certificate"],
        "category": "security",
        "severity": "high",
        "suggestion": "Check certificate validity, update CA certificates, or verify system time.",
    },
    "package_not_found": {
        "patterns": [r"unable to locate package", r"package.*not found", r"no package"],
        "category": "package",
        "severity": "medium",
        "suggestion": "Update package lists with `apt update` or check for typos.",
    },
    "git_error": {
        "patterns": [r"fatal:.*git", r"not a git repository", r"merge conflict"],
        "category": "git",
        "severity": "medium",
        "suggestion": "Verify git repository status with `git status`.",
    },
}


@dataclass
class ErrorAnalysisResult:
    command: str = ""
    error_message: str = ""
    exit_code: int = -1
    category: str = ""
    severity: str = "unknown"
    root_cause: str = ""
    suggested_fix: str = ""
    alternative_commands: list[str] = field(default_factory=list)
    knowledge_result: dict[str, Any] | None = None
    known_error: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "command": self.command,
            "error_message": self.error_message[:500],
            "exit_code": self.exit_code,
            "category": self.category,
            "severity": self.severity,
            "root_cause": self.root_cause,
            "suggested_fix": self.suggested_fix,
            "alternative_commands": self.alternative_commands,
        }


class ErrorAnalyzer:
    def __init__(self, db: DatabaseManager | None = None) -> None:
        self._db = db
        self._knowledge: KnowledgeEngine | None = None
        if db is not None:
            self._knowledge = KnowledgeEngine(db)

    def _match_known_pattern(self, error_message: str) -> dict[str, Any] | None:
        error_lower = error_message.lower()
        for error_type, info in ERROR_PATTERNS.items():
            for pattern in info["patterns"]:
                if re.search(pattern, error_lower):
                    return {"type": error_type, **info}
        return None

    def _lookup_command_in_knowledge(self, command: str) -> dict[str, Any] | None:
        if self._knowledge is None:
            return None
        try:
            cmd_name = command.split()[0] if command.strip() else command
            result = self._knowledge.explain(cmd_name)
            if result:
                return result
        except Exception as e:
            logger.debug("Knowledge lookup failed for %s: %s", command, e)
        return None

    def _get_error_from_history(self, command: str) -> str | None:
        if self._db is None:
            return None
        try:
            cursor = self._db.execute(
                "SELECT error_message FROM error_analysis WHERE command = ? ORDER BY id DESC LIMIT 1",
                (command,),
            )
            row = cursor.fetchone()
            if row:
                val: object = row[0]
                return str(val) if val is not None else None
        except Exception:
            pass
        return None

    def analyze(
        self,
        command: str,
        error_message: str,
        exit_code: int = -1,
        context: TerminalContext | None = None,
    ) -> ErrorAnalysisResult:
        result = ErrorAnalysisResult(
            command=command,
            error_message=error_message,
            exit_code=exit_code,
        )

        known = self._match_known_pattern(error_message)
        if known:
            result.known_error = known
            result.category = known["category"]
            result.severity = known["severity"]
            result.suggested_fix = known.get("suggestion", "")
            result.root_cause = (
                f"{known['type'].replace('_', ' ').title()}: {error_message[:200]}"
            )
            alt_cmds = self._get_alternative_commands(command, known["category"])
            result.alternative_commands = alt_cmds

        knowledge = self._lookup_command_in_knowledge(command)
        if knowledge:
            result.knowledge_result = knowledge
            if not result.root_cause:
                result.root_cause = (
                    f"Error in command '{command}': {error_message[:200]}"
                )
            if not result.suggested_fix:
                errors = knowledge.get("common_errors", [])
                if errors:
                    error_lower = error_message.lower()
                    for err in errors:
                        if (
                            isinstance(err, dict)
                            and err.get("error_pattern", "").lower() in error_lower
                        ):
                            result.suggested_fix = err.get("solution", "")
                            if err.get("explanation"):
                                result.root_cause = err["explanation"]
                            break

        if not result.root_cause:
            result.root_cause = (
                f"Unknown error in command '{command}'. Exit code: {exit_code}."
            )
        if not result.suggested_fix:
            result.suggested_fix = "Check the command syntax and arguments. Use `--help` for usage information."

        self._record_analysis(result)
        return result

    def _get_alternative_commands(self, command: str, category: str) -> list[str]:
        alt: list[str] = []
        command_base = command.split()[0] if command.strip() else ""
        alt_map: dict[str, dict[str, list[str]]] = {
            "missing_command": {
                "apt": ["apt-get", "dpkg"],
                "apt-get": ["apt"],
                "yum": ["dnf"],
                "dnf": ["yum"],
                "pip": ["pip3"],
                "python": ["python3"],
                "gcc": ["clang", "cc"],
                "vim": ["nano", "vi", "neovim"],
                "nano": ["vim", "vi"],
                "systemctl": ["service"],
                "service": ["systemctl"],
                "ip": ["ifconfig", "nmcli"],
                "curl": ["wget"],
                "wget": ["curl"],
                "grep": ["rg", "ack", "ag"],
                "ls": ["exa", "lsd"],
                "cat": ["bat", "less"],
                "ps": ["htop", "top"],
                "ssh": ["mosh", "autossh"],
                "docker": ["podman", "nerdctl"],
                "docker-compose": ["podman-compose"],
            },
        }
        cmd_alt = alt_map.get(category, {}).get(command_base, [])
        alt.extend(cmd_alt)
        return alt

    def _record_analysis(self, result: ErrorAnalysisResult) -> None:
        if self._db is None:
            return
        try:
            self._db.execute(
                """INSERT INTO error_analysis (command, error_message, exit_code, category, severity)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    result.command,
                    result.error_message[:500],
                    result.exit_code,
                    result.category,
                    result.severity,
                ),
            )
            self._db.commit()
        except Exception as e:
            logger.debug("Failed to record error analysis: %s", e)

    def get_recent_error(self) -> str | None:
        return self._get_error_from_history("")


def get_exit_code() -> int:
    try:
        r = subprocess.run(
            ["bash", "-c", "echo $?"], capture_output=True, text=True, timeout=5
        )
        if r.returncode == 0:
            return int(r.stdout.strip())
    except Exception:
        pass
    return -1


def get_last_command() -> str:
    try:
        if os.path.isfile(os.path.expanduser("~/.bash_history")):
            with open(os.path.expanduser("~/.bash_history")) as f:
                lines = f.readlines()
            if lines:
                return lines[-1].strip()
        if os.environ.get("HISTFILE"):
            hf = os.environ["HISTFILE"]
            if os.path.isfile(hf):
                with open(hf, errors="ignore") as f:
                    lines = f.readlines()
                if lines:
                    last = lines[-1].strip()
                    if ";" in last:
                        last = last.split(";")[-1].strip()
                    if ":" in last and len(last) > 10:
                        last = last.split(":", 2)[-1].strip() if ":" in last else last
                    return last
        return ""
    except Exception:
        return ""
