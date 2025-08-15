import pyautogui
import random
from time import sleep
import customtkinter as ctk
import keyboard
import json
import os
from tkinter import filedialog
from plyer import notification
import speech_recognition as sr
from threading import Thread
from PIL import Image, ImageDraw
import pystray  # For system tray
import pyttsx3  # For voice feedback

# ------------------ Configuration & Paths ------------------
SETTINGS_FILE = "typoer_settings.json"

# Default settings
default_settings = {
    "wpm": 200,
    "accuracy": 0.91,
    "start_key": "space",
    "stop_key": "escape",
    "theme": "dark",
    "color_theme": "blue",
    "sound_enabled": True,
    "always_on_top": False,
    "voice_enabled": False
}

# Load settings
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                loaded = json.load(f)
                return {**default_settings, **loaded}
        except Exception as e:
            print("Could not load settings:", e)
    return default_settings

def save_settings():
    settings = {
        "wpm": wpm_entry.get(),
        "accuracy": accuracy_entry.get(),
        "start_key": start_key_entry.get().lower(),
        "stop_key": stop_key_entry.get().lower(),
        "theme": ctk.get_appearance_mode().lower(),
        "color_theme": "blue",
        "sound_enabled": sound_var.get(),
        "always_on_top": always_on_top_var.get(),
        "voice_enabled": voice_var.get()
    }
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        print("Could not save settings:", e)

# Initialize settings
settings = load_settings()

# ------------------ Configure CustomTkinter ------------------
ctk.set_appearance_mode(settings["theme"])
ctk.set_default_color_theme("blue")

# ------------------ App Functions ------------------
def notify(title, message):
    if settings["sound_enabled"]:
        app.bell()
    try:
        notification.notify(title=title, message=message, timeout=3)
    except:
        pass

# Initialize TTS engine
tts_engine = None
def speak(text):
    global tts_engine
    if not tts_engine:
        try:
            tts_engine = pyttsx3.init()
            tts_engine.setProperty("rate", 180)
        except:
            return
    tts_engine.say(text)
    tts_engine.runAndWait()

# Global flags
voice_listening = False
typing_in_progress = False
tray_icon = None

def typoer(text, wpm, accuracy, start_key, stop_key):
    global typing_in_progress
    typing_in_progress = True

    possible_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ,.!? '
    chars_per_sec = (wpm * 5) / 60
    sec_per_char = 1 / chars_per_sec
    variation = 0.05
    min_delay = sec_per_char * (1 - variation)
    max_delay = sec_per_char * (1 + variation)

    total_chars = len(text.replace('\n', '')) + text.count('\n')
    progress_step = 100 / total_chars if total_chars > 0 else 0
    current_progress = 0

    # Reset preview
    preview_label.configure(text="")
    preview_label.pack(pady=5)

    status_label.configure(text=f"⏳ Press '{start_key.upper()}' to start typing...")
    app.update()

    # Poll for start key (non-blocking)
    while not keyboard.is_pressed(start_key):
        if not typing_in_progress:
            status_label.configure(text="🛑 Typing canceled.")
            preview_label.pack_forget()
            return
        sleep(0.05)

    # Debounce
    keyboard.release(start_key)
    sleep(0.1)

    notify("Typoer", "Typing started!")
    if settings["sound_enabled"]:
        Thread(target=speak, args=("Typing started.",), daemon=True).start()
    status_label.configure(text=f"⌨️ Typing... Press '{stop_key.upper()}' to stop.")
    app.update()

    for line in text.split('\n'):
        for char in line:
            if not typing_in_progress or keyboard.is_pressed(stop_key):
                keyboard.release(stop_key)
                sleep(0.1)

                status_label.configure(text="🛑 Typing stopped.")
                if settings["sound_enabled"]:
                    app.bell()
                    Thread(target=speak, args=("Typing stopped.",), daemon=True).start()
                app.update()
                notify("Typoer", "Typing stopped by user.")
                preview_label.pack_forget()
                return

            # Typo simulation
            if char != '\n' and random.random() > accuracy:
                typo_char = random.choice(possible_chars.replace(char, ''))
                pyautogui.write(typo_char)
                sleep(random.uniform(min_delay, max_delay))
                pyautogui.press('backspace')

            pyautogui.write(char)
            sleep(random.uniform(min_delay, max_delay))

            # Update preview
            current_text = preview_label.cget("text") + char
            preview_label.configure(text=current_text)
            app.update()

            current_progress += progress_step
            progress_bar.set(current_progress / 100)

        pyautogui.press('enter')
        sleep(random.uniform(min_delay, max_delay))

        preview_label.configure(text=preview_label.cget("text") + "\n")
        app.update()
        current_progress += progress_step
        progress_bar.set(current_progress / 100)

    typing_in_progress = False
    status_label.configure(text="✅ Typing complete!")
    progress_bar.set(1)
    if settings["sound_enabled"]:
        Thread(target=speak, args=("Typing completed.",), daemon=True).start()
    app.update()
    notify("Typoer", "Typing completed successfully!")
    preview_label.pack_forget()

