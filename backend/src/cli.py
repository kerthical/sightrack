import argparse
import os
import sys
import traceback

import cv2


def process_image(args: argparse.Namespace) -> None:
    image = cv2.imread(args.input)
    print("[*] Processing image file...")
    print(f"    - size: {image.shape[1]}x{image.shape[0]}")
    print(f"    - input: {args.input}")
    print(f"    - output: {args.output}")
    print()

    from processor import process_frame

    image, detected, yaw, pitch, roll = process_frame(image)

    print("[*] Result:")
    print(f"    - detected: {detected}")
    if detected:
        print(f"    - yaw: {yaw}")
        print(f"    - pitch: {pitch}")
        print(f"    - roll: {roll}")
    print()

    output_extension = args.output.split(".")[-1]
    if output_extension in ["jpg", "jpeg", "png"]:
        cv2.imwrite(args.output, image)
        print(f"[*] Image saved to {args.output}")
    elif output_extension in ["csv"]:
        with open(args.output, "w") as f:
            f.write("detected,yaw,pitch,roll\n")
            f.write(f"{detected},{yaw},{pitch},{roll}\n")
        print(f"[*] CSV file saved to {args.output}")
    else:
        print(f"[!] Unknown file extension {output_extension}!")
        sys.exit(1)


def process_video(args: argparse.Namespace) -> None:
    capture: cv2.VideoCapture = cv2.VideoCapture(args.input)
    if not capture.isOpened():
        print(f"[!] Error opening video file {args.file}!")
        sys.exit(1)

    width: int = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height: int = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps: int = int(capture.get(cv2.CAP_PROP_FPS))
    total_frames: int = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))

    print("[*] Processing video file...")
    print(f"    - size: {width}x{height}")
    print(f"    - fps: {fps}")
    print(f"    - total frames: {total_frames}")
    print(f"    - duration: {total_frames / fps:.2f} seconds")
    print(f"    - input: {args.input}")
    print(f"    - output: {args.output}")
    print()

    from processor import process_frame

    frame_count: int = 0

    output_extension = args.output.split(".")[-1]
    if output_extension in ["jpg", "jpeg", "png"]:
        pass
    elif output_extension in ["mp4", "avi", "mov"]:
        output: cv2.VideoWriter = cv2.VideoWriter(
            args.output, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height)
        )
        while capture.isOpened():
            ret, frame = capture.read()
            if not ret:
                break
            image, detected, yaw, pitch, roll = process_frame(frame)
            output.write(image)
            frame_count += 1
            print(
                f"\r[*] Processing frame {frame_count}/{total_frames} | detected: {detected}, yaw: {yaw}, pitch: {pitch}, roll: {roll}",
                end="",
            )
        print(f"[*] Video saved to {args.output}")
    elif output_extension in ["csv"]:
        with open(args.output, "w") as f:
            f.write("frame,detected,yaw,pitch,roll\n")
            while capture.isOpened():
                ret, frame = capture.read()
                if not ret:
                    break
                image, detected, yaw, pitch, roll = process_frame(frame)
                f.write(f"{frame_count},{detected},{yaw},{pitch},{roll}\n")
                frame_count += 1
                print(
                    f"\r[*] Processing frame {frame_count}/{total_frames} | detected: {detected}, yaw: {yaw}, pitch: {pitch}, roll: {roll}",
                    end="",
                )
        print(f"[*] CSV file saved to {args.output}")
    else:
        print(f"[!] Unknown file extension {output_extension}!")
        sys.exit(1)


if __name__ == "__main__":
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Process video/image file."
    )
    parser.add_argument("input", help="Video/Image file to process")
    parser.add_argument("output", help="Video/Image file to process")
    args: argparse.Namespace = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"[!] File {args.input} does not exist!")
        sys.exit(1)

    if os.path.isdir(args.input):
        print(f"[!] File {args.input} is a directory!")
        sys.exit(1)

    file_extension: str = args.input.split(".")[-1]
    if file_extension in ["jpg", "jpeg", "png"]:
        try:
            process_image(args)
        except Exception as e:
            print(f"[!] Error processing image file {args.input}!")
            print(e)
            traceback.print_exc()
            sys.exit(1)
    elif file_extension in ["mp4", "avi", "mov"]:
        try:
            process_video(args)
        except Exception as e:
            print(f"[!] Error processing video file {args.input}!")
            print(e)
            traceback.print_exc()
            sys.exit(1)
    else:
        print(f"[!] Unknown file extension {file_extension}!")
        sys.exit(1)
