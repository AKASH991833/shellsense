from __future__ import annotations

from rich.console import Console

from shellsense.shell.autocomplete import get_autocomplete_suggestions
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)
console = Console()


def autocomplete_callback(
    partial: str,
    limit: int = 10,
) -> None:
    results = get_autocomplete_suggestions(partial, limit=limit)

    for r in results:
        name = r.get("name", "")
        desc = r.get("short_description", "")
        if desc:
            console.print(f"{name}  --  {desc}")
        else:
            console.print(name)
