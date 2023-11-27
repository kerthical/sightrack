import numpy as np
from filterpy.kalman import KalmanFilter

from models.sixdof import SixDOFModel, SixDOFModelResult


class ImageProcessorResult:
    def __init__(self, image: np.ndarray, detected: bool, result: SixDOFModelResult):
        self.image = image
        self.detected = detected
        self.result = result


class ImageProcessor:
    def __init__(self):
        self.sixdof_model = SixDOFModel()
        self.kalman_filters = [create_kalman_filter() for _ in range(8)]
        self.result_history = []

    def process(self, image: np.array) -> ImageProcessorResult:
        raw_result = self.sixdof_model.inference(image)
        detected = bool(raw_result)

        if raw_result:
            measurements = [
                raw_result.bbox[0],
                raw_result.bbox[1],
                raw_result.bbox[2],
                raw_result.bbox[3],
                raw_result.score,
                raw_result.yaw,
                raw_result.pitch,
                raw_result.roll,
            ]

            for i, measurement in enumerate(measurements):
                kf = self.kalman_filters[i]
                kf.predict()
                kf.update([measurement])
                measurements[i] = kf.x[0, 0]

            result = SixDOFModelResult(
                bbox=measurements[:4],
                score=measurements[4],
                yaw=measurements[5],
                pitch=measurements[6],
                roll=measurements[7],
            )
            image = SixDOFModel.visualize(image, result, self.result_history) if result else image
        elif self.result_history:
            predicted_measurements = []
            for kf in self.kalman_filters:
                kf.predict()
                predicted_measurements.append(kf.x[0, 0])
            result = SixDOFModelResult(
                bbox=predicted_measurements[:4],
                score=predicted_measurements[4],
                yaw=predicted_measurements[5],
                pitch=predicted_measurements[6],
                roll=predicted_measurements[7],
            )
        else:
            result = None

        if result is not None:
            self.result_history.append(result)
            if len(self.result_history) > 300:
                self.result_history.pop(0)

        return ImageProcessorResult(image, detected, result)


def create_kalman_filter():
    kf = KalmanFilter(dim_x=2, dim_z=1)
    kf.F = np.array([[1.0, 1.0], [0.0, 1.0]])
    kf.H = np.array([[1.0, 0.0]])
    kf.Q = np.eye(2) * 0.0001
    kf.R = np.array([[5.0]])
    kf.P *= 50.0
    kf.x = np.array([[0.0], [0.0]])
    return kf
