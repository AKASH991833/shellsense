from __future__ import annotations

from rich.console import Console
from rich.table import Table

from shellsense.database.manager import DatabaseManager
from shellsense.knowledge.engine import KnowledgeEngine
from shellsense.knowledge.fuzzy import spell_correct
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)
console = Console()


def search_callback(
    query: str,
    limit: int = 20,
    fuzzy: bool = True,
) -> None:
    db = DatabaseManager()
    engine = KnowledgeEngine(db)

    results = engine.search(query, limit=limit)

    if not results:
        if fuzzy:
            corrections = spell_correct(query)
            if corrections:
                suggestions = ", ".join(
                    f"[bold cyan]{n}[/]" for n, _ in corrections[:5]
                )
                console.print(f"[yellow]No results for[/] [bold]'{query}'[/]")
                console.print(f"[green]Did you mean:[/] {suggestions}")
            else:
                console.print(
                    f"[yellow]No commands found matching[/] [bold]'{query}'[/]"
                )
        else:
            console.print(f"[yellow]No commands found matching[/] [bold]'{query}'[/]")
        db.close()
        return

    table = Table(
        title=f"Search Results: '{query}'",
        highlight=True,
    )
    table.add_column("Command", style="cyan", no_wrap=True)
    table.add_column("Category", style="blue")
    table.add_column("Difficulty", style="magenta")
    table.add_column("Risk", style="red")
    table.add_column("Description")

    for r in results:
        risk = str(r.get("risk_level", ""))
        risk_styled = (
            f"[bold red]{risk}[/]"
            if risk in ("DANGEROUS", "VERY_DANGEROUS")
            else f"[green]{risk}[/]"
        )
        table.add_row(
            str(r.get("name", "")),
            str(r.get("category", "")),
            str(r.get("difficulty", "")),
            risk_styled,
            str(r.get("short_description", "")),
        )

    console.print(table)
    console.print(f"\n[dim]{len(results)} result(s)[/]")
    db.close()
