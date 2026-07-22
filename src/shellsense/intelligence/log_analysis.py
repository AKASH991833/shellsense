from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass, field
from typing import Any

from shellsense.utils.logging import get_logger

logger = get_logger(__name__)

LOG_PATTERNS: dict[str, list[dict[str, Any]]] = {
    "systemd": [
        {
            "pattern": r"Failed to start",
            "severity": "high",
            "label": "Service failed to start",
        },
        {"pattern": r"error:", "severity": "high", "label": "Error detected"},
        {"pattern": r"warning:", "severity": "medium", "label": "Warning detected"},
        {"pattern": r"out of memory", "severity": "critical", "label": "Out of memory"},
        {"pattern": r"disk.*full", "severity": "critical", "label": "Disk full"},
        {"pattern": r"segfault", "severity": "critical", "label": "Segmentation fault"},
        {"pattern": r"timeout", "severity": "high", "label": "Timeout occurred"},
        {
            "pattern": r"authentication failure",
            "severity": "high",
            "label": "Auth failure",
        },
        {
            "pattern": r"permission denied",
            "severity": "medium",
            "label": "Permission denied",
        },
        {
            "pattern": r"connection refused",
            "severity": "high",
            "label": "Connection refused",
        },
        {
            "pattern": r"failed to connect",
            "severity": "high",
            "label": "Connection failed",
        },
    ],
    "nginx": [
        {"pattern": r"error:", "severity": "high", "label": "Nginx error"},
        {"pattern": r"failed", "severity": "high", "label": "Nginx failure"},
        {"pattern": r"conflict", "severity": "medium", "label": "Port/name conflict"},
    ],
    "ssh": [
        {
            "pattern": r"authentication failed",
            "severity": "high",
            "label": "SSH auth failed",
        },
        {
            "pattern": r"connection closed",
            "severity": "high",
            "label": "Connection closed",
        },
        {
            "pattern": r"permission denied",
            "severity": "high",
            "label": "SSH permission denied",
        },
        {
            "pattern": r"no matching host key",
            "severity": "high",
            "label": "Host key mismatch",
        },
    ],
    "docker": [
        {"pattern": r"error:", "severity": "high", "label": "Docker error"},
        {
            "pattern": r"cannot connect",
            "severity": "high",
            "label": "Docker daemon unreachable",
        },
        {"pattern": r"denied", "severity": "high", "label": "Access denied"},
    ],
}


@dataclass
class LogAnalysisResult:
    source: str = ""
    content_lines: list[str] = field(default_factory=list)
    suspicious_entries: list[dict[str, Any]] = field(default_factory=list)
    severity_counts: dict[str, int] = field(
        default_factory=lambda: {"critical": 0, "high": 0, "medium": 0, "low": 0}
    )
    summary: str = ""
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "total_lines": len(self.content_lines),
            "suspicious_count": len(self.suspicious_entries),
            "severity_counts": self.severity_counts,
            "summary": self.summary,
            "recommendations": self.recommendations,
            "suspicious_entries": [
                {
                    "line": e.get("line", 0),
                    "content": e.get("content", ""),
                    "severity": e.get("severity", ""),
                    "label": e.get("label", ""),
                }
                for e in self.suspicious_entries
            ],
        }


