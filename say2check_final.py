import torch
import sys
import os
import json
import time
import platform
import pyttsx3
import sounddevice as sd
import queue
import threading

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
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton,
    QVBoxLayout, QHBoxLayout, QWidget, QLabel, QGridLayout
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QCursor

# importing local modules
from interference_engine import ChessEye
from chess_listener import parse_chess_move
from chess_mover import execute_move
import vision_board_v2 as vision_board


# when True the voice thread discards all recognised text,
# set True just before TTS speaks, False after it finishes + short buffer
is_speaking = threading.Event()

# reference to the voice thread's audio queue, set when the thread starts,
# speak() uses this to flush captured audio before releasing the lock
_voice_audio_queue = None

def _drain_audio_queue():
    if _voice_audio_queue is None:
        return
    drained = 0
    while not _voice_audio_queue.empty():
        try:
            _voice_audio_queue.get_nowait()
            drained += 1
        except Exception:
            break
    if drained:
        print(f"drained {drained} audio chunks")

def speak(text):
    is_speaking.set()
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 175)
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"TTS error: {e}")
    finally:
        # waiting for TTS audio to finish, then draining whatever the mic
        # captured during that time, drain must happen before clearing the
        # lock so the voice thread can't process stale audio between drain and unlock
        time.sleep(0.3)
        _drain_audio_queue()
        time.sleep(0.15)
        is_speaking.clear()


# handling both "where is ..." and "e2 e4" style commands on one thread
class UnifiedVoiceThread(QThread):
    # signal for piece-location queries
    location_signal = pyqtSignal(str, str)
    # signal for move commands
    move_signal = pyqtSignal(str, str)
    # signal for status bar updates
    status_signal = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.audio_queue = queue.Queue()
        self._running = True

    def callback(self, indata, frames, time_info, status):
        if self._running:
            self.audio_queue.put(bytes(indata))

    def stop(self):
        self._running = False

    def run(self):
        model_path = "model"
        if not os.path.exists(model_path):
            print("model folder not found!")
            self.status_signal.emit("ERROR: model folder missing", "#FF4444")
            return

        model = Model(model_path)

        # tighter word list means fewer mis-recognitions,
        # each square letter has its NATO phonetic alternative
        # so the user can say "alpha four" instead of just "a four",
        # numbers have their most common ASR confusables listed explicitly
        vocab = (
            '["a alpha b bravo c charlie d delta e echo f foxtrot g golf h hotel '
            '1 2 3 4 5 6 7 8 '
            'where is white black '
            'king queen rook bishop knight pawn", "[unk]"]'
        )
        rec = KaldiRecognizer(model, 16000, vocab)
        rec.SetWords(True)

        # rejecting the full utterance if average confidence is too low
        CONFIDENCE_THRESHOLD = 0.72

        # exposing this thread's audio queue so speak() can drain it after TTS
        global _voice_audio_queue
        _voice_audio_queue = self.audio_queue

        self.status_signal.emit("● Listening...", "#00d1b2")
        print("voice thread started")

        with sd.RawInputStream(
                samplerate=16000, blocksize=8000,
                dtype='int16', channels=1,
                callback=self.callback
        ):
            while self._running:
                try:
                    data = self.audio_queue.get(timeout=1)
                except queue.Empty:
                    continue

                if not rec.AcceptWaveform(data):
                    continue

                result = json.loads(rec.Result())
                text = result.get("text", "").lower().strip()
                if not text:
                    continue

                # discarding everything while TTS is speaking,
                # kills the "piece location spoken → heard as move" bug
                if is_speaking.is_set():
                    print(f"discarded while speaking: {text}")
                    continue

                # running confidence filter
                words = result.get("result", [])
                if words:
                    avg_conf = sum(w.get("conf", 0) for w in words) / len(words)
                    if avg_conf < CONFIDENCE_THRESHOLD:
                        print(f"low confidence {avg_conf:.2f}, skipped")
                        continue
                    print(f"heard: {text}")
                else:
                    print(f"heard: {text}")

                # expanding NATO phonetic alphabet to chess letters
                # before passing to parse_chess_move
                nato = {
                    "alpha": "a", "bravo": "b", "charlie": "c",
                    "delta": "d", "echo": "e", "foxtrot": "f",
                    "golf": "g", "hotel": "h"
                }
                words_list = text.split()
                expanded = [nato.get(w, w) for w in words_list]
                text_expanded = " ".join(expanded)

                # branching to location query or move command
                if "where is" in text_expanded:
                    color = (
                        "white" if "white" in text_expanded else
                        "black" if "black" in text_expanded else None
                    )
                    piece = next(
                        (p for p in ["king", "queen", "rook", "bishop", "knight", "pawn"]
                         if p in text_expanded),
                        None
                    )
                    if color and piece:
                        self.status_signal.emit(
                            f"Finding {color} {piece}...", "#f39c12"
                        )
                        self.location_signal.emit(color, piece)
                    else:
                        self.status_signal.emit(
                            "Heard 'where is' — missing color or piece", "#888"
                        )

                else:
                    # requiring both squares with high per-word confidence,
                    # parse_chess_move uses fuzzy matching from chess_listener
                    start, end = parse_chess_move(text_expanded)
                    if start and end:
                        self.status_signal.emit(
                            f"Moving {start.upper()} → {end.upper()}", "#2ecc71"
                        )
                        self.move_signal.emit(start, end)
                    else:
                        print(f"no command: {text_expanded}")


