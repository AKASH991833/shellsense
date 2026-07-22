from __future__ import annotations

from rich.console import Console
from rich.markdown import Markdown

from shellsense.cli.commands.shared import get_engine
from shellsense.intelligence.formatter import ResponseFormatter

console = Console()


def ask_callback(
    question: str,
    system_style: str = "context",
    provider: str | None = None,
    show_context: bool = False,
) -> None:
    engine = get_engine()
    formatter = ResponseFormatter()

    context = engine.collect_terminal_context()

    if show_context:
        filtered = engine.privacy.filter_context(context.to_dict())
        formatter.print_context_summary(filtered)

    formatter.print_info("Thinking...")

    try:
        result = engine.ask_ai(question, system_style, provider)
        console.print(Markdown(result))
    except Exception as e:
        formatter.print_error(f"Failed to process question: {e}")
