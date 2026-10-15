import torch
import sys
import os
import json
import pyttsx3
import ctypes
import platform
import sounddevice as sd
import queue

from vosk import Model, KaldiRecognizer
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout,
                             QWidget, QLabel, QGridLayout)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

# importing the inference engine
from interference_engine import ChessEye

# fixing Windows DLL path for torch
if platform.system() == "Windows":
    try:
        from importlib.util import find_spec
        spec = find_spec("torch")
        if spec:
            lib_path = os.path.join(os.path.dirname(spec.origin), "lib")
            if hasattr(os, "add_dll_directory"):
                os.add_dll_directory(lib_path)
    except Exception: pass

def speak(text):
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 180)
        engine.say(text)
        engine.runAndWait()
    except Exception: pass


# trigger-based voice listener thread
class VoiceThread(QThread):
    command_heard = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.audio_queue = queue.Queue()

    def callback(self, indata, frames, time, status):
        self.audio_queue.put(bytes(indata))

    def run(self):
        model_path = "model"
        if not os.path.exists(model_path):
            print("ERROR: 'model' folder not found!")
            return

        model = Model(model_path)
        # vocabulary focused on the trigger and chess terms only
        vocabulary = '["where is white black king queen rook bishop knight pawn", "[unk]"]'
        rec = KaldiRecognizer(model, 16000, vocabulary)

        with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                               channels=1, callback=self.callback):
            print("standby: say 'where is the [color] [piece]'")

            while True:
                data = self.audio_queue.get()
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    text = result.get("text", "").lower()

                    # checking for the where is trigger
                    if "where is" in text:
                        print(f"command detected: {text}")

                        # identifying color
                        color = "white" if "white" in text else "black" if "black" in text else None

                        # identifying piece
                        piece = None
                        for p in ["king", "queen", "rook", "bishop", "knight", "pawn"]:
                            if p in text:
                                piece = p
                                break

                        if piece and color:
                            print(f"executing: {color.upper()} {piece.upper()}")
                            self.command_heard.emit(color, piece)
                        else:
                            print("heard trigger but missing color or piece name")


class VoiceLocatorOverlay(QMainWindow):
    def __init__(self):
        super().__init__()
        self.eye = ChessEye()
        self.initUI()

        self.v_thread = VoiceThread()
        self.v_thread.command_heard.connect(self.process_request)
        self.v_thread.start()

    def initUI(self):
        self.setWindowTitle("Say2Check Voice Finder")
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setGeometry(100, 100, 400, 500)
        self.setStyleSheet("background-color: #1a1a1a; color: white;")

        layout = QVBoxLayout()
        self.status_label = QLabel("Waiting for: 'Where is...'")
        self.status_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #00d1b2; margin: 20px;")
        layout.addWidget(self.status_label)

        grid = QGridLayout()
        pieces = ["King", "Queen", "Rook", "Bishop", "Knight", "Pawn"]

        for i, p in enumerate(pieces):
            # white buttons
            w_btn = QPushButton(f"W {p}")
            w_btn.setFixedHeight(40)
            w_btn.setStyleSheet("background-color: #f1f1f1; color: #111; font-weight: bold;")
            w_btn.clicked.connect(lambda checked, name=p: self.process_request("white", name))
            grid.addWidget(w_btn, i, 0)

            # black buttons
            b_btn = QPushButton(f"B {p}")
            b_btn.setFixedHeight(40)
            b_btn.setStyleSheet("background-color: #333; color: white; font-weight: bold;")
            b_btn.clicked.connect(lambda checked, name=p: self.process_request("black", name))
            grid.addWidget(b_btn, i, 1)

        layout.addLayout(grid)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def process_request(self, color, piece_type):
        self.status_label.setText(f"Scanning: {color} {piece_type}")
        QApplication.processEvents()

        # scanning the board with the inference engine
        board_state = self.eye.scan_board()

        if not board_state:
            speak("I can't see the board.")
            return

        found = []
        target = f"{color}_{piece_type.lower()}"

        for square, piece_id in board_state.items():
            if target in piece_id.lower():
                found.append(square)

        if found:
            found.sort()
            loc_str = " and ".join(found)
            msg = f"The {color} {piece_type} is at {loc_str}"
            self.status_label.setText(f"Found: {loc_str}")
            speak(msg)
        else:
            self.status_label.setText("Not found")
            speak(f"I don't see any {color} {piece_type}s.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VoiceLocatorOverlay()
    window.show()
    sys.exit(app.exec_())