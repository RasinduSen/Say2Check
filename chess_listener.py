import speech_recognition as sr
from vosk import Model
import os
import sys
import re
import difflib # <--- The Magic Library (Built-in)

# --- CONFIGURATION ---
if not os.path.exists("model"):
    print("Model folder not found!")
    sys.exit(1)

print("Loading Voice Model...")
vosk_model = Model("model")


# List of words to be listened and relevant comparisons to be made.
VALID_COMMANDS = {
    # Target Word : [List of valid representations]
    "1": ["one", "won", "1"],
    "2": ["two", "to", "too", "2"],
    "3": ["three", "tree", "3"],
    "4": ["four", "for", "fore", "4"],
    "5": ["five", "hive", "fi", "5"],
    "6": ["six", "sex", "6"],
    "7": ["seven", "7"],
    "8": ["eight", "ate", "8"],

    "a": ["a", "alpha", "hey", "ay"],
    "b": ["b", "bravo", "be", "bee"],
    "c": ["c", "charlie", "see", "sea", "si"],
    "d": ["d", "delta", "dee", "the"],
    "e": ["e", "echo", "he", "eat"],
    "f": ["f", "foxtrot", "eff", "if"],
    "g": ["g", "golf", "gee"],
    "h": ["h", "hotel", "age"]
}

def get_fuzzy_match(word):
    best_match = None
    highest_score = 0

    # Flattening the dictionary to a simple list for comparison
    all_targets = []
    for key, variants in VALID_COMMANDS.items():
        for variant in variants:
            all_targets.append((key, variant))

    # Checking similarity for every target
    for real_key, target_word in all_targets:
        # Calculate similarity (0.0 to 1.0)
        score = difflib.SequenceMatcher(None, word, target_word).ratio()

        if score > highest_score:
            highest_score = score
            best_match = real_key

    #Assinging the similarity threshold so that the system only accept if it's at least 60% similar
    if highest_score > 0.6:
        return best_match

    return None

def parse_chess_move(text):
    text = text.lower()
    words = text.split()
    clean_chars = []

    for word in words:
        # 1. Attempting Direct Lookup first
        found = False
        for key, variants in VALID_COMMANDS.items():
            if word in variants:
                clean_chars.append(key)
                found = True
                break

        # 2. If not found, using Fuzzy Logic
        if not found:
            guess = get_fuzzy_match(word)
            if guess:
                print(f"Debug: Fuzzy match '{word}' -> '{guess}'")
                clean_chars.append(guess)

    clean_string = "".join(clean_chars)

    # Looking for [Letter][Number] pair
    match = re.search(r"([a-h][1-8]).*?([a-h][1-8])", clean_string)

    if match:
        start = match.group(1)
        end = match.group(2)
        return start, end

    return None, None