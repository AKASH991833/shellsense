from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from shellsense.utils.logging import get_logger
from shellsense.utils.paths import (
    get_backup_dir,
    get_config_path,
    get_db_path,
    get_log_path,
    get_plugins_dir,
)

logger = get_logger(__name__)
console = Console()

BACKUP_ITEMS = ["config", "database", "plugins", "logs"]


def _get_backup_metadata(backup_path: Path) -> dict[str, Any]:
    meta_file = backup_path / "backup.json"
    if meta_file.exists():
        data: dict[str, Any] = json.loads(meta_file.read_text())
        return data
    return {}


def _ensure_backup_dir() -> Path:
    path = get_backup_dir()
    path.mkdir(parents=True, exist_ok=True)
    return path


def create_backup_callback(
    name: str | None = typer.Option(None, "--name", "-n", help="Backup name"),
    items: list[str] | None = typer.Option(
        None, "--item", "-i", help="Items to backup (config, database, plugins, logs)"
    ),
) -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = name or f"backup_{timestamp}"
    backup_path = _ensure_backup_dir() / backup_name
    backup_path.mkdir(parents=True, exist_ok=True)

    selected = items or BACKUP_ITEMS
    metadata: dict[str, Any] = {
        "name": backup_name,
        "created_at": datetime.now().isoformat(),
        "version": "1.0.0",
        "items": {},
    }

    for item in selected:
        item = item.lower()
        if item == "config":
            src = get_config_path()
            if src.exists():
                dst = backup_path / "config.json"
                shutil.copy2(str(src), str(dst))
                metadata["items"]["config"] = "config.json"
            else:
                console.print("[yellow]Config file not found, skipping[/]")
        elif item == "database":
            src = get_db_path()
            if src.exists():
                dst = backup_path / "shellsense.db"
                shutil.copy2(str(src), str(dst))
                metadata["items"]["database"] = "shellsense.db"
            else:
                console.print("[yellow]Database not found, skipping[/]")
        elif item == "plugins":
            src = get_plugins_dir()
            if src.exists():
                dst = backup_path / "plugins"
                shutil.copytree(str(src), str(dst), dirs_exist_ok=True)
                metadata["items"]["plugins"] = "plugins"
            else:
                console.print("[yellow]Plugins directory not found, skipping[/]")
        elif item == "logs":
            src = get_log_path()
            if src.exists():
                dst = backup_path / "shellsense.log"
                shutil.copy2(str(src), str(dst))
                metadata["items"]["logs"] = "shellsense.log"
            else:
                console.print("[yellow]Log file not found, skipping[/]")

    (backup_path / "backup.json").write_text(json.dumps(metadata, indent=2))
    console.print(
        Panel(
            f"[green]Backup created successfully[/]\n[cyan]Path:[/] {backup_path}",
            title="[bold green]Backup Complete[/]",
        )
    )


def restore_backup_callback(
    name: str = typer.Argument(..., help="Backup name to restore from"),
    items: list[str] | None = typer.Option(
        None, "--item", "-i", help="Items to restore (config, database, plugins, logs)"
    ),
) -> None:
    backup_path = get_backup_dir() / name
    if not backup_path.exists():
        console.print(f"[red]No backup found: {backup_path}[/]")
        raise typer.Exit(code=1)

    selected = items or BACKUP_ITEMS
    for item in selected:
        item = item.lower()
        if item == "config":
            src = backup_path / "config.json"
            if src.exists():
                shutil.copy2(str(src), str(get_config_path()))
                console.print("[green]Config restored[/]")
            else:
                console.print("[yellow]No config in backup, skipping[/]")
        elif item == "database":
            src = backup_path / "shellsense.db"
            if src.exists():
                shutil.copy2(str(src), str(get_db_path()))
                console.print("[green]Database restored[/]")
            else:
                console.print("[yellow]No database in backup, skipping[/]")
        elif item == "plugins":
            src = backup_path / "plugins"
            if src.exists():
                dst = get_plugins_dir()
                if dst.exists():
                    shutil.rmtree(str(dst))
                shutil.copytree(str(src), str(dst), dirs_exist_ok=True)
                console.print("[green]Plugins restored[/]")
            else:
                console.print("[yellow]No plugins in backup, skipping[/]")
        elif item == "logs":
            src = backup_path / "shellsense.log"
            if src.exists():
                shutil.copy2(str(src), str(get_log_path()))
                console.print("[green]Log file restored[/]")
            else:
                console.print("[yellow]No log file in backup, skipping[/]")

    console.print("[bold green]Restore complete[/]")


def list_backups_callback() -> None:
    backup_dir = get_backup_dir()
    if not backup_dir.exists():
        console.print("[yellow]No backups found[/]")
        return

    backups = sorted(
        [
            p
            for p in backup_dir.iterdir()
            if p.is_dir() and (p / "backup.json").exists()
        ],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    if not backups:
        console.print("[yellow]No backups found[/]")
        return

    table = Table(title="Available Backups", highlight=True)
    table.add_column("Name", style="cyan")
    table.add_column("Created", style="green")
    table.add_column("Items", style="yellow")
    table.add_column("Size", style="magenta")

    for b in backups:
        meta = _get_backup_metadata(b)
        created = meta.get("created_at", "unknown")[:19]
        items_str = ", ".join(meta.get("items", {}).keys()) or "empty"
        size = sum(f.stat().st_size for f in b.rglob("*") if f.is_file())
        size_str = (
            f"{size / 1024:.1f} KB"
            if size < 1024 * 1024
            else f"{size / (1024 * 1024):.1f} MB"
        )
        table.add_row(b.name, created, items_str, size_str)

    console.print(table)
