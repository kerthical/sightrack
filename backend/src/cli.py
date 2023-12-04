import argparse
import os
import sys
import traceback

import cv2

from processor import ImageProcessor


def process_file(input_file: str, output_file: str):
    processor = ImageProcessor()
    input_extension: str = input_file.split(".")[-1]
    output_extension = output_file.split(".")[-1]

    if input_extension in ["jpg", "jpeg", "png"]:
        image = cv2.imread(input_file)
        width = image.shape[1]
        height = image.shape[0]
        print(f"[+] Image file {os.path.abspath(input_file)} opened with {width}x{height} resolution")
        result = processor.process_frame(image)
        if output_extension in ["jpg", "jpeg", "png"]:
            cv2.imwrite(output_file, result.image)
            print(f"[+] Image file processed and result saved to {os.path.abspath(output_file)}")
        elif output_extension in ["csv"]:
            with open(output_file, "w") as f:
                f.write(f"detected,score,yaw,pitch,roll\n{result.detected},{result.result.score},{result.result.yaw},{result.result.pitch},{result.result.roll}")
            print(f"[+] Image file processed and data saved to {os.path.abspath(output_file)}")
        else:
            print("[!] Unsupported output file format")
            sys.exit(1)

    elif input_extension in ["mp4", "avi", "mov"]:
        capture: cv2.VideoCapture = cv2.VideoCapture(input_file)
        if not capture.isOpened():
            print(f"[!] Failed to open video file {os.path.abspath(input_file)}")
            sys.exit(1)
        fps: int = int(capture.get(cv2.CAP_PROP_FPS))
        width: int = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height: int = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames: int = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        print(f"[+] Video file {os.path.abspath(input_file)} opened with {fps} fps, {width}x{height} resolution and {total_frames} frames")

        frame_count: int = 0

        if output_extension in ["mp4", "avi", "mov"]:
            outfile: cv2.VideoWriter = cv2.VideoWriter(output_file, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
            while capture.isOpened():
                ret, frame = capture.read()
                if not ret:
                    break
                result = processor.process_frame(frame)
                outfile.write(result.image)
                frame_count += 1
                print(f"\r[+] Processing frame {frame_count+1}/{total_frames} ({round((frame_count+1)/total_frames*100, 2)}%)", end="")
            print(f"[+] Video file processed and saved to {os.path.abspath(output_file)}")
        elif output_extension in ["csv"]:
            with open(output_file, "w") as f:
                f.write("frame,detected,score,yaw,pitch,roll\n")
                while capture.isOpened():
                    ret, frame = capture.read()
                    if not ret:
                        break
                    image, result = processor.process_frame(frame)
                    f.write(f"{frame_count},{result.detected},{result.result.score},{result.result.yaw},{result.result.pitch},{result.result.roll}\n")
                    frame_count += 1
                    print(f"\r[+] Processing frame {frame_count+1}/{total_frames} ({round((frame_count+1)/total_frames*100, 2)}%)", end="")
            print(f"[+] Video file processed and data saved to {os.path.abspath(output_file)}")
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
    parser.add_argument("-f", "--force", action="store_true", help="Overwrite output file if it already exists")
    args: argparse.Namespace = parser.parse_args()

    if not os.path.exists(args.input) or os.path.isdir(args.input):
        print(f"[!] Input file {os.path.abspath(args.input)} does not exist")
        sys.exit(1)

    if os.path.exists(args.output) and os.path.isdir(args.output):
        print(f"[!] Output file {os.path.abspath(args.output)} is a directory")
        sys.exit(1)

    if os.path.exists(args.output) and not args.force:
        print("[*] Output file already exists, overwrite? (y/N)", end=" ")
        answer = input()
        if answer.lower() != "y":
            print("[!] Aborting")
            sys.exit(1)

    try:
        process_file(args.input, args.output)
    except Exception as e:
        print("[!] Error occured while processing file: ", e)
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)
