import argparse
import concurrent.futures
import os
import sys

import cv2
import tqdm



def process_image(args: argparse.Namespace) -> None:
    image = cv2.imread(args.input)
    processed_image = process_frame(image, 0)
    cv2.imwrite(args.output, processed_image)


def process_video(args: argparse.Namespace) -> None:
    capture: cv2.VideoCapture = cv2.VideoCapture(args.file)
    if not capture.isOpened():
        print(f"[!] Error opening video file {args.file}!")
        sys.exit(1)

    from processor import process_frame
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

    output: cv2.VideoWriter = cv2.VideoWriter(
        args.output, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height)
    )
    frame_count: int = 0

    with tqdm.tqdm(
            total=total_frames,
            desc="Processing video file...",
            unit="frames",
            unit_scale=True,
    ) as pbar:
        while capture.isOpened():
            ret, frame = capture.read()
            if not ret:
                break
            output.write(process_frame(frame, frame_count))
            frame_count += 1
            pbar.update(1)


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

    file_extension: str = args.file.split(".")[-1]
    if file_extension in ["jpg", "jpeg", "png"]:
        process_image(args)
    elif file_extension in ["mp4", "avi", "mov"]:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(process_video, args)
            try:
                future.result()
            except KeyboardInterrupt:
                print("Process cancelled.")
                executor.shutdown(wait=False)
                sys.exit(1)
    else:
        print(f"[!] Unknown file extension {file_extension}!")
        sys.exit(1)
