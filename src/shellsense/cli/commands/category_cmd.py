from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from shellsense.database.manager import DatabaseManager
from shellsense.knowledge.categories import get_all_category_names
from shellsense.knowledge.engine import KnowledgeEngine

console = Console()


def category_list_callback() -> None:
    db = DatabaseManager()
    engine = KnowledgeEngine(db)

    categories = engine.list_categories()

    table = Table(title="Categories", highlight=True)
    table.add_column("Category", style="cyan", no_wrap=True)
    table.add_column("Commands", style="green")

    for cat in categories:
        table.add_row(str(cat.get("category", "")), str(cat.get("count", 0)))

    console.print(table)
    db.close()


def category_show_callback(category: str) -> None:
    db = DatabaseManager()
    engine = KnowledgeEngine(db)

    commands = engine.commands_in_category(category)

    if not commands:
        valid = get_all_category_names()
        console.print(f"[red]Category not found:[/] [bold]'{category}'[/]")
        console.print(f"[yellow]Valid categories:[/] {', '.join(valid)}")
        db.close()
        raise typer.Exit(code=1)

    console.print(Panel(f"[bold cyan]Commands in category:[/] [bold]{category}[/]"))

    table = Table(highlight=True)
    table.add_column("Command", style="cyan", no_wrap=True)
    table.add_column("Difficulty", style="magenta")
    table.add_column("Risk", style="red")
    table.add_column("Description")

    for cmd in commands:
        risk = str(cmd.get("risk_level", ""))
        risk_styled = (
            f"[bold red]{risk}[/]"
            if risk in ("DANGEROUS", "VERY_DANGEROUS")
            else f"[green]{risk}[/]"
        )
        table.add_row(
            str(cmd.get("name", "")),
            str(cmd.get("difficulty", "")),
            risk_styled,
            str(cmd.get("short_description", "")),
        )

    console.print(table)
    db.close()
