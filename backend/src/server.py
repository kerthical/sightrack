import json
import sys
import tempfile
import time
import traceback
from typing import Optional, Union

from aiohttp import web, MultipartReader
from aiortc import (
    MediaStreamTrack,
    RTCPeerConnection,
    RTCSessionDescription,
    RTCDataChannel,
)
from aiortc.contrib.media import MediaPlayer
from av.frame import Frame
from av.packet import Packet
from av.video import VideoFrame

from processor import ImageProcessor


class VideoStreamTransformTrack(MediaStreamTrack):
    kind: str = "video"

    def __init__(self, track: MediaStreamTrack, channel: RTCDataChannel) -> None:
        super().__init__()
        self.track: MediaStreamTrack = track
        self.channel: RTCDataChannel = channel
        self.last_image: Optional[VideoFrame] = None
        self.start_time: Optional[float] = None
        self.processor = ImageProcessor()

    async def recv(self) -> VideoFrame:
        try:
            frame: Union[Frame, Packet] = await self.track.recv()

            if self.start_time is None:
                self.start_time = time.time()

            if (
                    time.time() - self.start_time - frame.pts * frame.time_base * 1.0 >= 0.2
                    and self.last_image is not None
            ):
                frame = self.last_image
                return frame

            result = self.processor.process_frame(frame.to_ndarray(format="bgr24"))
            image: VideoFrame = VideoFrame.from_ndarray(result.image, format="bgr24")
            image.pts = frame.pts
            image.time_base = frame.time_base
            self.last_image = image

            if self.channel.readyState == "open":
                self.channel.send(
                    json.dumps(
                        {
                            "detected": result.detected,
                            "frame": frame.pts * frame.time_base * 1.0,
                            "box": {
                                "bbox": result.box.bbox,
                                "score": result.box.score,
                            } if result.box else None,
                            "rotation": {
                                "yaw": result.rotation.yaw,
                                "pitch": result.rotation.pitch,
                                "roll": result.rotation.roll,
                            } if result.rotation else None,
                        }
                    )
                )

            return image
        except Exception as e:
            print("[!] Error occured while processing file: ", e)
            traceback.print_exc(file=sys.stdout)
            sys.exit(1)


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


async def handle_local(request: web.Request) -> web.Response:
    reader: MultipartReader = await request.multipart()
    data = None

    while True:
        part = await reader.next()
        if part is None:
            break
        if part.name == "file":
            file_name = part.filename
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_name)
            while True:
                chunk = await part.read_chunk()
                if not chunk:
                    break
                temp_file.write(chunk)
            temp_file.close()
        elif part.name == "data":
            data = await part.read(decode=False)
            data = json.loads(data.decode("utf-8"))

    offer: RTCSessionDescription = RTCSessionDescription(
        sdp=data["sdp"], type=data["type"]
    )
    pc: RTCPeerConnection = RTCPeerConnection()
    channel = pc.createDataChannel("data")

    @pc.on("track")
    def on_track(_) -> None:
        pc.addTrack(
            VideoStreamTransformTrack(MediaPlayer(temp_file.name).video, channel)
        )

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
    app.router.add_post("/local", handle_local)
    app.router.add_static("/", "../frontend/dist")

    web.run_app(app, host="127.0.0.1", port=8080)
