"""Play a time slice of an mp3 using pygame.mixer."""
from __future__ import annotations

import os
import threading
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame  # noqa: E402


class SegmentPlayer:
    """Loads one mp3 and plays [start, end) slices of it."""

    def __init__(self, volume: float = 0.8) -> None:
        pygame.mixer.init()
        self._volume = volume
        self._stop_timer: threading.Timer | None = None

    def load(self, path: Path) -> None:
        self._cancel_stop()
        pygame.mixer.music.load(str(path))

    def set_volume(self, volume: float) -> None:
        """volume is 0.0 - 1.0."""
        self._volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self._volume)

    def play(self, start: float, end: float) -> None:
        self._cancel_stop()
        pygame.mixer.music.set_volume(self._volume)
        pygame.mixer.music.play(start=start)
        self._stop_timer = threading.Timer(max(end - start, 0.1), pygame.mixer.music.stop)
        self._stop_timer.daemon = True
        self._stop_timer.start()

    def close(self) -> None:
        self._cancel_stop()
        pygame.mixer.quit()

    def _cancel_stop(self) -> None:
        if self._stop_timer is not None:
            self._stop_timer.cancel()
            self._stop_timer = None
