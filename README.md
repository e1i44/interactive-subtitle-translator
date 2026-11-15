# Local SRT & Audio Language Learning App

A desktop Python application built with PyQt6 for studying audio and subtitles (SRT) in French (`fr`), German (`de`), and Tamil (`ta`).

## Prerequisites

- Python 3.10 or higher
- PyAudio / Qt Multimedia dependencies (handled automatically by PyQt6 wheel on most systems)

## Setup & Running Locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Place your .srt and corresponding .mp3 files in a folder named media/ in the project root directory.

    Naming convention: filename.fr.srt and filename.mp3 (or sharing the same base name).

3. Run the application:
   ```
   python main.py
   ```
