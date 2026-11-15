import os
import re
import pysrt

def get_available_media(media_dir: str):
    if not os.path.exists(media_dir):
        return [], []
    
    files = os.listdir(media_dir)
    srt_files = [f for f in files if f.endswith('.srt')]
    audio_files = [f for f in files if f.endswith('.mp3') or f.endswith('.wav')]
    
    return srt_files, audio_files

def time_to_seconds(t):
    return t.hours * 3600 + t.minutes * 60 + t.seconds + t.milliseconds / 1000.0

def parse_srt_file(file_path: str):
    if not os.path.exists(file_path):
        return []
        
    subs = pysrt.open(file_path, encoding='utf-8')
    parsed_subtitles = []
    
    for sub in subs:
        start_sec = time_to_seconds(sub.start)
        end_sec = time_to_seconds(sub.end)
        text = sub.text.replace('\n', ' ')
        
        words_raw = text.split(' ')
        words = []
        for w in words_raw:
            if w.strip():
                clean_word = re.sub(r'[^\w\s]', '', w)
                words.append({
                    "raw": w,
                    "clean": clean_word
                })
        
        parsed_subtitles.append({
            "index": sub.index,
            "start": start_sec,
            "end": end_sec,
            "words": words
        })
        
    return parsed_subtitles