"""Entry point:  python main.py [path/to/show.fr.srt]"""
import argparse
from pathlib import Path

from lang_reader.audio import SegmentPlayer
from lang_reader.gui import App
from lang_reader.translator import GoogleWordTranslator

MEDIA_DIR = Path(__file__).resolve().parent / "media"


def main() -> None:
    parser = argparse.ArgumentParser(description="Click subtitle words to hear and translate them.")
    parser.add_argument("srt", nargs="?", help="optional .srt file to open at startup")
    args = parser.parse_args()

    MEDIA_DIR.mkdir(exist_ok=True)
    try:
        player = SegmentPlayer()
    except Exception as exc:
        raise SystemExit(f"Could not start audio: {exc}")

    app = App(GoogleWordTranslator(), player, MEDIA_DIR)
    if args.srt:
        app.load_file(args.srt)
    app.mainloop()


if __name__ == "__main__":
    main()
