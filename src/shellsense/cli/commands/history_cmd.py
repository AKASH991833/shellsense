from __future__ import annotations

from rich.console import Console
from rich.table import Table

from shellsense.database.manager import DatabaseManager
from shellsense.knowledge.engine import KnowledgeEngine
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)
console = Console()


def history_callback(limit: int = 20) -> None:
    db = DatabaseManager()
    engine = KnowledgeEngine(db)

    summary = engine.get_history_summary()
    console.print("[bold]History Summary[/]")
    console.print(f"  Searches:     {summary.get('searches', 0)}")
    console.print(f"  Suggestions:  {summary.get('suggestions', 0)}")
    console.print(f"  Explanations: {summary.get('explanations', 0)}")
    console.print(f"  Learning:     {summary.get('learning_entries', 0)}")
    console.print()

    history = engine.get_history(limit=limit)
    if not history:
        console.print("[yellow]No search history yet[/]")
        db.close()
        return

    table = Table(
        title=f"Recent Search History (last {len(history)})",
        highlight=True,
    )
    table.add_column("Query", style="cyan", no_wrap=True)
    table.add_column("Results", style="blue")
    table.add_column("Timestamp", style="dim")

    for h in history:
        table.add_row(
            str(h.get("query", "")),
            str(h.get("result_count", "")),
            str(h.get("timestamp", "")),
        )

    console.print(table)
    db.close()


def clear_history_callback() -> None:
    db = DatabaseManager()
    engine = KnowledgeEngine(db)
    engine.clear_history()
    console.print("[green]All history cleared successfully[/]")
    db.close()
