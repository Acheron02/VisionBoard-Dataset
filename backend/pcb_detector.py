import cv2
import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple

@dataclass
class PCBDetectionResult:
    detected: bool
    bbox: Optional[Tuple[int, int, int, int]] = None
    area_ratio: float = 0.0

class PCBDetector:
    """
    Robust PCB detector that works for multiple PCB colors under varying illumination.
    """

    MIN_AREA_RATIO = 0.05
    MAX_AREA_RATIO = 0.95
    MIN_ASPECT_RATIO = 0.3
    MAX_ASPECT_RATIO = 3.5

    def detect(self, frame: np.ndarray) -> PCBDetectionResult:
        if frame is None or frame.size == 0:
            return PCBDetectionResult(False)

        H, W = frame.shape[:2]
        frame_area = H * W

        # ---------------- 1️⃣ Preprocessing ----------------
        # Reduce noise and normalize illumination
        blur = cv2.GaussianBlur(frame, (7, 7), 0)
        lab = cv2.cvtColor(blur, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        lab = cv2.merge((l, a, b))
        norm_frame = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

        # ---------------- 2️⃣ Color-agnostic segmentation ----------------
        gray = cv2.cvtColor(norm_frame, cv2.COLOR_BGR2GRAY)

        # Adaptive threshold instead of fixed threshold
        thresh = cv2.adaptiveThreshold(
            gray,
            maxValue=255,
            adaptiveMethod=cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            thresholdType=cv2.THRESH_BINARY_INV,
            blockSize=35,
            C=10
        )

        # ---------------- 3️⃣ Morphology ----------------
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
        morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
        morph = cv2.dilate(morph, kernel, iterations=2)

        # ---------------- 4️⃣ Contour detection ----------------
        contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return PCBDetectionResult(False)

        # ---------------- 5️⃣ Geometry filtering ----------------
        largest = max(contours, key=cv2.contourArea)
        pcb_area = cv2.contourArea(largest)
        area_ratio = pcb_area / frame_area

        if not (self.MIN_AREA_RATIO <= area_ratio <= self.MAX_AREA_RATIO):
            return PCBDetectionResult(False)

        x, y, w, h = cv2.boundingRect(largest)
        aspect_ratio = max(w / h, h / w)
        if not (self.MIN_ASPECT_RATIO <= aspect_ratio <= self.MAX_ASPECT_RATIO):
            return PCBDetectionResult(False)

        return PCBDetectionResult(detected=True, bbox=(x, y, w, h), area_ratio=area_ratio)
