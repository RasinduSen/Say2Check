import torch
import sys
import os
import json
import pyttsx3
import ctypes
import platform
import sounddevice as sd
import queue
import re

# fixing Windows DLL path for torch
if platform.system() == "Windows":
    try:
        from importlib.util import find_spec
        spec = find_spec("torch")
        if spec:
            lib_path = os.path.join(os.path.dirname(spec.origin), "lib")
            if hasattr(os, "add_dll_directory"):
                os.add_dll_directory(lib_path)
    except Exception:
        pass

from vosk import Model, KaldiRecognizer
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout,
                             QWidget, QLabel, QGridLayout, QHBoxLayout)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

# importing the inference engine
from interference_engine import ChessEye

def speak(text):
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 180)
        engine.say(text)
        engine.runAndWait()
    except Exception:
        pass


# voice listener thread
class IntegratedVoiceThread(QThread):
    move_signal = pyqtSignal(str)
    location_signal = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.audio_queue = queue.Queue()

    def callback(self, indata, frames, time, status):
        self.audio_queue.put(bytes(indata))

    def run(self):
        model_path = "model"
        if not os.path.exists(model_path):
            print("VOSK ERROR: 'model' folder not found!")
            return

        model = Model(model_path)
        vocab = '["a b c d e f g h 1 2 3 4 5 6 7 8 where is white black king queen rook bishop knight pawn", "[unk]"]'
        rec = KaldiRecognizer(model, 16000, vocab)

        with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                               channels=1, callback=self.callback):
            print("voice system ready")
            while True:
                data = self.audio_queue.get()
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    text = result.get("text", "").lower()
                    if not text: continue

                    # branching to location query or move command
                    if "where is" in text:
                        color = "white" if "white" in text else "black" if "black" in text else None
                        piece = next((p for p in ["king", "queen", "rook", "bishop", "knight", "pawn"] if p in text), None)
                        if color and piece:
                            self.location_signal.emit(color, piece)
                    else:
                        # stripping spaces and extracting square coordinates
                        clean_text = text.replace(" ", "")
                        move_match = re.findall(r'[a-h][1-8]', clean_text)
                        if len(move_match) >= 2:
                            self.move_signal.emit("".join(move_match[:2]))


# main integrated overlay window
class IntegratedOverlay(QMainWindow):
    def __init__(self):
        super().__init__()
        # loading the AI brain
        self.eye = ChessEye()

        self.initUI()

        # starting voice thread after UI and AI are ready
        self.v_thread = IntegratedVoiceThread()
        self.v_thread.location_signal.connect(self.process_location)
        self.v_thread.move_signal.connect(self.process_move)
        self.v_thread.start()

    def initUI(self):
        self.setWindowTitle("Say2Check Integrated Master")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(100, 100, 380, 600)

        self.container = QWidget()
        self.container.setObjectName("MainFrame")
        self.container.setStyleSheet("""
            QWidget#MainFrame {
                background-color: rgba(20, 20, 25, 240);
                border: 2px solid #00d1b2;
                border-radius: 15px;
            }
            QLabel { color: white; border: none; }
            QPushButton {
                background-color: #2c3e50; color: white;
                border-radius: 8px; font-weight: bold; padding: 10px;
            }
            QPushButton:hover { background-color: #34495e; border: 1px solid #00d1b2; }
        """)

        layout = QVBoxLayout()
        self.status_label = QLabel("SYSTEM INITIALIZED")
        self.status_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #00d1b2; margin: 10px;")
        layout.addWidget(self.status_label)

        # 12-button grid
        grid = QGridLayout()
        pieces = ["King", "Queen", "Rook", "Bishop", "Knight", "Pawn"]
        for i, p in enumerate(pieces):
            w_btn = QPushButton(f"W {p}")
            w_btn.setStyleSheet("background-color: #ecf0f1; color: #2c3e50;")
            w_btn.clicked.connect(lambda checked, name=p: self.process_location("white", name))
            grid.addWidget(w_btn, i, 0)

            b_btn = QPushButton(f"B {p}")
            b_btn.setStyleSheet("background-color: #333; color: white;")
            b_btn.clicked.connect(lambda checked, name=p: self.process_location("black", name))
            grid.addWidget(b_btn, i, 1)
        layout.addLayout(grid)

        # action row
        action_layout = QHBoxLayout()

        self.btn_cal = QPushButton("AUTO-CALIBRATE")
        self.btn_cal.setFixedHeight(50)
        self.btn_cal.setStyleSheet("background-color: #27ae60;")
        self.btn_cal.clicked.connect(self.run_auto_calibration)
        action_layout.addWidget(self.btn_cal)

        self.btn_exit = QPushButton("EXIT")
        self.btn_exit.setFixedHeight(50)
        self.btn_exit.setStyleSheet("background-color: #c0392b;")
        self.btn_exit.clicked.connect(self.close)
        action_layout.addWidget(self.btn_exit)

        layout.addLayout(action_layout)
        self.container.setLayout(layout)
        self.setCentralWidget(self.container)

    def run_auto_calibration(self):
        self.status_label.setText("AUTO-SCANNING...")
        QApplication.processEvents()
        os.system("python vision_board.py")
        self.status_label.setText("SYSTEM ACTIVE")
        speak("Board detected.")

    def process_location(self, color, piece_type):
        self.status_label.setText(f"FINDING {piece_type.upper()}")
        QApplication.processEvents()
        board_state = self.eye.scan_board()
        target = f"{color}_{piece_type.lower()}"
        found = [sq for sq, pid in board_state.items() if target in pid.lower()]

        if found:
            locs = " and ".join(sorted(found))
            speak(f"{color} {piece_type} is at {locs}")
            self.status_label.setText(f"FOUND: {locs}")
        else:
            speak(f"No {color} {piece_type} found.")

    def process_move(self, move_str):
        self.status_label.setText(f"PLAYING: {move_str}")
        os.system(f"python play_move.py {move_str}")

    def mousePressEvent(self, event): self.old_pos = event.globalPos()
    def mouseMoveEvent(self, event):
        delta = event.globalPos() - self.old_pos
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.old_pos = event.globalPos()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # processing events to prevent "Not Responding" freeze during heavy init
    print("Say2Check starting up...")

    window = IntegratedOverlay()

    app.processEvents()

    window.show()
    print("system ready and listening")
    sys.exit(app.exec_())