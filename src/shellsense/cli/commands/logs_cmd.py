from __future__ import annotations

from rich.console import Console

from shellsense.cli.commands.shared import get_engine
from shellsense.intelligence.formatter import ResponseFormatter

console = Console()


def logs_analyze_callback(
    source: str = "journald",
    units: list[str] | None = None,
    lines: int = 100,
) -> None:
    engine = get_engine()
    formatter = ResponseFormatter()

    result = engine.analyze_logs(source=source, units=units, lines=lines)

    formatter.print_log_analysis(result.to_dict())

    if result.suspicious_entries:
        critical = [
            e for e in result.suspicious_entries if e.get("severity") == "critical"
        ]
        high = [e for e in result.suspicious_entries if e.get("severity") == "high"]
        if critical:
            for entry in critical:
                formatter.print_warning(f"[CRITICAL] {entry.get('content', '')[:200]}")
        if high:
            formatter.print_info(f"\n{len(high)} high-severity entries")
