import tkinter as tk
from ui.theme import theme
from ui.roundedbutton import RoundedButton
from backend.systemmonitor import SystemMonitor


class ErrorPage(tk.Frame):
    """Page displayed when system problems exist."""

    def __init__(self, parent, show_page, monitor, problems=None, next_page=None, next_page_kwargs=None):
        super().__init__(parent)
        self.show_page = show_page            # callable from main.py
        self.monitor = monitor                # SystemMonitor instance
        self.problems = problems or []
        self.next_page = next_page            # page to navigate after fixing problems
        self.next_page_kwargs = next_page_kwargs or {}  # store kwargs for next page

        colors = theme.colors()
        self.configure(bg=colors["bg"])

        # Container
        self.container = tk.Frame(self, bg=colors["bg"])
        self.container.pack(expand=True)

        # Title
        self.title_label = tk.Label(
            self.container,
            text="Please fix the problem first.",
            font=(theme.font_bold, theme.sizes["title"]),
            fg=colors["text"],
            bg=colors["bg"]
        )
        self.title_label.pack(pady=(0, 20))

        # Problems list
        self.problem_label = tk.Label(
            self.container,
            font=(theme.font_regular, theme.sizes["body"]),
            fg=colors["muted"],
            bg=colors["bg"],
            justify="left"
        )
        self.problem_label.pack()

        # Continue button
        self.continue_btn = RoundedButton(
            self.container,
            text="Continue",
            width=180,
            height=80,
            radius=20,
            font=(theme.font_regular, theme.sizes["body"]),
            command=self._on_continue,
            disabled=True
        )
        self.continue_btn.pack(pady=(20, 0))

        # Initial update
        self._update_problem_list()
        self._update_continue_button()

        # Subscribe to theme changes
        theme.subscribe(self.apply_theme)

        # Subscribe to monitor updates
        self.monitor.subscribe(self._on_system_update)

        # Cleanup on destroy
        self.bind("<Destroy>", self._on_destroy)

    # -----------------------------
    # SystemMonitor callback
    # -----------------------------
    def _on_system_update(self, problems):
        self.problems = problems
        self._update_problem_list()
        self._update_continue_button()

    # -----------------------------
    # Update problem list
    # -----------------------------
    def _update_problem_list(self):
        if self.problems:
            text = "\n".join(f"- {p}" for p in self.problems)
        else:
            text = "No problems detected."
        self.problem_label.config(text=text)

    # -----------------------------
    # Continue button logic
    # -----------------------------
    def _update_continue_button(self):
        if not self.problems:
            self.title_label.config(text="All problems fixed! You may continue.")
            self.continue_btn.set_disabled(False)
        else:
            self.title_label.config(text="Please fix the problem first.")
            self.continue_btn.set_disabled(True)

    def _on_continue(self):
        if not self.continue_btn.disabled and self.next_page:
            # Pass kwargs to next_page if available
            self.show_page(self.next_page, **self.next_page_kwargs)

    # -----------------------------
    # Theme handling
    # -----------------------------
    def apply_theme(self, colors):
        try:
            self.configure(bg=colors["bg"])
            self.container.configure(bg=colors["bg"])
            self.title_label.configure(bg=colors["bg"], fg=colors["text"])
            self.problem_label.configure(bg=colors["bg"], fg=colors["muted"])
        except tk.TclError:
            pass

    # -----------------------------
    # Cleanup
    # -----------------------------
    def _on_destroy(self, event=None):
        self.monitor.unsubscribe(self._on_system_update)
        if self.apply_theme in theme.subscribers:
            theme.subscribers.remove(self.apply_theme)
