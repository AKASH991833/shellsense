from __future__ import annotations

RISK_SAFE = "SAFE"
RISK_CAUTION = "CAUTION"
RISK_DANGEROUS = "DANGEROUS"
RISK_VERY_DANGEROUS = "VERY_DANGEROUS"

_RISK_ORDER: dict[str, int] = {
    RISK_SAFE: 0,
    RISK_CAUTION: 1,
    RISK_DANGEROUS: 2,
    RISK_VERY_DANGEROUS: 3,
}

_RISK_COLORS: dict[str, str] = {
    RISK_SAFE: "green",
    RISK_CAUTION: "yellow",
    RISK_DANGEROUS: "red",
    RISK_VERY_DANGEROUS: "bright_red",
}

_RISK_EMOJIS: dict[str, str] = {
    RISK_SAFE: "",
    RISK_CAUTION: "!",
    RISK_DANGEROUS: "!!",
    RISK_VERY_DANGEROUS: "!!!",
}


def risk_level_to_int(level: str) -> int:
    return _RISK_ORDER.get(level, 0)


def risk_color(level: str) -> str:
    return _RISK_COLORS.get(level, "white")


def risk_icon(level: str) -> str:
    return _RISK_EMOJIS.get(level, "")


def is_safe(level: str) -> bool:
    return level == RISK_SAFE


def is_dangerous(level: str) -> bool:
    return level in (RISK_DANGEROUS, RISK_VERY_DANGEROUS)


def requires_confirmation(level: str) -> bool:
    return level in (RISK_DANGEROUS, RISK_VERY_DANGEROUS)
