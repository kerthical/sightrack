import argparse
import sys

import cv2
import asyncio
from aiortc import MediaStreamTrack
from aiortc.contrib.media import MediaPlayer
from av import VideoFrame
from processor import process_frame


class VideoStreamTransformTrack(MediaStreamTrack):
    def __init__(self, track):
        super().__init__()
        self.kind = "video"
        self.track = track
        self.last_img = None
        self.start_time = None

    async def recv(self):
        frame = await self.track.recv()
        image = frame.to_ndarray(format="bgr24")

        try:
            image = process_frame(image, frame.pts)
        except Exception as e:
            print(e)
            sys.exit(1)
            pass

        new_frame = VideoFrame.from_ndarray(image, format="bgr24")
        new_frame.pts = frame.pts
        new_frame.time_base = frame.time_base

        self.last_img = new_frame

        return new_frame


async def main():
    parser = argparse.ArgumentParser(description="Process video frames")
    parser.add_argument("file", help="Video file to process")
    args = parser.parse_args()

    player = MediaPlayer(args.file)
    track = VideoStreamTransformTrack(player.video)

    # Prepare to write the output video
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(
        f"{args.file}_output.mp4",
        fourcc,
        player.video.frame_rate,
        (player.video.width, player.video.height),
    )

    while True:
        frame = await track.recv()
        img = frame.to_ndarray(format="bgr24")

        # Write the frame into the file
        out.write(img)

        if frame is None:
            break

    # Release everything after the job is finished
    out.release()


if __name__ == "__main__":
    asyncio.run(main())
