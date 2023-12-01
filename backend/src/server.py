import json
import tempfile
import time

from aiohttp import web
from aiortc import (
    MediaStreamTrack,
    RTCPeerConnection,
    RTCSessionDescription,
    RTCDataChannel,
)
from aiortc.contrib.media import MediaPlayer
from av.video import VideoFrame

from processor import ImageProcessor


class VideoStreamTransformTrack(MediaStreamTrack):
    kind: str = "video"

    def __init__(self, track: MediaStreamTrack, channel: RTCDataChannel) -> None:
        super().__init__()
        self.track = track
        self.channel = channel
        self.last_image = None
        self.start_time = None
        self.processor = ImageProcessor()

    async def recv(self) -> VideoFrame:
        frame = await self.track.recv()
        if self.start_time is None:
            self.start_time = time.time()
        if (
            time.time() - self.start_time - frame.pts * frame.time_base >= 0.2
            and self.last_image is not None
        ):
            return self.last_image
        result = self.processor.process_frame(frame.to_ndarray(format="bgr24"))
        image = VideoFrame.from_ndarray(result.image, format="bgr24")
        image.pts = frame.pts
        image.time_base = frame.time_base
        self.last_image = image
        if self.channel.readyState == "open":
            self.channel.send(json.dumps(result.__dict__))
        return image


async def handle_index(_) -> web.FileResponse:
    return web.FileResponse("../frontend/dist/index.html")


async def handle_request(request: web.Request, local: bool = False) -> web.Response:
    params = (
        await request.json()
        if not local
        else json.loads(
            (await request.multipart().next()).read(decode=False).decode("utf-8")
        )
    )
    pc = RTCPeerConnection()
    channel = pc.createDataChannel("data")
    pc.addTrack(
        VideoStreamTransformTrack(
            MediaPlayer(
                tempfile.NamedTemporaryFile(
                    delete=False, suffix=(await request.multipart().next()).filename
                ).name
            ).video
            if local
            else (await request.json())["track"],
            channel,
        )
    )
    await pc.setRemoteDescription(
        RTCSessionDescription(sdp=params["sdp"], type=params["type"])
    )
    await pc.setLocalDescription(await pc.createAnswer())
    return web.Response(
        content_type="application/json",
        text=json.dumps(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        ),
    )


if __name__ == "__main__":
    app = web.Application()
    app.router.add_get("/", handle_index)
    app.router.add_post("/remote", lambda request: handle_request(request, local=False))
    app.router.add_post("/local", lambda request: handle_request(request, local=True))
    app.router.add_static("/", "../frontend/dist")
    web.run_app(app, host="127.0.0.1", port=8080)
