import pyautogui
import time

print("--- COORDINATE FINDER ---")
print("Hover your mouse over a chess square (like E2).")
print("Press Ctrl+C in this terminal window to stop.")

try:
    while True:
        # getting current x and y position of the mouse
        x, y = pyautogui.position()

        # overwriting the same line so it doesn't spam, end='\r' returns cursor to start
        print(f"Current Position: X={x}, Y={y}", end='\r')

        # short pause to not overload the CPU
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nDone.")