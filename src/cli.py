import argparse
import csv

import cv2
import rerun as rr

from processor import ImageProcessor

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process video from camera or file.")
    parser.add_argument("--source", help="Camera id or video file path.", default=0)
    parser.add_argument("--output", help="Output video file path.")
    parser.add_argument("--raw", help="Visualize without 360 degree correction.", action="store_true")

    rr.script_add_args(parser)

    args = parser.parse_args()
    output_path = args.output
    output_ext = output_path.split(".")[-1] if output_path else None

    rr.script_setup(args, "sightrack")

    processor = ImageProcessor()
    cap = cv2.VideoCapture(args.source)

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)

    rr.log("video/result/frame", rr.Clear(recursive=True))

    print("Start processing video. Ctrl+C to stop.")

    if output_ext == "mp4":
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        while True:
            ret, image = cap.read()
            if not ret:
                break

            frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            result = processor.process(image, args.raw)

            rr.set_time_sequence("frame", frame)
            rr.log("video/result/frame", rr.Image(cv2.cvtColor(result.image, cv2.COLOR_BGR2RGB)))

            out.write(result.image)

        out.release()
    elif output_ext == 'csv':
        with open(output_path, 'w', newline='') as f:
            fieldNames = ['frame', 'detected', 'yaw', 'pitch', 'roll']
            writer = csv.DictWriter(f, fieldnames=fieldNames)

            writer.writeheader()

            while True:
                ret, image = cap.read()
                if not ret:
                    break

                frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
                result = processor.process(image, args.raw)

                rr.set_time_sequence("frame", frame)
                rr.log("video/result/frame", rr.Image(cv2.cvtColor(result.image, cv2.COLOR_BGR2RGB)))

                writer.writerow({
                    'frame': frame,
                    'detected': result.detected,
                    'yaw': result.result.yaw,
                    'pitch': result.result.pitch,
                    'roll': result.result.roll
                })
    else:
        while True:
            ret, image = cap.read()
            if not ret:
                break

            frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            result = processor.process(image, args.raw)

            rr.set_time_sequence("frame", frame)
            rr.log("video/result/frame", rr.Image(cv2.cvtColor(result.image, cv2.COLOR_BGR2RGB)))

    rr.script_teardown(args)
