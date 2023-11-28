import copy
import os
import shutil
import tarfile
import urllib.request

import cv2
import numpy as np
import onnxruntime

YOLO_MODEL_URL = "https://s3.ap-northeast-2.wasabisys.com/pinto-model-zoo/423_6DRepNet360/resources.tar.gz"


class YOLOModel:
    def __init__(self, model_path: str):
        if not os.path.exists(model_path):
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            urllib.request.urlretrieve(
                YOLO_MODEL_URL,
                model_path + ".tar.gz",
            )
            with tarfile.open(model_path + ".tar.gz", "r:gz") as tar:
                tar.extractall(model_path + "_tmp/")
            os.rename(
                model_path + "_tmp/gold_yolo_n_head_post_0277_0.5071_1x3x480x640.onnx",
                model_path,
            )
            os.remove(model_path + ".tar.gz")
            shutil.rmtree(model_path + "_tmp/")

        self.onnx_session = onnxruntime.InferenceSession(model_path)
        self.input_shapes = [input.shape for input in self.onnx_session.get_inputs()]
        self.input_names = [input.name for input in self.onnx_session.get_inputs()]
        self.output_names = [output.name for output in self.onnx_session.get_outputs()]

    def infer(self, image: np.ndarray):
        temp_image = copy.deepcopy(image)
        swap = (2, 0, 1)
        image1 = cv2.resize(
            temp_image,
            (
                int(self.input_shapes[0][3]),
                int(self.input_shapes[0][2]),
            ),
        )
        image1 = np.divide(image1, 255.0)
        image1 = image1[..., ::-1]
        image1 = image1.transpose(swap)
        image1 = np.ascontiguousarray(
            image1,
            dtype=np.float32,
        )
        resized_image = image1
        inferece_image = np.asarray([resized_image], dtype=np.float32)
        boxes = self.onnx_session.run(
            self.output_names,
            {input_name: inferece_image for input_name in self.input_names},
        )[0]

        image_height = temp_image.shape[0]
        image_width = temp_image.shape[1]

        result_boxes = []
        result_scores = []
        if len(boxes) > 0:
            scores = boxes[:, 6:7]
            keep_idxs = scores[:, 0] > 0.35
            scores_keep = scores[keep_idxs, :]
            boxes_keep = boxes[keep_idxs, :]

            if len(boxes_keep) > 0:
                for box, score in zip(boxes_keep, scores_keep):
                    x_min = int(max(box[2], 0) * image_width / self.input_shapes[0][3])
                    y_min = int(max(box[3], 0) * image_height / self.input_shapes[0][2])
                    x_max = int(
                        min(box[4], self.input_shapes[0][3])
                        * image_width
                        / self.input_shapes[0][3]
                    )
                    y_max = int(
                        min(box[5], self.input_shapes[0][2])
                        * image_height
                        / self.input_shapes[0][2]
                    )

                    result_boxes.append([x_min, y_min, x_max, y_max])
                    result_scores.append(score)

        result = np.asarray(result_boxes), np.asarray(result_scores)
        result_boxes, result_scores = result

        return result_boxes, result_scores
