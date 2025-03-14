# Typoer
Improved verison of georgetian3/typoer to fix the suntax error in paragraphs

# Typoer - Realistic Typing Simulation

## Overview
`Typoer` is a Python script that simulates human-like typing with customizable speed, accuracy, typos, and self-corrections. It allows for a realistic and dynamic typing experience.

## Features
- Adjustable **words per minute (WPM)** for different typing speeds.
- Customizable **accuracy level** to control the number of typos.
- **Realistic typo corrections** with backspacing.
- Allows users to **set a start and stop key** for better control.
- Supports **multiple paragraphs** as input.

## Installation
Ensure you have Python installed, then install the required dependency:

```sh
pip install keyboard
```

## Usage
Run the script from the terminal:

```sh
python typoer.py
```

### Input Instructions
1. Enter the text you want to be typed.
   - You can enter **multiple paragraphs** by pressing `Enter` after each one.
   - To finish entering text, press `Ctrl + D` (Linux/macOS) or `Ctrl + Z` (Windows) and `Enter`.
2. Enter your preferred **typing speed (WPM)**.
3. Set the **typing accuracy** (0 to 1, where 1 is perfect accuracy).
4. Choose a **start key** to begin the typing simulation.
5. Choose a **stop key** to interrupt the simulation anytime.

### Example Input
```
Enter the text to be typed:
This is the first paragraph.

This is the second paragraph.
(Press Ctrl + D or Ctrl + Z, then Enter to finish)
```

### Example Configuration
```
Enter typing speed (WPM): 200
Enter typing accuracy (0 to 1): 0.95
Enter key to start typing (default: right arrow): right
Enter key to stop typing (default: escape): escape
```

## Notes
- The script will **wait for the start key** before typing.
- Press the **stop key** anytime to end the typing simulation.
- The script introduces **random typing speeds, typos, and corrections** for a more natural effect.

## License
This project is open-source and available under the MIT License.


