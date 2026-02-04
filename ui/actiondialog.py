import tkinter as tk
from ui.roundedbutton import RoundedButton
from ui.theme import theme


class ActionDialog(tk.Frame):
    def __init__(
        self,
        parent,
        title="Confirmation",
        message="Are you sure?",
        confirm_text="Confirm",
        confirm_command=None,
        cancel_text="Cancel",
        toggle_button=None,
    ):
        super().__init__(parent)

        self.confirm_command = confirm_command
        self.toggle_button = toggle_button

        # ===============================
        # Dialog count tracking
        # ===============================
        theme.active_dialogs += 1

        # ONLY hide toggle, NEVER restore here
        if self.toggle_button and self.toggle_button.winfo_exists():
            self.toggle_button.place_forget()

        # ===============================
        # Overlay
        # ===============================
        self.overlay = tk.Frame(parent, bg="#000000")
        self.overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.overlay.lift()
        self.overlay.bind("<Button-1>", lambda e: "break")

        # ===============================
        # Dialog container
        # ===============================
        self.dialog = tk.Frame(self.overlay, bd=0, bg=theme.colors()["bg"])
        self.dialog.place(relx=0.5, rely=0.5, anchor="center")

        # =============================== 
        # Title
        # ===============================
        self.title_label = None
        if title.strip():
            self.title_label = tk.Label(
                self.dialog,
                text=title,
                font=(theme.font_bold, theme.sizes["title2"]),
                wraplength=500,
                justify="center",
            )
            self.title_label.pack(padx=24, pady=(20, 8))

        # ===============================
        # Message
        # ===============================
        self.dialog_message_label = None
        if message.strip():
            self.dialog_message_label = tk.Label(
                self.dialog,
                text=message,
                font=(theme.font_regular, theme.sizes["subtitle"]),
                wraplength=500,
                justify="center",
            )
            self.dialog_message_label.pack(padx=24, pady=(0, 16))

        # ===============================
        # Buttons
        # ===============================
        self.buttons_frame = tk.Frame(self.dialog, bg=theme.colors()["bg"])
        self.buttons_frame.pack(pady=(0, 20))

        colors = theme.colors()

        if confirm_text:
            RoundedButton(
                self.buttons_frame,
                text=confirm_text,
                width=180,
                height=80,
                radius=24,
                command=self._on_confirm,
                bg=colors["accent"],
                fg=colors["text"],
            ).pack(side="left", padx=10)

        if cancel_text:
            RoundedButton(
                self.buttons_frame,
                text=cancel_text,
                width=180,
                height=80,
                radius=24,
                command=self._on_cancel,
                bg=colors["danger"],
                fg=colors["text"],
            ).pack(side="left", padx=10)

        # ===============================
        # Theme
        # ===============================
        self.apply_theme(colors)
        theme.subscribe(self.apply_theme)

        self.pack()
        self.bind("<Destroy>", self._on_destroy)

    # --------------------------------------------------
    def apply_theme(self, colors):
        try:
            self.overlay.configure(bg="#000000")
            self.dialog.configure(bg=colors["bg"])
            if self.title_label:
                self.title_label.configure(bg=colors["bg"], fg=colors["text"])
            if self.dialog_message_label:
                self.dialog_message_label.configure(bg=colors["bg"], fg=colors["text"])
            self.buttons_frame.configure(bg=colors["bg"])
        except tk.TclError:
            pass

    # --------------------------------------------------
    def close(self):
        if self.toggle_button and self.toggle_button.winfo_exists():
            theme.active_dialogs -= 1
            if theme.active_dialogs == 0:
                # Restore the toggle to original position
                self.toggle_button.place(relx=1.0, x=-30, y=10, anchor="ne")

        self.destroy()
        self.overlay.destroy()

    # --------------------------------------------------
    def _on_confirm(self):
        if self.confirm_command:
            self.confirm_command()
        self.close()

    def _on_cancel(self):
        self.close()

    # --------------------------------------------------
    def _on_destroy(self, *_):
        if self.apply_theme in theme.subscribers:
            theme.subscribers.remove(self.apply_theme)

        if self.toggle_button and self.toggle_button.winfo_exists():
            theme.active_dialogs = max(0, theme.active_dialogs - 1)
            if theme.active_dialogs == 0:
                self.toggle_button.place(relx=1.0, x=-30, y=10, anchor="ne")