def start_typing():
    global typing_in_progress
    if typing_in_progress:
        status_label.configure(text="⚠️ Already typing...")
        return

    user_text = text_area.get("1.0", ctk.END).strip()
    if not user_text:
        status_label.configure(text="❌ Please enter text to type.")
        if settings["sound_enabled"]:
            app.bell()
        return

    try:
        wpm = int(wpm_entry.get())
        accuracy = float(accuracy_entry.get())
        start_key = start_key_entry.get().lower()
        stop_key = stop_key_entry.get().lower()
    except ValueError:
        status_label.configure(text="❌ Invalid WPM or Accuracy.")
        if settings["sound_enabled"]:
            app.bell()
        return

    valid_keys = {"space", "enter", "escape", "tab", "backspace", "delete", "shift", "ctrl", "alt", "capslock"}
    if start_key not in valid_keys and not len(start_key) == 1:
        status_label.configure(text="❌ Invalid start key.")
        return
    if stop_key not in valid_keys and not len(stop_key) == 1:
        status_label.configure(text="❌ Invalid stop key.")
        return

    estimated_chars = len(user_text.replace('\n', '')) + user_text.count('\n')
    estimated_time = (estimated_chars * 5) / (wpm * 60) * 60
    est_min = int(estimated_time // 60)
    est_sec = int(estimated_time % 60)
    status_label.configure(text=f"⏱️ Estimated time: {est_min}m {est_sec}s...")

    progress_bar.set(0)
    app.after(500, lambda: typoer(user_text, wpm, accuracy, start_key, stop_key))

def stop_typing():
    global typing_in_progress
    typing_in_progress = False
    status_label.configure(text="🛑 Typing stopped manually.")
    progress_bar.set(0)
    preview_label.pack_forget()
    if settings["sound_enabled"]:
        app.bell()
        Thread(target=speak, args=("Typing stopped.",), daemon=True).start()
    app.update()

def clear_text():
    text_area.delete("1.0", ctk.END)
    status_label.configure(text="📝 Ready to start.")
    progress_bar.set(0)
    preview_label.configure(text="")
    preview_label.pack_forget()

def import_text():
    file_path = filedialog.askopenfilename(
        title="Open Text File",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )
    if file_path:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            text_area.insert("1.0", content)
            status_label.configure(text=f"📄 Imported: {os.path.basename(file_path)}")
        except Exception as e:
            status_label.configure(text=f"❌ Failed to load file: {str(e)}")

def export_text():
    file_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )
    if file_path:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text_area.get("1.0", ctk.END))
            status_label.configure(text=f"💾 Saved: {os.path.basename(file_path)}")
        except Exception as e:
            status_label.configure(text=f"❌ Save failed: {str(e)}")

def reset_ui():
    clear_text()
    progress_bar.set(0)
    status_label.configure(text="📝 Ready to start.")

def toggle_theme():
    current = ctk.get_appearance_mode()
    new_mode = "Light" if current == "Dark" else "Dark"
    ctk.set_appearance_mode(new_mode)
    theme_toggle.configure(text=f"🎨 Theme: {new_mode}")
    save_settings()
    if tray_icon:
        tray_icon.icon = create_tray_icon(dark_mode=new_mode == "Dark")

