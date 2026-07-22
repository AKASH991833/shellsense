from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from shellsense.daemon.server import SOCKET_PATH, is_running
from shellsense.utils.logging import get_logger
from shellsense.utils.paths import ensure_shellsense_dir, get_shellsense_dir

logger = get_logger(__name__)
console = Console()


def init_callback(
    auto_yes: bool = typer.Option(
        False, "--yes", "-y", help="Auto-answer yes to all prompts"
    ),
    discover: bool = typer.Option(
        True, "--discover/--no-discover", help="Run command discovery"
    ),
    max_commands: int = typer.Option(
        200, "--max", "-m", help="Max commands to discover"
    ),
) -> None:
    """One-command setup: daemon, shell integration, discovery, systemd."""

    console.print(
        Panel(
            "[bold cyan]ShellSense AI - Quick Setup Wizard[/]\n"
            "This will set up everything you need:\n"
            "  1. Start background daemon\n"
            "  2. Discover commands from your system\n"
            "  3. Install shell integration (auto-suggestions)\n"
            "  4. Optionally enable systemd auto-start",
        )
    )

    if not auto_yes:
        typer.confirm("Continue with setup?", default=True, abort=True)

    ensure_shellsense_dir()

    _step("Starting daemon...")
    if is_running():
        _ok("Daemon already running")
    else:
        _run_cmd("shellsense daemon start", "Daemon started")

    time.sleep(1)

    if discover:
        _step(f"Discovering commands (max {max_commands})...")
        _run_cmd(f"shellsense discover scan --max {max_commands}", "Discovery complete")

    _step("Installing shell integration...")
    _run_cmd("shellsense install", "Shell hooks installed")

    _step("Systemd service...")
    _setup_systemd(auto_yes)

    console.print(
        Panel(
            "[bold green]ShellSense AI is ready![/]\n"
            "  • Daemon:    [cyan]shellsense daemon status[/]\n"
            "  • Search:    [cyan]shellsense search find large files[/]\n"
            "  • Suggest:   [cyan]shellsense suggest 'git com'[/]\n"
            "  • Doctor:    [cyan]shellsense doctor[/]\n"
            "\n"
            "Also available as: [bold]shs[/] (alias)\n"
            "\n"
            "Restart your terminal or run: [bold]exec bash[/]",
        )
    )


def _step(msg: str) -> None:
    console.print(f"\n[bold cyan]▸[/] {msg}")


def _ok(msg: str) -> None:
    console.print(f"  [green]✓[/] {msg}")


def _run_cmd(cmd: str, success_msg: str) -> bool:
    result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=30)
    if result.returncode == 0:
        _ok(success_msg)
        return True
    console.print(f"  [yellow]⚠ {result.stderr.strip() or 'Failed'}[/]")
    return False


def _setup_systemd(auto_yes: bool) -> None:
    service_name = "shellsense-daemon"
    user_services = Path.home() / ".config" / "systemd" / "user"
    service_path = user_services / f"{service_name}.service"
    bin_path = (
        shutil.which("shellsense")
        or shutil.which("shs")
        or Path.home() / ".local/bin/shellsense"
    )
    service_content = f"""[Unit]
Description=ShellSense AI Daemon
After=network.target

[Service]
Type=simple
ExecStart={bin_path} daemon start --foreground
Restart=on-failure
RestartSec=5
Environment=SS_DAEMON=1

[Install]
WantedBy=default.target
"""
    if service_path.exists():
        _ok("Systemd service already installed")
        return

    if not auto_yes:
        enable = typer.confirm(
            "Enable systemd auto-start? (daemon starts on login)", default=True
        )
    else:
        enable = True

    if not enable:
        _ok("Skipped systemd setup")
        return

    try:
        user_services.mkdir(parents=True, exist_ok=True)
        service_path.write_text(service_content)
        subprocess.run(
            ["systemctl", "--user", "daemon-reload"],
            capture_output=True,
            timeout=10,
        )
        subprocess.run(
            ["systemctl", "--user", "enable", service_name],
            capture_output=True,
            timeout=10,
        )
        subprocess.run(
            ["systemctl", "--user", "start", service_name],
            capture_output=True,
            timeout=10,
        )
        _ok(f"Systemd service enabled ({service_name})")
    except Exception as e:
        console.print(f"  [yellow]⚠ Systemd setup failed: {e}[/]")
