#!/usr/bin/env python3
"""Typoer: types your text into any window the way a person would.

It works at a chosen speed, makes the occasional typo on a neighbouring key and
corrects it with backspace. Start it with a global hotkey or a countdown, then
click into the window you want the text typed in.

Run:  python Typoer.py
"""
import json
import os
import queue
import random
import sys
import threading
import time
from tkinter import filedialog

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageTk

APP_NAME = "Typoer"
APP_VERSION = "2.0"
SETTINGS_FILE = "typoer_settings.json"

# ------------------ Settings ------------------
DEFAULT_SETTINGS = {
    "wpm": 200,
    "accuracy": 0.91,
    "start_key": "f8",
    "stop_key": "escape",
    "start_mode": "hotkey",   # "hotkey" or "countdown"
    "countdown": 5,
    "theme": "dark",
    "color_theme": "blue",    # kept so older settings files still round-trip
    "sound_enabled": True,
    "always_on_top": False,
    "voice_enabled": False,
}
WPM_RANGE = (20, 400)
ACCURACY_RANGE = (0.5, 1.0)
COUNTDOWN_CHOICES = (3, 5, 10)


def clamp(value, low, high):
    return max(low, min(high, value))


def load_settings(path=SETTINGS_FILE):
    """Defaults, overlaid with whatever valid values the settings file holds."""
    settings = dict(DEFAULT_SETTINGS)
    try:
        with open(path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
    except (OSError, ValueError):
        return settings
    if not isinstance(loaded, dict):
        return settings
    settings.update({k: v for k, v in loaded.items() if k in DEFAULT_SETTINGS})
    # Older versions saved numbers as text, so coerce rather than trust the types.
    try:
        settings["wpm"] = int(clamp(float(settings["wpm"]), *WPM_RANGE))
    except (TypeError, ValueError):
        settings["wpm"] = DEFAULT_SETTINGS["wpm"]
    try:
        settings["accuracy"] = clamp(float(settings["accuracy"]), *ACCURACY_RANGE)
    except (TypeError, ValueError):
        settings["accuracy"] = DEFAULT_SETTINGS["accuracy"]
    try:
        settings["countdown"] = int(settings["countdown"])
    except (TypeError, ValueError):
        settings["countdown"] = DEFAULT_SETTINGS["countdown"]
    if settings["countdown"] not in COUNTDOWN_CHOICES:
        settings["countdown"] = DEFAULT_SETTINGS["countdown"]
    if settings["start_mode"] not in ("hotkey", "countdown"):
        settings["start_mode"] = "hotkey"
    settings["theme"] = "light" if str(settings["theme"]).lower() == "light" else "dark"
    for key in ("start_key", "stop_key"):
        settings[key] = str(settings[key]).strip().lower() or DEFAULT_SETTINGS[key]
    for key in ("sound_enabled", "always_on_top", "voice_enabled"):
        settings[key] = bool(settings[key])
    return settings


def save_settings(settings, path=SETTINGS_FILE):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)
    except OSError as e:
        print("Could not save settings:", e)


# ------------------ Typing engine (no GUI in here) ------------------
# Keys next to each key on a QWERTY board: a slip of the finger lands on one of these.
NEIGHBOURS = {
    "q": "wa", "w": "qes", "e": "wrd", "r": "etf", "t": "ryg", "y": "tuh", "u": "yij",
    "i": "uok", "o": "ipl", "p": "ol", "a": "qsz", "s": "awdx", "d": "sefc", "f": "drgv",
    "g": "fthb", "h": "gyjn", "j": "hukm", "k": "jil", "l": "kop", "z": "asx", "x": "zsdc",
    "c": "xdfv", "v": "cfgb", "b": "vghn", "n": "bhjm", "m": "njk",
    "1": "2q", "2": "13w", "3": "24e", "4": "35r", "5": "46t", "6": "57y", "7": "68u",
    "8": "79i", "9": "80o", "0": "9p",
}
LETTERS = "abcdefghijklmnopqrstuvwxyz"


def typo_for(char, rng=random):
    """A plausible wrong key for `char`: a neighbour on the keyboard, in the same case."""
    near = NEIGHBOURS.get(char.lower())
    wrong = rng.choice(near) if near else rng.choice(LETTERS.replace(char.lower(), "") or LETTERS)
    return wrong.upper() if char.isupper() else wrong


def keystroke_plan(text, accuracy, rng=random):
    """Yield the keystrokes for `text` as (kind, char, counts) tuples.

    kind is "typo" (a wrong key), "backspace" (removing it) or "char" (the right key,
    where "\\n" means Enter and "\\t" means Tab). counts is True for the keystroke that
    completes one character of the text, which is what progress is measured in.
    """
    for char in text:
        if char not in "\n\t" and not char.isspace() and rng.random() > accuracy:
            yield ("typo", typo_for(char, rng), False)
            yield ("backspace", "", False)
        yield ("char", char, True)


def seconds_per_char(wpm):
    """A "word" is five characters, the usual convention for typing speed."""
    return 60.0 / (wpm * 5)


def estimate_seconds(char_count, wpm, accuracy):
    """Expected duration: every typo costs a wrong key, a pause and a backspace."""
    base = seconds_per_char(wpm)
    return char_count * base * (1 + 2.6 * (1 - accuracy))


