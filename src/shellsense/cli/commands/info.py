from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from shellsense import __description__, __title__, __version__
from shellsense.database.manager import DatabaseManager
from shellsense.knowledge.engine import KnowledgeEngine
from shellsense.knowledge.fuzzy import spell_correct
from shellsense.knowledge.risk import risk_color
from shellsense.utils.platform import get_system_info

console = Console()


def info_callback(command_name: str | None = None) -> None:
    if command_name is None:
        _show_system_info()
    else:
        _show_command_info(command_name)


def _show_system_info() -> None:
    info = get_system_info()

    table = Table(title=f"{__title__} v{__version__}", highlight=True)
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Description", __description__)
    table.add_row("System", info.system)
    table.add_row("Distribution", info.distro or "Unknown")
    table.add_row("Kernel", info.kernel or "Unknown")
    table.add_row("Architecture", info.architecture)
    table.add_row("Hostname", info.hostname)
    table.add_row("Python", info.python_version)
    table.add_row("Shell", info.shell or "Unknown")
    table.add_row("Terminal", info.terminal or "Unknown")

    console.print(Panel(table, title="[bold cyan]System Information[/]"))


def _show_command_info(command_name: str) -> None:
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
    table = Table(title=f"Command Info: [bold cyan]{name}[/]", highlight=True)
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Description", str(cmd.get("short_description", "")))
    table.add_row("Category", str(cmd.get("category", "")))
    table.add_row("Difficulty", str(cmd.get("difficulty", "")))
    table.add_row("Availability", str(cmd.get("availability", "")))
    risk = str(cmd.get("risk_level", "SAFE"))
    table.add_row("Risk Level", f"[{risk_color(risk)}]{risk}[/]")
    table.add_row("Syntax", f"[green]{cmd.get('syntax', '')}[/]")

    aliases = cmd.get("aliases", [])
    if aliases and isinstance(aliases, list) and len(aliases) > 0:
        table.add_row("Aliases", ", ".join(str(a) for a in aliases))

    docs = str(cmd.get("official_docs", ""))
    if docs:
        table.add_row("Documentation", f"[blue underline]{docs}[/]")

    examples = cmd.get("examples", [])
    if examples and isinstance(examples, list):
        table.add_row("Examples", str(min(len(examples), 5)))

    console.print(table)

    examples_list = cmd.get("examples", [])
    if examples_list and isinstance(examples_list, list) and len(examples_list) > 0:
        console.print("\n[bold]Examples:[/]")
        for ex in examples_list[:3]:
            console.print(f"  [green]$ {ex.get('command', '')}[/]")
            desc = ex.get("description", "")
            if desc:
                console.print(f"  [dim]{desc}[/]")

    db.close()
