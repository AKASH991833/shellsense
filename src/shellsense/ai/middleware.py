from __future__ import annotations

import time
from collections.abc import Callable

from shellsense.ai.providers.base import AIResponse
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)

BeforeHandler = Callable[[str, str], None]
AfterHandler = Callable[[str, str, AIResponse], None]


class MiddlewarePipeline:
    def __init__(self) -> None:
        self._before: list[BeforeHandler] = []
        self._after: list[AfterHandler] = []

    def add_before(self, handler: BeforeHandler) -> None:
        self._before.append(handler)

    def add_after(self, handler: AfterHandler) -> None:
        self._after.append(handler)

    def run_before(self, prompt: str, system_prompt: str) -> None:
        for handler in self._before:
            try:
                handler(prompt, system_prompt)
            except Exception as e:
                logger.warning("Middleware before error: %s", e)

    def run_after(self, prompt: str, system_prompt: str, response: AIResponse) -> None:
        for handler in self._after:
            try:
                handler(prompt, system_prompt, response)
            except Exception as e:
                logger.warning("Middleware after error: %s", e)


def logging_middleware(
    prompt: str, system_prompt: str, response: AIResponse | None = None
) -> None:
    if response is None:
        logger.debug(
            "AI request: prompt_len=%d system_len=%d", len(prompt), len(system_prompt)
        )
    else:
        logger.debug(
            "AI response: tokens=%d latency=%.1fms",
            response.usage.total_tokens,
            response.usage.latency_ms,
        )


def timing_middleware() -> tuple[BeforeHandler, AfterHandler]:
    start = [0.0]

    def before(prompt: str, system_prompt: str) -> None:
        start[0] = time.time()

    def after(prompt: str, system_prompt: str, response: AIResponse) -> None:
        elapsed = time.time() - start[0]
        response.usage.latency_ms = elapsed * 1000

    return before, after
