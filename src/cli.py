import argparse
import cv2

import rerun as rr

from processor import ImageProcessor

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process video from camera or file.")
    parser.add_argument("--source", help="Camera id or video file path.", default=0)

    rr.script_add_args(parser)

    args = parser.parse_args()

    rr.script_setup(args, "sightrack")

    processor = ImageProcessor()
    cap = cv2.VideoCapture(args.source)

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)

    rr.log("video/result/frame", rr.Clear(recursive=True))

    print("Start processing video. Ctrl+C to stop.")
    while True:
        ret, image = cap.read()
        if not ret:
            break

        frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
        result = processor.process(image)

        rr.set_time_sequence("frame", frame)
        rr.log("video/result/frame", rr.Image(cv2.cvtColor(result.image, cv2.COLOR_BGR2RGB)))

    rr.script_teardown(args)


