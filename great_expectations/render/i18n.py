from __future__ import annotations

from typing import Dict, Optional

DEFAULT_LOCALE = "en"
Translations = Dict[str, Dict[str, str]]


def _normalize_locale(locale: Optional[str]) -> str:
    if not locale:
        return DEFAULT_LOCALE
    return locale.strip().replace("-", "_").lower()


def _candidate_locales(locale: Optional[str]) -> list[str]:
    normalized_locale = _normalize_locale(locale)
    candidates = [normalized_locale]
    if "_" in normalized_locale:
        candidates.append(normalized_locale.split("_", 1)[0])
    if DEFAULT_LOCALE not in candidates:
        candidates.append(DEFAULT_LOCALE)
    return candidates


def translate(
    key: str,
    default: str,
    *,
    locale: Optional[str] = None,
    translations: Optional[Translations] = None,
) -> str:
    if not translations:
        return default

    normalized_translations = {
        _normalize_locale(locale_name): catalog for locale_name, catalog in translations.items()
    }

    for locale_name in _candidate_locales(locale):
        localized_catalog = normalized_translations.get(locale_name, {})
        translated = localized_catalog.get(key)
        if translated is not None:
            return translated

    return default
