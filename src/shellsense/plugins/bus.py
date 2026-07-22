from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from shellsense.utils.logging import get_logger

logger = get_logger(__name__)

MessageHandler = Callable[..., Any]


@dataclass
class Message:
    id: str = ""
    topic: str = ""
    sender: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now(UTC).isoformat()


class PluginEventBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[tuple[str, MessageHandler]]] = {}
        self._history: list[Message] = []
        self._max_history = 100

    def publish(
        self, topic: str, sender: str, data: dict[str, Any] | None = None
    ) -> None:
        msg = Message(topic=topic, sender=sender, data=data or {})
        self._history.append(msg)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history :]

        subscribers = self._subscribers.get(topic, [])
        for plugin_id, handler in subscribers:
            try:
                handler(msg)
            except Exception as e:
                logger.error(
                    "Bus handler '%s' for topic '%s' failed: %s",
                    plugin_id,
                    topic,
                    e,
                )

    def subscribe(self, topic: str, plugin_id: str, handler: MessageHandler) -> None:
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append((plugin_id, handler))
        logger.debug("Plugin '%s' subscribed to topic '%s'", plugin_id, topic)

    def unsubscribe(self, topic: str, plugin_id: str) -> None:
        if topic in self._subscribers:
            before = len(self._subscribers[topic])
            self._subscribers[topic] = [
                (pid, h) for pid, h in self._subscribers[topic] if pid != plugin_id
            ]
            removed = before - len(self._subscribers[topic])
            if removed:
                logger.debug(
                    "Unsubscribed plugin '%s' from topic '%s'",
                    plugin_id,
                    topic,
                )

    def unsubscribe_all(self, plugin_id: str) -> None:
        for topic in list(self._subscribers.keys()):
            self.unsubscribe(topic, plugin_id)

    def get_history(self, topic: str | None = None, limit: int = 10) -> list[Message]:
        if topic:
            return [m for m in self._history if m.topic == topic][-limit:]
        return self._history[-limit:]

    def clear(self) -> None:
        self._subscribers.clear()
        self._history.clear()
