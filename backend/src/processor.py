from typing import Optional

import numpy as np

from models.resnet import ResNetModel, ResNetModelResult
from models.yolo import YOLOModel, YOLOModelResult
from utilities import (
    find_max_confidence_result,
    smooth_value,
)


class ImageProcessorResult:
    def __init__(
        self,
        image: np.array,
        box: Optional[YOLOModelResult],
        rotation: Optional[ResNetModelResult],
    ):
        self.image = image
        self.detected = bool(box)
        self.box = box
        self.rotation = rotation


class ImageProcessor:
    def __init__(self):
        self.yolo_model = YOLOModel("./models/yolo.model")
        self.resnet_model = ResNetModel("./models/resnet.model")
        self.prev_values = {
            "box": {
                "bbox": [0, 0, 0, 0],
                "score": 0.0,
            },
            "rotation": {
                "yaw": 0.0,
                "pitch": 0.0,
                "roll": 0.0,
            },
        }

    def process_frame(self, image: np.array) -> ImageProcessorResult:
        boxes = self.yolo_model.infer(image)
        box = find_max_confidence_result(boxes) if len(boxes) else None
        rotation = (self.resnet_model.infer(image, box) if box else None)

        if box:
            self.prev_values["box"]["bbox"][0] = int(smooth_value(self.prev_values["box"]["bbox"][0], box.bbox[0]))
            self.prev_values["box"]["bbox"][1] = int(smooth_value(self.prev_values["box"]["bbox"][1], box.bbox[1]))
            self.prev_values["box"]["bbox"][2] = int(smooth_value(self.prev_values["box"]["bbox"][2], box.bbox[2]))
            self.prev_values["box"]["bbox"][3] = int(smooth_value(self.prev_values["box"]["bbox"][3], box.bbox[3]))
            self.prev_values["box"]["score"] = smooth_value(self.prev_values["box"]["score"], box.score)

            self.prev_values["rotation"]["yaw"] = smooth_value(self.prev_values["rotation"]["yaw"], rotation.yaw)
            self.prev_values["rotation"]["pitch"] = smooth_value(self.prev_values["rotation"]["pitch"], rotation.pitch)
            self.prev_values["rotation"]["roll"] = smooth_value(self.prev_values["rotation"]["roll"], rotation.roll)

            box = YOLOModelResult(self.prev_values["box"]["bbox"], self.prev_values["box"]["score"])
            rotation = ResNetModelResult(self.prev_values["rotation"]["yaw"], self.prev_values["rotation"]["pitch"], self.prev_values["rotation"]["roll"])
            image = YOLOModel.visualize(image, box)
            image = ResNetModel.visualize(image, box, rotation)

        return ImageProcessorResult(
            image=image,
            box=box,
            rotation=rotation,
        )