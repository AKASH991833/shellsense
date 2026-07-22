from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from shellsense.database.manager import DatabaseManager
from shellsense.knowledge.engine import KnowledgeEngine
from shellsense.knowledge.fuzzy import spell_correct
from shellsense.knowledge.risk import risk_color
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)
console = Console()


def explain_callback(command_name: str) -> None:
    db = DatabaseManager()
    engine = KnowledgeEngine(db)

    cmd = engine.explain(command_name)

    if cmd is None:
        corrections = spell_correct(command_name)
        if corrections:
            suggestion = corrections[0][0]
            console.print(f"[yellow]Command not found:[/] [bold]'{command_name}'[/]")
            console.print(
                f"[green]Did you mean[/] [bold cyan]{suggestion}[/][green]?[/]"
            )
            cmd = engine.explain(suggestion)

    if cmd is None:
        console.print(f"[red]Command not found:[/] [bold]'{command_name}'[/]")
        db.close()
        raise typer.Exit(code=1)

    name = str(cmd.get("name", ""))
    short_desc = str(cmd.get("short_description", ""))
    long_desc = str(cmd.get("long_description", ""))
    syntax = str(cmd.get("syntax", ""))
    category = str(cmd.get("category", ""))
    difficulty = str(cmd.get("difficulty", ""))
    risk = str(cmd.get("risk_level", "SAFE"))
    docs = str(cmd.get("official_docs", ""))
    warnings_text = str(cmd.get("warnings", ""))
    notes = str(cmd.get("notes", ""))
    aliases = cmd.get("aliases", [])
    if not isinstance(aliases, list):
        aliases = []

    console.print(
        Panel(
            f"[bold cyan]{name}[/] — [italic]{short_desc}[/]",
            title="[bold]Command Explanation[/]",
        )
    )

    console.print(f"\n[bold]Description:[/] {long_desc}")
    console.print(f"[bold]Syntax:[/] [green]{syntax}[/]")
    console.print(
        f"[bold]Category:[/] {category}  "
        f"[bold]Difficulty:[/] [magenta]{difficulty}[/]  "
        f"[bold]Risk:[/] [{risk_color(risk)}]{risk}[/]"
    )
    if aliases:
        console.print(f"[bold]Aliases:[/] {', '.join(str(a) for a in aliases)}")

    options = cmd.get("options", [])
    if options and isinstance(options, list):
        opt_table = Table(title="Options", highlight=True, box=None)
        opt_table.add_column("Flag", style="cyan", no_wrap=True)
        opt_table.add_column("Description")
        for opt in options:
            opt_table.add_row(str(opt.get("flag", "")), str(opt.get("description", "")))
        console.print("\n")
        console.print(opt_table)

    examples = cmd.get("examples", [])
    if examples and isinstance(examples, list):
        console.print("\n[bold]Examples:[/]")
        for ex in examples[:3]:
            title = ex.get("title", "")
            ex_cmd = ex.get("command", "")
            ex_desc = ex.get("description", "")
            console.print(f"  [bold]{title}[/]")
            console.print(f"  [green]$ {ex_cmd}[/]")
            if ex_desc:
                console.print(f"  [dim]{ex_desc}[/]")
            console.print("")

    errors = cmd.get("common_errors", [])
    if errors and isinstance(errors, list):
        console.print("[bold]Common Errors:[/]")
        for err in errors[:2]:
            console.print(f"  • [yellow]{err.get('error_pattern', '')}[/]")
            console.print(f"    [dim]{err.get('solution', '')}[/]")

    if warnings_text:
        console.print(f"\n[bold red]WARNING:[/] {warnings_text}")

    if notes:
        console.print(f"\n[bold]Notes:[/] [dim]{notes}[/]")

    related = cmd.get("related_commands", [])
    if related and isinstance(related, list):
        rel_list = ", ".join(f"[cyan]{r.get('name', '')}[/]" for r in related[:5])
        console.print(f"\n[bold]Related:[/] {rel_list}")

    if docs:
        console.print(f"\n[bold]Docs:[/] [blue underline]{docs}[/]")

    db.close()
