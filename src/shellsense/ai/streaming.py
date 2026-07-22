from __future__ import annotations

import sys
import time
from collections.abc import Generator

from shellsense.ai.providers.base import AIResponse, TokenUsage
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)


def simulate_streaming(text: str, chunk_size: int = 4) -> Generator[str, None, None]:
    for i in range(0, len(text), chunk_size):
        yield text[i : i + chunk_size]


def stream_to_console(text: str, delay: float = 0.015) -> None:
    for chunk in simulate_streaming(text):
        sys.stdout.write(chunk)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\n")


def build_streaming_response(chunks: list[str]) -> AIResponse:
    content = "".join(chunks)
    usage = TokenUsage(
        input_tokens=0,
        output_tokens=len(content.split()),
        total_tokens=len(content.split()),
    )
    return AIResponse(
        content=content,
        model="streaming",
        provider="streaming",
        usage=usage,
    )
