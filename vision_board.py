import cv2
import numpy as np
import pyautogui
import json

def find_board():
    print("Taking screenshot in 2 seconds... (Switch to your chess window!)")
    # giving the user time to switch windows
    pyautogui.sleep(2)

    # taking a screenshot
    screenshot = pyautogui.screenshot()
    # converting to a numpy array for OpenCV
    img = np.array(screenshot)
    # converting colors from RGB to BGR
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    # converting to grayscale for processing
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # blurring slightly to remove noise
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # running canny edge detection to find grid lines
    edges = cv2.Canny(blur, 50, 150)

    # finding contours
    contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    print(f"Found {len(contours)} shapes on screen...")

    # finding the largest square, which should be the board
    best_square = None
    max_area = 0

    for cnt in contours:
        area = cv2.contourArea(cnt)
        # filtering out small noise, must be bigger than 10,000 pixels
        if area > 10000:
            # approximating the shape to a polygon
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)

            # keeping it if it has 4 corners
            if len(approx) == 4:
                if area > max_area:
                    max_area = area
                    best_square = approx

    if best_square is None:
        print("ERROR: Could not find a chessboard! Make sure the board is visible.")
        return

    # getting x, y, width, height of the detected board
    x, y, w, h = cv2.boundingRect(best_square)
    print(f"Board detected at: X={x}, Y={y}, Width={w}, Height={h}")

    # drawing a box around the board for visual feedback
    cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 3)

    # calculating center coordinates for all 64 squares
    square_size = w / 8
    board_map = {}

    # rank 8 is at the top (low Y value)
    files = "abcdefgh"
    ranks = "87654321"

    for row_idx, rank in enumerate(ranks):
        for col_idx, file in enumerate(files):
            # calculating center of each square
            center_x = int(x + (col_idx * square_size) + (square_size / 2))
            center_y = int(y + (row_idx * square_size) + (square_size / 2))

            square_name = f"{file}{rank}"
            board_map[square_name] = (center_x, center_y)

            # drawing a dot on each center for visual check
            cv2.circle(img, (center_x, center_y), 5, (0, 0, 255), -1)

    # saving coordinates to JSON
    with open("board_coordinates.json", "w") as f:
        json.dump(board_map, f)

    print("Calibration Complete! Coordinates saved to 'board_coordinates.json'")

    # showing the result, press q to close
    cv2.imshow("Detected Board", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    find_board()