def format_duration(seconds):
    seconds = int(round(seconds))
    if seconds < 60:
        return f"{seconds}s"
    minutes, seconds = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}m {seconds:02d}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes:02d}m"


class Typist:
    """Sends keystrokes to whichever window has focus."""

    def __init__(self):
        import pyautogui  # imported late: on Linux it needs a display to load
        self.gui = pyautogui
        self.gui.PAUSE = 0  # the default 0.1s pause after every key caps speed at ~120 WPM
        self.skipped = 0
        self._x11 = None

    def backspace(self):
        self.gui.press("backspace")

    def type(self, char):
        """Type one character. Returns False if this system has no way to send it."""
        if char == "\n":
            self.gui.press("enter")
        elif char == "\t":
            self.gui.press("tab")
        elif " " <= char <= "~":
            self.gui.write(char)
        elif not self._type_unicode(char):
            self.skipped += 1
            return False
        return True

    def _type_unicode(self, char):
        """pyautogui only knows the keys on a US keyboard; accents, dashes and so on go here."""
        if sys.platform.startswith("linux"):
            return self._type_unicode_x11(char)
        try:
            import keyboard
            keyboard.write(char)
            return True
        except Exception:
            return False

    def _type_unicode_x11(self, char):
        # X can only press keys that exist in the keyboard map, so borrow an unused keycode,
        # point it at this character for a moment, press it, and put it back.
        try:
            if self._x11 is None:
                from Xlib import X, display
                from Xlib.ext import xtest
                d = display.Display()
                first, last = d.display.info.min_keycode, d.display.info.max_keycode
                mapping = d.get_keyboard_mapping(first, last - first + 1)
                spare = next((first + i for i, syms in reversed(list(enumerate(mapping))) if not any(syms)), None)
                if spare is None:
                    self._x11 = False
                    return False
                self._x11 = (d, X, xtest, spare, len(mapping[0]))
            if not self._x11:
                return False
            d, X, xtest, spare, width = self._x11
            code = ord(char)
            keysym = code if code < 0x100 else 0x01000000 + code
            d.change_keyboard_mapping(spare, [(keysym,) * width])
            d.sync()
            time.sleep(0.02)  # give the focused app a moment to see the new mapping
            xtest.fake_input(d, X.KeyPress, spare)
            xtest.fake_input(d, X.KeyRelease, spare)
            d.sync()
            time.sleep(0.02)
            d.change_keyboard_mapping(spare, [(0,) * width])
            d.sync()
            return True
        except Exception:
            self._x11 = False
            return False


class Hotkeys:
    """Global hotkeys through the `keyboard` module, which isn't usable everywhere.

    On Linux it needs root, and on macOS it needs accessibility permission. When it
    can't be used, `available` is False and the app starts on a countdown instead.
    """

    def __init__(self):
        self.available = False
        self.reason = ""
        try:
            import keyboard
            keyboard.is_pressed("shift")
            self._kb = keyboard
            self.available = True
        except Exception as e:  # ImportError("You must be root...") on Linux, among others
            self._kb = None
            self.reason = str(e) or type(e).__name__

    def is_valid(self, key):
        if not self.available or not key:
            return False
        try:
            self._kb.parse_hotkey(key)
            return True
        except Exception:
            return False

    def is_pressed(self, key):
        try:
            return bool(self._kb.is_pressed(key))
        except Exception:
            return False


class Run(threading.Thread):
    """One typing run, on its own thread so the window stays responsive.

    It never touches the GUI. Everything it has to say goes into `events` as
    (name, payload) tuples, which the window reads on its own thread.
    """

    def __init__(self, text, wpm, accuracy, start_mode, start_key, stop_key, countdown, hotkeys, events):
        super().__init__(daemon=True)
        self.text = text
        self.wpm = wpm
        self.accuracy = accuracy
        self.start_mode = start_mode
        self.start_key = start_key
        self.stop_key = stop_key
        self.countdown = countdown
        self.hotkeys = hotkeys
        self.events = events
        self.stop_event = threading.Event()

    def stop(self):
        self.stop_event.set()

    def say(self, name, payload=None):
        self.events.put((name, payload))

    def stopped(self):
        if self.stop_event.is_set():
            return True
        if self.hotkeys.available and self.stop_key and self.hotkeys.is_pressed(self.stop_key):
            self.stop_event.set()
            return True
        return False

    def wait(self, seconds):
        """Sleep, but wake early if stopped. Returns True when the run should end."""
        deadline = time.monotonic() + seconds
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return self.stopped()
            if self.stop_event.wait(min(remaining, 0.03)) or self.stopped():
                return True

    def run(self):
        try:
            typist = Typist()
        except Exception as e:
            self.say("error", f"Can't send keystrokes on this system: {e}")
            return
        try:
            if not self._wait_for_start():
                self.say("cancelled")
                return
            self._type(typist)
        except Exception as e:
            # pyautogui raises FailSafeException when the mouse is thrown into a screen corner
            if type(e).__name__ == "FailSafeException":
                self.say("stopped", "Stopped: the mouse was moved to a corner of the screen.")
            else:
                self.say("error", f"Typing failed: {e}")

    def _wait_for_start(self):
        if self.start_mode == "hotkey":
            self.say("waiting", self.start_key)
            while not self.hotkeys.is_pressed(self.start_key):
                if self.wait(0.02):
                    return False
            # Wait for the key to come back up, so it isn't still held when typing starts.
            while self.hotkeys.is_pressed(self.start_key):
                if self.wait(0.02):
                    return False
            return not self.wait(0.1)
        for left in range(self.countdown, 0, -1):
            self.say("countdown", left)
            if self.wait(1):
                return False
        return True

    def _type(self, typist):
        base = seconds_per_char(self.wpm)
        total = len(self.text)
        done = 0
        started = time.monotonic()
        last_report = 0.0
        self.say("started", total)
        for kind, char, counts in keystroke_plan(self.text, self.accuracy):
            if self.stopped():
                self.say("stopped", None)
                return
            if kind == "backspace":
                typist.backspace()
                pause = base * random.uniform(0.6, 1.1)
            elif kind == "typo":
                typist.type(char)
                pause = base * random.uniform(1.2, 2.4)  # the moment it takes to notice a slip
            else:
                typist.type(char)
                pause = base * random.uniform(0.6, 1.4)
                if char in ".!?\n":
                    pause += base * random.uniform(0.5, 1.5)  # people pause at the end of a sentence
            if counts:
                done += 1
                now = time.monotonic()
                if now - last_report >= 0.05 or done == total:
                    last_report = now
                    self.say("progress", (done, total, now - started))
            if self.wait(pause):
                self.say("stopped", None)
                return
        self.say("finished", (total, time.monotonic() - started, typist.skipped))