class LogAnalyzer:
    def __init__(self) -> None:
        self._log_sources: dict[str, str] = {
            "syslog": "/var/log/syslog",
            "auth": "/var/log/auth.log",
            "kernel": "/var/log/kern.log",
            "dmesg": "/var/log/dmesg",
            "boot": "/var/log/boot.log",
        }

    def analyze_systemd_journal(
        self, units: list[str] | None = None, lines: int = 100
    ) -> LogAnalysisResult:
        result = LogAnalysisResult(source="systemd-journal")
        cmd = ["journalctl", "--no-pager", "-n", str(lines)]
        if units:
            for unit in units:
                cmd.extend(["-u", unit])
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if r.returncode == 0:
                result.content_lines = r.stdout.strip().split("\n")
                self._analyze_content(result, "systemd")
        except Exception as e:
            result.summary = f"Failed to read journald: {e}"
        return result

    def analyze_log_file(
        self, path: str, log_type: str = "systemd", max_lines: int = 1000
    ) -> LogAnalysisResult:
        result = LogAnalysisResult(source=path)
        if not os.path.isfile(path):
            try:
                r = subprocess.run(
                    ["sudo", "test", "-f", path],
                    capture_output=True,
                    timeout=10,
                )
                if r.returncode != 0:
                    result.summary = f"Log file not found: {path}"
                    return result
            except Exception:
                result.summary = f"Log file not accessible: {path}"
                return result
        try:
            with open(path, errors="ignore") as f:
                lines = f.readlines()
            result.content_lines = [l.strip() for l in lines if l.strip()][-max_lines:]
            self._analyze_content(result, log_type)
        except Exception as e:
            result.summary = f"Failed to read log: {e}"
        return result

    def analyze_dmesg(self, lines: int = 100) -> LogAnalysisResult:
        result = LogAnalysisResult(source="dmesg")
        try:
            r = subprocess.run(
                ["dmesg", "--level=err,warn"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if r.returncode == 0:
                result.content_lines = r.stdout.strip().split("\n")[-lines:]
                for line in result.content_lines:
                    if (
                        "error" in line.lower()
                        or "fail" in line.lower()
                        or "oom" in line.lower()
                    ):
                        result.suspicious_entries.append(
                            {
                                "line": 0,
                                "content": line,
                                "severity": "high",
                                "label": "Kernel issue",
                            }
                        )
                        result.severity_counts["high"] += 1
                result.summary = f"Found {len(result.suspicious_entries)} kernel issues"
        except Exception as e:
            result.summary = f"Failed to read dmesg: {e}"
        return result

    def _analyze_content(self, result: LogAnalysisResult, log_type: str) -> None:
        patterns = LOG_PATTERNS.get(log_type, LOG_PATTERNS["systemd"])
        for i, line in enumerate(result.content_lines):
            line_lower = line.lower()
            for pattern in patterns:
                if re.search(pattern["pattern"], line_lower):
                    result.suspicious_entries.append(
                        {
                            "line": i + 1,
                            "content": line[:300],
                            "severity": pattern["severity"],
                            "label": pattern["label"],
                        }
                    )
                    result.severity_counts[pattern["severity"]] = (
                        result.severity_counts.get(pattern["severity"], 0) + 1
                    )
                    break

        total = len(result.suspicious_entries)
        critical = result.severity_counts.get("critical", 0)
        high = result.severity_counts.get("high", 0)

        if critical > 0:
            result.summary = f"Found {total} issues ({critical} critical, {high} high) - immediate attention required"
        elif high > 0:
            result.summary = (
                f"Found {total} issues ({high} high severity) - review recommended"
            )
        elif total > 0:
            result.summary = f"Found {total} minor issues"
        else:
            result.summary = "No significant issues detected"

        if critical > 0:
            result.recommendations.append("Address critical issues immediately")
        if high > 0:
            result.recommendations.append("Review and address high-severity items")
        if "disk" in result.summary.lower() or "memory" in result.summary.lower():
            result.recommendations.append("Check system resources (disk, memory)")
        if "fail" in result.summary.lower():
            result.recommendations.append(
                "Check service status with `systemctl --failed`"
            )


def analyze_journald(
    units: list[str] | None = None, lines: int = 100
) -> LogAnalysisResult:
    analyzer = LogAnalyzer()
    return analyzer.analyze_systemd_journal(units, lines)


def analyze_log_file(path: str, log_type: str = "systemd") -> LogAnalysisResult:
    analyzer = LogAnalyzer()
    return analyzer.analyze_log_file(path, log_type, max_lines=1000)
