import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import json
import pyautogui
import os
import time

MODEL_PATH = "chess_ai.pth"
CLASS_NAMES_PATH = "class_names.txt"
COORDS_PATH = "board_coordinates.json"

class ChessEye:
    def __init__(self):
        self.model = None
        self.class_names = []
        # using GPU if available, otherwise falling back to CPU
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.load_brain()

    def load_brain(self):
        """Loads the trained AI model."""
        if not os.path.exists(MODEL_PATH) or not os.path.exists(CLASS_NAMES_PATH):
            print("ERROR: AI Model or Class Names not found!")
            print("Did you run 'train_ai.py'?")
            return

        # loading class names
        with open(CLASS_NAMES_PATH, "r") as f:
            self.class_names = [line.strip() for line in f.readlines()]

        # rebuilding the MobileNetV2 architecture
        print(f"Loading AI Brain on {self.device}...")
        self.model = models.mobilenet_v2(weights=None)

        # modifying the last layer to match our number of chess pieces
        num_ftrs = self.model.classifier[1].in_features
        self.model.classifier[1] = nn.Linear(num_ftrs, len(self.class_names))

        # loading weights
        try:
            self.model.load_state_dict(torch.load(MODEL_PATH, map_location=self.device))
            self.model.to(self.device)
            self.model.eval()

            # defining image transformations, must match training
            self.transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
            ])
            print("AI Brain Loaded Successfully.")
        except Exception as e:
            print(f"Failed to load model: {e}")
            self.model = None

    def predict_piece(self, img):
        """Identifying the piece in a single square image."""
        if not self.model: return "unknown"

        # preprocessing the image
        img_t = self.transform(img).unsqueeze(0).to(self.device)

        # running the prediction
        with torch.no_grad():
            output = self.model(img_t)
            _, predicted_idx = torch.max(output, 1)

        return self.class_names[predicted_idx.item()]

    def scan_board(self):
        """Taking a screenshot and mapping every square to a piece."""
        if not os.path.exists(COORDS_PATH):
            print("Error: Board coordinates not found. Please Recalibrate.")
            return {}

        with open(COORDS_PATH, "r") as f:
            coords = json.load(f)

        screen = pyautogui.screenshot()

        # collecting distance between a1 and a2 to estimate square size
        if "a1" in coords and "a2" in coords:
            # calculating the distance
            h = abs(coords["a1"][1] - coords["a2"][1])
            radius = int(h / 2.5)
        else:
            radius = 25

        board_state = {}

        for square, pos in coords.items():
            cx, cy = pos

            # cropping the square
            box = (cx - radius, cy - radius, cx + radius, cy + radius)
            square_img = screen.crop(box)

            # asking the AI to identify the piece
            piece_name = self.predict_piece(square_img)
            board_state[square] = piece_name

        return board_state


if __name__ == "__main__":
    print("Switch to your Chess Window! Scanning in 3 seconds...")
    time.sleep(3)

    eye = ChessEye()
    current_state = eye.scan_board()

    print("\nDetected Board:")
    files = "abcdefgh"
    ranks = "87654321"

    for rank in ranks:
        row = f"{rank} | "
        for file in files:
            sq = f"{file}{rank}"
            piece = current_state.get(sq, "unknown")

            # formatting for display
            if "empty" in piece:
                short = " . "
            else:
                # e.g. "white_pawn" -> "WP"
                parts = piece.split("_")
                if len(parts) >= 2:
                    color = parts[0][0].upper()
                    role = parts[1][0].upper()
                    # fixing knight abbreviation to N
                    if "knight" in piece: role = "N"
                    short = f"{color}{role} "
                else:
                    short = "??"
            row += short
        print(row)
    print("    ------------------------")
    print("     a  b  c  d  e  f  g  h")