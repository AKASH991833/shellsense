from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from typing import Any

from shellsense.knowledge.engine import KnowledgeEngine
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ServiceResult:
    name: str = ""
    status: str = ""
    active: bool = False
    enabled: bool = False
    pid: int = 0
    memory: str = ""
    cpu: str = ""
    description: str = ""
    knowledge_description: str = ""
    knowledge_warnings: list[str] = field(default_factory=list)
    related_commands: list[str] = field(default_factory=list)
    common_errors: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "active": self.active,
            "enabled": self.enabled,
            "pid": self.pid,
            "memory": self.memory,
            "cpu": self.cpu,
            "description": self.description,
        }


class ServiceIntelligence:
    def __init__(self, knowledge: KnowledgeEngine | None = None) -> None:
        self._knowledge = knowledge

    def get_status(self, service_name: str) -> ServiceResult:
        result = ServiceResult(name=service_name)

        try:
            r = subprocess.run(
                [
                    "systemctl",
                    "show",
                    service_name,
                    "--property=ActiveState,UnitFileState,Description,MainPID,MemoryCurrent,CPUUsageNSec",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if r.returncode == 0:
                for line in r.stdout.strip().split("\n"):
                    if "=" in line:
                        key, val = line.split("=", 1)
                        if key == "ActiveState":
                            result.status = val
                            result.active = val == "active"
                        elif key == "UnitFileState":
                            result.enabled = val == "enabled"
                        elif key == "Description":
                            result.description = val
                        elif key == "MainPID":
                            try:
                                result.pid = int(val)
                            except ValueError:
                                pass
                        elif key == "MemoryCurrent":
                            if val and val != "0":
                                try:
                                    mem_bytes = int(val)
                                    result.memory = f"{mem_bytes / 1024 / 1024:.1f}M"
                                except ValueError:
                                    result.memory = val
                        elif key == "CPUUsageNSec":
                            if val and val != "0":
                                try:
                                    cpu_ns = int(val)
                                    result.cpu = f"{cpu_ns / 1e9:.1f}s"
                                except ValueError:
                                    result.cpu = val
        except FileNotFoundError:
            result.status = "systemctl not available"
        except Exception as e:
            logger.debug("Service check failed: %s", e)
            result.status = f"error: {e}"

        if self._knowledge:
            try:
                cmd_name = service_name
                info: dict[str, object] | None = self._knowledge.explain(cmd_name)
                if info:
                    desc = info.get("short_description", "")
                    result.knowledge_description = str(desc) if desc else ""
                    warnings = info.get("warnings")
                    if warnings:
                        if isinstance(warnings, list):
                            result.knowledge_warnings = [str(w) for w in warnings]
                        else:
                            result.knowledge_warnings = [str(warnings)]
                    related: list[dict[str, object]] | None = self._knowledge.related(
                        cmd_name
                    )
                    if related:
                        result.related_commands = [
                            str(r.get("related_command_name", ""))
                            for r in related
                            if isinstance(r, dict)
                        ]
                    errors = info.get("common_errors")
                    if errors:
                        if isinstance(errors, list):
                            result.common_errors = [
                                {str(k): str(v) for k, v in e.items()}
                                for e in errors
                                if isinstance(e, dict)
                            ]
            except Exception as e:
                logger.debug(
                    "Knowledge lookup failed for service %s: %s", service_name, e
                )

        return result

    def diagnose(self, service_name: str) -> str:
        try:
            r = subprocess.run(
                ["journalctl", "-u", service_name, "--no-pager", "-n", "30"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if r.returncode == 0:
                lines = r.stdout.strip().split("\n")
                error_lines = [
                    l
                    for l in lines
                    if "error" in l.lower()
                    or "fail" in l.lower()
                    or "warning" in l.lower()
                ]
                if error_lines:
                    return "\n".join(error_lines[-15:])
                return "No recent errors found in journal."
            return ""
        except Exception as e:
            return f"Failed to read journal: {e}"


def get_service_status(service_name: str) -> ServiceResult:
    svc = ServiceIntelligence()
    return svc.get_status(service_name)
