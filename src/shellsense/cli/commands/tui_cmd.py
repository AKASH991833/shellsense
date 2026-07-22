from __future__ import annotations

import sys

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.live import Live

from shellsense.database.manager import DatabaseManager
from shellsense.knowledge.engine import KnowledgeEngine
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)
console = Console()


def tui_callback() -> None:
    db = DatabaseManager()
    engine = KnowledgeEngine(db)
    engine.seed()

    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="footer", size=3),
    )
    layout["body"].split_row(
        Layout(name="categories", ratio=1),
        Layout(name="commands", ratio=2),
        Layout(name="details", ratio=2),
    )

    cat_dicts = engine.list_categories()
    categories: list[str] = [str(c.get("name", "")) for c in cat_dicts if c.get("name")]
    selected_cat: str = categories[0] if categories else ""
    commands: list[dict[str, object]] = engine.search("", limit=10)
    selected_cmd: dict[str, object] = commands[0] if commands else {}

    def _render() -> Layout:
        cat_table = Table(title="Categories", box=None, highlight=True)
        cat_table.add_column("Category", style="cyan")
        for c in categories:
            marker = ">" if c == selected_cat else " "
            cat_table.add_row(f"{marker} {c}")

        cmd_table = Table(title="Commands", box=None, highlight=True)
        cmd_table.add_column("Name", style="green")
        cmd_table.add_column("Description", style="white")
        for c in commands[:10]:  # type: ignore[assignment]
            name = str(c.get("name", ""))  # type: ignore[attr-defined]
            desc = str(c.get("short_description", ""))[:40]  # type: ignore[attr-defined]
            marker = ">" if name == selected_cmd.get("name") else " "
            cmd_table.add_row(f"{marker} {name}", desc)

        detail_text = Text()
        if selected_cmd:
            detail_text.append(
                f"Name: {selected_cmd.get('name', '')}\n", style="bold green"
            )
            detail_text.append(
                f"Category: {selected_cmd.get('category', '')}\n", style="cyan"
            )
            detail_text.append(
                f"Description: {selected_cmd.get('short_description', '')}\n",
                style="white",
            )
            detail_text.append(
                f"Syntax: {selected_cmd.get('syntax', selected_cmd.get('long_description', ''))}\n",
                style="yellow",
            )
            risk = str(selected_cmd.get("risk_level", ""))
            detail_text.append(
                f"Risk: {risk}\n",
                style="red" if risk in ("DANGEROUS", "VERY_DANGEROUS") else "green",
            )
            detail_text.append(
                f"Difficulty: {selected_cmd.get('difficulty', '')}", style="magenta"
            )

        layout["header"].update(
            Panel("ShellSense AI - Terminal Browser", style="bold cyan")
        )
        layout["categories"].update(Panel(cat_table, title="Categories"))
        layout["commands"].update(Panel(cmd_table, title="Commands"))
        layout["details"].update(Panel(detail_text, title="Details"))
        layout["footer"].update(
            Panel("Arrow keys: navigate | Enter: select | q: quit", style="dim")
        )
        return layout

    try:
        with Live(_render(), refresh_per_second=10, screen=True) as live:
            import tty
            import termios
            import fcntl
            import os

            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            old_flags = fcntl.fcntl(fd, fcntl.F_GETFL)
            try:
                tty.setraw(fd)
                fcntl.fcntl(fd, fcntl.F_SETFL, old_flags | os.O_NONBLOCK)

                cat_idx = 0
                cmd_idx = 0
                pane = "categories"

                while True:
                    live.update(_render())
                    try:
                        ch = sys.stdin.read(1)
                    except (BlockingIOError, OSError):
                        ch = ""

                    if not ch:
                        import time

                        time.sleep(0.05)
                        continue

                    if ch == "q":
                        break
                    elif ch == "\t":
                        pane = "commands" if pane == "categories" else "categories"
                    elif ch == "\x1b":
                        seq = sys.stdin.read(2) if sys.stdin.read(0) is not None else ""
                        if seq == "[A":
                            if pane == "categories" and cat_idx > 0:
                                cat_idx -= 1
                                selected_cat = (
                                    categories[cat_idx]
                                    if cat_idx < len(categories)
                                    else ""
                                )
                            elif pane == "commands" and cmd_idx > 0:
                                cmd_idx -= 1
                                selected_cmd = (
                                    commands[cmd_idx] if cmd_idx < len(commands) else {}
                                )
                        elif seq == "[B":
                            if pane == "categories" and cat_idx < len(categories) - 1:
                                cat_idx += 1
                                selected_cat = categories[cat_idx]
                            elif pane == "commands" and cmd_idx < len(commands) - 1:
                                cmd_idx += 1
                                selected_cmd = commands[cmd_idx]
                        elif seq == "[C":
                            pane = "commands"
                        elif seq == "[D":
                            pane = "categories"
                        elif seq == "[H":
                            pane = "categories"
                            cat_idx = 0
                            cmd_idx = 0
                    elif ch == "\r":
                        if pane == "commands" and selected_cmd:
                            console.print(
                                f"\n[bold green]shellsense explain {selected_cmd.get('name', '')}[/]"
                            )
                            console.print(
                                f"[yellow]{selected_cmd.get('short_description', '')}[/]"
                            )
                            break
                        elif pane == "categories" and selected_cat:
                            commands = engine.search("", limit=10)
                            commands = [
                                c for c in commands if c.get("category") == selected_cat
                            ]
                            if not commands:
                                commands = engine.search(selected_cat, limit=10)
                            pane = "commands"
                            cmd_idx = 0
                            selected_cmd = commands[0] if commands else {}
                    elif ch == "/":
                        pane = "commands"
                        cmd_idx = 0
                        search_buf = ""
                        console.print("\nSearch: ", end="")
                        while True:
                            sc = sys.stdin.read(1)
                            if sc == "\r" or sc == "\n":
                                break
                            if sc == "\x7f":
                                search_buf = search_buf[:-1]
                            else:
                                search_buf += sc
                        if search_buf:
                            commands = engine.search(search_buf, limit=10)
                            selected_cmd = commands[0] if commands else {}
                            cmd_idx = 0
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                fcntl.fcntl(fd, fcntl.F_SETFL, old_flags)
    except KeyboardInterrupt:
        pass
    except ImportError:
        console.print("[yellow]TUI mode requires a terminal with termios support[/]")
    finally:
        db.close()
