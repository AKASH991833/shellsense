from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any

from shellsense.utils.logging import get_logger
from shellsense.utils.paths import get_shellsense_dir

logger = get_logger(__name__)


class Conversation:
    def __init__(
        self,
        session_id: str | None = None,
        provider: str = "",
        model: str = "",
        system_prompt: str = "",
    ) -> None:
        self.session_id = session_id or str(uuid.uuid4())
        self.provider = provider
        self.model = model
        self.system_prompt = system_prompt
        self.messages: list[dict[str, str]] = []
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at

    def add_message(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "provider": self.provider,
            "model": self.model,
            "system_prompt": self.system_prompt,
            "messages": self.messages,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Conversation:
        conv = Conversation(
            session_id=data.get("session_id", ""),
            provider=data.get("provider", ""),
            model=data.get("model", ""),
            system_prompt=data.get("system_prompt", ""),
        )
        conv.messages = data.get("messages", [])
        conv.created_at = data.get("created_at", "")
        conv.updated_at = data.get("updated_at", "")
        return conv


class SessionManager:
    def __init__(self) -> None:
        self._sessions: dict[str, Conversation] = {}
        self._active_session_id: str | None = None
        self._storage_dir = get_shellsense_dir() / "conversations"
        self._storage_dir.mkdir(parents=True, exist_ok=True)

    def create_session(
        self,
        provider: str = "",
        model: str = "",
        system_prompt: str = "",
    ) -> Conversation:
        conv = Conversation(provider=provider, model=model, system_prompt=system_prompt)
        self._sessions[conv.session_id] = conv
        self._active_session_id = conv.session_id
        logger.debug("Created session: %s", conv.session_id)
        return conv

    def get_session(self, session_id: str) -> Conversation | None:
        if session_id in self._sessions:
            return self._sessions[session_id]
        return self._load_from_disk(session_id)

    def get_active_session(self) -> Conversation | None:
        if self._active_session_id and self._active_session_id in self._sessions:
            return self._sessions[self._active_session_id]
        return None

    def set_active_session(self, session_id: str) -> None:
        if session_id in self._sessions:
            self._active_session_id = session_id
        else:
            conv = self._load_from_disk(session_id)
            if conv:
                self._sessions[session_id] = conv
                self._active_session_id = session_id

    def delete_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
        path = self._storage_dir / f"{session_id}.json"
        if path.exists():
            path.unlink()
        if self._active_session_id == session_id:
            self._active_session_id = None

    def list_sessions(self) -> list[dict[str, Any]]:
        sessions: list[dict[str, Any]] = []
        for path in self._storage_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text())
                sessions.append(
                    {
                        "session_id": data.get("session_id", ""),
                        "provider": data.get("provider", ""),
                        "model": data.get("model", ""),
                        "message_count": len(data.get("messages", [])),
                        "created_at": data.get("created_at", ""),
                        "updated_at": data.get("updated_at", ""),
                    }
                )
            except Exception:
                continue
        for conv in self._sessions.values():
            if not any(s["session_id"] == conv.session_id for s in sessions):
                sessions.append(
                    {
                        "session_id": conv.session_id,
                        "provider": conv.provider,
                        "model": conv.model,
                        "message_count": len(conv.messages),
                        "created_at": conv.created_at,
                        "updated_at": conv.updated_at,
                    }
                )
        sessions.sort(key=lambda s: s.get("updated_at", ""), reverse=True)
        return sessions

    def save_session(self, session_id: str | None = None) -> None:
        sid = session_id or self._active_session_id
        if not sid or sid not in self._sessions:
            return
        conv = self._sessions[sid]
        path = self._storage_dir / f"{sid}.json"
        path.write_text(json.dumps(conv.to_dict(), indent=2))
        logger.debug("Saved session: %s", sid)

    def save_all(self) -> None:
        for sid in list(self._sessions.keys()):
            self.save_session(sid)

    def clear_all_sessions(self) -> None:
        self._sessions.clear()
        self._active_session_id = None
        for path in self._storage_dir.glob("*.json"):
            path.unlink()
        logger.info("All sessions cleared")

    def _load_from_disk(self, session_id: str) -> Conversation | None:
        path = self._storage_dir / f"{session_id}.json"
        if path.exists():
            try:
                data = json.loads(path.read_text())
                conv = Conversation.from_dict(data)
                self._sessions[session_id] = conv
                return conv
            except Exception as e:
                logger.warning("Failed to load session %s: %s", session_id, e)
        return None
