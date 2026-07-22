from __future__ import annotations

import locale
from pathlib import Path
from typing import Any

_TRANSLATIONS: dict[str, dict[str, str]] = {}
_CURRENT_LANG: str = "en"


def _load_translations(lang: str) -> dict[str, str]:
    lang_file = Path(__file__).resolve().parent / "locales" / f"{lang}.json"
    if lang_file.exists():
        import json

        try:
            with open(lang_file) as f:
                data: dict[str, str] = json.load(f)
                return data
        except Exception:
            pass
    return {}


def setup_i18n(language: str | None = None) -> None:
    global _CURRENT_LANG
    if language:
        _CURRENT_LANG = language
    else:
        try:
            detected = locale.getdefaultlocale()
            if detected and detected[0]:
                _CURRENT_LANG = detected[0][:2]
            else:
                _CURRENT_LANG = "en"
        except Exception:
            _CURRENT_LANG = "en"
    if _CURRENT_LANG not in _TRANSLATIONS:
        _TRANSLATIONS[_CURRENT_LANG] = _load_translations(_CURRENT_LANG)


def set_language(language: str) -> None:
    global _CURRENT_LANG
    _CURRENT_LANG = language
    if language not in _TRANSLATIONS:
        _TRANSLATIONS[language] = _load_translations(language)


def get_language() -> str:
    return _CURRENT_LANG


def _(key: str, **kwargs: Any) -> str:
    translations = _TRANSLATIONS.get(_CURRENT_LANG, {})
    text = translations.get(key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass
    return text


def available_languages() -> list[str]:
    locales_dir = Path(__file__).resolve().parent / "locales"
    if not locales_dir.exists():
        return ["en"]
    return sorted(f.stem for f in locales_dir.glob("*.json") if f.stem != "README") or [
        "en"
    ]
