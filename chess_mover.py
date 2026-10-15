import pyautogui
import time
import json
import os

# clicking top-left corner stops the script instantly
pyautogui.FAILSAFE = True

# holding coordinates found by vision_board.py
BOARD_COORDS = {}
CALIBRATION_FILE = "board_coordinates.json"

if os.path.exists(CALIBRATION_FILE):
    try:
        with open(CALIBRATION_FILE, "r") as f:
            BOARD_COORDS = json.load(f)
        print(f"Successfully loaded {len(BOARD_COORDS)} square coordinates.")
    except Exception as e:
        print(f"Error loading calibration file: {e}")
else:
    print("WARNING: 'board_coordinates.json' not found!")
    print("Please run 'vision_board.py' first to calibrate the system.")


def get_square_center(square_name):
    """
    Looks up the (X, Y) pixel coordinates for a given square name (e.g., 'e2').
    """
    # returning none if no board data is loaded
    if not BOARD_COORDS:
        print("Error: No board data loaded. Run calibration first.")
        return None

    # converting to lowercase just in case
    return BOARD_COORDS.get(square_name.lower())


def execute_move(start_square, end_square):
    """
    Moves the mouse to the start square, clicks,
    then moves to the end square and clicks.
    """
    print(f"Attempting move: {start_square} to {end_square}...")

    # getting coordinates for both squares
    start_pos = get_square_center(start_square)
    end_pos = get_square_center(end_square)

    if not start_pos or not end_pos:
        print(f"Error: Could not find coordinates for {start_square} or {end_square}.")
        print("Tip: Did you run calibration? Is the square name correct?")
        return

    # picking up the piece, slight duration to look human and avoid anti-cheat
    pyautogui.moveTo(start_pos[0], start_pos[1], duration=0.4)
    pyautogui.click()

    # dropping the piece
    pyautogui.moveTo(end_pos[0], end_pos[1], duration=0.4)
    pyautogui.click()

    print("Move executed!")


# running this file directly to test mouse movement without the full pipeline
if __name__ == "__main__":
    print("--- AUTOMATION TEST (Dynamic) ---")

    if not BOARD_COORDS:
        print("STOP: You must run 'vision_board.py' first!")
    else:
        print("Type a move like 'e2 e4' (or 'quit' to exit)")

        while True:
            user_input = input("Enter move: ").strip()

            if user_input == "quit":
                break

            try:
                parts = user_input.split()
                if len(parts) == 2:
                    start, end = parts
                    print("Switching to board in 2 seconds...")
                    time.sleep(2)
                    execute_move(start, end)
                else:
                    print("Invalid format. Use: e2 e4")
            except Exception as e:
                print(f"Error: {e}")