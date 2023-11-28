import sys
import time

from aiortc import MediaStreamTrack
from av import VideoFrame

from models.landmarker import LandmarkerModel, visualize
from models.resnet import ResNetModel
from models.yolo import YOLOModel

landmarker_model = LandmarkerModel("./models/landmarker.model")
yolo_model = YOLOModel("./models/yolo.model")
resnet_model = ResNetModel("./models/resnet.model")


class VideoProcessor(MediaStreamTrack):
    def __init__(self, track):
        super().__init__()
        self.kind = "video"
        self.track = track
        self.last_img = None
        self.start_time = None

    async def recv(self):
        frame = await self.track.recv()
        image = frame.to_ndarray(format="bgr24")

        if self.start_time is None:
            self.start_time = time.time()
        if (
            time.time() - self.start_time - frame.pts * frame.time_base * 1.0 >= 0.2
            and self.last_img is not None
        ):
            frame = self.last_img
            return frame

        try:
            landmark = landmarker_model.detect(image, frame.pts)

            if len(landmark.face_landmarks) == 0:
                boxes, scores = yolo_model.infer(image)
                if len(boxes) > 0:

                    def find_max_confidence_box_and_score(boxes, scores):
                        max_confidence = 0
                        max_confidence_box = None
                        max_confidence_score = None
                        for box, score in zip(boxes, scores):
                            confidence = (box[2] - box[0]) * (box[3] - box[1]) * score
                            if confidence > max_confidence:
                                max_confidence = confidence
                                max_confidence_box = box
                                max_confidence_score = score
                        return max_confidence_box, max_confidence_score

                    largest_box, largest_score = find_max_confidence_box_and_score(
                        boxes, scores
                    )

                    if largest_score[0] > 0.9:
                        yaw, pitch, roll = resnet_model.infer(
                            image, largest_box, largest_score
                        )
                        image = resnet_model.visualize(
                            image, largest_box, yaw, pitch, 0, largest_score[0]
                        )
            #
            # else:
            #     image = visualize(image, landmark)
        except Exception as e:
            print(e)
            sys.exit(1)
            pass

        new_frame = VideoFrame.from_ndarray(image, format="bgr24")
        new_frame.pts = frame.pts
        new_frame.time_base = frame.time_base

        self.last_img = new_frame

        return new_frame
