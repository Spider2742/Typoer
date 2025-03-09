import keyboard
import random
from time import sleep

def typoer(text, wpm=100, accuracy=1, backspace_duration=0.1, correction_coefficient=0.4, wait_key='', break_key='escape'):
    """
    Simulates human typing with typos and corrections.

    Args:
        text (str): The text to be typed.
        wpm (int, optional): Average typing speed in words per minute. Defaults to 100.
        accuracy (float, optional): Accuracy of typing (0 to 1). Higher is more accurate. Defaults to 1.
        backspace_duration (float, optional): Time taken for backspace press. Defaults to 0.1.
        correction_coefficient (float, optional): Controls typo correction frequency. Defaults to 0.4.
        wait_key (str, optional): Key to press before starting. Defaults to ''.
        break_key (str, optional): Key to press to stop. Defaults to 'escape'.
    """

    chars = list('abcdefghijklmnopqrstuvwxyz ')  # Include space for paragraphs
    spc = 12 / wpm
    spc_range = 0.8
    spc_low = spc * (1 - spc_range)
    spc_high = spc * (1 + spc_range)

    i = 0
    typos = 0

    if wait_key:
        keyboard.wait(wait_key)

    while i < len(text):
        if keyboard.is_pressed(break_key):
            return

        if typos and (i + typos >= len(text) or random.random() < 1 - correction_coefficient ** typos):
            sleep(backspace_duration)
            for _ in range(typos):
                keyboard.press_and_release('backspace')
                sleep(backspace_duration)
            typos = 0
        elif random.random() > accuracy:
            keyboard.write(random.choice(chars))
            typos += 1
        else:
            keyboard.write(text[i + typos])
            if typos:
                typos += 1
            else:
                i += 1

        duration = random.uniform(spc_low, spc_high)
        sleep(duration)

if __name__ == '__main__':
    text = """YOUR-TEXT-HERE"""
    typoer(text, wpm=120, accuracy=0.8, wait_key='right')