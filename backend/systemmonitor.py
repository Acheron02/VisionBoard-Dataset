import cv2
import socket
import threading
import time
import urllib.request


class SystemMonitor:
    """Continuously monitors camera and internet (robust, long-running safe)."""

    CHECK_INTERVAL = 3  # seconds
    INTERNET_FAIL_THRESHOLD = 3  # consecutive failures before offline
    INTERNET_TIMEOUT = 3  # seconds for server response

    def __init__(self):
        self.problems = []
        self.subscribers = []
        self._running = False
        self._thread = None

        # === CAMERA OWNERSHIP FLAGS ===
        self.camera_in_use = False
        self.suppress_updates = False

        # === INTERNET STATE ===
        self._internet_fail_count = 0

    # -------------------------------------------------
    def start(self):
        if not self._running:
            self._running = True
            self._thread = threading.Thread(
                target=self._run_loop,
                daemon=True
            )
            self._thread.start()

    def stop(self):
        self._running = False

    # -------------------------------------------------
    def subscribe(self, callback):
        if callback not in self.subscribers:
            self.subscribers.append(callback)

    def unsubscribe(self, callback):
        if callback in self.subscribers:
            self.subscribers.remove(callback)

    # -------------------------------------------------
    # Camera ownership helpers
    # -------------------------------------------------
    def pause_camera_check(self):
        self.camera_in_use = True
        self._remove_camera_problem()

    def resume_camera_check(self):
        self.camera_in_use = False

    def _remove_camera_problem(self):
        new_problems = [p for p in self.problems if "camera" not in p.lower()]
        if new_problems != self.problems:
            self.problems = new_problems
            self._notify()

    # -------------------------------------------------
    # INTERNET CHECK (ROBUST)
    # -------------------------------------------------
    def _has_internet(self):
        """
        Check internet connection with HTTP request to a reliable lightweight endpoint.
        Returns True if connection works within timeout.
        """
        try:
            urllib.request.urlopen("http://clients3.google.com/generate_204", timeout=self.INTERNET_TIMEOUT)
            return True
        except:
            return False

    # -------------------------------------------------
    def _notify(self):
        for cb in self.subscribers:
            cb(self.problems)

    # -------------------------------------------------
    def _run_loop(self):
        while self._running:
            if self.suppress_updates:
                time.sleep(self.CHECK_INTERVAL)
                continue

            problems = []

            # ===== CAMERA CHECK =====
            if not self.camera_in_use:
                cap = cv2.VideoCapture(0)
                if not cap.isOpened():
                    problems.append("No camera detected. Ensure a camera is connected.")
                cap.release()

            # ===== INTERNET CHECK =====
            if self._has_internet():
                self._internet_fail_count = 0
            else:
                self._internet_fail_count += 1

            # Only show warning if consecutive failures exceed threshold
            if self._internet_fail_count >= self.INTERNET_FAIL_THRESHOLD:
                problems.append("No internet connection. Please connect to a network.")

            # ===== Notify subscribers ONLY on change =====
            if problems != self.problems:
                self.problems = problems
                self._notify()

            time.sleep(self.CHECK_INTERVAL)
