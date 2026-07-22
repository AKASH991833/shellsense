from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

_TELEMETRY_ENABLED: bool = False
_TELEMETRY_FILE: str | None = None


def is_telemetry_enabled() -> bool:
    return _TELEMETRY_ENABLED


def enable_telemetry(data_dir: str | None = None) -> None:
    global _TELEMETRY_ENABLED, _TELEMETRY_FILE
    _TELEMETRY_ENABLED = True
    if data_dir:
        _TELEMETRY_FILE = os.path.join(data_dir, "telemetry.json")


def disable_telemetry() -> None:
    global _TELEMETRY_ENABLED
    _TELEMETRY_ENABLED = False


def record_event(event: str, data: dict[str, Any] | None = None) -> None:
    if not _TELEMETRY_ENABLED or not _TELEMETRY_FILE:
        return
    try:
        import datetime

        entry = {
            "event": event,
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            "data": data or {},
        }
        path = Path(_TELEMETRY_FILE)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            with open(path) as f:
                events = json.load(f)
        else:
            events = []
        events.append(entry)
        if len(events) > 1000:
            events = events[-1000:]
        with open(path, "w") as f:
            json.dump(events, f, indent=2)
    except Exception:
        pass


def get_telemetry_data() -> list[dict[str, Any]]:
    if not _TELEMETRY_FILE:
        return []
    try:
        path = Path(_TELEMETRY_FILE)
        if path.exists():
            data: list[dict[str, Any]] = json.loads(path.read_text())
            return data
    except Exception:
        pass
    return []
