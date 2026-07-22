from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from shellsense.database.manager import DatabaseManager
from shellsense.knowledge.engine import KnowledgeEngine
from shellsense.knowledge.fuzzy import spell_correct

console = Console()


def related_callback(command_name: str) -> None:
    db = DatabaseManager()
    engine = KnowledgeEngine(db)

    related = engine.related(command_name)

    if related is None:
        corrections = spell_correct(command_name)
        if corrections:
            suggestion = corrections[0][0]
            console.print(f"[yellow]Command not found:[/] [bold]'{command_name}'[/]")
            console.print(
                f"[green]Did you mean[/] [bold cyan]{suggestion}[/][green]?[/]"
            )
            related = engine.related(suggestion)

    if related is None or len(related) == 0:
        console.print(
            f"[red]No related commands found for[/] [bold]'{command_name}'[/]"
        )
        db.close()
        raise typer.Exit(code=1)

    console.print(Panel(f"[bold cyan]Commands related to:[/] [bold]{command_name}[/]"))

    table = Table(highlight=True)
    table.add_column("Command", style="cyan", no_wrap=True)
    table.add_column("Relationship", style="green")
    table.add_column("Description")

    for rel in related:
        table.add_row(
            str(rel.get("name", "")),
            str(rel.get("relationship", "")),
            str(rel.get("description", "")),
        )

    console.print(table)
    db.close()
