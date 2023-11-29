import json
import sys
import time
import traceback
from typing import Optional, Union

from aiohttp import web
from aiortc import (
    MediaStreamTrack,
    RTCPeerConnection,
    RTCSessionDescription,
    RTCDataChannel,
)
from av.frame import Frame
from av.packet import Packet
from av.video import VideoFrame

from processor import process_frame


class VideoStreamTransformTrack(MediaStreamTrack):
    kind: str = "video"

    def __init__(self, track: MediaStreamTrack, channel: RTCDataChannel) -> None:
        super().__init__()
        self.track: MediaStreamTrack = track
        self.channel: RTCDataChannel = channel
        self.last_image: Optional[VideoFrame] = None
        self.start_time: Optional[float] = None

    async def recv(self) -> VideoFrame:
        frame: Union[Frame, Packet] = await self.track.recv()

        if self.start_time is None:
            self.start_time = time.time()

        if (
                time.time() - self.start_time - frame.pts * frame.time_base * 1.0 >= 0.2
                and self.last_image is not None
        ):
            frame = self.last_image
            return frame

        try:
            image, detected, yaw, pitch, roll = process_frame(
                frame.to_ndarray(format="bgr24"), frame.pts
            )
            image: VideoFrame = VideoFrame.from_ndarray(image, format="bgr24")
            image.pts = frame.pts
            image.time_base = frame.time_base
            self.last_image = image
            if self.channel.readyState == "open":
                self.channel.send(
                    json.dumps(
                        {"detected": detected, "yaw": yaw, "pitch": pitch, "roll": roll}
                    )
                )
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc(file=sys.stdout)
            sys.exit(1)

        return image


async def handle_index(_) -> web.FileResponse:
    return web.FileResponse("../frontend/dist/index.html")


async def handle_remote(request: web.Request) -> web.Response:
    params: dict = await request.json()
    offer: RTCSessionDescription = RTCSessionDescription(
        sdp=params["sdp"], type=params["type"]
    )
    pc: RTCPeerConnection = RTCPeerConnection()
    channel = pc.createDataChannel("data")

    @pc.on("track")
    def on_track(track: MediaStreamTrack) -> None:
        pc.addTrack(VideoStreamTransformTrack(track, channel))

    @pc.on("connectionstatechange")
    async def on_connectionstatechange() -> None:
        if pc.connectionState == "failed":
            await pc.close()
        elif pc.connectionState == "closed":
            await pc.close()

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.Response(
        content_type="application/json",
        text=json.dumps(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        ),
    )


if __name__ == "__main__":
    app: web.Application = web.Application()
    app.router.add_get("/", handle_index)
    app.router.add_post("/remote", handle_remote)
    app.router.add_static("/", "../frontend/dist")

    web.run_app(app, host="127.0.0.1", port=8080)
