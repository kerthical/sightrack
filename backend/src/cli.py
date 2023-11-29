import argparse
import os
import sys

import cv2
from numpy import ndarray

from processor import process_frame

if __name__ == "__main__":
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Process video/image file."
    )
    parser.add_argument("input", help="Video/Image file to process")
    parser.add_argument("output", help="Video/Image file to process")
    args: argparse.Namespace = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"File {args.input} does not exist!")
        sys.exit(1)

    if os.path.isdir(args.input):
        print(f"File {args.input} is a directory!")
        sys.exit(1)

    file_extension: str = args.file.split(".")[-1]
    if file_extension in ["jpg", "jpeg", "png"]:
        pass
    elif file_extension in ["mp4", "avi", "mov"]:
        capture: cv2.VideoCapture = cv2.VideoCapture(args.file)
        if not capture.isOpened():
            print(f"Error opening video file {args.file}!")
            sys.exit(1)

        width: int = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height: int = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps: int = int(capture.get(cv2.CAP_PROP_FPS))

        output: cv2.VideoWriter = cv2.VideoWriter(
            args.output, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height)
        )
        frame_count: int = 0

        while capture.isOpened():
            ret: bool
            frame: ndarray
            ret, frame = capture.read()
            if not ret:
                break
            output.write(process_frame(frame, frame_count))
            frame_count += 1
