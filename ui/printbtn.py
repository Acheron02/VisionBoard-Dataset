import os
from PIL import Image, ImageTk
from ui.roundedbutton import RoundedButton
from ui.theme import theme


class PrintButton(RoundedButton):
    """
    Print Button that:
    - Uses RoundedButton's disabled logic
    - Prevents clicks when disabled
    - Properly applies theme when disabled
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
            image_path = os.path.join(current_dir, "images", "print_icon.png")

        # Load image
        if os.path.exists(image_path):
            pil_img = Image.open(image_path).resize(
                (height - 10, height - 10),
                Image.Resampling.LANCZOS
            )
            self.img = ImageTk.PhotoImage(pil_img)

        colors = theme.colors()

        super().__init__(
            parent,
            text="" if self.img else "Print",
            image=self.img,
            command=command,
            width=width,
            height=height,
            radius=radius,
            bg=colors.get("accent", "#7132CA"),
            fg=colors.get("text", "#FFFFFF"),
            font=font,
            disabled=True  # start disabled
        )

    # Override _on_click to respect disabled state from base class
    def _on_click(self, event):
        if not self.disabled and callable(self._user_command):
            self._user_command()

    # No need to override set_disabled — it fully uses RoundedButton's logic

    # Theme automatically handled by RoundedButton
    def apply_theme(self, colors):
        try:
            super().apply_theme(colors)
            # Force canvas background to match parent for clean corners
            if hasattr(self, "canvas"):
                self.canvas.configure(bg=self.master.cget("bg"))
        except Exception:
            pass