def toggle_always_on_top():
    app.attributes("-topmost", always_on_top_var.get())
    save_settings()

# ------------------ Voice Commands ------------------
def start_voice_listener():
    global voice_listening
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    while voice_listening:
        try:
            with microphone as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=2, phrase_time_limit=3)
            try:
                text = recognizer.recognize_google(audio).lower()
                if "start typing" in text:
                    app.after(0, start_typing)
                elif "stop typing" in text:
                    app.after(0, stop_typing)
            except sr.UnknownValueError:
                pass
            except sr.RequestError:
                pass
        except sr.WaitTimeoutError:
            pass
        except Exception as e:
            print("Voice error:", e)
            sleep(0.5)

def toggle_voice():
    global voice_listening
    if voice_var.get():
        voice_listening = True
        Thread(target=start_voice_listener, daemon=True).start()
    else:
        voice_listening = False

# ------------------ System Tray ------------------
def on_tray_quit():
    global tray_icon
    if tray_icon:
        tray_icon.visible = False
        tray_icon.stop()
    app.quit()

def on_tray_show():
    app.deiconify()

def minimize_to_tray():
    app.withdraw()
    icon_image = create_tray_icon(dark_mode=ctk.get_appearance_mode() == "Dark")
    global tray_icon
    tray_icon = pystray.Icon(
        "Typoer",
        icon_image,
        "Typoer - Typing Simulator",
        menu=pystray.Menu(
            pystray.MenuItem("Show", lambda: on_tray_show()),
            pystray.MenuItem("Quit", lambda: on_tray_quit())
        )
    )
    Thread(target=tray_icon.run, daemon=True).start()

def create_tray_icon(dark_mode=True):
    bg = (70, 150, 255) if dark_mode else (30, 100, 200)
    image = Image.new('RGB', (64, 64), color=bg)
    draw = ImageDraw.Draw(image)
    draw.text((15, 20), "⌨️", fill="white")
    return image

# ------------------ GUI Setup ------------------
app = ctk.CTk()
app.title("⌨️ Typoer - Realistic Typing Simulator")
app.geometry("800x750")
app.resizable(True, True)

# Variables
sound_var = ctk.BooleanVar(value=settings["sound_enabled"])
always_on_top_var = ctk.BooleanVar(value=settings["always_on_top"])
voice_var = ctk.BooleanVar(value=settings["voice_enabled"])

# Header
header = ctk.CTkLabel(app, text="Typoer", font=("Arial Black", 28, "bold"))
header.pack(pady=10)

subheader = ctk.CTkLabel(app, text="Simulate human-like typing with typos, speed, and realism", font=("Arial", 12))
subheader.pack(pady=5)

# Control Buttons (Top Right)
top_frame = ctk.CTkFrame(app, fg_color="transparent")
top_frame.pack(pady=5, padx=20, anchor="ne")

always_top_switch = ctk.CTkCheckBox(top_frame, text="📌 Always on Top", variable=always_on_top_var, command=toggle_always_on_top)
always_top_switch.grid(row=0, column=0, padx=5)

sound_switch = ctk.CTkCheckBox(top_frame, text="🔊 Sound", variable=sound_var, command=save_settings)
sound_switch.grid(row=0, column=1, padx=5)

theme_toggle = ctk.CTkButton(top_frame, text=f"🎨 Theme: {ctk.get_appearance_mode()}", width=120, command=toggle_theme)
theme_toggle.grid(row=0, column=2, padx=5)

voice_switch = ctk.CTkCheckBox(top_frame, text="🎤 Voice Cmd", variable=voice_var, command=toggle_voice)
voice_switch.grid(row=0, column=3, padx=5)

# Text Input
ctk.CTkLabel(app, text="📝 Enter or Import Text to Type:", font=("Arial", 13, "bold")).pack(pady=(10, 5))
text_area = ctk.CTkTextbox(app, wrap="word", height=120, font=("Consolas", 12))
text_area.pack(padx=20, pady=10, fill="both", expand=True)

# Preview Label
preview_label = ctk.CTkLabel(app, text="", font=("Consolas", 12), wraplength=760, justify="left", text_color="#00AA00")
preview_label.pack(pady=5)
preview_label.pack_forget()

