import argparse
import os
import sys
import traceback
import cv2
from processor import ImageProcessor


def process_file(input: str, output: str):
    print("[*] Starting process_file function")
    file_extension: str = input.split(".")[-1]
    processor = ImageProcessor()

    if file_extension in ["jpg", "jpeg", "png"]:
        print("[+] Processing image file")
        image = cv2.imread(input)
        width = image.shape[1]
        height = image.shape[0]
        print(f"[+] Image file opened with {width}x{height} resolution")

        result = processor.process_frame(image)

        if output.split(".")[-1] in ["jpg", "jpeg", "png"]:
            cv2.imwrite(output, image)
            print("[+] Image file processed and saved")
        elif output.split(".")[-1] in ["csv"]:
            with open(output, "w") as f:
                f.write(f"detected,yaw,pitch,roll,gaze_x,gaze_y,score\n{result.detected},{result.yaw},{result.pitch},{result.roll},{result.gaze_x},{result.gaze_y},{result.score}\n")
            print("[+] Image file processed and data saved to csv")
        else:
            print("[!] Unsupported output file format")
            sys.exit(1)

    elif file_extension in ["mp4", "avi", "mov"]:
        print("[+] Processing video file")
        capture: cv2.VideoCapture = cv2.VideoCapture(input)
        if not capture.isOpened():
            print("[!] Failed to open video file")
            sys.exit(1)
        fps: int = int(capture.get(cv2.CAP_PROP_FPS))
        width: int = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height: int = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames: int = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        print(f"[+] Video file opened with {fps} fps, {width}x{height} resolution and {total_frames} frames")

        frame_count: int = 0

        if output.split(".")[-1] in ["mp4", "avi", "mov"]:
            outfile: cv2.VideoWriter = cv2.VideoWriter(
                output, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height)
            )
            while capture.isOpened():
                ret, frame = capture.read()
                if not ret:
                    break
                result = processor.process_frame(frame)
                outfile.write(result.image)
                frame_count += 1
            print("[+] Video file processed and saved")
        elif output.split(".")[-1] in ["csv"]:
            with open(output, "w") as f:
                f.write("frame,detected,yaw,pitch,roll,gaze_x,gaze_y,score\n")
                while capture.isOpened():
                    ret, frame = capture.read()
                    if not ret:
                        break
                    result = processor.process_frame(frame)
                    f.write(f"{frame_count},{result.detected},{result.yaw},{result.pitch},{result.roll},{result.gaze_x},{result.gaze_y},{result.score}\n")
                    frame_count += 1
            print("[+] Video file processed and data saved to csv")
        else:
            print("[!] Unsupported output file format")
            sys.exit(1)
    else:
        print("[!] Unsupported input file format")
        sys.exit(1)


if __name__ == "__main__":
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Process video/image file."
    )
    parser.add_argument("input", help="Video/Image file to process")
    parser.add_argument("output", help="Video/Image file to process")
    args: argparse.Namespace = parser.parse_args()

    if not os.path.exists(args.input) or os.path.isdir(args.input):
        print("[!] Input file does not exist")
        sys.exit(1)

    try:
        process_file(args.input, args.output)
    except Exception as e:
        print("[!] Error occured while processing file: ", e)
        traceback.print_exc()
        sys.exit(1)
