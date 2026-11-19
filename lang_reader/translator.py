"""Translation backends. Anything with a matching `translate` method will do."""
from __future__ import annotations

from typing import Protocol


class Translator(Protocol):
    def translate(self, word: str, source_lang: str) -> str: ...


class GoogleWordTranslator:
    """Free Google Translate via deep-translator (needs internet, no API key)."""

    def __init__(self, target_lang: str = "en") -> None:
        self._target = target_lang
        self._cache: dict[tuple[str, str], str] = {}

    def translate(self, word: str, source_lang: str) -> str:
        key = (word, source_lang.lower())
        if key not in self._cache:
            from deep_translator import GoogleTranslator  # lazy: keeps tests dependency-free

            result = GoogleTranslator(source=source_lang, target=self._target).translate(word)
            self._cache[key] = result or ""
        return self._cache[key]
