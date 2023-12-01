import argparse
import os
import sys
import traceback
import cv2
from processor import ImageProcessor


def process_file(args: argparse.Namespace) -> None:
    file_extension: str = args.input.split(".")[-1]
    processor = ImageProcessor()

    if file_extension in ["jpg", "jpeg", "png"]:
        image = cv2.imread(args.input)
        image, detected, yaw, pitch, roll, _, _, _, _ = processor.process_frame(image)
        if args.output.split(".")[-1] in ["jpg", "jpeg", "png"]:
            cv2.imwrite(args.output, image)
        elif args.output.split(".")[-1] in ["csv"]:
            with open(args.output, "w") as f:
                f.write(f"detected,yaw,pitch,roll\n{detected},{yaw},{pitch},{roll}\n")
        else:
            sys.exit(1)

    elif file_extension in ["mp4", "avi", "mov"]:
        capture: cv2.VideoCapture = cv2.VideoCapture(args.input)
        if not capture.isOpened():
            sys.exit(1)
        fps: int = int(capture.get(cv2.CAP_PROP_FPS))
        width: int = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height: int = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames: int = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_count: int = 0

        if args.output.split(".")[-1] in ["mp4", "avi", "mov"]:
            output: cv2.VideoWriter = cv2.VideoWriter(
                args.output, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height)
            )
            while capture.isOpened():
                ret, frame = capture.read()
                if not ret:
                    break
                image, detected, yaw, pitch, roll, _, _, _, _ = processor.process_frame(frame)
                output.write(image)
                frame_count += 1
        elif args.output.split(".")[-1] in ["csv"]:
            with open(args.output, "w") as f:
                f.write("frame,detected,yaw,pitch,roll\n")
                while capture.isOpened():
                    ret, frame = capture.read()
                    if not ret:
                        break
                    image, detected, yaw, pitch, roll, _, _, _, _ = processor.process_frame(frame)
                    f.write(f"{frame_count},{detected},{yaw},{pitch},{roll}\n")
                    frame_count += 1
        else:
            sys.exit(1)
    else:
        sys.exit(1)


if __name__ == "__main__":
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Process video/image file."
    )
    parser.add_argument("input", help="Video/Image file to process")
    parser.add_argument("output", help="Video/Image file to process")
    args: argparse.Namespace = parser.parse_args()

    if not os.path.exists(args.input) or os.path.isdir(args.input):
        sys.exit(1)

    try:
        process_file(args)
    except Exception as e:
        print(e)
        traceback.print_exc()
        sys.exit(1)