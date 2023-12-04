from typing import Tuple, Optional

import cv2
import numpy as np

from models.sixdof import SixDOFModelResult


def smooth_value(
    current_value: float, previous_value: float, smoothing_factor: float = 0.3
) -> float:
    return smoothing_factor * current_value + (1 - smoothing_factor) * previous_value


def estimate_gaze_point(
    image: np.array,
    result: SixDOFModelResult,
) -> Tuple[int, int]:
    return 0, 0


def apply_heatmap(image: np.array, gaze_x: int, gaze_y: int, radius: int) -> np.array:
    heatmap = np.zeros(image.shape[:2], np.float32)
    cv2.circle(heatmap, (gaze_x, gaze_y), radius, (1,), thickness=-1)
    heatmap = cv2.GaussianBlur(heatmap, (51, 51), 0)
    heatmap = np.clip(heatmap / np.max(heatmap) * 255, 0, 255).astype(np.uint8)
    colored_heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
    colored_heatmap = np.dstack((colored_heatmap, np.where(heatmap == 0, 0, 255)))
    overlay = cv2.addWeighted(image, 0.5, colored_heatmap, 0.5, 0)
    return overlay
