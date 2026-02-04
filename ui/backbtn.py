import os
import tkinter as tk
from PIL import Image, ImageTk
from ui.roundedbutton import RoundedButton
from ui.theme import theme  # Singleton


class BackButton(RoundedButton):
    """
    Reusable Back Button component based on RoundedButton.
    Displays a '<' icon (or custom image from 'images' folder) and executes a command when clicked.
    Fully compatible with light/dark mode and hover colors.
    """

    def __init__(
        self,
        parent,
        command=None,
        image_path=None,
        width=85,
        height=50,
        radius=24,
        bg="#2196F3",
        fg="white",
        font=(theme.font_regular, theme.sizes["body"])
    ):
        self.default_bg = bg
        self.default_fg = fg

        # If no image_path is provided, default to "images/back_icon.png" next to this file
        self.img = None
        if image_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            image_path = os.path.join(base_dir, "images", "back_icon.png")

        if os.path.exists(image_path):
            pil_img = Image.open(image_path).resize((height - 10, height - 10), Image.Resampling.LANCZOS)
            self.img = ImageTk.PhotoImage(pil_img)
            super().__init__(
                parent,
                text="",
                image=self.img,
                command=command,
                width=width,
                height=height,
                radius=radius,
                bg=bg,
                fg=fg,
                font=font
            )
        else:
            super().__init__(
                parent,
                text="<",
                command=command,
                width=width,
                height=height,
                radius=radius,
                bg=bg,
                fg=fg,
                font=font
            )

    # ===============================
    # Theme support
    # ===============================
    def apply_theme(self, colors):
        """
        Dynamically apply theme colors.
        Delegates to RoundedButton.apply_theme to handle
        bg, fg, hover, and disabled states correctly.
        """
        try:
            super().apply_theme(colors)
        except tk.TclError:
            # Widget may already be destroyed
            pass
