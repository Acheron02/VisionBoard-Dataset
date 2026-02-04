import tkinter as tk
from PIL import Image, ImageTk
import os

class ThemeToggleButton(tk.Button):
    def __init__(self, parent, theme):
        self.theme = theme

        # Load icons with transparency
        current_dir = os.path.dirname(os.path.abspath(__file__))
        moon_path = os.path.join(current_dir, "images", "dark_icon.png")
        sun_path = os.path.join(current_dir, "images", "light_icon.png")

        self.moon_img = ImageTk.PhotoImage(
            Image.open(moon_path).convert("RGBA").resize((50, 50), Image.LANCZOS)
        )
        self.sun_img = ImageTk.PhotoImage(
            Image.open(sun_path).convert("RGBA").resize((50, 50), Image.LANCZOS)
        )

        # Inversion: show moon if current mode is light, sun if dark
        self.current_icon = self.moon_img if theme.mode == "light" else self.sun_img

        super().__init__(
            parent,
            image=self.current_icon,
            bd=0,
            highlightthickness=0,
            relief="flat",
            bg=theme.colors()["bg"],             # Use system bg color
            activebackground=theme.colors()["bg"],
            command=self.toggle_theme
        )

        # Subscribe to theme updates
        theme.subscribe(self.apply_theme)

    def toggle_theme(self):
        # Toggle theme
        self.theme.toggle()
        # Update icon to reflect next theme
        self.current_icon = self.moon_img if self.theme.mode == "light" else self.sun_img
        self.configure(image=self.current_icon)

    def apply_theme(self, c):
        # Update button background to match system theme bg
        self.configure(
            bg=c["bg"],
            activebackground=c["bg"]
        )
