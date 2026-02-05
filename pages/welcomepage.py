import os
import tkinter as tk
from PIL import Image, ImageTk
from pages.choosemodel import ChooseModel
from pages.errorpage import ErrorPage
from ui.theme import theme
from ui.actiondialog import ActionDialog


class WelcomePage(tk.Frame):
    def __init__(self, parent, show_page, monitor):
        super().__init__(parent)
        self.show_page = show_page
        self.monitor = monitor
        self.dialog = None

        # ---------------- Container ----------------
        self.container = tk.Frame(self)
        self.container.pack(expand=True)

        # ---------------- Title ----------------
        self.title_label = tk.Label(
            self.container,
            text="Welcome to",
            font=(theme.font_bold, theme.sizes["title"])
        )
        self.title_label.pack(pady=(0, 10))

        # ---------------- Logo ----------------
        logo_path = "ui/images/visionboard_logo.png"
        if os.path.exists(logo_path):
            logo_img = Image.open(logo_path)
            max_width = 600
            ratio = max_width / logo_img.width
            new_size = (int(logo_img.width * ratio), int(logo_img.height * ratio))
            logo_img = logo_img.resize(new_size, Image.LANCZOS)

            self.logo_photo = ImageTk.PhotoImage(logo_img)
            self.logo_label = tk.Label(self.container, image=self.logo_photo, bg=theme.colors()["bg"])
            self.logo_label.pack(pady=(0, 15))

        # ---------------- Subtitle ----------------
        self.subtitle_label = tk.Label(
            self.container,
            text="Click anywhere to proceed.",
            font=(theme.font_regular, theme.sizes["body"])
        )
        self.subtitle_label.pack()

        # Bind clicks to all widgets to proceed
        for w in (self, self.container, self.title_label, self.subtitle_label):
            w.bind("<Button-1>", self.proceed)
        if hasattr(self, "logo_label"):
            self.logo_label.bind("<Button-1>", self.proceed)

        # Apply initial theme
        self.apply_theme(theme.colors())
        theme.subscribe(self.apply_theme)

        # Auto-unsubscribe on destroy
        self.bind("<Destroy>", self._on_destroy)

        # Subscribe to monitor updates
        self.monitor.subscribe(self.on_system_update)
        self.on_system_update(self.monitor.problems)

    # ---------------- Theme ----------------
    def apply_theme(self, colors):
        """Apply theme colors to all widgets"""
        try:
            self.configure(bg=colors["bg"])
            self.container.configure(bg=colors["bg"])
            self.title_label.configure(bg=colors["bg"], fg=colors["text"])
            self.subtitle_label.configure(bg=colors["bg"], fg=colors["muted"])
            if hasattr(self, "logo_label"):
                self.logo_label.configure(bg=colors["bg"])
        except tk.TclError:
            pass

    # ---------------- Destroy ----------------
    def _on_destroy(self, event=None):
        if self.apply_theme in theme.subscribers:
            theme.subscribers.remove(self.apply_theme)
        self.monitor.unsubscribe(self.on_system_update)

    # ---------------- Proceed ----------------
    def proceed(self, event=None):
        """Navigate to ChooseModel page"""
        self.show_page(ChooseModel, monitor=self.monitor)

    # ---------------- System Updates ----------------
    def on_system_update(self, problems):
        """Show error dialog if a problem arises, auto-close if fixed"""
        if problems:
            if not self.dialog:
                def on_exit():
                    self.show_page(
                        ErrorPage,
                        monitor=self.monitor,
                        problems=problems,
                        next_page=WelcomePage
                    )

                self.dialog = ActionDialog(
                    self,
                    title="System Error",
                    message="\n".join(problems),
                    confirm_text="Exit",
                    confirm_command=on_exit,
                    cancel_text="",  # hides cancel button
                    toggle_button=self.master.toggle
                )
                self.dialog.apply_theme(theme.colors())
                self.dialog.bind("<Destroy>", lambda e: setattr(self, 'dialog', None))
            else:
                self.dialog.update_message("\n".join(problems))
        else:
            if self.dialog:
                self.dialog.close()
                self.dialog = None
