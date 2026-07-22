from __future__ import annotations

from rich.console import Console
from rich.markdown import Markdown

from shellsense.cli.commands.shared import get_engine
from shellsense.intelligence.error_analysis import get_last_command
from shellsense.intelligence.formatter import ResponseFormatter

console = Console()


def fix_callback(
    command: str | None = None,
    error_message: str | None = None,
    use_ai: bool = False,
    provider: str | None = None,
) -> None:
    engine = get_engine()
    formatter = ResponseFormatter()

    if not command:
        command = get_last_command()
        if not command:
            formatter.print_warning(
                "No command provided and could not detect last command."
            )
            return

    if not error_message:
        error_message = engine.get_recent_error() or ""

    result = engine.analyze_error(
        command, error_message, use_ai=use_ai, provider=provider
    )

    if isinstance(result, str):
        console.print(Markdown(result))
    else:
        formatter.print_error_analysis(result.to_dict())

        if result.known_error:
            formatter.print_info(f"\nCategory: {result.category}")
            formatter.print_info(f"Severity: {result.severity}")
