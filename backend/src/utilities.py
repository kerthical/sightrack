from typing import Tuple, Optional
import cv2
import numpy as np


def find_max_confidence_box_and_score(
    boxes: np.ndarray, scores: np.ndarray
) -> Tuple[Optional[np.array], Optional[float]]:
    confidences = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1]) * scores
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
