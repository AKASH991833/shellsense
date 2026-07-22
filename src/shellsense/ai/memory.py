from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from shellsense.utils.logging import get_logger
from shellsense.utils.paths import get_shellsense_dir

logger = get_logger(__name__)


class AIMemory:
    def __init__(self) -> None:
        self._memory_dir = get_shellsense_dir() / "ai_memory"
        self._memory_dir.mkdir(parents=True, exist_ok=True)
        self._preferences_file = self._memory_dir / "preferences.json"
        self._history_file = self._memory_dir / "history.json"
        self._preferences: dict[str, Any] = self._load_json(self._preferences_file)
        self._history: list[dict[str, Any]] = self._load_json(
            self._history_file, default=[]
        )
        self._temporary: dict[str, Any] = {}
        self._session: dict[str, Any] = {}
        self._enabled = True

    @property
    def enabled(self) -> bool:
        return self._enabled

    def enable(self) -> None:
        self._enabled = True
        logger.info("AI memory enabled")

    def disable(self) -> None:
        self._enabled = False
        logger.info("AI memory disabled")

    def set_preference(self, key: str, value: Any) -> None:
        if not self._enabled:
            return
        self._preferences[key] = value
        self._save_json(self._preferences_file, self._preferences)

    def get_preference(self, key: str, default: Any = None) -> Any:
        return self._preferences.get(key, default)

    def set_session_data(self, key: str, value: Any) -> None:
        self._session[key] = value

    def get_session_data(self, key: str, default: Any = None) -> Any:
        return self._session.get(key, default)

    def set_temporary(self, key: str, value: Any) -> None:
        self._temporary[key] = value

    def get_temporary(self, key: str, default: Any = None) -> Any:
        return self._temporary.get(key, default)

    def add_to_history(self, entry: dict[str, Any]) -> None:
        if not self._enabled:
            return
        entry["timestamp"] = datetime.now().isoformat()
        self._history.append(entry)
        if len(self._history) > 1000:
            self._history = self._history[-1000:]
        self._save_json(self._history_file, self._history)

    def get_history(self, limit: int = 50) -> list[dict[str, Any]]:
        return self._history[-limit:]

    def clear(self) -> None:
        self._preferences.clear()
        self._session.clear()
        self._temporary.clear()
        self._history.clear()
        self._save_json(self._preferences_file, self._preferences)
        self._save_json(self._history_file, self._history)
        logger.info("AI memory cleared")

    def export_data(self) -> dict[str, Any]:
        return {
            "preferences": self._preferences,
            "history": self._history[-100:],
            "exported_at": datetime.now().isoformat(),
        }

    def import_data(self, data: dict[str, Any]) -> None:
        if "preferences" in data:
            self._preferences.update(data["preferences"])
            self._save_json(self._preferences_file, self._preferences)
        if "history" in data:
            self._history.extend(data["history"])
            if len(self._history) > 1000:
                self._history = self._history[-1000:]
            self._save_json(self._history_file, self._history)
        logger.info("AI memory imported")

    def _load_json(self, path: Path, default: Any = None) -> Any:
        if default is None:
            default = {}
        try:
            if path.exists():
                return json.loads(path.read_text())
        except Exception as e:
            logger.warning("Failed to load %s: %s", path, e)
        return default

    def _save_json(self, path: Path, data: Any) -> None:
        try:
            path.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.warning("Failed to save %s: %s", path, e)
