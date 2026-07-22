from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from shellsense.utils.logging import get_logger

logger = get_logger(__name__)


class HookEvent(Enum):
    SHELL_STARTUP = "shell_startup"
    SHELL_SHUTDOWN = "shell_shutdown"
    BEFORE_COMMAND = "before_command"
    AFTER_COMMAND = "after_command"
    COMMAND_FAILURE = "command_failure"
    COMMAND_SUCCESS = "command_success"
    AI_REQUEST = "ai_request"
    AI_RESPONSE = "ai_response"
    CONTEXT_COLLECTION = "context_collection"
    GENERATION_REQUEST = "generation_request"
    VALIDATION_REQUEST = "validation_request"
    HISTORY_UPDATE = "history_update"
    PLUGIN_INSTALL = "plugin_install"
    PLUGIN_REMOVE = "plugin_remove"
    PLUGIN_ENABLE = "plugin_enable"
    PLUGIN_DISABLE = "plugin_disable"


@dataclass
class Hook:
    event: HookEvent
    plugin_id: str
    handler: Callable[..., Any]
    priority: int = 0
    enabled: bool = True
    name: str = ""


HookHandler = Callable[..., Any]


class HookRegistry:
    def __init__(self) -> None:
        self._hooks: dict[HookEvent, list[Hook]] = {}

    def register(
        self,
        event: HookEvent,
        plugin_id: str,
        handler: HookHandler,
        priority: int = 0,
        name: str = "",
    ) -> None:
        if event not in self._hooks:
            self._hooks[event] = []
        hook = Hook(
            event=event,
            plugin_id=plugin_id,
            handler=handler,
            priority=priority,
            name=name or handler.__name__,
        )
        self._hooks[event].append(hook)
        self._hooks[event].sort(key=lambda h: h.priority, reverse=True)
        logger.debug(
            "Hook '%s' registered by plugin '%s' (priority=%d)",
            event.value,
            plugin_id,
            priority,
        )

    def unregister(
        self, event: HookEvent, plugin_id: str, handler: HookHandler | None = None
    ) -> None:
        if event not in self._hooks:
            return
        before = len(self._hooks[event])
        if handler:
            self._hooks[event] = [
                h
                for h in self._hooks[event]
                if not (h.plugin_id == plugin_id and h.handler == handler)
            ]
        else:
            self._hooks[event] = [
                h for h in self._hooks[event] if h.plugin_id != plugin_id
            ]
        removed = before - len(self._hooks[event])
        if removed:
            logger.debug(
                "Unregistered %d hook(s) for plugin '%s' on event '%s'",
                removed,
                plugin_id,
                event.value,
            )

    def unregister_all(self, plugin_id: str) -> None:
        for event in list(self._hooks.keys()):
            self.unregister(event, plugin_id)

    def dispatch(self, event: HookEvent, **kwargs: Any) -> list[Any]:
        results: list[Any] = []
        hooks = self._hooks.get(event, [])
        for hook in hooks:
            if not hook.enabled:
                continue
            try:
                result = hook.handler(**kwargs)
                results.append(result)
            except Exception as e:
                logger.error(
                    "Hook '%s' for plugin '%s' failed: %s",
                    event.value,
                    hook.plugin_id,
                    e,
                )
        return results

    def get_hooks(self, event: HookEvent | None = None) -> dict[HookEvent, list[Hook]]:
        if event:
            return {event: list(self._hooks.get(event, []))}
        return {e: list(hooks) for e, hooks in self._hooks.items()}

    def get_plugin_hooks(self, plugin_id: str) -> list[Hook]:
        return [
            hook
            for hooks in self._hooks.values()
            for hook in hooks
            if hook.plugin_id == plugin_id
        ]

    def clear(self) -> None:
        self._hooks.clear()
