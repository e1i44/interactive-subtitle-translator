# Language Reader

A small desktop app for language learners. Open a subtitle (`.srt`) file and its
matching `.mp3`, then **click any word** to hear that subtitle line and see the
word's English translation. Translations stack up in the right-hand panel.

## Requirements

- Python 3.10+
- Tkinter (bundled with most Python installs; on Debian/Ubuntu: `sudo apt install python3-tk`; for mac/homebrew losers such as myself `brew install python-tk`). You can check if it is already installed  by running `python -m tkinter`. It should open a little window.
- Internet access (translations use Google Translate through `deep-translator`)
- A working audio output device if you want audio

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
python main.py                   # then type or browse to an .srt file
python main.py path/to/show.fr.srt   # or open a file straight away
```

## Files

Put your files in the `media/` folder, with the subtitle and audio sharing a name
apart from the extension:

```
media/show.fr.srt
media/show.fr.mp3     # or show.mp3
```

Pick the subtitle file from the dropdown to load it. You can switch to another set at any time without restarting. If you add files while the app is open, press Refresh. Browse… still opens a file from anywhere else.


The language code is inferred from the name (`show.fr.srt` → `fr`). If your file has no code, or it is wrong, just type the right one into the **Language** box;
it is read every time you click a word. Codes follow Google Translate, e.g.
`fr`, `es`, `de`, `ja`, `zh-CN`.

## Using it

| Control | What it does |
| --- | --- |
| SRT file / Refresh / Browse | Pick a file from media/ (loads at once); Refresh re-scans the folder; Browse opens a file from elsewhere |
| Language | Source language code used for translation |
| Font size | Resizes text in both panels (8–48) |
| Volume | Playback volume (0–100) |
| Hover a word | Highlights it |
| Click a word | Plays that subtitle's audio and appends the translation on the right |

## Tests

```bash
pip install pytest
pytest
```

## Project layout

```
main.py                 entry point
media/
  your .srt and .mp3 files (contents are git-ignored)
lang_reader/
  srt.py                SRT parsing
  words.py              word splitting
  files.py              language inference + file lookup
  translator.py         Translator interface + Google implementation
  audio.py              play a slice of an mp3 (pygame)
  gui.py                Tkinter app
tests/                  unit tests for the pure logic
```

## Notes

- **Swapping translators:** `App` accepts any object with
  `translate(word: str, source_lang: str) -> str`, so an offline dictionary can
  replace `GoogleWordTranslator` by changing one line in `main.py`.
- **Audio timing:** seeking inside variable-bitrate mp3s can be slightly off.
  If clips start early or late, re-encode as constant bitrate
  (`ffmpeg -i in.mp3 -b:a 128k out.mp3`).
- Words are translated individually, without sentence context.

Three behaviours to know about:

- **Language code:** it resets from the filename each time you load a file, so a code you typed by hand won't carry over to the next one.
- **Refresh and Browse:** the dropdown only scans `media/` when the app starts and when you press **Refresh**. I kept **Browse…** for files elsewhere, and it opens in `media/`.
- **Translations panel:** the right-hand translations are not cleared when you switch files, so they build up across the session as a running vocabulary log. If you'd rather it clear on each load, that's a two-line change in `load_file`. Say if you want it.