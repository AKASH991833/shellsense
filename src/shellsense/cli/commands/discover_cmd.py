from __future__ import annotations

from typing import Any

import typer
from rich.console import Console
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table

from shellsense.database.manager import DatabaseManager
from shellsense.knowledge.discovery import discover_all, scan_system_commands
from shellsense.knowledge.discovery_loader import (
    get_discovered_categories,
    get_discovered_count,
    refresh_discovered,
    seed_discovered,
)
from shellsense.utils.logging import get_logger
from shellsense.utils.paths import ensure_shellsense_dir, get_db_path

logger = get_logger(__name__)
console = Console()


def _get_db() -> DatabaseManager:
    ensure_shellsense_dir()
    db = DatabaseManager(get_db_path())
    db.initialize()
    return db


def discover_callback(
    max_commands: int = typer.Option(
        500, "--max", "-m", help="Maximum commands to discover"
    ),
    refresh: bool = typer.Option(
        False, "--refresh", "-r", help="Refresh existing discovered commands"
    ),
    stats: bool = typer.Option(
        False, "--stats", "-s", help="Show discovery stats only"
    ),
) -> None:
    """Scan system and discover Linux commands with descriptions."""
    db = _get_db()

    if stats:
        _show_stats(db)
        return

    if refresh:
        console.print("[cyan]Refreshing discovered commands...[/]")
        count = refresh_discovered(db)
        console.print(f"[green]Refreshed {count} commands[/]")
        _show_stats(db)
        return

    total_available = len(scan_system_commands())
    console.print(f"[cyan]Found {total_available} commands in system PATH[/]")

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:

        discovered_list: list[Any] = []
        task = progress.add_task("[cyan]Discovering commands...", total=total_available)

        def progress_callback(current: int, total: int, name: str) -> None:
            progress.update(
                task,
                completed=current,
                description=f"[cyan]Scanning: {name} ({current}/{total})[/]",
            )

        discovered_list = discover_all(
            progress_callback=progress_callback, max_commands=max_commands
        )

        progress.update(task, completed=total_available)

    discovered_count = len(discovered_list)
    console.print(
        f"\n[bold green]Discovery complete![/] {discovered_count} commands found"
    )
    console.print("[cyan]Seeding into database...[/]")
    count = seed_discovered(db, max_commands=max_commands)
    console.print(f"[bold green]Added {count} new commands to database[/]")
    _show_stats(db)


def _show_stats(db: DatabaseManager) -> None:
    total = get_discovered_count(db)
    if total == 0:
        console.print(
            "[yellow]No commands discovered yet. Run `ss discover` to start.[/]"
        )
        return
    console.print(f"\n[bold cyan]Discovered Commands:[/] {total}")
    categories = get_discovered_categories(db)
    if categories:
        table = Table(highlight=True)
        table.add_column("Category", style="cyan")
        table.add_column("Count", style="green")
        for cat in categories:
            table.add_row(str(cat["category"]), str(cat["count"]))
        console.print(table)
