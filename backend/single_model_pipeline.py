import os
import cv2
import numpy as np
from ultralytics import YOLO
from ui.theme import theme

def get_custom_color(label):
    """
    Returns the BGR color for a defect label from the current theme.
    Defaults to white if the label is not found.
    """
    # Pull the defect_colors from the current theme
    defect_colors = theme.colors().get("defect_colors", {})

    # Get the RGB tuple for the label, default to white
    rgb = defect_colors.get(label, (255, 255, 255))

    # Convert RGB -> BGR for OpenCV
    bgr = tuple(reversed(rgb))
    return bgr


class SingleModelPipeline:
    """
    Single-model pipeline
    - Supports single .pt OR folder of .pt files
    - Safe for maskless PCBs
    """

    MIN_BOX_W = 4
    MIN_BOX_H = 4
    MIN_AREA = 50
    MIN_AREA_RATIO = 0.0001
    MAX_AREA_RATIO = 0.95

    def __init__(self, model_path: str, model_config: dict):
        self.cfg = model_config
        self.model_paths = self._resolve_model_paths(model_path)
        self.models = [YOLO(p) for p in self.model_paths]

    def _resolve_model_paths(self, path):
        if os.path.isfile(path) and path.endswith(".pt"):
            return [path]

        if os.path.isdir(path):
            return [
                os.path.join(path, f)
                for f in os.listdir(path)
                if f.endswith(".pt")
            ]

        return []

    # ---------------- NMS helper ----------------
    def non_max_suppression(self, boxes, scores=None, iou_threshold=0.3):
        if len(boxes) == 0:
            return []

        boxes = np.array(boxes)
        scores = np.array(scores) if scores is not None else np.ones(len(boxes))

        x1 = boxes[:,0]
        y1 = boxes[:,1]
        x2 = boxes[:,2]
        y2 = boxes[:,3]
        areas = (x2 - x1) * (y2 - y1)

        order = scores.argsort()[::-1]
        keep = []

        while order.size > 0:
            i = order[0]
            keep.append(i)
            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])

            w = np.maximum(0.0, xx2 - xx1)
            h = np.maximum(0.0, yy2 - yy1)
            inter = w * h
            iou = inter / (areas[i] + areas[order[1:]] - inter)

            inds = np.where(iou <= iou_threshold)[0]
            order = order[inds + 1]

        return keep

    # ---------------- RUN ----------------
    def run(self, image_path: str, annotated_dir: str, model_name: str):
        os.makedirs(annotated_dir, exist_ok=True)

        img = cv2.imread(image_path)
        if img is None or img.size == 0:
            return None

        img = np.ascontiguousarray(img)
        H, W = img.shape[:2]
        img_area = H * W

        # ---- Brightness sanity check ----
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        mean_val = np.mean(gray)
        if mean_val < 2 or mean_val > 250:
            return None

        all_boxes = []
        all_labels = []
        all_scores = []

        for model, model_path in zip(self.models, self.model_paths):
            results = model.predict(
                image_path,
                conf=self.cfg["conf"],
                iou=self.cfg["iou"],
                max_det=self.cfg["max_det"],
                save=False
            )

            if not results or results[0].boxes is None:
                continue

            boxes = results[0].boxes
            names = model.names

            for i, box in enumerate(boxes.xyxy):
                x1, y1, x2, y2 = map(int, box)
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(W, x2), min(H, y2)

                bw, bh = x2 - x1, y2 - y1
                area = bw * bh

                if bw < self.MIN_BOX_W or bh < self.MIN_BOX_H or area < self.MIN_AREA:
                    continue

                area_ratio = area / img_area
                if area_ratio < self.MIN_AREA_RATIO or area_ratio > self.MAX_AREA_RATIO:
                    continue

                cls_id = int(boxes.cls[i])
                label = names.get(cls_id, "unknown")

                all_boxes.append([x1, y1, x2, y2])
                all_labels.append(label)
                all_scores.append(float(boxes.conf[i]))

        # ---------------- NMS per label ----------------
        final_boxes = []
        final_labels = []
        unique_labels = set(all_labels)

        for lbl in unique_labels:
            inds = [i for i, l in enumerate(all_labels) if l == lbl]
            lbl_boxes = [all_boxes[i] for i in inds]
            lbl_scores = [all_scores[i] for i in inds]

            keep = self.non_max_suppression(lbl_boxes, lbl_scores, iou_threshold=self.cfg.get("nms_iou", 0.3))
            for i in keep:
                final_boxes.append(lbl_boxes[i])
                final_labels.append(lbl)

        # ---------------- Draw final boxes ----------------
        merged_defect_summary = {}
        merged_defects_per_model = {"final": []}

        for box, label in zip(final_boxes, final_labels):
            x1, y1, x2, y2 = box
            color = get_custom_color(label)
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

            merged_defect_summary[label] = merged_defect_summary.get(label, 0) + 1
            merged_defects_per_model["final"].append({
                "label": label,
                "bbox": (x1, y1, x2, y2)
            })

        # ---------------- Save annotated image ----------------
        out_path = os.path.join(annotated_dir, os.path.basename(image_path))
        cv2.imwrite(out_path, img)

        # ---------------- Return result ----------------
        return {
            "defect_summary": merged_defect_summary,
            "defects_per_model": merged_defects_per_model,
            "annotated_image_path": out_path
        }
