"""Path helpers: language-code inference and matching audio lookup."""
from __future__ import annotations

import re
from pathlib import Path

_LANG_CODE = re.compile(r"^[a-z]{2,3}(-[a-z]{2,4})?$", re.IGNORECASE)


def list_srt_files(folder: str | Path) -> list[Path]:
    """All .srt files directly inside folder, sorted by name (empty if it doesn't exist)."""
    return sorted(Path(folder).glob("*.srt"), key=lambda p: p.name.lower())



def infer_language(srt_path: str | Path) -> str:
    """'show.fr.srt' -> 'fr'. Returns '' when no plausible code is present."""
    candidate = Path(Path(srt_path).stem).suffix.lstrip(".")
    return candidate if _LANG_CODE.match(candidate) else ""


def find_audio(srt_path: str | Path) -> Path | None:
    """Find the mp3 beside the srt: 'show.fr.mp3' first, then 'show.mp3'."""
    srt = Path(srt_path)
    stem = srt.stem
    for name in dict.fromkeys([f"{stem}.mp3", f"{Path(stem).stem}.mp3"]):
        candidate = srt.with_name(name)
        if candidate.is_file():
            return candidate
    return None
