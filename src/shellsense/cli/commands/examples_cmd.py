from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel

from shellsense.database.manager import DatabaseManager
from shellsense.knowledge.engine import KnowledgeEngine
from shellsense.knowledge.fuzzy import spell_correct

console = Console()


def examples_callback(command_name: str) -> None:
    db = DatabaseManager()
    engine = KnowledgeEngine(db)

    examples = engine.examples(command_name)

    if examples is None:
        corrections = spell_correct(command_name)
        if corrections:
            suggestion = corrections[0][0]
            console.print(f"[yellow]Command not found:[/] [bold]'{command_name}'[/]")
            console.print(
                f"[green]Did you mean[/] [bold cyan]{suggestion}[/][green]?[/]"
            )
            examples = engine.examples(suggestion)

    if examples is None or len(examples) == 0:
        console.print(f"[red]No examples found for[/] [bold]'{command_name}'[/]")
        db.close()
        raise typer.Exit(code=1)

    console.print(
        Panel(
            f"[bold cyan]Examples for[/] [bold]{command_name}[/]",
        )
    )

    for i, ex in enumerate(examples, 1):
        title = ex.get("title", f"Example {i}")
        command = ex.get("command", "")
        output = ex.get("output", "")
        description = ex.get("description", "")

        console.print(f"\n[bold]{i}. {title}[/]")
        console.print(f"   [green]$ {command}[/]")
        if output:
            console.print(f"   [dim]{output}[/]")
        if description:
            console.print(f"   [italic]{description}[/]")

    db.close()
