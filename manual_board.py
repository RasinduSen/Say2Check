import pyautogui
import json
import time

def manual_calibrate():
    print("Manual Calibration Mode")
    print("finding the Top-Left and Bottom-Right corners of the board.")

    # capturing top-left corner
    input("Hover your mouse over the TOP-LEFT corner of the board (A8) and press Enter...")
    x1, y1 = pyautogui.position()
    print(f"Top-Left captured: ({x1}, {y1})")

    # capturing bottom-right corner
    input("Hover your mouse over the BOTTOM-RIGHT corner of the board (H1) and press Enter...")
    x2, y2 = pyautogui.position()
    print(f"Bottom-Right captured: ({x2}, {y2})")

    # calculating the grid
    width = x2 - x1
    height = y2 - y1

    # checking if selection is roughly square, allowing 50px margin of error
    if abs(width - height) > 50:
        print("WARNING: Your selection isn't a perfect square.")
        print(f"Width: {width}, Height: {height}. Proceeding anyway...")

    square_size = width / 8
    board_map = {}

    files = "abcdefgh"
    ranks = "87654321"

    # generating center points for all 64 squares
    for r_idx, rank in enumerate(ranks):
        for c_idx, file in enumerate(files):
            center_x = int(x1 + (c_idx * square_size) + (square_size / 2))
            center_y = int(y1 + (r_idx * square_size) + (square_size / 2))

            board_map[f"{file}{rank}"] = (center_x, center_y)

    # saving to the same file the other scripts use
    with open("board_coordinates.json", "w") as f:
        json.dump(board_map, f)

    print("Success! 'board_coordinates.json' has been overwritten.")
    print("You can now run 'inference_engine.py' or 'chess_listener.py'.")

if __name__ == "__main__":
    manual_calibrate()