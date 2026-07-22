from __future__ import annotations

from rich.console import Console
from rich.table import Table

from shellsense.database.manager import DatabaseManager
from shellsense.knowledge.engine import KnowledgeEngine
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)
console = Console()


def suggest_callback(
    query: str,
    limit: int = 10,
    predict: bool = False,
) -> None:
    db = DatabaseManager()
    engine = KnowledgeEngine(db)

    if predict or " " in query:
        results = engine.suggest(query, limit=limit)
    else:
        results = engine.suggest(query, limit=limit)
    if not results:
        console.print(f"[yellow]No suggestions for[/] [bold]'{query}'[/]")
        console.print("[dim]Try a different query or check spelling[/]")
        db.close()
        return

    table = Table(
        title=f"Suggestions: '{query}'",
        highlight=True,
    )
    table.add_column("Suggestion", style="cyan", no_wrap=True)
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
    console.print(f"\n[dim]{len(results)} suggestion(s)[/]")
    db.close()