# File Buttons
button_row = ctk.CTkFrame(app, fg_color="transparent")
button_row.pack(pady=5)

import_button = ctk.CTkButton(button_row, text="📁 Import .txt", command=import_text, width=120, fg_color="#5C5C5C")
import_button.grid(row=0, column=0, padx=5)

export_button = ctk.CTkButton(button_row, text="💾 Export .txt", command=export_text, width=120, fg_color="#00AA00")
export_button.grid(row=0, column=1, padx=5)

# Input Frame
input_frame = ctk.CTkFrame(app)
input_frame.pack(pady=10, padx=20, fill="x")

labels = ["WPM:", "Accuracy (0-1):", "Start Key:", "Stop Key:"]
entries = []

for i, label in enumerate(labels):
    ctk.CTkLabel(input_frame, text=label, font=("Arial", 11)).grid(row=i, column=0, padx=15, pady=8, sticky="w")
    entry = ctk.CTkEntry(input_frame, placeholder_text=["e.g., 200", "e.g., 0.91", "e.g., space", "e.g., escape"][i])
    entry.grid(row=i, column=1, padx=10, pady=8, sticky="ew")
    entry.insert(0, settings[list(["wpm", "accuracy", "start_key", "stop_key"])[i]])
    entries.append(entry)

wpm_entry, accuracy_entry, start_key_entry, stop_key_entry = entries

# WPM Preset
ctk.CTkLabel(input_frame, text="Preset:", font=("Arial", 11)).grid(row=0, column=2, padx=15, pady=8, sticky="w")
wpm_preset = ctk.CTkComboBox(input_frame, values=["100", "150", "200", "250", "300"], width=100)
wpm_preset.set(str(settings["wpm"]))
wpm_preset.grid(row=0, column=3, padx=5, pady=8)
wpm_preset.configure(command=lambda x: wpm_entry.delete(0, 'end') or wpm_entry.insert(0, x))

input_frame.grid_columnconfigure(1, weight=1)

# Progress Bar
progress_bar = ctk.CTkProgressBar(app)
progress_bar.set(0)
progress_bar.pack(padx=20, pady=10, fill="x")

# Action Buttons
button_frame = ctk.CTkFrame(app, fg_color="transparent")
button_frame.pack(pady=15)

start_button = ctk.CTkButton(button_frame, text="▶ Start Typing", command=start_typing,
                             fg_color="#00A6FF", hover_color="#0088CC", font=("Arial", 12, "bold"), width=120)
start_button.grid(row=0, column=0, padx=10)

clear_button = ctk.CTkButton(button_frame, text="🗑 Clear Text", command=clear_text,
                             fg_color="#FF5555", hover_color="#DD3333", font=("Arial", 12), width=120)
clear_button.grid(row=0, column=1, padx=10)

minimize_button = ctk.CTkButton(button_frame, text="🔽 Minimize to Tray", command=minimize_to_tray,
                                fg_color="#666666", hover_color="#555555", width=140)
minimize_button.grid(row=0, column=2, padx=10)

reset_button = ctk.CTkButton(button_frame, text="🔁 Reset", command=reset_ui,
                             fg_color="#888888", hover_color="#666666", width=120)
reset_button.grid(row=0, column=3, padx=10)

# Status & Footer
status_label = ctk.CTkLabel(app, text="📝 Ready to start.", font=("Arial", 12, "italic"), text_color="#BBBBBB")
status_label.pack(pady=10)

footer = ctk.CTkLabel(app, text="💡 Tip: Press START key to begin typing | 'Esc' to stop", font=("Arial", 10), text_color="#888888")
footer.pack(side="bottom", pady=15)

# ------------------ Cleanup on Close ------------------
def on_closing():
    global voice_listening, typing_in_progress
    voice_listening = False
    typing_in_progress = False
    save_settings()
    if tray_icon:
        tray_icon.stop()
    if tts_engine:
        tts_engine.stop()
    app.quit()

app.protocol("WM_DELETE_WINDOW", on_closing)

# ------------------ Run App ------------------
if __name__ == "__main__":
    app.attributes("-topmost", settings["always_on_top"])
    app.mainloop()