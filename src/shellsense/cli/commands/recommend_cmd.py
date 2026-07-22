from __future__ import annotations

from rich.console import Console
from rich.table import Table

from shellsense.database.manager import DatabaseManager
from shellsense.knowledge.engine import KnowledgeEngine
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)
console = Console()


def recommend_callback(command: str, limit: int = 10) -> None:
    db = DatabaseManager()
    engine = KnowledgeEngine(db)

    results = engine.recommend(command, limit=limit)

    if not results:
        console.print(f"[yellow]No recommendations found for[/] [bold]'{command}'[/]")
        db.close()
        return

    table = Table(
        title=f"Recommendations for '{command}'",
        highlight=True,
    )
    table.add_column("Command", style="cyan", no_wrap=True)
    table.add_column("Category", style="blue")
    table.add_column("Relationship", style="green")
    table.add_column("Description")

    for r in results:
        relationship = str(r.get("relationship", r.get("similarity_reason", "")))
        table.add_row(
            str(r.get("name", "")),
            str(r.get("category", "")),
            relationship,
            str(r.get("short_description", "")),
        )

    console.print(table)
    console.print(f"\n[dim]{len(results)} recommendation(s)[/]")
    db.close()


def similar_callback(command: str, limit: int = 10) -> None:
    db = DatabaseManager()
    engine = KnowledgeEngine(db)

    results = engine.similar(command, limit=limit)

    if not results:
        console.print(f"[yellow]No similar commands found for[/] [bold]'{command}'[/]")
        db.close()
        return

    table = Table(
        title=f"Similar to '{command}'",
        highlight=True,
    )
    table.add_column("Command", style="cyan", no_wrap=True)
    table.add_column("Category", style="blue")
    table.add_column("Reason", style="green")
    table.add_column("Difficulty", style="magenta")
    table.add_column("Description")

    for r in results:
        reason = str(r.get("similarity_reason", ""))
        table.add_row(
            str(r.get("name", "")),
            str(r.get("category", "")),
            reason,
            str(r.get("difficulty", "")),
            str(r.get("short_description", "")),
        )

    console.print(table)
    console.print(f"\n[dim]{len(results)} similar command(s)[/]")
    db.close()
