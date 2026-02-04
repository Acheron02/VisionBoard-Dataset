import tkinter as tk
from pages.welcomepage import WelcomePage
import subprocess
import sys
import os
import atexit
import inspect
import time
import requests

from ui.themetoggle import ThemeToggleButton
from ui.theme import theme
from backend.systemmonitor import SystemMonitor

# ==============================
# SCREEN CONFIG (KIOSK)
# ==============================
SCREEN_W = 1024
SCREEN_H = 600

# ==============================
# NGROK SETUP
# ==============================
def start_ngrok(port=5000):
    """Start ngrok and return the process, suppressing stdout/stderr."""
    ngrok_process = subprocess.Popen(
        ["ngrok", "http", str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    atexit.register(lambda: terminate_process(ngrok_process))
    return ngrok_process

def get_ngrok_url(retry=10, delay=1):
    """Get the public HTTPS ngrok URL from local API with retries."""
    for _ in range(retry):
        try:
            tunnels = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=1).json()
            for t in tunnels.get('tunnels', []):
                if t.get('proto') == 'https':
                    return t.get('public_url')
        except Exception:
            time.sleep(delay)
    return None

def terminate_process(proc):
    """Terminate a subprocess gracefully."""
    if proc and proc.poll() is None:
        try:
            proc.terminate()
            proc.wait(timeout=1)
        except Exception:
            pass

# ==============================
# MAIN APP
# ==============================
def main():
    # ------------------------------
    # Start Flask webserver
    # ------------------------------
    webserver_path = os.path.join(
        os.path.dirname(__file__), "server", "webserver.py"
    )
    flask_process = subprocess.Popen(
        [sys.executable, webserver_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    atexit.register(lambda: terminate_process(flask_process))

    # ------------------------------
    # Start ngrok tunnel
    # ------------------------------
    ngrok_process = start_ngrok(port=5000)
    public_url = get_ngrok_url()
    if public_url:
        print(f"Ngrok public URL: {public_url}")
        os.environ["NGROK_URL"] = public_url
    else:
        print("Failed to get ngrok URL. QR codes may not work.")

    # ------------------------------
    # System Monitor
    # ------------------------------
    monitor = SystemMonitor()
    monitor.start()

    # ------------------------------
    # Tk App
    # ------------------------------
    root = tk.Tk()
    root.title("VisionBoard")

    root.geometry(f"{SCREEN_W}x{SCREEN_H}+0+0")
    root.minsize(SCREEN_W, SCREEN_H)
    root.maxsize(SCREEN_W, SCREEN_H)
    root.resizable(False, False)
    root.config(cursor="none")  # hide cursor

    # Kiosk mode
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.after(200, lambda: root.attributes("-topmost", False))
    root.tk.call("tk", "scaling", SCREEN_W / 1280)

    # ------------------------------
    # SAFE EXIT HANDLER
    # ------------------------------
    def quit_app(event=None):
        """Cleanly exit everything without terminal mess."""
        monitor.stop()
        terminate_process(flask_process)
        terminate_process(ngrok_process)
        try:
            root.quit()
            root.destroy()
        except Exception:
            pass

    root.bind_all("<Escape>", quit_app)

    # ------------------------------
    # GLOBAL THEME TOGGLE
    # ------------------------------
    toggle = ThemeToggleButton(root, theme)
    toggle.place(relx=1.0, x=-30, y=10, anchor="ne")
    root.toggle = toggle

    # ------------------------------
    # PAGE MANAGEMENT
    # ------------------------------
    current_page = None

    def show_page(page_class, **kwargs):
        nonlocal current_page

        if current_page:
            current_page.destroy()

        sig = inspect.signature(page_class.__init__)
        valid_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}

        if "monitor" in sig.parameters:
            valid_kwargs.setdefault("monitor", monitor)
        if "theme" in sig.parameters:
            valid_kwargs.setdefault("theme", theme)
        if "ngrok_url" in sig.parameters and public_url:
            valid_kwargs.setdefault("ngrok_url", public_url)

        current_page = page_class(root, show_page, **valid_kwargs)
        current_page.pack(fill="both", expand=True)
        toggle.lift()  # Keep toggle above everything

    # ------------------------------
    # START APP
    # ------------------------------
    show_page(WelcomePage)
    root.mainloop()

    # Final cleanup
    terminate_process(flask_process)
    terminate_process(ngrok_process)
    monitor.stop()


if __name__ == "__main__":
    main()
