"""Split text into clickable words."""
from __future__ import annotations

import re

# Letters (any script) with optional internal apostrophes/hyphens: l'homme, peut-être
_WORD = re.compile(r"[^\W\d_]+(?:['’\-][^\W\d_]+)*")


def find_words(text: str) -> list[tuple[int, int]]:
    """Return (start, end) character offsets of each word in text."""
    return [match.span() for match in _WORD.finditer(text)]
