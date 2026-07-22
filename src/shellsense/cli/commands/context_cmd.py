from __future__ import annotations

from rich.console import Console

from shellsense.cli.commands.shared import get_engine
from shellsense.intelligence.formatter import ResponseFormatter

console = Console()


def context_callback() -> None:
    engine = get_engine()
    formatter = ResponseFormatter()

    context = engine.collect_terminal_context()
    filtered = engine.privacy.filter_context(context.to_dict())

    formatter.print_context_summary(filtered)

    engine.privacy.is_allowed("user")
    allowed = engine.privacy.get_allowed_context_summary()
    if allowed:
        formatter.print_info(f"\nAllowed context: {allowed}")
