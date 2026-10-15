import sys
import time
import json
import pyautogui
import pyttsx3

from PyQt5.QtCore import Qt, pyqtSignal, QObject, QThread
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton
from PyQt5.QtGui import QFont, QCursor

import chess_listener
import chess_mover
import vision_board

# initializing text-to-speech
def speak(text):
    try:
        engine = pyttsx3.init()
        # speeding up the voice slightly since default is slow
        engine.setProperty('rate', 170)
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"TTS Error: {e}")


# running the voice listener on a separate thread
class VoiceWorker(QObject):
    text_update = pyqtSignal(str, str)

    def run_listener(self):
        self.text_update.emit("Status: Calibrating Mic...", "yellow")

        import speech_recognition as sr
        from vosk import KaldiRecognizer

        recognizer = sr.Recognizer()
        recognizer.pause_threshold = 0.4
        recognizer.non_speaking_duration = 0.3

        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            self.text_update.emit("Status: Ready", "white")
            speak("System Ready")

            # strict grammar list to limit recognition to chess-relevant words
            grammar_list = ["one", "won", "two", "to", "too", "three", "tree", "four", "for",
                            "five", "hive", "six", "seven", "eight", "ate",
                            "a", "alpha", "hey", "b", "bravo", "be", "c", "charlie", "see", "sea",
                            "d", "delta", "dee", "e", "echo", "he", "eat", "f", "foxtrot", "eff",
                            "g", "golf", "gee", "h", "hotel", "quit", "move", "go", "capture", "[unk]"
                            ]

            grammar_str = str(grammar_list).replace("'", '"').lower()
            rec = KaldiRecognizer(chess_listener.vosk_model, 16000, grammar_str)

            while True:
                try:
                    self.text_update.emit("● Listening...", "#FF4444")
                    try:
                        audio = recognizer.listen(source, timeout=1.0, phrase_time_limit=3.0)
                    except sr.WaitTimeoutError:
                        self.text_update.emit("Status: Idle", "gray")
                        continue

                    self.text_update.emit("● Processing...", "#FFFF00")
                    data = audio.get_raw_data(convert_rate=16000, convert_width=2)

                    if rec.AcceptWaveform(data):
                        result = json.loads(rec.Result())
                        text = result.get("text", "")

                        if text:
                            print(f"RAW INPUT: {text}")

                            if "quit" in text:
                                self.text_update.emit("Status: Quitting...", "red")
                                speak("Goodbye")
                                break

                            start, end = chess_listener.parse_chess_move(text)

                            if start and end:
                                self.text_update.emit(f"Action: {start} -> {end}", "#00FF00")
                                # converting e.g. "e2" to "E Two" for clearer audio
                                speak(f"Moving {start} to {end}")
                                chess_mover.execute_move(start, end)
                                time.sleep(0.5)
                            else:
                                self.text_update.emit(f"Ignored: '{text}'", "gray")

                except Exception as e:
                    print(f"Error in listener: {e}")


# building the overlay window
class OverlayWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(100, 100, 400, 200)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_widget.setStyleSheet("background-color: rgba(0, 0, 0, 220); border-radius: 15px;")

        layout = QVBoxLayout()

        self.label_title = QLabel("Say2Check")
        self.label_title.setFont(QFont("Arial", 16, QFont.Bold))
        self.label_title.setStyleSheet("color: white; background: transparent;")
        self.label_title.setAlignment(Qt.AlignCenter)

        self.label_status = QLabel("Initializing...")
        self.label_status.setFont(QFont("Arial", 14, QFont.Bold))
        self.label_status.setStyleSheet("color: gray; background: transparent;")
        self.label_status.setAlignment(Qt.AlignCenter)

        self.btn_calibrate = QPushButton("Recalibrate Board")
        self.btn_calibrate.setFont(QFont("Arial", 10, QFont.Bold))
        self.btn_calibrate.setStyleSheet("background-color: #444; color: white; padding: 8px; border-radius: 5px;")
        self.btn_calibrate.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_calibrate.clicked.connect(self.run_calibration)

        layout.addWidget(self.label_title)
        layout.addWidget(self.label_status)
        layout.addWidget(self.btn_calibrate)
        self.central_widget.setLayout(layout)
        self.old_pos = None

    def update_status(self, text, color):
        self.label_status.setText(text)
        self.label_status.setStyleSheet(f"color: {color}; background: transparent;")

    def run_calibration(self):
        self.update_status("Calibrating...", "yellow")
        QApplication.processEvents()
        try:
            vision_board.find_board()
            with open("board_coordinates.json", "r") as f:
                chess_mover.BOARD_COORDS = json.load(f)
            self.update_status("Board Updated!", "#00FF00")
            speak("Board calibrated")
        except Exception as e:
            self.update_status("Calibration Failed", "red")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = event.globalPos() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OverlayWindow()
    window.show()
    thread = QThread()
    worker = VoiceWorker()
    worker.moveToThread(thread)
    thread.started.connect(worker.run_listener)
    worker.text_update.connect(window.update_status)
    thread.start()
    sys.exit(app.exec_())