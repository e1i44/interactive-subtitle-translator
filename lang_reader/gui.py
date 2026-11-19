"""Tkinter GUI: subtitle text on the left, word translations on the right."""
from __future__ import annotations

import queue
import tkinter as tk
import tkinter.font as tkfont
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, ttk
from typing import Protocol

from .files import find_audio, infer_language, list_srt_files
from .srt import Cue, load_srt
from .translator import Translator
from .words import find_words

DEFAULT_FONT_SIZE = 14
MIN_FONT_SIZE, MAX_FONT_SIZE = 8, 48
DEFAULT_VOLUME = 80  # percent
PANEL_WIDTH_CHARS = 45
HOVER_BG = "#ffe97f"
POLL_MS = 100


class Player(Protocol):
    def load(self, path: Path) -> None: ...
    def play(self, start: float, end: float) -> None: ...
    def set_volume(self, volume: float) -> None: ...
    def close(self) -> None: ...


@dataclass(frozen=True)
class WordSpan:
    start: str  # Tk text index
    end: str
    word: str
    cue: Cue


class App(tk.Tk):
    def __init__(self, translator: Translator, player: Player, media_dir: Path) -> None:
        super().__init__()
        self.title("Language Reader")
        self.geometry("1100x700")
        self.minsize(800, 400)

        self._translator = translator
        self._player = player
        self._media_dir = media_dir
        self._pool = ThreadPoolExecutor(max_workers=1)  # one worker keeps results in click order
        self._results: queue.Queue[tuple[str, str]] = queue.Queue()
        self._spans: list[WordSpan] = []
        self._hovered: int | None = None
        self._audio_ready = False

        self._choice = tk.StringVar()
        self._lang = tk.StringVar()
        self._font_size = tk.IntVar(value=DEFAULT_FONT_SIZE)
        self._volume = tk.DoubleVar(value=DEFAULT_VOLUME)
        self._status = tk.StringVar(value="Choose an .srt file to begin.")
        self._font = tkfont.Font(root=self, size=DEFAULT_FONT_SIZE)

        self._build_settings()
        self._build_panels()
        self._refresh_files()
        ttk.Label(self, textvariable=self._status, anchor="w").grid(
            row=2, column=0, sticky="ew", padx=8, pady=(0, 6)
        )
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self._font_size.trace_add("write", self._on_font_size)
        self._volume.trace_add("write", self._on_volume)
        self._player.set_volume(DEFAULT_VOLUME / 100)
        self.after(POLL_MS, self._poll_results)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---- layout -----------------------------------------------------------

    def _build_settings(self) -> None:
        bar = ttk.Frame(self, padding=8)
        bar.grid(row=0, column=0, sticky="ew")
        bar.columnconfigure(1, weight=1)

        ttk.Label(bar, text="SRT file").grid(row=0, column=0)
        self._picker = ttk.Combobox(bar, textvariable=self._choice, state="readonly")
        self._picker.grid(row=0, column=1, sticky="ew", padx=4)
        self._picker.bind("<<ComboboxSelected>>", self._on_pick)
        ttk.Button(bar, text="Refresh", command=self._refresh_files).grid(row=0, column=2)
        ttk.Button(bar, text="Browse…", command=self._browse).grid(row=0, column=3, padx=(4, 0))

        options = ttk.Frame(bar)
        options.grid(row=1, column=0, columnspan=4, sticky="w", pady=(6, 0))
        ttk.Label(options, text="Language").pack(side="left")
        ttk.Entry(options, textvariable=self._lang, width=7).pack(side="left", padx=(4, 16))
        ttk.Label(options, text="Font size").pack(side="left")
        ttk.Spinbox(
            options, from_=MIN_FONT_SIZE, to=MAX_FONT_SIZE, width=4, textvariable=self._font_size
        ).pack(side="left", padx=(4, 16))
        ttk.Label(options, text="Volume").pack(side="left")
        ttk.Scale(options, from_=0, to=100, length=120, variable=self._volume).pack(
            side="left", padx=4
        )

    def _build_panels(self) -> None:
        frame = ttk.Frame(self, padding=(8, 0))
        frame.grid(row=1, column=0, sticky="nsew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure((0, 1), weight=1, uniform="panel")  # equal widths

        self._source = self._make_panel(frame, column=0)
        self._output = self._make_panel(frame, column=1)

        self._source.tag_configure("hover", background=HOVER_BG)
        self._source.bind("<Motion>", self._on_motion)
        self._source.bind("<Leave>", lambda _e: self._set_hover(None))
        self._source.bind("<Button-1>", self._on_click)

    def _make_panel(self, parent: ttk.Frame, column: int) -> tk.Text:
        holder = ttk.Frame(parent)
        holder.grid(row=0, column=column, sticky="nsew", padx=4)
        holder.rowconfigure(0, weight=1)
        holder.columnconfigure(0, weight=1)

        text = tk.Text(
            holder, width=PANEL_WIDTH_CHARS, wrap="word", font=self._font,
            state="disabled", cursor="arrow", padx=8, pady=8,
        )
        scrollbar = ttk.Scrollbar(holder, command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        text.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        return text

    # ---- loading ----------------------------------------------------------
    def _refresh_files(self) -> None:
        """Re-scan the media folder so files added after launch appear."""
        self._picker["values"] = [p.name for p in list_srt_files(self._media_dir)]

    def _on_pick(self, _event: tk.Event) -> None:
        self.load_file(self._media_dir / self._choice.get())

    def _browse(self) -> None:
        chosen = filedialog.askopenfilename(
            initialdir=self._media_dir, filetypes=[("Subtitles", "*.srt")]
        )
        if chosen:
            self.load_file(chosen)


    def load_file(self, raw_path: str | Path) -> None:
        path = Path(raw_path).expanduser()
        self._choice.set(path.name)
        if path.suffix.lower() != ".srt" or not path.is_file():
            self._status.set(f"Not a readable .srt file: {path}")
            return
        try:
            cues = load_srt(path)
        except (OSError, UnicodeDecodeError) as exc:
            self._status.set(f"Could not read {path.name}: {exc}")
            return

        self._render(cues)
        language = infer_language(path)
        self._lang.set(language)
        status = f"Loaded {len(cues)} subtitles · {self._load_audio(find_audio(path))}"
        if not language:
            status += " · couldn't infer the language, please enter a code"
        self._status.set(status)

    def _load_audio(self, audio: Path | None) -> str:
        """Load the mp3 into the player; return a short status fragment."""
        self._audio_ready = False
        if audio is None:
            return "no matching .mp3 found"
        try:
            self._player.load(audio)
        except Exception as exc:  # pygame raises its own error type
            return f"audio error: {exc}"
        self._audio_ready = True
        return f"audio: {audio.name}"

    def _render(self, cues: list[Cue]) -> None:
        text = self._source
        text.configure(state="normal")
        for i in range(len(self._spans)):
            text.tag_delete(f"w{i}")
        text.delete("1.0", "end")
        self._spans = []
        self._hovered = None

        for cue in cues:
            pos = 0
            for start, end in find_words(cue.text):
                text.insert("end", cue.text[pos:start])
                begin = text.index("end-1c")
                text.insert("end", cue.text[start:end], f"w{len(self._spans)}")
                self._spans.append(WordSpan(begin, text.index("end-1c"), cue.text[start:end], cue))
                pos = end
            text.insert("end", cue.text[pos:] + "\n\n")

        text.configure(state="disabled")
        text.yview_moveto(0)

    # ---- mouse interaction --------------------------------------------------

    def _word_at(self, event: tk.Event) -> int | None:
        """Index of the word under the pointer, or None if over blank space."""
        index = self._source.index(f"@{event.x},{event.y}")
        box = self._source.bbox(index)
        if box is None:
            return None
        x, y, width, height = box
        if not (x <= event.x < x + width and y <= event.y < y + height):
            return None
        for tag in self._source.tag_names(index):
            if tag[0] == "w" and tag[1:].isdigit():
                return int(tag[1:])
        return None

    def _on_motion(self, event: tk.Event) -> None:
        self._set_hover(self._word_at(event))

    def _set_hover(self, word_id: int | None) -> None:
        if word_id == self._hovered:
            return
        self._source.tag_remove("hover", "1.0", "end")
        if word_id is not None:
            span = self._spans[word_id]
            self._source.tag_add("hover", span.start, span.end)
        self._source.configure(cursor="hand2" if word_id is not None else "arrow")
        self._hovered = word_id

    def _on_click(self, event: tk.Event) -> None:
        word_id = self._word_at(event)
        if word_id is None:
            return
        span = self._spans[word_id]
        self._play(span.cue)
        self._request_translation(span.word)

    # ---- audio & translation ------------------------------------------------

    def _play(self, cue: Cue) -> None:
        if not self._audio_ready:
            self._status.set("No audio loaded for this file.")
            return
        try:
            self._player.play(cue.start, cue.end)
        except Exception as exc:
            self._status.set(f"Audio error: {exc}")

    def _request_translation(self, word: str) -> None:
        language = self._lang.get().strip()
        if not language:
            self._status.set("Enter a language code (e.g. 'fr') to translate.")
            return
        self._pool.submit(self._translate_job, word, language)

    def _translate_job(self, word: str, language: str) -> None:
        """Runs on the worker thread; results go through a queue to the UI thread."""
        try:
            result = self._translator.translate(word, language)
        except Exception as exc:
            result = f"⚠ {exc}"
        self._results.put((word, result))

    def _poll_results(self) -> None:
        while True:
            try:
                word, translation = self._results.get_nowait()
            except queue.Empty:
                break
            self._append_translation(word, translation)
        self.after(POLL_MS, self._poll_results)

    def _append_translation(self, word: str, translation: str) -> None:
        self._output.configure(state="normal")
        self._output.insert("end", f"{word} → {translation}\n")
        self._output.configure(state="disabled")
        self._output.see("end")

    # ---- settings -----------------------------------------------------------

    def _on_font_size(self, *_: object) -> None:
        try:
            size = self._font_size.get()
        except tk.TclError:  # box is empty / mid-edit
            return
        self._font.configure(size=max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, size)))

    def _on_volume(self, *_: object) -> None:
        self._player.set_volume(self._volume.get() / 100)

    def _on_close(self) -> None:
        self._pool.shutdown(wait=False, cancel_futures=True)
        self._player.close()
        self.destroy()