# ------------------ Look ------------------
# (light, dark) pairs, the form CustomTkinter takes.
BG = ("#f3f1ea", "#131417")
PANEL = ("#ffffff", "#1b1c21")
FIELD = ("#f7f5ef", "#121317")
BORDER = ("#dcd8cc", "#2b2d34")
TEXT = ("#1b1c20", "#eceef2")
MUTED = ("#5d626e", "#9aa0ad")
FAINT = ("#7f8490", "#737986")
ACCENT = ("#f0bc2a", "#f5c542")
ACCENT_HOVER = ("#e2ab12", "#ffd563")
ACCENT_INK = "#1a1405"
ACCENT_TEXT = ("#8a6400", "#f5c542")
SUBTLE = ("#ebe8de", "#25272e")
SUBTLE_HOVER = ("#e0dccf", "#2f323a")
SELECTED = ("#ffffff", "#3d4049")
SELECTED_HOVER = ("#ffffff", "#474a54")
DANGER = ("#c8372d", "#e5534b")
DANGER_HOVER = ("#b02e25", "#f0655d")
OK = ("#1f8f5f", "#3ecf8e")
TYPED = ("#9a7500", "#f5c542")   # text already typed, shown in the editor during a run


def pick(pair):
    """The half of a (light, dark) pair that is showing right now."""
    return pair[1] if ctk.get_appearance_mode() == "Dark" else pair[0]


def logo_image(size=256):
    """The Typoer mark: a raised yellow keycap with a T and a typo squiggle."""
    scale = 4
    s = size * scale
    u = s / 64
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((9 * u, 15 * u, 55 * u, 57 * u), radius=11 * u, fill="#a87f12")
    d.rounded_rectangle((12 * u, 8 * u, 52 * u, 47 * u), radius=9 * u, fill="#f5c542")
    ink, w = "#17181c", int(5 * u)
    d.line((24 * u, 17 * u, 40 * u, 17 * u), fill=ink, width=w)
    d.line((32 * u, 17 * u, 32 * u, 32 * u), fill=ink, width=w)
    for x, y in ((24, 17), (40, 17), (32, 32)):
        d.ellipse((x * u - w / 2, y * u - w / 2, x * u + w / 2, y * u + w / 2), fill=ink)
    points, x, up = [], 22.5, True
    while x <= 41.7:
        points += [(x * u, 39.5 * u), ((x + 1.2) * u, (37.8 if up else 41.2) * u), ((x + 2.4) * u, 39.5 * u)]
        x, up = x + 2.4, not up
    d.line(points, fill=ink, width=int(2.6 * u), joint="curve")
    return img.resize((size, size), Image.LANCZOS)


def mono_family(root):
    from tkinter import font as tkfont
    have = set(tkfont.families(root))
    for name in ("JetBrains Mono", "Cascadia Mono", "Consolas", "Menlo", "SF Mono", "Source Code Pro", "DejaVu Sans Mono",
                 "Noto Sans Mono", "Adwaita Mono", "Liberation Mono", "Courier New"):
        if name in have:
            return name
    return "TkFixedFont"


