# 🤖 Typoer - Realistic Typing Simulator

> **A modern, feature-rich typing automation tool with GUI, voice control, and cross-platform support**

Simulates **natural human typing behavior** — complete with typos, backspace corrections, variable speed, accuracy control, and full GUI. Perfect for demos, testing, and automation.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.7%2B-blue)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-green)

---

## 🌟 Features

- ✅ **Realistic Typing Simulation**
  - Adjustable **Words Per Minute (WPM)**, from 20 to 400
  - Adjustable **accuracy**, from 50% to 100%, to control typo frequency
  - Typos land on a **neighbouring key**, then get fixed with backspace
  - Uneven key timing, with short pauses at the end of sentences

- ✅ **Types Anything**
  - Preserves line breaks, tabs and blank lines
  - Accents, dashes, curly quotes and other **Unicode characters** are typed too
    (on Linux this needs X11 or XWayland)

- ✅ **🎨 Modern GUI (CustomTkinter)**
  - Editor with live **word count, character count and time estimate**
  - The text **lights up as it is typed**, next to a progress bar and time left
  - One **Start / Stop** button; the window stays responsive while typing
  - **Dark and Light** themes

- ✅ **🎛️ Two Ways to Start**
  - **Hotkey**: set your own **Start Key** (default `f8`) and **Stop Key** (default `escape`)
  - **Countdown**: 3, 5 or 10 seconds to click into the target window
  - Where global hotkeys can't be used (Linux without root), Typoer uses the countdown automatically

- ✅ **🎙️ Voice Commands**
  - Say `"start typing"` or `"stop typing"` to control the simulator
  - Powered by Google Speech Recognition (internet required)

- ✅ **📁 File Import & Export**
  - **Import** a `.txt` file (it replaces the current text)
  - **Export** the text to `.txt`
  - Settings saved to `typoer_settings.json`

- ✅ **🔊 Sound, Always on Top, Tray**
  - Optional sound and spoken status
  - **Always-on-top** window option
  - **Minimise to tray**, or a normal minimise where the desktop has no tray

---

## 🚀 Installation

### 1. Clone the repository
```bash
git clone https://github.com/Spider2742/typoer.git
cd typoer
```

### 2. Install Python dependencies
```bash
pip install --upgrade pip
pip install customtkinter pyautogui keyboard plyer speechrecognition pyaudio pystray pillow pyttsx3
```

> ⚠️ **Linux Users**: You may need input permissions for keyboard/mouse access.
>
> Run:
> ```bash
> sudo usermod -aG input $USER
> ```
> Then **log out and back in**.

---

## 🖥️ Usage (GUI Mode)

### Run the app
```bash
python Typoer.py
```

### Step-by-Step Guide

1. **Enter or Import Text**
   - Type or paste into the editor
   - Or click **Import** to load a `.txt` file

2. **Adjust Settings**
   - `Speed`: typing speed in WPM (e.g., `200`)
   - `Accuracy`: how often a typo is made (e.g., `91%`)
   - `Start with`: **Hotkey** or **Countdown**
   - `Start key` / `Stop key`: any key name, such as `f8`, `escape`, `space` or a single letter

3. **Optional Features**
   - 🔔 **Sound and spoken status**
   - 🎤 **Voice commands** (say "start typing")
   - 📌 **Always on top**
   - 🎨 **Light / Dark** theme

4. **Start Typing**
   - Click **Start** (or press `Ctrl+Enter`)
   - Click into the window where the text should go (e.g., browser, editor)
   - Press your **Start Key**, or wait for the countdown
   - To stop: press your **Stop Key**, click **Stop**, or throw the mouse into a corner of the screen

5. **Extra Tools**
   - 🧹 **Clear**: empty the editor and reset progress
   - 💾 **Export**: save the current text as `.txt`
   - 🔽 **Minimise to tray**: keep running in the background

> 💡 **Tip**: Pick a start key that types nothing, like `f8`. A key such as `space` also lands in the window you are typing into.

---

## 📦 Packaging

### 🪟 Windows: Build `.exe` with PyInstaller
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon=icon.ico --name "Typoer" Typoer.py
```
- Output: `dist/Typoer.exe`
- Distribute the `.exe` — no Python needed!

> 🖼️ Make sure `icon.ico` is in the folder

---

### 🐧 Linux: Build Flatpak (Universal Linux App)

1. Install Flatpak SDK:
```bash
flatpak install flathub org.freedesktop.Platform//22.08 org.freedesktop.Sdk//22.08
```

2. Build and install:
```bash
flatpak-builder \
  --user \
  --install \
  --force-clean \
  build-dir \
  com.spider.Typoer.yml
```

3. Run:
```bash
flatpak run com.spider.Typoer
```

4. (Optional) Export as `.flatpak` bundle:
```bash
flatpak build-export repo build-dir
flatpak build-bundle repo typoer.flatpak com.spider.Typoer
```

Now share `typoer.flatpak` with any Linux user!

---

## 📄 License

MIT © [Spider2742]  
Feel free to use, modify, and distribute. Credit is appreciated but not required.

---

## 📝 Notes

- In **Hotkey** mode, typing waits for the Start Key. In **Countdown** mode it starts when the countdown ends.
- Press the **Stop Key**, click **Stop**, or move the mouse into a screen corner to interrupt.
- **Global hotkeys** come from the `keyboard` module, which needs root on Linux and accessibility
  permission on macOS. Without them, Typoer falls back to the countdown.
- On **Linux**, keystrokes are sent through X11, so the target window has to be an X11 or XWayland app.
- **Voice commands** require:
  - Microphone access
  - Internet (Google Speech API)
- Settings are saved automatically.

---

📬 **Found a bug or want a new feature?**  
👉 [Open an Issue](https://github.com/Spider2742/Typoer/issues)

---

## 🔗 Attribution

This project was inspired by and improves upon the original idea from [georgetian3/typoer](https://github.com/georgetian3/typoer).  
Special thanks to the original author for the concept and initial implementation.
