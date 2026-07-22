from __future__ import annotations

from typing import Any

DEFAULT_SHORTCUTS: dict[str, dict[str, Any]] = {
    "accept_suggestion": {
        "keys": ["right", "tab"],
        "description": "Accept the current suggestion",
    },
    "cycle_next": {
        "keys": ["ctrl+n", "down"],
        "description": "Cycle to the next suggestion",
    },
    "cycle_previous": {
        "keys": ["ctrl+p", "up"],
        "description": "Cycle to the previous suggestion",
    },
    "dismiss": {
        "keys": ["esc"],
        "description": "Dismiss suggestions",
    },
    "interactive_help": {
        "keys": ["ctrl+h"],
        "description": "Show interactive help for current command",
    },
    "toggle_autocomplete": {
        "keys": ["ctrl+space"],
        "description": "Toggle autocomplete on/off",
    },
}


def get_shortcut(action: str) -> dict[str, Any] | None:
    return DEFAULT_SHORTCUTS.get(action)


def get_all_shortcuts() -> dict[str, dict[str, Any]]:
    return DEFAULT_SHORTCUTS.copy()
