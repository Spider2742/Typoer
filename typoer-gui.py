import pyautogui
import random
from time import sleep
import tkinter as tk
from tkinter import scrolledtext, messagebox
import keyboard

def typoer(text, wpm, accuracy, start_key, stop_key):
    possible_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ,.!? '  
    sec_per_char = 12 / wpm
    variation = 0.05  
    min_delay = sec_per_char * (1 - variation)
    max_delay = sec_per_char * (1 + variation)

    status_label.config(text=f"Press '{start_key.upper()}' to start typing...")
    root.update()
    keyboard.wait(start_key)
    
    status_label.config(text=f"Typing... Press '{stop_key.upper()}' to stop.")
    root.update()
    
    for line in text.split('\n'):
        for char in line:
            if keyboard.is_pressed(stop_key):
                status_label.config(text="Typing stopped.")
                root.update()
                return
            
            if char != '\n' and random.random() > accuracy:  # Introduce typos correctly
                typo = random.choice(possible_chars)
                pyautogui.write(typo)
                pyautogui.press('backspace')  # Always correct typos immediately
            
            pyautogui.write(char)
            sleep(random.uniform(min_delay, max_delay))
        
        pyautogui.press('enter')
        sleep(random.uniform(min_delay, max_delay))
    
    status_label.config(text="Typing complete!")
    root.update()

def start_typing():
    user_text = text_area.get("1.0", tk.END).strip()
    if not user_text:
        messagebox.showwarning("Warning", "Please enter some text to type.")
        return
    
    wpm = int(wpm_entry.get())
    accuracy = float(accuracy_entry.get())
    start_key = start_key_entry.get()
    stop_key = stop_key_entry.get()
    
    typoer(user_text, wpm, accuracy, start_key, stop_key)

# GUI Setup
root = tk.Tk()
root.title("Typoer - Simulated Typing")
root.geometry("600x500")
root.configure(bg="#121212")

tk.Label(root, text="Enter text to type:", font=("Arial", 12, "bold"), fg="#FFFFFF", bg="#121212").pack(pady=5)
text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=10, font=("Consolas", 10), bg="#1E1E1E", fg="#FFFFFF", insertbackground="#FFFFFF", relief=tk.FLAT)
text_area.pack(pady=5)

tk.Label(root, text="WPM:", font=("Arial", 10, "bold"), fg="#FFFFFF", bg="#121212").pack()
wpm_entry = tk.Entry(root, font=("Arial", 10), bg="#1E1E1E", fg="#FFFFFF", insertbackground="#FFFFFF", relief=tk.FLAT)
wpm_entry.insert(0, "200")
wpm_entry.pack()

tk.Label(root, text="Accuracy (0 to 1):", font=("Arial", 10, "bold"), fg="#FFFFFF", bg="#121212").pack()
accuracy_entry = tk.Entry(root, font=("Arial", 10), bg="#1E1E1E", fg="#FFFFFF", insertbackground="#FFFFFF", relief=tk.FLAT)
accuracy_entry.insert(0, "1.0")  # Default to perfect accuracy
accuracy_entry.pack()

tk.Label(root, text="Start Key:", font=("Arial", 10, "bold"), fg="#FFFFFF", bg="#121212").pack()
start_key_entry = tk.Entry(root, font=("Arial", 10), bg="#1E1E1E", fg="#FFFFFF", insertbackground="#FFFFFF", relief=tk.FLAT)
start_key_entry.insert(0, "space")
start_key_entry.pack()

tk.Label(root, text="Stop Key:", font=("Arial", 10, "bold"), fg="#FFFFFF", bg="#121212").pack()
stop_key_entry = tk.Entry(root, font=("Arial", 10), bg="#1E1E1E", fg="#FFFFFF", insertbackground="#FFFFFF", relief=tk.FLAT)
stop_key_entry.insert(0, "escape")
stop_key_entry.pack()

type_button = tk.Button(root, text="Start Typing", command=start_typing, font=("Arial", 12, "bold"), bg="#00A6FF", fg="#FFFFFF", relief=tk.FLAT, activebackground="#0088CC")
type_button.pack(pady=5)

status_label = tk.Label(root, text="Waiting to start...", font=("Arial", 10, "bold"), fg="#FFFFFF", bg="#121212")
status_label.pack(pady=5)

root.mainloop()
