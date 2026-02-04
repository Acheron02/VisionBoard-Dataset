# ui/retakebtn.py
import os
from PIL import Image, ImageTk
from ui.roundedbutton import RoundedButton
from ui.theme import theme

class RetakeButton(RoundedButton):
    """
    Theme-aware Retake Button fully compliant with RoundedButton.
    Supports icon/text and responds to theme changes.
    """
    def __init__(
        self,
        parent,
        command=None,
        image_path=None,
        width=220,
        height=100,
        radius=20,
        font=None
    ):
        font = font or (theme.font_bold, theme.sizes["body"])
        self.img = None

        # Default icon path
        if image_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            image_path = os.path.join(current_dir, "images", "redo_icon.png")

        # Load image if exists
        if os.path.exists(image_path):
            pil_img = Image.open(image_path).resize((height - 10, height - 10), Image.Resampling.LANCZOS)
            self.img = ImageTk.PhotoImage(pil_img)

        # Initial colors from theme
        colors = theme.colors()
        bg = colors.get("accent", "#F44336")
        fg = colors.get("text", "#FFFFFF")

        # Initialize RoundedButton
        super().__init__(
            parent,
            text="" if self.img else "Retake",
            image=self.img,
            command=command,
            width=width,
            height=height,
            radius=radius,
            bg=bg,
            fg=fg,
            font=font
        )

        # Subscribe to theme updates
        theme.subscribe(self.apply_theme)

    def apply_theme(self, colors):
        """
        Properly update colors so the rounded corners match new theme.
        """
        try:
            super().apply_theme(colors)

            # Force canvas background to match parent for perfect corners
            if hasattr(self, "canvas"):
                self.canvas.configure(bg=self.master.cget("bg"))
        except Exception:
            pass
