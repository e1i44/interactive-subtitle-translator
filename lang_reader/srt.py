"""Minimal SRT parser."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_TIME_LINE = re.compile(
    r"(\d+):(\d{2}):(\d{2})[,.](\d{1,3})\s*-->\s*(\d+):(\d{2}):(\d{2})[,.](\d{1,3})"
)
_MARKUP = re.compile(r"<[^>]+>|\{\\[^}]*\}")  # <i>...</i> and {\an8} styles


@dataclass(frozen=True)
class Cue:
    start: float  # seconds
    end: float  # seconds
    text: str


def _seconds(hours: str, minutes: str, seconds: str, millis: str) -> float:
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(millis.ljust(3, "0")) / 1000


def _parse_block(block: str) -> Cue | None:
    """Parse one blank-line-separated block; the timing line is line 1 or 2."""
    lines = block.strip().split("\n")
    for i, line in enumerate(lines[:2]):
        match = _TIME_LINE.search(line)
        if match:
            groups = match.groups()
            text = _MARKUP.sub("", "\n".join(lines[i + 1 :])).strip()
            if text:
                return Cue(_seconds(*groups[:4]), _seconds(*groups[4:]), text)
    return None


def parse_srt(content: str) -> list[Cue]:
    """Parse SRT text into cues, silently skipping malformed blocks."""
    normalised = content.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n").strip()
    cues = (_parse_block(block) for block in re.split(r"\n\s*\n", normalised))
    return [cue for cue in cues if cue is not None]


def load_srt(path: Path) -> list[Cue]:
    return parse_srt(path.read_text(encoding="utf-8-sig"))
