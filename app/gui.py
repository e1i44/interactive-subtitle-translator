import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
    QComboBox, QSlider, QTextBrowser, QSplitter, QGroupBox, 
    QFormLayout
)
from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

from app.srt_parser import get_available_media, parse_srt_file
from app.translator_service import translate_word

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SRT Audio & Translation App")
        self.resize(1100, 700)

        self.media_dir = os.path.join(os.path.dirname(__file__), "../media")
        os.makedirs(self.media_dir, exist_ok=True)

        self.current_subtitles = []
        self.current_audio_path = ""
        self.audio_timer = QTimer(self)
        self.audio_timer.setSingleShot(True)
        self.audio_timer.timeout.connect(self.stop_audio_segment)

        # Multimedia setup
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(1.0)

        self.init_ui()
        self.load_media_list()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # Left Sidebar for Settings & Controls
        sidebar = QWidget()
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar.setFixedWidth(280)

        settings_group = QGroupBox("Settings")
        form_layout = QFormLayout(settings_group)

        self.file_combo = QComboBox()
        self.file_combo.currentIndexChanged.connect(self.on_file_selected)
        form_layout.addRow("Media File:", self.file_combo)

        self.lang_combo = QComboBox()
        self.lang_combo.addItem("French (fr)", "fr")
        self.lang_combo.addItem("German (de)", "de")
        self.lang_combo.addItem("Tamil (ta)", "ta")
        form_layout.addRow("Language:", self.lang_combo)

        self.font_slider = QSlider(Qt.Orientation.Horizontal)
        self.font_slider.setRange(10, 32)
        self.font_slider.setValue(16)
        self.font_slider.valueChanged.connect(self.on_font_size_changed)
        form_layout.addRow("Font Size:", self.font_slider)

        self.vol_slider = QSlider(Qt.Orientation.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(100)
        self.vol_slider.valueChanged.connect(self.on_volume_changed)
        form_layout.addRow("Volume:", self.vol_slider)

        sidebar_layout.addWidget(settings_group)
        sidebar_layout.addStretch()

        # Splitter for Main Two Panels
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left Panel: Subtitles Text Browser
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.addWidget(QLabel("<b>Subtitles</b>"))
        
        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(False)
        self.text_browser.anchorClicked.connect(self.on_word_clicked)
        self.text_browser.setStyleSheet("""
            QTextBrowser {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 10px;
                font-size: 16px;
                line-height: 1.6;
            }
            a.word {
                color: black;
                text-decoration: none;
                padding: 1px 2px;
                border-radius: 3px;
            }
            a.word:hover {
                background-color: #007bff;
                color: white;
            }
        """)
        left_layout.addWidget(self.text_browser)

        # Right Panel: Translation Display
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.addWidget(QLabel("<b>Translation</b>"))

        self.translation_label = QLabel("Click any word on the left to see its English translation.")
        self.translation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.translation_label.setStyleSheet("""
            QLabel {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 20px;
                color: #007bff;
                padding: 20px;
            }
        """)
        right_layout.addWidget(self.translation_label)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([600, 400])

        main_layout.addWidget(sidebar)
        main_layout.addWidget(splitter)

    def load_media_list(self):
        srt_files, audio_files = get_available_media(self.media_dir)
        self.file_combo.clear()
        self.file_combo.addItem("-- Select Base Name --", "")

        base_names = set()
        for f in srt_files:
            base = f.replace('.fr.srt', '').replace('.de.srt', '').replace('.ta.srt', '').replace('.srt', '')
            base_names.add(base)

        for base in sorted(base_names):
            self.file_combo.addItem(base, base)

    def on_file_selected(self, index):
        base = self.file_combo.currentData()
        if not base:
            return

        srt_files, audio_files = get_available_media(self.media_dir)
        
        matched_srt = None
        lang = "fr"
        for f in srt_files:
            if f.startswith(base):
                matched_srt = f
                if ".fr" in f: lang = "fr"
                elif ".de" in f: lang = "de"
                elif ".ta" in f: lang = "ta"
                break

        matched_audio = None
        for f in audio_files:
            if f.startswith(base):
                matched_audio = f
                break

        # Set language combo selection
        for i in range(self.lang_combo.count()):
            if self.lang_combo.itemData(i) == lang:
                self.lang_combo.setCurrentIndex(i)
                break

        if matched_srt:
            file_path = os.path.join(self.media_dir, matched_srt)
            self.current_subtitles = parse_srt_file(file_path)
            self.render_subtitles()

        if matched_audio:
            self.current_audio_path = os.path.join(self.media_dir, matched_audio)
            self.player.setSource(QUrl.fromLocalFile(self.current_audio_path))

    def render_subtitles(self):
        if not self.current_subtitles:
            self.text_browser.setHtml("<p style='color: #888;'>No subtitles found.</p>")
            return

        html_parts = []
        for sub in self.current_subtitles:
            time_str = f"[{self.format_time(sub['start'])} -> {self.format_time(sub['end'])}]"
            html_parts.append(f"<div style='margin-bottom: 10px;'><span style='color: #888; font-size: 11px;'>{time_str}</span><br>")
            
            for w in sub['words']:
                # Anchor format: word:clean_word|start_sec|end_sec
                href = f"word:{w['clean']}|{sub['start']}|{sub['end']}"
                html_parts.append(f"<a class='word' href='{href}'>{w['raw']}</a> ")
            
            html_parts.append("</div>")

        self.text_browser.setHtml("".join(html_parts))

    def on_word_clicked(self, url: QUrl):
        scheme = url.scheme()
        if scheme == "word":
            path = url.path() # clean_word|start|end
            try:
                parts = path.split('|')
                clean_word = parts[0]
                start_sec = float(parts[1])
                end_sec = float(parts[2])

                self.play_audio_segment(start_sec, end_sec)
                self.fetch_and_show_translation(clean_word)
            except Exception as e:
                print("Error handling click:", e)

    def play_audio_segment(self, start, end):
        if not self.current_audio_path:
            return

        if self.audio_timer.isActive():
            self.audio_timer.stop()

        self.player.setPosition(int(start * 1000))
        self.player.play()

        duration_ms = int((end - start) * 1000)
        if duration_ms > 0:
            self.audio_timer.start(duration_ms)

    def stop_audio_segment(self):
        self.player.pause()

    def fetch_and_show_translation(self, word):
        if not word.strip():
            return

        source_lang = self.lang_combo.currentData()
        translation = translate_word(word, source_lang, "en")
        
        self.translation_label.setText(f"<div style='font-size: 28px; font-weight: bold; color: #007bff; margin-bottom: 10px;'>{translation}</div><div style='font-size: 16px; color: #555;'>Original: <b>{word}</b></div>")

    def on_font_size_changed(self, value):
        self.text_browser.setStyleSheet(f"""
            QTextBrowser {{
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 10px;
                font-size: {value}px;
                line-height: 1.6;
            }}
            a.word {{
                color: black;
                text-decoration: none;
                padding: 1px 2px;
                border-radius: 3px;
            }}
            a.word:hover {{
                background-color: #007bff;
                color: white;
            }}
        """)

    def on_volume_changed(self, value):
        self.audio_output.setVolume(value / 100.0)

    def format_time(self, seconds):
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"