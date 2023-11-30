from typing import Tuple, Optional

import cv2
import numpy as np

from models.landmark import LandmarkModel
from models.resnet import ResNetModel
from models.yolo import YOLOModel


class ImageProcessor:
    def __init__(self, smoothing_factor: float = 0.3):
        self.landmark_model = LandmarkModel("./models/landmark.model")
        self.yolo_model = YOLOModel("./models/yolo.model")
        self.resnet_model = ResNetModel("./models/resnet.model")
        self.smoothing_factor = smoothing_factor
        self.prev_yaw = 0
        self.prev_pitch = 0
        self.prev_roll = 0
        self.prev_gaze_x = 0
        self.prev_gaze_y = 0

    def smooth_value(self, current_value: float, previous_value: float) -> float:
        return (
            self.smoothing_factor * current_value
            + (1 - self.smoothing_factor) * previous_value
        )

    @staticmethod
    def estimate_gaze_point(
            image: np.array, yaw: float, pitch: float, head_box: Tuple[float, float, float, float]
    ) -> Tuple[int, int]:
        width = image.shape[1]
        height = image.shape[0]
        face_center_x = (head_box[0] + head_box[2]) / 2
        face_center_y = (head_box[1] + head_box[3]) / 2
        yaw_rad = np.deg2rad(yaw)
        pitch_rad = np.deg2rad(pitch)
        gaze_x = face_center_x + (yaw_rad * width / 2)
        gaze_y = face_center_y - (pitch_rad * height / 2)
        gaze_x = np.clip(gaze_x, 0, width)
        gaze_y = np.clip(gaze_y, 0, height)

        return int(gaze_x), int(gaze_y)


    @staticmethod
    def apply_heatmap(
        image: np.array, gaze_x: int, gaze_y: int, radius: int
    ) -> np.array:
        heatmap = np.zeros((image.shape[0], image.shape[1]), np.float32)
        cv2.circle(heatmap, (gaze_x, gaze_y), radius, (1,), thickness=-1)
        heatmap = cv2.GaussianBlur(heatmap, (51, 51), 0)
        heatmap = heatmap / np.max(heatmap)
        heatmap = np.clip(heatmap * 255, 0, 255)
        heatmap = heatmap.astype(np.uint8)
        colored_heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
        alpha_channel = np.ones(heatmap.shape, dtype=heatmap.dtype) * 255
        alpha_channel[heatmap == 0] = 0
        colored_heatmap = np.dstack((colored_heatmap, alpha_channel))
        if image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
            overlay = cv2.addWeighted(image, 1.0, colored_heatmap, 0.5, 0)
            overlay = cv2.cvtColor(overlay, cv2.COLOR_BGRA2BGR)
        else:
            overlay = cv2.addWeighted(image, 1.0, colored_heatmap, 0.5, 0)

        return overlay

    @staticmethod
    def find_max_confidence_box_and_score(
        boxes: np.ndarray, scores: np.ndarray
    ) -> Tuple[Optional[np.array], Optional[float]]:
        max_confidence = 0
        max_confidence_box = None
        max_confidence_score = None
        for box, score in zip(boxes, scores):
            confidence = (box[2] - box[0]) * (box[3] - box[1]) * score
            if confidence > max_confidence:
                max_confidence = confidence
                max_confidence_box = box
                max_confidence_score = score.item()
        return max_confidence_box, max_confidence_score

    def process_frame(
        self, image: np.array
    ) -> Tuple[np.array, bool, float, float, float, float, float, np.array, float]:
        boxes, scores = self.yolo_model.infer(image)
        yaw, pitch, roll, gaze_x, gaze_y = 0, 0, 0, 0, 0
        largest_box, largest_score = None, None

        if len(boxes) > 0:
            largest_box, largest_score = self.find_max_confidence_box_and_score(
                boxes, scores
            )
            yaw, pitch, roll = self.resnet_model.infer(
                image, largest_box, largest_score
            )
            gaze_x, gaze_y = self.estimate_gaze_point(image, yaw, pitch, largest_box)

            yaw = self.smooth_value(yaw, self.prev_yaw)
            pitch = self.smooth_value(pitch, self.prev_pitch)
            roll = self.smooth_value(roll, self.prev_roll)
            gaze_x = self.smooth_value(gaze_x, self.prev_gaze_x)
            gaze_y = self.smooth_value(gaze_y, self.prev_gaze_y)
            image = ResNetModel.visualize(image, largest_box, yaw, pitch, 0)
            image = self.apply_heatmap(
                image,
                int(gaze_x),
                int(gaze_y),
                int((1 - largest_score) * (largest_box[2] - largest_box[0])),
            )

            self.prev_yaw = yaw
            self.prev_pitch = pitch
            self.prev_roll = roll
            self.prev_gaze_x = gaze_x
            self.prev_gaze_y = gaze_y

        return image, len(boxes) > 0, yaw, pitch, 0, gaze_x, gaze_y, largest_box, largest_score
