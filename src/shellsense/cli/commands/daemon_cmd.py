from __future__ import annotations

import os
import signal
import sys
import time
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from shellsense.daemon.client import DaemonClient
from shellsense.daemon.server import PID_PATH, SOCKET_PATH, get_daemon_pid, is_running
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)
console = Console()


def daemon_start_callback(
    foreground: bool = typer.Option(
        False, "--foreground", "-f", help="Run in foreground"
    ),
) -> None:
    """Start the ShellSense daemon."""
    if is_running():
        pid = get_daemon_pid()
        console.print(f"[yellow]Daemon already running (PID: {pid})[/]")
        raise typer.Exit(code=1)

    if foreground:
        from shellsense.daemon.server import DaemonServer

        server = DaemonServer(SOCKET_PATH)
        console.print("[green]Daemon starting in foreground...[/]")
        try:
            server.start()
        except KeyboardInterrupt:
            server.stop()
            console.print("[yellow]Daemon stopped[/]")
        return

    pid = os.fork()
    if pid > 0:
        console.print(f"[green]Daemon started (PID: {pid})[/]")
        time.sleep(0.5)
        if is_running():
            client = DaemonClient()
            stats = client.stats()
            if stats.get("status") == "ok":
                counts = stats.get("counts", {})
                console.print(
                    f"  Commands: {counts.get('total', '?')} "
                    f"(seeded: {counts.get('seeded', '?')}, "
                    f"discovered: {counts.get('discovered', '?')})"
                )
        return
    elif pid == 0:
        sys.stdin.close()
        sys.stdout.close()
        sys.stderr.close()
        from shellsense.daemon.server import DaemonServer

        server = DaemonServer(SOCKET_PATH)
        server.start()
        os._exit(0)
    else:
        console.print("[red]Failed to fork daemon process[/]")
        raise typer.Exit(code=1)


def daemon_stop_callback() -> None:
    """Stop the ShellSense daemon."""
    if not is_running():
        console.print("[yellow]Daemon is not running[/]")
        return

    client = DaemonClient()
    resp = client.shutdown()
    if resp.get("status") == "shutting_down":
        time.sleep(1)
        if os.path.exists(PID_PATH):
            os.unlink(PID_PATH)
        if os.path.exists(SOCKET_PATH):
            os.unlink(SOCKET_PATH)
        console.print("[green]Daemon stopped[/]")
    else:
        pid = get_daemon_pid()
        if pid:
            try:
                os.kill(pid, signal.SIGTERM)
                time.sleep(1)
                if os.path.exists(PID_PATH):
                    os.unlink(PID_PATH)
                if os.path.exists(SOCKET_PATH):
                    os.unlink(SOCKET_PATH)
                console.print("[green]Daemon killed[/]")
            except ProcessLookupError:
                console.print("[yellow]Daemon process not found[/]")


def daemon_status_callback() -> None:
    """Show daemon status."""
    if not is_running():
        console.print("[yellow]Daemon is not running[/]")
        console.print("Run [bold cyan]ss daemon start[/] to start it")
        return

    client = DaemonClient()
    status = client.status()
    stats = client.stats()

    table = Table(title="Daemon Status", highlight=True)
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Status", "Running")
    if status.get("pid"):
        table.add_row("PID", str(status["pid"]))
    if status.get("uptime"):
        uptime = int(status["uptime"])
        mins, secs = divmod(uptime, 60)
        table.add_row("Uptime", f"{mins}m {secs}s")
    table.add_row("Socket", str(status.get("socket", SOCKET_PATH)))

    if stats.get("status") == "ok":
        counts = stats.get("counts", {})
        table.add_row("Total Commands", str(counts.get("total", 0)))
        table.add_row("Seeded", str(counts.get("seeded", 0)))
        table.add_row("Discovered", str(counts.get("discovered", 0)))

    console.print(table)


def daemon_restart_callback() -> None:
    """Restart the ShellSense daemon."""
    daemon_stop_callback()
    time.sleep(1)
    daemon_start_callback()


def daemon_suggest_callback(
    partial: str = typer.Argument(..., help="Partial command to get suggestion for"),
) -> None:
    """Get auto-suggestion for a partial command."""
    client = DaemonClient()
    resp = client.suggest(partial)
    if resp.get("status") != "ok":
        console.print(f"[red]Error: {resp.get('message', 'Unknown error')}[/]")
        return

    prediction = resp.get("prediction", "")
    if prediction:
        console.print(f"[bold green]Suggestion:[/] {prediction}")
    else:
        console.print("[yellow]No suggestion available[/]")

    suggestions = resp.get("suggestions", [])
    if len(suggestions) > 1:
        table = Table(highlight=True)
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Category", style="yellow")
        for s in suggestions[:5]:
            table.add_row(
                str(s.get("name", "")),
                str(s.get("description", ""))[:50],
                str(s.get("category", "")),
            )
        console.print(table)
