from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from shellsense.ai.providers.base import AIResponse

console = Console()


class ResponseFormatter:
    def __init__(self) -> None:
        self._console = console

    def format_markdown(self, text: str) -> Markdown:
        return Markdown(text)

    def print_markdown(self, text: str) -> None:
        self._console.print(Markdown(text))

    def print_code_block(self, code: str, language: str = "bash") -> None:
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        self._console.print(syntax)

    def print_warning(self, message: str) -> None:
        text = Text(message, style="bold yellow")
        self._console.print(Panel(text, border_style="yellow", title="Warning"))

    def print_error(self, message: str) -> None:
        text = Text(message, style="bold red")
        self._console.print(Panel(text, border_style="red", title="Error"))

    def print_success(self, message: str) -> None:
        text = Text(message, style="bold green")
        self._console.print(Panel(text, border_style="green", title="Success"))

    def print_info(self, message: str) -> None:
        self._console.print(Text(message, style="cyan"))

    def print_table(
        self, title: str, columns: list[str], rows: list[list[str]]
    ) -> None:
        table = Table(title=title)
        for col in columns:
            table.add_column(col, style="cyan")
        for row in rows:
            table.add_row(*row)
        self._console.print(table)

    def print_panel(self, title: str, content: str) -> None:
        self._console.print(Panel(content, title=title))

    def print_ai_response(self, response: AIResponse) -> None:
        if not response.content:
            self.print_error("No response received from AI.")
            return
        self._console.print(Markdown(response.content))

    def print_error_analysis(self, analysis: dict[str, Any]) -> None:
        if "root_cause" in analysis:
            self.print_panel("Root Cause", analysis["root_cause"])
        if "recommended_fix" in analysis:
            self._console.print("\n[bold green]Recommended Fix:[/bold green]")
            if isinstance(analysis["recommended_fix"], list):
                for i, step in enumerate(analysis["recommended_fix"], 1):
                    self._console.print(f"  {i}. {step}")
            else:
                self._console.print(f"  {analysis['recommended_fix']}")
        if "alternative_commands" in analysis:
            alt = analysis["alternative_commands"]
            if isinstance(alt, list) and alt:
                rows = [
                    (
                        [cmd]
                        if isinstance(cmd, str)
                        else [cmd.get("command", ""), cmd.get("reason", "")]
                    )
                    for cmd in alt
                ]
                if rows and len(rows[0]) == 2:
                    self.print_table(
                        "Alternative Commands", ["Command", "Reason"], rows
                    )
                else:
                    self._console.print("\n[bold]Alternative Commands:[/bold]")
                    for cmd in alt:
                        if isinstance(cmd, str):
                            self._console.print(f"  - {cmd}")
        if "warnings" in analysis:
            warnings = analysis["warnings"]
            if isinstance(warnings, list):
                for w in warnings:
                    self.print_warning(w)
            elif isinstance(warnings, str):
                self.print_warning(warnings)

    def print_script_analysis(self, analysis: dict[str, Any]) -> None:
        if "overview" in analysis:
            self.print_panel("Overview", analysis["overview"])
        if "complexity" in analysis:
            self._console.print(f"\n[bold]Complexity:[/bold] {analysis['complexity']}")
        if "bugs" in analysis:
            bugs = analysis["bugs"]
            if isinstance(bugs, list) and bugs:
                rows = [[str(b)] for b in bugs]
                self.print_table("Potential Bugs", ["Issue"], rows)
        if "security" in analysis:
            sec = analysis["security"]
            if isinstance(sec, list) and sec:
                rows = [[str(s)] for s in sec]
                self.print_table("Security Issues", ["Issue"], rows)
        if "improvements" in analysis:
            imp = analysis["improvements"]
            if isinstance(imp, list) and imp:
                self._console.print("\n[bold green]Improvements:[/bold green]")
                for i, item in enumerate(imp, 1):
                    self._console.print(f"  {i}. {item}")

    def print_log_analysis(self, analysis: dict[str, Any]) -> None:
        if "summary" in analysis:
            self.print_panel("Summary", analysis["summary"])
        if "anomalies" in analysis:
            anomalies = analysis["anomalies"]
            if isinstance(anomalies, list) and anomalies:
                rows = [[str(a)] for a in anomalies]
                self.print_table("Anomalies", ["Finding"], rows)
        if "recommendations" in analysis:
            recs = analysis["recommendations"]
            if isinstance(recs, list) and recs:
                self._console.print("\n[bold green]Recommendations:[/bold green]")
                for r in recs:
                    self._console.print(f"  • {r}")

    def print_service_status(self, status: dict[str, Any]) -> None:
        table = Table(title=f"Service: {status.get('name', 'Unknown')}")
        table.add_column("Property", style="cyan")
        table.add_column("Value")
        for key, val in status.items():
            if key != "name":
                table.add_row(key.replace("_", " ").title(), str(val))
        self._console.print(table)

    def print_context_summary(self, context: dict[str, Any]) -> None:
        table = Table(title="Terminal Context")
        table.add_column("Property", style="cyan")
        table.add_column("Value")
        for key, val in context.items():
            if isinstance(val, list):
                val_str = ", ".join(str(v) for v in val[:5])
                if len(val) > 5:
                    val_str += f" ... (+{len(val)-5} more)"
            elif isinstance(val, dict):
                val_str = ", ".join(f"{k}={v}" for k, v in list(val.items())[:5])
                if len(val) > 5:
                    val_str += f" ... (+{len(val)-5} more)"
            else:
                val_str = str(val)
            table.add_row(key.replace("_", " ").title(), val_str)
        self._console.print(table)

    def print_privacy_status(self, settings: dict[str, bool]) -> None:
        table = Table(title="Privacy Settings")
        table.add_column("Setting", style="cyan")
        table.add_column("Status")
        for key, val in sorted(settings.items()):
            status_str = "[green]Allowed[/green]" if val else "[red]Denied[/red]"
            display_key = key.replace("share_", "").replace("_", " ").title()
            table.add_row(display_key, status_str)
        self._console.print(table)
