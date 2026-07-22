from __future__ import annotations

import re
from typing import Any

DANGEROUS_PATTERNS: list[dict[str, Any]] = [
    {
        "pattern": r"\brm\s+-rf\s+/*\s*$",
        "level": "VERY_DANGEROUS",
        "message": "Recursive force delete from root",
    },
    {
        "pattern": r"\brm\s+-rf\b.*\s+/\s*$",
        "level": "VERY_DANGEROUS",
        "message": "Recursive force delete root directory",
    },
    {
        "pattern": r"\bdd\s+if=.*\s+of=",
        "level": "DANGEROUS",
        "message": "Direct disk write operation",
    },
    {
        "pattern": r"\bmkfs\b",
        "level": "DANGEROUS",
        "message": "Filesystem creation",
    },
    {
        "pattern": r"\bmkswap\b",
        "level": "DANGEROUS",
        "message": "Swap creation",
    },
    {
        "pattern": r"\bshutdown\b",
        "level": "CAUTION",
        "message": "System shutdown",
    },
    {
        "pattern": r"\breboot\b",
        "level": "CAUTION",
        "message": "System reboot",
    },
    {
        "pattern": r"\bpoweroff\b",
        "level": "CAUTION",
        "message": "System power off",
    },
    {
        "pattern": r"\binit\s+0\b",
        "level": "DANGEROUS",
        "message": "System shutdown via init",
    },
    {
        "pattern": r"\binit\s+6\b",
        "level": "DANGEROUS",
        "message": "System reboot via init",
    },
    {
        "pattern": r"\buserdel\s+-rf?\b",
        "level": "DANGEROUS",
        "message": "Force user deletion",
    },
    {
        "pattern": r"\bpasswd\s+-l\b",
        "level": "CAUTION",
        "message": "Lock user account",
    },
    {
        "pattern": r"\bchmod\s+777\b",
        "level": "CAUTION",
        "message": "World-writable permissions",
    },
    {
        "pattern": r"\bchown\s+-R\b",
        "level": "CAUTION",
        "message": "Recursive ownership change",
    },
    {
        "pattern": r"\b>\s+/dev/sd",
        "level": "VERY_DANGEROUS",
        "message": "Direct write to block device",
    },
    {
        "pattern": r"\b:\w*\s*\{\s*:\s*\|\s*:\s*&",
        "level": "DANGEROUS",
        "message": "Fork bomb pattern detected",
    },
    {
        "pattern": r"\bsudo\s+rm\s+-rf\s+/\s*$",
        "level": "VERY_DANGEROUS",
        "message": "Sudo recursive delete root",
    },
    {
        "pattern": r"\bwget\s+.*\|\s*bash\b",
        "level": "DANGEROUS",
        "message": "Piped web script execution",
    },
    {
        "pattern": r"\bcurl\s+.*\|\s*bash\b",
        "level": "DANGEROUS",
        "message": "Piped web script execution",
    },
]


def check_command_safety(command: str) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    for pattern_def in DANGEROUS_PATTERNS:
        if re.search(pattern_def["pattern"], command):
            warnings.append(
                {
                    "command": command,
                    "pattern": pattern_def["pattern"],
                    "level": pattern_def["level"],
                    "message": pattern_def["message"],
                }
            )
    return warnings


def requires_confirmation(warnings: list[dict[str, Any]]) -> bool:
    for w in warnings:
        if w.get("level") in ("DANGEROUS", "VERY_DANGEROUS"):
            return True
    return False


def get_warning_level(warnings: list[dict[str, Any]]) -> str:
    levels = [w.get("level", "SAFE") for w in warnings]
    if "VERY_DANGEROUS" in levels:
        return "VERY_DANGEROUS"
    if "DANGEROUS" in levels:
        return "DANGEROUS"
    if "CAUTION" in levels:
        return "CAUTION"
    return "SAFE"
