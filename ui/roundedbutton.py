import tkinter as tk
from PIL import Image, ImageTk
from ui.theme import theme


class RoundedButton(tk.Canvas):
    def __init__(
        self,
        parent,
        text="",
        image=None,
        command=None,
        width=150,
        height=50,
        radius=12,
        bg=None,
        fg=None,
        font=None,
        disabled=False,
    ):
        self.parent = parent
        self._user_command = command
        self.disabled = disabled
        self.radius = radius
        self.font = font or (theme.font_regular, theme.sizes["body"])

        super().__init__(
            parent,
            width=width,
            height=height,
            bg=parent["bg"],
            highlightthickness=0
        )

        # ===============================
        # Theme colors
        # ===============================
        colors = theme.colors()
        self.bg_color = bg or colors["accent"]
        self.fg_color = fg or colors["text"]
        self.disabled_color = colors.get("muted", "#888888")
        self.hover_color = self._darker_color(self.bg_color)
        self.img = None

        # ===============================
        # Draw smooth rounded rectangle
        # ===============================
        self.round_rect = self.create_rounded_rect(0, 0, width, height, radius, fill=self.bg_color)

        # ===============================
        # Add text or image
        # ===============================
        self.text_id = None
        self.image_id = None

        if image:
            if isinstance(image, str):
                pil_img = Image.open(image).resize((height - 10, height - 10))
                self.img = ImageTk.PhotoImage(pil_img)
            else:
                self.img = image if isinstance(image, ImageTk.PhotoImage) else ImageTk.PhotoImage(image)

            self.image_id = self.create_image(width // 2, height // 2, image=self.img)
        else:
            self.text_id = self.create_text(width // 2, height // 2, text=text, fill=self.fg_color, font=self.font)

        # ===============================
        # Events
        # ===============================
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

        # ===============================
        # Theme subscription
        # ===============================
        theme.subscribe(self.apply_theme)
        self._update_visual_state()
        self.bind("<Destroy>", self._on_destroy)

    # ==================================================
    # Draw a smooth rounded rectangle (no overlapping lines)
    # ==================================================
    def create_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        """Draw a single rounded rectangle using a polygon with smooth corners."""
        points = [
            x1+r, y1,
            x2-r, y1,
            x2, y1,
            x2, y1+r,
            x2, y2-r,
            x2, y2,
            x2-r, y2,
            x1+r, y2,
            x1, y2,
            x1, y2-r,
            x1, y1+r,
            x1, y1
        ]
        return self.create_polygon(points, smooth=True, splinesteps=36, **kwargs)

    # ==================================================
    # Event handlers
    # ==================================================
    def _on_click(self, event):
        if not self.disabled and self._user_command:
            self._user_command()

    def _on_enter(self, event):
        if not self.disabled:
            self._update_rect_color(self.hover_color)

    def _on_leave(self, event):
        if not self.disabled:
            self._update_rect_color(self.bg_color)

    # ==================================================
    # Update rectangle color
    # ==================================================
    def _update_rect_color(self, color):
        self.itemconfig(self.round_rect, fill=color)

    # ==================================================
    # Darker color helper
    # ==================================================
    def _darker_color(self, hex_color, factor=0.85):
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        r = max(0, int(r * factor))
        g = max(0, int(g * factor))
        b = max(0, int(b * factor))
        return f"#{r:02x}{g:02x}{b:02x}"

    # ==================================================
    # State control
    # ==================================================
    def set_disabled(self, disabled=True):
        self.disabled = disabled
        self._update_visual_state()

    def _update_visual_state(self):
        if self.disabled:
            self._update_rect_color(self.disabled_color)
            if self.text_id:
                self.itemconfig(self.text_id, fill=self.parent["bg"])
        else:
            self._update_rect_color(self.bg_color)
            if self.text_id:
                self.itemconfig(self.text_id, fill=self.fg_color)

    # ==================================================
    # Theme updates
    # ==================================================
    def apply_theme(self, colors):
        try:
            self.configure(bg=colors["bg"])
            if not self.disabled:
                self.bg_color = colors.get("accent", self.bg_color)
                self.fg_color = colors.get("text", self.fg_color)
                self.hover_color = self._darker_color(self.bg_color)
            self.disabled_color = colors.get("muted", self.disabled_color)
            self._update_visual_state()
        except tk.TclError:
            pass

    # ==================================================
    # Cleanup
    # ==================================================
    def _on_destroy(self, *_):
        if self.apply_theme in theme.subscribers:
            theme.subscribers.remove(self.apply_theme)
