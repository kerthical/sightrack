from models.landmark import LandmarkModel, visualize
from models.resnet import ResNetModel
from models.yolo import YOLOModel

landmark_model = LandmarkModel("./models/landmark.model")
yolo_model = YOLOModel("./models/yolo.model")
resnet_model = ResNetModel("./models/resnet.model")


def process_frame(image, pts):
    landmark = landmark_model.detect(image, pts)

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
                yaw, pitch, roll = resnet_model.infer(image, largest_box, largest_score)
                image = resnet_model.visualize(
                    image, largest_box, yaw, pitch, 0, largest_score[0]
                )

    else:
        image = visualize(image, landmark)

    return image
