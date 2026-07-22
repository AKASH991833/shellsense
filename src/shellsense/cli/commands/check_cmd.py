from __future__ import annotations

from rich.console import Console

from shellsense.shell.warnings import check_command_safety
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)
console = Console()


def check_command_callback(command: str) -> None:
    warnings = check_command_safety(command)
    if not warnings:
        return

    for w in warnings:
        level = w.get("level", "UNKNOWN")
        message = w.get("message", "")
        if level in ("DANGEROUS", "VERY_DANGEROUS"):
            console.print(f"[bold red]{level}[/] {message}")
        else:
            console.print(f"[yellow]{level}[/] {message}")
