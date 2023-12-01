from typing import Tuple, Optional

import numpy as np

from models.resnet import ResNetModel
from models.yolo import YOLOModel
from utilities import find_max_confidence_box_and_score, estimate_gaze_point, smooth_value, apply_heatmap


class ImageProcessorResult:
    def __init__(self,
                 image: np.array,
                 detected: bool,
                 yaw: float,
                 pitch: float,
                 roll: float,
                 gaze_x: float,
                 gaze_y: float,
                 largest_box: Optional[Tuple[float, float, float, float]],
                 largest_score: Optional[float]):
        self.image = image
        self.detected = detected
        self.yaw = yaw
        self.pitch = pitch
        self.roll = roll
        self.gaze_x = gaze_x
        self.gaze_y = gaze_y
        self.largest_box = largest_box
        self.largest_score = largest_score


class ImageProcessor:
    def __init__(self):
        self.yolo_model = YOLOModel("./models/yolo.model")
        self.resnet_model = ResNetModel("./models/resnet.model")
        self.prev_values = {'yaw': 0, 'pitch': 0, 'roll': 0, 'gaze_x': 0, 'gaze_y': 0}

    def process_frame(self, image: np.array) -> ImageProcessorResult:
        boxes, scores = self.yolo_model.infer(image)
        box, score = find_max_confidence_box_and_score(boxes, scores) if boxes else (None, None)
        yaw, pitch, roll, gaze_x, gaze_y = self.resnet_model.infer(image, box, score) if box else (0, 0, 0, 0, 0)
        gaze_x, gaze_y = estimate_gaze_point(image, yaw, pitch, box) if box else (0, 0)

        for key in self.prev_values.keys():
            self.prev_values[key] = smooth_value(locals()[key], self.prev_values[key])

        if box:
            image = ResNetModel.visualize(image, box, yaw, pitch, 0)
            image = apply_heatmap(image, int(gaze_x), int(gaze_y), int((1 - score) * (box[2] - box[0])))

        return ImageProcessorResult(
            image=image,
            detected=bool(box),
            yaw=self.prev_values['yaw'],
            pitch=self.prev_values['pitch'],
            roll=self.prev_values['roll'],
            gaze_x=self.prev_values['gaze_x'],
            gaze_y=self.prev_values['gaze_y'],
            largest_box=box,
            largest_score=score
        )
