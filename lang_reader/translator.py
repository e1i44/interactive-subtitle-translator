"""Translation backends. Anything with a matching `translate` method will do."""
from __future__ import annotations
import asyncio
from typing import Protocol


class Translator(Protocol):
    def translate(self, word: str, source_lang: str) -> str: ...


class GoogleWordTranslator:

    def __init__(self, target_lang: str = "en") -> None:
        self._target = target_lang
        self._cache: dict[tuple[str, str], str] = {}

    def translate(self, word: str, source_lang: str) -> str:
        key = (word, source_lang.lower())
        if key not in self._cache:
            self._cache[key] = asyncio.run(self._translate(*key))
        return self._cache[key]

    async def _translate(self, word: str, source_lang: str) -> str:
        from googletrans import Translator as GoogleClient  # lazy: keeps tests dependency-free

        async with GoogleClient(raise_exception=True) as client:
            result = await client.translate(word, dest=self._target, src=source_lang)
        return result.text