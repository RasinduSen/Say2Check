import cv2
import numpy as np
import pyautogui
import json
import threading
import time
import pyttsx3
import os

# how often to check if the board has moved, in seconds
CHECK_INTERVAL = 2.0

# how different the border region must be to trigger recalibration,
# 0.15 means 15% pixel change in the border region counts as a board move
DRIFT_THRESHOLD = 0.15

# how many pixels wide to sample around the board border for comparison
BORDER_SAMPLE = 20

# how many consecutive checks must confirm drift before recalibrating,
# prevents firing mid-resize while the user is still dragging the window,
# at CHECK_INTERVAL=2s and STABILITY_CHECKS=2 we wait roughly 4s of stable drift
STABILITY_CHECKS = 2

COORDS_FILE = "board_coordinates.json"


def _speak(text):
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 175)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print(f"[WATCHER] TTS error: {e}")


def _load_coords():
    # loading current board coordinates from JSON
    if not os.path.exists(COORDS_FILE):
        return None
    with open(COORDS_FILE, "r") as f:
        return json.load(f)


def _get_board_bbox(coords):
    # deriving board bounding box from coordinates, returning x, y, w, h in screen pixels
    if not coords:
        return None
    xs = [v[0] for v in coords.values()]
    ys = [v[1] for v in coords.values()]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)

    # coords are square centers so adding half a square on each side
    half_sq_w = (x_max - x_min) / 14  # 7 gaps between 8 centers
    half_sq_h = (y_max - y_min) / 14

    x = int(x_min - half_sq_w)
    y = int(y_min - half_sq_h)
    w = int((x_max - x_min) + 2 * half_sq_w)
    h = int((y_max - y_min) + 2 * half_sq_h)
    return x, y, w, h


def _capture_border(bbox):
    # screenshotting just the border strip around the board,
    # comparing borders rather than the full board so piece
    # movements don't trigger false recalibrations
    x, y, w, h = bbox
    screen = pyautogui.screenshot()
    img = np.array(screen)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    sh, sw = img.shape

    # clamping to screen bounds
    x1 = max(0, x - BORDER_SAMPLE)
    y1 = max(0, y - BORDER_SAMPLE)
    x2 = min(sw, x + w + BORDER_SAMPLE)
    y2 = min(sh, y + h + BORDER_SAMPLE)

    border_region = img[y1:y2, x1:x2].copy()

    # blanking out the inner board area so only the border strip remains
    inner_x1 = BORDER_SAMPLE
    inner_y1 = BORDER_SAMPLE
    inner_x2 = border_region.shape[1] - BORDER_SAMPLE
    inner_y2 = border_region.shape[0] - BORDER_SAMPLE

    if inner_x2 > inner_x1 and inner_y2 > inner_y1:
        border_region[inner_y1:inner_y2, inner_x1:inner_x2] = 0

    return border_region


def _compute_drift(ref_frame, current_frame):
    # comparing two border frames, returning drift score between 0.0 and 1.0
    if ref_frame is None or current_frame is None:
        return 0.0

    # resizing to same shape if window was resized
    if ref_frame.shape != current_frame.shape:
        current_frame = cv2.resize(current_frame, (ref_frame.shape[1], ref_frame.shape[0]))

    diff = cv2.absdiff(ref_frame, current_frame)
    # only counting pixels that changed significantly, ignoring minor rendering noise
    _, thresh = cv2.threshold(diff, 25, 1, cv2.THRESH_BINARY)
    changed = thresh.sum()
    total = thresh.size
    return changed / total if total > 0 else 0.0


