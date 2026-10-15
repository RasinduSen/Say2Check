import cv2
import numpy as np
import pyautogui
import json

COORDS_FILE = "board_coordinates.json"


def _map_squares(x, y, w, h):
    square_w = w / 8
    square_h = h / 8
    files = "abcdefgh"
    ranks = "87654321"
    board_map = {}
    for row_idx, rank in enumerate(ranks):
        for col_idx, file in enumerate(files):
            cx = int(x + col_idx * square_w + square_w / 2)
            cy = int(y + row_idx * square_h + square_h / 2)
            board_map[f"{file}{rank}"] = [cx, cy]
    return board_map


def _score_candidate(gray, x, y, w, h):
    """
    Scoring a candidate rectangle by sampling corner pixels of each square.
    Chess boards always have 2 alternating colors, checking corners
    rather than centers so pieces don't interfere with the score.
    Returns 0.0 to 1.0.
    """
    sq_w = w / 8
    sq_h = h / 8
    THRESHOLD = 25
    alternating = 0
    total = 0

    for row in range(8):
        for col in range(8):
            # sampling corner of square, away from piece centers
            px = int(x + col * sq_w + sq_w * 0.1)
            py = int(y + row * sq_h + sq_h * 0.1)
            px = max(0, min(px, gray.shape[1] - 1))
            py = max(0, min(py, gray.shape[0] - 1))
            val = int(gray[py, px])

            # comparing to right neighbour corner
            if col < 7:
                rx = int(x + (col + 1) * sq_w + sq_w * 0.1)
                ry = py
                rx = max(0, min(rx, gray.shape[1] - 1))
                right = int(gray[ry, rx])
                total += 1
                if abs(val - right) > THRESHOLD:
                    alternating += 1

            # comparing to bottom neighbour corner
            if row < 7:
                bx = px
                by = int(y + (row + 1) * sq_h + sq_h * 0.1)
                by = max(0, min(by, gray.shape[0] - 1))
                below = int(gray[by, bx])
                total += 1
                if abs(val - below) > THRESHOLD:
                    alternating += 1

    return alternating / total if total > 0 else 0.0


def find_board(delay=2, show_preview=True):
    """
    Finding all rectangles on screen and scoring each one by how well
    it matches a checkerboard alternating pattern using corner sampling
    so pieces don't interfere. Taking the highest scoring square candidate.
    Works at startup and mid-game.
    """
    if delay > 0:
        print(f"[V2] Screenshot in {delay}s... Switch to your chess window!")
        pyautogui.sleep(delay)

    screenshot = pyautogui.screenshot()
    img = np.array(screenshot)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # finding candidate rectangles
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 30, 120)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    best_score = 0
    best_box = None

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 15000:
            continue

        x, y, w, h = cv2.boundingRect(cnt)

        # skipping if not roughly square, chess boards are always square
        if abs(w - h) > 0.2 * max(w, h):
            continue

        # skipping if too small to be a board
        if w < 100 or h < 100:
            continue

        score = _score_candidate(gray, x, y, w, h)

        if score > best_score:
            best_score = score
            best_box = (x, y, w, h)

    # requiring at least 55% alternation to accept as a chess board
    if best_box is None or best_score < 0.55:
        print(f"[V2] ERROR: No chessboard found (best score: {best_score:.2f}).")
        print("      Make sure the board is fully visible on screen.")
        return False

    x, y, w, h = best_box
    print(f"[V2] Board found at X={x} Y={y} W={w} H={h} (score={best_score:.2f})")

    board_map = _map_squares(x, y, w, h)

    cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 3)
    for sq, pos in board_map.items():
        cv2.circle(img, (pos[0], pos[1]), 4, (0, 0, 255), -1)

    with open(COORDS_FILE, "w") as f:
        json.dump(board_map, f)
    print(f"[V2] Saved {len(board_map)} squares to '{COORDS_FILE}'")

    if show_preview:
        cv2.imshow("Board Detected (V2)", img)
        print("[V2] Press any key to close...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return True


if __name__ == "__main__":
    success = find_board()
    print("[V2] Success." if success else "[V2] Failed.")