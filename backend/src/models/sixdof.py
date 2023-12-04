import os
import shutil
import tarfile
from math import cos, sin
from typing import Optional, Tuple
from urllib import request

import cv2
import numpy as np
import onnxruntime

MODELS_URL = "https://s3.ap-northeast-2.wasabisys.com/pinto-model-zoo/423_6DRepNet360/resources.tar.gz"
YOLO_MODEL_NAME = "gold_yolo_n_head_post_0277_0.5071_1x3x480x640.onnx"
REPNET_MODEL_NAME = "sixdrepnet360_Nx3x224x224.onnx"


class SixDOFModelResult:
    def __init__(self, bbox: list[int], score: float, yaw: float, pitch: float, roll: float):
        self.bbox = bbox
        self.score = score
        self.yaw = yaw
        self.pitch = pitch
        self.roll = roll

    def to_dict(self):
        return {
            "bbox": self.bbox,
            "score": self.score,
            "yaw": self.yaw,
            "pitch": self.pitch,
            "roll": self.roll,
        }


class SixDOFModel:
    def __init__(self):
        models = ["./models/yolo.model", "./models/resnet.model"]
        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]

        if not all(map(lambda model: os.path.exists(model), models)):
            os.makedirs(os.path.dirname("./models"), exist_ok=True)
            request.urlretrieve(MODELS_URL, "./models/models.tar.gz")
            with tarfile.open("./models/models.tar.gz", "r:gz") as tar:
                tar.extractall("./models/models_tmp/")
            os.rename("./models/models_tmp/%s" % YOLO_MODEL_NAME, models[0])
            os.rename("./models/models_tmp/%s" % REPNET_MODEL_NAME, models[1])
            os.remove("./models/models.tar.gz")
            shutil.rmtree("./models/models_tmp/")

        self.yolo_model = onnxruntime.InferenceSession(models[0], providers=providers)
        self.repnet_model = onnxruntime.InferenceSession(models[1], providers=providers)

    def infer(self, input_image: np.ndarray) -> Optional[SixDOFModelResult]:
        input_shapes: list[Tuple[int, int, int, int]] = [i.shape for i in self.yolo_model.get_inputs()]
        image_height: int = input_image.shape[0]
        image_width: int = input_image.shape[1]
        image: np.ndarray = np.copy(input_image)
        image: np.ndarray = cv2.resize(
            image, (int(input_shapes[0][3]), int(input_shapes[0][2]))
        )
        image: np.ndarray = np.divide(image, 255.0)
        image: np.ndarray = image[..., ::-1]
        image: np.ndarray = image.transpose((2, 0, 1))
        image: np.ndarray = np.ascontiguousarray(image, dtype=np.float32)
        image: np.ndarray = np.asarray([image], dtype=np.float32)
        boxes = self.yolo_model.run(
            [output.name for output in self.yolo_model.get_outputs()],
            {
                input_name: image
                for input_name in [i.name for i in self.yolo_model.get_inputs()]
            },
        )[0]

        box = None
        if len(boxes) > 0:
            scores: np.ndarray = boxes[:, 6:7]
            keep_idxs: np.ndarray = scores[:, 0] > 0.35
            scores_keep: np.ndarray = scores[keep_idxs, :]
            boxes_keep: np.ndarray = boxes[keep_idxs, :]

            if len(boxes_keep) > 0:
                for box, score in zip(boxes_keep, scores_keep):
                    x_min: int = int(max(box[2], 0) * image_width / input_shapes[0][3])
                    y_min: int = int(max(box[3], 0) * image_height / input_shapes[0][2])
                    x_max: int = int(min(box[4], input_shapes[0][3]) * image_width / input_shapes[0][3])
                    y_max: int = int(min(box[5], input_shapes[0][2]) * image_height / input_shapes[0][2])
                    size = (x_max - x_min) * (y_max - y_min)
                    confidence = size * score[0]
                    if box is None or confidence > box[1]:
                        box = ([x_min, y_min, x_max, y_max], confidence)

        if box is None:
            return None

        x1: int = int(box[0][0])
        y1: int = int(box[0][1])
        x2: int = int(box[0][2])
        y2: int = int(box[0][3])
        cx: int = (x1 + x2) // 2
        cy: int = (y1 + y2) // 2
        w: int = abs(x2 - x1)
        h: int = abs(y2 - y1)
        ew: float = w * 1.2
        eh: float = h * 1.2
        ex1: int = int(cx - ew / 2)
        ex2: int = int(cx + ew / 2)
        ey1: int = int(cy - eh / 2)
        ey2: int = int(cy + eh / 2)
        ex1: int = ex1 if ex1 >= 0 else 0
        ex2: int = ex2 if ex2 <= image_width else image_width
        ey1: int = ey1 if ey1 >= 0 else 0
        ey2: int = ey2 if ey2 <= image_height else image_height
        image: np.ndarray = np.copy(input_image)
        image: np.ndarray = image[ey1:ey2, ex1:ex2, :]
        image: np.ndarray = cv2.resize(image, (256, 256))
        image: np.ndarray = image[16:240, 16:240, :]
        image: np.ndarray = image[..., ::-1]
        image: np.ndarray = (image / 255.0 - np.asarray([0.485, 0.456, 0.406], dtype=np.float32)) / np.asarray([0.229, 0.224, 0.225], dtype=np.float32)
        image: np.ndarray = image.transpose(2, 0, 1)
        image: np.ndarray = image[np.newaxis, ...]
        image: np.ndarray = image.astype(np.float32)
        rotation: np.ndarray = self.repnet_model.run(None, {"input": image})[0]
        yaw_deg: float = rotation[0][0].item()
        pitch_deg: float = rotation[0][1].item()
        roll_deg: float = rotation[0][2].item()

        return SixDOFModelResult(box[0], float(box[1]), yaw_deg, pitch_deg, roll_deg)

    @staticmethod
    def visualize(input_image: np.ndarray, result: SixDOFModelResult) -> np.ndarray:
        image = np.copy(input_image)
        x1: int = result.bbox[0]
        y1: int = result.bbox[1]
        x2: int = result.bbox[2]
        y2: int = result.bbox[3]
        tdx: float = float((x1 + x2) // 2)
        tdy: float = float((y1 + y2) // 2)
        pitch: float = result.pitch * np.pi / 180
        yaw: float = -(result.yaw * np.pi / 180)
        roll: float = result.roll * np.pi / 180
        size: int = 600
        x1: float = size * (cos(yaw) * cos(roll)) + tdx
        y1: float = size * (cos(pitch) * sin(roll) + cos(roll) * sin(pitch) * sin(yaw)) + tdy
        x2: float = size * (-cos(yaw) * sin(roll)) + tdx
        y2: float = size * (cos(pitch) * cos(roll) - sin(pitch) * sin(yaw) * sin(roll)) + tdy
        x3: float = size * (sin(yaw)) + tdx
        y3: float = size * (-cos(yaw) * sin(pitch)) + tdy
        face_width = result.bbox[2] - result.bbox[0]
        face_height = result.bbox[3] - result.bbox[1]
        face_size = (face_width + face_height) / 2
        face_center = ((result.bbox[0] + result.bbox[2]) / 2, (result.bbox[1] + result.bbox[3]) / 2)
        camera_distance = 0.5 * 360 / np.tan(face_size / 2)
        gaze_direction = np.array([np.cos(result.yaw) * np.cos(result.pitch), np.sin(result.yaw) * np.cos(result.pitch), np.sin(result.pitch)])
        gaze_point = np.array(face_center) + camera_distance * gaze_direction
        gaze_point[0] = np.clip(gaze_point[0], 0, input_image.shape[1] - 1)
        gaze_point[1] = np.clip(gaze_point[1], 0, input_image.shape[0] - 1)
        heatmap = np.zeros((input_image.shape[0], input_image.shape[1]), dtype=np.float32)
        cv2.circle(heatmap, (int(gaze_point[0]), int(gaze_point[1])), int(face_size), (1,), -1)
        heatmap_color = cv2.applyColorMap((heatmap * 255).astype(np.uint8), cv2.COLORMAP_JET)

        image = cv2.rectangle(image, (result.bbox[0], result.bbox[1]), (result.bbox[2], result.bbox[3]), (0, 0, 255), 2)
        image = cv2.putText(image, "score: %.2f" % result.score, (result.bbox[0], result.bbox[3] + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        image = cv2.putText(image, "yaw: %.2f" % result.yaw, (result.bbox[0], result.bbox[3] + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        image = cv2.putText(image, "pitch: %.2f" % result.pitch, (result.bbox[0], result.bbox[3] + 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        image = cv2.putText(image, "roll: %.2f" % result.roll, (result.bbox[0], result.bbox[3] + 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        image = cv2.line(image, (int(tdx), int(tdy)), (int(x1), int(y1)), (255, 0, 0), 3)
        image = cv2.line(image, (int(tdx), int(tdy)), (int(x2), int(y2)), (0, 255, 0), 3)
        image = cv2.line(image, (int(tdx), int(tdy)), (int(x3), int(y3)), (0, 0, 255), 3)
        image = cv2.addWeighted(image, 0.7, heatmap_color, 0.3, 0)

        return image