class BoardWatcher:
    """
    Background thread monitoring the board region every CHECK_INTERVAL seconds.
    If the board has drifted, silently re-runs vision_board_v2.find_board()
    and reloads coordinates into chess_mover. Speaks 'Board updated' on success.
    """

    def __init__(self, on_recalibrate=None):
        # on_recalibrate: optional callback after successful recalibration,
        # receives the new coords dict, use to update the overlay status label
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._stop_event = threading.Event()
        self._on_recalibrate = on_recalibrate
        self._ref_frame = None
        self._bbox = None
        self._lock = threading.Lock()
        self._drift_count = 0

    def start(self):
        # starting the watcher, call after initial calibration is done
        coords = _load_coords()
        if not coords:
            print("[WATCHER] No board_coordinates.json found. Watcher will wait.")
        else:
            self._bbox = _get_board_bbox(coords)
            self._ref_frame = _capture_border(self._bbox)
            print(f"[WATCHER] Started. Checking every {CHECK_INTERVAL}s.")

        self._thread.start()

    def stop(self):
        # stopping the watcher thread cleanly
        self._stop_event.set()
        self._thread.join(timeout=5)
        print("[WATCHER] Stopped.")

    def refresh_reference(self):
        # resetting the reference frame after a manual calibration,
        # prevents the watcher from immediately recalibrating again
        coords = _load_coords()
        if coords:
            with self._lock:
                self._bbox = _get_board_bbox(coords)
                self._ref_frame = _capture_border(self._bbox)
            print("[WATCHER] Reference frame refreshed.")

    def _run(self):
        while not self._stop_event.is_set():
            time.sleep(CHECK_INTERVAL)

            # trying to load coords if no bbox yet, user may have just calibrated
            with self._lock:
                if self._bbox is None:
                    coords = _load_coords()
                    if coords:
                        self._bbox = _get_board_bbox(coords)
                        self._ref_frame = _capture_border(self._bbox)
                    continue

                bbox = self._bbox
                ref = self._ref_frame

            # capturing current border and comparing
            try:
                current = _capture_border(bbox)
                drift = _compute_drift(ref, current)
            except Exception as e:
                print(f"[WATCHER] Capture error: {e}")
                continue

            if drift > DRIFT_THRESHOLD:
                self._drift_count += 1
                print(f"[WATCHER] Drift {drift:.2f} — confirmation {self._drift_count}/{STABILITY_CHECKS}")

                # only recalibrating once the board has been stable in its new
                # position for STABILITY_CHECKS consecutive intervals,
                # preventing firing mid-resize while the window is being dragged
                if self._drift_count >= STABILITY_CHECKS:
                    print("[WATCHER] Drift confirmed stable. Recalibrating...")
                    self._drift_count = 0
                    self._recalibrate()
            else:
                # resetting counter, board is back to normal or drift was transient
                if self._drift_count > 0:
                    print(f"[WATCHER] Drift cleared before threshold, resetting counter.")
                self._drift_count = 0

    def _recalibrate(self):
        # re-running vision_board_v2 silently and reloading coords
        try:
            import vision_board_v2
            # no delay, no preview window, silent background recalibration
            success = vision_board_v2.find_board(delay=0, show_preview=False)

            if success:
                # reloading coords into chess_mover live
                import chess_mover
                new_coords = _load_coords()
                if new_coords:
                    chess_mover.BOARD_COORDS = new_coords

                # resetting reference frame to new board position
                with self._lock:
                    self._bbox = _get_board_bbox(new_coords)
                    self._ref_frame = _capture_border(self._bbox)

                print("[WATCHER] Recalibration successful.")

                # notifying callback to update overlay status label
                if self._on_recalibrate:
                    try:
                        self._on_recalibrate(new_coords)
                    except Exception as e:
                        print(f"[WATCHER] Callback error: {e}")

                # speaking confirmation on a separate thread so watcher doesn't block
                threading.Thread(target=_speak, args=("Board updated",), daemon=True).start()

            else:
                print("[WATCHER] Recalibration failed — board not found. Will retry.")

        except Exception as e:
            print(f"[WATCHER] Recalibration error: {e}")


if __name__ == "__main__":
    print("Board Watcher V2 Test")
    print("Make sure board_coordinates.json exists before running.")
    print("Move your chess window to trigger recalibration.")
    print("Press Ctrl+C to stop.\n")

    def on_recal(coords):
        print(f"[TEST] Recalibrated — {len(coords)} squares updated.")

    watcher = BoardWatcher(on_recalibrate=on_recal)
    watcher.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        watcher.stop()
        print("Done.")