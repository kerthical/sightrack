import os
import urllib.request

import cv2
import mediapipe as mp
import numpy as np
from mediapipe import solutions
from mediapipe.framework.formats import landmark_pb2

LANDMARKER_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
BaseOptions = mp.tasks.BaseOptions
FaceLandmarker = mp.tasks.vision.FaceLandmarker
FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode
NormalizedLandmark = landmark_pb2.NormalizedLandmark
NormalizedLandmarkList = landmark_pb2.NormalizedLandmarkList


class LandmarkerModel:
    def __init__(self, model_path: str):
        if not os.path.exists(model_path):
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            urllib.request.urlretrieve(
                LANDMARKER_MODEL_URL,
                model_path,
            )

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

    def detect(self, image, timestamp):
        return self.landmarker.detect_for_video(
            mp.Image(image_format=mp.ImageFormat.SRGB, data=image),
            timestamp,
        )

    @staticmethod
    def visualize(image, result):
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

        if result.face_landmarks:
            # 顔のlandmarkを取得
            face_landmarks = result.face_landmarks[0]

            # 顔の主要なlandmarkのインデックス
            # mediapipeのモデルに依存するため、モデルが変わるとインデックスも変わる可能性があります
            # 鼻の先端、顎、左目の外側、右目の外側、左口角、右口角
            landmark_indices = [
                1,
                152,
                263,
                33,
                61,
                291,
            ]

            # 3Dモデルポイント
            model_points = np.array(
                [
                    (0.0, 0.0, 0.0),
                    (0.0, -330.0, -65.0),
                    (-225.0, 170.0, -135.0),
                    (225.0, 170.0, -135.0),
                    (-150.0, -150.0, -125.0),
                    (150.0, -150.0, -125.0),
                ]
            )

            # 2Dイメージポイント
            image_points = np.array(
                [
                    (
                        face_landmarks[idx].x * image.shape[1],
                        face_landmarks[idx].y * image.shape[0],
                    )
                    for idx in landmark_indices
                ],
                dtype="double",
            )

            # カメラの内部パラメータ
            size = image.shape
            focal_length = size[1]
            center = (size[1] / 2, size[0] / 2)
            camera_matrix = np.array(
                [[focal_length, 0, center[0]], [0, focal_length, center[1]], [0, 0, 1]],
                dtype="double",
            )

            # 歪み係数はゼロと仮定
            dist_coeffs = np.zeros((4, 1))

            # PnP問題を解く
            success, rotation_vector, translation_vector = cv2.solvePnP(
                model_points, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE
            )

            # 回転ベクトルからオイラー角を取得
            rvec_matrix = cv2.Rodrigues(rotation_vector)[0]
            proj_matrix = np.hstack((rvec_matrix, translation_vector))
            eulerAngles = cv2.decomposeProjectionMatrix(proj_matrix)[6]

            # yaw, pitch, rollを取得
            yaw = eulerAngles[1]
            pitch = eulerAngles[0]
            roll = eulerAngles[2]

            # yawを左上に青色で表示
            cv2.putText(
                annotated_image,
                f"Yaw: {yaw[0]:.2f}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 0, 0),
                4,
                cv2.LINE_AA,
            )

            # 顔の中心からyaw, pitch方向に線を描画
            nose_point = image_points[0]
            # cv2.line(
            #     annotated_image,
            #     (int(nose_point[0]), int(nose_point[1])),
            #     (
            #         int(nose_point[0] + 100 * np.sin(yaw) * np.cos(pitch)),
            #         int(nose_point[1] + 100 * np.sin(pitch)),
            #     ),
            #     (255, 0, 0),
            #     4,
            # )

        return annotated_image