# ------------------ Window ------------------
class TypoerApp(ctk.CTk):
    def __init__(self):
        self.settings = load_settings()
        ctk.set_appearance_mode(self.settings["theme"])
        ctk.set_default_color_theme("blue")
        super().__init__(fg_color=BG)

        self.title(APP_NAME)
        self.geometry("980x680")
        self.minsize(860, 640)

        self.hotkeys = Hotkeys()
        self.events = queue.Queue()
        self.run = None
        self.tray_icon = None
        self.voice_stop = None
        self._tts_lock = threading.Lock()
        self._tts = None
        self._text_offset = 0

        self.logo = logo_image(256)
        self._icon = ImageTk.PhotoImage(self.logo.resize((64, 64), Image.LANCZOS))
        self.iconphoto(True, self._icon)

        self.f_ui = ctk.CTkFont(size=13)
        self.f_small = ctk.CTkFont(size=12)
        self.f_label = ctk.CTkFont(size=13, weight="bold")
        self.f_title = ctk.CTkFont(size=20, weight="bold")
        self.f_value = ctk.CTkFont(size=13, weight="bold")
        self.f_mono = ctk.CTkFont(family=mono_family(self), size=13)
        self.f_button = ctk.CTkFont(size=14, weight="bold")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_header()
        self._build_editor()
        self._build_sidebar()
        self._build_footer()

        self.attributes("-topmost", self.settings["always_on_top"])
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.bind("<Control-Return>", lambda _e: self.toggle_run())
        self._refresh_start_mode()
        self._refresh_counts()
        self.set_status("Ready. Add some text, then press Start.", MUTED)
        if self.settings["voice_enabled"]:
            self.after(300, self.toggle_voice)
        self.after(40, self._drain_events)

    # ---- building blocks ----
    def _card(self, parent, **grid):
        card = ctk.CTkFrame(parent, fg_color=PANEL, border_color=BORDER, border_width=1, corner_radius=10)
        card.grid(**grid)
        return card

    def _subtle_button(self, parent, text, command, width=84):
        return ctk.CTkButton(parent, text=text, command=command, width=width, height=30, corner_radius=7,
                             font=self.f_small, fg_color=SUBTLE, hover_color=SUBTLE_HOVER, text_color=TEXT,
                             text_color_disabled=FAINT)

    def _section(self, parent, row, title, value_text=""):
        head = ctk.CTkFrame(parent, fg_color="transparent")
        head.grid(row=row, column=0, sticky="ew", padx=18, pady=(14, 6))
        head.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(head, text=title, font=self.f_label, text_color=TEXT, anchor="w").grid(row=0, column=0, sticky="w")
        value = ctk.CTkLabel(head, text=value_text, font=self.f_value, text_color=ACCENT_TEXT, anchor="e")
        value.grid(row=0, column=1, sticky="e")
        return value

    def _divider(self, parent, row):
        ctk.CTkFrame(parent, height=1, fg_color=BORDER).grid(row=row, column=0, sticky="ew", padx=18, pady=(14, 0))

    def _build_header(self):
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(16, 12))
        bar.grid_columnconfigure(2, weight=1)
        mark = ctk.CTkImage(light_image=self.logo, dark_image=self.logo, size=(34, 34))
        ctk.CTkLabel(bar, text="", image=mark).grid(row=0, column=0, padx=(0, 10))
        ctk.CTkLabel(bar, text=APP_NAME, font=self.f_title, text_color=TEXT).grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(bar, text="Types your text like a person would, typos and all.", font=self.f_ui,
                     text_color=MUTED).grid(row=0, column=2, sticky="w", padx=14, pady=(4, 0))
        self.theme_switch = ctk.CTkSegmentedButton(
            bar, values=["Light", "Dark"], command=self.set_theme, font=self.f_small, height=30,
            fg_color=SUBTLE, unselected_color=SUBTLE, unselected_hover_color=SUBTLE_HOVER,
            selected_color=SELECTED, selected_hover_color=SELECTED_HOVER, text_color=TEXT)
        self.theme_switch.set("Light" if self.settings["theme"] == "light" else "Dark")
        self.theme_switch.grid(row=0, column=3, sticky="e", padx=(0, 8))
        self._subtle_button(bar, "Minimise to tray", self.minimize_to_tray, width=124).grid(row=0, column=4, sticky="e")

    def _build_editor(self):
        card = self._card(self, row=1, column=0, sticky="nsew", padx=(20, 8), pady=0)
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 10))
        top.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(top, text="Text to type", font=self.f_label, text_color=TEXT).grid(row=0, column=0, sticky="w")
        self.counts_label = ctk.CTkLabel(top, text="", font=self.f_small, text_color=MUTED, anchor="w")
        self.counts_label.grid(row=0, column=1, sticky="w", padx=12)
        self.import_btn = self._subtle_button(top, "Import", self.import_text)
        self.import_btn.grid(row=0, column=2, padx=(0, 6))
        self.export_btn = self._subtle_button(top, "Export", self.export_text)
        self.export_btn.grid(row=0, column=3, padx=(0, 6))
        self.clear_btn = self._subtle_button(top, "Clear", self.clear_text, width=70)
        self.clear_btn.grid(row=0, column=4)

        self.text_area = ctk.CTkTextbox(card, wrap="word", font=self.f_mono, fg_color=FIELD, text_color=TEXT,
                                        border_color=BORDER, border_width=1, corner_radius=8,
                                        scrollbar_button_color=SUBTLE, scrollbar_button_hover_color=SUBTLE_HOVER)
        self.text_area.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        self.text_area.tag_config("typed", foreground=pick(TYPED))
        self.text_area.bind("<<Modified>>", self._on_text_modified)

        self.empty_hint = ctk.CTkLabel(
            self.text_area, text="Type or paste text here, or use Import to open a .txt file.",
            font=self.f_ui, text_color=FAINT, fg_color="transparent")
        self.empty_hint.bind("<Button-1>", lambda _e: self.text_area.focus_set())

    def _build_sidebar(self):
        side = self._card(self, row=1, column=1, sticky="ns", padx=(8, 20), pady=0)
        side.configure(width=300)
        side.grid_propagate(False)
        side.grid_columnconfigure(0, weight=1)
        slider = dict(height=16, fg_color=SUBTLE, progress_color=ACCENT, button_color=ACCENT,
                      button_hover_color=ACCENT_HOVER)

        # Speed
        self.wpm_value = self._section(side, 0, "Speed", f'{self.settings["wpm"]} WPM')
        self.wpm_slider = ctk.CTkSlider(side, from_=WPM_RANGE[0], to=WPM_RANGE[1],
                                        number_of_steps=(WPM_RANGE[1] - WPM_RANGE[0]) // 5,
                                        command=self._on_wpm, **slider)
        self.wpm_slider.set(self.settings["wpm"])
        self.wpm_slider.grid(row=1, column=0, sticky="ew", padx=16)

        # Accuracy
        self.acc_value = self._section(side, 2, "Accuracy", "")
        self.acc_slider = ctk.CTkSlider(side, from_=50, to=100, number_of_steps=50, command=self._on_accuracy, **slider)
        self.acc_slider.set(round(self.settings["accuracy"] * 100))
        self.acc_slider.grid(row=3, column=0, sticky="ew", padx=16)
        self.acc_hint = ctk.CTkLabel(side, text="", font=self.f_small, text_color=MUTED, anchor="w")
        self.acc_hint.grid(row=4, column=0, sticky="ew", padx=18, pady=(6, 0))
        self._show_accuracy()

        # Start and stop
        self._divider(side, 5)
        self._section(side, 6, "Start with" if self.hotkeys.available else "Start after a countdown")
        self.mode_switch = ctk.CTkSegmentedButton(
            side, values=["Hotkey", "Countdown"], command=self._on_mode, font=self.f_small, height=30,
            fg_color=SUBTLE, unselected_color=SUBTLE, unselected_hover_color=SUBTLE_HOVER,
            selected_color=SELECTED, selected_hover_color=SELECTED_HOVER, text_color=TEXT,
            text_color_disabled=MUTED)
        if self.hotkeys.available:
            self.mode_switch.grid(row=7, column=0, sticky="ew", padx=16)

        self.mode_box = ctk.CTkFrame(side, fg_color="transparent")
        self.mode_box.grid(row=8, column=0, sticky="ew", padx=18, pady=(10 if self.hotkeys.available else 0, 0))
        self.mode_box.grid_columnconfigure(1, weight=1)
        entry = dict(height=30, font=self.f_mono, fg_color=FIELD, border_color=BORDER, border_width=1,
                     text_color=TEXT, corner_radius=7, width=110, justify="center")
        self.start_key_label = ctk.CTkLabel(self.mode_box, text="Start key", font=self.f_ui, text_color=MUTED)
        self.start_key_entry = ctk.CTkEntry(self.mode_box, **entry)
        self.start_key_entry.insert(0, self.settings["start_key"])
        self.stop_key_label = ctk.CTkLabel(self.mode_box, text="Stop key", font=self.f_ui, text_color=MUTED)
        self.stop_key_entry = ctk.CTkEntry(self.mode_box, **entry)
        self.stop_key_entry.insert(0, self.settings["stop_key"])
        self.countdown_label = ctk.CTkLabel(self.mode_box, text="Seconds", font=self.f_ui, text_color=MUTED)
        self.countdown_switch = ctk.CTkSegmentedButton(
            self.mode_box, values=[str(n) for n in COUNTDOWN_CHOICES], command=self._on_countdown,
            font=self.f_small, height=30, width=110, fg_color=SUBTLE, unselected_color=SUBTLE,
            unselected_hover_color=SUBTLE_HOVER, selected_color=SELECTED, selected_hover_color=SELECTED_HOVER,
            text_color=TEXT, text_color_disabled=MUTED)
        self.countdown_switch.set(str(self.settings["countdown"]))
        self.mode_note = ctk.CTkLabel(side, text="", font=self.f_small, text_color=MUTED, anchor="w",
                                      justify="left", wraplength=262)
        self.mode_note.grid(row=9, column=0, sticky="ew", padx=18, pady=(8, 0))

        # Options
        self._divider(side, 10)
        self._section(side, 11, "Options")
        switch = dict(font=self.f_ui, text_color=TEXT, progress_color=ACCENT, button_color=("#4a4e58", "#e9ebf0"),
                      button_hover_color=("#33363e", "#ffffff"), fg_color=("#d5d1c5", "#3a3d46"),
                      switch_width=38, switch_height=20)
        self.sound_var = ctk.BooleanVar(value=self.settings["sound_enabled"])
        self.voice_var = ctk.BooleanVar(value=self.settings["voice_enabled"])
        self.top_var = ctk.BooleanVar(value=self.settings["always_on_top"])
        ctk.CTkSwitch(side, text="Sound and spoken status", variable=self.sound_var, command=self._on_option,
                      **switch).grid(row=12, column=0, sticky="w", padx=18, pady=3)
        ctk.CTkSwitch(side, text="Voice commands", variable=self.voice_var, command=self.toggle_voice,
                      **switch).grid(row=13, column=0, sticky="w", padx=18, pady=3)
        ctk.CTkSwitch(side, text="Always on top", variable=self.top_var, command=self._on_option,
                      **switch).grid(row=14, column=0, sticky="w", padx=18, pady=(3, 16))


    def _build_footer(self):
        bar = self._card(self, row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=(12, 18))
        bar.grid_columnconfigure(0, weight=1)
        left = ctk.CTkFrame(bar, fg_color="transparent")
        left.grid(row=0, column=0, sticky="ew", padx=(16, 14), pady=14)
        left.grid_columnconfigure(1, weight=1)
        self.status_dot = ctk.CTkLabel(left, text="●", font=ctk.CTkFont(size=12), text_color=MUTED, width=14)
        self.status_dot.grid(row=0, column=0, sticky="w")
        self.status_label = ctk.CTkLabel(left, text="", font=self.f_ui, text_color=TEXT, anchor="w")
        self.status_label.grid(row=0, column=1, sticky="ew", padx=(6, 10))
        self.progress_label = ctk.CTkLabel(left, text="", font=self.f_small, text_color=MUTED, anchor="e")
        self.progress_label.grid(row=0, column=2, sticky="e")
        self.progress_bar = ctk.CTkProgressBar(left, height=6, fg_color=SUBTLE, progress_color=ACCENT, corner_radius=3)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(9, 0))

        self.start_button = ctk.CTkButton(bar, text="Start", command=self.toggle_run, width=150, height=42,
                                          corner_radius=9, font=self.f_button, fg_color=ACCENT,
                                          hover_color=ACCENT_HOVER, text_color=ACCENT_INK)
        self.start_button.grid(row=0, column=1, padx=(0, 14), pady=12)

    # ---- status and counts ----
    def set_status(self, text, colour=MUTED):
        self.status_label.configure(text=text)
        self.status_dot.configure(text_color=colour)

    def current_text(self):
        raw = self.text_area.get("1.0", "end-1c").replace("\r\n", "\n")
        text = raw.strip()
        self._text_offset = len(raw) - len(raw.lstrip())
        return text

    def _on_text_modified(self, _event=None):
        inner = self.text_area._textbox
        if inner.edit_modified():
            inner.edit_modified(False)
            self._refresh_counts()

    def _refresh_counts(self):
        text = self.current_text()
        if text:
            self.empty_hint.place_forget()
            words = len(text.split())
            took = format_duration(estimate_seconds(len(text), self.wpm(), self.accuracy()))
            self.counts_label.configure(
                text=f'{words:,} word{"" if words == 1 else "s"}  ·  {len(text):,} characters  ·  about {took}')
        else:
            self.empty_hint.place(x=14, y=10)
            self.counts_label.configure(text="")

    def wpm(self):
        return int(round(self.wpm_slider.get()))

    def accuracy(self):
        return round(self.acc_slider.get()) / 100

    def _on_wpm(self, _value):
        self.wpm_value.configure(text=f"{self.wpm()} WPM")
        self._refresh_counts()

    def _show_accuracy(self):
        acc = self.accuracy()
        self.acc_value.configure(text=f"{round(acc * 100)}%")
        if acc >= 1:
            self.acc_hint.configure(text="No typos at all.")
        else:
            every = round(1 / (1 - acc))
            self.acc_hint.configure(text=f"About one typo every {every} characters, then fixed.")

    def _on_accuracy(self, _value):
        self._show_accuracy()
        self._refresh_counts()

    # ---- settings ----
    def _on_mode(self, value):
        self.settings["start_mode"] = "hotkey" if value == "Hotkey" else "countdown"
        self._refresh_start_mode()

    def _on_countdown(self, value):
        self.settings["countdown"] = int(value)

    def _refresh_start_mode(self):
        for widget in self.mode_box.winfo_children():
            widget.grid_forget()
        if not self.hotkeys.available:
            self.settings["start_mode"] = "countdown"
            self.mode_note.configure(
                text="Global hotkeys need root on Linux, so they're off here. To stop, press Stop or throw "
                     "the mouse into a screen corner.")
        else:
            self.mode_switch.set("Hotkey" if self.settings["start_mode"] == "hotkey" else "Countdown")
        if self.settings["start_mode"] == "hotkey":
            self.start_key_label.grid(row=0, column=0, sticky="w", pady=3)
            self.start_key_entry.grid(row=0, column=1, sticky="e", pady=3)
            self.stop_key_label.grid(row=1, column=0, sticky="w", pady=3)
            self.stop_key_entry.grid(row=1, column=1, sticky="e", pady=3)
            self.mode_note.configure(text="Press Start, click where the text should go, then press the start key.")
        else:
            self.countdown_label.grid(row=0, column=0, sticky="w", pady=3)
            self.countdown_switch.grid(row=0, column=1, sticky="e", pady=3)
            if self.hotkeys.available:
                self.stop_key_label.grid(row=1, column=0, sticky="w", pady=3)
                self.stop_key_entry.grid(row=1, column=1, sticky="e", pady=3)
                self.mode_note.configure(text="Press Start, then click where the text should go before the countdown ends.")

    def _on_option(self):
        self.settings["sound_enabled"] = bool(self.sound_var.get())
        self.settings["always_on_top"] = bool(self.top_var.get())
        self.attributes("-topmost", self.settings["always_on_top"])
        self.store_settings()

    def set_theme(self, value):
        self.settings["theme"] = value.lower()
        ctk.set_appearance_mode(self.settings["theme"])
        self.text_area.tag_config("typed", foreground=pick(TYPED))
        self.store_settings()

    def store_settings(self):
        self.settings.update(
            wpm=self.wpm(), accuracy=self.accuracy(),
            start_key=self.start_key_entry.get().strip().lower() or DEFAULT_SETTINGS["start_key"],
            stop_key=self.stop_key_entry.get().strip().lower() or DEFAULT_SETTINGS["stop_key"],
            sound_enabled=bool(self.sound_var.get()), always_on_top=bool(self.top_var.get()),
            voice_enabled=bool(self.voice_var.get()))
        save_settings(self.settings)

    # ---- files ----
    def import_text(self):
        path = filedialog.askopenfilename(title="Open text file",
                                          filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except OSError as e:
            self.set_status(f"Couldn't open that file: {e.strerror or e}", DANGER)
            return
        self.text_area.delete("1.0", "end")
        self.text_area.insert("1.0", content)
        self._refresh_counts()
        self.set_status(f"Imported {os.path.basename(path)}.", OK)

    def export_text(self):
        if not self.current_text():
            self.set_status("There's no text to export yet.", DANGER)
            return
        path = filedialog.asksaveasfilename(title="Save text as", defaultextension=".txt",
                                            filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.text_area.get("1.0", "end-1c"))
        except OSError as e:
            self.set_status(f"Couldn't save the file: {e.strerror or e}", DANGER)
            return
        self.set_status(f"Saved {os.path.basename(path)}.", OK)

    def clear_text(self):
        self.text_area.delete("1.0", "end")
        self.progress_bar.set(0)
        self.progress_label.configure(text="")
        self._refresh_counts()
        self.set_status("Ready. Add some text, then press Start.", MUTED)

    # ---- running ----
    def toggle_run(self):
        if self.run and self.run.is_alive():
            self.stop_typing()
        else:
            self.start_typing()

    def start_typing(self):
        if self.run and self.run.is_alive():
            return
        text = self.current_text()
        if not text:
            self.set_status("Add some text to type first.", DANGER)
            self.beep()
            return
        mode = self.settings["start_mode"]
        start_key = self.start_key_entry.get().strip().lower()
        stop_key = self.stop_key_entry.get().strip().lower()
        if self.hotkeys.available:
            if mode == "hotkey" and not self.hotkeys.is_valid(start_key):
                self.set_status(f'"{start_key}" isn\'t a key name. Try f8, space or a single letter.', DANGER)
                self.beep()
                return
            if not self.hotkeys.is_valid(stop_key):
                self.set_status(f'"{stop_key}" isn\'t a key name. Try escape, f9 or a single letter.', DANGER)
                self.beep()
                return
            if mode == "hotkey" and start_key == stop_key:
                self.set_status("The start key and the stop key need to be different.", DANGER)
                self.beep()
                return
        self.store_settings()
        self._set_running(True)
        self.progress_bar.set(0)
        self.progress_label.configure(text="")
        self.text_area.tag_remove("typed", "1.0", "end")
        self.run = Run(text, self.wpm(), self.accuracy(), mode, start_key, stop_key,
                       self.settings["countdown"], self.hotkeys, self.events)
        self.run.start()

    def stop_typing(self):
        if self.run and self.run.is_alive():
            self.run.stop()

    def _set_running(self, running):
        state = "disabled" if running else "normal"
        self.text_area.configure(state=state)
        for widget in (self.import_btn, self.clear_btn, self.wpm_slider, self.acc_slider,
                       self.start_key_entry, self.stop_key_entry, self.countdown_switch):
            widget.configure(state=state)
        if self.hotkeys.available:
            self.mode_switch.configure(state=state)
        if running:
            self.start_button.configure(text="Stop", fg_color=DANGER, hover_color=DANGER_HOVER, text_color="#ffffff")
        else:
            self.start_button.configure(text="Start", fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color=ACCENT_INK)

    def _drain_events(self):
        try:
            while True:
                name, payload = self.events.get_nowait()
                self._handle(name, payload)
        except queue.Empty:
            pass
        self.after(40, self._drain_events)

    def _handle(self, name, payload):
        if name == "waiting":
            self.set_status(f"Click where the text should go, then press {payload.upper()} to begin.", ACCENT_TEXT)
        elif name == "countdown":
            self.set_status(f"Typing starts in {payload}. Click where the text should go.", ACCENT_TEXT)
        elif name == "started":
            how = f"press {self.run.stop_key.upper()} or Stop" if self.hotkeys.available else "press Stop"
            self.set_status(f"Typing. To stop, {how}.", ACCENT_TEXT)
            self.announce("Typing started.")
        elif name == "progress":
            done, total, elapsed = payload
            self.progress_bar.set(done / total if total else 0)
            left = (elapsed / done) * (total - done) if done else 0
            self.progress_label.configure(text=f"{done:,} / {total:,}  ·  {format_duration(left)} left")
            start = f"1.0+{self._text_offset}c"
            self.text_area.tag_add("typed", start, f"1.0+{self._text_offset + done}c")
        elif name == "finished":
            total, elapsed, skipped = payload
            self.progress_bar.set(1)
            wpm = (total / 5) / (elapsed / 60) if elapsed > 0 else 0
            self.progress_label.configure(text=f"{total:,} / {total:,}")
            note = f" {skipped} character{'s' if skipped != 1 else ''} couldn't be typed here and were skipped." if skipped else ""
            self.text_area.tag_remove("typed", "1.0", "end")
            self.set_status(f"Done in {format_duration(elapsed)}, at {wpm:.0f} WPM.{note}", OK)
            self.announce("Typing completed.", notify="Typing completed.")
            self._set_running(False)
        elif name == "stopped":
            self.set_status(payload or "Stopped.", MUTED)
            self.announce("Typing stopped.")
            self._set_running(False)
        elif name == "cancelled":
            self.set_status("Cancelled before typing started.", MUTED)
            self._set_running(False)
        elif name == "error":
            self.set_status(payload, DANGER)
            self.beep()
            self._set_running(False)
        elif name == "voice":
            if payload == "start":
                self.start_typing()
            else:
                self.stop_typing()
        elif name == "voice_error":
            self.voice_var.set(False)
            self.voice_stop = None
            self.set_status(payload, DANGER)
            self.store_settings()

    # ---- sound, speech, notifications ----
    def beep(self):
        if self.settings["sound_enabled"]:
            self.bell()

    def announce(self, spoken, notify=None):
        if self.settings["sound_enabled"]:
            self.bell()
            threading.Thread(target=self._speak, args=(spoken,), daemon=True).start()
        if notify:
            threading.Thread(target=self._notify, args=(notify,), daemon=True).start()

    def _speak(self, text):
        if not self._tts_lock.acquire(blocking=False):
            return  # already speaking; pyttsx3 can't run two loops at once
        try:
            if self._tts is None:
                import pyttsx3
                self._tts = pyttsx3.init()
                self._tts.setProperty("rate", 180)
            self._tts.say(text)
            self._tts.runAndWait()
        except Exception:
            pass
        finally:
            self._tts_lock.release()

    @staticmethod
    def _notify(message):
        try:
            from plyer import notification
            notification.notify(title=APP_NAME, message=message, timeout=3)
        except Exception:
            pass

    # ---- voice commands ----
    def toggle_voice(self):
        if self.voice_var.get():
            if self.voice_stop is None:
                self.voice_stop = threading.Event()
                threading.Thread(target=self._listen, args=(self.voice_stop,), daemon=True).start()
                self.set_status('Listening for "start typing" and "stop typing".', OK)
        elif self.voice_stop is not None:
            self.voice_stop.set()
            self.voice_stop = None
            self.set_status("Voice commands are off.", MUTED)
        self.store_settings()

    def _listen(self, stop):
        try:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            microphone = sr.Microphone()
            with microphone as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
        except Exception as e:
            self.events.put(("voice_error", f"Voice commands need a working microphone: {e}"))
            return
        while not stop.is_set():
            try:
                with microphone as source:
                    audio = recognizer.listen(source, timeout=2, phrase_time_limit=3)
                heard = recognizer.recognize_google(audio).lower()
            except (sr.WaitTimeoutError, sr.UnknownValueError):
                continue
            except sr.RequestError:
                self.events.put(("voice_error", "Voice commands need an internet connection."))
                return
            except Exception as e:
                self.events.put(("voice_error", f"Voice commands stopped: {e}"))
                return
            if stop.is_set():
                return
            if "start typing" in heard:
                self.events.put(("voice", "start"))
            elif "stop typing" in heard:
                self.events.put(("voice", "stop"))

    # ---- tray ----
    def minimize_to_tray(self):
        if self.tray_icon is not None:
            self.withdraw()
            return
        try:
            import pystray
            icon = pystray.Icon(
                APP_NAME, self.logo.resize((64, 64), Image.LANCZOS), APP_NAME,
                menu=pystray.Menu(
                    pystray.MenuItem("Show", lambda: self.after(0, self.restore_from_tray), default=True),
                    pystray.MenuItem("Quit", lambda: self.after(0, self.on_close))))
            threading.Thread(target=icon.run, daemon=True).start()
        except Exception:
            # No system tray on this desktop: an ordinary minimise is the honest fallback.
            self.iconify()
            self.set_status("No system tray here, so the window was minimised instead.", MUTED)
            return
        self.tray_icon = icon
        self.withdraw()

    def restore_from_tray(self):
        if self.tray_icon is not None:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
            self.tray_icon = None
        self.deiconify()
        self.lift()

    # ---- closing ----
    def on_close(self):
        if self.run and self.run.is_alive():
            self.run.stop()
        if self.voice_stop is not None:
            self.voice_stop.set()
        self.store_settings()
        if self.tray_icon is not None:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
        self.destroy()


def main():
    TypoerApp().mainloop()


if __name__ == "__main__":
    main()
