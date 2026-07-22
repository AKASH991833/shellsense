from __future__ import annotations

from rich.console import Console

from shellsense.cli.commands.shared import get_engine
from shellsense.intelligence.formatter import ResponseFormatter

console = Console()


def privacy_show_callback() -> None:
    engine = get_engine()
    formatter = ResponseFormatter()

    settings = engine.privacy.get_summary()
    formatter.print_privacy_status(settings)


def privacy_allow_callback(key: str) -> None:
    engine = get_engine()
    engine.privacy.allow(key)
    console.print(f"[green]Allowed:[/] {key.replace('_', ' ').title()}")


def privacy_deny_callback(key: str) -> None:
    engine = get_engine()
    engine.privacy.deny(key)
    console.print(f"[red]Denied:[/] {key.replace('_', ' ').title()}")


def privacy_toggle_callback(key: str) -> None:
    engine = get_engine()
    result = engine.privacy.toggle(key)
    status = "Allowed" if result else "Denied"
    color = "green" if result else "red"
    console.print(f"[{color}]{status}:[/] {key.replace('_', ' ').title()}")


def privacy_reset_callback() -> None:
    engine = get_engine()
    engine.privacy.reset_to_defaults()
    console.print("[green]Privacy settings reset to defaults.[/]")


PRIVACY_KEYS = [
    "current_directory",
    "shell",
    "operating_system",
    "distribution",
    "kernel_version",
    "user",
    "hostname",
    "system_time",
    "git_repository",
    "git_branch",
    "git_status",
    "history",
    "environment_variables",
    "virtual_env",
    "container_info",
    "package_managers",
    "processes",
    "filesystems",
    "last_error",
    "last_command",
]
