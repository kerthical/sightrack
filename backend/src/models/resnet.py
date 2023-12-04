import copy
import os
import shutil
import tarfile
import urllib.request
from math import sin, cos

import cv2
import numpy as np
import onnxruntime

from .yolo import YOLOModelResult

RESNET_MODEL_URL: str = "https://s3.ap-northeast-2.wasabisys.com/pinto-model-zoo/423_6DRepNet360/resources.tar.gz"


class ResNetModelResult:
    def __init__(self, yaw: float, pitch: float, roll: float):
        self.yaw = yaw
        self.pitch = pitch
        self.roll = roll


class ResNetModel:
    def __init__(self, model_path: str):
        if not os.path.exists(model_path):
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            urllib.request.urlretrieve(
                RESNET_MODEL_URL,
                model_path + ".tar.gz",
            )
            with tarfile.open(model_path + ".tar.gz", "r:gz") as tar:
                tar.extractall(model_path + "_tmp/")
            os.rename(
                model_path + "_tmp/sixdrepnet360_Nx3x224x224.onnx",
                model_path,
            )
            os.remove(model_path + ".tar.gz")
            shutil.rmtree(model_path + "_tmp/")

        self.onnx_session = onnxruntime.InferenceSession(
            model_path,
            providers=[
                "CUDAExecutionProvider",
                "CPUExecutionProvider",
            ],
        )

    def infer(self, image: np.ndarray, result: YOLOModelResult) -> ResNetModelResult:
        mean: np.ndarray = np.asarray([0.485, 0.456, 0.406], dtype=np.float32)
        std: np.ndarray = np.asarray([0.229, 0.224, 0.225], dtype=np.float32)
        box = result.bbox

        debug_image: np.ndarray = copy.deepcopy(image)

        image_height: int = debug_image.shape[0]
        image_width: int = debug_image.shape[1]

        x1: int = int(box[0])
        y1: int = int(box[1])
        x2: int = int(box[2])
        y2: int = int(box[3])

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

        inference_image: np.ndarray = copy.deepcopy(debug_image)
        head_image_bgr: np.ndarray = inference_image[ey1:ey2, ex1:ex2, :]
        resized_image_bgr: np.ndarray = cv2.resize(head_image_bgr, (256, 256))
        cropped_image_bgr: np.ndarray = resized_image_bgr[16:240, 16:240, :]

        cropped_image_rgb: np.ndarray = cropped_image_bgr[..., ::-1]
        normalized_image_rgb: np.ndarray = (cropped_image_rgb / 255.0 - mean) / std
        normalized_image_rgb: np.ndarray = normalized_image_rgb.transpose(2, 0, 1)
        normalized_image_rgb: np.ndarray = normalized_image_rgb[np.newaxis, ...]
        normalized_image_rgb: np.ndarray = normalized_image_rgb.astype(np.float32)
        yaw_pitch_roll: np.ndarray = self.onnx_session.run(
            None,
            {"input": normalized_image_rgb},
        )[0]
        yaw_deg: float = yaw_pitch_roll[0][0].item()
        pitch_deg: float = yaw_pitch_roll[0][1].item()
        roll_deg: float = yaw_pitch_roll[0][2].item()

        return ResNetModelResult(yaw_deg, pitch_deg, roll_deg)

    @staticmethod
    def visualize(
        image: np.ndarray,
        box: YOLOModelResult,
        rotation: ResNetModelResult,
    ) -> np.ndarray:
        annotated_image: np.ndarray = copy.deepcopy(image)
        size: int = 600
        x1: int = box.bbox[0]
        y1: int = box.bbox[1]
        x2: int = box.bbox[2]
        y2: int = box.bbox[3]
        tdx: float = float((x1 + x2) // 2)
        tdy: float = float((y1 + y2) // 2)

        pitch: float = rotation.pitch * np.pi / 180
        yaw: float = -(rotation.yaw * np.pi / 180)
        roll: float = rotation.roll * np.pi / 180

        x1: float = size * (cos(yaw) * cos(roll)) + tdx
        y1: float = (
            size * (cos(pitch) * sin(roll) + cos(roll) * sin(pitch) * sin(yaw)) + tdy
        )
        x2: float = size * (-cos(yaw) * sin(roll)) + tdx
        y2: float = (
            size * (cos(pitch) * cos(roll) - sin(pitch) * sin(yaw) * sin(roll)) + tdy
        )
        x3: float = size * (sin(yaw)) + tdx
        y3: float = size * (-cos(yaw) * sin(pitch)) + tdy

        cv2.line(
            annotated_image, (int(tdx), int(tdy)), (int(x1), int(y1)), (0, 0, 255), 2
        )
        cv2.line(
            annotated_image, (int(tdx), int(tdy)), (int(x2), int(y2)), (0, 255, 0), 2
        )
        cv2.line(
            annotated_image, (int(tdx), int(tdy)), (int(x3), int(y3)), (255, 0, 0), 2
        )

        return annotated_image
