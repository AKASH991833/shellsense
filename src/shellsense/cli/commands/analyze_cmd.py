from __future__ import annotations

from rich.console import Console
from rich.markdown import Markdown

from shellsense.cli.commands.shared import get_engine
from shellsense.intelligence.formatter import ResponseFormatter

console = Console()


def analyze_callback(
    path: str,
    use_ai: bool = False,
    provider: str | None = None,
) -> None:
    engine = get_engine()
    formatter = ResponseFormatter()

    result = engine.analyze_script(path, use_ai=use_ai, provider=provider)

    if isinstance(result, str):
        console.print(Markdown(result))
    else:
        formatter.print_script_analysis(result.to_dict())
        if result.security_issues:
            for issue in result.security_issues:
                formatter.print_warning(f"[{issue['severity']}] {issue['message']}")


def optimize_callback(
    path: str,
    use_ai: bool = False,
    provider: str | None = None,
) -> None:
    engine = get_engine()
    formatter = ResponseFormatter()

    result = engine.optimize_script(path, use_ai=use_ai, provider=provider)

    if isinstance(result, str):
        console.print(Markdown(result))
    else:
        formatter.print_script_analysis(result.to_dict())
        if result.performance_improvements:
            formatter.print_info("\nPerformance Improvements:")
            for imp in result.performance_improvements:
                formatter.print_info(f"  • {imp}")


def explain_script_callback(
    path: str,
    use_ai: bool = False,
    provider: str | None = None,
) -> None:
    engine = get_engine()
    formatter = ResponseFormatter()

    result = engine.explain_script(path, use_ai=use_ai, provider=provider)

    if result:
        console.print(Markdown(result))
    else:
        formatter.print_warning("Could not explain script.")
