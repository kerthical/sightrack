import os
import shutil
import tarfile
from math import cos, sin
from typing import Optional, Tuple
from urllib import request

import cv2
import numpy as np
import rerun as rr
import onnxruntime

MODELS_URL = "https://s3.ap-northeast-2.wasabisys.com/pinto-model-zoo/423_6DRepNet360/resources.tar.gz"
YOLO_MODEL_NAME = "gold_yolo_n_head_post_0277_0.5071_1x3x480x640.onnx"
REPNET_MODEL_NAME = "sixdrepnet360_Nx3x224x224.onnx"


class SixDOFModelResult:
    def __init__(self, bbox: list[float], score: float, yaw: float, pitch: float, roll: float):
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
            print("[*] Model not found in ./models, downloading...", end=" ")
            os.makedirs("./models", exist_ok=True)
            request.urlretrieve(MODELS_URL, "./models/models.tar.gz")
            with tarfile.open("./models/models.tar.gz", "r:gz") as tar:
                tar.extractall("./models/models_tmp/")
            os.replace("./models/models_tmp/%s" % YOLO_MODEL_NAME, models[0])
            os.replace("./models/models_tmp/%s" % REPNET_MODEL_NAME, models[1])
            os.remove("./models/models.tar.gz")
            shutil.rmtree("./models/models_tmp/")
            print("(Done)")

        self.yolo_model = onnxruntime.InferenceSession(models[0], providers=providers)
        self.repnet_model = onnxruntime.InferenceSession(models[1], providers=providers)

    def inference(self, input_image: np.ndarray) -> Optional[SixDOFModelResult]:
        input_shapes: list[Tuple[int, int, int, int]] = [i.shape for i in self.yolo_model.get_inputs()]
        image_height: int = input_image.shape[0]
        image_width: int = input_image.shape[1]
        image = np.copy(input_image)
        image = cv2.resize(image, (int(input_shapes[0][3]), int(input_shapes[0][2])))
        image = np.divide(image, 255.0)
        image = image[..., ::-1]
        image = image.transpose((2, 0, 1))
        image = np.ascontiguousarray(image, dtype=np.float32)
        image = np.asarray([image], dtype=np.float32)
        boxes = self.yolo_model.run(
            [output.name for output in self.yolo_model.get_outputs()],
            {input_name: image for input_name in [i.name for i in self.yolo_model.get_inputs()]},
        )[0]

        box = None
        if len(boxes) > 0:
            scores: np.ndarray = boxes[:, 6:7]
            keep_ids: np.ndarray = scores[:, 0] > 0.5
            scores_keep: np.ndarray = scores[keep_ids, :]
            boxes_keep: np.ndarray = boxes[keep_ids, :]

            if len(boxes_keep) > 0:
                for b, s in zip(boxes_keep, scores_keep):
                    x_min: int = int(max(b[2], 0) * image_width / input_shapes[0][3])
                    y_min: int = int(max(b[3], 0) * image_height / input_shapes[0][2])
                    x_max: int = int(min(b[4], input_shapes[0][3]) * image_width / input_shapes[0][3])
                    y_max: int = int(min(b[5], input_shapes[0][2]) * image_height / input_shapes[0][2])
                    size = ((x_max - x_min) * (y_max - y_min)) / (image_width * image_height)
                    confidence = s[0] * size
                    if box is None or confidence > box[1]:
                        box = ([x_min, y_min, x_max, y_max], s[0])

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
        image = np.copy(input_image)
        image = image[ey1:ey2, ex1:ex2, :]
        image = cv2.resize(image, (256, 256))
        image = image[16:240, 16:240, :]
        image = image[..., ::-1]
        image = (image / 255.0 - np.asarray([0.485, 0.456, 0.406], dtype=np.float32)) / np.asarray(
            [0.229, 0.224, 0.225], dtype=np.float32
        )
        image = image.transpose(2, 0, 1)
        image = image[np.newaxis, ...]
        image = image.astype(np.float32)
        rotation = self.repnet_model.run(None, {"input": image})[0]
        yaw_deg: float = rotation[0][0].item()
        pitch_deg: float = rotation[0][1].item()
        roll_deg: float = rotation[0][2].item()

        return SixDOFModelResult(box[0], float(box[1]), yaw_deg, pitch_deg, roll_deg)

    @staticmethod
    def visualize_raw(input_image: np.ndarray, result: SixDOFModelResult):
        image = np.copy(input_image)
        cv2.rectangle(image, (int(result.bbox[0]), int(result.bbox[1])), (int(result.bbox[2]), int(result.bbox[3])), (0, 255, 0), 2)
        cv2.putText(image, "yaw=%.2f, pitch=%.2f, roll=%.2f" % (result.yaw, result.pitch, result.roll), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        draw_axis(image, result.yaw * np.pi / -180, 0, 0, 100, 100, 100, color=(0, 255, 0))
        return image


    @staticmethod
    def visualize(
        input_image: np.ndarray, result: SixDOFModelResult, result_history: list[SixDOFModelResult]
    ) -> np.ndarray:
        image = np.copy(input_image)
        image_width = image.shape[1]
        image_height = image.shape[0]
        x1, y1, x2, y2 = map(int, result.bbox)
        if (x2 - x1) * (y2 - y1) == 0:
            return image

        tdx = (x1 + x2) // 2
        tdy = (y1 + y2) // 2
        half_image_width = image_width // 2

        background_side_start = (tdx + half_image_width // 2) % image_width
        background_side_end = (tdx - half_image_width // 2 + image_width) % image_width
        if background_side_start < background_side_end:
            background_side_image = image[:, background_side_start:background_side_end]
        else:
            background_side_image_left = image[:, background_side_start:]
            background_side_image_right = image[:, :background_side_end]
            background_side_image = np.concatenate((background_side_image_left, background_side_image_right), axis=1)

        if len(result_history) > 10:
            target_result_history = result_history[-10:]
            dispersion = np.std([r.yaw for r in target_result_history]) + np.std([r.pitch for r in target_result_history])
            if dispersion < 7:
                yaw: float = result.yaw * np.pi / 180
                pitch: float = result.pitch * np.pi / 180
                roll: float = result.roll * np.pi / 180
                median_yaw = np.median([r.yaw for r in result_history]) * np.pi / 180
                median_pitch = np.median([r.pitch for r in result_history]) * np.pi / 180
                median_roll = np.median([r.roll for r in result_history]) * np.pi / 180
                draw_axis(image, yaw, pitch, roll, tdx, tdy, image_height // 10, color=(0, 255, 0))
                draw_axis(image, median_yaw, median_pitch, median_roll, tdx, tdy, image_height // 10, color=(0, 0, 255))

                delta_yaw = yaw - median_yaw
                delta_pitch = pitch - median_pitch
                delta_roll = roll - median_roll
                scale_x = background_side_image.shape[1]
                scale_y = background_side_image.shape[0]
                offset_x = background_side_image.shape[1] // 2
                offset_y = background_side_image.shape[0] // 2
                end_x = int(offset_x + delta_yaw * scale_x)
                end_y = int(offset_y - delta_pitch * scale_y)
                radius = int(background_side_image.shape[0] // 40 * min(max(0.5, dispersion), 3))
                cv2.arrowedLine(background_side_image, (offset_x, offset_y), (end_x, end_y), (255, 0, 0), 2)
                cv2.circle(background_side_image, (end_x, end_y), radius, (0, 255, 0), 2)

                start_y = int(background_side_image.shape[1] * 0.2)
                cv2.putText(background_side_image, "current: yaw=%.2f, pitch=%.2f, roll=%.2f" % (yaw, pitch, roll), (10, start_y + 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                cv2.putText(background_side_image, "median: yaw=%.2f, pitch=%.2f, roll=%.2f" % (median_yaw, median_pitch, median_roll), (10, start_y + 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                cv2.putText(background_side_image, "delta: yaw=%.2f, pitch=%.2f, roll=%.2f" % (delta_yaw, delta_pitch, delta_roll), (10, start_y + 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                cv2.putText(background_side_image, "dispersion: %.2f" % dispersion, (10, start_y + 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        cropped_face_image = image[y1 - 30 : y2 + 30, x1 - 30 : x2 + 30]
        cropped_face_image = cv2.resize(
            cropped_face_image, (int(background_side_image.shape[1] * 0.2), int(background_side_image.shape[0] * 0.2))
        )
        background_side_image[
            0 : cropped_face_image.shape[0],
            background_side_image.shape[1] - cropped_face_image.shape[1] : background_side_image.shape[1],
        ] = cropped_face_image

        return background_side_image


def draw_axis(image: np.ndarray, yaw: float, pitch: float, roll: float, x_offset: int, y_offset: int, size: int, color: tuple=(0, 0, 255), thickness: int=2):
    x1 = size * (cos(yaw) * cos(roll)) + x_offset
    y1 = size * (cos(pitch) * sin(roll) + cos(roll) * sin(pitch) * sin(yaw)) + y_offset
    x2 = size * (-cos(yaw) * sin(roll)) + x_offset
    y2 = size * (cos(pitch) * cos(roll) - sin(pitch) * sin(yaw) * sin(roll)) + y_offset
    x3 = size * (sin(yaw)) + x_offset
    y3 = size * (-cos(yaw) * sin(pitch)) + y_offset
    cv2.arrowedLine(image, (int(x_offset), int(y_offset)), (int(x1), int(y1)), color, thickness)
    cv2.arrowedLine(image, (int(x_offset), int(y_offset)), (int(x2), int(y2)), color, thickness)
    cv2.arrowedLine(image, (int(x_offset), int(y_offset)), (int(x3), int(y3)), color, thickness)
