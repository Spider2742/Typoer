# 🤖 Typoer - Realistic Typing Simulator

> **A modern, feature-rich typing automation tool with GUI, voice control, and cross-platform support**

Simulates **natural human typing behavior** — complete with typos, backspace corrections, variable speed, accuracy control, and full GUI. Perfect for demos, testing, and automation.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.7%2B-blue)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-green)

---

## 🌟 Features

- ✅ **Realistic Typing Simulation**
  - Adjustable **Words Per Minute (WPM)**
  - Configurable **accuracy (0–1)** to control typo frequency
  - Random delays and typing variations
  - Backspace corrections for typos

- ✅ **Multi-Paragraph & Line Break Support**
  - Preserves formatting and newlines
  - Handles large blocks of text seamlessly

- ✅ **🎨 Modern GUI (CustomTkinter)**
  - Clean, responsive interface
  - Live **typing preview animation**
  - Visual **progress bar** during typing
  - One-click **start, stop, clear**

- ✅ **🎙️ Voice Commands**
  - Say `"start typing"` or `"stop typing"` to control the simulator
  - Powered by Google Speech Recognition (internet required)

- ✅ **🎛️ Custom Hotkeys**
  - Set your own **Start Key** (e.g., `space`)
  - Set your own **Stop Key** (e.g., `escape`)
  - Works globally across applications

- ✅ **📁 File Import & Export**
  - **Import** `.txt` files with one click
  - **Export** typed text to `.txt`
  - Settings saved to `typoer_settings.json`

- ✅ **🎨 Theme & Sound**
  - Toggle **Dark/Light mode**
  - Enable/disable **sound notifications**
  - **Always-on-top** window option

- ✅ **🗑️ Minimize to System Tray**
  - Minimize to tray (Linux/Windows)
  - Restore with system tray icon

- ✅ **📦 Cross-Platform Packaging**
  - Build standalone `.exe` (Windows)
  - Build `.flatpak` (Linux)
  - Ready for distribution

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
python typoer.py
```

### Step-by-Step Guide

1. **Enter or Import Text**
   - Type directly into the large text box
   - Or click **📁 Import .txt** to load a file

2. **Adjust Settings**
   - `WPM`: Typing speed (e.g., `200`)
   - `Accuracy`: Typo frequency (e.g., `0.91`)
   - `Start Key`: Key to begin typing (e.g., `space`)
   - `Stop Key`: Key to stop (e.g., `escape`)

3. **Optional Features**
   - 🔔 Toggle **Sound** for alerts
   - 📌 Enable **Always on Top**
   - 🎤 Enable **Voice Commands** (say "start typing")
   - 🎨 Switch **Theme** (Dark/Light)

4. **Start Typing**
   - Click **▶ Start Typing**
   - Focus any text field (e.g., browser, editor)
   - Press your **Start Key** (e.g., `space`) to begin
   - Press your **Stop Key** (e.g., `escape`) to cancel

5. **Extra Tools**
   - 🔁 **Reset**: Clear text and progress
   - 💾 **Export**: Save current text as `.txt`
   - 🔽 **Minimize to Tray**: Keep running in background

> 💡 **Tip**: Enable **"Always on Top"** to keep Typoer visible while typing elsewhere!

---

## 📦 Packaging

### 🪟 Windows: Build `.exe` with PyInstaller
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon=icon.ico --name "Typoer" typoer.py
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

- The script **waits for the Start Key** before typing begins.
- Press the **Stop Key** anytime to interrupt.
- **Voice commands** require:
  - Microphone access
  - Internet (Google Speech API)
- **Accessibility permissions** are required for keyboard/mouse control on all OS.
- Settings are saved automatically on exit.

---

📬 **Found a bug or want a new feature?**  
👉 [Open an Issue](https://github.com/Spider2742/typoer/issues)

- [ ] https://github.com/Spider2742/Typoer/issues/3
---

## 🔗 Attribution

This project was inspired by and improves upon the original idea from [georgetian3/typoer](https://github.com/georgetian3/typoer).  
Special thanks to the original author for the concept and initial implementation.
