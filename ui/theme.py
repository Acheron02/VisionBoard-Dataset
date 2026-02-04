# ui/theme.py
import tkinter as tk
from tkinter import font
from pathlib import Path

class ThemeManager:
    def __init__(self, root=None):
        self.mode = "dark"
        self.subscribers = []
        self.active_dialogs = 0

        # --- Define color palettes ---
        self.themes = {
            "dark": {
                "bg": "#050E3C",
                "panel": "#360185",
                "text": "#F7F6BB",
                "text2": "#F7F6BB",
                "muted": "#777777",
                "accent": "#7132CA",
                "danger": "#F4B342",
                "defect_colors": {
                    "short": (255, 0, 0),
                    "open": (0, 0, 255),
                    "90": (255, 255, 255),
                    "ps": (0, 255, 255),
                    "sb": (255, 0, 255),
                    "mc": (255, 255, 0),
                    "resistor": (255, 255, 255),
                    "capacitor": (255, 0, 0),
                },
            },
            "light": {
                "bg": "#EEEAF7",
                "panel": "#D9D1F5",
                "text": "#5A2FD6",
                "text2": "#4F646F",
                "muted": "#777777",
                "accent": "#F2C66D",
                "danger": "#e74c3c",
                "defect_colors": {    # <-- added here too
                    "short": (255, 0, 0),
                    "open": (0, 0, 255),
                    "90": (255, 255, 255),
                    "ps": (0, 255, 255),
                    "sb": (255, 0, 255),
                    "mc": (255, 255, 0),
                    "resistor": (255, 255, 255),
                    "capacitor": (255, 0, 0),
                },
            }
        }

        # --- Font sizes ---
        self.sizes = {
            "title": 55,
            "title2": 35,      # Headers / titles
            "subtitle": 23,    # Subtitles
            "body": 26,        # Body text, buttons, labels
            "small": 14,
            "feedback": 18
        }

        # --- Font paths ---
        bold_path = "/usr/share/fonts/truetype/fonts/BebasNeueRegular.ttf"
        regular_path = "/usr/share/fonts/truetype/fonts/NunitoRegular.ttf"

        # --- Load fonts dynamically if root is provided ---
        self.font_bold = "Bebas Neue"    # fallback
        self.font_regular = "Nunito" # fallback

        if root is not None:
            try:
                if Path(bold_path).exists():
                    tmp = font.Font(root=root, file=bold_path, size=self.sizes["body"])
                    self.font_bold = tmp.actual("family")
                if Path(regular_path).exists():
                    tmp = font.Font(root=root, file=regular_path, size=self.sizes["body"])
                    self.font_regular = tmp.actual("family")
            except Exception as e:
                print("Failed to load Segoe UI fonts, fallback to system font:", e)

    # ===============================
    # Theme functions
    # ===============================
    def colors(self):
        return self.themes[self.mode]

    def toggle(self):
        self.mode = "light" if self.mode == "dark" else "dark"
        self.notify()

    def subscribe(self, callback):
        if callback not in self.subscribers:
            self.subscribers.append(callback)

    def notify(self):
        for cb in self.subscribers:
            cb(self.colors())

# Singleton theme instance
theme = ThemeManager()
