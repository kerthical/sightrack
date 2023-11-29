import os
import urllib.request

import cv2
import mediapipe as mp
import numpy as np
from mediapipe import solutions
from mediapipe.framework.formats import landmark_pb2
from mediapipe.tasks.python.vision import FaceLandmarkerResult

LANDMARKER_MODEL_URL: str = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
BaseOptions = mp.tasks.BaseOptions
FaceLandmarker = mp.tasks.vision.FaceLandmarker
FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode
NormalizedLandmark = landmark_pb2.NormalizedLandmark
NormalizedLandmarkList = landmark_pb2.NormalizedLandmarkList


def estimate_pose(image: np.array, landmarks: list) -> tuple:
    landmark_indices = [1, 33, 263, 61, 291, 199]
    model_points = np.array(
        [
            (0.0, -3.406404, 5.979507),
            (-2.266659, -7.425768, 4.389812),
            (2.266659, -7.425768, 4.389812),
            (-0.729766, -1.593712, 5.833208),
            (0.729766, -1.593712, 5.833208),
            (0.0, 1.728369, 6.316750),
        ]
    )
    image_points = np.array(
        [
            (landmarks[idx].x * image.shape[1], landmarks[idx].y * image.shape[0])
            for idx in landmark_indices
        ],
        dtype="double",
    )
    size = image.shape
    focal_length = size[1]
    center = (size[1] / 2, size[0] / 2)
    camera_matrix = np.array(
        [[focal_length, 0, center[0]], [0, focal_length, center[1]], [0, 0, 1]],
        dtype="double",
    )
    dist_coeffs = np.zeros((4, 1))
    success, rotation_vector, translation_vector = cv2.solvePnP(
        model_points,
        image_points,
        camera_matrix,
        dist_coeffs,
        flags=cv2.SOLVEPNP_ITERATIVE,
    )
    return success, rotation_vector, translation_vector, image_points


def draw_pose(
    image: np.array,
    rotation_vector: np.array,
    translation_vector: np.array,
    image_points: np.array,
) -> np.array:
    rotation_vector[1] += np.pi / 2
    axis = np.float32([[50, 0, 0], [0, 50, 0], [0, 0, -50]])
    size = image.shape
    focal_length = size[1]
    center = (size[1] / 2, size[0] / 2)
    camera_matrix = np.array(
        [[focal_length, 0, center[0]], [0, focal_length, center[1]], [0, 0, 1]],
        dtype="double",
    )
    dist_coeffs = np.zeros((4, 1))
    imgpts, jac = cv2.projectPoints(
        axis, rotation_vector, translation_vector, camera_matrix, dist_coeffs
    )
    euler_angle = cv2.Rodrigues(rotation_vector)[0]
    yaw = euler_angle[1][0] * 180 / np.pi
    nose_tip = tuple(image_points[0].astype(int))
    image = cv2.line(
        image, nose_tip, tuple(imgpts[0].ravel().astype(int)), (255, 0, 0), 4
    )
    image = cv2.line(
        image, nose_tip, tuple(imgpts[1].ravel().astype(int)), (0, 255, 0), 4
    )
    image = cv2.line(
        image, nose_tip, tuple(imgpts[2].ravel().astype(int)), (0, 0, 255), 4
    )
    return image


class LandmarkModel:
    def __init__(self, model_path: str):
        if not os.path.exists(model_path):
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            urllib.request.urlretrieve(LANDMARKER_MODEL_URL, model_path)
        self.landmarker = FaceLandmarker.create_from_options(
            FaceLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=model_path),
                running_mode=VisionRunningMode.VIDEO,
                num_faces=1,
                min_face_detection_confidence=0.1,
                min_face_presence_confidence=0.1,
                min_tracking_confidence=0.1,
                output_facial_transformation_matrixes=True,
            )
        )

    def detect(self, image: np.array, timestamp: int) -> FaceLandmarkerResult:
        return self.landmarker.detect_for_video(
            mp.Image(image_format=mp.ImageFormat.SRGB, data=image), timestamp
        )

    @staticmethod
    def visualize(image: np.array, result: FaceLandmarkerResult) -> np.array:
        face_landmarks_list = result.face_landmarks
        annotated_image = np.copy(image)
        for idx in range(len(face_landmarks_list)):
            face_landmarks = face_landmarks_list[idx]
            face_landmarks_proto = NormalizedLandmarkList()
            face_landmarks_proto.landmark.extend(
                [
                    NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z)
                    for landmark in face_landmarks
                ]
            )
            solutions.drawing_utils.draw_landmarks(
                image=annotated_image,
                landmark_list=face_landmarks_proto,
                connections=mp.solutions.face_mesh.FACEMESH_TESSELATION,
                connection_drawing_spec=mp.solutions.drawing_styles.get_default_face_mesh_tesselation_style(),
                landmark_drawing_spec=None,
            )
            solutions.drawing_utils.draw_landmarks(
                image=annotated_image,
                landmark_list=face_landmarks_proto,
                connections=mp.solutions.face_mesh.FACEMESH_CONTOURS,
                connection_drawing_spec=mp.solutions.drawing_styles.get_default_face_mesh_contours_style(),
                landmark_drawing_spec=None,
            )
            solutions.drawing_utils.draw_landmarks(
                image=annotated_image,
                landmark_list=face_landmarks_proto,
                connections=mp.solutions.face_mesh.FACEMESH_IRISES,
                connection_drawing_spec=mp.solutions.drawing_styles.get_default_face_mesh_iris_connections_style(),
                landmark_drawing_spec=None,
            )
        return annotated_image
