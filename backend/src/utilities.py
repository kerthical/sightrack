from typing import Tuple, Optional, List

import cv2
import numpy as np


class BoundingBox:
    def __init__(self, x1: float, y1: float, x2: float, y2: float):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

    @classmethod
    def from_array(cls, arr: np.ndarray):
        return cls(*arr)

    def to_array(self) -> np.ndarray:
        return np.array([self.x1, self.y1, self.x2, self.y2])


def find_max_confidence_box_and_score(boxes: List[BoundingBox], scores: np.ndarray) -> Optional[Tuple[BoundingBox, float]]:
    boxes_array = np.array([box.to_array() for box in boxes])
    confidences = (boxes_array[:, 2] - boxes_array[:, 0]) * (boxes_array[:, 3] - boxes_array[:, 1]) * scores
    max_confidence_index = np.argmax(confidences)
    return boxes[max_confidence_index], scores[max_confidence_index].item()


def smooth_value(
        current_value: float, previous_value: float, smoothing_factor: float = 0.3
) -> float:
    return smoothing_factor * current_value + (1 - smoothing_factor) * previous_value


def estimate_gaze_point(
        image: np.array,
        yaw: float,
        pitch: float,
        head_box: Tuple[float, float, float, float],
) -> Tuple[int, int]:
    return 0, 0


def apply_heatmap(image: np.array, gaze_x: int, gaze_y: int, radius: int) -> np.array:
    heatmap = np.zeros(image.shape[:2], np.float32)
    cv2.circle(heatmap, (gaze_x, gaze_y), radius, (1,), thickness=-1)
    heatmap = cv2.GaussianBlur(heatmap, (51, 51), 0)
    heatmap = np.clip(heatmap / np.max(heatmap) * 255, 0, 255).astype(np.uint8)
    colored_heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
    colored_heatmap = np.dstack((colored_heatmap, np.where(heatmap == 0, 0, 255)))
    overlay = cv2.addWeighted(
        cv2.cvtColor(image, cv2.COLOR_BGR2BGRA), 1.0, colored_heatmap, 0.5, 0
    )
    return cv2.cvtColor(overlay, cv2.COLOR_BGRA2BGR) if image.shape[2] == 3 else overlay
