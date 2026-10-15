import torch
import sys
import os
import pyttsx3
import ctypes
import platform
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QGridLayout
from PyQt5.QtCore import Qt

# fixing Windows DLL path for torch
if platform.system() == "Windows":
    try:
        from importlib.util import find_spec
        spec = find_spec("torch")
        if spec:
            lib_path = os.path.join(os.path.dirname(spec.origin), "lib")
            os.add_dll_directory(lib_path)
    except Exception:
        pass

# importing the inference engine
from interference_engine import ChessEye

def speak(text):
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 175)
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"TTS Error: {e}")


class FeedbackChecker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.eye = ChessEye()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Say2Check: 12-Piece Feedback Test")
        self.setGeometry(100, 100, 500, 600)
        self.setStyleSheet("background-color: #121212; color: white;")

        main_layout = QVBoxLayout()

        self.label = QLabel("Click a specific piece to locate")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("color: #00d1b2; font-size: 14px; margin: 10px;")
        main_layout.addWidget(self.label)

        grid = QGridLayout()
        pieces = ["King", "Queen", "Rook", "Bishop", "Knight", "Pawn"]

        # white pieces section
        white_label = QLabel("WHITE PIECES")
        white_label.setStyleSheet("font-weight: bold; color: #ecf0f1; margin-top: 10px;")
        grid.addWidget(white_label, 0, 0, 1, 3, Qt.AlignCenter)

        for i, p in enumerate(pieces):
            btn = QPushButton(f"W {p}")
            btn.setFixedHeight(45)
            btn.setStyleSheet("background-color: #f1f1f1; color: #333; font-weight: bold; border-radius: 5px;")
            btn.clicked.connect(lambda checked, name=p: self.process_logic("white", name))
            grid.addWidget(btn, (i // 3) + 1, i % 3)

        # black pieces section
        black_label = QLabel("BLACK PIECES")
        black_label.setStyleSheet("font-weight: bold; color: #7f8c8d; margin-top: 20px;")
        grid.addWidget(black_label, 3, 0, 1, 3, Qt.AlignCenter)

        for i, p in enumerate(pieces):
            btn = QPushButton(f"B {p}")
            btn.setFixedHeight(45)
            btn.setStyleSheet("background-color: #34495e; color: white; font-weight: bold; border-radius: 5px;")
            btn.clicked.connect(lambda checked, name=p: self.process_logic("black", name))
            grid.addWidget(btn, (i // 3) + 4, i % 3)

        main_layout.addLayout(grid)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def process_logic(self, color, piece_type):
        self.label.setText(f"Scanning for {color} {piece_type}...")
        QApplication.processEvents()

        board_state = self.eye.scan_board()

        if not board_state:
            speak("I cannot see the board.")
            return

        found_squares = []
        # building search term like "white_king" or "black_pawn"
        target = f"{color}_{piece_type.lower()}"

        for square, piece_id in board_state.items():
            if target in piece_id.lower():
                found_squares.append(square)

        if found_squares:
            found_squares.sort()
            loc_text = " and ".join(found_squares)
            response = f"The {color} {piece_type} is at {loc_text}"
            self.label.setText(f"Found: {loc_text}")
            speak(response)
        else:
            response = f"I do not see any {color} {piece_type}s."
            self.label.setText("Not found.")
            speak(response)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FeedbackChecker()
    window.show()
    sys.exit(app.exec_())