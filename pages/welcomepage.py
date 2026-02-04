import tkinter as tk
from pages.choosemodel import ChooseModel
from pages.errorpage import ErrorPage
from ui.theme import theme  # Singleton
from ui.actiondialog import ActionDialog

class WelcomePage(tk.Frame):
    def __init__(self, parent, show_page, monitor):
        super().__init__(parent)
        self.show_page = show_page
        self.monitor = monitor

        self.dialog = None  # current ActionDialog instance

        # === Widgets ===
        self.container = tk.Frame(self)
        self.container.pack(expand=True)

        self.title_label = tk.Label(
            self.container,
            text="Welcome to VisionBoard",
            font=(theme.font_bold, theme.sizes["title"])
        )
        self.title_label.pack(pady=(0, 10))

        self.subtitle_label = tk.Label(
            self.container,
            text="Click anywhere to proceed.",
            font=(theme.font_regular, theme.sizes["body"])
        )
        self.subtitle_label.pack()

        # Bind clicks to all widgets to proceed
        for w in (self, self.container, self.title_label, self.subtitle_label):
            w.bind("<Button-1>", self.proceed)

        # Apply initial theme
        self.apply_theme(theme.colors())
        theme.subscribe(self.apply_theme)

        # Auto-unsubscribe on destroy
        self.bind("<Destroy>", self._on_destroy)

        # Subscribe to monitor updates
        self.monitor.subscribe(self.on_system_update)
        self.on_system_update(self.monitor.problems)

    # -----------------------------
    def apply_theme(self, colors):
        """Apply theme colors to all widgets"""
        try:
            self.configure(bg=colors["bg"])
            self.container.configure(bg=colors["bg"])
            self.title_label.configure(bg=colors["bg"], fg=colors["text"])
            self.subtitle_label.configure(bg=colors["bg"], fg=colors["muted"])
        except tk.TclError:
            pass

    def _on_destroy(self, event=None):
        """Unsubscribe from theme manager and monitor when destroyed"""
        if self.apply_theme in theme.subscribers:
            theme.subscribers.remove(self.apply_theme)
        self.monitor.unsubscribe(self.on_system_update)

    # -----------------------------
    def proceed(self, event=None):
        """Navigate to ChooseModel page"""
        self.show_page(ChooseModel, monitor=self.monitor)

    # -----------------------------
    def on_system_update(self, problems):
        """Show error dialog if a problem arises, auto-close if fixed"""
        if problems:
            # Show a new dialog only if none exists
            if not self.dialog:
                def on_exit():
                    # Always navigate to ErrorPage when exiting
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
                
                # Clear reference when dialog destroyed
                self.dialog.bind("<Destroy>", lambda e: setattr(self, 'dialog', None))
            else:
                # Update message if dialog already exists
                self.dialog.update_message("\n".join(problems))
        else:
            # Problems fixed → close dialog if open
            if self.dialog:
                self.dialog.close()
                self.dialog = None
