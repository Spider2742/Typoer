# 🤖 Typoer - Realistic Typing Simulator

> **An improved and enhanced version of [georgetian3/typoer](https://github.com/georgetian3/typoer)**  
> Simulates human-like typing with typos, corrections, variable speed, and full GUI control.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.7%2B-blue)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-green)

---

## 📖 Overview

`Typoer` is a Python script that simulates **natural human typing behavior** — complete with typos, backspace corrections, variable speed, and accuracy control. This improved version fixes input handling for multi-paragraph text and adds a **modern GUI**, **voice commands**, **system tray support**, and more.

Perfect for:
- Testing input fields
- Creating typing demos
- Automating text entry with realism

---

## 🌟 Features

- ✅ **Realistic Typing Simulation**
  - Adjustable **Words Per Minute (WPM)**
  - Configurable **accuracy (0–1)** to control typo frequency
  - Random delays and typing variations
  - Backspace corrections for typos

- ✅ **Multi-Paragraph Support**
  - Preserve line breaks and formatting
  - Handles large blocks of text seamlessly

- ✅ **GUI Interface (New!)**
  - Easy-to-use **CustomTkinter** interface
  - Live **typing preview animation**
  - Visual **progress bar** during typing
  - One-click **start, stop, and clear**

- ✅ **🎙️ Voice Commands (New!)**
  - Say `"start typing"` or `"stop typing"` to control the simulator
  - Powered by Google Speech Recognition (internet required)

- ✅ **🎛️ Hotkey Control**
  - Set custom **start key** (e.g., `space`)
  - Set custom **stop key** (e.g., `escape`)
  - Works globally across apps

- ✅ **📁 File Import & Export**
  - Import `.txt` files with **one click**
  - Settings saved automatically to `typoer_settings.json`

- ✅ **🎨 Theme & Sound**
  - Toggle **Dark/Light mode**
  - Enable/disable **sound notifications**
  - Always-on-top window option

- ✅ **🗑️ Minimize to System Tray (New!)**
  - Minimize and run in background
  - Access via tray icon (Linux/Windows)

- ✅ **📦 Export Ready**
  - Build standalone `.exe` (Windows) with PyInstaller
  - Build `.flatpak` (Linux) for universal distribution

---

## 🚀 Installation

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/typoer.git
cd typoer
```

### 2. Install dependencies
```bash
pip install --upgrade pip
pip install customtkinter pyautogui keyboard plyer speechrecognition pyaudio pystray pillow
```

> [!NOTE]  
> On Linux, you may need system permissions for keyboard/mouse access.  
> Run with `sudo` only if necessary, or add your user to the `input` group:
> ```bash
> sudo usermod -aG input $USER
> ```
> Then log out and back in.

---

## 🖥️ Usage (GUI Mode)

### Run the app
```bash
python typoer.py
```

### How to Use
1. **Enter text** in the large input box (supports multiple paragraphs).
2. **Import text** from a `.txt` file using the "📁 Import .txt File" button.
3. Adjust:
   - `WPM` (e.g., 200)
   - `Accuracy` (e.g., 0.91)
   - `Start Key` (e.g., `space`)
   - `Stop Key` (e.g., `escape`)
4. Click **▶ Start Typing**.
5. Press your **Start Key** (e.g., `space`) to begin typing.
6. Press your **Stop Key** (e.g., `escape`) anytime to cancel.

> 💡 **Tip**: Enable "🎤 Voice Cmd" to say `"start typing"` and begin hands-free!

---

## ⚙️ CLI Mode (Legacy)

You can still use a CLI version — just modify the script or create a separate `typoer_cli.py`.

---

## 📦 Packaging

### 🪟 Windows: Build `.exe`
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "Typoer" typoer.py
```
Output: `dist/Typoer.exe`

### 🐧 Linux: Build Flatpak
```bash
flatpak install flathub org.freedesktop.Platform//22.08 org.freedesktop.Sdk//22.08
flatpak-builder --user --install build-dir com.spider.Typoer.yml --force-clean
flatpak run com.spider.Typoer
```

---

## 📄 License

MIT © [Your Name]  
Feel free to use, modify, and distribute. Credit is appreciated but not required.

---

## 📝 Notes
- The script waits for the **start key** before typing begins.
- Press the **stop key** anytime to interrupt.
- Voice commands require an active microphone and internet.
- Accessibility permissions (keyboard/mouse control) are required on all OS.

---
📬 **Found a bug or want a new feature?**  
👉 [Open an issue](https://github.com/yourusername/typoer/issues) or contribute!