# building the main overlay window
class Say2CheckFinal(QMainWindow):

    def __init__(self):
        super().__init__()

        # loading the CV brain
        print("loading vision model...")
        self.eye = ChessEye()

        self._build_ui()
        self._start_voice()

    def _build_ui(self):
        self.setWindowTitle("Say2Check")
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(340)

        # outer container
        self.container = QWidget()
        self.container.setObjectName("MainFrame")
        self.container.setStyleSheet("""
            QWidget#MainFrame {
                background-color: rgba(13, 17, 23, 245);
                border: 1px solid #30363d;
                border-radius: 12px;
            }
        """)
        self.setCentralWidget(self.container)

        root = QVBoxLayout()
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        # title bar
        title_row = QHBoxLayout()

        title = QLabel("♟ Say2Check")
        title.setFont(QFont("Consolas", 13, QFont.Bold))
        title.setStyleSheet("color: #58a6ff; background: transparent;")
        title_row.addWidget(title)

        title_row.addStretch()

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(26, 26)
        btn_close.setCursor(QCursor(Qt.PointingHandCursor))
        btn_close.setStyleSheet("""
            QPushButton {
                background: transparent; color: #8b949e;
                border: none; font-size: 14px;
            }
            QPushButton:hover { color: #ff7b72; }
        """)
        btn_close.clicked.connect(self.close)
        title_row.addWidget(btn_close)

        root.addLayout(title_row)

        # status label
        self.status_label = QLabel("Initialising...")
        self.status_label.setFont(QFont("Consolas", 10))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFixedHeight(32)
        self.status_label.setStyleSheet("""
            color: #8b949e;
            background: rgba(255,255,255,0.04);
            border: 1px solid #21262d;
            border-radius: 6px;
            padding: 4px 8px;
        """)
        root.addWidget(self.status_label)

        # divider label
        loc_hdr = QLabel("  PIECE LOCATOR")
        loc_hdr.setFont(QFont("Consolas", 8))
        loc_hdr.setStyleSheet("color: #484f58; background: transparent; letter-spacing: 2px;")
        root.addWidget(loc_hdr)

        # 12-button grid, white left black right
        grid = QGridLayout()
        grid.setSpacing(6)

        pieces = ["King", "Queen", "Rook", "Bishop", "Knight", "Pawn"]

        # column headers
        w_hdr = QLabel("WHITE")
        w_hdr.setFont(QFont("Consolas", 8))
        w_hdr.setAlignment(Qt.AlignCenter)
        w_hdr.setStyleSheet("color: #e6edf3; background: transparent; letter-spacing: 1px;")
        grid.addWidget(w_hdr, 0, 0)

        b_hdr = QLabel("BLACK")
        b_hdr.setFont(QFont("Consolas", 8))
        b_hdr.setAlignment(Qt.AlignCenter)
        b_hdr.setStyleSheet("color: #8b949e; background: transparent; letter-spacing: 1px;")
        grid.addWidget(b_hdr, 0, 1)

        PIECE_ICONS = {
            "King": "♔", "Queen": "♕", "Rook": "♖",
            "Bishop": "♗", "Knight": "♘", "Pawn": "♙"
        }

        for i, p in enumerate(pieces):
            icon = PIECE_ICONS[p]

            # white button
            w_btn = QPushButton(f"{icon}  {p}")
            w_btn.setFixedHeight(36)
            w_btn.setCursor(QCursor(Qt.PointingHandCursor))
            w_btn.setFont(QFont("Consolas", 9, QFont.Bold))
            w_btn.setStyleSheet("""
                QPushButton {
                    background-color: #21262d;
                    color: #e6edf3;
                    border: 1px solid #30363d;
                    border-radius: 6px;
                    text-align: left;
                    padding-left: 10px;
                }
                QPushButton:hover {
                    background-color: #2d333b;
                    border-color: #58a6ff;
                    color: #58a6ff;
                }
                QPushButton:pressed { background-color: #161b22; }
            """)
            w_btn.clicked.connect(
                lambda checked, name=p: self._on_locate("white", name)
            )
            grid.addWidget(w_btn, i + 1, 0)

            # black button
            b_btn = QPushButton(f"{icon}  {p}")
            b_btn.setFixedHeight(36)
            b_btn.setCursor(QCursor(Qt.PointingHandCursor))
            b_btn.setFont(QFont("Consolas", 9, QFont.Bold))
            b_btn.setStyleSheet("""
                QPushButton {
                    background-color: #161b22;
                    color: #8b949e;
                    border: 1px solid #21262d;
                    border-radius: 6px;
                    text-align: left;
                    padding-left: 10px;
                }
                QPushButton:hover {
                    background-color: #2d333b;
                    border-color: #f78166;
                    color: #f78166;
                }
                QPushButton:pressed { background-color: #0d1117; }
            """)
            b_btn.clicked.connect(
                lambda checked, name=p: self._on_locate("black", name)
            )
            grid.addWidget(b_btn, i + 1, 1)

        root.addLayout(grid)

        # bottom action row
        action_row = QHBoxLayout()
        action_row.setSpacing(6)

        btn_cal = QPushButton("⊕  Calibrate")
        btn_cal.setFixedHeight(38)
        btn_cal.setCursor(QCursor(Qt.PointingHandCursor))
        btn_cal.setFont(QFont("Consolas", 9, QFont.Bold))
        btn_cal.setStyleSheet("""
            QPushButton {
                background-color: #1f6feb;
                color: white;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #388bfd; }
            QPushButton:pressed { background-color: #1158c7; }
        """)
        btn_cal.clicked.connect(self._on_calibrate)
        action_row.addWidget(btn_cal)

        btn_manual = QPushButton("⊙  Manual Cal")
        btn_manual.setFixedHeight(38)
        btn_manual.setCursor(QCursor(Qt.PointingHandCursor))
        btn_manual.setFont(QFont("Consolas", 9, QFont.Bold))
        btn_manual.setStyleSheet("""
            QPushButton {
                background-color: #21262d;
                color: #8b949e;
                border: 1px solid #30363d;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #2d333b; color: #e6edf3; }
        """)
        btn_manual.clicked.connect(self._on_manual_calibrate)
        action_row.addWidget(btn_manual)

        root.addLayout(action_row)

        # hint text
        hint = QLabel('Say "e2 e4" to move  ·  "where is white king" to find')
        hint.setFont(QFont("Consolas", 7))
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("color: #484f58; background: transparent;")
        hint.setWordWrap(True)
        root.addWidget(hint)

        self.container.setLayout(root)
        self.adjustSize()
        self.move(80, 80)

        # drag support
        self._drag_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self._drag_pos:
            delta = event.globalPos() - self._drag_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self._drag_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    # starting the voice thread
    def _start_voice(self):
        self.v_thread = UnifiedVoiceThread()
        self.v_thread.status_signal.connect(self._update_status)
        self.v_thread.location_signal.connect(self._on_locate)
        self.v_thread.move_signal.connect(self._on_move)
        self.v_thread.start()

    def closeEvent(self, event):
        self.v_thread.stop()
        self.v_thread.quit()
        self.v_thread.wait(2000)
        event.accept()

    def _update_status(self, text, color):
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"""
            color: {color};
            background: rgba(255,255,255,0.04);
            border: 1px solid #21262d;
            border-radius: 6px;
            padding: 4px 8px;
        """)

    def _on_locate(self, color, piece_type):
        """Scanning the board with the CV model and speaking the piece location."""
        self._update_status(f"Scanning for {color} {piece_type}...", "#f39c12")
        QApplication.processEvents()

        board_state = self.eye.scan_board()

        if not board_state:
            speak("I cannot see the board.")
            self._update_status("Board not visible", "#ff7b72")
            return

        target = f"{color}_{piece_type.lower()}"
        found = sorted([sq for sq, pid in board_state.items() if target in pid.lower()])

        if found:
            loc_str = " and ".join(found)
            msg = f"The {color} {piece_type} is at {loc_str}"
            self._update_status(f"Found: {loc_str.upper()}", "#2ecc71")
            speak(msg)
        else:
            self._update_status(f"No {color} {piece_type} found", "#ff7b72")
            speak(f"I don't see any {color} {piece_type}s on the board.")

    def _on_move(self, start, end):
        self._update_status(f"Moving {start.upper()} → {end.upper()}", "#2ecc71")
        QApplication.processEvents()
        execute_move(start, end)
        speak("Move complete")
        QThread.msleep(600)
        self._update_status("● Listening...", "#00d1b2")

    def _on_calibrate(self):
        self._update_status("Auto-scanning board...", "#f39c12")
        QApplication.processEvents()
        try:
            vision_board.find_board()
            import chess_mover
            with open("board_coordinates.json", "r") as f:
                chess_mover.BOARD_COORDS = json.load(f)
            self._update_status("Board calibrated ✓", "#2ecc71")
            speak("Board calibrated.")
        except Exception as e:
            print(f"calibration error: {e}")
            self._update_status("Calibration failed", "#ff7b72")
            speak("Calibration failed.")

    def _on_manual_calibrate(self):
        self._update_status("Manual calibration started...", "#f39c12")
        QApplication.processEvents()
        try:
            import manual_board
            manual_board.manual_calibrate()
            import chess_mover
            with open("board_coordinates.json", "r") as f:
                chess_mover.BOARD_COORDS = json.load(f)
            self._update_status("Manual calibration done ✓", "#2ecc71")
            speak("Manual calibration complete.")
        except Exception as e:
            print(f"manual cal error: {e}")
            self._update_status("Manual calibration failed", "#ff7b72")


if __name__ == "__main__":
    print("Say2Check starting...")

    app = QApplication(sys.argv)
    app.setApplicationName("Say2Check")

    window = Say2CheckFinal()
    window.show()

    speak("Say2Check ready.")
    print("ready")

    sys.exit(app.exec_())