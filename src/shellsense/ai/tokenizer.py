from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from shellsense.utils.logging import get_logger

logger = get_logger(__name__)

ESTIMATED_COST_PER_TOKEN: dict[str, dict[str, float]] = {
    "openai": {"input": 0.00000015, "output": 0.00000060},
    "gemini": {"input": 0.00000010, "output": 0.00000040},
    "ollama": {"input": 0.0, "output": 0.0},
    "claude": {"input": 0.00000025, "output": 0.00000125},
    "openrouter": {"input": 0.00000015, "output": 0.00000060},
    "local": {"input": 0.0, "output": 0.0},
}


@dataclass
class UsageRecord:
    provider: str = ""
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0
    latency_ms: float = 0.0
    timestamp: str = ""


class TokenTracker:
    def __init__(self) -> None:
        self._daily: dict[str, UsageRecord] = {}
        self._monthly: dict[str, UsageRecord] = {}
        self._session: list[UsageRecord] = []
        self._provider_totals: dict[str, dict[str, int | float]] = {}

    def record_usage(self, record: UsageRecord) -> None:
        self._session.append(record)
        date_key = datetime.now().strftime("%Y-%m-%d")
        month_key = datetime.now().strftime("%Y-%m")
        self._update_aggregate(self._daily, date_key, record)
        self._update_aggregate(self._monthly, month_key, record)
        if record.provider not in self._provider_totals:
            self._provider_totals[record.provider] = {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "cost": 0.0,
                "requests": 0,
            }
        stats = self._provider_totals[record.provider]
        stats["input_tokens"] += record.input_tokens
        stats["output_tokens"] += record.output_tokens
        stats["total_tokens"] += record.total_tokens
        stats["cost"] += record.cost
        stats["requests"] += 1

    def estimate_cost(
        self, provider: str, input_tokens: int, output_tokens: int
    ) -> float:
        rates = ESTIMATED_COST_PER_TOKEN.get(provider, {"input": 0.0, "output": 0.0})
        return (input_tokens * rates["input"]) + (output_tokens * rates["output"])

    def get_session_usage(self) -> list[UsageRecord]:
        return list(self._session)

    def get_daily_usage(self) -> dict[str, Any]:
        date_key = datetime.now().strftime("%Y-%m-%d")
        record = self._daily.get(date_key, UsageRecord())
        return {
            "date": date_key,
            "total_tokens": record.total_tokens,
            "input_tokens": record.input_tokens,
            "output_tokens": record.output_tokens,
            "cost": record.cost,
        }

    def get_monthly_usage(self) -> dict[str, Any]:
        month_key = datetime.now().strftime("%Y-%m")
        record = self._monthly.get(month_key, UsageRecord())
        return {
            "month": month_key,
            "total_tokens": record.total_tokens,
            "input_tokens": record.input_tokens,
            "output_tokens": record.output_tokens,
            "cost": record.cost,
        }

    def get_provider_usage(self) -> dict[str, dict[str, Any]]:
        return dict(self._provider_totals)

    def _update_aggregate(
        self, store: dict[str, UsageRecord], key: str, record: UsageRecord
    ) -> None:
        if key not in store:
            store[key] = UsageRecord(
                provider=record.provider,
                model=record.model,
                input_tokens=record.input_tokens,
                output_tokens=record.output_tokens,
                total_tokens=record.total_tokens,
                cost=record.cost,
                latency_ms=record.latency_ms,
            )
        else:
            agg = store[key]
            agg.input_tokens += record.input_tokens
            agg.output_tokens += record.output_tokens
            agg.total_tokens += record.total_tokens
            agg.cost += record.cost
            agg.latency_ms = max(agg.latency_ms, record.latency_ms)
