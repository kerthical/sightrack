import numpy as np

from models.sixdof import SixDOFModel, SixDOFModelResult
from utilities import smooth_value


class ImageProcessorResult:
    def __init__(self, image: np.ndarray, detected: bool, result: SixDOFModelResult):
        self.image = image
        self.detected = detected
        self.result = result


class ImageProcessor:
    def __init__(self):
        self.sixdof_model = SixDOFModel()
        self.prev_values = {
            "bbox": [0, 0, 0, 0],
            "score": 0.0,
            "yaw": 0.0,
            "pitch": 0.0,
            "roll": 0.0,
        }

    def process_frame(self, image: np.array) -> ImageProcessorResult:
        raw_result = self.sixdof_model.infer(image)

        if raw_result:
            self.prev_values["bbox"][0] = int(smooth_value(self.prev_values["bbox"][0], raw_result.bbox[0]))
            self.prev_values["bbox"][1] = int(smooth_value(self.prev_values["bbox"][1], raw_result.bbox[1]))
            self.prev_values["bbox"][2] = int(smooth_value(self.prev_values["bbox"][2], raw_result.bbox[2]))
            self.prev_values["bbox"][3] = int(smooth_value(self.prev_values["bbox"][3], raw_result.bbox[3]))
            self.prev_values["score"] = smooth_value(self.prev_values["score"], raw_result.score)
            self.prev_values["yaw"] = smooth_value(self.prev_values["yaw"], raw_result.yaw)
            self.prev_values["pitch"] = smooth_value(self.prev_values["pitch"], raw_result.pitch)
            self.prev_values["roll"] = smooth_value(self.prev_values["roll"], raw_result.roll)

        result = SixDOFModelResult(
            bbox=self.prev_values["bbox"],
            score=self.prev_values["score"],
            yaw=self.prev_values["yaw"],
            pitch=self.prev_values["pitch"],
            roll=self.prev_values["roll"],
        )
        image = SixDOFModel.visualize(image, result)

        return ImageProcessorResult(image, bool(raw_result), result)
