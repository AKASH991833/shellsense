from __future__ import annotations

from typing import Any

from shellsense.ai.tokenizer import TokenTracker


class AIAnalytics:
    def __init__(self, token_tracker: TokenTracker) -> None:
        self._tracker = token_tracker

    def get_daily_report(self) -> dict[str, Any]:
        return self._tracker.get_daily_usage()

    def get_monthly_report(self) -> dict[str, Any]:
        return self._tracker.get_monthly_usage()

    def get_provider_report(self) -> dict[str, Any]:
        return self._tracker.get_provider_usage()

    def get_session_report(self) -> list[Any]:
        return self._tracker.get_session_usage()

    def get_summary(self) -> dict[str, Any]:
        daily = self.get_daily_report()
        monthly = self.get_monthly_report()
        providers = self.get_provider_report()
        return {
            "daily": daily,
            "monthly": monthly,
            "providers": providers,
            "total_requests": sum(p.get("requests", 0) for p in providers.values()),
            "total_cost": monthly.get("cost", 0),
        }
