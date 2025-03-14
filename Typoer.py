import keyboard
import random
from time import sleep

def typoer(text, wpm=250, accuracy=0.98, backspace_delay=0.03, correction_chance=1, start_key='', stop_key='escape'):
    """
    Simulates human-like typing with natural speed, typos, and self-corrections.

    Args:
        text (str): The text to type.
        wpm (int, optional): Typing speed in words per minute. Defaults to 250.
        accuracy (float, optional): Accuracy rate (0 to 1). Defaults to 0.98.
        backspace_delay (float, optional): Delay between backspace presses. Defaults to 0.03.
        correction_chance (float, optional): Probability of fixing typos. Defaults to 0.85.
        start_key (str, optional): Key to press before starting. Defaults to ''.
        stop_key (str, optional): Key to press to stop typing. Defaults to 'escape'.
    """
    possible_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ,.!? '  # Expanded character set
    
    sec_per_char = 12 / wpm
    variation = 0.08  # Reduced randomness for more fluid typing
    min_delay = sec_per_char * (1 - variation)
    max_delay = sec_per_char * (1 + variation)

    index = 0
    typo_stack = 0

    if start_key:
        print(f"Press '{start_key}' to start typing...")
        keyboard.wait(start_key)

    print("Typing started. Press '" + stop_key + "' to stop.")
    while index < len(text):
        if keyboard.is_pressed(stop_key):
            print("Typing stopped.")
            return

        # Correct typos naturally
        if typo_stack and (random.random() < correction_chance):
            for _ in range(typo_stack):
                keyboard.press_and_release('backspace')
                sleep(backspace_delay)
            typo_stack = 0
            continue

        # Introduce occasional typos
        if random.random() > accuracy:
            keyboard.write(random.choice(possible_chars))
            typo_stack += 1
        else:
            keyboard.write(text[index])
            index += 1

        # Simulate realistic typing delays
        sleep(random.uniform(min_delay, max_delay))

if __name__ == '__main__':
    print("Enter the text to be typed (type 'END' on a new line to finish):")
    lines = []
    while True:
        line = input()
        if line.strip().upper() == 'END':
            break
        lines.append(line)
    user_text = "\n".join(lines)
    
    user_wpm = int(input("Enter typing speed (WPM): ") or 250)
    user_accuracy = float(input("Enter typing accuracy (0 to 1): ") or 0.98)
    start_key = input("Enter key to start typing (default: right arrow): ") or 'right'
    stop_key = input("Enter key to stop typing (default: escape): ") or 'escape'

    typoer(user_text, wpm=user_wpm, accuracy=user_accuracy, start_key=start_key, stop_key=stop_key)
