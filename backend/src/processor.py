from typing import Tuple, Optional

import numpy as np

from models.landmark import LandmarkModel
from models.resnet import ResNetModel
from models.yolo import YOLOModel

landmark_model: LandmarkModel = LandmarkModel("./models/landmark.model")
yolo_model: YOLOModel = YOLOModel("./models/yolo.model")
resnet_model: ResNetModel = ResNetModel("./models/resnet.model")


def find_max_confidence_box_and_score(
    boxes: np.ndarray, scores: np.ndarray
) -> Tuple[Optional[np.array], Optional[float]]:
    max_confidence: float = 0
    max_confidence_box: Optional[np.array] = None
    max_confidence_score: Optional[float] = None
    for box, score in zip(boxes, scores):
        confidence: float = (box[2] - box[0]) * (box[3] - box[1]) * score
        if confidence > max_confidence:
            max_confidence = confidence
            max_confidence_box = box
            max_confidence_score = score.item()
    return max_confidence_box, max_confidence_score


def process_frame(
    image: np.array, frame_count: int
) -> Tuple[np.array, bool, float, float, float]:
    landmark = landmark_model.detect(image, frame_count)
    boxes, scores = yolo_model.infer(image)

    if len(boxes) > 0:
        largest_box, largest_score = find_max_confidence_box_and_score(boxes, scores)
        if largest_score > 0.9:
            yaw, pitch, roll = resnet_model.infer(image, largest_box, largest_score)
            image = ResNetModel.visualize(image, largest_box, yaw, pitch, 0)
        else:
            yaw, pitch, roll = -1, -1, -1
    else:
        yaw, pitch, roll = -1, -1, -1

    image = LandmarkModel.visualize(image, landmark)

    return image, len(boxes) > 0, yaw, pitch, roll
